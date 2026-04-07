"""
Modelo Administrador.
Usuario con permisos completos del sistema.
"""
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db


class Administrador(UserMixin, db.Model):
    """Modelo de administrador con autenticación segura."""
    __tablename__ = 'administradores'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre_completo = db.Column(db.String(150), nullable=True, default='Administrador')

    def set_password(self, password):
        """Genera hash seguro de la contraseña."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica la contraseña contra el hash almacenado."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.username}>'
