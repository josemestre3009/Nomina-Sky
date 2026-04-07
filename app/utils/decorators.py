"""
Decoradores personalizados.
"""
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def admin_required(f):
    """
    Decorador que verifica que el usuario actual sea un administrador.
    Redirige a login si no está autenticado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debe iniciar sesión para acceder.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
