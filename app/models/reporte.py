"""
Modelo ReporteDiario.
Registra la actividad de un empleado en un día específico,
junto con el valor asignado por el administrador.
"""
from datetime import datetime
from app.extensions import db


class ReporteDiario(db.Model):
    """Reporte de actividad diaria de un empleado."""
    __tablename__ = 'reportes_diarios'

    # Evitar reportes duplicados del mismo empleado en el mismo día
    __table_args__ = (
        db.UniqueConstraint('empleado_id', 'fecha', name='uq_empleado_fecha'),
    )

    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleados.id'), nullable=False, index=True)
    fecha = db.Column(db.Date, nullable=False, index=True)
    actividad = db.Column(db.Text, nullable=False)

    # Valores de pago (SOLO visibles para el administrador)
    valor_dia_original = db.Column(db.Float, nullable=False, default=0.0)
    valor_dia_aplicado = db.Column(db.Float, nullable=False, default=0.0)

    # Estado del pago
    estado_pago = db.Column(db.String(20), nullable=False, default='pendiente')
    # Valores posibles: 'pendiente', 'revisado', 'ausente'

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Reporte {self.empleado_id} - {self.fecha}>'

    @property
    def estado_badge(self):
        """Retorna la clase CSS del badge según el estado."""
        badges = {
            'pendiente': 'bg-warning',
            'revisado': 'bg-success',
            'ausente': 'bg-danger'
        }
        return badges.get(self.estado_pago, 'bg-secondary')

    def to_dict(self, incluir_valores=False):
        """
        Serializa el reporte a diccionario.
        incluir_valores=False excluye valores monetarios (para vista de cliente).
        """
        data = {
            'id': self.id,
            'empleado_id': self.empleado_id,
            'fecha': self.fecha.strftime('%d/%m/%Y') if self.fecha else '',
            'actividad': self.actividad,
            'estado_pago': self.estado_pago,
            'created_at': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else ''
        }
        if incluir_valores:
            data['valor_dia_original'] = self.valor_dia_original
            data['valor_dia_aplicado'] = self.valor_dia_aplicado
        return data
