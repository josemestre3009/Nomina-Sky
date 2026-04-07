"""
Funciones auxiliares.
"""
from datetime import datetime


def parse_fecha(fecha_str):
    """Parsea una fecha de formato dd/mm/yyyy a objeto date."""
    if not fecha_str:
        return None
    try:
        return datetime.strptime(fecha_str, '%d/%m/%Y').date()
    except ValueError:
        try:
            return datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return None


def formato_numero(valor):
    """Formatea un número con separador de miles."""
    if valor is None:
        return '0'
    return f'{valor:,.0f}'.replace(',', '.')
