"""
Sistema de Florería - Ventas de Flores y Plantas
Desarrollado con Flask, SQLAlchemy, Pydantic y MySQL
"""

from app import create_app
from app.extensions import db
from app.models import Usuario, Categoria, Producto, Pedido, DetallePedido

app = create_app('development')

@app.shell_context_processor
def make_shell_context():
    """Agregar modelos al contexto de Flask shell"""
    return {
        'db': db,
        'Usuario': Usuario,
        'Categoria': Categoria,
        'Producto': Producto,
        'Pedido': Pedido,
        'DetallePedido': DetallePedido
    }


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
