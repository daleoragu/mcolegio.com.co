"""Ficha del estudiante: el estudiante pide, la administración o el director autoriza, y todo queda registrado."""
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from notas.models import (CambioFicha, Curso, Docente, FichaEstudiante, Notificacion, SolicitudFicha)

from .base import CLAVE, ColegioDePrueba

MEDIA = tempfile.mkdtemp(prefix='fichas-')
GIF = (b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,'
       b'\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')


@override_settings(MEDIA_ROOT=MEDIA)
class SolicitudesFicha(ColegioDePrueba):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.ana = self.estudiantes[0]
        self.ficha = FichaEstudiante.objects.create(estudiante=self.ana, eps='Sura', celular_madre='3001111111')
        self.yo = self.cliente(self.ana.user)

    def pedir(self, **datos):
        base = {'tipo_documento': 'TI', 'numero_documento': '', 'eps': 'Sura', 'celular_madre': '3001111111'}
        base.update(datos)
        return self.yo.post('/estudiante/mi-ficha/', base)

    def test_el_estudiante_no_edita_directo(self):
        r = self.yo.get(f'/admin/gestion-estudiantes/editar/{self.ana.id}/')
        self.assertRedirects(r, '/estudiante/mi-ficha/', fetch_redirect_response=False)
        # Ni con un POST armado a mano al formulario de la administración
        otro = Curso.objects.create(colegio=self.a, nombre='701', grado=7, subgrupo='1')
        self.yo.post(f'/admin/gestion-estudiantes/editar/{self.ana.id}/', {
            'first_name': 'HACKER', 'last_name': 'X', 'curso': otro.id, 'is_active': 'on', 'es_inclusion': 'on',
            'tipo_documento': 'TI'})
        self.ana.refresh_from_db()
        self.assertEqual((self.ana.curso, self.ana.es_inclusion, self.ana.user.first_name), (self.curso, False, 'Ana'))

    def test_la_pagina_no_trae_inclusion_ni_curso_ni_nombres(self):
        r = self.yo.get('/estudiante/mi-ficha/')
        self.assertContains(r, 'Enviar los cambios para autorizar')
        for campo in ('es_inclusion', 'name="curso"', 'name="first_name"', 'is_active', 'compromiso'):
            self.assertNotContains(r, campo)

    def test_pedir_no_cambia_la_ficha_y_avisa(self):
        self.pedir(eps='Nueva EPS', celular_madre='3209999999', es_inclusion='on')
        self.ficha.refresh_from_db()
        self.assertEqual(self.ficha.eps, 'Sura')                     # aún no cambia
        self.ana.refresh_from_db()
        self.assertFalse(self.ana.es_inclusion)                      # nunca
        s = SolicitudFicha.objects.get()
        self.assertEqual(set(s.cambios), {'eps', 'celular_madre'})
        avisados = set(Notificacion.objects.filter(mensaje__contains='pide cambiar').values_list('destinatario', flat=True))
        self.assertEqual(avisados, {self.rectora.id, self.u_docente.id})     # administración y director de grupo

    def test_sin_cambios_no_crea_solicitud(self):
        self.pedir()
        self.assertFalse(SolicitudFicha.objects.exists())

    def test_otra_solicitud_reemplaza_la_pendiente(self):
        self.pedir(eps='A')
        self.pedir(eps='B')
        self.assertEqual(SolicitudFicha.objects.get().cambios['eps']['despues'], 'B')

    def test_autorizar_en_parte_y_registro(self):
        self.pedir(eps='Nueva EPS', celular_madre='3209999999', fecha_nacimiento='2012-05-03')
        s = SolicitudFicha.objects.get()
        r = self.cliente(self.u_docente).post(f'/fichas/solicitudes/{s.pk}/', {
            'accion': 'aprobar', 'campos': ['eps', 'fecha_nacimiento']})
        self.ficha.refresh_from_db()
        self.assertEqual((self.ficha.eps, self.ficha.celular_madre, str(self.ficha.fecha_nacimiento)),
                         ('Nueva EPS', '3001111111', '2012-05-03'))
        s.refresh_from_db()
        self.assertEqual((s.estado, s.revisada_por), ('PARCIAL', self.u_docente))
        log = {c.campo: c for c in CambioFicha.objects.filter(estudiante=self.ana)}
        self.assertEqual(set(log), {'eps', 'fecha_nacimiento'})
        self.assertEqual((log['eps'].antes, log['eps'].despues, log['eps'].hecho_por, log['eps'].autorizado_por,
                          log['eps'].origen), ('Sura', 'Nueva EPS', self.ana.user, self.u_docente, 'SOLICITUD'))
        self.assertTrue(Notificacion.objects.filter(destinatario=self.ana.user, mensaje__contains='2 dato').exists())
        r = self.cliente(self.rectora).get(f'/fichas/{self.ana.id}/historial/')
        self.assertContains(r, 'Nueva EPS')

    def test_foto_nueva(self):
        foto = SimpleUploadedFile('yo.gif', GIF, content_type='image/gif')
        self.pedir(foto=foto)
        s = SolicitudFicha.objects.get()
        self.assertIn('foto', s.cambios)
        self.ficha.refresh_from_db()
        self.assertFalse(self.ficha.foto)
        self.cliente(self.rectora).post(f'/fichas/solicitudes/{s.pk}/', {'accion': 'aprobar', 'campos': ['foto']})
        self.ficha.refresh_from_db()
        self.assertTrue(self.ficha.foto)

    def test_rechazar_pide_motivo(self):
        self.pedir(eps='X')
        s = SolicitudFicha.objects.get()
        c = self.cliente(self.rectora)
        c.post(f'/fichas/solicitudes/{s.pk}/', {'accion': 'rechazar'})
        s.refresh_from_db()
        self.assertEqual(s.estado, 'PENDIENTE')
        c.post(f'/fichas/solicitudes/{s.pk}/', {'accion': 'rechazar', 'respuesta': 'Traiga el carné de la EPS'})
        s.refresh_from_db()
        self.assertEqual(s.estado, 'RECHAZADA')
        self.ficha.refresh_from_db()
        self.assertEqual(self.ficha.eps, 'Sura')

    def test_quien_autoriza(self):
        self.pedir(eps='X')
        s = SolicitudFicha.objects.get()
        otro = User.objects.create_user('otro', password=CLAVE)
        Docente.objects.create(colegio=self.a, user=otro)
        self.assertEqual(self.cliente(otro).get(f'/fichas/solicitudes/{s.pk}/').status_code, 404)
        self.assertEqual(self.cliente(otro).get('/fichas/solicitudes/').status_code, 403)
        self.assertEqual(self.yo.get(f'/fichas/solicitudes/{s.pk}/').status_code, 404)
        self.yo.post(f'/fichas/solicitudes/{s.pk}/', {'accion': 'aprobar', 'campos': ['eps']})
        self.ficha.refresh_from_db()
        self.assertEqual(self.ficha.eps, 'Sura')

    def test_la_administracion_deja_registro(self):
        self.cliente(self.rectora).post(f'/admin/gestion-estudiantes/editar/{self.ana.id}/', {
            'first_name': 'Ana', 'last_name': 'Prueba', 'curso': self.curso.id, 'is_active': 'on', 'es_inclusion': 'on',
            'tipo_documento': 'TI', 'eps': 'Sura', 'celular_madre': '3001111111'})
        self.ana.refresh_from_db()
        self.assertTrue(self.ana.es_inclusion)
        c = CambioFicha.objects.get(estudiante=self.ana, campo='es_inclusion')
        self.assertEqual((c.antes, c.despues, c.hecho_por, c.origen), ('No', 'Sí', self.rectora, 'ADMIN'))

    def test_el_docente_deja_registro(self):
        self.cliente(self.u_docente).post(f'/observador/ficha/{self.ana.id}/editar/', {
            'tipo_documento': 'TI', 'eps': 'Coomeva', 'celular_madre': '3001111111'})
        c = CambioFicha.objects.get(estudiante=self.ana, campo='eps')
        self.assertEqual((c.despues, c.hecho_por, c.origen), ('Coomeva', self.u_docente, 'DOCENTE'))
