"""Mis colegas: docentes de distintos colegios y de Mi Salón Virtual se agregan, se escriben y arman grupos."""
import json

from django.contrib.auth.models import User

from notas.models import Docente, Notificacion
from notas.tests.base import ColegioDePrueba
from salon_digital.models import Cuenta

from .models import Colega, Conversacion, Mensaje, PerfilColega


class Colegas(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.de_b = User.objects.create_user('bea', password='x', first_name='Beatriz', last_name='Bonilla')
        Docente.objects.create(colegio=cls.b, user=cls.de_b)                    # docente de otro colegio
        cls.libre = User.objects.create_user('lucho', password='x', first_name='Luis', last_name='Libre')
        Cuenta.objects.create(usuario=cls.libre, slug='lucho', nombre_publico='Luis Libre', estado='verificada',
                              institucion='IE Fátima', municipio='Líbano', departamento='Tolima')   # Salón Digital
        cls.ana = cls.estudiantes[0]

    def _post(self, c, url, datos):
        return c.post(url, datos, HTTP_HOST='a.localhost')

    def test_solicitud_escribir_y_bloquear(self):
        profe, bea, lucho = self.cliente(self.u_docente), self.cliente(self.de_b), self.cliente(self.libre)
        # Buscar: aparecen docentes de otros colegios y del Salón Digital; nunca estudiantes
        r = profe.get('/chat/colegas/?q=Libre')
        self.assertContains(r, 'Luis Libre'); self.assertContains(r, 'IE Fátima')
        self.assertNotContains(profe.get(f'/chat/colegas/?q={self.ana.user.first_name}'), 'Agregar</button>')
        # Los estudiantes no entran
        self.assertEqual(self.cliente(self.ana.user).get('/chat/colegas/').status_code, 403)
        # Sin ser colegas no se pueden escribir
        profe.post('/chat/colegas/escribir/', {'usuario': self.libre.pk})
        self.assertFalse(Conversacion.objects.filter(colegio__isnull=True).exists())
        # Solicitud → aviso → aceptar
        profe.post('/chat/colegas/solicitud/', {'usuario': self.libre.pk, 'accion': 'enviar'})
        self.assertTrue(Notificacion.objects.filter(destinatario=self.libre, mensaje__contains='quiere ser su colega').exists())
        self.assertContains(lucho.get('/chat/colegas/'), 'Le quieren agregar')
        self.assertEqual(lucho.get('/chat/colegas/no-leidos/').json()['solicitudes'], 1)
        lucho.post('/chat/colegas/solicitud/', {'usuario': self.u_docente.pk, 'accion': 'aceptar'})
        self.assertEqual(Colega.objects.get().estado, 'aceptada')
        # Ahora sí: conversación uno a uno (siempre la misma), con mensaje y aviso
        r = profe.post('/chat/colegas/escribir/', {'usuario': self.libre.pk})
        conv = Conversacion.objects.get(colegio__isnull=True)
        self.assertEqual(conv.tipo, 'colegas'); self.assertRedirects(r, f'/chat/colegas/c/{conv.pk}/', fetch_redirect_response=False)
        lucho.post('/chat/colegas/escribir/', {'usuario': self.u_docente.pk})
        self.assertEqual(Conversacion.objects.filter(colegio__isnull=True).count(), 1)
        r = profe.post(f'/chat/colegas/c/{conv.pk}/enviar/', json.dumps({'texto': 'Hola, ¿armamos la olimpiada?'}), content_type='application/json')
        self.assertTrue(r.json()['ok'])
        self.assertTrue(Notificacion.objects.filter(destinatario=self.libre, url=f'/chat/colegas/c/{conv.pk}/').exists())
        self.assertEqual(lucho.get('/chat/colegas/no-leidos/').json()['n'], 1)
        r = lucho.get(f'/chat/colegas/c/{conv.pk}/')
        self.assertContains(r, 'armamos la olimpiada'); self.assertContains(r, 'Pedro Profe')
        self.assertEqual(lucho.get('/chat/colegas/no-leidos/').json()['n'], 0)
        # Alguien que no está en la conversación no la ve
        self.assertEqual(bea.get(f'/chat/colegas/c/{conv.pk}/').status_code, 404)
        # Las conversaciones de colegas no aparecen en el chat del colegio
        self.assertNotContains(profe.get('/chat/'), 'armamos la olimpiada')
        # Bloquear: ya no se escriben ni puede volver a enviar solicitud
        lucho.post('/chat/colegas/solicitud/', {'usuario': self.u_docente.pk, 'accion': 'bloquear'})
        r = profe.post(f'/chat/colegas/c/{conv.pk}/enviar/', json.dumps({'texto': 'Hola'}), content_type='application/json')
        self.assertEqual(r.status_code, 403)
        profe.post('/chat/colegas/solicitud/', {'usuario': self.libre.pk, 'accion': 'enviar'})
        self.assertEqual(list(Colega.objects.values_list('estado', flat=True)), ['bloqueada'])
        self.assertEqual(profe.get('/chat/colegas/?q=Libre').context['encontrados'], [])      # quien lo bloqueó no aparece

    def test_grupo_de_docentes(self):
        profe, bea, lucho = self.cliente(self.u_docente), self.cliente(self.de_b), self.cliente(self.libre)
        for u in (self.de_b, self.libre):
            Colega.objects.create(de=self.u_docente, para=u, estado='aceptada')
        r = profe.post('/chat/colegas/grupo/nuevo/', {'nombre': 'Jurado olimpiada Zona Norte', 'todos': 'on'})
        conv = Conversacion.objects.get(tipo='colegas_g')
        self.assertRedirects(r, f'/chat/colegas/c/{conv.pk}/', fetch_redirect_response=False)
        self.assertEqual(set(conv.participantes.filter(activo=True).values_list('usuario__username', flat=True)), {'profe', 'bea', 'lucho'})
        self.assertTrue(Notificacion.objects.filter(destinatario=self.de_b, mensaje__contains='Jurado olimpiada').exists())
        # Bea y Lucho no son colegas entre sí, pero en el grupo se leen
        bea.post(f'/chat/colegas/c/{conv.pk}/enviar/', json.dumps({'texto': 'Yo reviso las de 9.º'}), content_type='application/json')
        r = lucho.get(f'/chat/colegas/c/{conv.pk}/')
        self.assertContains(r, 'Yo reviso las de 9.º'); self.assertContains(r, 'Grupo de docentes')
        # Solo el moderador quita, renombra y deja «solo moderadores escriben»
        lucho.post(f'/chat/colegas/c/{conv.pk}/accion/', {'accion': 'quitar', 'usuario': self.de_b.pk})
        self.assertTrue(conv.participantes.get(usuario=self.de_b).activo)
        profe.post(f'/chat/colegas/c/{conv.pk}/accion/', {'accion': 'solo_lectura'})
        r = bea.post(f'/chat/colegas/c/{conv.pk}/enviar/', json.dumps({'texto': 'x'}), content_type='application/json')
        self.assertEqual(r.status_code, 403)
        profe.post(f'/chat/colegas/c/{conv.pk}/accion/', {'accion': 'renombrar', 'nombre': 'Jurado 2026'})
        conv.refresh_from_db(); self.assertEqual(conv.nombre, 'Jurado 2026')
        # Bea sale; si el moderador sale, otro queda de moderador
        bea.post(f'/chat/colegas/c/{conv.pk}/accion/', {'accion': 'salir'})
        self.assertFalse(conv.participantes.get(usuario=self.de_b).activo)
        profe.post(f'/chat/colegas/c/{conv.pk}/accion/', {'accion': 'salir'})
        self.assertTrue(conv.participantes.get(usuario=self.libre).moderador)

    def test_perfil_oculto(self):
        PerfilColega.objects.create(usuario=self.libre, visible=False)
        self.assertEqual(self.cliente(self.u_docente).get('/chat/colegas/?q=Libre').context['encontrados'], [])
        lucho = self.cliente(self.libre)
        lucho.post('/chat/colegas/ajustes/', {'visible': 'on', 'area': 'Matemáticas'})
        r = self.cliente(self.u_docente).get('/chat/colegas/?q=Matemáticas')
        self.assertContains(r, 'Luis Libre'); self.assertContains(r, 'Matemáticas')
        self.assertContains(lucho.get('/chat/colegas/?tab=perfil'), 'Cómo me ven los demás docentes')

    def test_foto_perfil_y_avisos(self):
        """Foto de perfil (cuadrada), página de perfil y la campana con los avisos de colegas."""
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        lucho, profe = self.cliente(self.libre), self.cliente(self.u_docente)
        b = io.BytesIO(); Image.new('RGB', (800, 500), '#3366cc').save(b, 'JPEG')
        lucho.post('/chat/colegas/ajustes/', {'visible': 'on', 'area': 'Matemáticas', 'grados': '6.º a 9.º', 'municipio': 'Líbano',
                                              'presentacion': 'Organizo olimpiadas', 'foto': SimpleUploadedFile('yo.jpg', b.getvalue(), content_type='image/jpeg')})
        p = PerfilColega.objects.get(usuario=self.libre)
        self.assertTrue(p.foto); self.assertEqual(Image.open(p.foto.path).size, (400, 400))
        # Lo que no es imagen no se guarda
        r = lucho.post('/chat/colegas/ajustes/', {'visible': 'on', 'foto': SimpleUploadedFile('x.jpg', b'hola', content_type='image/jpeg')})
        p.refresh_from_db(); self.assertTrue(p.foto)
        # La foto sale en la búsqueda y en el perfil
        r = profe.get('/chat/colegas/?q=Libre')
        self.assertContains(r, p.foto.url)
        r = profe.get(f'/chat/colegas/u/{self.libre.pk}/')
        self.assertContains(r, 'Organizo olimpiadas'); self.assertContains(r, '6.º a 9.º'); self.assertContains(r, 'Agregar como colega')
        # Solicitud con mensaje → la campana de Lucho la muestra; al abrir el aviso queda leído y lleva a las solicitudes
        profe.post('/chat/colegas/solicitud/', {'usuario': self.libre.pk, 'accion': 'enviar', 'mensaje': 'Hola, hagamos la olimpiada'})
        j = lucho.get('/chat/colegas/avisos/').json()
        self.assertEqual(j['n'], 1); self.assertIn('quiere ser su colega', j['avisos'][0]['mensaje']); self.assertEqual(j['avisos'][0]['icono'], 'fa-user-plus')
        r = lucho.get(j['avisos'][0]['url'])
        self.assertRedirects(r, '/chat/colegas/?tab=solicitudes', fetch_redirect_response=False)
        self.assertEqual(lucho.get('/chat/colegas/avisos/').json()['n'], 0)
        self.assertContains(lucho.get('/chat/colegas/?tab=solicitudes'), 'Hola, hagamos la olimpiada')
        # Aceptar → aviso para Pedro; al ver Mis colegas queda leído solo
        lucho.post('/chat/colegas/solicitud/', {'usuario': self.u_docente.pk, 'accion': 'aceptar'})
        acepto = Notificacion.objects.get(destinatario=self.u_docente, mensaje__contains='aceptó su solicitud')
        self.assertFalse(acepto.leido)
        self.assertIn('aceptó su solicitud', profe.get('/chat/colegas/avisos/').json()['avisos'][0]['mensaje'])
        profe.get('/chat/colegas/')
        acepto.refresh_from_db(); self.assertTrue(acepto.leido)
        # Marcar todo como leído
        Notificacion.objects.create(destinatario=self.libre, mensaje='otro', url='/chat/colegas/')
        lucho.post('/chat/colegas/avisos/leidos/')
        self.assertEqual(lucho.get('/chat/colegas/avisos/').json()['n'], 0)
        # Nadie abre avisos ajenos
        n = Notificacion.objects.filter(destinatario=self.u_docente).first()
        self.assertEqual(lucho.get(f'/chat/colegas/aviso/{n.pk}/').status_code, 404)
        # Perfil oculto: solo lo ven sus colegas
        p.visible = False; p.save()
        self.assertEqual(self.cliente(self.de_b).get(f'/chat/colegas/u/{self.libre.pk}/').status_code, 404)
        self.assertEqual(profe.get(f'/chat/colegas/u/{self.libre.pk}/').status_code, 200)
