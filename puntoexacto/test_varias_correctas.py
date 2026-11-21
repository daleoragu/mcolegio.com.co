# -*- coding: utf-8 -*-
"""Preguntas con dos respuestas correctas y hojas donde el estudiante marcó dos."""
from notas.tests.base import ColegioDePrueba

from . import formas as formas_mod
from .calificacion import calificar_hoja
from .models import Examen, Hoja


class VariasCorrectas(ColegioDePrueba):

    def setUp(self):
        self.c = self.cliente(self.rectora)
        self.c.post('/puntoexacto/nuevo/', {
            'titulo': 'Parcial', 'fecha': '2026-10-06', 'componente': 'SABER',
            'numero_preguntas': '4', 'numero_opciones': '4', 'hojas_por_pagina': '1',
            'metodo': 'con_piso', 'nota_todo_mal': '1', 'nota_nada_marcado': '1',
            'opciones_por_pregunta': '{}'})
        self.ex = Examen.objects.get()
        datos = {'metodo': 'con_piso'}
        for n, letra in zip(range(1, 5), 'ABCD'):
            datos.update({f'correcta_{n}': letra, f'opciones_{n}': '4', f'puntos_{n}': '1'})
        datos['tambien_1'] = ['C']                  # en la 1 también vale la C
        r = self.c.post(f'/puntoexacto/{self.ex.id}/clave/', datos)
        self.assertNotEqual(r.status_code, 400)

    def nota(self, lectura):
        hoja = Hoja.objects.create(examen=self.ex, identificador=f'PE-{Hoja.objects.count() + 1}', nombre_libre='Ana')
        formas_mod.guardar_lectura(hoja, lectura)
        calificar_hoja(hoja)
        hoja.refresh_from_db()
        return hoja

    def test_la_clave_guarda_la_otra_correcta(self):
        p = self.ex.preguntas.get(numero=1)
        self.assertEqual(p.correcta, 'A')
        self.assertEqual(sorted(p.letras_correctas()), ['A', 'C'])
        self.assertTrue(p.tiene_otra_correcta)
        self.assertEqual(p.rotulo_correctas(), 'A o C')
        self.assertFalse(self.ex.preguntas.get(numero=2).tiene_otra_correcta)
        h = self.c.get(f'/puntoexacto/{self.ex.id}/clave/').content.decode()
        self.assertIn('name="tambien_1"', h)
        self.assertIn('+ Otra correcta', h)

    def test_cualquiera_de_las_dos_vale(self):
        con_a = self.nota({'1': 'A', '2': 'B', '3': 'C', '4': 'D'})
        con_c = self.nota({'1': 'C', '2': 'B', '3': 'C', '4': 'D'})
        self.assertEqual(con_a.nota, self.ex.nota_maxima)
        self.assertEqual(con_c.nota, self.ex.nota_maxima)

    def test_marcar_las_dos_correctas_vale_y_una_mala_no(self):
        dos_buenas = self.nota({'1': 'CA', '2': 'B', '3': 'C', '4': 'D'})
        self.assertEqual(dos_buenas.respuestas.get(pregunta__numero=1).marcada, 'AC')
        self.assertEqual(dos_buenas.nota, self.ex.nota_maxima)
        una_mala = self.nota({'1': 'AB', '2': 'B', '3': 'C', '4': 'D'})
        self.assertLess(una_mala.nota, self.ex.nota_maxima)
        # En una pregunta con una sola correcta, dos marcadas no valen.
        doble = self.nota({'1': 'A', '2': 'BC', '3': 'C', '4': 'D'})
        self.assertLess(doble.nota, self.ex.nota_maxima)

    def test_letra_que_no_existe_se_descarta(self):
        h = self.nota({'1': 'AZ', '2': 'B', '3': 'C', '4': 'D'})
        self.assertFalse(h.respuestas.filter(pregunta__numero=1).exclude(marcada='').exists())

    def test_quitar_la_otra_correcta(self):
        datos = {'metodo': 'con_piso'}
        for n, letra in zip(range(1, 5), 'ABCD'):
            datos.update({f'correcta_{n}': letra, f'opciones_{n}': '4', f'puntos_{n}': '1'})
        self.c.post(f'/puntoexacto/{self.ex.id}/clave/', datos)
        self.assertEqual(self.ex.preguntas.get(numero=1).letras_correctas(), ['A'])
