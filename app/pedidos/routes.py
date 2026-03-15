"""
Rutas CRUD para Pedidos/Ventas
Incluye: Crear, Leer, Actualizar, Cancelar, Búsqueda y Gestión de Estados
"""

from datetime import datetime
from flask import render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import current_user
from pydantic import ValidationError

from app.pedidos import pedidos_bp
from app.pedidos.schemas import PedidoCreateSchema, PedidoUpdateSchema, generar_numero_pedido
from app.pedidos.pdf_generator import generar_factura_pdf
from app.auth.decorators import cliente_required, vendedor_required
from app.models import Pedido, DetallePedido, Producto, Usuario
from app.extensions import db


@pedidos_bp.route('/')
@cliente_required
def listar():
    """
    Listar pedidos con búsqueda y filtros
    Acceso: Cliente ve sus pedidos, Vendedor/Admin ven todos
    """
    busqueda = request.args.get('busqueda', '', type=str)
    estado = request.args.get('estado', 'todos', type=str)
    orden = request.args.get('orden', 'fecha_desc', type=str)

    if current_user.is_vendedor():
        query = Pedido.query
    else:
        query = Pedido.query.filter_by(cliente_id=current_user.id)

    if busqueda:
        query = query.filter(Pedido.numero_pedido.like(f'%{busqueda}%'))

    if estado != 'todos':
        query = query.filter_by(estado=estado)

    if orden == 'fecha_desc':
        query = query.order_by(Pedido.fecha_pedido.desc())
    elif orden == 'fecha_asc':
        query = query.order_by(Pedido.fecha_pedido.asc())
    elif orden == 'total_desc':
        query = query.order_by(Pedido.total.desc())
    elif orden == 'total_asc':
        query = query.order_by(Pedido.total.asc())

    page = request.args.get('page', 1, type=int)
    per_page = 15
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    pedidos = pagination.items

    return render_template('pedidos/listar.html',
                           pedidos=pedidos,
                           pagination=pagination,
                           busqueda=busqueda,
                           estado=estado,
                           orden=orden)


@pedidos_bp.route('/<int:id>')
@cliente_required
def ver(id):
    """
    Ver detalle de un pedido
    Acceso: Cliente solo ve sus pedidos, Vendedor/Admin ven todos
    """
    pedido = Pedido.query.get_or_404(id)

    if not current_user.is_vendedor() and pedido.cliente_id != current_user.id:
        flash('No tienes permiso para ver este pedido.', 'danger')
        return redirect(url_for('pedidos.listar'))

    return render_template('pedidos/ver.html', pedido=pedido)


