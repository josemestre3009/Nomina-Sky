"""
Rutas de autenticación.
Login (solo contraseña) y logout del administrador.
"""
import time
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user
from app.models.admin import Administrador
from app.forms.auth_forms import LoginForm
from app.services import audit_service
from app.extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/admin')

# ─── Protección contra fuerza bruta ───
MAX_INTENTOS = 5
BLOQUEO_SEGUNDOS = 300  # 5 minutos


def _get_login_key():
    """Obtener clave de intentos de login basada en IP."""
    return f'login_intentos_{request.remote_addr}'


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Inicio de sesión del administrador."""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    form = LoginForm()

    # Verificar bloqueo por intentos fallidos
    intentos = session.get('login_intentos', 0)
    bloqueado_hasta = session.get('login_bloqueado_hasta', 0)

    if time.time() < bloqueado_hasta:
        restante = int((bloqueado_hasta - time.time()) / 60) + 1
        flash(f'⚠️ Demasiados intentos fallidos. Intente en {restante} minuto(s).', 'danger')
        return render_template('auth/login.html', form=form, bloqueado=True)

    # Si ya pasó el bloqueo, resetear
    if time.time() >= bloqueado_hasta and intentos >= MAX_INTENTOS:
        session.pop('login_intentos', None)
        session.pop('login_bloqueado_hasta', None)
        intentos = 0

    if form.validate_on_submit():
        # Buscar el administrador por nombre de usuario
        admin = Administrador.query.filter_by(username=form.username.data).first()

        if admin and admin.check_password(form.password.data):
            # Login exitoso — resetear intentos
            session.pop('login_intentos', None)
            session.pop('login_bloqueado_hasta', None)

            login_user(admin, remember=False)

            # Regenerar session para prevenir session fixation
            session.regenerate = True

            audit_service.registrar(
                entidad='admin',
                entidad_id=admin.id,
                accion='login',
                descripcion=f'Inicio de sesión exitoso desde {request.remote_addr}',
                usuario=admin.username
            )
            db.session.commit()
            flash(f'¡Bienvenido, {admin.nombre_completo}!', 'success')

            next_page = request.args.get('next')
            # Validar que next_page sea una ruta relativa (prevenir open redirect)
            if next_page and not next_page.startswith('/'):
                next_page = None
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            # Login fallido — incrementar intentos
            intentos += 1
            session['login_intentos'] = intentos

            if intentos >= MAX_INTENTOS:
                session['login_bloqueado_hasta'] = time.time() + BLOQUEO_SEGUNDOS
                audit_service.registrar(
                    entidad='admin',
                    entidad_id=None,
                    accion='login',
                    descripcion=f'Cuenta bloqueada por {MAX_INTENTOS} intentos fallidos desde {request.remote_addr}',
                    usuario='desconocido'
                )
                db.session.commit()
                flash('⚠️ Demasiados intentos fallidos. Cuenta bloqueada temporalmente.', 'danger')
            else:
                restantes = MAX_INTENTOS - intentos
                flash(f'❌ Usuario o contraseña incorrectos. {restantes} intento(s) restante(s).', 'danger')

    return render_template('auth/login.html', form=form, bloqueado=False)


@auth_bp.route('/logout')
def logout():
    """Cierre de sesión."""
    if current_user.is_authenticated:
        audit_service.registrar(
            entidad='admin',
            entidad_id=current_user.id,
            accion='login',
            descripcion='Cierre de sesión',
            usuario=current_user.username
        )
        db.session.commit()
    logout_user()
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('auth.login'))
