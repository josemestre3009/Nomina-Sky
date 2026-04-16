"""
Servicio de nómina.
Calcula resúmenes de nómina para empleados en un rango de fechas.
REGLA CLAVE: Los resúmenes para el cliente NO muestran valores por día.
"""
from app.extensions import db
from app.models.empleado import Empleado
from app.models.reporte import ReporteDiario
from app.models.bono import Bono


def generar_resumen(empleado_ids, fecha_inicio, fecha_fin):
    """
    Genera resumen de nómina para uno o varios empleados.

    Args:
        empleado_ids: Lista de IDs de empleados
        fecha_inicio: Fecha inicial del rango
        fecha_fin: Fecha final del rango

    Returns:
        Lista de dicts con resumen por empleado:
        {
            'empleado': Empleado,
            'reportes': [ReporteDiario],
            'dias_trabajados': int,
            'bonos': [Bono],
            'total_bonos': float,
            'total_dias': float,       # SOLO uso interno admin
            'total_final': float       # Total días + bonos
        }
    """
    resumenes = []

    for emp_id in empleado_ids:
        empleado = db.session.get(Empleado, emp_id)
        if not empleado:
            continue

        # Obtener reportes en el rango de fechas
        reportes = ReporteDiario.query.filter(
            ReporteDiario.empleado_id == emp_id,
            ReporteDiario.fecha >= fecha_inicio,
            ReporteDiario.fecha <= fecha_fin
        ).order_by(ReporteDiario.fecha.asc()).all()

        # Calcular total por días trabajados (valor_dia_aplicado)
        total_dias = sum(r.valor_dia_aplicado for r in reportes)
        dias_trabajados = sum(1 for r in reportes if r.estado_pago == 'revisado')
        dias_registrados = len(reportes)

        # Obtener bonos aplicables en el rango
        bonos = Bono.query.filter(
            Bono.empleado_id == emp_id,
            db.or_(
                # Bonos sin fecha (aplican siempre)
                db.and_(Bono.fecha_inicio.is_(None), Bono.fecha_fin.is_(None)),
                # Bonos con rango que intersecta
                db.and_(
                    Bono.fecha_inicio <= fecha_fin,
                    Bono.fecha_fin >= fecha_inicio
                ),
                # Bonos con solo fecha_inicio
                db.and_(
                    Bono.fecha_inicio.isnot(None),
                    Bono.fecha_fin.is_(None),
                    Bono.fecha_inicio >= fecha_inicio,
                    Bono.fecha_inicio <= fecha_fin
                )
            )
        ).all()

        total_bonos = sum(b.valor for b in bonos)
        total_final = total_dias + total_bonos

        resumenes.append({
            'empleado': empleado,
            'reportes': reportes,
            'dias_trabajados': dias_trabajados,
            'dias_registrados': dias_registrados,
            'bonos': bonos,
            'total_bonos': total_bonos,
            'total_dias': total_dias,         # Solo para el admin
            'total_final': total_final
        })

    return resumenes


def obtener_estadisticas_dashboard(fecha_inicio=None, fecha_fin=None):
    """
    Obtiene estadísticas generales para el dashboard.
    """
    from datetime import date, timedelta
    from sqlalchemy import func

    hoy = date.today()

    # Empleados activos
    empleados_activos = Empleado.query.filter_by(estado='activo').count()

    # Reportes de hoy
    reportes_hoy = ReporteDiario.query.filter_by(fecha=hoy).count()

    # Pendientes
    pendientes = ReporteDiario.query.filter_by(estado_pago='pendiente').count()

    # Total pagado (en rango o todo)
    query_pagado = db.session.query(func.sum(ReporteDiario.valor_dia_aplicado)).filter(
        ReporteDiario.estado_pago == 'pagado'
    )
    if fecha_inicio and fecha_fin:
        query_pagado = query_pagado.filter(
            ReporteDiario.fecha >= fecha_inicio,
            ReporteDiario.fecha <= fecha_fin
        )
    total_pagado = query_pagado.scalar() or 0

    # Total pendiente
    total_pendiente = db.session.query(
        func.sum(ReporteDiario.valor_dia_aplicado)
    ).filter(
        ReporteDiario.estado_pago.in_(['pendiente', 'revisado'])
    ).scalar() or 0

    # Reportes por día (últimos 7 días) para gráfico
    reportes_semana = []
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        count = ReporteDiario.query.filter_by(fecha=dia).count()
        reportes_semana.append({
            'fecha': dia.strftime('%d/%m'),
            'cantidad': count
        })

    # Top empleados por reportes este mes
    inicio_mes = hoy.replace(day=1)
    top_empleados = db.session.query(
        Empleado.nombre,
        func.count(ReporteDiario.id).label('total')
    ).join(ReporteDiario).filter(
        ReporteDiario.fecha >= inicio_mes
    ).group_by(Empleado.id).order_by(
        func.count(ReporteDiario.id).desc()
    ).limit(5).all()

    return {
        'empleados_activos': empleados_activos,
        'reportes_hoy': reportes_hoy,
        'pendientes': pendientes,
        'total_pagado': total_pagado,
        'total_pendiente': total_pendiente,
        'reportes_semana': reportes_semana,
        'top_empleados': [{'nombre': e[0], 'total': e[1]} for e in top_empleados]
    }
