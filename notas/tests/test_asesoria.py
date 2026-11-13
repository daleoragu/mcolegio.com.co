"""Asesoría docente: el botón que explica cada página (solo docentes y administradores)."""
import json
import re

from django.urls import resolve, reverse

from notas import asesoria
from notas.tests.base import ColegioDePrueba


class Asesoria(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def datos(self, r):
        m = re.search(r'<script id="asesoria-datos" type="application/json">(.*?)</script>', r.content.decode(), re.S)
        return json.loads(m.group(1)) if m else None

    def test_el_docente_tiene_el_boton_con_la_guia_de_planeacion(self):
        r = self.cliente(self.u_docente).get(reverse('materiales:lista'))
        self.assertContains(r, 'Asesoría docente')
        d = self.datos(r)
        self.assertEqual(d['vista'], 'materiales:lista')
        self.assertIn('Planeación', d['guia']['titulo'])
        self.assertTrue(any('Enviar' in p['t'] for p in d['guia']['pasos']))
        self.assertEqual(len(d['mapa']), 5)

    def test_el_estudiante_no_lo_ve(self):
        ana = self.estudiantes[0]
        r = self.cliente(ana.user).get('/')
        self.assertNotContains(r, 'as-boton', status_code=r.status_code)

    def test_paginas_sin_guia_ofrecen_mapa_y_glosario(self):
        d = asesoria.datos(type('R', (), {'resolver_match': resolve(reverse('materiales:ayuda'))})())
        self.assertIsNone(d['guia'])
        self.assertIn('enviar a mis grupos', d['glosario'])

    def test_las_paginas_del_aula_explican_las_pestanas(self):
        g = asesoria.guia('aula:tareas')
        self.assertEqual(g['pasos'][0]['s'], '.au-pestanas')
        self.assertEqual(asesoria.guia('aula:mascota')['titulo'], 'Mascota académica')

    def test_todas_las_guias_estan_bien_formadas(self):
        for vista, g in asesoria.GUIAS.items():
            reverse(vista, args=[1]) if vista in ('materiales:editor', 'aula:mascota') else reverse(vista)
            self.assertTrue(g['titulo'] and g['resumen'] and g['pasos'], vista)
            for p in g['pasos']:
                self.assertTrue(p['t'] and p['x'] and (p.get('c') or p.get('s')), (vista, p))