@pedidos_bp.route('/crear', methods=['GET', 'POST'])
@cliente_required
def crear():
    """
    Crear nuevo pedido
    Acceso: Todos los usuarios autenticados
    """
    productos = Producto.query.filter_by(activo=True).filter(Producto.stock > 0).all()

    if request.method == 'POST':
        try:
            form_data = {
                'direccion_entrega': request.form.get('direccion_entrega'),
                'telefono_contacto': request.form.get('telefono_contacto'),
                'notas': request.form.get('notas'),
                'detalles': []
            }

            productos_ids = request.form.getlist('productos[]')
            cantidades = request.form.getlist('cantidades[]')

            for prod_id, cantidad in zip(productos_ids, cantidades):
                if prod_id and cantidad:
                    form_data['detalles'].append({
                        'producto_id': int(prod_id),
                        'cantidad': int(cantidad)
                    })

            datos = PedidoCreateSchema(**form_data)

            detalles_validados = []
            subtotal = 0

            for detalle_data in datos.detalles:
                producto = Producto.query.get(detalle_data.producto_id)

                if not producto:
                    raise ValueError(f'El producto con ID {detalle_data.producto_id} no existe')

                if not producto.activo:
                    raise ValueError(f'El producto "{producto.nombre}" no está disponible')

                if producto.stock < detalle_data.cantidad:
                    raise ValueError(f'Stock insuficiente para "{producto.nombre}". Stock disponible: {producto.stock}')

                detalle_subtotal = producto.precio * detalle_data.cantidad
                subtotal += detalle_subtotal

                detalles_validados.append({
                    'producto': producto,
                    'cantidad': detalle_data.cantidad,
                    'precio_unitario': producto.precio,
                    'subtotal': detalle_subtotal
                })

            numero_pedido = generar_numero_pedido()
            while Pedido.query.filter_by(numero_pedido=numero_pedido).first():
                numero_pedido = generar_numero_pedido()

            nuevo_pedido = Pedido(
                numero_pedido=numero_pedido,
                cliente_id=current_user.id,
                estado='completado',
                direccion_entrega=datos.direccion_entrega,
                telefono_contacto=datos.telefono_contacto,
                notas=datos.notas,
                subtotal=subtotal,
                total=subtotal
            )

            db.session.add(nuevo_pedido)
            db.session.flush()  
            for detalle in detalles_validados:
                detalle_pedido = DetallePedido(
                    pedido_id=nuevo_pedido.id,
                    producto_id=detalle['producto'].id,
                    cantidad=detalle['cantidad'],
                    precio_unitario=detalle['precio_unitario'],
                    subtotal=detalle['subtotal']
                )
                db.session.add(detalle_pedido)

                detalle['producto'].reducir_stock(detalle['cantidad'])

            db.session.commit()

            flash(f'Pedido {nuevo_pedido.numero_pedido} creado exitosamente.', 'success')
            return redirect(url_for('pedidos.ver', id=nuevo_pedido.id))

        except ValidationError as e:
            for error in e.errors():
                campo = error['loc'][0]
                mensaje = error['msg']
                flash(f'{campo}: {mensaje}', 'danger')

        except ValueError as e:
            flash(str(e), 'danger')

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear pedido: {str(e)}', 'danger')

    return render_template('pedidos/crear.html', productos=productos)


@pedidos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@vendedor_required
def editar(id):
    """
    Editar información de un pedido (solo vendedor/admin)
    Acceso: Vendedor y Admin
    Nota: No se pueden modificar los productos, solo datos de entrega y estado
    """
    pedido = Pedido.query.get_or_404(id)

    if pedido.estado in ['entregado', 'cancelado']:
        flash('No se puede editar un pedido entregado o cancelado.', 'warning')
        return redirect(url_for('pedidos.ver', id=pedido.id))

    if request.method == 'POST':
        try:
            form_data = request.form.to_dict()

            if form_data.get('fecha_entrega'):
                try:
                    form_data['fecha_entrega'] = datetime.fromisoformat(form_data['fecha_entrega'])
                except:
                    form_data['fecha_entrega'] = None

            datos = PedidoUpdateSchema(**form_data)

            if datos.estado is not None:
                if not validar_transicion_estado(pedido.estado, datos.estado):
                    flash(f'Transición de estado inválida: {pedido.estado} -> {datos.estado}', 'danger')
                    return render_template('pedidos/editar.html', pedido=pedido)

                pedido.estado = datos.estado

            if datos.direccion_entrega is not None:
                pedido.direccion_entrega = datos.direccion_entrega

            if datos.telefono_contacto is not None:
                pedido.telefono_contacto = datos.telefono_contacto

            if datos.notas is not None:
                pedido.notas = datos.notas

            if datos.fecha_entrega is not None:
                pedido.fecha_entrega = datos.fecha_entrega

            db.session.commit()

            flash(f'Pedido {pedido.numero_pedido} actualizado exitosamente.', 'success')
            return redirect(url_for('pedidos.ver', id=pedido.id))

        except ValidationError as e:
            for error in e.errors():
                campo = error['loc'][0]
                mensaje = error['msg']
                flash(f'{campo}: {mensaje}', 'danger')

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar pedido: {str(e)}', 'danger')

    return render_template('pedidos/editar.html', pedido=pedido)


