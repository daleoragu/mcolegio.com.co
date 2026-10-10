# -*- coding: utf-8 -*-
"""Cada hoja lleva el curso y la sede de SU estudiante, también en pruebas censales."""
from notas.models import Curso, Sede
from notas.tests.base import ColegioDePrueba

from . import hojas as H
from .models import Examen, Hoja
from .test_formas import texto_del_pdf


class HojaConCursoYSede(ColegioDePrueba):

    def setUp(self):
        self.sede = Sede.objects.create(colegio=self.a, nombre='La Esperanza')
        self.curso.sede = self.sede
        self.curso.save()
        self.otro = Curso.objects.create(colegio=self.a, nombre='702', grado=7, subgrupo='2')
        e = self.estudiantes[2]
        e.curso = self.otro
        e.save()
        # Prueba censal: sin asignatura, aplicada a dos cursos.
        self.ex = Examen.objects.create(colegio=self.a, titulo='Simulacro', fecha='2026-10-20',
                                        numero_preguntas=5)
        for i, est in enumerate(self.estudiantes):
            Hoja.objects.create(examen=self.ex, estudiante=est, identificador=f'PE-C-{i}')

    def test_el_pdf_dice_curso_y_sede_de_cada_uno(self):
        hojas = list(self.ex.hojas.all())
        texto = texto_del_pdf(H.generar_pdf(self.ex, hojas)).decode('latin-1')
        self.assertIn('Curso 601', texto)
        self.assertIn('Sede La Esperanza', texto)
        self.assertIn('Curso 702', texto)
        self.assertNotIn('Sede Sede', texto)

    def test_al_imprimir_salen_agrupadas_por_curso(self):
        r = self.cliente(self.rectora).get(f'/puntoexacto/{self.ex.id}/hojas/imprimir/')
        self.assertEqual(r['Content-Type'], 'application/pdf')
        texto = texto_del_pdf(r.content).decode('latin-1')
        self.assertLess(texto.index('Curso 601'), texto.index('Curso 702'))

    def test_la_camara_muestra_el_curso(self):
        r = self.cliente(self.rectora).get(f'/puntoexacto/{self.ex.id}/escanear/')
        self.assertContains(r, '601 · Sede La Esperanza')
