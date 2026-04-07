"""
Rutas de nómina.
Generación de resúmenes para el cliente (SIN valores por día).
"""
from flask import Blueprint, render_template, request, flash, session
from flask_login import login_required
from app.models.empleado import Empleado
from app.services import nomina_service

nomina_bp = Blueprint('nomina', __name__, url_prefix='/admin/nomina')


@nomina_bp.route('/generar', methods=['GET', 'POST'])
@login_required
def generar():
    """Formulario para seleccionar empleados y rango de fechas."""
    empleados = Empleado.query.filter_by(estado='activo').order_by(Empleado.nombre).all()

    if request.method == 'POST':
        empleado_ids = request.form.getlist('empleado_ids', type=int)
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')

        if not empleado_ids:
            flash('❌ Debe seleccionar al menos un empleado.', 'danger')
            return render_template('admin/nomina/generar.html', empleados=empleados)

        if not fecha_inicio or not fecha_fin:
            flash('❌ Debe seleccionar el rango de fechas.', 'danger')
            return render_template('admin/nomina/generar.html', empleados=empleados)

        from datetime import datetime
        try:
            fi = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            ff = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except ValueError:
            flash('❌ Formato de fecha inválido.', 'danger')
            return render_template('admin/nomina/generar.html', empleados=empleados)

        if fi > ff:
            flash('❌ La fecha inicial no puede ser mayor a la final.', 'danger')
            return render_template('admin/nomina/generar.html', empleados=empleados)

        # Generar resúmenes
        resumenes = nomina_service.generar_resumen(empleado_ids, fi, ff)

        if not resumenes:
            flash('⚠️ No se encontraron datos para el rango seleccionado.', 'warning')
            return render_template('admin/nomina/generar.html', empleados=empleados)

        # Guardar parámetros en sesión para exportación
        session['nomina_empleado_ids'] = empleado_ids
        session['nomina_fecha_inicio'] = fecha_inicio
        session['nomina_fecha_fin'] = fecha_fin

        return render_template('admin/nomina/resumen.html',
                               resumenes=resumenes,
                               fecha_inicio=fi,
                               fecha_fin=ff)

    return render_template('admin/nomina/generar.html', empleados=empleados)