@pedidos_bp.route('/<int:id>/cancelar', methods=['POST'])
@cliente_required
def cancelar(id):
    """
    Cancelar un pedido
    Acceso: Cliente solo puede cancelar sus pedidos, Vendedor/Admin pueden cancelar cualquiera
    Nota: Solo se pueden cancelar pedidos en estado 'pendiente'
    """
    pedido = Pedido.query.get_or_404(id)

    if not current_user.is_vendedor() and pedido.cliente_id != current_user.id:
        flash('No tienes permiso para cancelar este pedido.', 'danger')
        return redirect(url_for('pedidos.listar'))

    if pedido.estado != 'pendiente':
        flash('Solo se pueden cancelar pedidos en estado "pendiente".', 'warning')
        return redirect(url_for('pedidos.ver', id=pedido.id))

    try:
        for detalle in pedido.detalles:
            detalle.producto.stock += detalle.cantidad

        pedido.estado = 'cancelado'
        db.session.commit()

        flash(f'Pedido {pedido.numero_pedido} cancelado exitosamente. Stock restaurado.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al cancelar pedido: {str(e)}', 'danger')

    return redirect(url_for('pedidos.ver', id=pedido.id))


@pedidos_bp.route('/<int:id>/cambiar-estado', methods=['POST'])
@vendedor_required
def cambiar_estado(id):
    """
    Cambiar estado de un pedido (vendedor/admin)
    Acceso: Vendedor y Admin
    """
    pedido = Pedido.query.get_or_404(id)
    nuevo_estado = request.form.get('estado')

    estados_validos = ['pendiente', 'procesando', 'enviado', 'entregado', 'cancelado']
    if nuevo_estado not in estados_validos:
        flash('Estado inválido.', 'danger')
        return redirect(url_for('pedidos.ver', id=pedido.id))

    if not validar_transicion_estado(pedido.estado, nuevo_estado):
        flash(f'Transición de estado inválida: {pedido.estado} -> {nuevo_estado}', 'danger')
        return redirect(url_for('pedidos.ver', id=pedido.id))

    try:
        if nuevo_estado == 'cancelado' and pedido.estado != 'cancelado':
            for detalle in pedido.detalles:
                detalle.producto.stock += detalle.cantidad

        if nuevo_estado == 'entregado':
            pedido.fecha_entrega = datetime.utcnow()

        pedido.estado = nuevo_estado
        db.session.commit()

        flash(f'Estado del pedido cambiado a "{nuevo_estado}".', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado: {str(e)}', 'danger')

    return redirect(url_for('pedidos.ver', id=pedido.id))


def validar_transicion_estado(estado_actual, nuevo_estado):
    """
    Validar que la transición de estado sea válida

    Reglas:
    - pendiente -> procesando, cancelado
    - procesando -> enviado, cancelado
    - enviado -> entregado
    - entregado -> (no se puede cambiar)
    - cancelado -> (no se puede cambiar)
    """
    transiciones_validas = {
        'pendiente': ['procesando', 'cancelado'],
        'procesando': ['enviado', 'cancelado'],
        'enviado': ['entregado'],
        'entregado': [],
        'cancelado': []
    }

    return nuevo_estado in transiciones_validas.get(estado_actual, [])


@pedidos_bp.route('/api/producto/<int:id>')
@cliente_required
def api_producto(id):
    """API endpoint para obtener info de producto (para formulario dinámico)"""
    producto = Producto.query.get_or_404(id)

    return jsonify({
        'id': producto.id,
        'nombre': producto.nombre,
        'precio': float(producto.precio),
        'stock': producto.stock,
        'imagen': producto.imagen
    })


@pedidos_bp.route('/<int:id>/factura')
@cliente_required
def descargar_factura(id):
    """
    Descargar factura en PDF de un pedido
    Acceso: Cliente solo puede descargar sus facturas, Vendedor/Admin pueden todas
    """
    pedido = Pedido.query.get_or_404(id)

    if not current_user.is_vendedor() and pedido.cliente_id != current_user.id:
        flash('No tienes permiso para descargar esta factura.', 'danger')
        return redirect(url_for('pedidos.listar'))

    try:
        pdf_buffer = generar_factura_pdf(pedido)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'factura_{pedido.numero_pedido}.pdf'
        )
    except Exception as e:
        flash(f'Error al generar factura: {str(e)}', 'danger')
        return redirect(url_for('pedidos.ver', id=pedido.id))
