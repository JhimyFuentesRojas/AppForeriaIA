import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
basedir = Path(__file__).parent.parent
load_dotenv(basedir / '.env')


class Config:
    """Configuración base de la aplicación Flask"""

    # Configuración general
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Configuración de base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:@localhost/floreria_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuración de subida de archivos
    UPLOAD_FOLDER = str(basedir / 'app' / 'static' / 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB por defecto
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # Configuración de Groq IA
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    GROQ_MODEL = os.environ.get('GROQ_MODEL', 'llama-3.1-8b-instant')

    # Flask-Admin
    FLASK_ADMIN_SWATCH = 'cerulean'

    @staticmethod
    def init_app(app):
        """Inicializar la aplicación con configuraciones adicionales"""
        # Crear carpeta de uploads si no existe
        upload_folder = Path(app.config['UPLOAD_FOLDER'])
        upload_folder.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
