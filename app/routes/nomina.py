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


@nomina_bp.route('/api/ajuste', methods=['POST'])
@login_required
def api_agregar_ajuste():
    """API: Agrega un adicional o descuento (Bono) a una nómina en curso."""
    from app.extensions import db, csrf
    from app.models.empleado import Empleado
    from app.models.bono import Bono
    from app.services import audit_service
    from flask_login import current_user
    from flask import jsonify
    from datetime import datetime
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se enviaron datos.'}), 400
        
    empleado_id = data.get('empleado_id')
    valor = data.get('valor')
    descripcion = str(data.get('descripcion', '')).strip()
    fecha_fin_str = data.get('fecha_fin')
    
    if not all([empleado_id, valor, descripcion, fecha_fin_str]):
        return jsonify({'error': 'Faltan campos obligatorios.'}), 400
        
    try:
        valor = float(valor)
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Valor o fecha con formato inválido.'}), 400
        
    empleado = db.session.get(Empleado, empleado_id)
    if not empleado:
        return jsonify({'error': 'Empleado no encontrado.'}), 404
        
    # Creamos un bono asociado exclusivamente a la fecha_fin de la nómina
    nuevo_ajuste = Bono(
        empleado_id=empleado.id,
        valor=valor,
        descripcion=descripcion,
        fecha_inicio=fecha_fin,  # Esto hace que aplique al mes correspondiente
        fecha_fin=fecha_fin
    )
    
    db.session.add(nuevo_ajuste)
    
    tipo_ajuste = "Adicional" if valor >= 0 else "Descuento"
    audit_service.registrar(
        entidad='bono',
        entidad_id=None,
        accion='crear',
        descripcion=f'{tipo_ajuste} desde Nómina: {empleado.nombre} - {descripcion}',
        valores_nuevos={'valor': valor, 'fecha': fecha_fin_str},
        usuario=current_user.username
    )
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{tipo_ajuste} guardado correctamente.',
        'ajuste_id': nuevo_ajuste.id
    })


@nomina_bp.route('/api/ajuste/editar/<int:ajuste_id>', methods=['POST'])
@login_required
def api_editar_ajuste(ajuste_id):
    """API: Edita un adicional o descuento (Bono) existente."""
    from app.extensions import db
    from app.models.bono import Bono
    from app.services import audit_service
    from flask_login import current_user
    from flask import jsonify

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se enviaron datos.'}), 400

    valor = data.get('valor')
    descripcion = str(data.get('descripcion', '')).strip()

    if not all([valor is not None, descripcion]):
        return jsonify({'error': 'Faltan campos obligatorios.'}), 400

    try:
        valor = float(valor)
    except ValueError:
        return jsonify({'error': 'Valor con formato inválido.'}), 400

    ajuste = db.session.get(Bono, ajuste_id)
    if not ajuste:
        return jsonify({'error': 'Ajuste no encontrado.'}), 404

    valores_anteriores = {'valor': ajuste.valor, 'descripcion': ajuste.descripcion}
    
    ajuste.valor = valor
    ajuste.descripcion = descripcion

    tipo_ajuste = "Adicional" if valor >= 0 else "Descuento"
    audit_service.registrar(
        entidad='bono',
        entidad_id=ajuste.id,
        accion='actualizar',
        descripcion=f'Edición de {tipo_ajuste} desde Nómina: {ajuste.descripcion}',
        valores_anteriores=valores_anteriores,
        valores_nuevos={'valor': ajuste.valor, 'descripcion': ajuste.descripcion},
        usuario=current_user.username
    )

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Ajuste editado correctamente.'
    })


@nomina_bp.route('/api/ajuste/eliminar/<int:ajuste_id>', methods=['POST', 'DELETE'])
@login_required
def api_eliminar_ajuste(ajuste_id):
    """API: Elimina un adicional o descuento (Bono)."""
    from app.extensions import db
    from app.models.bono import Bono
    from app.services import audit_service
    from flask_login import current_user
    from flask import jsonify

    ajuste = db.session.get(Bono, ajuste_id)
    if not ajuste:
        return jsonify({'error': 'Ajuste no encontrado.'}), 404

    valores_anteriores = {'valor': ajuste.valor, 'descripcion': ajuste.descripcion}
    
    db.session.delete(ajuste)
    
    audit_service.registrar(
        entidad='bono',
        entidad_id=ajuste_id,
        accion='eliminar',
        descripcion=f'Eliminación de Ajuste (Nomina): {ajuste.descripcion}',
        valores_anteriores=valores_anteriores,
        usuario=current_user.username
    )

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Ajuste eliminado correctamente.'
    })
