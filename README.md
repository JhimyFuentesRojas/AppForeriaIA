# Sistema Web Florería con Inteligencia Artificial

Plataforma de gestión y venta de flores desarrollada en Flask, que integra capacidades de Inteligencia Artificial (mediante Groq y Llama-3.1-8b) para mejorar la experiencia tanto de los clientes (mediante un chatbot asistente) como de los administradores (mediante un dashboard analítico avanzado).

--- 

## Integrantes Equipo 14
- Limberg Edgar Montes Tancara
- Jhimy Fuentes Rojas


## 1. Documentación de la Inteligencia Artificial (IA)

### Explicación General
El sistema utiliza la API de Groq, operando el avanzado modelo de lenguaje **Llama-3.1-8b-instant**. La arquitectura de IA se basa en un servicio centralizado (`chatbot_service.py`) que recibe el contexto (historial de mensajes, catálogos, datos estadísticos) y el rol del usuario, generando sugerencias mediante el diseño de prompts del sistema altamente estructurados. 

La integración funciona mediante un **flujo de interacción** donde:
1. El usuario (cliente o admin) envía un mensaje de texto.
2. El sistema empaqueta el mensaje junto al contexto actual (productos en stock y datos recientes de pedidos) y se envía vía HTTP POST a Groq.
3. El modelo de IA interpreta la intención del usuario y responde estrictamente en formato JSON.
4. El backend traduce esta estructura en acciones nativas de UI, mostrando texto interactivo u operando los sistemas de la tienda (recomendando tarjetas, modificando la base de datos, insertando en el carrito).

---

### Documentación — Chatbot para Clientes
El Chatbot de clientes actúa como un asistente virtual personalizado en tiempo real para ayudar con la compra de arreglos florales y productos. 

#### Funcionalidades:
- **Consultar productos disponibles:** Entiende si hay stock en la BD y avisa a los usuarios.
- **Recomendar flores según ocasión:** Puede realizar match semántico entre "Flores para cumpleaños" y "Girasoles / Rosas".
- **Mostrar productos con precio e imagen:** La IA retorna listados estructurados que luego el frontend procesa para generar _tarjetas de productos visuales_ con sus fotografías directamente en la ventana de chat.
- **Añadir productos al carrito:** Las tarjetas de sugerencia incluyen botones interactivos que inyectan los productos directamente en la sesión de compra del usuario sin hacerlo salir del chat.
- **Guiar al cliente en la compra:** Mantiene contexto durante toda la navegación.

#### Ejemplos de preguntas que puede responder:
- *"¿Qué flores tienen stock disponible hoy?"*
- *"Recomiéndame flores para un cumpleaños de mi esposa."*
- *"¿Cuál es la flor más económica de toda la tienda?"*
- *"¿Qué flores románticas tienen disponibles en este momento?"*

---

### Documentación — Chatbot para Administradores
El modo administrador del Chatbot (activable automáticamente cuando ingresan los encargados de la tienda) actúa como un ingeniero de datos en miniatura y asistente operativo.

#### Funcionalidades:
- **Consultar estadísticas del sistema:** Provee respuestas inmediatas sobre datos agregados de ventas.
- **Ver productos con bajo stock:** Analiza de todos los catálogos y resalta aquellos críticos (< 10 unidades).
- **Crear productos desde el chat:** Tiene capacidad `function-calling`. Si un admin pide agregar "Violetas a 50 Bs", el chatbot orquesta y comete una inserción SQL directamente hacia la base de datos de productos.
- **Actualizar stock de productos:** Puede recibir peticiones para reponer y modificar inventarios sin tener que pasar por formularios tradicionales.
- **Analizar ventas:** Genera resúmenes ejecutivos rápidos.

#### Ejemplos de preguntas del admin:
- *"¿Cuántos productos hay registrados actualmente en la base de datos?"*
- *"Dime qué productos tienen bajo stock para reponerlos."*
- *"¿Cuál es el producto económicamente más vendido?"*
- *"Añade un nuevo producto llamado Hortensia Imperial por 150 bs con 5 unidades de stock en categoría Exóticas."*

---

### Documentación — Dashboard Inteligente IA
El Panel IA proporciona analítica visual (gráficos) y un análisis en lenguaje natural profundo de métricas críticas que el sistema genera todos los días en formato `batch`, visible sólo para cuentas Admin.

El dashboard genera dinámicamente:
- **Análisis de los datos del sistema:** Relaciones entre `pedidos`, `detalles_pedido`, `productos` y fechas de compra.
- **Generación de Insights automáticos:** Analiza el historial completo del mes y devuelve interpretaciones de negocio.
- **Muestra de métricas clave:** Indicadores sobre tendencias, caídas de ventas, y stock.

