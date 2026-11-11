"""Editar mensajes, buscar lo que se escribió y vaciar el chat (para mí o para todos) en los tres chats."""
import json
from datetime import timedelta

from django.utils import timezone

from .models import ConversacionSalon, Conversacion, Mensaje, MensajeSalon, Participante
from .tests import Chat, ChatMiSalon


class EnElColegio(Chat):
    def accion(self, cl, conv, datos):
        return cl.post(f'/chat/c/{conv.pk}/accion/', datos, HTTP_X_REQUESTED_WITH='fetch')

    def test_editar_buscar_y_vaciar(self):
        profe, ana, beto = self.cliente(self.u_docente), self.cliente(self.ana.user), self.cliente(self.beto.user)
        profe.post('/chat/grupo/', {'tipo': 'curso', 'id': self.curso.pk})
        conv = Conversacion.objects.get(tipo='curso')
        ana.get(f'/chat/c/{conv.pk}/'); beto.get(f'/chat/c/{conv.pk}/')
        m1 = self._enviar(ana, conv, 'La tarea de fracciones es para el lunes').json()['mensaje']
        self._enviar(profe, conv, 'Recuerden traer el compás')
        self.assertTrue(m1['puede_editar'])
        # Editar: solo lo propio; queda «editado» y la versión original para los directivos
        self.assertEqual(self.accion(beto, conv, {'accion': 'editar', 'mensaje': m1['id'], 'texto': 'hack'}).status_code, 403)
        j = self.accion(ana, conv, {'accion': 'editar', 'mensaje': m1['id'], 'texto': 'La tarea de fracciones es para el martes'}).json()
        self.assertTrue(j['ok']); self.assertTrue(j['mensaje']['editado'])
        self.assertEqual(self.accion(ana, conv, {'accion': 'editar', 'mensaje': m1['id'], 'texto': '  '}).status_code, 400)
        m = Mensaje.objects.get(pk=m1['id'])
        self.assertEqual((m.texto, m.texto_original), ('La tarea de fracciones es para el martes', 'La tarea de fracciones es para el lunes'))
        # Los que ya lo tenían en pantalla reciben el cambio
        ultimo = Mensaje.objects.order_by('-pk').first().pk
        j = beto.get(f'/chat/c/{conv.pk}/nuevos/?despues={ultimo}').json()
        self.assertEqual(j['editados'], [{'id': m.pk, 'texto': 'La tarea de fracciones es para el martes'}])
        self.assertContains(beto.get(f'/chat/c/{conv.pk}/'), 'editado · ')
        # Pasadas 24 horas ya no se edita
        Mensaje.objects.filter(pk=m.pk).update(creado=timezone.now() - timedelta(hours=25))
        self.assertEqual(self.accion(ana, conv, {'accion': 'editar', 'mensaje': m.pk, 'texto': 'x'}).status_code, 403)
        # Buscar: no importan las mayúsculas ni el orden de las palabras
        r = beto.get(f'/chat/c/{conv.pk}/nuevos/?q=martes FRACCIONES').json()['resultados']
        self.assertEqual([x['id'] for x in r], [m.pk])
        self.assertEqual(len(beto.get(f'/chat/c/{conv.pk}/nuevos/?q=compás').json()['resultados']), 1)
        self.assertEqual(beto.get(f'/chat/c/{conv.pk}/nuevos/?q=lunes').json()['resultados'], [])   # lo de antes de editar no
        # Abrir alrededor de un mensaje (desde el buscador)
        self.assertEqual(beto.get(f'/chat/c/{conv.pk}/?ver={m.pk}').status_code, 200)
        # Vaciar para mí: Beto ya no ve lo anterior; Ana sí
        beto.post(f'/chat/c/{conv.pk}/accion/', {'accion': 'limpiar', 'alcance': 'mi'})
        self.assertNotContains(beto.get(f'/chat/c/{conv.pk}/'), 'compás')
        self.assertEqual(beto.get(f'/chat/c/{conv.pk}/nuevos/?q=compás').json()['resultados'], [])
        self.assertContains(ana.get(f'/chat/c/{conv.pk}/'), 'compás')
        # Un estudiante no vacía para todos (le queda solo para él); el docente moderador sí
        ana.post(f'/chat/c/{conv.pk}/accion/', {'accion': 'limpiar', 'alcance': 'todos'})
        conv.refresh_from_db(); self.assertIsNone(conv.limpiado)
        self._enviar(profe, conv, 'Mensaje nuevo')
        profe.post(f'/chat/c/{conv.pk}/accion/', {'accion': 'limpiar', 'alcance': 'todos'})
        conv.refresh_from_db(); self.assertIsNotNone(conv.limpiado)
        r = self.cliente(self.u_docente).get(f'/chat/c/{conv.pk}/')
        self.assertNotContains(r, 'Mensaje nuevo'); self.assertContains(r, 'Vaciar para todos')
        self.assertEqual(Mensaje.objects.filter(conversacion=conv).count(), 3)   # no se borró nada de la base de datos
        # Una pantalla abierta se entera de que se vació (para recargarse)
        self.assertTrue(beto.get(f'/chat/c/{conv.pk}/nuevos/?despues=0').json()['corte'])

    def test_vaciar_en_chat_uno_a_uno(self):
        ana = self.cliente(self.ana.user)
        ana.post('/chat/nueva/', {'usuario': self.u_docente.pk})
        conv = Conversacion.objects.get()
        self._enviar(ana, conv, 'Hola profe')
        r = ana.get(f'/chat/c/{conv.pk}/')
        self.assertContains(r, 'Vaciar el chat (solo para mí)'); self.assertNotContains(r, 'Vaciar para todos')
        self.assertContains(r, 'id="ch-buscar"')


