"""Modelos de base de datos para el Sistema de Florería"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db


class Usuario(UserMixin, db.Model):
    """Modelo de Usuario con roles (admin, vendedor, cliente)"""
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nombre_completo = db.Column(db.String(200), nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.Text)

    rol = db.Column(db.String(20), nullable=False, default='cliente')

    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_conexion = db.Column(db.DateTime)

    pedidos = db.relationship('Pedido', backref='cliente', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hashear y establecer contraseña"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verificar contraseña"""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Verificar si el usuario es administrador"""
        return self.rol == 'admin'

    def is_vendedor(self):
        """Verificar si el usuario es vendedor"""
        return self.rol in ['admin', 'vendedor']

    def __repr__(self):
        return f'<Usuario {self.username} - {self.rol}>'


class Categoria(db.Model):
    """Modelo de Categoría de productos (flores/plantas)"""
    __tablename__ = 'categorias'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False, index=True)
    descripcion = db.Column(db.Text)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    productos = db.relationship('Producto', backref='categoria', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Categoria {self.nombre}>'


class Producto(db.Model):
    """Modelo de Producto (flores, plantas, arreglos)"""
    __tablename__ = 'productos'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False, index=True)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    imagen = db.Column(db.String(255))  
    sku = db.Column(db.String(50), unique=True, index=True)

    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)

    activo = db.Column(db.Boolean, default=True)
    destacado = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    detalles_pedido = db.relationship('DetallePedido', backref='producto', lazy='dynamic')

    @property
    def stock_disponible(self):
        """Verificar si hay stock disponible"""
        return self.stock > 0

    def reducir_stock(self, cantidad):
        """Reducir stock del producto"""
        if self.stock >= cantidad:
            self.stock -= cantidad
            return True
        return False

    def __repr__(self):
        return f'<Producto {self.nombre} - ${self.precio}>'


class Pedido(db.Model):
    """Modelo de Pedido/Venta"""
    __tablename__ = 'pedidos'

    id = db.Column(db.Integer, primary_key=True)
    numero_pedido = db.Column(db.String(50), unique=True, nullable=False, index=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    estado = db.Column(db.String(20), default='completado')

    subtotal = db.Column(db.Numeric(10, 2), default=0.00)
    total = db.Column(db.Numeric(10, 2), default=0.00)

    direccion_entrega = db.Column(db.Text, nullable=False)
    telefono_contacto = db.Column(db.String(20))
    notas = db.Column(db.Text)

    fecha_pedido = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_entrega = db.Column(db.DateTime)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    detalles = db.relationship('DetallePedido', backref='pedido', lazy='dynamic', cascade='all, delete-orphan')

    def calcular_total(self):
        """Calcular el total del pedido"""
        self.subtotal = sum(detalle.subtotal for detalle in self.detalles)
        self.total = self.subtotal
        return self.total

    def __repr__(self):
        return f'<Pedido {self.numero_pedido} - {self.estado}>'


class DetallePedido(db.Model):
    """Modelo de Detalle de Pedido (items del pedido)"""
    __tablename__ = 'detalles_pedido'

    id = db.Column(db.Integer, primary_key=True)

    pedido_id = db.Column(db.Integer, db.ForeignKey('pedidos.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)

    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    def calcular_subtotal(self):
        """Calcular subtotal del detalle"""
        self.subtotal = self.cantidad * self.precio_unitario
        return self.subtotal

    def __repr__(self):
        return f'<DetallePedido Pedido:{self.pedido_id} Producto:{self.producto_id}>'

class ChatMensaje(db.Model):
    """Modelo de Historial de Chatbot"""
    __tablename__ = 'chat_mensajes'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    rol_usuario = db.Column(db.String(20), nullable=False) # 'cliente' o 'admin'
    mensaje = db.Column(db.Text, nullable=False)
    respuesta = db.Column(db.Text, nullable=False)
    tipo_chat = db.Column(db.String(20), nullable=False) # Contexto 'cliente' o 'admin'
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario', backref=db.backref('mensajes_chat', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<ChatMensaje {self.id} - Usuario:{self.usuario_id}>'
