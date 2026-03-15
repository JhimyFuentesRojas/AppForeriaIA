"""
Script de Seed - Datos iniciales para Florería Examen
Crea: categorías, productos, usuario admin, usuario cliente y pedidos de prueba
"""

from app import create_app
from app.extensions import db
from app.models import Usuario, Categoria, Producto, Pedido, DetallePedido
from datetime import datetime, timedelta
import random

app = create_app('development')

CATEGORIAS = [
    {"nombre": "Rosas",        "slug": "rosas",        "descripcion": "Rosas frescas de todas las variedades y colores."},
    {"nombre": "Flores Mixtas","slug": "flores-mixtas","descripcion": "Arreglos con combinación de flores de temporada."},
    {"nombre": "Plantas",      "slug": "plantas",      "descripcion": "Plantas de interior y exterior para el hogar."},
    {"nombre": "Orquídeas",    "slug": "orquideas",    "descripcion": "Orquídeas exóticas y elegantes de importación."},
    {"nombre": "Girasoles",    "slug": "girasoles",    "descripcion": "Girasoles frescos y arreglos con girasoles."},
]

PRODUCTOS = [
    # Rosas (cat 0)
    {"nombre": "Rosas Rojas x12",          "sku": "ROS-001", "precio": 25.00, "stock": 40, "destacado": True,  "cat": 0, "descripcion": "Docena de rosas rojas de primera calidad, perfectas para regalar."},
    {"nombre": "Rosas Blancas x12",         "sku": "ROS-002", "precio": 23.00, "stock": 30, "destacado": False, "cat": 0, "descripcion": "Docena de rosas blancas elegantes, ideales para bodas."},
    {"nombre": "Rosas Rosadas x6",          "sku": "ROS-003", "precio": 14.00, "stock": 25, "destacado": True,  "cat": 0, "descripcion": "Media docena de rosas rosadas, delicadas y románticas."},
    {"nombre": "Ramo Premium 24 Rosas",     "sku": "ROS-004", "precio": 48.00, "stock": 3,  "destacado": True,  "cat": 0, "descripcion": "Ramo de 24 rosas rojas con follaje verde y lazo de seda."},

    # Flores Mixtas (cat 1)
    {"nombre": "Arreglo Primaveral",        "sku": "MIX-001", "precio": 35.00, "stock": 15, "destacado": True,  "cat": 1, "descripcion": "Arreglo colorido con tulipanes, gerberas y margaritas de temporada."},
    {"nombre": "Bouquet Romántico",         "sku": "MIX-002", "precio": 42.00, "stock": 10, "destacado": True,  "cat": 1, "descripcion": "Bouquet mixto con rosas, lirios y flores silvestres."},
    {"nombre": "Centro de Mesa Clásico",    "sku": "MIX-003", "precio": 55.00, "stock": 8,  "destacado": False, "cat": 1, "descripcion": "Centro de mesa con flores variadas, ideal para eventos y celebraciones."},
    {"nombre": "Mini Arreglo de Escritorio","sku": "MIX-004", "precio": 18.00, "stock": 2,  "destacado": False, "cat": 1, "descripcion": "Pequeño arreglo floral perfecto para escritorios y espacios pequeños."},

    # Plantas (cat 2)
    {"nombre": "Suculenta Mixta",           "sku": "PLA-001", "precio": 12.00, "stock": 50, "destacado": True,  "cat": 2, "descripcion": "Suculenta en maceta de cerámica, fácil de cuidar y decorativa."},
    {"nombre": "Cactus Decorativo",         "sku": "PLA-002", "precio": 10.00, "stock": 35, "destacado": False, "cat": 2, "descripcion": "Cactus variado en maceta de barro, resistente y de bajo mantenimiento."},
    {"nombre": "Helecho Boston",            "sku": "PLA-003", "precio": 20.00, "stock": 20, "destacado": False, "cat": 2, "descripcion": "Helecho frondoso ideal para interior, purifica el aire del hogar."},
    {"nombre": "Pothos Colgante",           "sku": "PLA-004", "precio": 15.00, "stock": 0,  "destacado": False, "cat": 2, "descripcion": "Pothos en maceta colgante, crece rápido y es ideal para interiores."},

    # Orquídeas (cat 3)
    {"nombre": "Orquídea Phalaenopsis",     "sku": "ORQ-001", "precio": 60.00, "stock": 12, "destacado": True,  "cat": 3, "descripcion": "Orquídea mariposa de importación, disponible en blanco, rosa y morado."},
    {"nombre": "Orquídea Dendrobium",       "sku": "ORQ-002", "precio": 75.00, "stock": 7,  "destacado": False, "cat": 3, "descripcion": "Orquídea exótica con múltiples flores en vara, de larga duración."},
    {"nombre": "Orquídea Mini en Caja",     "sku": "ORQ-003", "precio": 45.00, "stock": 5,  "destacado": True,  "cat": 3, "descripcion": "Orquídea mini presentada en caja regalo, perfecta como obsequio."},

    # Girasoles (cat 4)
    {"nombre": "Girasoles x6",             "sku": "GIR-001", "precio": 20.00, "stock": 22, "destacado": True,  "cat": 4, "descripcion": "Ramo de 6 girasoles frescos, alegres y llenos de color."},
    {"nombre": "Arreglo Girasol y Rosas",  "sku": "GIR-002", "precio": 38.00, "stock": 9,  "destacado": True,  "cat": 4, "descripcion": "Combinación de girasoles y rosas rojas en papel kraft artesanal."},
    {"nombre": "Corona de Girasoles",      "sku": "GIR-003", "precio": 50.00, "stock": 4,  "destacado": False, "cat": 4, "descripcion": "Corona decorativa hecha con girasoles y follaje seco, estilo rústico."},
]

