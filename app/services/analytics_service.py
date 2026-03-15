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

    @staticmethod
    def obtener_productos_sin_ventas():
        """Productos activos que nunca han sido vendidos."""
        vendidos_ids = db.session.query(DetallePedido.producto_id).distinct()
        productos = Producto.query.filter(
            Producto.activo == True,
            ~Producto.id.in_(vendidos_ids)
        ).all()
        return [{'nombre': p.nombre, 'stock': p.stock, 'precio': float(p.precio)} for p in productos]

    @staticmethod
    def obtener_ventas_por_producto():
        """Ventas totales por producto (todos, no solo top 5)."""
        resultados = db.session.query(
            Producto.nombre,
            func.sum(DetallePedido.cantidad).label('total_vendido'),
            func.sum(DetallePedido.subtotal).label('ingresos')
        ).join(
            DetallePedido, Producto.id == DetallePedido.producto_id
        ).group_by(
            Producto.id
        ).order_by(
            desc('total_vendido')
        ).all()
        return [{'nombre': r[0], 'cantidad': int(r[1]), 'ingresos': float(r[2])} for r in resultados]

    @classmethod
    def generar_analisis_completo_para_reporte(cls):
        """
        Genera un análisis ejecutivo detallado con recomendaciones de negocio concretas.
        Devuelve un dict con: resumen, recomendaciones (lista), conclusion.
        """
        kpis          = cls.obtener_kpis()
        mas_vendidos  = cls.obtener_productos_mas_vendidos(5)
        categorias    = cls.obtener_categorias_populares()
        alertas_stock = cls.obtener_productos_alertas_stock()
        sin_ventas    = cls.obtener_productos_sin_ventas()
        todos_prod    = cls.obtener_ventas_por_producto()

        vendidos_nombres = {p['nombre'] for p in todos_prod}
        cat_top   = categorias[:2]  if categorias else []
        cat_bajas = categorias[-2:] if len(categorias) > 2 else []

        # Productos populares con stock bajo (sí se venden Y tienen poco stock)
        alertas_populares = [
            p for p in alertas_stock if p['nombre'] in vendidos_nombres
        ]

        contexto  = f"Ventas totales: ${kpis['ventas_totales']:,.2f}\n"
        contexto += f"Pedidos hoy: {kpis['pedidos_hoy']}\n\n"

        contexto += "PRODUCTOS VENDIDOS (ranking por unidades):\n"
        for p in todos_prod:
            contexto += f"  {p['nombre']}: {p['cantidad']} uds vendidas, ${p['ingresos']:,.2f}\n"

        if sin_ventas:
            contexto += "\nPRODUCTOS SIN NINGUNA VENTA — ACCION REQUERIDA: promocion, descuento o combo (NO reponer):\n"
            for p in sin_ventas:
                contexto += f"  {p['nombre']}: {p['stock']} uds en stock sin vender\n"

        if alertas_populares:
            contexto += "\nPRODUCTOS POPULARES CON POCO STOCK — ACCION REQUERIDA: reponer urgente:\n"
            for p in alertas_populares:
                nivel = "AGOTADO" if p['stock'] == 0 else f"{p['stock']} uds restantes"
                contexto += f"  {p['nombre']}: {nivel}\n"

        contexto += "\nCATEGORIAS MAS VENDIDAS (lideres):\n"
        for c in cat_top:
            contexto += f"  {c['nombre']}: {c['porcentaje']}% participacion, {c['cantidad']} uds\n"

        if cat_bajas:
            contexto += "\nCATEGORIAS CON MENOR PARTICIPACION — ACCION REQUERIDA: estrategia para impulsar:\n"
            for c in cat_bajas:
                contexto += f"  {c['nombre']}: {c['porcentaje']}% participacion, {c['cantidad']} uds\n"

        prompt = """Eres consultor de una floreria. Responde en espanol, sin markdown, sin asteriscos, solo texto plano.
Usa este formato exacto:

RESUMEN:
[2-3 oraciones: producto estrella, categoria lider, ventas totales, menciona si hay categorias con poca participacion]

RECOMENDACIONES:
1. Titulo corto: explicacion de 1-2 oraciones con nombres exactos de productos.
2. Titulo corto: explicacion.
3. Titulo corto: explicacion.
4. Titulo corto: explicacion.

CONCLUSION:
[1-2 oraciones con la accion mas urgente]

El contexto ya indica la accion correcta para cada producto y categoria. Respetala al pie de la letra:
- Si dice ACCION: promocion/descuento/combo -> usa esa accion, nunca sugieras reponer ese producto.
- Si dice ACCION: reponer urgente -> recomienda reposicion con cantidad concreta.
- Si dice ACCION: estrategia para impulsar -> sugiere bundle, descuento de categoria o showcase."""

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user",   "content": contexto},
        ]
        respuesta = ai_service.obtener_respuesta(messages, temperature=0.6)
        return _parsear_analisis(respuesta)

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


def _parsear_analisis(texto):
    """
    Parsea la respuesta estructurada de Groq en secciones.
    Devuelve dict con claves: resumen, recomendaciones (list of dicts), conclusion.
    Si el formato no se detecta, todo va al resumen.
    """
    resultado = {'resumen': '', 'recomendaciones': [], 'conclusion': ''}
    if not texto:
        return resultado

    import re
    seccion_actual = None
    buffer = []

    for linea in texto.splitlines():
        l = linea.strip()
        if re.match(r'^RESUMEN\s*:', l, re.IGNORECASE):
            seccion_actual = 'resumen'
            resto = re.sub(r'^RESUMEN\s*:', '', l, flags=re.IGNORECASE).strip()
            if resto:
                buffer = [resto]
            else:
                buffer = []
        elif re.match(r'^RECOMENDACIONES\s*:', l, re.IGNORECASE):
            if seccion_actual == 'resumen':
                resultado['resumen'] = ' '.join(buffer).strip()
            seccion_actual = 'recomendaciones'
            buffer = []
        elif re.match(r'^CONCLUSI[ÓO]N\s*:', l, re.IGNORECASE):
            if seccion_actual == 'recomendaciones':
                _flush_recomendaciones(buffer, resultado)
            seccion_actual = 'conclusion'
            resto = re.sub(r'^CONCLUSI[ÓO]N\s*:', '', l, flags=re.IGNORECASE).strip()
            buffer = [resto] if resto else []
        else:
            if l:
                buffer.append(l)

    # Vaciar último buffer
    if seccion_actual == 'resumen':
        resultado['resumen'] = ' '.join(buffer).strip()
    elif seccion_actual == 'recomendaciones':
        _flush_recomendaciones(buffer, resultado)
    elif seccion_actual == 'conclusion':
        resultado['conclusion'] = ' '.join(buffer).strip()

    # Fallback: si no se pudo parsear, poner todo en resumen
    if not resultado['resumen'] and not resultado['recomendaciones']:
        resultado['resumen'] = texto.strip()

    return resultado


def _flush_recomendaciones(buffer, resultado):
    import re
    rec_actual = None
    for linea in buffer:
        m = re.match(r'^(\d+)\.\s*([^:]+):\s*(.*)', linea)
        if m:
            if rec_actual:
                resultado['recomendaciones'].append(rec_actual)
            rec_actual = {'titulo': m.group(2).strip(), 'detalle': m.group(3).strip()}
        elif rec_actual:
            rec_actual['detalle'] += ' ' + linea.strip()
    if rec_actual:
        resultado['recomendaciones'].append(rec_actual)
