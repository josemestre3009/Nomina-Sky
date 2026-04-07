"""
Punto de entrada principal de la aplicación Nomina-Sky.
Ejecutar con: flask run o python run.py
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
