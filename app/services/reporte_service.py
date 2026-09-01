"""
Servicio de reportes diarios.
Maneja la lógica de negocio de creación y gestión de reportes.
"""
from datetime import date
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models.empleado import Empleado
from app.models.reporte import ReporteDiario
from app.services import audit_service


class ReporteError(Exception):
    """Excepción personalizada para errores de reportes."""
    pass


# El empleado solo puede modificar sus reportes mientras el administrador
# no los haya procesado. Un reporte 'revisado' ya cuenta como día trabajado
# en la nómina, y uno 'ausente' lo marcó el administrador: ninguno se toca.
ESTADOS_EDITABLES_POR_EMPLEADO = ('pendiente',)


def es_editable_por_empleado(reporte):
    """Indica si el empleado aún puede modificar el reporte."""
    return reporte.estado_pago in ESTADOS_EDITABLES_POR_EMPLEADO


def obtener_empleado_activo(cedula):
    """
    Busca un empleado activo por cédula.

    Raises:
        ReporteError: Si no existe o está inactivo
    """
    empleado = Empleado.query.filter_by(cedula=cedula).first()
    if not empleado:
        raise ReporteError('No se encontró un empleado con esa cédula.')

    if not empleado.esta_activo:
        raise ReporteError('El empleado no está activo en el sistema.')

    return empleado


def guardar_reporte(cedula, fecha, actividad):
    """
    Crea el reporte diario de un empleado, o actualiza la actividad
    si ya existe uno para esa fecha.

    Args:
        cedula: Cédula del empleado
        fecha: Fecha del reporte
        actividad: Descripción de la actividad

    Returns:
        Tupla (ReporteDiario, actualizado) donde `actualizado` es True
        cuando se editó un reporte existente.

    Raises:
        ReporteError: Si hay error de validación
    """
    empleado = obtener_empleado_activo(cedula)

    existente = ReporteDiario.query.filter_by(
        empleado_id=empleado.id,
        fecha=fecha
    ).first()

    if existente:
        if not es_editable_por_empleado(existente):
            raise ReporteError(
                f'El reporte del {fecha.strftime("%d/%m/%Y")} ya fue procesado por el '
                'administrador y no se puede modificar.'
            )

        actividad_anterior = existente.actividad
        if actividad_anterior == actividad:
            return existente, True

        existente.actividad = actividad
        audit_service.registrar(
            entidad='reporte',
            entidad_id=existente.id,
            accion='editar',
            descripcion=f'Reporte editado por empleado {empleado.nombre} para {fecha.strftime("%d/%m/%Y")}',
            valores_anteriores={'actividad': actividad_anterior[:100]},
            valores_nuevos={'actividad': actividad[:100]},
            usuario=f'empleado:{empleado.cedula}'
        )
        db.session.commit()
        return existente, True

    # Crear reporte con valor por defecto del empleado
    reporte = ReporteDiario(
        empleado_id=empleado.id,
        fecha=fecha,
        actividad=actividad,
        valor_dia_original=empleado.valor_dia_defecto,
        valor_dia_aplicado=empleado.valor_dia_defecto,
        estado_pago='pendiente'
    )

    try:
        db.session.add(reporte)
        audit_service.registrar(
            entidad='reporte',
            entidad_id=None,  # Se asigna después del commit
            accion='crear',
            descripcion=f'Reporte creado por empleado {empleado.nombre} para {fecha.strftime("%d/%m/%Y")}',
            valores_nuevos={
                'empleado': empleado.nombre,
                'fecha': fecha.strftime('%d/%m/%Y'),
                'actividad': actividad[:100]
            },
            usuario=f'empleado:{empleado.cedula}'
        )
        db.session.commit()
        return reporte, False
    except IntegrityError:
        db.session.rollback()
        raise ReporteError('Ya existe un reporte para esta fecha. Recargue la página e intente de nuevo.')


def obtener_reportes_filtrados(pagina=1, por_pagina=15, cedula=None, nombre=None,
                                fecha_inicio=None, fecha_fin=None, estado_pago=None):
    """
    Obtiene reportes con filtros y paginación.
    """
    query = ReporteDiario.query.join(Empleado)

    if cedula:
        query = query.filter(Empleado.cedula.contains(cedula))
    if nombre:
        query = query.filter(Empleado.nombre.ilike(f'%{nombre}%'))
    if fecha_inicio:
        query = query.filter(ReporteDiario.fecha >= fecha_inicio)
    if fecha_fin:
        query = query.filter(ReporteDiario.fecha <= fecha_fin)
    if estado_pago:
        query = query.filter(ReporteDiario.estado_pago == estado_pago)

    return query.order_by(ReporteDiario.fecha.desc()).paginate(
        page=pagina, per_page=por_pagina, error_out=False
    )


def contar_reportes_hoy():
    """Cuenta reportes registrados hoy."""
    hoy = date.today()
    return ReporteDiario.query.filter_by(fecha=hoy).count()


def contar_pendientes():
    """Cuenta reportes con estado pendiente."""
    return ReporteDiario.query.filter_by(estado_pago='pendiente').count()
