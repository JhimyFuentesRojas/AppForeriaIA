"""Servicio de Chatbot para clientes y administradores"""

from app.models import Producto, Categoria, Pedido, DetallePedido
from app.services.ai_service import ai_service
from sqlalchemy import func
from datetime import datetime, date

class ChatbotService:
    
    @staticmethod
    def _obtener_contexto_cliente():
        """Obtiene datos relevantes de la BD para responder a clientes"""
        # Obtenemos productos activos con stock
        productos = Producto.query.filter_by(activo=True).filter(Producto.stock > 0).all()
        # Obtenemos todas las categorías activas
        categorias = Categoria.query.filter_by(activo=True).all()
        
        contexto = "DATOS ACTUALES DE LA FLORERÍA:\n\n"
        
        contexto += "CATEGORÍAS DISPONIBLES:\n"
        for cat in categorias:
            contexto += f"- {cat.nombre}: {cat.descripcion}\n"
            
        contexto += "\nPRODUCTOS DISPONIBLES EN STOCK (con precios e imágenes):\n"
        for prod in productos:
            cat_nombre = prod.categoria.nombre if prod.categoria else "Sin categoría"
            img = prod.imagen if prod.imagen else ""
            contexto += f"- ID:{prod.id} | {prod.nombre} (Categoría: {cat_nombre}) | Precio: ${prod.precio} | Stock: {prod.stock} | Desc: {prod.descripcion} | Img: {img}\n"
            
        contexto += "\nREGLAS DE RESPUESTA (MODO CLIENTE) - MUY IMPORTANTE:\n"
        contexto += "1. Eres un asistente virtual, NO PUEDES añadir productos al carrito por tu cuenta. Solo debes sugerir productos.\n"
        contexto += "2. DEBES responder SIEMPRE con un objeto JSON válido y estrictamente con estas 2 claves: 'mensaje' y 'productos'.\n"
        contexto += "3. La clave 'mensaje' debe contener tu respuesta, recomendaciones atractivas o ayuda en texto plano.\n"
        contexto += "4. La clave 'productos' DEBE ser siempre una lista []. Si recomiendas productos reales de la base de datos, llena esta lista con objetos con este formato exacto:\n"
        contexto += '   {"id": 1, "nombre": "Rosas", "precio": 25.0, "stock": 10, "imagen": "/static/uploads/rosas.jpg"}\n'
        contexto += "5. Usa las propiedades exactas de ID, precio, stock e imagen que te presenté en DATOS ACTUALES. Asegúrate de incluir la ruta de la imagen exactamente como se mostró en la fuente.\n"
        contexto += "6. NUNCA digas que añadiste productos al carrito. Si el usuario pide comprar, dile que use el botón 'Añadir al carrito' que aparece en las tarjetas de productos.\n"
        
        return contexto

    @staticmethod
    def _obtener_contexto_admin():
        """Obtiene datos estadísticos de la BD para responder a administradores"""
        
        hoy = date.today()
        
        # Total de productos y categorías
        total_productos = Producto.query.count()
        total_categorias = Categoria.query.count()
        
        # Productos con bajo stock (< 5)
        bajo_stock = Producto.query.filter(Producto.stock < 5).all()
        
        # Pedidos de hoy
        pedidos_hoy = Pedido.query.filter(func.date(Pedido.fecha_pedido) == hoy).all()
        total_ventas_hoy = sum(p.total for p in pedidos_hoy)
        
        contexto = "DATOS ESTADÍSTICOS DE LA FLORERÍA (PANEL DE ADMINISTRACIÓN):\n\n"
        contexto += f"- Total de productos registrados: {total_productos}\n"
        contexto += f"- Total de categorías: {total_categorias}\n"
        contexto += f"- Pedidos realizados hoy ({hoy}): {len(pedidos_hoy)}\n"
        contexto += f"- Total vendido hoy: ${total_ventas_hoy}\n\n"
        
        contexto += "PRODUCTOS CON BAJO STOCK O AGOTADOS:\n"
        if bajo_stock:
            for p in bajo_stock:
                contexto += f"- ID:{p.id} | {p.nombre} (Stock actual: {p.stock}, Precio: ${p.precio})\n"
        else:
            contexto += "- Todos los productos tienen buen nivel de stock (5 o más).\n"
            
        contexto += "\nREGLAS DE RESPUESTA PARA ADMIN:\n"
        contexto += "1. DEBES responder SIEMPRE con un objeto JSON válido.\n"
        contexto += "2. El JSON debe tener esta estructura obligatoria:\n"
        contexto += '   {"mensaje": "Tu respuesta verbal como asistente admin", "accion_requerida": "ninguna", "parametros_accion": {}}\n'
        contexto += "3. Si el admin te pide CREAR un nuevo producto, y ya te proporcionó toda la información (nombre, precio, stock, descripción, categoría), establece:\n"
        contexto += '   "accion_requerida": "crear_producto"\n'
        contexto += '   Y en "parametros_accion" incluye: "nombre", "precio", "stock" (entero), "descripcion", "categoria_slug" (como "romantico" o "cumpleaños").\n'
        contexto += "   Si NO te ha dado toda la información, pide educadamente los datos faltantes en tu 'mensaje' y mantén 'accion_requerida': 'ninguna'.\n"
        contexto += "4. Si el admin pide ACTUALIZAR STOCK de un producto, establece:\n"
        contexto += '   "accion_requerida": "actualizar_stock"\n'
        contexto += '   Y en "parametros_accion" incluye: "nombre" o "id" del producto, y "nuevo_stock" (entero).\n'
        
        return contexto

    @classmethod
    def procesar_mensaje_cliente(cls, pregunta, historial=None):
        """Procesa una pregunta de un cliente y devuelve la respuesta generada por IA en JSON"""
        if historial is None:
            historial = []
            
        contexto = cls._obtener_contexto_cliente()
        
        messages = [
            {"role": "system", "content": "Eres el asistente virtual oficial de nuestra florería en línea. Responde exclusivamente en formato JSON."}
        ]
        
        messages.append({"role": "system", "content": contexto})
        
        # Filtramos mensajes de historial para asegurarnos que todos sean serializables
        for msg in historial[-5:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        messages.append({"role": "user", "content": pregunta})
        
        respuesta = ai_service.obtener_respuesta(messages, response_format={"type": "json_object"})
        
        # Si la API falla, puede retornar un string de error. Intentaremos que sea parseable.
        return respuesta

    @classmethod
    def procesar_mensaje_admin(cls, pregunta, historial=None):
        """Procesa una pregunta del administrador y devuelve la respuesta generada por IA en JSON"""
        if historial is None:
            historial = []
            
        contexto = cls._obtener_contexto_admin()
        
        messages = [
            {"role": "system", "content": "Eres el asistente administrativo de la florería. Debes responder SOLO en formato JSON estructurado."}
        ]
        
        messages.append({"role": "system", "content": contexto})
        
        for msg in historial[-5:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
            
        messages.append({"role": "user", "content": pregunta})
        
        respuesta = ai_service.obtener_respuesta(messages, response_format={"type": "json_object"})
        
        return respuesta
