"""
Modelo Auditoría.
Registra todas las acciones importantes del sistema para trazabilidad.
"""
import json
from datetime import datetime
from app.extensions import db


class Auditoria(db.Model):
    """Registro de auditoría del sistema."""
    __tablename__ = 'auditoria'

    id = db.Column(db.Integer, primary_key=True)
    entidad = db.Column(db.String(50), nullable=False)       # Ej: 'empleado', 'reporte', 'bono'
    entidad_id = db.Column(db.Integer, nullable=True)         # ID del registro afectado
    accion = db.Column(db.String(20), nullable=False)         # crear, editar, eliminar
    descripcion = db.Column(db.Text, nullable=True)
    valores_anteriores = db.Column(db.Text, nullable=True)    # JSON
    valores_nuevos = db.Column(db.Text, nullable=True)        # JSON
    usuario = db.Column(db.String(80), nullable=False, default='sistema')
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Auditoria {self.accion} {self.entidad} #{self.entidad_id}>'

    @property
    def valores_ant_dict(self):
        """Parsea valores anteriores de JSON a dict."""
        if self.valores_anteriores:
            try:
                return json.loads(self.valores_anteriores)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    @property
    def valores_new_dict(self):
        """Parsea valores nuevos de JSON a dict."""
        if self.valores_nuevos:
            try:
                return json.loads(self.valores_nuevos)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    @property
    def accion_badge(self):
        """Retorna clase CSS del badge según acción."""
        badges = {
            'crear': 'bg-success',
            'editar': 'bg-primary',
            'eliminar': 'bg-danger',
            'login': 'bg-info',
            'config': 'bg-warning text-dark'
        }
        return badges.get(self.accion, 'bg-secondary')