class EnMiSalon(ChatMiSalon):
    def test_editar_buscar_y_vaciar(self):
        grupo_conv = ConversacionSalon.objects.create(grupo=self.grupo)
        self.est_luis.post(f'{self.base}pin/', {'pin': self.luis.pin_chat})
        m = self._enviar(self.est_luis, grupo_conv.pk, 'Profe, ¿el quiz es de ecuaciones?').json()['mensaje']
        d = self._enviar(self.profe, grupo_conv.pk, 'Sí, de ecuaciones lineales').json()['mensaje']
        url = f'{self.base}c/{grupo_conv.pk}/accion/'
        # Luis edita lo suyo; Sara no; el docente edita lo suyo
        self.assertTrue(self.est_luis.post(url, {'accion': 'editar', 'mensaje': m['id'], 'texto': 'Profe, ¿el quiz es de funciones?'},
                                           HTTP_X_REQUESTED_WITH='fetch').json()['ok'])
        self.assertEqual(self.est_sara.post(url, {'accion': 'editar', 'mensaje': m['id'], 'texto': 'x'}).status_code, 403)
        self.assertEqual(self.profe.post(url, {'accion': 'editar', 'mensaje': m['id'], 'texto': 'x'}).status_code, 403)
        self.assertTrue(self.profe.post(url, {'accion': 'editar', 'mensaje': d['id'], 'texto': 'Sí, de funciones'}).json()['ok'])
        self.assertEqual(MensajeSalon.objects.get(pk=m['id']).texto_original, 'Profe, ¿el quiz es de ecuaciones?')
        # Buscar
        r = self.est_sara.get(f'{self.base}c/{grupo_conv.pk}/nuevos/?q=funciones').json()['resultados']
        self.assertEqual(len(r), 2)
        # Vaciar: Luis para sí; el docente para todos
        self.est_luis.post(url, {'accion': 'limpiar'})
        self.assertNotContains(self.est_luis.get(f'{self.base}c/{grupo_conv.pk}/'), 'funciones')
        self.assertContains(self.est_sara.get(f'{self.base}c/{grupo_conv.pk}/'), 'funciones')
        self.est_sara.post(url, {'accion': 'limpiar'})                                   # sin PIN no vacía
        self.assertContains(self.est_sara.get(f'{self.base}c/{grupo_conv.pk}/'), 'funciones')
        self.profe.post(url, {'accion': 'limpiar', 'alcance': 'todos'})
        self.assertNotContains(self.est_sara.get(f'{self.base}c/{grupo_conv.pk}/'), 'funciones')
        self.assertEqual(MensajeSalon.objects.filter(conversacion=grupo_conv).count(), 2)
