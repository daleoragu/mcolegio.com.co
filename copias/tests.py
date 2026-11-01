"""Copia de seguridad: qué trae el .zip, quién lo puede bajar y el recordatorio."""
import datetime
import io
import json
import zipfile
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from notas.models import Calificacion
from notas.tests.base import ColegioDePrueba

from .models import AjusteCopia


def _png():
    from PIL import Image
    b = io.BytesIO()
    Image.new('RGB', (20, 20), 'green').save(b, 'PNG')
    return SimpleUploadedFile('f.png', b.getvalue(), content_type='image/png')


class CopiaDeSeguridad(ColegioDePrueba):

    def _zip(self, cliente, medios='1'):
        r = cliente.get(f'/copias/archivo.zip?medios={medios}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/zip')
        return zipfile.ZipFile(io.BytesIO(r.content))

    def test_estudiante_chat_circulares_y_notas(self):
        from chat.models import AjustesChat, Conversacion
        from circulares.models import Circular, Lectura
        AjustesChat.objects.create(colegio=self.a, silencio_desde=datetime.time(0, 0), silencio_hasta=datetime.time(0, 0),
                                   silencio_fin_de_semana=False)
        ana = self.estudiantes[0]
        est = self.cliente(ana.user)
        est.post('/chat/nueva/', {'usuario': self.u_docente.pk})
        conv = Conversacion.objects.get()
        est.post(f'/chat/c/{conv.pk}/enviar/', json.dumps({'texto': 'Profe, mañana no voy'}), content_type='application/json')
        est.post(f'/chat/c/{conv.pk}/enviar/', {'archivo': _png(), 'texto': 'La excusa'})
        c = Circular.objects.create(colegio=self.a, numero=7, titulo='Salida pedagógica', cuerpo='El viernes salimos.',
                                    publicada=timezone.now())
        Lectura.objects.create(circular=c, usuario=ana.user)
        Calificacion.objects.create(colegio=self.a, estudiante=ana, materia=self.materia, periodo=self.p1,
                                    docente=self.docente, tipo_nota='PROM_PERIODO', valor_nota=Decimal('4.5'))
        z = self._zip(est)
        nombres = z.namelist()
        for esperado in ('index.html', 'mis-datos.html', 'chat/index.html', 'circulares/index.html'):
            self.assertIn(esperado, nombres)
        chat_html = next(z.read(n).decode() for n in nombres if n.startswith('chat/') and n.endswith('.html') and n != 'chat/index.html')
        self.assertIn('Profe, mañana no voy', chat_html)
        self.assertTrue(any(n.startswith('chat/medios/') for n in nombres))           # la foto va
        self.assertIn('Salida pedagógica', z.read('circulares/index.html').decode())
        notas = next(z.read(n).decode() for n in nombres if n.startswith('estudiante/'))
        self.assertIn('Matemáticas', notas)
        self.assertIn('4.5', notas)
        # Sin fotos ni audios
        z2 = self._zip(est, medios='0')
        self.assertFalse(any(n.startswith('chat/medios/') for n in z2.namelist()))
        # Lo de otra persona no aparece
        z3 = self._zip(self.cliente(self.estudiantes[1].user))
        self.assertNotIn('chat/index.html', z3.namelist())
        self.assertNotIn('circulares/index.html', z3.namelist())

    def test_docente_planillas_y_salon(self):
        ana = self.estudiantes[0]
        Calificacion.objects.create(colegio=self.a, estudiante=ana, materia=self.materia, periodo=self.p1,
                                    docente=self.docente, tipo_nota='PROM_PERIODO', valor_nota=Decimal('3.8'))
        z = self._zip(self.cliente(self.u_docente))
        csvs = [n for n in z.namelist() if n.startswith('docente/') and n.endswith('.csv')]
        self.assertEqual(len(csvs), 1)
        contenido = z.read(csvs[0]).decode('utf-8-sig')
        self.assertIn('3,8', contenido)
        # Docente de Mi Salón Virtual: su chat con el grupo
        from aula.tests.test_planilla_examenes import salon
        from chat.models import ConversacionSalon
        cuenta, grupo, luis, sara, profe, aula = salon()
        profe.get(f'/aula/{aula.pk}/chat/')
        conv = ConversacionSalon.objects.get(grupo=grupo, integrante__isnull=True)
        profe.post(f'/aula/{aula.pk}/chat/c/{conv.pk}/enviar/', json.dumps({'texto': 'Bienvenidos'}), content_type='application/json')
        r = profe.get('/copias/archivo.zip')
        z = zipfile.ZipFile(io.BytesIO(r.content))
        self.assertIn('chat-salon/index.html', z.namelist())
        self.assertContains(profe.get('/copias/'), 'Hacer copia ahora')

    def test_recordatorio(self):
        est = self.cliente(self.estudiantes[0].user)
        self.assertFalse(est.get('/copias/pendiente/').json()['pendiente'])          # no la ha activado
        est.post('/copias/ajustes/', {'destino': 'descarga', 'cada_dias': '7', 'medios': 'on'})
        a = AjusteCopia.objects.get(usuario=self.estudiantes[0].user)
        self.assertEqual((a.destino, a.cada_dias, a.incluir_medios), ('descarga', 7, True))
        self.assertTrue(est.get('/copias/pendiente/').json()['pendiente'])           # nunca la ha hecho
        j = est.post('/copias/hecha/', json.dumps({'destino': 'google', 'peso': 1234}), content_type='application/json').json()
        self.assertTrue(j['ok'])
        self.assertFalse(est.get('/copias/pendiente/').json()['pendiente'])
        AjusteCopia.objects.filter(pk=a.pk).update(ultima=timezone.now() - datetime.timedelta(days=8))
        self.assertTrue(est.get('/copias/pendiente/').json()['pendiente'])
        est.post('/copias/ajustes/', {'destino': 'descarga', 'cada_dias': '0'})
        self.assertFalse(est.get('/copias/pendiente/').json()['pendiente'])          # «solo cuando la pida»
        # Sin sesión no hay copia
        from django.test import Client
        self.assertEqual(Client(HTTP_HOST='a.localhost').get('/copias/archivo.zip').status_code, 302)
        # El menú la ofrece
        self.assertContains(self.cliente(self.u_docente).get('/panel-docente/'), '/copias/')
