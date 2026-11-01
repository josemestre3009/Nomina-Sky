# Usar una imagen ligera de Python 3.11
FROM python:3.11-slim

# Evitar que Python genere archivos .pyc y permitir logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Configurar Zona Horaria
ENV TZ=America/Bogota

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Persistir la base SQLite cuando DATABASE_URL apunta a /app/instance
RUN mkdir -p /app/instance
VOLUME ["/app/instance"]

# Exponer el puerto de Flask
EXPOSE 8000

# Inicializar el esquema y el admin antes de servir la aplicación
CMD ["sh", "-c", "flask --app run:app init-db && exec gunicorn --bind 0.0.0.0:8000 run:app"]
