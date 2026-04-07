"""
Formularios de gestión de empleados.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class EmpleadoForm(FlaskForm):
    """Formulario para crear/editar empleados."""
    nombre = StringField('Nombre Completo', validators=[
        DataRequired(message='El nombre es obligatorio.'),
        Length(min=3, max=150, message='El nombre debe tener entre 3 y 150 caracteres.')
    ], render_kw={'placeholder': 'Nombre completo del empleado'})

    cedula = StringField('Cédula', validators=[
        DataRequired(message='La cédula es obligatoria.'),
        Length(min=5, max=20, message='La cédula debe tener entre 5 y 20 caracteres.')
    ], render_kw={'placeholder': 'Número de cédula'})

    cargo = StringField('Cargo', validators=[
        DataRequired(message='El cargo es obligatorio.'),
        Length(max=100)
    ], render_kw={'placeholder': 'Cargo del empleado'})

    valor_dia_defecto = FloatField('Valor por Día (COP)', validators=[
        DataRequired(message='El valor por día es obligatorio.'),
        NumberRange(min=0, message='El valor debe ser mayor o igual a 0.')
    ], render_kw={'placeholder': '0.00'})

    estado = SelectField('Estado', choices=[
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo')
    ], validators=[DataRequired()])

    fecha_ingreso = DateField('Fecha de Ingreso', format='%Y-%m-%d', validators=[
        Optional()
    ])

    submit = SubmitField('Guardar')
