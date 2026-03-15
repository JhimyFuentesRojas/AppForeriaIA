"""Comandos CLI personalizados para la aplicación"""

import click
from flask.cli import with_appcontext
from app.extensions import db
from decimal import Decimal
from app.models import Usuario, Categoria, Producto


@click.command('init-db')
@with_appcontext
def init_db():
    """Inicializar la base de datos con datos de prueba"""
    click.echo('Creando tablas de base de datos...')
    db.create_all()

    # 1. Crear Administrador
    if not Usuario.query.filter_by(username='admin').first():
        admin = Usuario(
            username='admin',
            email='admin@floreria.com',
            nombre_completo='Administrador Principal',
            rol='admin',
            activo=True
        )
        admin.set_password('admin123') # La contraseña será admin123
        db.session.add(admin)
        click.echo('✅ Usuario Admin creado (User: admin / Pass: admin123)')
    else:
        click.echo('⚠️ El usuario Admin ya existe.')
        
    # 2. Crear categorías iniciales si no existen
    categorias = [
        {'nombre': 'Rosas', 'descripcion': 'Rosas de diferentes colores y variedades', 'slug': 'rosas'},
        {'nombre': 'Orquídeas', 'descripcion': 'Orquídeas exóticas y elegantes', 'slug': 'orquideas'},
        {'nombre': 'Plantas de Interior', 'descripcion': 'Plantas perfectas para decorar tu hogar', 'slug': 'plantas-interior'},
        {'nombre': 'Arreglos Florales', 'descripcion': 'Arreglos personalizados para toda ocasión', 'slug': 'arreglos-florales'},
        {'nombre': 'Plantas Suculentas', 'descripcion': 'Suculentas fáciles de cuidar', 'slug': 'suculentas'},
    ]

    cats_creadas = {}  # AQUÍ ESTÁ EL DICCIONARIO SOLUCIONADO
    for cat_data in categorias:
        categoria = Categoria.query.filter_by(slug=cat_data['slug']).first()
        if not categoria:
            categoria = Categoria(**cat_data)
            db.session.add(categoria)
            db.session.flush()  # IMPORTANTE: Esto le asigna un ID a la categoría
            click.echo(f'  - Categoría creada: {cat_data["nombre"]}')
        cats_creadas[cat_data['slug']] = categoria

    # 3. Crear productos
    if Producto.query.count() == 0:
        productos_data = [
            Producto(
                nombre='Ramo "Amor Eterno" de 24 Rosas Rojas',
                descripcion='Espectacular ramo de 24 rosas rojas de tallo largo, importadas. Ideal para aniversarios, propuestas o para expresar amor profundo. Incluye follaje fino y envoltura de papel coreano negro.',
                precio=Decimal('450.00'),
                stock=15,
                sku='ROS-024-ROJ',
                categoria_id=cats_creadas['rosas'].id, 
                imagen='productos/ramo_rosas.jpg', 
                destacado=True,
                activo=True
            ),
            Producto(
                nombre='Orquídea Phalaenopsis Blanca en Base de Cerámica',
                descripcion='Elegante orquídea Phalaenopsis de dos varas en color blanco puro. Perfecta para decorar oficinas, salas de estar o como un regalo corporativo sofisticado. Fácil cuidado.',
                precio=Decimal('650.00'),
                stock=8,
                sku='ORQ-PHA-BLA',
                categoria_id=cats_creadas['orquideas'].id,
                imagen='productos/orquidea_blanca.jpg',
                destacado=True,
                activo=True
            ),
            Producto(
                nombre='Arreglo Primaveral "Amanecer"',
                descripcion='Un diseño alegre y colorido que combina girasoles, gerberas y lisiantus en una base rústica de madera. Transmite alegría y buenas energías.',
                precio=Decimal('380.00'),
                stock=12,
                sku='ARR-PRI-001',
                categoria_id=cats_creadas['arreglos-florales'].id,
                imagen='productos/arreglo_primaveral.jpg',
                destacado=False,
                activo=True
            ),
            Producto(
                nombre='Monstera Deliciosa (Costilla de Adán)',
                descripcion='La planta de interior por excelencia. Hojas grandes y perforadas que dan un toque tropical a cualquier espacio. Incluye maceta plástica decorativa blanca.',
                precio=Decimal('220.00'),
                stock=5,
                sku='PLA-MON-001',
                categoria_id=cats_creadas['plantas-interior'].id,
                imagen='productos/monstera.jpg',
                destacado=False,
                activo=True
            )
        ]
        
        db.session.add_all(productos_data)
        click.echo('✅ 4 Productos creados.')
    else:
        click.echo('⚠️ Los productos ya existen en la base de datos.')

    db.session.commit()
    click.echo('Base de datos inicializada correctamente!')


@click.command('create-admin')
@click.option('--username', prompt='Username', help='Nombre de usuario')
@click.option('--email', prompt='Email', help='Email del administrador')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Contraseña')
@click.option('--nombre', prompt='Nombre completo', help='Nombre completo')
@with_appcontext
def create_admin(username, email, password, nombre):
    """Crear un usuario administrador"""
    # Verificar si ya existe
    if Usuario.query.filter_by(username=username).first():
        click.echo(f'Error: El usuario {username} ya existe.')
        return

    if Usuario.query.filter_by(email=email).first():
        click.echo(f'Error: El email {email} ya está registrado.')
        return

    # Crear administrador
    admin = Usuario(
        username=username,
        email=email,
        nombre_completo=nombre,
        rol='admin',
        activo=True
    )
    admin.set_password(password)

    db.session.add(admin)
    db.session.commit()

    click.echo(f'Administrador {username} creado exitosamente!')