# -*- coding: utf-8 -*-
"""Que cada función salga en el menú y el panel que le corresponden."""
import re

from django.contrib.auth.models import Group

from actas.models import RedactorActas
from notas.permisos import es_docente_usuario

from .base import ColegioDePrueba


class Menus(ColegioDePrueba):

    def test_administrador_tiene_las_tres_pestanas_y_ver_como(self):
        r = self.cliente(self.rectora).get('/panel-administrador/')
        html = r.content.decode()
        for texto in ('Panel de Administración', 'Panel Docente', 'Panel Estudiante',
                      'Ver como este docente', 'Ver como este estudiante'):
            self.assertIn(texto, html)
        self.assertIn('Prueba Ana', html)              # estudiantes para «Ver como»
        self.assertIn('/actas/', html)
        self.assertIn('/admin/gestion-academica/areas/', html)

    def test_superusuario_tambien(self):
        r = self.cliente(self.super).get('/panel-administrador/')
        self.assertContains(r, 'Panel Estudiante')

    def test_menu_del_administrador_tiene_todo(self):
        html = self.cliente(self.rectora).get('/panel-administrador/').content.decode()
        for ruta in ('/admin/gestion-academica/areas/', '/panel-administrador/#docente',
                     '/panel-administrador/#estudiante'):
            self.assertIn(ruta, html)

    def test_docente_sin_grupo_igual_ve_su_menu(self):
        self.u_docente.groups.clear()
        self.assertTrue(es_docente_usuario(self.u_docente))
        html = self.cliente(self.u_docente).get('/panel-docente/').content.decode()
        self.assertIn('Ingresar Notas', html)
        self.assertIn('Mis planillas', html)
        self.assertIn('Consultar Asistencia', html)
        self.assertNotIn('/actas/', html)              # sin el rol no le sale Actas

    def test_docente_con_rol_ve_actas_en_menu_y_panel(self):
        RedactorActas.objects.create(colegio=self.a, docente=self.docente)
        html = self.cliente(self.u_docente).get('/panel-docente/').content.decode()
        self.assertEqual(html.count('href="/actas/"'), 2)   # menú y panel

    def test_estudiante_no_es_docente(self):
        u = self.estudiantes[0].user
        self.assertFalse(es_docente_usuario(u))
        Group.objects.get_or_create(name='Docentes')
        self.assertNotIn('Ingresar Notas', self.cliente(u).get('/panel-estudiante/').content.decode())


class MenusDeLoNuevo(ColegioDePrueba):
    """Lo de certificados, circulares, libro final y Salón Digital, y que todos los enlaces abran."""

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
