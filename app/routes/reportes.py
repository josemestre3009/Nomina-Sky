"""
Rutas de gestión de reportes.
Vista de calendario interactivo para gestionar reportes por empleado.
"""
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.extensions import db, csrf
from app.models.reporte import ReporteDiario
from app.models.empleado import Empleado
from app.forms.reporte_forms import FiltroReporteForm
from app.services import audit_service

reportes_bp = Blueprint('reportes', __name__, url_prefix='/admin/reportes')


@reportes_bp.route('/')
@login_required
def lista():
    """Vista principal: calendario de reportes por empleado."""
    empleados = Empleado.query.filter_by(estado='activo').order_by(Empleado.nombre).all()
    empleado_id = request.args.get('empleado_id', type=int)
    mes = request.args.get('mes', type=int, default=date.today().month)
    anio = request.args.get('anio', type=int, default=date.today().year)

    empleado_actual = None
    if empleado_id:
        empleado_actual = db.session.get(Empleado, empleado_id)
    elif empleados:
        empleado_actual = empleados[0]
        empleado_id = empleado_actual.id

    return render_template('admin/reportes/calendario.html',
                           empleados=empleados,
                           empleado_actual=empleado_actual,
                           mes=mes, anio=anio)


@reportes_bp.route('/api/reportes/<int:empleado_id>/<int:anio>/<int:mes>')
@login_required
def api_reportes_mes(empleado_id, anio, mes):
    """API: Obtener reportes de un empleado en un mes específico."""
    reportes = ReporteDiario.query.filter(
        ReporteDiario.empleado_id == empleado_id,
        db.extract('year', ReporteDiario.fecha) == anio,
        db.extract('month', ReporteDiario.fecha) == mes
    ).order_by(ReporteDiario.fecha).all()

    data = []
    for r in reportes:
        data.append({
            'id': r.id,
            'dia': r.fecha.day,
            'fecha': r.fecha.strftime('%d/%m/%Y'),
            'actividad': r.actividad,
            'valor_dia_original': r.valor_dia_original,
            'valor_dia_aplicado': r.valor_dia_aplicado,
            'estado_pago': r.estado_pago
        })

    return jsonify(data)


@reportes_bp.route('/api/reportes/todos/<int:anio>/<int:mes>')
@login_required
def api_reportes_todos_mes(anio, mes):
    """API: Obtener reportes de TODOS los empleados en un mes específico."""
    reportes = ReporteDiario.query.filter(
        db.extract('year', ReporteDiario.fecha) == anio,
        db.extract('month', ReporteDiario.fecha) == mes
    ).join(Empleado).order_by(ReporteDiario.fecha, Empleado.nombre).all()

    data = []
    for r in reportes:
        data.append({
            'id': r.id,
            'dia': r.fecha.day,
            'fecha': r.fecha.strftime('%d/%m/%Y'),
            'empleado_id': r.empleado_id,
            'empleado_nombre': r.empleado.nombre,
            'actividad': r.actividad,
            'valor_dia_original': r.valor_dia_original,
            'valor_dia_aplicado': r.valor_dia_aplicado,
            'estado_pago': r.estado_pago
        })

    return jsonify(data)