# Pedidos de prueba: (índice_producto, cantidad)
PEDIDOS_SEED = [
    [(0, 2), (4, 1)],   # pedido 1
    [(6, 1), (12, 1)],  # pedido 2
    [(0, 3), (15, 2)],  # pedido 3
    [(8, 4), (9, 2)],   # pedido 4
    [(1, 1), (16, 1)],  # pedido 5
    [(4, 2), (13, 1)],  # pedido 6
]


def seed():
    with app.app_context():
        # Verificar si ya hay datos
        if Usuario.query.count() > 0:
            print("⚠  Ya existen datos. Limpiando tablas antes de hacer seed...")
            DetallePedido.query.delete()
            Pedido.query.delete()
            Producto.query.delete()
            Categoria.query.delete()
            Usuario.query.delete()
            db.session.commit()

        print("Insertando usuarios...")
        admin = Usuario(
            username="admin",
            email="admin@floreria.com",
            nombre_completo="Administrador Principal",
            telefono="555-100-0001",
            direccion="Calle Principal #123, Ciudad",
            rol="admin",
            activo=True,
        )
        admin.set_password("admin123")

        cliente = Usuario(
            username="cliente1",
            email="cliente@floreria.com",
            nombre_completo="María García López",
            telefono="555-200-0001",
            direccion="Av. Las Flores #456, Colonia Jardines",
            rol="cliente",
            activo=True,
        )
        cliente.set_password("cliente123")

        db.session.add_all([admin, cliente])
        db.session.flush()

        print("Insertando categorías...")
        cats_obj = []
        for c in CATEGORIAS:
            cat = Categoria(nombre=c["nombre"], slug=c["slug"], descripcion=c["descripcion"], activo=True)
            db.session.add(cat)
            cats_obj.append(cat)
        db.session.flush()

        print("Insertando productos...")
        prods_obj = []
        for p in PRODUCTOS:
            prod = Producto(
                nombre=p["nombre"],
                sku=p["sku"],
                precio=p["precio"],
                stock=p["stock"],
                destacado=p["destacado"],
                descripcion=p["descripcion"],
                categoria_id=cats_obj[p["cat"]].id,
                activo=True,
            )
            db.session.add(prod)
            prods_obj.append(prod)
        db.session.flush()

        print("Insertando pedidos de prueba...")
        for i, items in enumerate(PEDIDOS_SEED):
            fecha = datetime.utcnow() - timedelta(days=random.randint(1, 30))
            pedido = Pedido(
                numero_pedido=f"PED-2026-{str(i + 1).zfill(4)}",
                cliente_id=cliente.id,
                estado="completado",
                direccion_entrega=cliente.direccion,
                telefono_contacto=cliente.telefono,
                fecha_pedido=fecha,
            )
            db.session.add(pedido)
            db.session.flush()

            total = 0
            for prod_idx, cantidad in items:
                producto = prods_obj[prod_idx]
                subtotal = float(producto.precio) * cantidad
                total += subtotal
                detalle = DetallePedido(
                    pedido_id=pedido.id,
                    producto_id=producto.id,
                    cantidad=cantidad,
                    precio_unitario=producto.precio,
                    subtotal=subtotal,
                )
                db.session.add(detalle)

            pedido.subtotal = total
            pedido.total = total

        db.session.commit()

        print("\n=== Seed completado exitosamente ===")
        print(f"  Categorías : {len(CATEGORIAS)}")
        print(f"  Productos  : {len(PRODUCTOS)}")
        print(f"  Pedidos    : {len(PEDIDOS_SEED)}")
        print("\nUsuarios creados:")
        print("  ADMIN   → usuario: admin       | contraseña: admin123")
        print("  CLIENTE → usuario: cliente1    | contraseña: cliente123")


if __name__ == "__main__":
    seed()
