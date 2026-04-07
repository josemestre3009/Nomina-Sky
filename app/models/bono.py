"""
Modelo Bono.
Bonificaciones adicionales asignadas a un empleado.
"""
from datetime import datetime
from app.extensions import db


class Bono(db.Model):
    """Bono adicional para un empleado."""
    __tablename__ = 'bonos'

    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleados.id'), nullable=False, index=True)
    valor = db.Column(db.Float, nullable=False, default=0.0)
    descripcion = db.Column(db.String(255), nullable=False, default='Bono')
    fecha_inicio = db.Column(db.Date, nullable=True)
    fecha_fin = db.Column(db.Date, nullable=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Bono {self.empleado_id} - ${self.valor}>'

    def to_dict(self):
        """Serializa el bono a diccionario."""
        return {
            'id': self.id,
            'empleado_id': self.empleado_id,
            'valor': self.valor,
            'descripcion': self.descripcion,
            'fecha_inicio': self.fecha_inicio.strftime('%d/%m/%Y') if self.fecha_inicio else '',
            'fecha_fin': self.fecha_fin.strftime('%d/%m/%Y') if self.fecha_fin else '',
            'fecha_creacion': self.fecha_creacion.strftime('%d/%m/%Y %H:%M') if self.fecha_creacion else ''
        }
