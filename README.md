# 🌤️ Nomina-Sky

**Sistema de Gestión de Nómina y Reporte Diario de Empleados**

Aplicación web profesional desarrollada en Python con Flask para gestionar reportes de actividad diaria de empleados, calcular nóminas y generar resúmenes para el cliente.

## 🚀 Características Principales

- **Reporte Público**: Los empleados reportan actividades con su cédula (sin login)
- **Panel Admin**: Dashboard con estadísticas, gráficos y gestión completa
- **CRUD Empleados**: Crear, editar, activar/desactivar empleados
- **Gestión de Reportes**: Filtrar, editar valores por día, estados de pago
- **Bonos**: Asignar bonificaciones adicionales por empleado
- **Nómina**: Generar resúmenes SIN mostrar valores individuales por día
- **Exportación**: PDF y Excel con formato profesional
- **Auditoría**: Registro completo de acciones del sistema
- **Configuración**: Cambiar credenciales del administrador desde el panel

## 📋 Requisitos Previos

- Python 3.9 o superior
- pip (gestor de paquetes de Python)

## ⚡ Instalación Rápida

### 1. Clonar o descargar el proyecto

```bash
cd Nomina-Sky
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Editar el archivo `.env` según sea necesario:

```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=tu-clave-secreta-segura
DATABASE_URL=sqlite:///nomina_sky.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### 5. Inicializar base de datos y datos de prueba

```bash
flask db init
flask db migrate -m "Inicial"
flask db upgrade
python seed.py
```

### 6. Ejecutar la aplicación

```bash
flask run
```

O directamente:

```bash
python run.py
```

La aplicación estará disponible en: **http://localhost:5000**

## 🔐 Credenciales de Prueba

| Rol | Usuario | Contraseña |
|-----|---------|------------|
| Admin | admin | admin123 |

> Las credenciales se pueden cambiar desde: **Panel Admin → Configuración**

## 📱 Cédulas de Empleados de Prueba

| Empleado | Cédula |
|----------|--------|
| Carlos Andrés Pérez | 1030567890 |
| María Fernanda López | 1045678901 |
| Juan David Martínez | 1023456789 |
| Alejandra Ríos García | 1078901234 |
| Pedro Luis Hernández (inactivo) | 1012345678 |

## 🗂️ Estructura del Proyecto

```
Nomina-Sky/
├── app/
│   ├── __init__.py          # Application Factory
│   ├── config.py            # Configuración
│   ├── extensions.py        # Extensiones Flask
│   ├── models/              # Modelos SQLAlchemy
│   ├── forms/               # Formularios Flask-WTF
│   ├── routes/              # Blueprints (rutas)
│   ├── services/            # Lógica de negocio
│   ├── utils/               # Utilidades
│   ├── templates/           # Templates HTML
│   └── static/              # CSS, JS, imágenes
├── migrations/              # Migraciones Alembic
├── .env                     # Variables de entorno
├── requirements.txt         # Dependencias
├── seed.py                  # Datos de prueba
├── run.py                   # Punto de entrada
└── README.md
```

## 🔧 Tecnologías

- **Backend**: Python + Flask
- **Base de datos**: SQLite / PostgreSQL / MySQL
- **ORM**: SQLAlchemy
- **Frontend**: Bootstrap 5, Chart.js, SweetAlert2
- **Autenticación**: Flask-Login
- **Formularios**: Flask-WTF
- **Migraciones**: Flask-Migrate
- **Exportación**: ReportLab (PDF), openpyxl (Excel)

## 💰 Regla de Negocio Clave

> **Los resúmenes de nómina exportados NUNCA muestran el valor pagado por día individual.** Solo muestran el total final (suma de días + bonos). Los valores por día son de uso exclusivo del administrador.

## 📊 Migrar a PostgreSQL/MySQL

Cambiar la variable `DATABASE_URL` en `.env`:

```env
# PostgreSQL
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/nomina_sky

# MySQL
DATABASE_URL=mysql+pymysql://usuario:contraseña@localhost:3306/nomina_sky
```

Luego ejecutar:

```bash
flask db upgrade
python seed.py
```

## 📄 Licencia

Proyecto privado — Sky Soluciones © 2026
