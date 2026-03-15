"""
Módulo de Categorías - CRUD Completo
Integrante 1: [Nombre del estudiante]
Rama: modulo-categorias-nombre_estudiante
"""

from flask import Blueprint

categorias_bp = Blueprint('categorias', __name__)

from app.categorias import routes
