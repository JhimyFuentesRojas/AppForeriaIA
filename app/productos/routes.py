"""
Rutas CRUD para Productos con Subida de Imágenes
Incluye: Crear, Leer, Actualizar, Eliminar, Búsqueda, Filtros y Subida de Imágenes
RETO ADICIONAL: Subida y optimización de imágenes
"""

from flask import render_template, redirect, url_for, flash, request
from pydantic import ValidationError
from decimal import Decimal

from app.productos import productos_bp
from app.productos.schemas import ProductoCreateSchema, ProductoUpdateSchema
from app.productos.utils import (
    guardar_imagen, eliminar_imagen, extension_permitida,
    validar_tamano_archivo, generar_sku_unico
)
from app.auth.decorators import vendedor_required
from app.models import Producto, Categoria
from app.extensions import db


@productos_bp.route('/')
def listar():
    """
    Listar productos con búsqueda y filtros avanzados
    Acceso: Público
    """
    busqueda = request.args.get('busqueda', '', type=str)
    categoria_id = request.args.get('categoria_id', None, type=int)
    precio_min = request.args.get('precio_min', None, type=float)
    precio_max = request.args.get('precio_max', None, type=float)
    solo_destacados = request.args.get('destacados', False, type=bool)
    orden = request.args.get('orden', 'nombre', type=str)

    query = Producto.query.filter_by(activo=True)

    if busqueda:
        query = query.filter(
            (Producto.nombre.like(f'%{busqueda}%')) |
            (Producto.descripcion.like(f'%{busqueda}%'))
        )

    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)

    if precio_min is not None:
        query = query.filter(Producto.precio >= precio_min)
    if precio_max is not None:
        query = query.filter(Producto.precio <= precio_max)

    if solo_destacados:
        query = query.filter_by(destacado=True)

    if orden == 'nombre':
        query = query.order_by(Producto.nombre.asc())
    elif orden == 'precio_asc':
        query = query.order_by(Producto.precio.asc())
    elif orden == 'precio_desc':
        query = query.order_by(Producto.precio.desc())
    elif orden == 'fecha':
        query = query.order_by(Producto.fecha_creacion.desc())
    elif orden == 'stock':
        query = query.order_by(Producto.stock.desc())

    page = request.args.get('page', 1, type=int)
    per_page = 12
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    productos = pagination.items

    categorias = Categoria.query.filter_by(activo=True).all()

    return render_template('productos/listar.html',
                           productos=productos,
                           pagination=pagination,
                           categorias=categorias,
                           busqueda=busqueda,
                           categoria_id=categoria_id,
                           precio_min=precio_min,
                           precio_max=precio_max,
                           solo_destacados=solo_destacados,
                           orden=orden)


@productos_bp.route('/<int:id>')
def ver(id):
    """
    Ver detalle de un producto
    Acceso: Público
    """
    producto = Producto.query.get_or_404(id)

    productos_relacionados = Producto.query.filter(
        Producto.categoria_id == producto.categoria_id,
        Producto.id != producto.id,
        Producto.activo == True
    ).limit(4).all()

    return render_template('productos/ver.html',
                           producto=producto,
                           productos_relacionados=productos_relacionados)


