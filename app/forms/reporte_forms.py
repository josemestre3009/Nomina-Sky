"""
Formularios de reportes diarios.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, FloatField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class ReportePublicoForm(FlaskForm):
    """Formulario público para que empleados reporten actividades."""
    cedula = StringField('Número de Cédula', validators=[
        DataRequired(message='La cédula es obligatoria.'),
        Length(min=5, max=20, message='Cédula inválida.')
    ], render_kw={'placeholder': 'Ingrese su número de cédula', 'autofocus': True})

    fecha = DateField('Fecha del Reporte', format='%Y-%m-%d', validators=[
        DataRequired(message='La fecha es obligatoria.')
    ])

    actividad = TextAreaField('Actividad Realizada', validators=[
        DataRequired(message='Debe describir la actividad realizada.'),
        Length(min=10, max=2000, message='La actividad debe tener entre 10 y 2000 caracteres.')
    ], render_kw={
        'placeholder': 'Describa detalladamente las actividades realizadas en el día...',
        'rows': 5
    })

    submit = SubmitField('Enviar Reporte')


class ReporteAdminForm(FlaskForm):
    """Formulario de administrador para editar reportes."""
    actividad = TextAreaField('Actividad', validators=[
        DataRequired(message='La actividad es obligatoria.'),
        Length(min=10, max=2000)
    ], render_kw={'rows': 5})

    valor_dia_aplicado = FloatField('Valor del Día (COP)', validators=[
        DataRequired(message='El valor del día es obligatorio.'),
        NumberRange(min=0, message='El valor debe ser mayor o igual a 0.')
    ], render_kw={'placeholder': '0.00'})

    estado_pago = SelectField('Estado de Pago', choices=[
        ('pendiente', 'Pendiente'),
        ('revisado', 'Revisado'),
        ('ausente', 'Ausente')
    ], validators=[DataRequired()])

    submit = SubmitField('Guardar Cambios')


class FiltroReporteForm(FlaskForm):
    """Formulario para filtrar reportes (no usa CSRF porque es GET)."""
    class Meta:
        csrf = False

    cedula = StringField('Cédula', render_kw={'placeholder': 'Filtrar por cédula'})
    nombre = StringField('Nombre', render_kw={'placeholder': 'Filtrar por nombre'})
    fecha_inicio = DateField('Desde', format='%Y-%m-%d', validators=[Optional()])
    fecha_fin = DateField('Hasta', format='%Y-%m-%d', validators=[Optional()])
    estado_pago = SelectField('Estado', choices=[
        ('', 'Todos'),
        ('pendiente', 'Pendiente'),
        ('revisado', 'Revisado'),
        ('ausente', 'Ausente')
    ])
