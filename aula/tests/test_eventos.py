"""Eventos: la olimpiada de matemáticas (apagada hasta que el organizador la activa; el servidor cuenta)."""
import json

from aula.models import Evento, ParticipacionEvento
from notas.models import Curso
from notas.tests.base import ColegioDePrueba


class Olimpiada(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def setUp(self):
        self.ana, self.beto, _ = self.estudiantes
        self.admin = self.cliente(self.rectora)

    def crear(self, titulo='Olimpiada del colegio'):
        self.admin.post('/aula/eventos/', {'titulo': titulo})
        return Evento.objects.order_by('-pk').first()

    def post(self, cliente, url, datos):
        return cliente.post(url, json.dumps(datos), content_type='application/json').json()

    def test_el_nombre_lo_pone_el_organizador_y_queda_apagado(self):
        ev = self.crear('Mi gran olimpiada')
        self.assertEqual((ev.titulo, ev.activo), ('Mi gran olimpiada', False))
        self.assertEqual(len(ev.preguntas), 45)                     # banco inicial
        self.admin.post('/aula/eventos/', {'titulo': '  '})
        self.assertEqual(Evento.objects.count(), 1)                 # sin nombre no se crea
        # Apagado: el estudiante no lo ve ni puede entrar
        c = self.cliente(self.ana.user)
        self.assertNotContains(c.get('/aula/eventos/'), 'Mi gran olimpiada')
        self.assertEqual(c.get(f'/aula/eventos/{ev.pk}/').status_code, 404)
        self.assertNotContains(c.get('/aula/'), 'Eventos</div>')
        # Activado
        self.admin.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'activar'})
        ev.refresh_from_db()
        self.assertTrue(ev.activo)
        self.assertContains(c.get('/aula/eventos/'), 'Mi gran olimpiada')
        self.assertContains(c.get(f'/aula/eventos/{ev.pk}/'), 'olimpiada.js')
        self.assertContains(c.get('/aula/'), 'Eventos</div>')
        # El estudiante no configura
        self.assertEqual(c.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'activar'}).status_code, 403)

    def test_docente_organizador(self):
        ev = self.crear()
        profe = self.cliente(self.u_docente)
        self.assertEqual(profe.get(f'/aula/eventos/{ev.pk}/configurar/').status_code, 403)
        self.admin.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'organizadores', 'organizadores': [self.u_docente.pk]})
        self.assertEqual(profe.get(f'/aula/eventos/{ev.pk}/configurar/').status_code, 200)
        profe.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'config', 'titulo': 'Otro nombre', 'bloques': '3', 'minutos': '10',
                                                        'descanso': '2', 'cada': '4', 'por_parada': '5', 'bono': '30',
                                                        'g_tangram': ['6', '7'], 'd_tangram': 'dificil', 'g_geoplano': ['10', '11']})
        ev.refresh_from_db()
        self.assertEqual((ev.titulo, ev.config['bloques'], ev.config['por_parada'], ev.config['juegos']), ('Otro nombre', 3, 2, ['tangram', 'geoplano']))
        self.assertEqual(ev.config['por_juego']['tangram'], {'grados': [6, 7], 'dificultad': 'dificil'})

    def test_juegos_por_grado(self):
        ev = self.crear(); ev.activo = True
        ev.config = dict(ev.config, juegos=['tangram', 'geoplano'], por_juego={'tangram': {'grados': [6], 'dificultad': 'media'}, 'geoplano': {'grados': [10], 'dificultad': 'auto'}})
        ev.save()
        c = self.cliente(self.ana.user)          # Ana está en 6.º
        r = c.get(f'/aula/eventos/{ev.pk}/')
        datos = r.context['datos']
        self.assertEqual([j[0] for j in datos['juegos']], ['tangram'])
        self.assertEqual(datos['dificultad']['tangram'], 'media')
        # un punto en un juego que no es de su grado no cuenta
        r = self.post(c, f'/aula/eventos/{ev.pk}/registro/', {'eventos': [{'seq': 1, 'tipo': 'punto', 'juego': 'geoplano', 'nivel': 1, 't': 10},
                                                                          {'seq': 2, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 1, 't': 20}]})
        self.assertEqual(r['puntos'], 1)
        # sin juegos para su grado no puede entrar
        ev.config = dict(ev.config, por_juego={'tangram': {'grados': [9]}, 'geoplano': {'grados': [10]}})
        ev.save()
        self.assertEqual(c.get(f'/aula/eventos/{ev.pk}/').status_code, 302)

    def test_puntos_preguntas_y_ranking(self):
        ev = self.crear()
        ev.activo = True
        ev.config = dict(ev.config, cada=2, por_parada=1, juegos=['tangram', 'geoplano'])
        ev.save()
        c = self.cliente(self.ana.user)
        url = f'/aula/eventos/{ev.pk}'
        r = self.post(c, url + '/registro/', {'eventos': [{'seq': 1, 'tipo': 'inicio'}]})
        p = ParticipacionEvento.objects.get(evento=ev, estudiante=self.ana)
        self.assertEqual((p.ciclo, r['puntos']), ('exploradores', 0))
        # Antes de 2 puntos no hay pregunta
        self.assertIsNone(c.get(url + '/pregunta/').json()['pregunta'])
        r = self.post(c, url + '/registro/', {'eventos': [{'seq': 2, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 1, 't': 10},
                                                          {'seq': 2, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 1, 't': 10},     # repetido
                                                          {'seq': 3, 'tipo': 'punto', 'juego': 'otro', 'nivel': 1, 't': 20},       # juego no habilitado
                                                          {'seq': 4, 'tipo': 'punto', 'juego': 'geoplano', 'nivel': 2, 't': 11},  # muy rápido
                                                          {'seq': 5, 'tipo': 'punto', 'juego': 'geoplano', 'nivel': 2, 't': 40}]})
        self.assertEqual((r['puntos'], r['debe']), (2, 1))
        q = c.get(url + '/pregunta/').json()['pregunta']
        self.assertTrue(q['texto'])
        self.assertNotIn('clave', q)                                    # el estudiante no ve la respuesta
        self.assertEqual(q['categoria'], 'Euclides')
        # Responder: se busca la correcta con lo que guardó el servidor
        p.refresh_from_db()
        x = ev.preguntas[p.pendiente['i']]
        k = next(j for j, o in enumerate(p.pendiente['orden']) if x['opciones'][o]['correcta'])
        r = self.post(c, url + '/responder/', {'k': k})
        self.assertTrue(r['bien'])
        p.refresh_from_db()
        self.assertEqual((p.puntos, p.bonos, p.preguntas_hechas, p.tiempo_efectivo), (2, 1, 1, 10.0))   # 40 s − 30 s
        self.assertIsNone(c.get(url + '/pregunta/').json()['pregunta'])     # ya respondió la que le tocaba
        # Beto: 2 puntos más lento y sin bono → Ana va primero
        b = self.cliente(self.beto.user)
        self.post(b, url + '/registro/', {'eventos': [{'seq': 1, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 0, 't': 5},
                                                      {'seq': 2, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 3, 't': 30}]})
        r = self.admin.get(url + '/resultados/')
        filas = r.context['tablas'][0][2]
        self.assertEqual([f.estudiante for f in filas], [self.ana, self.beto])
        self.assertIn('Ana Prueba', self.admin.get(url + '/resultados/?csv=1').content.decode())

    def test_fuera_de_los_grados(self):
        ev = self.crear(); ev.activo = True; ev.save()
        quinto = Curso.objects.create(colegio=self.a, nombre='501', grado=5, subgrupo='1')
        e5 = self.crear_estudiante('quinta', curso=quinto)
        c = self.cliente(e5.user)
        self.assertEqual(c.get(f'/aula/eventos/{ev.pk}/').status_code, 302)
        self.assertTrue(self.post(c, f'/aula/eventos/{ev.pk}/registro/', {'eventos': []}).get('prueba'))

    def test_preguntas_pegadas_e_importadas(self):
        ev = self.crear()
        url = f'/aula/eventos/{ev.pk}/configurar/'
        self.admin.post(url, {'accion': 'pegar', 'ciclo': 'expertos', 'categoria': 'newton', 'texto': '1. ¿2³?\nA) 6\n*B) 8\n2. Sin correcta\nA) 1\nB) 2'})
        ev.refresh_from_db()
        self.assertEqual(len(ev.preguntas), 46)
        # Importar de un juego del salón virtual
        from aula.models import Aula, JuegoAula
        profe = self.cliente(self.u_docente); profe.get(f'/aula/asignacion/{self.asig.id}/')
        aula = Aula.objects.get(asignacion=self.asig)
        j = JuegoAula.objects.create(aula=aula, tipo='laberinto', titulo='Repaso', preguntas=[{'texto': '¿3 + 3?', 'opciones': [{'texto': '6', 'correcta': True}, {'texto': '7', 'correcta': False}]}])
        self.admin.post(url, {'accion': 'importar', 'juego': j.pk, 'ciclo': 'exploradores', 'categoria': 'newton'})
        ev.refresh_from_db()
        self.assertEqual(ev.preguntas[-1]['origen'], 'Salón virtual: Repaso')
        self.admin.post(url, {'accion': 'quitar', 'i': len(ev.preguntas) - 1})
        ev.refresh_from_db()
        self.assertEqual(len(ev.preguntas), 46)

    def test_grupos_con_nombre_y_grados_de_primaria(self):
        ev = self.crear(); ev.activo = True; ev.save()
        quinto = Curso.objects.create(colegio=self.a, nombre='501', grado=5, subgrupo='1')
        e5 = self.crear_estudiante('quinta', curso=quinto)
        url = f'/aula/eventos/{ev.pk}/configurar/'
        self.assertContains(self.admin.get(url), 'Grupos de participantes')
        # Se agrega un grupo de primaria con el nombre que se quiera
        self.admin.post(url, {'accion': 'grupos', 'gn_exploradores': 'Exploradores', 'gg_exploradores': ['6', '7'], 'gl_exploradores': '0',
                              'gn_investigadores': 'Investigadores', 'gg_investigadores': ['8', '9'], 'gl_investigadores': '1',
                              'gn_expertos': 'Expertos', 'gg_expertos': ['10', '11'], 'gl_expertos': '2',
                              'nuevo_nombre': 'Pequeños Genios', 'ng_nuevo': ['3', '4', '5'], 'nl_nuevo': '0'})
        ev.refresh_from_db()
        g = ev.config['grupos'][-1]
        self.assertEqual((g['nombre'], g['grados'], g['id']), ('Pequeños Genios', [3, 4, 5], 'pequeñosgenios'))
        c = self.cliente(e5.user)
        r = c.get(f'/aula/eventos/{ev.pk}/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['datos']['grupo']['nombre'], 'Pequeños Genios')
        self.post(c, f'/aula/eventos/{ev.pk}/registro/', {'eventos': [{'seq': 1, 'tipo': 'inicio'}]})
        self.assertEqual(ParticipacionEvento.objects.get(estudiante=e5).ciclo, 'pequeñosgenios')
        # Un grado no puede estar en dos grupos
        self.admin.post(url, {'accion': 'grupos', 'gn_exploradores': 'X', 'gg_exploradores': ['5', '6'], 'gl_exploradores': '0',
                              'gn_pequeñosgenios': 'Pequeños Genios', 'gg_pequeñosgenios': ['5']})
        ev.refresh_from_db()
        self.assertEqual(ev.config['grupos'][0]['grados'], [6, 7])          # no cambió
        # Resultados con el grupo nuevo
        self.assertContains(self.admin.get(f'/aula/eventos/{ev.pk}/resultados/'), 'Pequeños Genios')

    def test_participantes_por_curso_o_por_estudiante(self):
        ev = self.crear(); ev.activo = True; ev.save()
        otro = Curso.objects.create(colegio=self.a, nombre='602', grado=6, subgrupo='2')
        e602 = self.crear_estudiante('dora', curso=otro)
        url = f'/aula/eventos/{ev.pk}/configurar/'
        self.admin.post(url, {'accion': 'participantes', 'modo': 'cursos', 'cursos': [self.curso.pk]})
        self.assertEqual(self.cliente(self.ana.user).get(f'/aula/eventos/{ev.pk}/').status_code, 200)
        self.assertEqual(self.cliente(e602.user).get(f'/aula/eventos/{ev.pk}/').status_code, 302)
        # Solo algunos estudiantes (por ejemplo, los clasificados)
        self.admin.post(url, {'accion': 'participantes', 'modo': 'estudiantes', 'estudiantes': [e602.pk]})
        self.assertEqual(self.cliente(self.ana.user).get(f'/aula/eventos/{ev.pk}/').status_code, 302)
        self.assertEqual(self.cliente(e602.user).get(f'/aula/eventos/{ev.pk}/').status_code, 200)
        self.assertTrue(self.post(self.cliente(self.ana.user), f'/aula/eventos/{ev.pk}/registro/', {'eventos': []}).get('prueba'))

    def test_el_docente_crea_su_evento(self):
        profe = self.cliente(self.u_docente)
        self.assertContains(profe.get('/aula/'), 'Eventos</div>')          # la tarjeta le aparece a todo docente
        profe.post('/aula/eventos/', {'titulo': 'Reto de 6.º', 'alcance': 'codigo'})
        ev = Evento.objects.get(titulo='Reto de 6.º')
        self.assertEqual((ev.creador, ev.alcance, len(ev.codigo), ev.colegio), (self.u_docente, 'codigo', 6, self.a))
        self.assertEqual(profe.get(f'/aula/eventos/{ev.pk}/configurar/').status_code, 200)
        self.assertContains(profe.get(f'/aula/eventos/{ev.pk}/configurar/'), ev.codigo)
        # otro docente no lo configura
        from django.contrib.auth.models import User
        from notas.models import Docente
        u2 = User.objects.create_user('otra', password='x'); Docente.objects.create(colegio=self.a, user=u2)
        self.assertEqual(self.cliente(u2).get(f'/aula/eventos/{ev.pk}/configurar/').status_code, 403)

    def test_salon_digital_y_participantes_de_afuera(self):
        from django.contrib.auth.models import User
        from django.test import Client
        from salon_digital.models import Cuenta
        u = User.objects.create_user('libre', password='x', first_name='Lina')
        Cuenta.objects.create(usuario=u, slug='lina', nombre_publico='Lina')
        docente = Client(HTTP_HOST='testserver'); docente.force_login(u)
        docente.post('/aula/eventos/', {'titulo': 'Olimpiada intercolegial'})
        ev = Evento.objects.get(titulo='Olimpiada intercolegial')
        self.assertEqual((ev.colegio, ev.alcance, ev.creador), (None, 'codigo', u))
        # Apagado: no se puede inscribir
        anon = Client(HTTP_HOST='testserver')
        r = anon.post(f'/aula/eventos/c/{ev.codigo}/', {'nombre': 'Pedro Pérez', 'institucion': 'Colegio Otro', 'grado': '7'})
        self.assertFalse(ParticipacionEvento.objects.exists())
        docente.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'activar'})
        # Entra con el código, sin cuenta
        r = anon.post('/aula/eventos/entrar/', {'codigo': ev.codigo.lower()})
        self.assertRedirects(r, f'/aula/eventos/c/{ev.codigo}/', fetch_redirect_response=False)
        r = anon.post(f'/aula/eventos/c/{ev.codigo}/', {'nombre': 'Pedro Pérez', 'institucion': 'Colegio Otro', 'grado': '7'})
        self.assertRedirects(r, f'/aula/eventos/{ev.pk}/', fetch_redirect_response=False)
        p = ParticipacionEvento.objects.get(evento=ev)
        self.assertEqual((p.nombre, p.institucion, p.grado, p.ciclo, p.estudiante), ('Pedro Pérez', 'Colegio Otro', 7, 'exploradores', None))
        r = anon.get(f'/aula/eventos/{ev.pk}/')
        self.assertEqual(r.context['datos']['grupo']['nombre'], 'Exploradores')
        r = anon.post(f'/aula/eventos/{ev.pk}/registro/', json.dumps({'eventos': [{'seq': 1, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 0, 't': 9}]}),
                      content_type='application/json').json()
        self.assertEqual(r['puntos'], 1)
        # Una estudiante de otro colegio también entra con el código (se le llena su nombre)
        ana = self.cliente(self.ana.user)
        self.assertContains(ana.get(f'/aula/eventos/c/{ev.codigo}/'), 'Ana Prueba')
        # Resultados del docente: nombre e institución
        r = docente.get(f'/aula/eventos/{ev.pk}/resultados/')
        self.assertContains(r, 'Pedro Pérez')
        self.assertContains(r, 'Colegio Otro')
        # Sin inscripción no se juega: lo manda a inscribirse
        self.assertEqual(Client(HTTP_HOST='testserver').get(f'/aula/eventos/{ev.pk}/').status_code, 302)

    def test_evento_del_colegio_no_se_ve_desde_afuera(self):
        from django.test import Client
        ev = self.crear(); ev.activo = True; ev.save()
        self.assertEqual(Client(HTTP_HOST='testserver').get(f'/aula/eventos/{ev.pk}/').status_code, 404)