@productos_bp.route('/crear', methods=['GET', 'POST'])
@vendedor_required
def crear():
    """
    Crear nuevo producto con subida de imagen
    Acceso: Vendedor y Admin
    """
    categorias = Categoria.query.filter_by(activo=True).all()

    if request.method == 'POST':
        form_data = None
        try:
            form_data = request.form.to_dict()

            form_data['precio'] = Decimal(form_data.get('precio', 0))
            form_data['stock'] = int(form_data.get('stock', 0))
            form_data['categoria_id'] = int(form_data.get('categoria_id'))
            form_data['activo'] = form_data.get('activo') == 'on'
            form_data['destacado'] = form_data.get('destacado') == 'on'

            if not form_data.get('sku'):
                form_data['sku'] = generar_sku_unico()

            datos = ProductoCreateSchema(**form_data)

            categoria = Categoria.query.get(datos.categoria_id)
            if not categoria:
                flash('La categoría seleccionada no existe.', 'danger')
                return render_template('productos/crear.html', categorias=categorias, form_data=form_data)

            if Producto.query.filter_by(sku=datos.sku).first():
                flash(f'El SKU "{datos.sku}" ya está en uso.', 'danger')
                return render_template('productos/crear.html', categorias=categorias, form_data=form_data)

            imagen_path = None
            if 'imagen' in request.files:
                archivo = request.files['imagen']
                if archivo and archivo.filename != '':
                    if not validar_tamano_archivo(archivo):
                        flash('La imagen supera el tamaño máximo permitido (16 MB).', 'danger')
                        return render_template('productos/crear.html', categorias=categorias, form_data=form_data)

                    if not extension_permitida(archivo.filename):
                        flash('Formato de imagen no permitido. Usa: PNG, JPG, JPEG, GIF, WEBP', 'danger')
                        return render_template('productos/crear.html', categorias=categorias, form_data=form_data)

                    try:
                        imagen_path = guardar_imagen(archivo, carpeta='productos')
                    except Exception as e:
                        flash(f'Error al guardar imagen: {str(e)}', 'danger')
                        return render_template('productos/crear.html', categorias=categorias, form_data=form_data)

            nuevo_producto = Producto(
                nombre=datos.nombre,
                descripcion=datos.descripcion,
                precio=datos.precio,
                stock=datos.stock,
                sku=datos.sku,
                categoria_id=datos.categoria_id,
                imagen=imagen_path,
                activo=datos.activo,
                destacado=datos.destacado
            )

            db.session.add(nuevo_producto)
            db.session.commit()

            flash(f'Producto "{nuevo_producto.nombre}" creado exitosamente.', 'success')
            return redirect(url_for('productos.ver', id=nuevo_producto.id))

        except ValidationError as e:
            for error in e.errors():
                campo = error['loc'][0]
                mensaje = error['msg']
                flash(f'{campo}: {mensaje}', 'danger')
            return render_template('productos/crear.html', categorias=categorias, form_data=form_data)

        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('productos/crear.html', categorias=categorias, form_data=form_data)

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear producto: {str(e)}', 'danger')
            return render_template('productos/crear.html', categorias=categorias, form_data=form_data if form_data else request.form.to_dict())

    return render_template('productos/crear.html', categorias=categorias, form_data=None)


@productos_bp.route('/<int:id>/test-editar', methods=['GET', 'POST'])
@vendedor_required
def test_editar(id):
    """PRUEBA SIMPLE - Formulario sin Bootstrap"""
    producto = Producto.query.get_or_404(id)

    if request.method == 'POST':
        print("=" * 50)
        print("TEST EDITAR - RECIBIDO POST")
        print(f"Form data: {request.form.to_dict()}")
        print("=" * 50)

        producto.nombre = request.form.get('nombre')
        producto.precio = Decimal(request.form.get('precio'))
        producto.stock = int(request.form.get('stock'))
        producto.categoria_id = int(request.form.get('categoria_id'))
        producto.sku = request.form.get('sku')
        producto.activo = 'activo' in request.form
        producto.destacado = 'destacado' in request.form

        db.session.commit()

        flash(f'¡FUNCIONA! Producto "{producto.nombre}" actualizado.', 'success')
        return redirect(url_for('productos.ver', id=producto.id))

    return render_template('productos/test_editar.html', producto=producto)