#### Ejemplos de análisis generados por IA (Insights Reales):
- *"El producto más vendido este mes es Rosas Rojas con 35 ventas."*
- *"La categoría más popular es 'Flores Románticas' y representa el 40% de las ventas totales del período."*
- *"El producto 'Tulipanes Rojos' podría agotarse pronto debido a su inusualmente bajo stock (2 unidades), te recomendamos reponer urgente."*

---

## 2. Guía de Instalación del Proyecto

A continuación se detalla cómo desplegar el proyecto desde cero en cualquier estación de desarrollo.

### Prerrequisitos
- **Python 3.9+** instalado.
- Servidor de MySQL local (ej. XAMPP, Workbench) corriendo en el puerto 3306.

### Paso a paso:

**1. Instalar Python**
Asegúrate del correcto runtime usando `python --version`.

**2. Clonar el repositorio**
```bash
git clone <url-del-repositorio>
cd AppFloreria
```

**3. Crear entorno virtual**
Aísla las dependencias del sistema global creándolo dentro del directorio.
```bash
python -m venv .venv
```

**4. Activar el entorno e Instalar Dependencias**
```bash
# En Windows:
.venv\Scripts\activate

# En Linux o MacOS:
source .venv/bin/activate

pip install -r requirements.txt
```

**5. Configurar Variables de Entorno**
Crea en la raíz del proyecto un archivo `.env` según el archivo base `env.example` y rellénalo con lo siguiente:
```dotenv
FLASK_APP=main.py
FLASK_ENV=development
SECRET_KEY=clave_secreta_super_segura
SQLALCHEMY_DATABASE_URI=mysql://usuario:contraseña@localhost/floreria_db
GROQ_API_KEY=tu_propia_api_key_de_groq
```

**6. Configurar Base de Datos**
Crea la base de datos en tu entorno MySQL con el nombre exacto de tu variable de entorno: `CREATE DATABASE floreria_db;`.

**7. Ejecutar Migraciones e Inserción Inicial**
Creará las tablas `usuarios`, `categorias`, `productos` y `pedidos`.
```bash
flask db upgrade
flask seed-all   # Comando manual si existe en el proyecto para insertar productos
```

**8. Ejecutar el Servidor Flask**
Levantará la app local.
```bash
flask run
# Alternativamente, si usaste uv o main.py directo:
python main.py
```
> El proyecto estará disponible en [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 3. Arquitectura del Sistema

El sistema implementa un modelo **Monolítico MVC Flexible** (Model, View, Controller) encapsulado en Flask Blueprints, logrando escalabilidad e independencia entre submódulos.

### Estructura de Carpetas

```
app/
├── auth/            # Endpoints y lógica de Autenticación, registro y recuperación.
├── categorias/      # Controladores de CRUD de categorías.
├── main/            # Vistas estáticas, Home o Landing pages.
├── base/            # Servicios transversales.
├── models/          # Entidades SQLAlchemy (User, Product, Cart, Order).
├── pedidos/         # Controladores de transacciones E-Commerce.
├── productos/       # Administración interna de los catálogos y CRUD de inventario.
├── routes/          # Rutas específicas modernas (Como Chatbot y Dashboard AJAX).
├── services/        # Lógica de Negocio y Conexiones IA (Ej: chatbot_service.py).
├── static/          # Assets públicos (CSS, JS, media de las flores).
├── templates/       # Vistas HTML, Jinja2 macros y base layout.
├── tienda/          # Controladores cliente público: Vitrina de la Tienda, Carrito, y Frontend de Compras.
└── utils/           # Herramientas de manejo de fechas o limpiadores.

main.py              # Entry-point principal.
requirements.txt     # Dependencias Pypi
.env                 # Variables de entorno ignoradas por Git.
```

### Servicios de IA e Integración con Groq
La capa arquitectónica de inteligencia artificial se aísla mediante el patrón _Service Layer_.
El archivo fundamental es `app/services/chatbot_service.py`, interactuando con `groq.Groq(api_key=...)`.
Las plantillas (`app/templates/chatbot_widget.html`) hablan con Blueprints exclusivos de datos vía `fetch` asíncronos en `app/routes/chatbot_routes.py`. Los JSON de la respuesta de la IA (Llama) se decodifican y mapean a modelos relacionales antes de mostrarse en HTML.

### Rutas Principales
- **Públicas E-Commerce:** `/tienda/` (Catálogo), `/tienda/carrito` (Cesta), `/tienda/checkout` (Caja asíncrona segura).
- **APIs de Inteligencia:** `/api/chatbot`, `/api/chatbot/add-to-cart`, `/api/admin/dashboard-ai`, `/api/admin/update-stock`.
- **Zonas Administrivas Protegidas:** `/dashboard-ia` y `/productos`.
- **Seguridad:** `/auth/login` manejado por sesiones encriptadas y `Flask-Login`.
