"""
Módulo de Productos - CRUD Completo con Subida de Imágenes
Integrante 2: [Nombre del estudiante]
Rama: modulo-productos-nombre_estudiante
"""

from flask import Blueprint

productos_bp = Blueprint('productos', __name__)

from app.productos import routes
