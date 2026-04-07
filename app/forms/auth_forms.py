"""
Formularios de autenticación.
"""
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    """Formulario de inicio de sesión."""
    username = StringField('Usuario', validators=[
        DataRequired(message='El usuario es obligatorio.'),
        Length(max=80)
    ], render_kw={'placeholder': 'Ingrese su usuario', 'autofocus': True})

    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es obligatoria.'),
        Length(max=128)
    ], render_kw={'placeholder': 'Ingrese su contraseña'})

    submit = SubmitField('Ingresar')


class CambiarCredencialesForm(FlaskForm):
    """Formulario para cambiar credenciales del administrador."""
    username = StringField('Nuevo Usuario', validators=[
        DataRequired(message='El usuario es obligatorio.'),
        Length(min=3, max=80, message='El usuario debe tener entre 3 y 80 caracteres.')
    ], render_kw={'placeholder': 'Nuevo nombre de usuario'})

    password_actual = PasswordField('Contraseña Actual', validators=[
        DataRequired(message='Debe ingresar su contraseña actual.')
    ], render_kw={'placeholder': 'Contraseña actual'})

    password_nueva = PasswordField('Nueva Contraseña', validators=[
        Length(min=0, max=128, message='La contraseña no puede superar 128 caracteres.')
    ], render_kw={'placeholder': 'Dejar vacío para no cambiar'})

    password_confirmar = PasswordField('Confirmar Nueva Contraseña', render_kw={
        'placeholder': 'Confirmar nueva contraseña'
    })

    submit = SubmitField('Guardar Cambios')
