"""
Extensiones de Flask inicializadas sin app (patrón Application Factory).
Se vinculan con la app en create_app().
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

# Base de datos ORM
db = SQLAlchemy()

# Gestión de sesiones y autenticación
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Debe iniciar sesión para acceder a esta página.'
login_manager.login_message_category = 'warning'

# Migraciones de base de datos
migrate = Migrate()

# Protección CSRF
csrf = CSRFProtect()
