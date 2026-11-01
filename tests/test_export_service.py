import re
import unittest
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from app.services import export_service


class GenerarPdfTest(unittest.TestCase):
    def test_conserva_actividad_larga_y_genera_varias_paginas(self):
        actividad = ('Instalación <principal> & revisión completa. ' * 60)[:1990] + '\nFIN-REPORTE'
        empleado = SimpleNamespace(nombre='Ana & José', cedula='123', cargo='Técnico <Líder>')
        reportes = [
            SimpleNamespace(
                fecha=date(2026, 1, 1) + timedelta(days=i),
                actividad=actividad if i == 0 else f'Actividad normal número {i}',
                estado_pago='revisado',
                valor_dia_aplicado=100000,
            )
            for i in range(100)
        ]
        resumen = {
            'empleado': empleado,
            'dias_registrados': len(reportes),
            'dias_trabajados': len(reportes),
            'reportes': reportes,
            'bonos': [SimpleNamespace(descripcion='Extra <urgente> & nocturno', valor=50000)],
            'total_final': 10050000,
        }
        textos = []
        paragraph_original = export_service.Paragraph

        def registrar_paragraph(texto, estilo):
            textos.append(texto)
            return paragraph_original(texto, estilo)

        with patch.object(export_service, 'Paragraph', side_effect=registrar_paragraph):
            contenido = export_service.generar_pdf(
                [resumen], date(2026, 1, 1), date(2026, 4, 10)
            ).getvalue()

        actividad_escapada = export_service._texto_pdf(actividad)
        self.assertIn(actividad_escapada, textos)
        self.assertIn('FIN-REPORTE', actividad_escapada)
        self.assertIn('&lt;principal&gt; &amp; revisión', actividad_escapada)
        self.assertGreater(len(re.findall(rb'/Type\s*/Page\b', contenido)), 1)

    def test_divide_una_actividad_mayor_que_una_pagina(self):
        actividad = ('Línea detallada\n' * 125)[:2000]
        resumen = {
            'empleado': SimpleNamespace(nombre='Ana', cedula='123', cargo='Técnica'),
            'dias_registrados': 1,
            'dias_trabajados': 1,
            'reportes': [SimpleNamespace(
                fecha=date(2026, 1, 1),
                actividad=actividad,
                estado_pago='revisado',
                valor_dia_aplicado=100000,
            )],
            'bonos': [],
            'total_final': 100000,
        }

        contenido = export_service.generar_pdf(
            [resumen], date(2026, 1, 1), date(2026, 1, 1)
        ).getvalue()

        self.assertGreater(len(re.findall(rb'/Type\s*/Page\b', contenido)), 1)


if __name__ == '__main__':
    unittest.main()
