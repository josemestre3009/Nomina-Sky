"""
Application Factory de Actividades Sky.
Crea y configura la aplicación Flask con todos sus componentes.
Incluye medidas de seguridad robustas.
"""
import os
import secrets
from flask import Flask, render_template, request, g
from werkzeug.middleware.proxy_fix import ProxyFix
from .config import config_map
from .extensions import db, login_manager, migrate, csrf, limiter


def create_app(config_name=None):
    """Crea y configura la instancia de Flask."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map['default']))

    # ProxyFix: permite que Flask confíe en los headers del proxy de Easypanel/Nginx
    # Necesario para que HTTPS, IPs y URLs funcionen correctamente detrás de un reverse proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # ─── Configuración de seguridad de sesión/cookies ───
    # SESSION_COOKIE_SECURE se controla via variable de entorno COOKIE_SECURE=true
    # (no automático por FLASK_ENV para evitar problemas con proxies que usan HTTP internamente)
    _secure = os.environ.get('COOKIE_SECURE', 'false').lower() == 'true'
    app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
    app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')
    app.config.setdefault('SESSION_COOKIE_SECURE', _secure)
    app.config.setdefault('REMEMBER_COOKIE_HTTPONLY', True)
    app.config.setdefault('REMEMBER_COOKIE_SECURE', _secure)
    app.config.setdefault('REMEMBER_COOKIE_DURATION', 0)
    app.config.setdefault('WTF_CSRF_TIME_LIMIT', 3600)  # CSRF tokens válidos 1 hora
    app.config.setdefault('MAX_CONTENT_LENGTH', 2 * 1024 * 1024)  # Máx 2MB uploads

    # Asegurar que exista el directorio de instancia
    os.makedirs(app.instance_path, exist_ok=True)

    # Inicializar extensiones
    _init_extensions(app)

    # Registrar blueprints
    _register_blueprints(app)

    # Registrar filtros Jinja2
    _register_filters(app)

    # Registrar manejadores de error
    _register_error_handlers(app)

    # Registrar comandos CLI
    _register_cli_commands(app)

    # Registrar headers de seguridad y nonce CSP
    _register_security_headers(app)

    # Context processor: nonce disponible en todos los templates
    @app.context_processor
    def inject_csp_nonce():
        return {'csp_nonce': getattr(g, 'csp_nonce', '')}

    return app


def _init_extensions(app):
    """Inicializa todas las extensiones con la app."""
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    limiter.init_app(app)

    # Configurar login_manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Debe iniciar sesión para acceder.'
    login_manager.login_message_category = 'warning'
    login_manager.session_protection = 'strong'

    from .models.admin import Administrador

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(Administrador, int(user_id))
        except (ValueError, TypeError):
            return None


def _register_blueprints(app):
    """Registra todos los blueprints de la aplicación."""
    from .routes.public import public_bp
    from .routes.auth import auth_bp
    from .routes.admin_panel import admin_bp
    from .routes.reportes import reportes_bp
    from .routes.nomina import nomina_bp
    from .routes.exportar import exportar_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(nomina_bp)
    app.register_blueprint(exportar_bp)


def _register_filters(app):
    """Registra filtros personalizados para Jinja2."""
    from .utils.filters import formato_moneda, formato_fecha, formato_estado, formato_fecha_hora

    app.jinja_env.filters['moneda'] = formato_moneda
    app.jinja_env.filters['fecha'] = formato_fecha
    app.jinja_env.filters['fecha_hora'] = formato_fecha_hora
    app.jinja_env.filters['estado'] = formato_estado

    # Deshabilitar cache de templates en desarrollo para seguridad
    app.jinja_env.auto_reload = app.debug


def _register_error_handlers(app):
    """Registra páginas de error personalizadas."""

    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(413)
    def too_large(error):
        return render_template('errors/500.html'), 413


def _register_security_headers(app):
    """Aplica headers HTTP de seguridad a todas las respuestas."""

    is_production = os.environ.get('FLASK_ENV') == 'production'

    @app.before_request
    def generate_csp_nonce():
        g.csp_nonce = secrets.token_hex(16)

    @app.after_request
    def set_security_headers(response):
        nonce = getattr(g, 'csp_nonce', '')

        # Prevenir clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        # Prevenir MIME sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Prevenir XSS reflejado (navegadores antiguos)
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # Permisos de funcionalidades del navegador
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        # HSTS — solo en producción (requiere HTTPS)
        if is_production:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        # Content-Security-Policy con nonce por petición
        # script-src-elem: controla <script> tags (con nonce)
        # script-src-attr: permite event handlers inline (onclick, onchange, etc.)
        # connect-src: permite fetch de source maps desde CDN
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            f"script-src 'self' 'unsafe-inline' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
            f"script-src-elem 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
            "script-src-attr 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self' https://cdn.jsdelivr.net; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self';"
        )
        # Cache control para páginas sensibles
        if request.path.startswith('/admin'):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

        return response


def _register_cli_commands(app):
    """Registra comandos CLI personalizados."""
    import click

    @app.cli.command('seed')
    def seed_command():
        """Carga datos de prueba en la base de datos."""
        from seed import seed_database
        seed_database(app)
        click.echo('✅ Datos de prueba cargados exitosamente.')

    @app.cli.command('init-db')
    def init_db_command():
        """Crea todas las tablas e inicializa el admin."""
        db.create_all()
        _create_default_admin(app)
        click.echo('✅ Base de datos inicializada.')

    @app.cli.command('create-admin')
    @click.option('--username', prompt='Usuario', help='Nombre de usuario del admin')
    @click.option('--password', prompt='Contraseña', hide_input=True, help='Contraseña del admin')
    def create_admin_command(username, password):
        """Crea un usuario administrador."""
        from .models.admin import Administrador
        admin = Administrador.query.filter_by(username=username).first()
        if admin:
            click.echo(f'⚠️ El usuario "{username}" ya existe.')
            return
        admin = Administrador(username=username, nombre_completo=username)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f'✅ Admin "{username}" creado exitosamente.')


def _create_default_admin(app):
    """Crea el administrador por defecto si no existe."""
    from .models.admin import Administrador
    username = app.config.get('ADMIN_USERNAME', 'admin')
    password = app.config.get('ADMIN_PASSWORD', 'admin123')

    admin = Administrador.query.filter_by(username=username).first()
    if not admin:
        admin = Administrador(username=username, nombre_completo='Administrador')
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
