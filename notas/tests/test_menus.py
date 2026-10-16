# -*- coding: utf-8 -*-
"""Cada rol ve en su menú y en su panel lo que le corresponde, y los enlaces abren."""
import re

from notas.tests.base import ColegioDePrueba


class Menus(ColegioDePrueba):

    def _enlaces(self, r):
        html = r.content.decode()
        return set(re.findall(r'href="(/[^"#?]*)', html))

    def _abren(self, cliente, enlaces):
        for e in enlaces:
            if e.startswith(('/static', '/media', '/logout', '/salir')):
                continue
            codigo = cliente.get(e).status_code
            self.assertLess(codigo, 500, f'{e} -> {codigo}')

    def test_estudiante_sin_grupo_ve_su_seccion(self):
        ana = self.estudiantes[0]
        c = self.cliente(ana.user)
        r = c.get('/panel-estudiante/', follow=True)
        for texto in ('Mis certificados', 'Circulares', 'Mi informe parcial', 'Mi Observador'):
            self.assertContains(r, texto)
        self.assertEqual(c.get('/estudiante/mi-observador/').status_code, 200)
        self._abren(c, self._enlaces(r))

    def test_docente(self):
        c = self.cliente(self.u_docente)
        r = c.get('/panel-docente/')
        for texto in ('Subir planilla', 'Circulares', 'Salón Digital'):
            self.assertContains(r, texto)
        self._abren(c, self._enlaces(r))

    def test_administrador(self):
        c = self.cliente(self.rectora)
        r = c.get('/panel-administrador/')
        for texto in ('Libro final', 'Circulares (enviar)', 'Certificados'):
            self.assertContains(r, texto)
        self._abren(c, self._enlaces(r))
