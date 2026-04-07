"""
Filtros Jinja2 personalizados para la aplicación Actividades Sky.
Formato de moneda COP, fechas en español, estados de pago.
"""
from markupsafe import Markup


def formato_moneda(valor):
    """
    Formatea un valor numérico como moneda colombiana (COP).
    Ejemplo: 150000 → $150.000 COP
    """
    if valor is None:
        return '$0 COP'
    try:
        valor = float(valor)
        formateado = f'{valor:,.0f}'.replace(',', '.')
        return f'${formateado} COP'
    except (ValueError, TypeError):
        return '$0 COP'


def formato_fecha(fecha):
    """Formatea una fecha al formato dd/mm/yyyy."""
    if fecha is None:
        return ''
    try:
        return fecha.strftime('%d/%m/%Y')
    except AttributeError:
        return str(fecha)


def formato_fecha_hora(fecha):
    """Formatea fecha y hora al formato dd/mm/yyyy HH:MM."""
    if fecha is None:
        return ''
    try:
        return fecha.strftime('%d/%m/%Y %H:%M')
    except AttributeError:
        return str(fecha)


def formato_estado(estado):
    """Retorna HTML con badge para el estado de pago."""
    estados = {
        'pendiente': '<span class="badge bg-warning text-dark">Pendiente</span>',
        'revisado': '<span class="badge bg-success">Revisado</span>',
        'ausente': '<span class="badge" style="background-color: var(--text-muted); color: white;">Ausente</span>',
        'activo': '<span class="badge bg-success">Activo</span>',
        'inactivo': '<span class="badge bg-secondary">Inactivo</span>'
    }
    return Markup(estados.get(estado, f'<span class="badge bg-secondary">{estado}</span>'))
