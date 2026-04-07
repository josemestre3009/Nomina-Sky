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
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-por-defecto-cambiar')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(os.path.dirname(basedir), 'instance', 'nomina_sky.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    # Credenciales admin por defecto (configurables desde .env)
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

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
    'default': DevelopmentConfig
}
