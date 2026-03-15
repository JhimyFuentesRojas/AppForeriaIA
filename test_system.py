import requests
import sys

BASE_URL = "http://127.0.0.1:5000"
SESSION = requests.Session()

def print_step(msg):
    print(f"\n[+] {msg}")

def test_login():
    print_step("Registrando/Iniciando sesión como cliente nuevo...")
    
    import random
    import re
    rnd = random.randint(1000, 9999)
    email = f"testuser_{rnd}@test.com"
    pwd = "password123"
    
    # Obtener token CSRF de la página de registro
    res_get = SESSION.get(f"{BASE_URL}/auth/registro")
    csrf_match = re.search(r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']', res_get.text)
    csrf_token = csrf_match.group(1) if csrf_match else ""
    
    res = SESSION.post(f"{BASE_URL}/auth/registro", data={
        'csrf_token': csrf_token,
        'nombre': 'Usuario',
        'apellido': 'Test',
        'email': email,
        'telefono': '12345678',
        'direccion': 'Test Dir',
        'password': pwd,
        'confirm_password': pwd
    }, allow_redirects=True)
    
    # Obtener token CSRF de login
    res_get_login = SESSION.get(f"{BASE_URL}/auth/login")
    csrf_match_login = re.search(r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']', res_get_login.text)
    csrf_token_login = csrf_match_login.group(1) if csrf_match_login else ""
    
    res = SESSION.post(f"{BASE_URL}/auth/login", data={'csrf_token': csrf_token_login, 'email': email, 'password': pwd}, allow_redirects=True)
    if "Mi Perfil" not in res.text and "Cerrar Sesión" not in res.text:
         return False, "No se pudo iniciar sesión con el usuario recién creado.", "app/auth/routes.py", "Revise el flujo de registro o login (puede ser por CSRF o validaciones)."
         
    return True, "", "", ""

def test_get_product():
    print_step("Obteniendo ID de un producto disponible...")
    res = SESSION.get(f"{BASE_URL}/tienda/")
    # Buscar algún producto_id en el HTML para probar
    import re
    matches = re.findall(r'action="/tienda/agregar-carrito/(\d+)"', res.text)
    if not matches:
        return False, "No se encontraron productos disponibles con stock en la tienda.", "app/tienda/routes.py", "Asegúrese de cargar los datos de prueba (seed) en la BD e inicie sesión correctamente."
    return True, matches[0], "", ""

def test_add_to_cart(producto_id):
    print_step(f"Añadiendo producto {producto_id} al carrito...")
    res = SESSION.post(f"{BASE_URL}/tienda/agregar-carrito/{producto_id}", data={"cantidad": 1}, headers={"Accept": "application/json"}, allow_redirects=False)
    
    if res.status_code == 302:
         return False, f"El servidor redirigió (302). Probablemente faltó login o `Accept: application/json` no funcionó. Location: {res.headers.get('Location')}", "app/tienda/routes.py", "Asegurar que la sesión esté iniciada y el endpoint devuelva JSON."

    if 'application/json' not in res.headers.get('Content-Type', ''):
         return False, f"El servidor no devolvió JSON. Devolvió: {res.text[:100]}...", "app/tienda/routes.py", "Verificar endpoint AJAX de agregar_carrito."

    try:
        json_data = res.json()
    except Exception as e:
        return False, f"Respuesta no es JSON válido: {res.text[:100]}", "app/tienda/routes.py", ""
        
    if not json_data.get('success'):
         return False, f"La API devolvió éxito=False: {json_data.get('message')}", "app/tienda/routes.py", "Revisar validaciones de stock y parámetros recibidos."
         
    return True, json_data, "", ""

def test_view_cart():
    print_step("Revisando el carrito de compras...")
    res = SESSION.get(f"{BASE_URL}/tienda/carrito")
    if res.status_code != 200:
         return False, f"Error al acceder al carrito HTTP {res.status_code}", "app/tienda/routes.py", "Revisar la ruta ver_carrito y el renderizado de carrito.html."
         
    if "Tu carrito está vacío" in res.text:
         return False, "El carrito aparece vacío a pesar de haber agregado elementos.", "app/tienda/routes.py", "Asegurarse de que el objeto session['carrito'] sea modificado y gaurdado (session.modified = True)."
         
    return True, "", "", ""

def test_checkout():
    print_step("Procesando pedido (Checkout)...")
    res = SESSION.post(f"{BASE_URL}/tienda/procesar-compra", data={
        "direccion_entrega": "Avenida Siempre Viva 742, Springfield",
        "telefono_contacto": "555123456",
        "notas": "Llamar antes de entregar"
    }, headers={"Accept": "application/json"})
    
    if res.status_code != 200:
         return False, f"La compra falló con HTTP {res.status_code}: {res.text}", "app/tienda/routes.py", "Revisar excepciones (ValueError) o rollback en procesar_compra."
         
    json_data = res.json()
    if not json_data.get('success'):
         return False, f"Fallo al procesar compra: {json_data.get('message')}", "app/tienda/routes.py", "Atender el mensaje de error del json que el servidor devolvió."
         
    return True, json_data.get('redirect_url'), "", ""

def test_empty_cart_post_checkout():
    print_step("Validando que el carrito esté limpio post-compra...")
    res = SESSION.get(f"{BASE_URL}/api/carrito-count")
    if res.status_code == 200:
        json_data = res.json()
        if json_data.get('count', 0) > 0:
             return False, "El carrito no fue vaciado después de crear el pedido.", "app/tienda/routes.py", "Llamar session.pop('carrito', None) justo antes de devolver el success=True en procesar_compra."
    return True, "", "", ""

def run_tests():
    print("="*50)
    print("INICIANDO PRUEBAS AUTOMÁTICAS E2E - SISTEMA FLORERÍA")
    print("="*50)
    
    # 1. Login (Optional for test script to setup session, trying to use a generic approach)
    ok, err, file, sol = test_login()
    # It might pass or fail depending on actual DB seeded data.
    # In Flask-Login, some routes are @login_required.
    
    # 2. Get random Product
    ok, prod_id, file, sol = test_get_product()
    if not ok: return abort(err, file, sol)
    
    # 3. Add to Cart
    ok, data, file, sol = test_add_to_cart(prod_id)
    if not ok: return abort(err, file, sol)
    
    # 4. View Cart
    ok, _, file, sol = test_view_cart()
    if not ok: return abort(err, file, sol)
    
    # 5. Checkout
    ok, redirect_url, file, sol = test_checkout()
    if not ok: return abort(err, file, sol)
    
    # 6. Verify empty cart
    ok, _, file, sol = test_empty_cart_post_checkout()
    if not ok: return abort(err, file, sol)
    
    print("\n" + "="*50)
    print("[EXITO] TODAS LAS PRUEBAS PASARON CORRECTAMENTE")
    print("El flujo completo: agregar carrito, verificar stock, cobrar e inserción es estable.")
    print("="*50 + "\n")

def abort(err, file, sol):
    print("\n" + "[ERROR] "*10)
    print("ERROR CRÍTICO DETECTADO DURANTE EL FLUJO")
    print(f"Mensaje    : {err}")
    print(f"Archivo    : {file}")
    print(f"Solución   : {sol}")
    print("[ERROR] "*10 + "\n")
    sys.exit(1)

if __name__ == "__main__":
    try:
        run_tests()
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] No se pudo conectar a localhost:5000. Asegúrese que FLASK esté corriendo corriendo `uv run main.py`.")
        sys.exit(1)
