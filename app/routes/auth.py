"""
Rutas de autenticación.
Login (solo contraseña) y logout del administrador.
"""
import time
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user
from app.models.admin import Administrador
from app.forms.auth_forms import LoginForm
from app.services import audit_service
from app.extensions import db, limiter
from app.utils.session_store import register_session, invalidate_session

auth_bp = Blueprint('auth', __name__, url_prefix='/admin')

# ─── Protección contra fuerza bruta (server-side, por IP) ───
MAX_INTENTOS = 5
BLOQUEO_SEGUNDOS = 300  # 5 minutos

# Almacenamiento server-side de intentos: {ip: {'intentos': int, 'bloqueado_hasta': float}}
_intentos_por_ip: dict = {}


def _get_estado_ip(ip: str) -> tuple[int, float]:
    """Retorna (intentos, bloqueado_hasta) para la IP dada."""
    datos = _intentos_por_ip.get(ip, {})
    return datos.get('intentos', 0), datos.get('bloqueado_hasta', 0.0)


def _registrar_intento_fallido(ip: str) -> int:
    """Incrementa el contador de intentos para la IP. Retorna total de intentos."""
    datos = _intentos_por_ip.setdefault(ip, {'intentos': 0, 'bloqueado_hasta': 0.0})
    datos['intentos'] += 1
    if datos['intentos'] >= MAX_INTENTOS:
        datos['bloqueado_hasta'] = time.time() + BLOQUEO_SEGUNDOS
    return datos['intentos']


def _resetear_intentos(ip: str) -> None:
    """Limpia el registro de intentos para la IP tras login exitoso."""
    _intentos_por_ip.pop(ip, None)


def _is_safe_redirect(url: str) -> bool:
    """Valida que la URL de redirección sea segura (ruta relativa del mismo host)."""
    if not url:
        return False
    # Rechaza cualquier URL que no empiece con exactamente '/' o que use protocolo
    if not url.startswith('/') or url.startswith('//'):
        return False
    # Rechaza URLs con caracteres de control o backslash (bypass tricks)
    if any(c in url for c in ('\r', '\n', '\\')):
        return False
    return True


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('20/minute')
def login():
    """Inicio de sesión del administrador."""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    form = LoginForm()
    ip = request.remote_addr

    # Verificar bloqueo por intentos fallidos (server-side por IP)
    intentos, bloqueado_hasta = _get_estado_ip(ip)

    if time.time() < bloqueado_hasta:
        restante = int((bloqueado_hasta - time.time()) / 60) + 1
        flash(f'⚠️ Demasiados intentos fallidos. Intente en {restante} minuto(s).', 'danger')
        return render_template('auth/login.html', form=form, bloqueado=True)

    # Si el bloqueo ya expiró, resetear
    if bloqueado_hasta > 0 and time.time() >= bloqueado_hasta:
        _resetear_intentos(ip)
        intentos = 0

    if form.validate_on_submit():
        admin = Administrador.query.filter_by(username=form.username.data).first()

        if admin and admin.check_password(form.password.data):
            # Login exitoso — resetear intentos server-side
            _resetear_intentos(ip)

            login_user(admin, remember=False)

            # Regenerar session para prevenir session fixation
            session.regenerate = True

            # Control de sesiones concurrentes: invalidar token anterior y emitir uno nuevo
            token = str(uuid.uuid4())
            register_session(admin.id, token)
            session['_session_token'] = token

            audit_service.registrar(
                entidad='admin',
                entidad_id=admin.id,
                accion='login',
                descripcion=f'Inicio de sesión exitoso desde {ip}',
                usuario=admin.username
            )
            db.session.commit()
            flash(f'¡Bienvenido, {admin.nombre_completo}!', 'success')

            next_page = request.args.get('next')
            # Validar redirección segura (prevenir open redirect, incluido //evil.com)
            if not _is_safe_redirect(next_page):
                next_page = None
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            # Login fallido — registrar server-side
            total_intentos = _registrar_intento_fallido(ip)

            if total_intentos >= MAX_INTENTOS:
                audit_service.registrar(
                    entidad='admin',
                    entidad_id=None,
                    accion='login',
                    descripcion=f'Cuenta bloqueada por {MAX_INTENTOS} intentos fallidos desde {ip}',
                    usuario='desconocido'
                )
                db.session.commit()
                flash('⚠️ Demasiados intentos fallidos. Cuenta bloqueada temporalmente.', 'danger')
            else:
                restantes = MAX_INTENTOS - total_intentos
                # Auditar cada intento fallido individualmente
                audit_service.registrar(
                    entidad='admin',
                    entidad_id=None,
                    accion='login',
                    descripcion=f'Intento fallido #{total_intentos} desde {ip} — {restantes} intento(s) restante(s)',
                    usuario=form.username.data or 'desconocido'
                )
                db.session.commit()
                flash(f'❌ Usuario o contraseña incorrectos. {restantes} intento(s) restante(s).', 'danger')

    return render_template('auth/login.html', form=form, bloqueado=False)


@auth_bp.route('/logout')
def logout():
    """Cierre de sesión."""
    if current_user.is_authenticated:
        invalidate_session(current_user.id)
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
