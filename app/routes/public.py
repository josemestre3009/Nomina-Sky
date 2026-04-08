"""
Rutas públicas.
Permite a los empleados reportar actividades sin necesidad de login.
"""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models.empleado import Empleado
from app.services.reporte_service import crear_reporte, ReporteError
from app.forms.reporte_forms import ReportePublicoForm
from app.extensions import limiter

public_bp = Blueprint('public', __name__)


@public_bp.route('/', methods=['GET', 'POST'])
def reporte():
    """Formulario público para reporte de actividad diaria."""
    form = ReportePublicoForm()

    if request.method == 'GET':
        cedula_arg = request.args.get('cedula')
        if cedula_arg:
            form.cedula.data = cedula_arg

    if form.validate_on_submit():
        try:
            reporte = crear_reporte(
                cedula=form.cedula.data.strip(),
                fecha=form.fecha.data,
                actividad=form.actividad.data.strip()
            )
            flash('✅ Reporte enviado exitosamente. ¡Gracias!', 'success')
            return redirect(url_for('public.confirmacion',
                                    nombre=reporte.empleado.nombre,
                                    fecha=reporte.fecha.strftime('%d/%m/%Y'),
                                    cedula=reporte.empleado.cedula))
        except ReporteError as e:
            flash(f'❌ {str(e)}', 'danger')

    # Establecer fecha por defecto a hoy
    if not form.fecha.data:
        form.fecha.data = date.today()

    return render_template('public/reporte.html', form=form)


@public_bp.route('/confirmacion')
def confirmacion():
    """Página de confirmación después de enviar reporte."""
    nombre = request.args.get('nombre', 'Empleado')
    fecha = request.args.get('fecha', '')
    cedula = request.args.get('cedula', '')
    return render_template('public/confirmacion.html', nombre=nombre, fecha=fecha, cedula=cedula)


@public_bp.route('/buscar-empleado/<cedula>')
@limiter.limit('30/minute')
def buscar_empleado(cedula):
    """API para buscar empleado por cédula (AJAX)."""
    empleado = Empleado.query.filter_by(cedula=cedula.strip()).first()
    if empleado and empleado.esta_activo:
        return jsonify({
            'encontrado': True,
            'nombre': empleado.nombre,
            'cargo': empleado.cargo,
            'cedula': empleado.cedula
        })
    return jsonify({'encontrado': False})
