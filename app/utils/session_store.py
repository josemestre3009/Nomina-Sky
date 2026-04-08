"""
Almacén server-side de sesiones activas.
Permite invalidar sesiones previas al hacer login desde otro lugar (control de sesiones concurrentes).
"""

# {admin_id: session_token}
_active_sessions: dict = {}


def register_session(admin_id: int, token: str) -> None:
    """Registra el token de la sesión activa para un admin, invalidando cualquier sesión previa."""
    _active_sessions[admin_id] = token


def is_valid_session(admin_id: int, token: str) -> bool:
    """Verifica que el token de sesión coincida con el registrado en el servidor."""
    return bool(token) and _active_sessions.get(admin_id) == token


def invalidate_session(admin_id: int) -> None:
    """Invalida la sesión activa de un admin (logout)."""
    _active_sessions.pop(admin_id, None)
