"""Chat del colegio: quién habla con quién, grupos que se arman solos, silencio, borrar y reportar."""
import datetime
import json
from unittest import mock

from django.contrib.auth.models import User
from django.utils import timezone

from notas.models import Curso, Docente, Notificacion
from notas.tests.base import ColegioDePrueba

from . import reglas as R
from .models import AjustesChat, Conversacion, Mensaje, Participante, Reporte

SIN_SILENCIO = dict(silencio_desde=datetime.time(0, 0), silencio_hasta=datetime.time(0, 0), silencio_fin_de_semana=False)


class Chat(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        AjustesChat.objects.create(colegio=cls.a, **SIN_SILENCIO)
        cls.ana, cls.beto = cls.estudiantes[0], cls.estudiantes[1]
        cls.u_otra = User.objects.create_user('otra', password='x', first_name='Olga', last_name='Otra')
        Docente.objects.create(colegio=cls.a, user=cls.u_otra)          # docente sin clases en 601
        cls.otro_curso = Curso.objects.create(colegio=cls.a, nombre='702', grado=7, subgrupo='2')
        cls.dora = cls.crear_estudiante('dora', curso=cls.otro_curso)
        cls.curso_b = Curso.objects.create(colegio=cls.b, nombre='601B', grado=6, subgrupo='1')
        cls.de_b = cls.crear_estudiante('bruno', colegio=cls.b, curso=cls.curso_b)

    def _enviar(self, cliente, conv, texto):
        return cliente.post(f'/chat/c/{conv.pk}/enviar/', json.dumps({'texto': texto}), content_type='application/json')

    def test_quien_habla_con_quien(self):
        ana = self.ana.user
        contactos_ana = set(R.contactos(ana, self.a).values_list('username', flat=True))
        self.assertIn('profe', contactos_ana)           # docente y director de su curso
        self.assertIn('rectora', contactos_ana)         # directivos
        self.assertNotIn('beto', contactos_ana)         # nunca otro estudiante
        self.assertNotIn('otra', contactos_ana)         # docente que no le dicta
        self.assertNotIn('bruno', contactos_ana)        # otro colegio
        profe = set(R.contactos(self.u_docente, self.a).values_list('username', flat=True))
        self.assertTrue({'ana', 'beto', 'caro', 'otra', 'rectora'} <= profe)
        self.assertNotIn('dora', profe)                 # estudiante de un curso donde no dicta
        self.assertIn('dora', set(R.contactos(self.rectora, self.a).values_list('username', flat=True)))
        # Un estudiante no puede abrir un chat con otro
        c = self.cliente(ana)
        c.post('/chat/nueva/', {'usuario': self.beto.user.pk})
        self.assertFalse(Conversacion.objects.exists())
        # Alguien de otro colegio no entra al chat de este
        self.assertIn(self.cliente(self.de_b.user).get('/chat/').status_code, (302, 403))

    def test_conversacion_avisos_y_leidos(self):
        est = self.cliente(self.ana.user)
        r = est.post('/chat/nueva/', {'usuario': self.u_docente.pk})
        conv = Conversacion.objects.get()
        self.assertRedirects(r, f'/chat/c/{conv.pk}/', fetch_redirect_response=False)
        self.assertEqual(est.post('/chat/nueva/', {'usuario': self.u_docente.pk}).status_code, 302)
        self.assertEqual(Conversacion.objects.count(), 1)                     # la misma conversación
        self.assertTrue(self._enviar(est, conv, 'Profe, mañana no puedo ir, estoy enferma').json()['ok'])
        self._enviar(est, conv, 'Le mando la excusa')
        avisos = Notificacion.objects.filter(destinatario=self.u_docente, url=f'/chat/c/{conv.pk}/')
        self.assertEqual(avisos.count(), 1)                                   # un aviso por conversación
        profe = self.cliente(self.u_docente)
        self.assertEqual(profe.get('/chat/no-leidos/').json()['n'], 2)
        r = profe.get(f'/chat/c/{conv.pk}/')
        self.assertContains(r, 'Le mando la excusa')
        self.assertEqual(profe.get('/chat/no-leidos/').json()['n'], 0)
        self.assertFalse(avisos.filter(leido=False).exists())
        primero = Mensaje.objects.order_by('id').first()
        j = profe.get(f'/chat/c/{conv.pk}/nuevos/?despues={primero.pk}').json()
        self.assertEqual([m['texto'] for m in j['mensajes']], ['Le mando la excusa'])
        # Otra persona no ve la conversación
        self.assertEqual(self.cliente(self.beto.user).get(f'/chat/c/{conv.pk}/').status_code, 404)
        # Borrar deja rastro: el texto se guarda
        m = Mensaje.objects.get(texto='Le mando la excusa')
        est.post(f'/chat/c/{conv.pk}/accion/', {'accion': 'borrar', 'mensaje': m.pk})
        m.refresh_from_db()
        self.assertTrue(m.eliminado)
        self.assertNotContains(profe.get(f'/chat/c/{conv.pk}/'), 'Le mando la excusa')

    def test_horario_de_silencio(self):
        AjustesChat.objects.filter(colegio=self.a).update(silencio_desde=datetime.time(0, 0),
                                                          silencio_hasta=datetime.time(23, 59, 59))
        est = self.cliente(self.ana.user)
        est.post('/chat/nueva/', {'usuario': self.u_docente.pk})
        conv = Conversacion.objects.get()
        self._enviar(est, conv, 'Mensaje de noche')
        self.assertFalse(Notificacion.objects.filter(url=f'/chat/c/{conv.pk}/').exists())
        self.assertEqual(self.cliente(self.u_docente).get('/chat/no-leidos/').json()['n'], 1)   # sí queda en el chat
        sabado = timezone.make_aware(datetime.datetime(2026, 11, 7, 10, 0))
        AjustesChat.objects.filter(colegio=self.a).update(**SIN_SILENCIO)
        self.assertFalse(R.en_silencio(self.a, sabado))
        AjustesChat.objects.filter(colegio=self.a).update(silencio_fin_de_semana=True)
        self.assertTrue(R.en_silencio(self.a, sabado))
        noche = timezone.make_aware(datetime.datetime(2026, 11, 4, 22, 0))
        AjustesChat.objects.filter(colegio=self.a).update(silencio_desde=datetime.time(18, 0), silencio_hasta=datetime.time(6, 0))
        self.assertTrue(R.en_silencio(self.a, noche))
        self.assertFalse(R.en_silencio(self.a, noche.replace(hour=10)))

    def test_grupo_del_curso_solo_lectura_y_reporte(self):
        profe = self.cliente(self.u_docente)
        r = profe.post('/chat/grupo/', {'tipo': 'curso', 'id': self.curso.pk})
        conv = Conversacion.objects.get(tipo='curso')
        self.assertRedirects(r, f'/chat/c/{conv.pk}/', fetch_redirect_response=False)
        miembros = {p.usuario.username: p.moderador for p in conv.participantes.filter(activo=True)}
        self.assertEqual(miembros, {'ana': False, 'beto': False, 'caro': False, 'profe': True})
        # Un estudiante no abre grupos
        self.assertEqual(self.cliente(self.ana.user).post('/chat/grupo/', {'tipo': 'curso', 'id': self.curso.pk}).status_code, 404)
        # Estudiante nuevo en el curso: entra solo al grupo
        nuevo = self.crear_estudiante('eli')
        self.cliente(self.ana.user).get(f'/chat/c/{conv.pk}/')
        self.assertTrue(Participante.objects.filter(conversacion=conv, usuario=nuevo.user, activo=True).exists())
        # Sale del curso: deja de estar
        nuevo.curso = self.otro_curso
        nuevo.save()
        R.sincronizar(conv)
        self.assertFalse(Participante.objects.filter(conversacion=conv, usuario=nuevo.user, activo=True).exists())
        # Solo docentes escriben
        est = self.cliente(self.beto.user)
        self.assertTrue(self._enviar(est, conv, 'Hola a todos').json()['ok'])
        profe.post(f'/chat/c/{conv.pk}/accion/', {'accion': 'solo_lectura'})
        self.assertEqual(self._enviar(est, conv, 'Otro').status_code, 403)
        self.assertTrue(self._enviar(profe, conv, 'Recuerden la tarea').json()['ok'])
        # Reportar: avisa a los directivos y la rectora puede revisar la conversación
        m = Mensaje.objects.get(texto='Hola a todos')
        self.cliente(self.ana.user).post(f'/chat/m/{m.pk}/reportar/', {'motivo': 'Me están molestando'})
        self.assertTrue(Reporte.objects.filter(mensaje=m).exists())
        self.assertTrue(Notificacion.objects.filter(destinatario=self.rectora, url='/chat/administrar/').exists())
        rectora = self.cliente(self.rectora)
        self.assertContains(rectora.get('/chat/administrar/'), 'Me están molestando')
        self.assertContains(rectora.get(f'/chat/c/{conv.pk}/'), 'tiene mensajes reportados')
        rectora.post('/chat/administrar/', {'accion': 'resolver', 'reporte': Reporte.objects.get().pk, 'borrar': 'on',
                                            'nota': 'Se habló con el estudiante'})
        m.refresh_from_db()
        self.assertTrue(m.eliminado)
        # Un docente no administra el chat
        self.assertEqual(profe.get('/chat/administrar/').status_code, 403)

    def test_grupo_creado_por_el_docente(self):
        profe = self.cliente(self.u_docente)
        profe.post('/chat/grupo/nuevo/', {'nombre': 'Proyecto ambiental', 'miembros': [self.ana.user.pk, self.u_otra.pk,
                                                                                      self.dora.user.pk]})
        conv = Conversacion.objects.get(tipo='grupo')
        nombres = set(conv.participantes.values_list('usuario__username', flat=True))
        self.assertEqual(nombres, {'profe', 'ana', 'otra'})       # dora no es de sus cursos: no entra
        self.assertEqual(self.cliente(self.ana.user).get('/chat/grupo/nuevo/').status_code, 404)
        self.assertContains(self.cliente(self.ana.user).get('/chat/'), 'Proyecto ambiental')
        self.cliente(self.ana.user).post(f'/chat/c/{conv.pk}/accion/', {'accion': 'salir'})
        self.assertFalse(Participante.objects.get(conversacion=conv, usuario=self.ana.user).activo)

    def test_menu(self):
        self.a.modulos_activos = list(self.a.modulos_activos or []) + ['chat']
        self.a.save(update_fields=['modulos_activos'])
        self.assertContains(self.cliente(self.u_docente).get('/panel-docente/'), '/chat/')
        self.a.modulos_activos = [m for m in self.a.modulos_activos if m != 'chat']
        self.a.save(update_fields=['modulos_activos'])
        self.assertEqual(self.cliente(self.u_docente).get('/chat/').status_code, 403)
