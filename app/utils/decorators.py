"""
Decoradores personalizados.
"""
from functools import wraps
from flask import redirect, url_for, flash, session
from flask_login import current_user, logout_user
from app.utils.session_store import is_valid_session


def admin_required(f):
    """
    Decorador que verifica autenticación y que la sesión activa sea válida
    (previene sesiones concurrentes: si el mismo admin inicia sesión desde otro lugar,
    la sesión anterior queda invalidada automáticamente).
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debe iniciar sesión para acceder.', 'warning')
            return redirect(url_for('auth.login'))

        token = session.get('_session_token')
        if not is_valid_session(current_user.id, token):
            logout_user()
            session.clear()
            flash('Su sesión fue cerrada porque se inició sesión desde otro lugar.', 'warning')
            return redirect(url_for('auth.login'))

        return f(*args, **kwargs)
    return decorated_function
