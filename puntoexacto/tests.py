# puntoexacto/tests.py
"""Cuentas de PuntoExacto que no necesitan base de datos.

    python manage.py test puntoexacto
"""
from decimal import Decimal as D

from django.test import SimpleTestCase

from .calificacion import nota_desde_puntaje, repartir_pesos
from .models import limpiar_rotulos


class Pesos(SimpleTestCase):

    def test_sin_pesos_se_reparte_por_puntos(self):
        pesos, avisos = repartir_pesos([(1, D(15), None), (2, D(20), None)])
        self.assertAlmostEqual(float(pesos[1]), 15 / 35)
        self.assertEqual(avisos, [])

    def test_peso_fijo_y_el_resto_por_puntos(self):
        pesos, _ = repartir_pesos([(1, D(15), D(40)), (2, D(20), None), (None, D(5), None)])
        self.assertEqual(pesos[1], D('0.4'))
        self.assertEqual(pesos[2], D('0.48'))

    def test_pesos_que_no_suman_100_se_ajustan_y_avisan(self):
        pesos, avisos = repartir_pesos([(1, D(15), D(30)), (2, D(20), D(30))])
        self.assertEqual(pesos[1], D('0.5'))
        self.assertTrue(avisos)


class Notas(SimpleTestCase):

    def test_metodos(self):
        self.assertEqual(nota_desde_puntaje(D(3.5), D(5), D(5), D(1), 'manual'), D('3.5'))
        self.assertEqual(nota_desde_puntaje(D(2), D(4), D(5), D(1), 'con_piso'), D(3))
        self.assertEqual(nota_desde_puntaje(D(2), D(4), D(5), D(1), 'proporcional'), D('2.5'))

    def test_etiquetas_de_opciones(self):
        self.assertEqual(limpiar_rotulos('v, f'), ['v', 'f'])
        self.assertEqual(limpiar_rotulos('Verdadero,Falso'), ['Ve', 'Fa'])
