"""
Servicio de auditoría.
Registra todas las acciones importantes del sistema.
"""
import json
from datetime import datetime
from app.extensions import db
from app.models.auditoria import Auditoria


def registrar(entidad, entidad_id, accion, descripcion='',
              valores_anteriores=None, valores_nuevos=None, usuario='sistema'):
    """
    Registra una acción en el log de auditoría.

    Args:
        entidad: Tipo de entidad (empleado, reporte, bono, config)
        entidad_id: ID del registro afectado
        accion: Tipo de acción (crear, editar, eliminar, login, config)
        descripcion: Descripción legible de la acción
        valores_anteriores: Dict con valores antes del cambio
        valores_nuevos: Dict con valores después del cambio
        usuario: Username del administrador que realizó la acción
    """
    registro = Auditoria(
        entidad=entidad,
        entidad_id=entidad_id,
        accion=accion,
        descripcion=descripcion,
        valores_anteriores=json.dumps(valores_anteriores, ensure_ascii=False, default=str) if valores_anteriores else None,
        valores_nuevos=json.dumps(valores_nuevos, ensure_ascii=False, default=str) if valores_nuevos else None,
        usuario=usuario,
        fecha=datetime.utcnow()
    )
    db.session.add(registro)
    # No hacemos commit aquí — se hace en la transacción principal
    return registro


def obtener_registros(pagina=1, por_pagina=20, entidad=None, accion=None):
    """
    Obtiene registros de auditoría con paginación y filtros.
    """
    query = Auditoria.query.order_by(Auditoria.fecha.desc())

    if entidad:
        query = query.filter(Auditoria.entidad == entidad)
    if accion:
        query = query.filter(Auditoria.accion == accion)

    return query.paginate(page=pagina, per_page=por_pagina, error_out=False)
