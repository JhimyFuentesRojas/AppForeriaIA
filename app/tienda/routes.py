"""
Rutas de la Tienda - E-commerce con Carrito de Compras
"""

from flask import render_template, redirect, url_for, flash, request, session, jsonify
from decimal import Decimal

from app.tienda import tienda_bp
from app.models import Producto, Categoria, Pedido, DetallePedido
from app.extensions import db
from flask_login import current_user, login_required

def clean_cart_session():
    """Valida y limpia la sesión del carrito de ítems corruptos"""
    carrito = session.get('carrito', {})
    if not isinstance(carrito, dict):
        carrito = {}
    
    carrito_limpio = {}
    modificado = False
    
    for key, item in list(carrito.items()):
        if not isinstance(item, dict) or 'producto_id' not in item:
            modificado = True
            continue
            
        try:
            prod_id = int(item.get('producto_id'))
            if str(prod_id) != str(key):
                modificado = True
                continue
            carrito_limpio[str(prod_id)] = item
        except (ValueError, TypeError):
            modificado = True
            continue
            
    if modificado:
        session['carrito'] = carrito_limpio
        session.modified = True
        
    return carrito_limpio

@tienda_bp.route('/')
def index():
    """
    Vista principal de la tienda con filtros laterales
    Estilo e-commerce profesional
    """
    # Obtener parámetros de filtros
    categoria_id = request.args.get('categoria', type=int)
    precio_min = request.args.get('precio_min', type=float)
    precio_max = request.args.get('precio_max', type=float)
    busqueda = request.args.get('q', '', type=str)
    orden = request.args.get('orden', 'nombre', type=str)

    # Query base: solo productos activos con stock
    query = Producto.query.filter_by(activo=True).filter(Producto.stock > 0)

    # Aplicar filtros
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)

    if precio_min is not None:
        query = query.filter(Producto.precio >= precio_min)

    if precio_max is not None:
        query = query.filter(Producto.precio <= precio_max)

    if busqueda:
        query = query.filter(
            (Producto.nombre.like(f'%{busqueda}%')) |
            (Producto.descripcion.like(f'%{busqueda}%'))
        )

    # Ordenamiento
    if orden == 'precio_asc':
        query = query.order_by(Producto.precio.asc())
    elif orden == 'precio_desc':
        query = query.order_by(Producto.precio.desc())
    elif orden == 'nombre':
        query = query.order_by(Producto.nombre.asc())
    elif orden == 'destacados':
        query = query.order_by(Producto.destacado.desc(), Producto.nombre.asc())

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 12
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    productos = pagination.items

    # Obtener todas las categorías para el filtro lateral
    categorias = Categoria.query.filter_by(activo=True).all()

    # Calcular rangos de precio
    precio_stats = db.session.query(
        db.func.min(Producto.precio),
        db.func.max(Producto.precio)
    ).filter_by(activo=True).first()

    precio_minimo = float(precio_stats[0]) if precio_stats[0] else 0
    precio_maximo = float(precio_stats[1]) if precio_stats[1] else 1000

    # Obtener cantidad de items en el carrito
    carrito = clean_cart_session()
    items_carrito = sum(item.get('cantidad', 0) for item in carrito.values())

    return render_template('tienda/index.html',
                          productos=productos,
                          categorias=categorias,
                          pagination=pagination,
                          categoria_id=categoria_id,
                          precio_min=precio_min,
                          precio_max=precio_max,
                          precio_minimo=precio_minimo,
                          precio_maximo=precio_maximo,
                          busqueda=busqueda,
                          orden=orden,
                          items_carrito=items_carrito)


@tienda_bp.route('/agregar-carrito/<int:producto_id>', methods=['POST'])
@login_required
def agregar_carrito(producto_id):
    """Agregar producto al carrito"""
    producto = Producto.query.get_or_404(producto_id)

    if not producto.activo or producto.stock <= 0:
        return jsonify({'success': False, 'message': 'Producto no disponible'}), 400

    cantidad = request.form.get('cantidad', 1, type=int)

    if cantidad <= 0:
        return jsonify({'success': False, 'message': 'Cantidad inválida'}), 400

    if cantidad > producto.stock:
        return jsonify({'success': False, 'message': f'Stock insuficiente. Disponible: {producto.stock}'}), 400

    # Obtener o crear carrito en sesión
    carrito = clean_cart_session()

    producto_key = str(producto_id)

    if producto_key in carrito:
        # Actualizar cantidad
        nueva_cantidad = carrito[producto_key]['cantidad'] + cantidad
        if nueva_cantidad > producto.stock:
            return jsonify({'success': False, 'message': f'Stock insuficiente. Disponible: {producto.stock}'}), 400
        carrito[producto_key]['cantidad'] = nueva_cantidad
    else:
        # Agregar nuevo producto
        carrito[producto_key] = {
            'producto_id': producto_id,
            'nombre': producto.nombre,
            'precio': float(producto.precio),
            'cantidad': cantidad,
            'imagen': producto.imagen,
            'stock': producto.stock
        }

    session['carrito'] = carrito
    session.modified = True

    # Calcular totales
    items_carrito = sum(item.get('cantidad', 0) for item in carrito.values())
    total_carrito = sum(item.get('precio', 0) * item.get('cantidad', 0) for item in carrito.values())

    return jsonify({
        'success': True,
        'message': f'{producto.nombre} agregado al carrito',
        'items_carrito': items_carrito,
        'total_carrito': f'${total_carrito:.2f}'
    })


