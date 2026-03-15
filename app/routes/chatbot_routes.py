"""Rutas para el Chatbot Inteligente"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.services.chatbot_service import ChatbotService
from app.auth.decorators import admin_required

from app.extensions import db
from app.models import ChatMensaje

chatbot_bp = Blueprint('chatbot', __name__)

@chatbot_bp.route('/api/chatbot/history', methods=['GET'])
@login_required
def obtener_historial():
    """Endpoint para obtener el historial de chat del usuario actual"""
    try:
        tipo_chat = request.args.get('tipo', 'cliente')
        # Verificar permisos si pide admin
        if tipo_chat == 'admin' and not current_user.is_admin():
            return jsonify({'error': 'No autorizado'}), 403
            
        mensajes = ChatMensaje.query.filter_by(
            usuario_id=current_user.id,
            tipo_chat=tipo_chat
        ).order_by(ChatMensaje.fecha.asc()).all()
        
        historial = []
        for msg in mensajes:
            historial.append({'role': 'user', 'content': msg.mensaje})
            historial.append({'role': 'assistant', 'content': msg.respuesta})
            
        return jsonify(historial)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chatbot_bp.route('/api/chatbot', methods=['POST'])
@login_required
def chat_cliente():
    """Endpoint para el chatbot de clientes"""
    try:
        data = request.get_json()
        if not data or 'pregunta' not in data:
            return jsonify({'error': 'La pregunta es requerida'}), 400
            
        pregunta = data['pregunta']
        historial = data.get('historial', [])
        
        # Procesar con IA
        respuesta_ia_raw = ChatbotService.procesar_mensaje_cliente(pregunta, historial)
        
        try:
            respuesta_json = json.loads(respuesta_ia_raw)
            respuesta_final = respuesta_json
        except json.JSONDecodeError:
            # Fallback
            respuesta_final = {"mensaje": respuesta_ia_raw, "productos_sugeridos": []}
        
        # Guardar en BD
        nuevo_mensaje = ChatMensaje(
            usuario_id=current_user.id,
            rol_usuario=current_user.rol,
            mensaje=pregunta,
            respuesta=json.dumps(respuesta_final),
            tipo_chat='cliente'
        )
        db.session.add(nuevo_mensaje)
        db.session.commit()
        
        return jsonify({'respuesta': respuesta_final})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

from flask import session
from app.tienda.routes import clean_cart_session

@chatbot_bp.route('/api/chatbot/add-to-cart', methods=['POST'])
@login_required
def chatbot_add_to_cart():
    """Endpoint para agregar productos sugeridos al carrito desde el chatbot"""
    try:
        data = request.get_json()
        producto_id = data.get('producto_id')
        cantidad = data.get('cantidad', 1)
        
        if not producto_id:
            return jsonify({'success': False, 'message': 'ID de producto requerido'}), 400
            
        producto = Producto.query.get_or_404(producto_id)
        
        if not producto.activo or producto.stock < cantidad:
            return jsonify({'success': False, 'message': 'Stock insuficiente o producto inactivo'}), 400
            
        # Reutilizar lógica segura de sesión del carrito
        carrito = clean_cart_session()
        producto_key = str(producto.id)
        
        if producto_key in carrito:
            carrito[producto_key]['cantidad'] += cantidad
        else:
            carrito[producto_key] = {
                'producto_id': producto.id,
                'nombre': producto.nombre,
                'precio': float(producto.precio),
                'imagen': producto.imagen,
                'cantidad': cantidad,
                'stock': producto.stock
            }
            
        session['carrito'] = carrito
        session.modified = True
        
        items_carrito = sum(item.get('cantidad', 0) for item in carrito.values())
        
        return jsonify({
            'success': True, 
            'message': f'¡Agregaste {producto.nombre} a tu carrito!', 
            'items_carrito': items_carrito
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


import json
from decimal import Decimal
from app.models import Producto, Categoria

@chatbot_bp.route('/api/admin/chatbot', methods=['POST'])
@admin_required
def chat_admin():
    """Endpoint para el chatbot del administrador"""
    try:
        data = request.get_json()
        if not data or 'pregunta' not in data:
            return jsonify({'error': 'La pregunta es requerida'}), 400
            
        pregunta = data['pregunta']
        historial = data.get('historial', [])
        
        # Procesar con IA
        respuesta_ia_raw = ChatbotService.procesar_mensaje_admin(pregunta, historial)
        
        try:
            respuesta_json = json.loads(respuesta_ia_raw)
            accion = respuesta_json.get('accion_requerida', 'ninguna')
            params = respuesta_json.get('parametros_accion', {})
            
            # Ejecutar acción si aplica
            if accion == 'crear_producto':
                cat = Categoria.query.filter_by(slug=params.get('categoria_slug')).first()
                if not cat:
                    cat = Categoria.query.first() # Failsafe
                
                nuevo_prod = Producto(
                    nombre=params.get('nombre'),
                    precio=Decimal(str(params.get('precio', 0))),
                    stock=int(params.get('stock', 0)),
                    descripcion=params.get('descripcion', ''),
                    categoria_id=cat.id if cat else 1,
                    activo=True
                )
                db.session.add(nuevo_prod)
                db.session.commit()
                respuesta_json['mensaje'] += f"\n\n¡Hecho! Se insertó el producto '{nuevo_prod.nombre}' en base de datos."
                
            elif accion == 'actualizar_stock':
                prod_nombre = params.get('nombre')
                nuevo_stock = int(params.get('nuevo_stock', 0))
                prod = Producto.query.filter(Producto.nombre.ilike(f"%{prod_nombre}%")).first()
                if prod:
                    prod.stock = nuevo_stock
                    db.session.commit()
                    respuesta_json['mensaje'] += f"\n\n¡Hecho! El stock de '{prod.nombre}' se actualizó a {nuevo_stock}."
                else:
                    respuesta_json['mensaje'] += f"\n\n(No encontré el producto '{prod_nombre}' para actualizarlo)."
                    
            respuesta_final = respuesta_json
            
        except json.JSONDecodeError:
            # Fallback en caso de que la IA alucine y no devuelva JSON
            respuesta_final = {"mensaje": respuesta_ia_raw}
        
        nuevo_mensaje = ChatMensaje(
            usuario_id=current_user.id,
            rol_usuario=current_user.rol,
            mensaje=pregunta,
            respuesta=json.dumps(respuesta_final),
            tipo_chat='admin'
        )
        db.session.add(nuevo_mensaje)
        db.session.commit()
        
        return jsonify({'respuesta': respuesta_final})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