@reportes_bp.route('/api/reporte/<int:id>', methods=['PUT'])
@login_required
def api_actualizar_reporte(id):
    """API: Actualizar actividad, valor y estado de un reporte."""
    reporte = ReporteDiario.query.get_or_404(id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No se recibieron datos.'}), 400

    # Guardar valores anteriores para auditoría
    valores_ant = {
        'actividad': reporte.actividad[:100],
        'valor_dia_aplicado': reporte.valor_dia_aplicado,
        'estado_pago': reporte.estado_pago
    }

    # Sanitizar y validar
    if 'actividad' in data:
        actividad = str(data['actividad']).strip()[:2000]
        if len(actividad) < 5:
            return jsonify({'error': 'La actividad debe tener al menos 5 caracteres.'}), 400
        reporte.actividad = actividad

    if 'valor_dia_aplicado' in data:
        try:
            valor = float(data['valor_dia_aplicado'])
            if valor < 0:
                return jsonify({'error': 'El valor no puede ser negativo.'}), 400
            reporte.valor_dia_aplicado = valor
        except (ValueError, TypeError):
            return jsonify({'error': 'Valor inválido.'}), 400

    if 'estado_pago' in data:
        estado = str(data['estado_pago']).strip()
        if estado not in ('pendiente', 'revisado', 'ausente'):
            return jsonify({'error': 'Estado inválido.'}), 400
        reporte.estado_pago = estado

    audit_service.registrar(
        entidad='reporte',
        entidad_id=reporte.id,
        accion='editar',
        descripcion=f'Reporte editado: {reporte.empleado.nombre} - {reporte.fecha.strftime("%d/%m/%Y")}',
        valores_anteriores=valores_ant,
        valores_nuevos={
            'actividad': reporte.actividad[:100],
            'valor_dia_aplicado': reporte.valor_dia_aplicado,
            'estado_pago': reporte.estado_pago
        },
        usuario=current_user.username
    )
    db.session.commit()

    return jsonify({'success': True, 'message': 'Reporte actualizado.'})


@reportes_bp.route('/api/reporte/<int:id>', methods=['DELETE'])
@login_required
def api_eliminar_reporte(id):
    """API: Eliminar un reporte."""
    reporte = ReporteDiario.query.get_or_404(id)

    audit_service.registrar(
        entidad='reporte',
        entidad_id=reporte.id,
        accion='eliminar',
        descripcion=f'Reporte eliminado: {reporte.empleado.nombre} - {reporte.fecha.strftime("%d/%m/%Y")}',
        valores_anteriores={
            'empleado': reporte.empleado.nombre,
            'fecha': reporte.fecha.strftime('%d/%m/%Y'),
            'actividad': reporte.actividad[:100],
            'valor_dia_aplicado': reporte.valor_dia_aplicado
        },
        usuario=current_user.username
    )
    db.session.delete(reporte)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Reporte eliminado.'})


@reportes_bp.route('/api/reporte/admin_crear', methods=['POST'])
@login_required
def api_crear_reporte_admin():
    """API: Crear un reporte manualmente desde el calendario (ej: Ausencia)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se recibieron datos.'}), 400

    empleado_id = data.get('empleado_id')
    fecha_str = data.get('fecha')
    actividad = str(data.get('actividad', '')).strip()[:2000]
    valor_dia = data.get('valor_dia_aplicado', 0)
    estado = data.get('estado_pago', 'ausente')

    if not empleado_id or not fecha_str or len(actividad) < 5:
        return jsonify({'error': 'Faltan datos obligatorios o actividad muy corta.'}), 400

    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Fecha inválida.'}), 400

    if estado not in ('pendiente', 'revisado', 'ausente'):
        return jsonify({'error': 'Estado inválido.'}), 400

    # Verificar si ya existe reporte
    existe = ReporteDiario.query.filter_by(empleado_id=empleado_id, fecha=fecha_obj).first()
    if existe:
        return jsonify({'error': 'Ya existe un reporte para esta fecha.'}), 400

    empleado = db.session.get(Empleado, empleado_id)
    if not empleado:
        return jsonify({'error': 'Empleado no encontrado.'}), 404

    reporte = ReporteDiario(
        empleado_id=empleado.id,
        fecha=fecha_obj,
        actividad=actividad,
        valor_dia_original=empleado.valor_dia_defecto,
        valor_dia_aplicado=float(valor_dia),
        estado_pago=estado
    )
    db.session.add(reporte)

    audit_service.registrar(
        entidad='reporte',
        entidad_id=None,
        accion='crear',
        descripcion=f'Reporte manual creado: {empleado.nombre} - {fecha_str}',
        valores_nuevos={
            'actividad': reporte.actividad[:100],
            'valor_dia_aplicado': reporte.valor_dia_aplicado,
            'estado_pago': reporte.estado_pago
        },
        usuario=current_user.username
    )
    db.session.commit()

    return jsonify({'success': True, 'message': 'Reporte guardado.'})


@reportes_bp.route('/api/reporte/admin_crear_masivo', methods=['POST'])
@login_required
def api_crear_reporte_masivo():
    """API: Crear reportes masivamente para empleados sin registro en un día."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se recibieron datos.'}), 400

    fecha_str = data.get('fecha')
    actividad = str(data.get('actividad', 'Trabajó jornada habitual')).strip()[:2000]
    estado = data.get('estado_pago', 'revisado')

    if not fecha_str or len(actividad) < 3:
        return jsonify({'error': 'Faltan datos obligatorios o actividad muy corta.'}), 400

    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Fecha inválida.'}), 400

    empleados_activos = Empleado.query.filter_by(estado='activo').all()
    if not empleados_activos:
        return jsonify({'error': 'No hay empleados activos.'}), 400

    # Filtrar los que ya tienen reporte
    existentes = ReporteDiario.query.filter_by(fecha=fecha_obj).all()
    ids_ya_con_reporte = {r.empleado_id for r in existentes}

    nuevos = 0
    for emp in empleados_activos:
        if emp.id not in ids_ya_con_reporte:
            reporte = ReporteDiario(
                empleado_id=emp.id,
                fecha=fecha_obj,
                actividad=actividad,
                valor_dia_original=emp.valor_dia_defecto,
                valor_dia_aplicado=emp.valor_dia_defecto,
                estado_pago=estado
            )
            db.session.add(reporte)
            nuevos += 1

    if nuevos == 0:
        return jsonify({'success': True, 'message': 'Todos los empleados ya tenían reporte para este día.', 'creados': 0})

    audit_service.registrar(
        entidad='reporte',
        entidad_id=None,
        accion='crear',
        descripcion=f'Reportes masivos creados para {nuevos} empleados - {fecha_str}',
        valores_nuevos={'estado_pago': estado, 'cantidad': nuevos},
        usuario=current_user.username
    )
    db.session.commit()

    return jsonify({'success': True, 'message': f'Se registraron {nuevos} asistencias masivas.', 'creados': nuevos})


@reportes_bp.route('/api/reporte/bulk_update', methods=['POST'])
@login_required
def api_actualizar_reportes_bulk():
    """API: Actualizar o crear múltiples reportes en una sola transacción."""
    data = request.get_json()
    if not data or 'reportes' not in data:
        return jsonify({'error': 'No se recibieron datos de reportes.'}), 400

    reportes_data = data['reportes']
    fecha_str = data.get('fecha')
    
    if not fecha_str:
        return jsonify({'error': 'Fecha no especificada.'}), 400

    try:
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Fecha inválida.'}), 400

    actualizados = 0
    creados = 0
    errores = []

    for r_data in reportes_data:
        emp_id = r_data.get('empleado_id')
        actividad = str(r_data.get('actividad', '')).strip()[:2000]
        valor = r_data.get('valor_dia_aplicado', 0)
        estado = r_data.get('estado_pago')

        if not emp_id or not estado:
            continue

        # No forzar texto automático. Se guarda lo que el usuario haya escrito.
        if not actividad:
            actividad = ""

        # Buscar si ya existe
        reporte = ReporteDiario.query.filter_by(empleado_id=emp_id, fecha=fecha_obj).first()
        
        try:
            if reporte:
                reporte.actividad = actividad
                reporte.valor_dia_aplicado = float(valor)
                reporte.estado_pago = estado
                actualizados += 1
            else:
                empleado = db.session.get(Empleado, emp_id)
                if not empleado:
                    errores.append(f"Empleado {emp_id} no encontrado.")
                    continue
                
                nuevo_reporte = ReporteDiario(
                    empleado_id=emp_id,
                    fecha=fecha_obj,
                    actividad=actividad,
                    valor_dia_original=empleado.valor_dia_defecto,
                    valor_dia_aplicado=float(valor),
                    estado_pago=estado
                )
                db.session.add(nuevo_reporte)
                creados += 1
        except Exception as e:
            errores.append(f"Error con empleado {emp_id}: {str(e)}")

    if errores and not actualizados and not creados:
        return jsonify({'error': 'No se pudo procesar ningún reporte.', 'detalles': errores}), 400

    audit_service.registrar(
        entidad='reporte',
        entidad_id=None,
        accion='editar_masivo',
        descripcion=f'Actualización masiva de reportes para el {fecha_str} ({actualizados} act, {creados} cre)',
        valores_nuevos={'fecha': fecha_str, 'actualizados': actualizados, 'creados': creados},
        usuario=current_user.username
    )
    
    db.session.commit()

    return jsonify({
        'success': True, 
        'message': f'Se procesaron {actualizados + creados} reportes correctamente.',
        'actualizados': actualizados,
        'creados': creados,
        'errores': errores
    })