@tienda_bp.route('/carrito')
@login_required
def ver_carrito():
    """Ver contenido del carrito"""
    carrito = clean_cart_session()

    if not carrito:
        flash('Tu carrito está vacío', 'info')
        return redirect(url_for('tienda.index'))

    # Calcular totales
    items = []
    subtotal = 0

    for key, item in list(carrito.items()):
        # Verificar que el producto aún existe y tiene stock usando get seguro
        prod_id = item.get('producto_id')
        if not prod_id:
            continue
            
        producto = Producto.query.get(prod_id)
        if producto and producto.activo:
            item_subtotal = item.get('precio', 0) * item.get('cantidad', 0)
            items.append({
                **item,
                'subtotal': item_subtotal,
                'stock_actual': producto.stock
            })
            subtotal += item_subtotal
        else:
            # Producto ya no existe o está inactivo, remover silenciosamente
            del carrito[key]
            session.modified = True

    return render_template('tienda/carrito.html',
                          items=items,
                          subtotal=subtotal,
                          total=subtotal)


@tienda_bp.route('/actualizar-carrito/<int:producto_id>', methods=['POST'])
@login_required
def actualizar_carrito(producto_id):
    """Actualizar cantidad de un producto en el carrito"""
    carrito = clean_cart_session()
    producto_key = str(producto_id)

    if producto_key not in carrito:
        return jsonify({'success': False, 'message': 'Producto no encontrado en el carrito'}), 404

    nueva_cantidad = request.form.get('cantidad', type=int)

    if nueva_cantidad <= 0:
        # Eliminar del carrito
        if producto_key in carrito:
            del carrito[producto_key]
        session['carrito'] = carrito
        session.modified = True
        
        # Calcular nuevos totales
        items_carrito = sum(item.get('cantidad', 0) for item in carrito.values())
        total_carrito = sum(item.get('precio', 0) * item.get('cantidad', 0) for item in carrito.values())
        
        return jsonify({
            'success': True, 
            'message': 'Producto eliminado del carrito',
            'items_carrito': items_carrito,
            'total_carrito': f'${total_carrito:.2f}',
            'deleted': True
        })

    # Verificar stock
    producto = Producto.query.get(producto_id)
    if not producto or nueva_cantidad > producto.stock:
        return jsonify({'success': False, 'message': 'Stock insuficiente'}), 400

    carrito[producto_key]['cantidad'] = nueva_cantidad
    session['carrito'] = carrito
    session.modified = True

    # Calcular nuevos totales
    items_carrito = sum(item.get('cantidad', 0) for item in carrito.values())
    total_carrito = sum(item.get('precio', 0) * item.get('cantidad', 0) for item in carrito.values())
    item_subtotal = carrito[producto_key].get('precio', 0) * nueva_cantidad

    return jsonify({
        'success': True,
        'items_carrito': items_carrito,
        'total_carrito': f'${total_carrito:.2f}',
        'item_subtotal': f'${item_subtotal:.2f}'
    })


@tienda_bp.route('/eliminar-carrito/<int:producto_id>', methods=['POST'])
@login_required
def eliminar_carrito(producto_id):
    """Eliminar producto del carrito (AJAX preferido)"""
    carrito = clean_cart_session()
    producto_key = str(producto_id)

    if producto_key in carrito:
        del carrito[producto_key]
        session['carrito'] = carrito
        session.modified = True

    # Calcular nuevos totales
    items_carrito = sum(item.get('cantidad', 0) for item in carrito.values())
    total_carrito = sum(item.get('precio', 0) * item.get('cantidad', 0) for item in carrito.values())

    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            'success': True,
            'message': 'Producto eliminado del carrito',
            'items_carrito': items_carrito,
            'total_carrito': f'${total_carrito:.2f}'
        })

    flash('Producto eliminado del carrito', 'success')
    return redirect(url_for('tienda.ver_carrito'))


@tienda_bp.route('/vaciar-carrito', methods=['POST'])
@login_required
def vaciar_carrito():
    """Vaciar todo el carrito"""
    session.pop('carrito', None)
    session.modified = True
    flash('Carrito vaciado', 'info')
    return redirect(url_for('tienda.index'))


