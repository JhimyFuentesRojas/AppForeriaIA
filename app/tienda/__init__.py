"""
Módulo de Tienda - Vista de E-commerce con Carrito
Vista profesional con filtros laterales y carrito de compras
"""

from flask import Blueprint

tienda_bp = Blueprint('tienda', __name__, url_prefix='/tienda')

from app.tienda import routes
