"""
Formularios de bonos.
"""
from flask_wtf import FlaskForm
from wtforms import FloatField, StringField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class BonoForm(FlaskForm):
    """Formulario para crear/editar bonos."""
    empleado_id = SelectField('Empleado', coerce=int, validators=[
        DataRequired(message='Debe seleccionar un empleado.')
    ])

    valor = FloatField('Valor del Bono (COP)', validators=[
        DataRequired(message='El valor del bono es obligatorio.'),
        NumberRange(min=0.01, message='El valor debe ser mayor a 0.')
    ], render_kw={'placeholder': '0.00'})

    descripcion = StringField('Descripción', validators=[
        DataRequired(message='La descripción es obligatoria.'),
        Length(min=3, max=255, message='La descripción debe tener entre 3 y 255 caracteres.')
    ], render_kw={'placeholder': 'Ej: Bono por productividad'})

    fecha_inicio = DateField('Fecha Inicio', format='%Y-%m-%d', validators=[Optional()])
    fecha_fin = DateField('Fecha Fin', format='%Y-%m-%d', validators=[Optional()])

    submit = SubmitField('Guardar Bono')
