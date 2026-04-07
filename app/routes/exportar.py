"""
Rutas de exportación.
Genera archivos PDF y Excel con resúmenes de nómina.
"""
from datetime import datetime
from flask import Blueprint, session, flash, redirect, url_for, send_file
from flask_login import login_required
from app.services import nomina_service, export_service

exportar_bp = Blueprint('exportar', __name__, url_prefix='/admin/exportar')


@exportar_bp.route('/pdf')
@login_required
def pdf():
    """Exportar resumen de nómina como PDF."""
    params = _obtener_parametros_sesion()
    if params is None:
        return redirect(url_for('nomina.generar'))

    empleado_ids, fecha_inicio, fecha_fin = params
    resumenes = nomina_service.generar_resumen(empleado_ids, fecha_inicio, fecha_fin)

    if not resumenes:
        flash('⚠️ No hay datos para exportar.', 'warning')
        return redirect(url_for('nomina.generar'))

    buffer = export_service.generar_pdf(resumenes, fecha_inicio, fecha_fin)

    nombre_archivo = f'nomina_{fecha_inicio.strftime("%Y%m%d")}_{fecha_fin.strftime("%Y%m%d")}.pdf'
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=nombre_archivo
    )


@exportar_bp.route('/excel')
@login_required
def excel():
    """Exportar resumen de nómina como Excel."""
    params = _obtener_parametros_sesion()
    if params is None:
        return redirect(url_for('nomina.generar'))

    empleado_ids, fecha_inicio, fecha_fin = params
    resumenes = nomina_service.generar_resumen(empleado_ids, fecha_inicio, fecha_fin)

    if not resumenes:
        flash('⚠️ No hay datos para exportar.', 'warning')
        return redirect(url_for('nomina.generar'))

    buffer = export_service.generar_excel(resumenes, fecha_inicio, fecha_fin)

    nombre_archivo = f'nomina_{fecha_inicio.strftime("%Y%m%d")}_{fecha_fin.strftime("%Y%m%d")}.xlsx'
    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=nombre_archivo
    )


def _obtener_parametros_sesion():
    """Obtiene los parámetros de nómina guardados en sesión."""
    empleado_ids = session.get('nomina_empleado_ids')
    fecha_inicio_str = session.get('nomina_fecha_inicio')
    fecha_fin_str = session.get('nomina_fecha_fin')

    if not all([empleado_ids, fecha_inicio_str, fecha_fin_str]):
        flash('❌ Primero debe generar un resumen de nómina.', 'danger')
        return None

    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        flash('❌ Error en los parámetros de fecha.', 'danger')
        return None

    return empleado_ids, fecha_inicio, fecha_fin
