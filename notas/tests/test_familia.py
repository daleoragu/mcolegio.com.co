"""Hermanos: unir, cambiar de hijo sin clave, sugerencias por celular y avisos de todos al mismo celular."""
import json
from unittest import mock

from django.core.cache import cache
from django.urls import reverse

from notas import familia, push
from notas.models import Curso, Estudiante, Familia, FichaEstudiante, Notificacion, SuscripcionPush

from .base import CLAVE, ColegioDePrueba
from .test_push import _celular, _Respuesta


class Familias(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ana, cls.beto, cls.caro = cls.estudiantes

    def setUp(self):
        cache.clear()                    # el contador de intentos no pasa de una prueba a otra

    def test_el_acudiente_agrega_otro_hijo_con_su_clave(self):
        c = self.cliente(self.ana.user)
        c.post(reverse('notas:mi_familia'), {'accion': 'agregar', 'usuario': 'beto', 'clave': 'mala'})
        self.ana.refresh_from_db()
        self.assertIsNone(self.ana.familia_id)
        c.post(reverse('notas:mi_familia'), {'accion': 'agregar', 'usuario': self.beto.user.username, 'clave': CLAVE})
        self.ana.refresh_from_db()
        self.beto.refresh_from_db()
        self.assertIsNotNone(self.ana.familia_id)
        self.assertEqual(self.ana.familia_id, self.beto.familia_id)
        self.assertContains(c.get(reverse('notas:mi_familia')), 'Ver a Beto')

    def test_no_se_puede_agregar_un_estudiante_de_otro_colegio(self):
        otro_colegio = self.b
        ajeno = self.crear_estudiante('ajeno', curso=Curso.objects.create(colegio=otro_colegio, nombre='601', grado=6),
                                      colegio=otro_colegio)
        self.cliente(self.ana.user).post(reverse('notas:mi_familia'),
                                         {'accion': 'agregar', 'usuario': ajeno.user.username, 'clave': CLAVE})
        self.assertFalse(Familia.objects.exists())

    def test_demasiados_intentos_se_frenan(self):
        c = self.cliente(self.ana.user)
        for _ in range(6):
            c.post(reverse('notas:mi_familia'), {'accion': 'agregar', 'usuario': self.beto.user.username, 'clave': 'mala'})
        c.post(reverse('notas:mi_familia'), {'accion': 'agregar', 'usuario': self.beto.user.username, 'clave': CLAVE})
        self.assertFalse(Familia.objects.exists())

    def test_cambiar_de_hijo_solo_dentro_de_la_familia(self):
        familia.unir([self.ana, self.beto])
        c = self.cliente(self.ana.user)
        c.post(reverse('notas:cambiar_de_hijo', args=[self.beto.id]))
        self.assertEqual(int(c.session['_auth_user_id']), self.beto.user.id)
        c.post(reverse('notas:cambiar_de_hijo', args=[self.caro.id]))       # caro no es de la familia
        self.assertEqual(int(c.session['_auth_user_id']), self.beto.user.id)

    def test_unir_junta_familias_y_separar_deshace(self):
        familia.unir([self.ana, self.beto])
        otro = self.crear_estudiante('dani')
        familia.unir([self.caro, otro])
        familia.unir([self.beto, self.caro])
        self.assertEqual(Familia.objects.count(), 1)
        self.assertEqual(Estudiante.objects.filter(familia__isnull=False).count(), 4)
        for e in (self.ana, self.caro, otro):
            e.refresh_from_db()
            familia.separar(e)
        self.assertFalse(Familia.objects.exists())                      # quedó uno solo: se deshizo
        self.assertFalse(Estudiante.objects.filter(familia__isnull=False).exists())

    def test_sugerencias_por_celular_compartido(self):
        FichaEstudiante.objects.create(estudiante=self.ana, celular_madre='300 123 4567')
        FichaEstudiante.objects.create(estudiante=self.beto, celular_acudiente='3001234567', celular_padre='3150000000')
        FichaEstudiante.objects.create(estudiante=self.caro, celular_padre='315-000-0000')
        grupos = familia.sugerencias(self.a)
        self.assertEqual([{e.pk for e in g} for g in grupos], [{self.ana.pk, self.beto.pk, self.caro.pk}])
        r = self.cliente(self.rectora).post(reverse('notas:familias'),
                                            {'accion': 'unir', 'estudiantes': [self.ana.pk, self.beto.pk, self.caro.pk]})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(familia.sugerencias(self.a), [])
        self.assertEqual(Estudiante.objects.filter(familia__isnull=False).count(), 3)

    def test_la_pagina_de_familias_es_solo_para_administrativos(self):
        self.assertEqual(self.cliente(self.ana.user).get(reverse('notas:familias')).status_code, 403)
        self.assertEqual(self.cliente(self.rectora).get(reverse('notas:familias')).status_code, 200)


@mock.patch.object(push, 'EN_SEGUNDO_PLANO', False)
class AvisosDeTodosLosHijos(ColegioDePrueba):

    def _suscribir(self, usuario, endpoint):
        _, p256dh, auth = _celular()
        self.cliente(usuario).post('/app/push/suscribir/', json.dumps(
            {'endpoint': endpoint, 'keys': {'p256dh': p256dh, 'auth': auth}}), content_type='application/json')

    def test_al_celular_de_la_cuenta_de_ana_le_llegan_los_avisos_de_beto_con_su_nombre(self):
        ana, beto = self.estudiantes[0], self.estudiantes[1]
        familia.unir([ana, beto])
        self._suscribir(ana.user, 'https://fcm.googleapis.com/fcm/send/cel-mama')
        with mock.patch.object(push, 'enviar_a', return_value='ok') as mandar, self.captureOnCommitCallbacks(execute=True):
            Notificacion.objects.create(colegio=self.a, destinatario=beto.user, mensaje='Nueva circular N.º 4')
        self.assertEqual(mandar.call_count, 1)
        self.assertEqual(mandar.call_args[0][0].endpoint, 'https://fcm.googleapis.com/fcm/send/cel-mama')
        self.assertEqual(mandar.call_args[0][1]['cuerpo'], 'Beto: Nueva circular N.º 4')

    def test_un_celular_con_las_dos_cuentas_recibe_una_sola_vez(self):
        ana, beto = self.estudiantes[0], self.estudiantes[1]
        familia.unir([ana, beto])
        self._suscribir(ana.user, 'https://fcm.googleapis.com/fcm/send/cel')
        self._suscribir(beto.user, 'https://fcm.googleapis.com/fcm/send/cel')
        self.assertEqual(SuscripcionPush.objects.count(), 2)
        with mock.patch('urllib.request.urlopen', return_value=_Respuesta()) as abrir, \
                self.captureOnCommitCallbacks(execute=True):
            Notificacion.objects.create(colegio=self.a, destinatario=ana.user, mensaje='Hola')
        self.assertEqual(abrir.call_count, 1)

    def test_sin_familia_no_le_llega_a_otros(self):
        ana, beto = self.estudiantes[0], self.estudiantes[1]
        self._suscribir(ana.user, 'https://fcm.googleapis.com/fcm/send/cel-ana')
        with mock.patch.object(push, 'enviar_a', return_value='ok') as mandar, self.captureOnCommitCallbacks(execute=True):
            Notificacion.objects.create(colegio=self.a, destinatario=beto.user, mensaje='Solo para Beto')
        mandar.assert_not_called()
