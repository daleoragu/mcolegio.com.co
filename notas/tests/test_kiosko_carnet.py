"""Carné con QR al azar y kiosko de asistencia (cámara, lector USB y ausentes)."""
from django.contrib.auth.models import User
from django.utils import timezone

from notas.models import Asistencia, Curso, Docente
from notas.views.carnet_views import codigo_leido

from .base import CLAVE, ColegioDePrueba


class CarnetYKiosko(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ana, cls.beto, cls.caro = cls.estudiantes
        otro = Curso.objects.create(colegio=cls.a, nombre='701', grado=7, subgrupo='1')
        cls.de_otro_curso = cls.crear_estudiante('dani', curso=otro)

    def kiosko(self, usuario=None):
        c = self.cliente(usuario or self.u_docente)
        c.post('/asistencia/kiosko/', {'asignacion_id': self.asig.id})
        return c

    def pasar(self, c, estudiante, como_url=True):
        codigo = estudiante.asegurar_codigo_carnet()
        texto = f'https://a.mcolegio.com.co/c/{codigo}/' if como_url else codigo
        return c.post('/asistencia/kiosko/registrar/', {'codigo': texto}).json()

    def estado(self, estudiante):
        a = Asistencia.objects.filter(estudiante=estudiante, asignacion=self.asig, fecha=timezone.localdate()).first()
        return a.estado if a else None

    # --- Carné ---------------------------------------------------------------
    def test_carne_individual_ya_no_da_error(self):
        r = self.cliente(self.rectora).get(f'/carnet/generar/{self.ana.id}/')
        self.assertEqual(r.status_code, 200)
        self.ana.refresh_from_db()
        self.assertTrue(self.ana.codigo_carnet)
        self.assertContains(r, 'data:image/png;base64,')

    def test_el_codigo_no_es_el_numero_del_estudiante(self):
        codigos = {e.asegurar_codigo_carnet() for e in self.estudiantes}
        self.assertEqual(len(codigos), 3)
        for e in self.estudiantes:
            self.assertGreaterEqual(len(e.codigo_carnet), 12)
            self.assertNotIn(str(e.id), [e.codigo_carnet])

    def test_cambiar_el_codigo_invalida_el_carne_viejo(self):
        viejo = self.ana.asegurar_codigo_carnet()
        self.cliente(self.rectora).post(f'/carnet/generar/{self.ana.id}/', {'accion': 'nuevo_codigo'})
        self.ana.refresh_from_db()
        self.assertNotEqual(self.ana.codigo_carnet, viejo)
        self.assertEqual(self.cliente().get(f'/c/{viejo}/').status_code, 404)
        self.assertContains(self.cliente().get(f'/c/{self.ana.codigo_carnet}/'), 'Carné estudiantil válido')

    def test_un_estudiante_no_ve_el_carne_de_otro(self):
        r = self.cliente(self.beto.user).get(f'/carnet/generar/{self.ana.id}/')
        self.assertEqual(r.status_code, 404)

    def test_impresion_masiva(self):
        r = self.cliente(self.rectora).get('/herramientas/imprimir-carnets/')
        self.assertEqual(r.status_code, 200)
        self.ana.refresh_from_db()
        self.assertTrue(self.ana.codigo_carnet)

    def test_leer_el_codigo(self):
        self.assertEqual(codigo_leido('https://x.co/c/AbC_12-xyZ90/'), 'AbC_12-xyZ90')
        self.assertEqual(codigo_leido('  AbC_12-xyZ90 '), 'AbC_12-xyZ90')
        self.assertIsNone(codigo_leido('https://x.co/asistencia/registrar-qr/5/'))
        self.assertIsNone(codigo_leido('hola mundo'))

    # --- Kiosko ----------------------------------------------------------------
    def test_pasar_el_carne_marca_presente(self):
        c = self.kiosko()
        j = self.pasar(c, self.ana)
        self.assertTrue(j['ok'])
        self.assertEqual(self.estado(self.ana), 'P')
        self.assertEqual(j['dia']['presentes'], 1)
        self.assertEqual(j['dia']['pendientes'], 2)
        # Con el lector USB que entrega solo el código, también sirve
        self.assertTrue(self.pasar(c, self.beto, como_url=False)['ok'])
        # Dos veces no duplica
        self.assertTrue(self.pasar(c, self.ana).get('repetido'))
        self.assertEqual(Asistencia.objects.filter(estudiante=self.ana).count(), 1)

    def test_estudiante_de_otro_curso_no_se_marca(self):
        j = self.pasar(self.kiosko(), self.de_otro_curso)
        self.assertFalse(j['ok'])
        self.assertIsNone(Asistencia.objects.filter(estudiante=self.de_otro_curso).first())

    def test_carne_viejo_no_marca(self):
        c = self.kiosko()
        j = c.post('/asistencia/kiosko/registrar/',
                   {'codigo': f'https://a.mcolegio.com.co/asistencia/registrar-qr/{self.ana.id}/'}).json()
        self.assertFalse(j['ok'])
        self.assertIn('antiguo', j['mensaje'])
        c.get(f'/asistencia/registrar-qr/{self.ana.id}/')
        self.assertIsNone(self.estado(self.ana))

    def test_abrir_el_qr_con_el_kiosko_activo_marca(self):
        c = self.kiosko()
        r = c.get(f'/c/{self.caro.asegurar_codigo_carnet()}/')
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.estado(self.caro), 'P')

    def test_marcar_ausentes_y_luego_llega_tarde(self):
        c = self.kiosko()
        self.pasar(c, self.ana)
        c.post('/asistencia/kiosko/ausentes/')
        self.assertEqual(self.estado(self.ana), 'P')
        self.assertEqual(self.estado(self.beto), 'A')
        self.assertEqual(self.estado(self.caro), 'A')
        j = self.pasar(c, self.beto)
        self.assertTrue(j['ok'])
        self.assertEqual(self.estado(self.beto), 'T')

    def test_sin_clase_activa_no_marca(self):
        c = self.cliente(self.u_docente)
        j = self.pasar(c, self.ana)
        self.assertFalse(j['ok'])

    def test_docente_no_activa_clase_ajena(self):
        u = User.objects.create_user('otro_profe', password=CLAVE)
        Docente.objects.create(colegio=self.a, user=u)
        c = self.kiosko(u)
        self.assertFalse(self.pasar(c, self.ana)['ok'])
        self.assertIsNone(self.estado(self.ana))

    def test_pagina_del_kiosko(self):
        r = self.kiosko().get('/asistencia/kiosko/')
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Leer con la cámara')
        self.assertContains(r, 'Marcar ausentes')
        self.assertContains(r, 'jsQR.js')
