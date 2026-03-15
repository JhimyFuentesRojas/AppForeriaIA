"""Servicio de Análisis para el Dashboard Inteligente del Administrador"""

from app.models import Producto, Categoria, Pedido, DetallePedido
from app.extensions import db
from app.services.ai_service import ai_service
from sqlalchemy import func, desc
from datetime import datetime, date, timedelta

class AnalyticsService:

    @staticmethod
    def obtener_kpis():
        """Obtiene los Indicadores Clave de Rendimiento (KPIs) para mostrar en el dashboard"""
        hoy = date.today()
        
        total_productos = Producto.query.count()
        
        # Obtener ventas totales históricas (pedidos completados)
        ventas_totales = db.session.query(func.sum(Pedido.total)).filter(Pedido.estado == 'completado').scalar() or 0
        
        # Obtener pedidos del día
        pedidos_hoy = Pedido.query.filter(func.date(Pedido.fecha_pedido) == hoy).count()
        
        # Obtener productos con bajo stock (< 5)
        productos_bajo_stock = Producto.query.filter(Producto.stock < 5).count()
        
        return {
            'total_productos': total_productos,
            'ventas_totales': float(ventas_totales),
            'pedidos_hoy': pedidos_hoy,
            'productos_bajo_stock': productos_bajo_stock
        }
        
    @staticmethod
    def obtener_productos_mas_vendidos(limite=5):
        """Obtiene los productos más vendidos históricamente"""
        resultados = db.session.query(
            Producto.nombre,
            func.sum(DetallePedido.cantidad).label('total_vendido')
        ).join(
            DetallePedido, Producto.id == DetallePedido.producto_id
        ).group_by(
            Producto.id
        ).order_by(
            desc('total_vendido')
        ).limit(limite).all()
        
        return [{'nombre': r[0], 'cantidad': int(r[1])} for r in resultados]

    @staticmethod
    def obtener_categorias_populares():
        """Obtiene la distribución de ventas por categoría para el gráfico"""
        resultados = db.session.query(
            Categoria.nombre,
            func.sum(DetallePedido.cantidad).label('total_vendido')
        ).join(
            Producto, Categoria.id == Producto.categoria_id
        ).join(
            DetallePedido, Producto.id == DetallePedido.producto_id
        ).group_by(
            Categoria.id
        ).order_by(
            desc('total_vendido')
        ).all()
        
        total_general = sum(r[1] for r in resultados) if resultados else 0
        
        datos = []
        for r in resultados:
            porcentaje = round((r[1] / total_general * 100), 2) if total_general > 0 else 0
            datos.append({
                'nombre': r[0],
                'cantidad': int(r[1]),
                'porcentaje': porcentaje
            })
            
        return datos

    @staticmethod
    def obtener_productos_alertas_stock():
        """Lista detallada de productos que requieren reposición"""
        productos = Producto.query.filter(Producto.stock < 10).order_by(Producto.stock).all()
        return [{
            'id': p.id,
            'nombre': p.nombre,
            'stock': p.stock,
            'precio': float(p.precio)
        } for p in productos]

    @classmethod
    def generar_resumen_ia(cls):
        """Genera un análisis narrativo inteligente del estado del negocio usando Groq"""
        kpis = cls.obtener_kpis()
        mas_vendidos = cls.obtener_productos_mas_vendidos(3)
        cat_populares = cls.obtener_categorias_populares()
        alertas_stock = cls.obtener_productos_alertas_stock()
        
        contexto = "DATOS DEL DASHBOARD PARA ANÁLISIS:\n"
        contexto += f"- Ventas totales históricas: ${kpis['ventas_totales']}\n"
        contexto += f"- Pedidos realizados hoy: {kpis['pedidos_hoy']}\n\n"
        
        contexto += "TOP 3 PRODUCTOS MÁS VENDIDOS:\n"
        for p in mas_vendidos:
            contexto += f"- {p['nombre']}: {p['cantidad']} unidades\n"
            
        contexto += "\nCATEGORÍAS MÁS POPULARES:\n"
        for c in cat_populares[:3]:
            contexto += f"- {c['nombre']}: {c['porcentaje']}%\n"
            
        contexto += "\nALERTAS DE STOCK (QUEDAN POCOS):\n"
        if alertas_stock:
            for p in alertas_stock[:5]:
                contexto += f"- {p['nombre']}: solo quedan {p['stock']} unidades\n"
        else:
            contexto += "- Todo el inventario tiene niveles saludables de stock.\n"
            
        prompt = """
        Eres un analista de datos experto especializado en ventas de florerías.
        Toma los datos proporcionados y genera un breve párrafo (3-4 oraciones máximo) 
        resumiendo el rendimiento del negocio. 
        Menciona específicamente el producto más vendido, la categoría líder y lanza una advertencia 
        de stock si es necesario. Tu tono debe ser profesional y directo.
        
        Ejemplo de formato esperado: "El producto más vendido es X con Y ventas, liderado por la categoría de Z 
        que representa el W% de participación. Las ventas totales se mantienen en $V.
        Sin embargo, sugerimos reabastecer el producto P ya que su stock está por debajo del nivel óptimo."
        """
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": contexto}
        ]
        
        return ai_service.obtener_respuesta(messages, temperature=0.5)
