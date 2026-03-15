# test_db.py
import pymysql
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

try:
    connection = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='root',  # Tu contraseña
        database='floreria_db',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    print("✅ ¡Conexión exitosa a MySQL!")
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT DATABASE();")
        result = cursor.fetchone()
        print(f"📦 Base de datos actual: {result['DATABASE()']}")
        
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print(f"📋 Tablas encontradas: {len(tables)}")
        for table in tables:
            print(f"   - {list(table.values())[0]}")
    
    connection.close()
    
except pymysql.Error as e:
    print(f"❌ Error de conexión: {e}")