"""Meses del periodo en Consultar Asistencia."""
from .base import ColegioDePrueba


class MesesDelPeriodo(ColegioDePrueba):
    """La lista de meses de Consultar Asistencia no depende del idioma del servidor."""

    def test_meses_en_espanol(self):
        r = self.cliente(self.u_docente).get(f'/ajax/obtener-meses/?periodo_id={self.p1.id}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['meses'], [[2, 'Febrero'], [3, 'Marzo'], [4, 'Abril']])

    def test_pide_iniciar_sesion(self):
        self.assertEqual(self.cliente().get(f'/ajax/obtener-meses/?periodo_id={self.p1.id}').status_code, 302)
