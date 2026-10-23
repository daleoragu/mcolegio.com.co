"""El colegio escoge en qué documentos firma el director(a) de grado."""
from notas.models import Colegio

from .base import ColegioDePrueba


class FirmaDelDirector(ColegioDePrueba):

    def test_valores_de_fabrica(self):
        f = self.a.firma_director
        self.assertTrue(f['boletin'])
        self.assertTrue(f['boletin_final'])
        self.assertFalse(f['libro'])          # el libro lo firman rectoría y secretaría

    def test_lo_guardado_manda_y_lo_que_falta_usa_el_de_fabrica(self):
        self.a.firmas_director = {'boletin': False, 'libro': True}
        self.a.save()
        f = Colegio.objects.get(pk=self.a.pk).firma_director
        self.assertEqual((f['boletin'], f['libro'], f['boletin_final']), (False, True, True))
        self.a.firmas_director = 'basura'
        self.assertTrue(self.a.firma_director['boletin'])

    def test_aparece_en_la_configuracion(self):
        r = self.cliente(self.rectora).get('/admin/configuracion-calificaciones/')
        self.assertContains(r, 'Firmas en los documentos')
        self.assertContains(r, 'name="firma_director_libro"')
