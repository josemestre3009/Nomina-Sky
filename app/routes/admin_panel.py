"""
Panel de administración.
Dashboard, CRUD de empleados, auditoría y configuración.
"""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.extensions import db
from app.models.empleado import Empleado
from app.models.bono import Bono
from app.forms.empleado_forms import EmpleadoForm
from app.forms.bono_forms import BonoForm
from app.forms.auth_forms import CambiarCredencialesForm
from app.services import audit_service, nomina_service
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ─── DASHBOARD ───────────────────────────────────────────────

@admin_bp.route('/')
@login_required
def dashboard():
    """Panel principal con estadísticas y gráficos."""
    from app.models.reporte import ReporteDiario
    stats = nomina_service.obtener_estadisticas_dashboard()
    # Últimos 8 reportes para la tabla del dashboard
    recent_reports = ReporteDiario.query.join(Empleado).order_by(
        ReporteDiario.fecha.desc(), ReporteDiario.created_at.desc()
    ).limit(8).all()
    return render_template('admin/dashboard.html', stats=stats, recent_reports=recent_reports)


# ─── EMPLEADOS ───────────────────────────────────────────────

@admin_bp.route('/empleados')
@login_required
def empleados_lista():
    """Lista de todos los empleados con paginación y búsqueda."""
    page = request.args.get('page', 1, type=int)
    buscar = request.args.get('buscar', '')
    estado = request.args.get('estado', '')

    query = Empleado.query

    if buscar:
        query = query.filter(
            db.or_(
                Empleado.nombre.ilike(f'%{buscar}%'),
                Empleado.cedula.contains(buscar)
            )
        )
    if estado:
        query = query.filter_by(estado=estado)

    empleados = query.order_by(Empleado.nombre.asc()).paginate(
        page=page, per_page=15, error_out=False
    )

    return render_template('admin/empleados/lista.html',
                           empleados=empleados, buscar=buscar, estado=estado)


@admin_bp.route('/empleados/crear', methods=['GET', 'POST'])
@login_required
def empleados_crear():
    """Crear nuevo empleado."""
    form = EmpleadoForm()

    if form.validate_on_submit():
        # Verificar cédula única
        existe = Empleado.query.filter_by(cedula=form.cedula.data.strip()).first()
        if existe:
            flash('❌ Ya existe un empleado con esa cédula.', 'danger')
            return render_template('admin/empleados/crear.html', form=form)

        empleado = Empleado(
            nombre=form.nombre.data.strip(),
            cedula=form.cedula.data.strip(),
            cargo=form.cargo.data.strip(),
            valor_dia_defecto=form.valor_dia_defecto.data,
            estado=form.estado.data,
            fecha_ingreso=form.fecha_ingreso.data or date.today()
        )
        db.session.add(empleado)

        audit_service.registrar(
            entidad='empleado',
            entidad_id=None,
            accion='crear',
            descripcion=f'Empleado creado: {empleado.nombre}',
            valores_nuevos={
                'nombre': empleado.nombre,
                'cedula': empleado.cedula,
                'cargo': empleado.cargo,
                'valor_dia': empleado.valor_dia_defecto
            },
            usuario=current_user.username
        )
        db.session.commit()
        flash(f'✅ Empleado {empleado.nombre} creado exitosamente.', 'success')
        return redirect(url_for('admin.empleados_lista'))

    if not form.fecha_ingreso.data:
        form.fecha_ingreso.data = date.today()

    return render_template('admin/empleados/crear.html', form=form)


