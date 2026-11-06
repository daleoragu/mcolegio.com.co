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
        self.assertEqual(ev.config['por_juego']['tangram'], {'grados': [6, 7], 'dificultad': 'dificil', 'velocidad': 'normal'})

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
        r = anon.post(f'/aula/eventos/c/{ev.codigo}/', {'nombre': 'Pedro Pérez', 'institucion': 'Colegio Otro', 'grado': '7', 'autoriza': 'on'})
        self.assertFalse(ParticipacionEvento.objects.exists())
        docente.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'activar'})
        # Entra con el código, sin cuenta
        r = anon.post('/aula/eventos/entrar/', {'codigo': ev.codigo.lower()})
        self.assertRedirects(r, f'/aula/eventos/c/{ev.codigo}/', fetch_redirect_response=False)
        r = anon.post(f'/aula/eventos/c/{ev.codigo}/', {'nombre': 'Pedro Pérez', 'institucion': 'Colegio Otro', 'grado': '7', 'autoriza': 'on'})
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

    def test_juegos_arcade_y_propios_en_el_evento(self):
        from aula.models import Aula, JuegoAula
        profe = self.cliente(self.u_docente); profe.get(f'/aula/asignacion/{self.asig.id}/')
        aula = Aula.objects.get(asignacion=self.asig)
        j = JuegoAula.objects.create(aula=aula, tipo='impostor', titulo='Fracciones', preguntas=[
            {'texto': '1/2 + 1/2', 'opciones': [{'texto': '1', 'correcta': True}, {'texto': '2', 'correcta': False}]},
            {'texto': '1/4 + 1/4', 'opciones': [{'texto': '1/2', 'correcta': True}, {'texto': '1/8', 'correcta': False}]}])
        ev = self.crear(); ev.activo = True; ev.save()
        url = f'/aula/eventos/{ev.pk}/configurar/'
        r = self.admin.get(url)
        self.assertContains(r, 'Expulsa al impostor (arcade)')          # todos los arcade
        self.assertContains(r, 'Fracciones · Expulsa al impostor')       # y los propios del salón virtual
        datos = {'accion': 'config', 'titulo': ev.titulo, 'bloques': '2', 'minutos': '15', 'descanso': '3', 'cada': '5', 'por_parada': '1', 'bono': '30',
                 f'g_p_{j.pk}': ['6'], 'g_a_ovejas': ['6'], 'g_tangram': ['10']}
        self.admin.post(url, datos)
        r = self.cliente(self.ana.user).get(f'/aula/eventos/{ev.pk}/')
        d = r.context['datos']
        self.assertEqual(sorted(x[0] for x in d['juegos']), sorted([f'p_{j.pk}', 'a_ovejas']))
        self.assertEqual(d['motor'], {f'p_{j.pk}': 'impostor', 'a_ovejas': 'ovejas'})
        self.assertEqual(len(d['propios'][f'p_{j.pk}']['preguntas']), 2)
        self.assertContains(r, 'aula/juegos/impostor.js')
        self.assertContains(r, 'aula/juegos/ovejas.js')
        res = self.post(self.cliente(self.ana.user), f'/aula/eventos/{ev.pk}/registro/', {'eventos': [{'seq': 1, 'tipo': 'punto', 'juego': f'p_{j.pk}', 'nivel': 0, 't': 10}]})
        self.assertEqual(res['puntos'], 1)

    def test_resultados_con_filtros_y_velocidad(self):
        ev = self.crear(); ev.activo = True; ev.save()
        septimo = Curso.objects.create(colegio=self.a, nombre='701', grado=7, subgrupo='1')
        e7 = self.crear_estudiante('sofia', curso=septimo)
        for est, t in [(self.ana, 10), (e7, 5)]:
            self.post(self.cliente(est.user), f'/aula/eventos/{ev.pk}/registro/', {'eventos': [{'seq': 1, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 0, 't': t}]})
        url = f'/aula/eventos/{ev.pk}/resultados/'
        filas = self.admin.get(url + '?grado=7').context['tablas'][0][2]
        self.assertEqual([p.estudiante for p in filas], [e7])
        filas = self.admin.get(url + '?grupo=todos&q=ana').context['tablas'][0][2]
        self.assertEqual([p.estudiante for p in filas], [self.ana])
        self.assertEqual(len(self.admin.get(url + '?grupo=todos').context['tablas']), 1)
        csv = self.admin.get(url + '?grado=7&csv=1').content.decode()
        self.assertIn('Sofia Prueba', csv); self.assertNotIn('Ana Prueba', csv)
        # Velocidad por juego en el evento
        self.admin.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'config', 'titulo': ev.titulo, 'g_a_ovejas': ['6'], 'v_a_ovejas': 'lenta'})
        d = self.cliente(self.ana.user).get(f'/aula/eventos/{ev.pk}/').context['datos']
        self.assertEqual(d['ritmo']['a_ovejas'], .6)

    def test_inscripcion_con_aprobacion_y_cupos(self):
        """Los de fuera llenan el formulario; el organizador aprueba con cupos por institución y por nivel."""
        from django.contrib.auth.models import User
        from django.test import Client
        from salon_digital.models import Cuenta
        u = User.objects.create_user('libre2', password='x', first_name='Lina')
        Cuenta.objects.create(usuario=u, slug='lina2', nombre_publico='Lina')
        org = Client(HTTP_HOST='testserver'); org.force_login(u)
        org.post('/aula/eventos/', {'titulo': 'Intercolegial'})
        ev = Evento.objects.get(titulo='Intercolegial')
        org.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'inscripcion', 'abierta': 'on', 'aprobacion': 'on', 'cupo_colegio': '2', 'cupo_nivel': '1'})
        url = f'/aula/eventos/c/{ev.codigo}/'
        # Con aprobación se inscriben aunque el evento siga apagado, pero piden documento y contacto
        uno = Client(HTTP_HOST='testserver')
        r = uno.post(url, {'nombre': 'Pedro Pérez', 'institucion': 'Colegio San José', 'grado': '7'})
        self.assertContains(r, 'documento')
        datos = {'nombre': 'Pedro Pérez', 'institucion': 'Colegio San José', 'ciudad': 'Ibagué', 'grado': '7', 'documento': '100001', 'contacto': '3001234567'}
        # Sin la autorización de datos (y del acudiente) no se inscribe; los robots llenan el campo escondido
        self.assertContains(uno.post(url, datos), 'autorización del tratamiento')
        self.assertContains(uno.post(url, dict(datos, autoriza='on')), 'acudiente')
        datos.update(autoriza='on', acudiente='Rosa Pérez')
        self.assertContains(uno.post(url, dict(datos, sitio_web='http://spam')), 'No se pudo enviar')
        self.assertFalse(ParticipacionEvento.objects.filter(evento=ev).exists())
        r = uno.post(url, datos)
        self.assertRedirects(r, url, fetch_redirect_response=False)
        p = ParticipacionEvento.objects.get(evento=ev)
        self.assertEqual((p.estado, p.datos['ciudad'], len(p.datos['clave'])), ('pendiente', 'Ibagué', 6))
        self.assertEqual(p.datos['autorizacion']['acudiente'], 'Rosa Pérez')
        self.assertContains(uno.get(url), 'Inscripción recibida')
        # El cupo por nivel (1 en Exploradores) cuenta las pendientes; la misma institución escrita distinto es la misma
        dos = Client(HTTP_HOST='testserver')
        r = dos.post(url, dict(datos, nombre='María Gómez', documento='100002', institucion='colegio  san jose', grado='6'))
        self.assertContains(r, 'nivel Exploradores')
        r = dos.post(url, dict(datos, nombre='María Gómez', documento='100002', institucion='colegio  san jose', grado='8'))
        self.assertEqual(ParticipacionEvento.objects.filter(evento=ev).count(), 2)
        # El mismo documento no se inscribe dos veces; el cupo por institución (2) ya está lleno
        r = Client(HTTP_HOST='testserver').post(url, dict(datos, nombre='Otro Nombre', grado='10'))
        self.assertContains(r, 'Ya hay una inscripción con ese documento')
        r = Client(HTTP_HOST='testserver').post(url, dict(datos, nombre='Otro Nombre', documento='100003', grado='10'))
        self.assertContains(r, 'sus 2 cupo(s)')
        # Pendiente: no juega aunque se active el evento
        org.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'activar'})
        self.assertContains(uno.get(f'/aula/eventos/{ev.pk}/'), 'Inscripción recibida')
        r = uno.post(f'/aula/eventos/{ev.pk}/registro/', json.dumps({'eventos': [{'seq': 1, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 0, 't': 9}]}),
                     content_type='application/json').json()
        self.assertTrue(r.get('prueba'))
        # El organizador las ve y las aprueba
        r = org.get(f'/aula/eventos/{ev.pk}/inscripciones/')
        self.assertContains(r, 'María Gómez'); self.assertContains(r, '3001234567')
        self.assertContains(org.get(f'/aula/eventos/{ev.pk}/configurar/'), '2 pendientes')
        org.post(f'/aula/eventos/{ev.pk}/inscripciones/', {'accion': 'aprobar_todas'})
        self.assertEqual(ParticipacionEvento.objects.filter(evento=ev, estado='aprobada').count(), 2)
        r = uno.post(f'/aula/eventos/{ev.pk}/registro/', json.dumps({'eventos': [{'seq': 1, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 0, 't': 9}]}),
                     content_type='application/json').json()
        self.assertEqual(r['puntos'], 1)
        # Rechazar con motivo: lo ve el participante y sale del ranking
        q = ParticipacionEvento.objects.get(evento=ev, nombre='María Gómez')
        org.post(f'/aula/eventos/{ev.pk}/inscripciones/', {'accion': 'rechazar', 'pid': q.pk, 'motivo': 'Falta el permiso firmado'})
        self.assertContains(dos.get(f'/aula/eventos/{ev.pk}/'), 'Falta el permiso firmado')
        tablas = org.get(f'/aula/eventos/{ev.pk}/resultados/').context['tablas']
        self.assertEqual([p.nombre for _, _, filas in tablas for p in filas], ['Pedro Pérez'])
        # Desde otro equipo: con el documento y la clave recupera su inscripción
        otro = Client(HTTP_HOST='testserver')
        r = otro.post(url, {'accion': 'recuperar', 'documento': '100001', 'clave': p.datos['clave'].lower()})
        self.assertRedirects(r, url, fetch_redirect_response=False)
        self.assertRedirects(otro.get(url), f'/aula/eventos/{ev.pk}/', fetch_redirect_response=False)
        # Aprobar sobre el cupo solo si el organizador lo fuerza
        org.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'inscripcion', 'abierta': 'on', 'aprobacion': 'on', 'cupo_colegio': '1', 'cupo_nivel': '0'})
        org.post(f'/aula/eventos/{ev.pk}/inscripciones/', {'accion': 'aprobar', 'pid': q.pk})
        self.assertEqual(ParticipacionEvento.objects.get(pk=q.pk).estado, 'rechazada')
        org.post(f'/aula/eventos/{ev.pk}/inscripciones/', {'accion': 'aprobar', 'pid': q.pk, 'forzar': '1'})
        self.assertEqual(ParticipacionEvento.objects.get(pk=q.pk).estado, 'aprobada')
        # CSV de inscripciones
        r = org.get(f'/aula/eventos/{ev.pk}/inscripciones/?estado=todas&csv=1')
        self.assertIn('Colegio San José', r.content.decode())
        # Otro usuario no ve las inscripciones
        self.assertEqual(Client(HTTP_HOST='testserver').get(f'/aula/eventos/{ev.pk}/inscripciones/').status_code, 302)

    def test_ranking_en_vivo_diplomas_y_correo(self):
        from django.core import mail
        from django.test import Client
        ev = self.crear('Olimpiada 2026')
        self.admin.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'activar'})
        ana = self.cliente(self.ana.user)
        ana.get(f'/aula/eventos/{ev.pk}/')
        r = self.post(ana, f'/aula/eventos/{ev.pk}/registro/', {'eventos': [{'seq': 1, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 0, 't': 9}]})
        self.assertEqual(r['puntos'], 1)
        # Ranking en vivo (para proyectar): página y datos que se actualizan solos
        self.assertContains(self.admin.get(f'/aula/eventos/{ev.pk}/en-vivo/'), 'Olimpiada 2026')
        j = self.admin.get(f'/aula/eventos/{ev.pk}/en-vivo/?json=1').json()
        self.assertIn('Ana Prueba', [f['nombre'] for t in j['tablas'] for f in t['filas']])
        self.assertEqual(ana.get(f'/aula/eventos/{ev.pk}/en-vivo/').status_code, 403)
        # Diplomas: primeros puestos (con puntos) y de participación
        r = self.admin.get(f'/aula/eventos/{ev.pk}/diplomas/?firmante=Rosa+Díaz&cargo=Rectora')
        self.assertContains(r, 'Primer puesto'); self.assertContains(r, 'Ana Prueba'); self.assertContains(r, 'Rectora')
        self.assertContains(self.admin.get(f'/aula/eventos/{ev.pk}/diplomas/?tipo=todos'), 'CERTIFICADO DE PARTICIPACIÓN')
        # Correo al aprobar la inscripción de alguien de fuera (si dejó un correo)
        self.admin.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'alcance', 'alcance': 'codigo'})
        self.admin.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'inscripcion', 'abierta': 'on', 'aprobacion': 'on'})
        ev.refresh_from_db()
        Client(HTTP_HOST='testserver').post(f'/aula/eventos/c/{ev.codigo}/', {
            'nombre': 'Pedro Pérez', 'institucion': 'Colegio Otro', 'ciudad': 'Neiva', 'grado': '7', 'documento': '100009',
            'contacto': 'familia@correo.co', 'acudiente': 'Rosa Pérez', 'autoriza': 'on'})
        p = ParticipacionEvento.objects.get(evento=ev, nombre='Pedro Pérez')
        mail.outbox = []
        self.admin.post(f'/aula/eventos/{ev.pk}/inscripciones/', {'accion': 'aprobar', 'pid': p.pk})
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('APROBADA', mail.outbox[0].body); self.assertIn(p.datos['clave'], mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].to, ['familia@correo.co'])

    def test_boton_actualizar(self):
        """Si a alguien se le queda pegada la olimpiada, «Actualizar» guarda, recarga y sigue donde iba."""
        ev = self.crear('Olimpiada')
        self.admin.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'activar'})
        r = self.cliente(self.ana.user).get(f'/aula/eventos/{ev.pk}/')
        self.assertContains(r, 'id="ol-actualizar"')
        self.assertContains(r, 'id="ol-atascado"')

    def test_vigilancia_camara_y_microfono(self):
        """El organizador exige cámara y micrófono: los trozos se guardan privados, solo los ven los organizadores
        y se borran solos a los días configurados."""
        import os
        from datetime import timedelta
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.core.management import call_command
        from django.utils import timezone
        from aula.models import GrabacionEvento
        ev = self.crear('Olimpiada vigilada')
        url_conf = f'/aula/eventos/{ev.pk}/configurar/'
        # Sin confirmar la autorización de los acudientes no se activa
        self.admin.post(url_conf, {'accion': 'vigilancia', 'activa': 'on', 'dias': '15'})
        ev.refresh_from_db(); self.assertFalse((ev.config.get('vigilancia') or {}).get('activa'))
        self.admin.post(url_conf, {'accion': 'vigilancia', 'activa': 'on', 'acepto_legal': 'on', 'dias': '15'})
        self.admin.post(url_conf, {'accion': 'activar'})
        ev.refresh_from_db(); self.assertEqual(ev.config['vigilancia'], {'activa': True, 'dias': 15})
        ana = self.cliente(self.ana.user)
        r = ana.get(f'/aula/eventos/{ev.pk}/')
        self.assertEqual(r.context['datos']['vigilancia'], {'activa': True, 'dias': 15})
        self.assertContains(r, '/grabacion/')
        url = f'/aula/eventos/{ev.pk}/grabacion/'
        self.assertTrue(ana.post(url, {'tipo': 'acepto'}).json()['ok'])
        trozo = lambda n: SimpleUploadedFile(f't{n}.webm', b'\x1aE\xdf\xa3' + b'0' * 2000, content_type='video/webm')
        self.assertTrue(ana.post(url, {'trozo': trozo(1), 'n': 1, 't': 0}).json()['ok'])
        self.assertTrue(ana.post(url, {'trozo': trozo(2), 'n': 2, 't': 30}).json()['ok'])
        ana.post(url, {'tipo': 'corte', 't': 45, 'motivo': 'se apagó la cámara'})
        ana.post(url, {'tipo': 'reanudo', 't': 60})
        # Lo que no es video no se guarda
        self.assertEqual(ana.post(url, {'trozo': SimpleUploadedFile('x.txt', b'hola', content_type='text/plain')}).status_code, 400)
        p = ParticipacionEvento.objects.get(evento=ev, estudiante=self.ana)
        self.assertEqual(p.grabaciones.count(), 2)
        self.assertTrue(p.datos['vigilancia']['acepto'])
        self.assertEqual([c['tipo'] for c in p.datos['vigilancia']['cortes']], ['corte', 'reanudo'])
        # El organizador la ve; los demás no
        r = self.admin.get(f'/aula/eventos/{ev.pk}/grabaciones/{p.pk}/')
        self.assertContains(r, 'se apagó la cámara'); self.assertEqual(len(r.context['trozos']), 2)
        g = p.grabaciones.first()
        self.assertEqual(self.admin.get(f'/aula/eventos/{ev.pk}/grabaciones/archivo/{g.pk}/').status_code, 302)
        self.assertEqual(ana.get(f'/aula/eventos/{ev.pk}/grabaciones/archivo/{g.pk}/').status_code, 403)
        self.assertEqual(ana.get(f'/aula/eventos/{ev.pk}/grabaciones/{p.pk}/').status_code, 403)
        self.assertContains(self.admin.get(f'/aula/eventos/{ev.pk}/resultados/'), '🎥 2')
        # Pasados los días de guarda se borran solas (con su archivo)
        ruta = g.archivo.path
        self.assertTrue(os.path.exists(ruta))
        GrabacionEvento.objects.filter(pk=g.pk).update(creada=timezone.now() - timedelta(days=16))
        call_command('limpiar_grabaciones_eventos', stdout=open(os.devnull, 'w'))
        self.assertEqual(p.grabaciones.count(), 1)
        self.assertFalse(os.path.exists(ruta))
        # Borrar todas y apagar la vigilancia
        self.admin.post(url_conf, {'accion': 'borrar_grabaciones'})
        self.assertEqual(GrabacionEvento.objects.count(), 0)
        self.admin.post(url_conf, {'accion': 'vigilancia', 'dias': '15'})
        self.assertEqual(ana.post(url, {'tipo': 'acepto'}).status_code, 400)

    def test_grabaciones_a_mi_nube(self):
        """El organizador copia las grabaciones a su Drive u OneDrive (lo hace su navegador) y puede borrarlas del servidor."""
        import zipfile, io
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        from aula.models import GrabacionEvento
        ev = self.crear('Olimpiada vigilada')
        self.admin.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'vigilancia', 'activa': 'on', 'acepto_legal': 'on', 'dias': '30'})
        self.admin.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'activar'})
        ana = self.cliente(self.ana.user)
        ana.get(f'/aula/eventos/{ev.pk}/')
        for n in (1, 2):
            ana.post(f'/aula/eventos/{ev.pk}/grabacion/', {'trozo': SimpleUploadedFile(f't{n}.webm', b'VIDEO%d' % n, content_type='video/webm'), 'n': n})
        p = ParticipacionEvento.objects.get(evento=ev, estudiante=self.ana)
        url = f'/aula/eventos/{ev.pk}/grabaciones/nube/'
        d = self.admin.get(url).json()
        self.assertEqual(d['evento'], 'Olimpiada vigilada')
        trozos = d['personas'][0]['trozos']
        self.assertEqual(len(trozos), 2); self.assertTrue(trozos[0]['archivo'].endswith('.webm'))
        # Los bytes salen del mismo sitio (para que el navegador los suba a la nube)
        r = self.admin.get(trozos[0]['url'])
        self.assertEqual(b''.join(r.streaming_content), b'VIDEO1')
        # Sin marcar en la nube no se borra nada; marcados sí
        post = lambda datos: self.admin.post(url, json.dumps(datos), content_type='application/json').json()
        self.assertEqual(post({'accion': 'borrar', 'ids': [t['id'] for t in trozos]})['n'], 0)
        self.assertEqual(post({'accion': 'marcar', 'nube': 'google', 'ids': [trozos[0]['id']]})['n'], 1)
        self.assertEqual(post({'accion': 'borrar', 'ids': [t['id'] for t in trozos]})['n'], 1)
        self.assertEqual(GrabacionEvento.objects.filter(participacion=p).count(), 1)
        # ZIP de un participante
        r = self.admin.get(f'/aula/eventos/{ev.pk}/grabaciones/{p.pk}/zip/')
        z = zipfile.ZipFile(io.BytesIO(b''.join(r.streaming_content)))
        self.assertEqual(len(z.namelist()), 1)
        # Los paneles aparecen (con Drive configurado) y nadie más entra
        with override_settings(GOOGLE_CLIENT_ID='x'):
            self.assertContains(self.admin.get(f'/aula/eventos/{ev.pk}/grabaciones/{p.pk}/'), 'data-nube="google"')
            self.assertContains(self.admin.get(f'/aula/eventos/{ev.pk}/resultados/'), 'Guardar las grabaciones del evento en mi nube')
        self.assertEqual(ana.get(url).status_code, 403)
        self.assertEqual(ana.post(url, json.dumps({'accion': 'borrar', 'ids': [1]}), content_type='application/json').status_code, 403)

    def test_planilla_de_inscripcion(self):
        """El organizador descarga la planilla, los colegios la llenan y él la sube: se crean y actualizan inscripciones."""
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import Client
        from openpyxl import load_workbook
        from aula.planilla_eventos import leer_grado
        ev = self.crear('Intercolegial 2026')
        self.admin.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'alcance', 'alcance': 'codigo'})
        self.admin.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'inscripcion', 'abierta': 'on', 'aprobacion': 'on', 'cupo_colegio': '3', 'cupo_nivel': '2'})
        ev.refresh_from_db()
        url = f'/aula/eventos/{ev.pk}/planilla/'
        r = self.admin.get(url + '?vacia=1')
        self.assertIn('spreadsheetml', r['Content-Type'])
        libro = load_workbook(io.BytesIO(r.content))
        hoja = libro['Inscripción']
        self.assertEqual(hoja['A3'].value, 'Nombre completo')
        self.assertIn('Instrucciones', libro.sheetnames)
        self.assertEqual((leer_grado('7.º'), leer_grado('Séptimo'), leer_grado(8), leer_grado('Transición'), leer_grado('x')), (7, 7, 8, 0, None))
        # Un colegio la llena
        filas = [
            ['Pedro Pérez Gómez', '1001001', 'Colegio San José', 'Ibagué', '7.º', 'familia@correo.co', 'Rosa Gómez', 'Prof. Luis', 'SÍ'],
            ['María Ruiz López', '1001002', 'Colegio San José', 'Ibagué', 'Sexto', '', 'Ana López', '', 'si'],
            ['Juan Sin Permiso', '1001003', 'Colegio San José', '', '9', '', '', '', 'NO'],          # sin autorización
            ['Luis Fuera Grado', '1001004', 'Colegio San José', '', 'Transición', '', 'Rosa', '', 'SÍ'],   # grado que no está
            ['Tercero Exploradores', '1001005', 'colegio san jose', '', '6', '', 'Carlos Ruiz', '', 'SÍ'],  # cupo de nivel (2)
            ['Pedro Repetido', '1001001', 'Colegio San José', '', '7', '', 'Rosa Gómez', '', 'SÍ'],        # repetido en la planilla
            [None] * 9,
        ]
        for f in filas:
            hoja.append(f)
        salida = io.BytesIO(); libro.save(salida)
        r = self.admin.post(url, {'archivo': SimpleUploadedFile('planilla.xlsx', salida.getvalue())}, follow=True)
        self.assertContains(r, '2 inscripción(es) nueva(s)')
        errores = '\n'.join(m for _, m in r.context['errores_planilla'])
        self.assertIn('autorización', errores); self.assertIn('Transición', errores); self.assertIn('cupo', errores); self.assertIn('repetido', errores)
        ps = {p.datos['documento']: p for p in ParticipacionEvento.objects.filter(evento=ev)}
        self.assertEqual(set(ps), {'1001001', '1001002'})
        pedro = ps['1001001']
        self.assertEqual((pedro.estado, pedro.grado, pedro.ciclo, pedro.datos['autorizacion']['origen']), ('pendiente', 7, 'exploradores', 'planilla'))
        # Con «aprobar de una vez», y al subirla de nuevo se actualiza (no se repite)
        libro = load_workbook(io.BytesIO(self.admin.get(url).content))
        hoja = libro['Inscripción']
        fila = next(r for r in range(4, hoja.max_row + 1) if hoja.cell(r, 2).value == '1001001')
        self.assertEqual(hoja.cell(fila, 11).value, pedro.datos['clave'])          # la clave sale en la planilla
        hoja.cell(fila, 4).value = 'Espinal'
        salida = io.BytesIO(); libro.save(salida)
        r = self.admin.post(url, {'archivo': SimpleUploadedFile('planilla.xlsx', salida.getvalue()), 'aprobar': 'on'}, follow=True)
        self.assertContains(r, 'actualizada(s)')
        pedro.refresh_from_db()
        self.assertEqual((pedro.datos['ciudad'], ParticipacionEvento.objects.filter(evento=ev).count()), ('Espinal', 2))
        # CSV también sirve
        csv_txt = 'Nombre completo;Número de documento;Colegio o institución;Grado;Acudiente (o docente) que autoriza los datos;Autoriza datos (SÍ)\nCamila Torres Díaz;2002001;Liceo Nacional;10;Marta Díaz;SÍ\n'
        self.admin.post(url, {'archivo': SimpleUploadedFile('p.csv', csv_txt.encode('utf-8'), content_type='text/csv'), 'aprobar': 'on'})
        camila = ParticipacionEvento.objects.get(evento=ev, datos__documento='2002001')
        self.assertEqual((camila.estado, camila.ciclo), ('aprobada', 'expertos'))
        # El estudiante entra con su documento y la clave de la planilla
        c = Client(HTTP_HOST='testserver')
        r = c.post(f'/aula/eventos/c/{ev.codigo}/', {'accion': 'recuperar', 'documento': '2002001', 'clave': camila.datos['clave']})
        self.assertRedirects(r, f'/aula/eventos/c/{ev.codigo}/', fetch_redirect_response=False)
        # Un archivo cualquiera no rompe nada; y nadie más la descarga
        r = self.admin.post(url, {'archivo': SimpleUploadedFile('x.xlsx', b'basura')}, follow=True)
        self.assertContains(r, 'No se pudo leer')
        self.assertEqual(self.cliente(self.ana.user).get(url).status_code, 403)