@productos_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@vendedor_required
def editar(id):
    """
    Editar producto existente con actualización de imagen
    Acceso: Vendedor y Admin
    """
    producto = Producto.query.get_or_404(id)
    categorias = Categoria.query.filter_by(activo=True).all()

    if request.method == 'POST':
        try:
            form_data = request.form.to_dict()

            if 'precio' in form_data and form_data['precio']:
                form_data['precio'] = Decimal(form_data['precio'])
            if 'stock' in form_data and form_data['stock']:
                form_data['stock'] = int(form_data['stock'])
            if 'categoria_id' in form_data and form_data['categoria_id']:
                form_data['categoria_id'] = int(form_data['categoria_id'])

            form_data['activo'] = form_data.get('activo') == 'on'
            form_data['destacado'] = form_data.get('destacado') == 'on'

            datos = ProductoUpdateSchema(**form_data)

            if datos.nombre is not None:
                producto.nombre = datos.nombre
            if datos.descripcion is not None:
                producto.descripcion = datos.descripcion
            if datos.precio is not None:
                producto.precio = datos.precio
            if datos.stock is not None:
                producto.stock = datos.stock
            if datos.categoria_id is not None:
                if not Categoria.query.get(datos.categoria_id):
                    flash('La categoría seleccionada no existe.', 'danger')
                    return render_template('productos/editar.html', producto=producto, categorias=categorias)
                producto.categoria_id = datos.categoria_id
            if datos.sku is not None:
                if Producto.query.filter(Producto.sku == datos.sku, Producto.id != id).first():
                    flash(f'El SKU "{datos.sku}" ya está en uso.', 'danger')
                    return render_template('productos/editar.html', producto=producto, categorias=categorias)
                producto.sku = datos.sku
            if datos.activo is not None:
                producto.activo = datos.activo
            if datos.destacado is not None:
                producto.destacado = datos.destacado

            if 'imagen' in request.files:
                archivo = request.files['imagen']
                if archivo and archivo.filename != '':
                    if not validar_tamano_archivo(archivo):
                        flash('La imagen supera el tamaño máximo permitido (16 MB).', 'danger')
                        return render_template('productos/editar.html', producto=producto, categorias=categorias)

                    if not extension_permitida(archivo.filename):
                        flash('Formato de imagen no permitido. Usa: PNG, JPG, JPEG, GIF, WEBP', 'danger')
                        return render_template('productos/editar.html', producto=producto, categorias=categorias)

                    if producto.imagen:
                        eliminar_imagen(producto.imagen)

                    try:
                        imagen_path = guardar_imagen(archivo, carpeta='productos')
                        producto.imagen = imagen_path
                    except Exception as e:
                        flash(f'Error al guardar imagen: {str(e)}', 'danger')
                        return render_template('productos/editar.html', producto=producto, categorias=categorias)

            try:
                db.session.commit()
                flash(f'Producto "{producto.nombre}" actualizado exitosamente.', 'success')
                return redirect(url_for('productos.ver', id=producto.id))
            except Exception as commit_error:
                db.session.rollback()
                flash(f'Error al guardar cambios en la base de datos: {str(commit_error)}', 'danger')
                return render_template('productos/editar.html', producto=producto, categorias=categorias)

        except ValidationError as e:
            db.session.rollback()
            for error in e.errors():
                campo = error['loc'][0]
                mensaje = error['msg']
                flash(f'Error de validación - {campo}: {mensaje}', 'danger')
            return render_template('productos/editar.html', producto=producto, categorias=categorias)

        except ValueError as e:
            db.session.rollback()
            flash(f'Error de valor: {str(e)}', 'danger')
            return render_template('productos/editar.html', producto=producto, categorias=categorias)

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar producto: {str(e)}', 'danger')
            return render_template('productos/editar.html', producto=producto, categorias=categorias)

    return render_template('productos/editar.html', producto=producto, categorias=categorias)


@productos_bp.route('/<int:id>/eliminar', methods=['POST'])
@vendedor_required
def eliminar(id):
    """
    Eliminar producto
    Acceso: Vendedor y Admin
    Nota: Se eliminará la imagen asociada
    """
    producto = Producto.query.get_or_404(id)

    try:
        if producto.detalles_pedido.count() > 0:
            flash(f'No se puede eliminar el producto "{producto.nombre}" porque está asociado a pedidos.', 'warning')
            return redirect(url_for('productos.ver', id=producto.id))

        if producto.imagen:
            eliminar_imagen(producto.imagen)

        nombre = producto.nombre
        db.session.delete(producto)
        db.session.commit()

        flash(f'Producto "{nombre}" eliminado exitosamente.', 'success')
        return redirect(url_for('productos.listar'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar producto: {str(e)}', 'danger')
        return redirect(url_for('productos.ver', id=producto.id))


@productos_bp.route('/<int:id>/eliminar-imagen', methods=['POST'])
@vendedor_required
def eliminar_imagen_producto(id):
    """
    Eliminar solo la imagen del producto
    Acceso: Vendedor y Admin
    """
    producto = Producto.query.get_or_404(id)

    try:
        if not producto.imagen:
            flash('El producto no tiene imagen asociada.', 'info')
            return redirect(url_for('productos.editar', id=producto.id))

        eliminar_imagen(producto.imagen)
        producto.imagen = None
        db.session.commit()

        flash('Imagen eliminada exitosamente.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar imagen: {str(e)}', 'danger')

    return redirect(url_for('productos.editar', id=producto.id))


@productos_bp.route('/<int:id>/toggle-destacado', methods=['POST'])
@vendedor_required
def toggle_destacado(id):
    """
    Marcar/Desmarcar producto como destacado
    Acceso: Vendedor y Admin
    """
    producto = Producto.query.get_or_404(id)

    try:
        producto.destacado = not producto.destacado
        db.session.commit()

        estado = 'destacado' if producto.destacado else 'no destacado'
        flash(f'Producto "{producto.nombre}" marcado como {estado}.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado: {str(e)}', 'danger')

    return redirect(url_for('productos.ver', id=producto.id))
