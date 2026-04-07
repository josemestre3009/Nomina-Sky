"""
Script de carga de datos de prueba para Nomina-Sky.
Crea un admin por defecto, empleados de prueba, reportes y bonos.

Ejecutar con: flask seed
O directamente: python seed.py
"""
from datetime import date, timedelta, datetime
from app import create_app
from app.extensions import db
from app.models.admin import Administrador
from app.models.empleado import Empleado
from app.models.reporte import ReporteDiario
from app.models.bono import Bono


def seed_database(app=None):
    """Carga datos de prueba en la base de datos."""
    if app is None:
        app = create_app()

    with app.app_context():
        print('🔧 Creando tablas...')
        db.create_all()

        # ─── Admin por defecto ───
        admin = Administrador.query.filter_by(username='admin').first()
        if not admin:
            admin = Administrador(
                username=app.config.get('ADMIN_USERNAME', 'admin'),
                nombre_completo='Administrador Principal'
            )
            admin.set_password(app.config.get('ADMIN_PASSWORD', 'admin123'))
            db.session.add(admin)
            print('✅ Admin creado: admin / admin123')
        else:
            print('ℹ️  Admin ya existe.')

        # ─── Empleados de prueba ───
        empleados_data = [
            {
                'nombre': 'Carlos Andrés Pérez',
                'cedula': '1030567890',
                'cargo': 'Técnico de Soporte',
                'valor_dia_defecto': 120000,
                'estado': 'activo',
                'fecha_ingreso': date(2025, 3, 15)
            },
            {
                'nombre': 'María Fernanda López',
                'cedula': '1045678901',
                'cargo': 'Desarrolladora',
                'valor_dia_defecto': 180000,
                'estado': 'activo',
                'fecha_ingreso': date(2025, 1, 10)
            },
            {
                'nombre': 'Juan David Martínez',
                'cedula': '1023456789',
                'cargo': 'Analista de Redes',
                'valor_dia_defecto': 150000,
                'estado': 'activo',
                'fecha_ingreso': date(2025, 6, 1)
            },
            {
                'nombre': 'Alejandra Ríos García',
                'cedula': '1078901234',
                'cargo': 'Diseñadora UX',
                'valor_dia_defecto': 140000,
                'estado': 'activo',
                'fecha_ingreso': date(2025, 8, 20)
            },
            {
                'nombre': 'Pedro Luis Hernández',
                'cedula': '1012345678',
                'cargo': 'Técnico de Campo',
                'valor_dia_defecto': 100000,
                'estado': 'inactivo',
                'fecha_ingreso': date(2024, 11, 5)
            }
        ]

        empleados = []
        for data in empleados_data:
            emp = Empleado.query.filter_by(cedula=data['cedula']).first()
            if not emp:
                emp = Empleado(**data)
                db.session.add(emp)
                print(f'✅ Empleado creado: {emp.nombre} ({emp.cedula})')
            else:
                print(f'ℹ️  Empleado ya existe: {emp.nombre}')
            empleados.append(emp)

        db.session.flush()

        # ─── Reportes de prueba ───
        hoy = date.today()
        actividades = [
            'Instalación y configuración de equipos de red en oficina principal. Verificación de conectividad.',
            'Desarrollo de módulo de reportes para el sistema interno. Corrección de bugs en producción.',
            'Análisis de tráfico de red y optimización de firewall. Documentación de procedimientos.',
            'Diseño de interfaces para el nuevo portal web del cliente. Revisión con el equipo.',
            'Soporte técnico remoto a usuarios. Resolución de 15 tickets de mesa de ayuda.',
            'Capacitación al personal en uso de herramientas de colaboración. Creación de manual.',
            'Migración de servidor de correo. Verificación de cuentas y configuración DNS.',
            'Implementación de sistema de backup automatizado. Pruebas de restauración.',
            'Revisión de seguridad de la infraestructura. Actualización de parches críticos.',
            'Desarrollo de API REST para integración con sistema de nómina.',
            'Mantenimiento preventivo de equipos de cómputo. Limpieza y actualización de software.',
            'Configuración de VPN para acceso remoto seguro. Documentación de accesos.',
            'Análisis de requerimientos para nuevo proyecto. Reunión con stakeholders.',
            'Pruebas de rendimiento del servidor web. Optimización de consultas SQL.',
            'Instalación de cableado estructurado en nueva sede. Certificación de puntos.',
        ]

        estados = ['pendiente', 'revisado', 'pagado']
        reporte_count = 0

        for i, emp in enumerate(empleados[:4]):  # Solo empleados activos
            for j in range(5):  # 5 días por empleado
                fecha = hoy - timedelta(days=j + 1)
                existente = ReporteDiario.query.filter_by(
                    empleado_id=emp.id, fecha=fecha
                ).first()

                if not existente:
                    idx = (i * 5 + j) % len(actividades)
                    reporte = ReporteDiario(
                        empleado_id=emp.id,
                        fecha=fecha,
                        actividad=actividades[idx],
                        valor_dia_original=emp.valor_dia_defecto,
                        valor_dia_aplicado=emp.valor_dia_defecto,
                        estado_pago=estados[j % 3]
                    )
                    db.session.add(reporte)
                    reporte_count += 1

        print(f'✅ {reporte_count} reportes de prueba creados.')

        # ─── Bonos de prueba ───
        if not Bono.query.first():
            bono1 = Bono(
                empleado_id=empleados[1].id,  # María Fernanda
                valor=250000,
                descripcion='Bono por productividad Q1 2026',
                fecha_inicio=hoy - timedelta(days=30),
                fecha_fin=hoy
            )
            bono2 = Bono(
                empleado_id=empleados[0].id,  # Carlos Andrés
                valor=150000,
                descripcion='Bono por disponibilidad fin de semana',
                fecha_inicio=hoy - timedelta(days=15),
                fecha_fin=hoy
            )
            db.session.add_all([bono1, bono2])
            print('✅ 2 bonos de prueba creados.')
        else:
            print('ℹ️  Bonos ya existen.')

        db.session.commit()
        print('\n🎉 Datos de prueba cargados exitosamente.')
        print('─' * 40)
        print('Credenciales de administrador:')
        print(f'  Usuario: {app.config.get("ADMIN_USERNAME", "admin")}')
        print(f'  Contraseña: {app.config.get("ADMIN_PASSWORD", "admin123")}')
        print('─' * 40)


if __name__ == '__main__':
    seed_database()
