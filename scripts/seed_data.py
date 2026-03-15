"""Script para insertar datos completos de prueba a la BD para validar Chatbot y Dashboard"""

import os
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime, date, timedelta
import random

# Agregar el directorio raíz al path para importar la app
basedir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(basedir))

from app import create_app
from app.extensions import db
from app.models import Usuario, Categoria, Producto, Pedido, DetallePedido

def seed_db():
    app = create_app('development')
    
    with app.app_context():
        print("Iniciando inserción masiva de datos de prueba...")
        
        # 1. Crear clientes de prueba si no existen
        clientes_data = [
            {'username': 'cliente1', 'email': 'cliente1@test.com', 'nombre': 'María López'},
            {'username': 'cliente2', 'email': 'cliente2@test.com', 'nombre': 'Juan Pérez'}
        ]
        
        usuarios_creados = {}
        for c in clientes_data:
            user = Usuario.query.filter_by(username=c['username']).first()
            if not user:
                user = Usuario(
                    username=c['username'],
                    email=c['email'],
                    nombre_completo=c['nombre'],
                    rol='cliente'
                )
                user.set_password('123456')
                db.session.add(user)
                print(f"  - Cliente creado: {c['username']}")
            usuarios_creados[c['username']] = user
            
        db.session.flush()

        # 2. Obtener o crear categorías base
        cats = ['romantico', 'cumpleaños', 'decoracion', 'condolencias']
        # Los guardamos en diccionario con IDs 
        cat_ids = {}
        
        for c_slug in cats:
            cat = Categoria.query.filter_by(slug=c_slug).first()
            if not cat:
                nombre = c_slug.capitalize().replace('-', ' ')
                cat = Categoria(nombre=nombre, slug=c_slug, descripcion=f"Flores para {nombre}")
                db.session.add(cat)
                db.session.flush()
                print(f"  - Categoría nueva: {nombre}")
            cat_ids[c_slug] = cat.id

        # 3. Crear productos si no existen (Requisito: Rosas Rojas, Tulipanes, Girasoles, Orquideas, Lirios)
        prods_data = [
            {
                'nombre': 'Rosas Rojas Premium', 'precio': '300.50', 'stock': 35, 
                'sku': 'ROS-PREM-001-', 'cat': 'romantico', 'desc': 'Docena de rosas rojas de tallo largo.'
            },
            {
                'nombre': 'Tulipanes Holandeses', 'precio': '450.00', 'stock': 2, # Bajo stock a propósito
                'sku': 'TUL-HOL-001-', 'cat': 'romantico', 'desc': 'Hermosos tulipanes frescos multicolor.'
            },
            {
                'nombre': 'Arreglo Girasoles Sol', 'precio': '280.00', 'stock': 15, 
                'sku': 'GIR-SOL-001-', 'cat': 'cumpleaños', 'desc': 'Arreglo vibrante con 5 girasoles grandes.'
            },
            {
                'nombre': 'Orquídeas Phalaenopsis', 'precio': '650.00', 'stock': 8, 
                'sku': 'ORQ-PHA-001-', 'cat': 'decoracion', 'desc': 'Planta de orquídea en base de cerámica.'
            },
            {
                'nombre': 'Ramo de Lirios Blancos', 'precio': '320.00', 'stock': 20, 
                'sku': 'LIR-BLA-001-', 'cat': 'condolencias', 'desc': 'Lirios blancos elegantes.'
            }
        ]
        
        productos_creados = {}
        hoy_str = datetime.now().strftime("%H%M%S") # Para SKUs unicos si hay colision
        
        for p in prods_data:
            sku_real = p['sku'] + hoy_str
            # Buscar por nombre para no duplicar exactos
            prod = Producto.query.filter_by(nombre=p['nombre']).first()
            if not prod:
                prod = Producto(
                    nombre=p['nombre'],
                    descripcion=p['desc'],
                    precio=Decimal(p['precio']),
                    stock=p['stock'],
                    sku=sku_real,
                    categoria_id=cat_ids[p['cat']],
                    activo=True
                )
                db.session.add(prod)
                print(f"  - Producto creado: {p['nombre']}")
            # Siempre guardar referencia para ventas
            productos_creados[p['nombre']] = prod
            
        db.session.flush()

        # 4. Crear pedidos históricos (Simulación de ventas para los gráficos)
        id_cliente = usuarios_creados['cliente1'].id
        
        # Pedidos del mes pasado y este mes
        fechas_pedidos = [
            datetime.now() - timedelta(days=20),
            datetime.now() - timedelta(days=15),
            datetime.now() - timedelta(days=5),
            datetime.now(), # Hoy
            datetime.now()  # Hoy también
        ]
        
        for index, fecha in enumerate(fechas_pedidos):
            pedido = Pedido(
                numero_pedido=f"PED-SEED-{fecha.strftime('%Y%m%d%H%M')}-{index}",
                cliente_id=id_cliente,
                estado='completado',
                direccion_entrega="Calle de prueba 123",
                fecha_pedido=fecha
            )
            db.session.add(pedido)
            db.session.flush()
            
            # Agregar detalles. Pedido 0, 1 y 3 tendrán Rosas para que sean las más vendidas
            if index in [0, 1, 3]:
                d = DetallePedido(
                    pedido_id=pedido.id, 
                    producto_id=productos_creados['Rosas Rojas Premium'].id,
                    cantidad=random.randint(1, 3),
                    precio_unitario=productos_creados['Rosas Rojas Premium'].precio,
                )
                d.subtotal = d.cantidad * d.precio_unitario
                db.session.add(d)
                
            # Agregar Girasoles 
            if index in [2, 4]:
                d = DetallePedido(
                    pedido_id=pedido.id, 
                    producto_id=productos_creados['Arreglo Girasoles Sol'].id,
                    cantidad=1,
                    precio_unitario=productos_creados['Arreglo Girasoles Sol'].precio,
                )
                d.subtotal = d.cantidad * d.precio_unitario
                db.session.add(d)
                
            db.session.flush()
            pedido.calcular_total()
            
            print(f"  - Pedido {pedido.numero_pedido} con total ${pedido.total} simulado en {fecha.strftime('%Y-%m-%d')}")

        try:
            db.session.commit()
            print("\n✅ ¡Todos los datos inyectados correctamente!")
            print("Ya puedes probar el chatbot y ver los gráficos llenos en el dashboard.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error insertando datos: {str(e)}")

if __name__ == '__main__':
    seed_db()
