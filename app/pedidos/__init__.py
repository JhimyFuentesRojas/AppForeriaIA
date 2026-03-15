"""
Módulo de Pedidos/Ventas - CRUD Completo
Integrante 3: [Nombre del estudiante]
Rama: modulo-pedidos-nombre_estudiante
"""

from flask import Blueprint

pedidos_bp = Blueprint('pedidos', __name__)

from app.pedidos import routes
