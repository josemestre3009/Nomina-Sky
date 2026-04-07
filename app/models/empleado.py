"""
Modelo Empleado.
Representa a un trabajador registrado en el sistema.
"""
from datetime import date
from app.extensions import db


class Empleado(db.Model):
    """Modelo de empleado con datos personales y valor por día."""
    __tablename__ = 'empleados'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    cedula = db.Column(db.String(20), unique=True, nullable=False, index=True)
    cargo = db.Column(db.String(100), nullable=False, default='Operario')
    valor_dia_defecto = db.Column(db.Float, nullable=False, default=0.0)
    estado = db.Column(db.String(20), nullable=False, default='activo')  # activo / inactivo
    fecha_ingreso = db.Column(db.Date, nullable=False, default=date.today)

    # Relaciones
    reportes = db.relationship('ReporteDiario', backref='empleado', lazy='dynamic',
                               cascade='all, delete-orphan')
    bonos = db.relationship('Bono', backref='empleado', lazy='dynamic',
                            cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Empleado {self.nombre} - {self.cedula}>'

    @property
    def esta_activo(self):
        """Retorna True si el empleado está activo."""
        return self.estado == 'activo'

    def to_dict(self):
        """Serializa el empleado a diccionario (para API JSON)."""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'cedula': self.cedula,
            'cargo': self.cargo,
            'estado': self.estado,
            'fecha_ingreso': self.fecha_ingreso.strftime('%d/%m/%Y') if self.fecha_ingreso else ''
        }