@admin_bp.route('/empleados/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def empleados_editar(id):
    """Editar empleado existente."""
    empleado = Empleado.query.get_or_404(id)
    form = EmpleadoForm(obj=empleado)

    if form.validate_on_submit():
        # Verificar cédula única (excluyendo al actual)
        existe = Empleado.query.filter(
            Empleado.cedula == form.cedula.data.strip(),
            Empleado.id != id
        ).first()
        if existe:
            flash('❌ Ya existe otro empleado con esa cédula.', 'danger')
            return render_template('admin/empleados/editar.html', form=form, empleado=empleado)

        # Guardar valores anteriores para auditoría
        valores_ant = {
            'nombre': empleado.nombre,
            'cedula': empleado.cedula,
            'cargo': empleado.cargo,
            'valor_dia': empleado.valor_dia_defecto,
            'estado': empleado.estado
        }

        empleado.nombre = form.nombre.data.strip()
        empleado.cedula = form.cedula.data.strip()
        empleado.cargo = form.cargo.data.strip()
        empleado.valor_dia_defecto = form.valor_dia_defecto.data
        empleado.estado = form.estado.data
        if form.fecha_ingreso.data:
            empleado.fecha_ingreso = form.fecha_ingreso.data

        audit_service.registrar(
            entidad='empleado',
            entidad_id=empleado.id,
            accion='editar',
            descripcion=f'Empleado editado: {empleado.nombre}',
            valores_anteriores=valores_ant,
            valores_nuevos={
                'nombre': empleado.nombre,
                'cedula': empleado.cedula,
                'cargo': empleado.cargo,
                'valor_dia': empleado.valor_dia_defecto,
                'estado': empleado.estado
            },
            usuario=current_user.username
        )
        db.session.commit()
        flash(f'✅ Empleado {empleado.nombre} actualizado.', 'success')
        return redirect(url_for('admin.empleados_lista'))

    return render_template('admin/empleados/editar.html', form=form, empleado=empleado)


@admin_bp.route('/empleados/<int:id>/eliminar', methods=['POST'])
@login_required
def empleados_eliminar(id):
    """Eliminar empleado y sus registros (reportes, bonos) en cascada."""
    empleado = Empleado.query.get_or_404(id)

    audit_service.registrar(
        entidad='empleado',
        entidad_id=empleado.id,
        accion='eliminar',
        descripcion=f'Empleado eliminado: {empleado.nombre} ({empleado.cedula})',
        valores_anteriores={
            'nombre': empleado.nombre,
            'cedula': empleado.cedula,
            'cargo': empleado.cargo
        },
        usuario=current_user.username
    )
    db.session.delete(empleado)
    db.session.commit()
    flash(f'✅ Empleado \'{empleado.nombre}\' eliminado permanentemente.', 'success')
    return redirect(url_for('admin.empleados_lista'))


# ─── BONOS ───────────────────────────────────────────────────

@admin_bp.route('/bonos')
@login_required
def bonos_lista():
    """Lista de todos los bonos."""
    page = request.args.get('page', 1, type=int)
    bonos = Bono.query.join(Empleado).order_by(Bono.fecha_creacion.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template('admin/bonos/lista.html', bonos=bonos)


@admin_bp.route('/bonos/crear', methods=['GET', 'POST'])
@login_required
def bonos_crear():
    """Crear nuevo bono."""
    form = BonoForm()
    # Cargar empleados activos en el select
    form.empleado_id.choices = [
        (e.id, f'{e.nombre} ({e.cedula})')
        for e in Empleado.query.filter_by(estado='activo').order_by(Empleado.nombre).all()
    ]

    if form.validate_on_submit():
        bono = Bono(
            empleado_id=form.empleado_id.data,
            valor=form.valor.data,
            descripcion=form.descripcion.data.strip(),
            fecha_inicio=form.fecha_inicio.data,
            fecha_fin=form.fecha_fin.data
        )
        db.session.add(bono)

        empleado = db.session.get(Empleado, form.empleado_id.data)
        audit_service.registrar(
            entidad='bono',
            entidad_id=None,
            accion='crear',
            descripcion=f'Bono creado para {empleado.nombre}: {bono.descripcion}',
            valores_nuevos={
                'empleado': empleado.nombre,
                'valor': bono.valor,
                'descripcion': bono.descripcion
            },
            usuario=current_user.username
        )
        db.session.commit()
        flash(f'✅ Bono creado exitosamente para {empleado.nombre}.', 'success')
        return redirect(url_for('admin.bonos_lista'))

    return render_template('admin/bonos/crear.html', form=form)


@admin_bp.route('/bonos/<int:id>/eliminar', methods=['POST'])
@login_required
def bonos_eliminar(id):
    """Eliminar bono."""
    bono = Bono.query.get_or_404(id)

    audit_service.registrar(
        entidad='bono',
        entidad_id=bono.id,
        accion='eliminar',
        descripcion=f'Bono eliminado: {bono.descripcion}',
        valores_anteriores={
            'empleado_id': bono.empleado_id,
            'valor': bono.valor,
            'descripcion': bono.descripcion
        },
        usuario=current_user.username
    )
    db.session.delete(bono)
    db.session.commit()
    flash('✅ Bono eliminado correctamente.', 'success')
    return redirect(url_for('admin.bonos_lista'))


# ─── AUDITORÍA ───────────────────────────────────────────────

@admin_bp.route('/auditoria')
@login_required
def auditoria():
    """Log de auditoría del sistema."""
    page = request.args.get('page', 1, type=int)
    entidad = request.args.get('entidad', '')
    accion = request.args.get('accion', '')

    registros = audit_service.obtener_registros(
        pagina=page,
        por_pagina=20,
        entidad=entidad or None,
        accion=accion or None
    )
    return render_template('admin/auditoria.html',
                           registros=registros, entidad=entidad, accion=accion)


# ─── CONFIGURACIÓN ───────────────────────────────────────────

@admin_bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
def configuracion():
    """Configuración del sistema — cambiar credenciales del admin."""
    form = CambiarCredencialesForm()
    form.username.data = form.username.data or current_user.username

    if form.validate_on_submit():
        # Verificar contraseña actual
        if not current_user.check_password(form.password_actual.data):
            flash('❌ La contraseña actual es incorrecta.', 'danger')
            return render_template('admin/configuracion.html', form=form)

        valores_ant = {'username': current_user.username}
        cambios = []

        # Cambiar username
        if form.username.data.strip() and form.username.data.strip() != current_user.username:
            current_user.username = form.username.data.strip()
            cambios.append('usuario actualizado')

        # Cambiar contraseña (solo si se proporcionó)
        if form.password_nueva.data:
            if form.password_nueva.data != form.password_confirmar.data:
                flash('❌ Las contraseñas nuevas no coinciden.', 'danger')
                return render_template('admin/configuracion.html', form=form)
            if len(form.password_nueva.data) < 4:
                flash('❌ La nueva contraseña debe tener al menos 4 caracteres.', 'danger')
                return render_template('admin/configuracion.html', form=form)
            current_user.set_password(form.password_nueva.data)
            cambios.append('contraseña actualizada')

        if cambios:
            audit_service.registrar(
                entidad='config',
                entidad_id=current_user.id,
                accion='config',
                descripcion=f'Configuración actualizada: {", ".join(cambios)}',
                valores_anteriores=valores_ant,
                valores_nuevos={'username': current_user.username},
                usuario=current_user.username
            )
            db.session.commit()
            flash(f'✅ Configuración actualizada: {", ".join(cambios)}.', 'success')
        else:
            flash('No se detectaron cambios.', 'info')

        return redirect(url_for('admin.configuracion'))

    # Pre-llenar username en GET
    if request.method == 'GET':
        form.username.data = current_user.username

    return render_template('admin/configuracion.html', form=form)
