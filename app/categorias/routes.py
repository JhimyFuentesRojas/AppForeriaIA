"""
Rutas CRUD para Categorías
Incluye: Crear, Leer, Actualizar, Eliminar, Búsqueda y Filtros
"""

from flask import render_template, redirect, url_for, flash, request
from pydantic import ValidationError

from app.categorias import categorias_bp
from app.categorias.schemas import CategoriaCreateSchema, CategoriaUpdateSchema, generar_slug
from app.auth.decorators import vendedor_required
from app.models import Categoria
from app.extensions import db


@categorias_bp.route('/')
def listar():
    """
    Listar todas las categorías con búsqueda y filtros
    Acceso: Público
    """
   
    busqueda = request.args.get('busqueda', '', type=str)
    filtro_activo = request.args.get('activo', 'todos', type=str)
    orden = request.args.get('orden', 'nombre', type=str)

  
    query = Categoria.query


    if busqueda:
        query = query.filter(Categoria.nombre.like(f'%{busqueda}%'))

    if filtro_activo == 'activo':
        query = query.filter_by(activo=True)
    elif filtro_activo == 'inactivo':
        query = query.filter_by(activo=False)


    if orden == 'nombre':
        query = query.order_by(Categoria.nombre.asc())
    elif orden == 'fecha':
        query = query.order_by(Categoria.fecha_creacion.desc())
    elif orden == 'productos':
       
        query = query.outerjoin(Categoria.productos).group_by(Categoria.id).order_by(db.func.count().desc())

    page = request.args.get('page', 1, type=int)
    per_page = 10
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    categorias = pagination.items

    return render_template('categorias/listar.html',
                           categorias=categorias,
                           pagination=pagination,
                           busqueda=busqueda,
                           filtro_activo=filtro_activo,
                           orden=orden)


@categorias_bp.route('/<int:id>')
def ver(id):
    """
    Ver detalle de una categoría
    Acceso: Público
    """
    categoria = Categoria.query.get_or_404(id)
    productos = categoria.productos.filter_by(activo=True).all()

    return render_template('categorias/ver.html',
                           categoria=categoria,
                           productos=productos)


@categorias_bp.route('/crear', methods=['GET', 'POST'])
@vendedor_required
def crear():
    """
    Crear nueva categoría
    Acceso: Vendedor y Admin
    """
    if request.method == 'POST':
        try:

            datos = CategoriaCreateSchema(**request.form.to_dict())

            slug_base = generar_slug(datos.nombre)
            slug = slug_base
            contador = 1

            while Categoria.query.filter_by(slug=slug).first():
                slug = f"{slug_base}-{contador}"
                contador += 1

            nueva_categoria = Categoria(
                nombre=datos.nombre,
                descripcion=datos.descripcion,
                slug=slug,
                activo=datos.activo
            )

            db.session.add(nueva_categoria)
            db.session.commit()

            flash(f'Categoría "{nueva_categoria.nombre}" creada exitosamente.', 'success')
            return redirect(url_for('categorias.ver', id=nueva_categoria.id))

        except ValidationError as e:
            for error in e.errors():
                campo = error['loc'][0]
                mensaje = error['msg']
                flash(f'{campo}: {mensaje}', 'danger')

        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear categoría: {str(e)}', 'danger')

    return render_template('categorias/crear.html')


@categorias_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@vendedor_required
def editar(id):
    """
    Editar categoría existente
    Acceso: Vendedor y Admin
    """
    categoria = Categoria.query.get_or_404(id)

    if request.method == 'POST':
        try:
            datos = CategoriaUpdateSchema(**request.form.to_dict())

            if datos.nombre is not None:
                if datos.nombre != categoria.nombre:
                    slug_base = generar_slug(datos.nombre)
                    slug = slug_base
                    contador = 1

                    while Categoria.query.filter(
                        Categoria.slug == slug,
                        Categoria.id != id
                    ).first():
                        slug = f"{slug_base}-{contador}"
                        contador += 1

                    categoria.slug = slug

                categoria.nombre = datos.nombre

            if datos.descripcion is not None:
                categoria.descripcion = datos.descripcion

            if datos.activo is not None:
                categoria.activo = datos.activo

            db.session.commit()

            flash(f'Categoría "{categoria.nombre}" actualizada exitosamente.', 'success')
            return redirect(url_for('categorias.ver', id=categoria.id))

        except ValidationError as e:
            for error in e.errors():
                campo = error['loc'][0]
                mensaje = error['msg']
                flash(f'{campo}: {mensaje}', 'danger')

        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar categoría: {str(e)}', 'danger')

    return render_template('categorias/editar.html', categoria=categoria)


@categorias_bp.route('/<int:id>/eliminar', methods=['POST'])
@vendedor_required
def eliminar(id):
    """
    Eliminar categoría
    Acceso: Vendedor y Admin
    Nota: Solo se puede eliminar si no tiene productos asociados
    """
    categoria = Categoria.query.get_or_404(id)

    try:
        if categoria.productos.count() > 0:
            flash(f'No se puede eliminar la categoría "{categoria.nombre}" porque tiene {categoria.productos.count()} productos asociados.', 'warning')
            return redirect(url_for('categorias.ver', id=categoria.id))

        nombre = categoria.nombre
        db.session.delete(categoria)
        db.session.commit()

        flash(f'Categoría "{nombre}" eliminada exitosamente.', 'success')
        return redirect(url_for('categorias.listar'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar categoría: {str(e)}', 'danger')
        return redirect(url_for('categorias.ver', id=categoria.id))


@categorias_bp.route('/<int:id>/toggle-activo', methods=['POST'])
@vendedor_required
def toggle_activo(id):
    """
    Activar/Desactivar categoría
    Acceso: Vendedor y Admin
    """
    categoria = Categoria.query.get_or_404(id)

    try:
        categoria.activo = not categoria.activo
        db.session.commit()

        estado = 'activada' if categoria.activo else 'desactivada'
        flash(f'Categoría "{categoria.nombre}" {estado} exitosamente.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar estado: {str(e)}', 'danger')

    return redirect(url_for('categorias.ver', id=categoria.id))
