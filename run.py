"""
Punto de entrada principal de la aplicación Nomina-Sky.
Ejecutar con: flask run o python run.py
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug, port=5000)
