# Usar una imagen ligera de Python
FROM python:3.9-slim

# Evitar que Python genere archivos .pyc y permitir logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Configurar Zona Horaria (Crucial para que datetime.now() de la nómina no quede en UTC)
ENV TZ=America/Bogota

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias (para ReportLab u otras libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Asegurarse de que exista la carpeta instance para la base de datos SQLite
RUN mkdir -p /app/instance

# Declarar que la carpeta instance debe ser persistente
VOLUME ["/app/instance"]

# Exponer el puerto de Flask
EXPOSE 8000

# Comando para iniciar la aplicación (usando Gunicorn para producción)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]