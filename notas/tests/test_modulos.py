# -*- coding: utf-8 -*-
"""Módulos por colegio: lo apagado no sale en menús ni abre, y los datos se conservan."""
from notas.modulos import PLANES, TODOS, activos, modulo_de_ruta
from notas.models import Colegio
from notas.tests.base import ColegioDePrueba


class Modulos(ColegioDePrueba):

    def _apagar(self, *codigos):
        self.a.modulos_activos = [m for m in TODOS if m not in codigos]
        self.a.save(update_fields=['modulos_activos'])

    def test_un_colegio_nuevo_tiene_todo(self):
        self.assertEqual(activos(Colegio.objects.create(nombre='Nuevo', slug='nuevo')), set(TODOS))

    def test_rutas(self):
        self.assertEqual(modulo_de_ruta('/circulares/gestion/'), 'circulares')
        self.assertEqual(modulo_de_ruta('/certificados/verificar/ABC/'), None)   # la verificación pública sigue
        self.assertEqual(modulo_de_ruta('/docente/planillas/'), None)            # núcleo

    def test_apagado_no_sale_en_menu_ni_abre(self):
        self._apagar('circulares', 'correo', 'puntoexacto')
        c = self.cliente(self.u_docente)
        r = c.get('/panel-docente/')
        self.assertNotContains(r, '/circulares/')
        self.assertNotContains(r, '/puntoexacto/')
        self.assertNotContains(r, '/mensajeria/')
        self.assertContains(r, 'Ingresar Notas')                                 # el núcleo sigue
        r = c.get('/circulares/')
        self.assertEqual(r.status_code, 403)
        self.assertContains(r, 'no está activo', status_code=403)
        # El otro colegio no se ve afectado.
        self.assertIn('circulares', activos(self.b))

    def test_estudiante_y_admin(self):
        self._apagar('certificados', 'reporte_parcial')
        r = self.cliente(self.estudiantes[0].user).get('/panel-estudiante/')
        self.assertNotContains(r, 'Mis certificados')
        self.assertNotContains(r, 'Mi informe parcial')
        r = self.cliente(self.rectora).get('/panel-administrador/')
        self.assertNotContains(r, 'Libro final')
        self.assertContains(r, 'Circulares')

    def test_portal_apagado_deja_solo_el_ingreso(self):
        self._apagar('portal')
        r = self.cliente().get('/')
        self.assertContains(r, 'Ingreso a la plataforma')
        self.assertEqual(self.cliente(self.rectora).get('/admin/portal/noticias/').status_code, 403)
        self.assertEqual(self.cliente(self.rectora).get('/admin/portal/personalizacion/').status_code, 200)

    def test_pantalla_del_dueno_y_planes(self):
        c = self.cliente(self.super)
        self.assertContains(c.get('/plataforma/modulos/'), 'Colegio A')
        c.post('/plataforma/modulos/', {'colegio': self.a.pk, 'plan': 'basico'})
        self.a.refresh_from_db()
        self.assertEqual(set(self.a.modulos_activos), set(PLANES['basico'][1]))
        c.post('/plataforma/modulos/', {'colegio': self.a.pk, 'plan': 'publico'})
        self.a.refresh_from_db()
        self.assertEqual(set(self.a.modulos_activos), set(TODOS) - {'cartera'})
        c.post('/plataforma/modulos/', {'colegio': self.a.pk, 'mod_actas': 'on'})
        self.a.refresh_from_db()
        self.assertEqual(self.a.modulos_activos, ['actas'])
        self.assertNotEqual(self.cliente(self.rectora).get('/plataforma/modulos/').status_code, 200)
