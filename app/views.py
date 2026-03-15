"""Vistas principales de la aplicación"""

from flask import Blueprint, render_template
from app.models import Producto, Categoria

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Página principal - Mostrar productos destacados"""
    productos_destacados = Producto.query.filter_by(activo=True, destacado=True).limit(8).all()
    categorias = Categoria.query.filter_by(activo=True).all()

    return render_template('index.html',
                           productos=productos_destacados,
                           categorias=categorias)


@main_bp.route('/about')
def about():
    """Página acerca de"""
    return render_template('about.html')