@tienda_bp.route('/checkout')
@login_required
def checkout():
    """Proceso de checkout"""
    carrito = clean_cart_session()

    if not carrito:
        flash('Tu carrito está vacío', 'warning')
        return redirect(url_for('tienda.index'))

    # Calcular totales
    items = []
    subtotal = 0

    for key, item in list(carrito.items()):
        prod_id = item.get('producto_id')
        if not prod_id: continue
        producto = Producto.query.get(prod_id)
        if producto and producto.activo and producto.stock >= item.get('cantidad', 0):
            item_subtotal = item.get('precio', 0) * item.get('cantidad', 0)
            items.append({
                **item,
                'subtotal': item_subtotal
            })
            subtotal += item_subtotal

    return render_template('tienda/checkout.html',
                          items=items,
                          subtotal=subtotal,
                          total=subtotal,
                          usuario=current_user)


@tienda_bp.route('/procesar-compra', methods=['POST'])
@login_required
def procesar_compra():
    """Procesar la compra y crear el pedido (AJAX)"""
    carrito = clean_cart_session()

    if not carrito:
        return jsonify({'success': False, 'message': 'Tu carrito está vacío'})

    try:
        # Obtener datos del formulario
        direccion_entrega = request.form.get('direccion_entrega')
        telefono_contacto = request.form.get('telefono_contacto')
        notas = request.form.get('notas', '')

        if not direccion_entrega or not telefono_contacto:
            return jsonify({'success': False, 'message': 'Debes completar la dirección y teléfono'})

        # Generar número de pedido
        from app.pedidos.schemas import generar_numero_pedido
        numero_pedido = generar_numero_pedido()
        while Pedido.query.filter_by(numero_pedido=numero_pedido).first():
            numero_pedido = generar_numero_pedido()

        # Crear pedido con estado completado (pago simulado)
        nuevo_pedido = Pedido(
            numero_pedido=numero_pedido,
            cliente_id=current_user.id,
            estado='completado',
            direccion_entrega=direccion_entrega,
            telefono_contacto=telefono_contacto,
            notas=notas
        )

        db.session.add(nuevo_pedido)
        db.session.flush()

        # Crear detalles y reducir stock
        subtotal = 0
        for key, item in list(carrito.items()):
            prod_id = item.get('producto_id')
            producto = Producto.query.get(prod_id)

            if not producto or not producto.activo:
                raise ValueError(f'Producto {item.get("nombre", "Desconocido")} no disponible')

            cantidad_item = item.get('cantidad', 0)
            if producto.stock < cantidad_item:
                raise ValueError(f'Stock insuficiente para {producto.nombre}')

            # Crear detalle
            detalle = DetallePedido(
                pedido_id=nuevo_pedido.id,
                producto_id=producto.id,
                cantidad=cantidad_item,
                precio_unitario=producto.precio,
                subtotal=producto.precio * cantidad_item
            )
            db.session.add(detalle)

            # Reducir stock
            producto.stock -= cantidad_item
            subtotal += detalle.subtotal

        # Actualizar totales del pedido
        nuevo_pedido.subtotal = subtotal
        nuevo_pedido.total = subtotal

        db.session.commit()

        # Vaciar carrito
        session.pop('carrito', None)
        session.modified = True

        # Redirigir a pantalla de procesando (simula pago)
        return jsonify({
            'success': True,
            'message': 'Pedido procesado con éxito',
            'redirect_url': url_for('tienda.procesando_pago', pedido_id=nuevo_pedido.id)
        })

    except ValueError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al procesar la compra: {str(e)}'})


@tienda_bp.route('/producto/<int:id>')
def detalle_producto(id):
    """Vista rápida del producto (modal o página)"""
    producto = Producto.query.get_or_404(id)

    # Productos relacionados
    relacionados = Producto.query.filter(
        Producto.categoria_id == producto.categoria_id,
        Producto.id != producto.id,
        Producto.activo == True,
        Producto.stock > 0
    ).limit(4).all()

    return render_template('tienda/producto_detalle.html',
                          producto=producto,
                          relacionados=relacionados)


@tienda_bp.route('/api/carrito-count')
def carrito_count():
    """API endpoint para obtener el número de items en el carrito"""
    carrito = clean_cart_session()
    items_count = sum(item.get('cantidad', 0) for item in carrito.values())
    return jsonify({'count': items_count})


@tienda_bp.route('/procesando-pago/<int:pedido_id>')
@login_required
def procesando_pago(pedido_id):
    """
    Pantalla de procesando pago (simulación)
    Muestra mensaje de procesamiento y luego redirige al pedido con factura
    """
    pedido = Pedido.query.get_or_404(pedido_id)

    if pedido.cliente_id != current_user.id and not current_user.is_vendedor():
        flash('No tienes permiso para ver este pedido.', 'danger')
        return redirect(url_for('tienda.index'))

    return render_template('tienda/procesando_pago.html', pedido=pedido)
