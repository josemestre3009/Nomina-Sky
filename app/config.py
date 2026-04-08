"""
Configuración de la aplicación Actividades Sky.
Soporta SQLite (desarrollo) y PostgreSQL/MySQL (producción).
"""
import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configuración base."""
    
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("🔒 ERROR CRÍTICO: No hay 'SECRET_KEY' en las variables de entorno. Falta configurar Entorno en Easypanel o el archivo .env")

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("💾 ERROR CRÍTICO: No hay 'DATABASE_URL' en las variables de entorno.")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # Credenciales admin, OBLIGATORIAS para arrancar
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise ValueError("🛡️ ERROR CRÍTICO: Falta configurar 'ADMIN_USERNAME' o 'ADMIN_PASSWORD' en las variables de entorno.")

    # Paginación
    ITEMS_PER_PAGE = 15

    # Moneda
    CURRENCY = 'COP'
    CURRENCY_SYMBOL = '$'


class DevelopmentConfig(Config):
    """Configuración de desarrollo."""
    DEBUG = True


class ProductionConfig(Config):
    """Configuración de producción."""
    DEBUG = False


class TestingConfig(Config):
    """Configuración de testing."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Mapa de configuraciones
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig
}
