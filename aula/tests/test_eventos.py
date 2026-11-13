"""Eventos: la olimpiada de matemáticas (apagada hasta que el organizador la activa; el servidor cuenta)."""
import json

from django.contrib.auth.models import User

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
        # Inscripciones sin habilitar: no se puede inscribir
        anon = Client(HTTP_HOST='testserver')
        pedro = {'nombre': 'Pedro Pérez', 'institucion': 'Colegio Otro', 'grado': '7', 'documento': '1.000.123', 'autoriza': 'on'}
        r = anon.post(f'/aula/eventos/c/{ev.codigo}/', pedro)
        self.assertFalse(ParticipacionEvento.objects.exists())
        self.assertContains(docente.get(f'/aula/eventos/{ev.pk}/configurar/'), 'Habilitar inscripciones')
        docente.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'inscripciones_abrir', 'abrir': '1'})
        # Sin documento no se inscribe
        self.assertContains(anon.post(f'/aula/eventos/c/{ev.codigo}/', dict(pedro, documento='')), 'número de documento')
        docente.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'activar'})
        # Entra con el código, sin cuenta
        r = anon.post('/aula/eventos/entrar/', {'codigo': ev.codigo.lower()})
        self.assertRedirects(r, f'/aula/eventos/c/{ev.codigo}/', fetch_redirect_response=False)
        r = anon.post(f'/aula/eventos/c/{ev.codigo}/', pedro)
        self.assertRedirects(r, f'/aula/eventos/c/{ev.codigo}/', fetch_redirect_response=False)
        p = ParticipacionEvento.objects.get(evento=ev)
        # Le mostramos su código de seguridad una vez; después entra directo a la prueba
        r = anon.get(f'/aula/eventos/c/{ev.codigo}/')
        self.assertContains(r, p.datos['clave']); self.assertContains(r, 'Entrar a la prueba')
        self.assertRedirects(anon.get(f'/aula/eventos/c/{ev.codigo}/'), f'/aula/eventos/{ev.pk}/', fetch_redirect_response=False)
        # El mismo documento (escrito distinto) no se inscribe dos veces
        otro = Client(HTTP_HOST='testserver')
        self.assertContains(otro.post(f'/aula/eventos/c/{ev.codigo}/', dict(pedro, nombre='Pedro Otro', documento='1000123')), 'ya está inscrito')
        self.assertEqual(ParticipacionEvento.objects.filter(evento=ev).count(), 1)
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
        org.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'inscripciones_abrir', 'abrir': '1'})
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
        self.assertContains(r, 'Ese documento ya está inscrito')
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
        org.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'inscripciones_abrir', 'abrir': '1'})
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
        self.admin.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'inscripciones_abrir', 'abrir': '1'})
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
        # Sin ninguna forma de supervisar tampoco
        self.admin.post(url_conf, {'accion': 'vigilancia', 'activa': 'on', 'acepto_legal': 'on', 'dias': '15'})
        ev.refresh_from_db(); self.assertFalse((ev.config.get('vigilancia') or {}).get('activa'))
        self.admin.post(url_conf, {'accion': 'vigilancia', 'activa': 'on', 'acepto_legal': 'on', 'dias': '15', 'camara': 'on'})
        self.admin.post(url_conf, {'accion': 'activar'})
        ev.refresh_from_db()
        self.assertEqual(ev.config['vigilancia'], {'activa': True, 'dias': 15, 'guardar': 'video', 'camara': True, 'juego': False, 'pantalla': False, 'salidas': False})
        ana = self.cliente(self.ana.user)
        r = ana.get(f'/aula/eventos/{ev.pk}/')
        d = r.context['datos']['vigilancia']
        self.assertTrue(d['graba']); self.assertIn('cámara y el micrófono', d['texto']); self.assertNotIn('pantalla', d['texto'])
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

    def test_supervision_pantalla_y_registro_de_salidas(self):
        """Pantalla + juego + registro de salidas: las condiciones lo dicen, las salidas se anotan con su duración
        y las ven el organizador y los veedores (en la tabla y en el CSV)."""
        ev = self.crear('Olimpiada supervisada')
        url_conf = f'/aula/eventos/{ev.pk}/configurar/'
        self.admin.post(url_conf, {'accion': 'vigilancia', 'activa': 'on', 'acepto_legal': 'on', 'dias': '20',
                                   'camara': 'on', 'juego': 'on', 'pantalla': 'on', 'salidas': 'on'})
        self.admin.post(url_conf, {'accion': 'activar'})
        r = self.admin.get(url_conf)
        self.assertContains(r, 'Supervisión de la prueba'); self.assertContains(r, 'Recomendado')
        self.assertContains(r, 'se graba la pantalla'); self.assertContains(r, 'sale de la prueba')
        ana = self.cliente(self.ana.user)
        d = ana.get(f'/aula/eventos/{ev.pk}/').context['datos']['vigilancia']
        self.assertTrue(d['pantalla'] and d['salidas'] and d['graba'])
        self.assertIn('no se salga de la prueba', d['texto']); self.assertIn('registro de cada vez que el estudiante sale', d['texto'])
        self.post(ana, f'/aula/eventos/{ev.pk}/registro/', {'eventos': [{'seq': 1, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 0, 't': 9}]})
        url = f'/aula/eventos/{ev.pk}/grabacion/'
        ana.post(url, {'tipo': 'sale', 't': 100, 'motivo': 'cambió de pestaña o de aplicación'})
        ana.post(url, {'tipo': 'vuelve', 't': 100, 'seg': '12.4'})
        ana.post(url, {'tipo': 'sale', 't': 300, 'motivo': 'cambió de ventana'})
        ana.post(url, {'tipo': 'vuelve', 't': 300, 'seg': '30'})
        p = ParticipacionEvento.objects.get(evento=ev, estudiante=self.ana)
        sal = p.datos['vigilancia']['salidas']
        self.assertEqual([x['seg'] for x in sal], [12.4, 30.0]); self.assertEqual(sal[1]['motivo'], 'cambió de ventana')
        r = self.admin.get(f'/aula/eventos/{ev.pk}/resultados/')
        self.assertContains(r, 'salió 2 veces'); self.assertContains(r, '42 s fuera')
        self.assertIn('Salidas de la prueba', self.admin.get(f'/aula/eventos/{ev.pk}/resultados/?csv=1').content.decode())
        r = self.admin.get(f'/aula/eventos/{ev.pk}/grabaciones/{p.pk}/')
        self.assertContains(r, 'Salió de la prueba 2 veces'); self.assertContains(r, '1:40')
        # Los veedores también ven las salidas (sin enlace a los videos)
        self.admin.post(url_conf, {'accion': 'veedor', 'nombre': 'Prof. Veedor', 'correo': 'veedor@ejemplo.com'})
        ev.refresh_from_db()
        vs = ev.config.get('veedores') or []
        self.assertTrue(vs)
        r = self.client.get(f'/aula/eventos/v/{vs[0]["token"]}/')
        self.assertContains(r, 'salió 2 veces'); self.assertNotContains(r, '/grabaciones/')
        # Solo registro de salidas: no se aceptan videos
        self.admin.post(url_conf, {'accion': 'vigilancia', 'activa': 'on', 'acepto_legal': 'on', 'dias': '20', 'salidas': 'on'})
        from django.core.files.uploadedfile import SimpleUploadedFile
        trozo = SimpleUploadedFile('t.webm', b'\x1aE\xdf\xa3' + b'0' * 2000, content_type='video/webm')
        self.assertEqual(ana.post(url, {'trozo': trozo, 'n': 1, 't': 0}).status_code, 400)
        self.assertTrue(ana.post(url, {'tipo': 'sale', 't': 400}).json()['ok'])
        self.assertFalse(ana.get(f'/aula/eventos/{ev.pk}/').context['datos']['vigilancia']['graba'])

    def test_supervision_con_pantallazos(self):
        """Con «pantallazos» llegan imágenes (una por reto, pregunta o salida) y se ven en galería con su momento."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        ev = self.crear('Olimpiada con pantallazos')
        url_conf = f'/aula/eventos/{ev.pk}/configurar/'
        self.admin.post(url_conf, {'accion': 'vigilancia', 'activa': 'on', 'acepto_legal': 'on', 'dias': '20',
                                   'camara': 'on', 'juego': 'on', 'salidas': 'on', 'guardar': 'pantallazos'})
        self.admin.post(url_conf, {'accion': 'activar'})
        ev.refresh_from_db(); self.assertEqual(ev.config['vigilancia']['guardar'], 'pantallazos')
        self.assertContains(self.admin.get(url_conf), 'id="vig-fotos" checked')
        ana = self.cliente(self.ana.user)
        d = ana.get(f'/aula/eventos/{ev.pk}/').context['datos']['vigilancia']
        self.assertIn('pantallazos', d['texto']); self.assertNotIn('micrófono', d['texto'])
        self.post(ana, f'/aula/eventos/{ev.pk}/registro/', {'eventos': [{'seq': 1, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 0, 't': 9}]})
        url = f'/aula/eventos/{ev.pk}/grabacion/'
        jpg = lambda: SimpleUploadedFile('p.jpg', b'\xff\xd8\xff\xe0' + b'0' * 3000, content_type='image/jpeg')
        for n, (t, momento) in enumerate([(5, 'reto'), (40, 'pregunta'), (95, 'salio')], 1):
            self.assertTrue(ana.post(url, {'trozo': jpg(), 'n': n, 't': t, 'momento': momento}).json()['ok'])
        self.assertEqual(ana.post(url, {'trozo': SimpleUploadedFile('x.svg', b'<svg/>', content_type='image/svg+xml'), 'n': 9}).status_code, 400)
        p = ParticipacionEvento.objects.get(evento=ev, estudiante=self.ana)
        self.assertEqual(p.grabaciones.count(), 3)
        g = p.grabaciones.get(numero=2)
        self.assertTrue(g.archivo.name.endswith('.jpg')); self.assertEqual(g.tipo, 'image/jpeg;pregunta')
        r = self.admin.get(f'/aula/eventos/{ev.pk}/grabaciones/{p.pk}/')
        self.assertContains(r, 'Pantallazos (3)'); self.assertContains(r, 'salió de la prueba'); self.assertContains(r, 'min 1:35')
        self.assertNotContains(r, 'id="gr-video"')

    def test_grabaciones_a_mi_nube(self):
        """El organizador copia las grabaciones a su Drive u OneDrive (lo hace su navegador) y puede borrarlas del servidor."""
        import zipfile, io
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings
        from aula.models import GrabacionEvento
        ev = self.crear('Olimpiada vigilada')
        self.admin.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'vigilancia', 'activa': 'on', 'acepto_legal': 'on', 'dias': '30', 'camara': 'on'})
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
        self.admin.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'inscripciones_abrir', 'abrir': '1'})
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

    def test_preguntas_por_grado_planilla_y_banco_611(self):
        """Olimpiada 6.º–11.º: banco de 240 preguntas, planilla de Excel de preguntas y preguntas por grado."""
        import io
        from django.core.files.uploadedfile import SimpleUploadedFile
        from openpyxl import load_workbook
        from aula import planilla_preguntas
        banco = planilla_preguntas.banco_olimpiada()
        self.assertEqual(len(banco), 240)
        for g in range(6, 12):
            del_grado = [p for p in banco if p['grado'] == g]
            self.assertEqual(len(del_grado), 40)
            self.assertEqual({p['categoria'] for p in del_grado}, {'euclides', 'newton', 'bernoulli'})
        for p in banco:      # cada una: 4 opciones distintas y una sola correcta
            textos = [o['texto'] for o in p['opciones']]
            self.assertEqual((len(textos), len(set(textos)), sum(o['correcta'] for o in p['opciones'])), (4, 4, 1), p['texto'])
        ev = self.crear('Primera Olimpiada Matemática Zona Norte del Tolima')
        conf = f'/aula/eventos/{ev.pk}/configurar/'
        # Cargar el banco: cada pregunta al grupo de su grado
        self.admin.post(conf, {'accion': 'banco_611'})
        ev.refresh_from_db()
        n611 = [x for x in ev.preguntas if x.get('origen') == 'Banco olimpiada 6.º–11.º']
        ya_estaban = {(x['ciclo'], x['texto']) for x in ev.preguntas if x.get('origen') != 'Banco olimpiada 6.º–11.º'}
        self.assertEqual(len(n611), 240 - sum(1 for p in banco if (p['ciclo'], p['texto']) in ya_estaban))
        self.assertGreater(len(n611), 230)
        self.assertTrue(all(x['ciclo'] == {6: 'exploradores', 7: 'exploradores', 8: 'investigadores', 9: 'investigadores'}.get(x['grado'], 'expertos') for x in n611))
        self.admin.post(conf, {'accion': 'banco_611'})          # no se repiten
        ev.refresh_from_db(); self.assertEqual(len([x for x in ev.preguntas if x.get('origen') == 'Banco olimpiada 6.º–11.º']), len(n611))
        # Planilla: descargar las del evento y subir una propia (nivel por nombre o por grado)
        r = self.admin.get(f'/aula/eventos/{ev.pk}/preguntas/planilla/')
        hoja = load_workbook(io.BytesIO(r.content))['Preguntas']
        self.assertEqual([c.value for c in hoja[1]][:5], ['Grado', 'Nivel', 'Pensamiento', 'Tema', 'Pregunta'])
        self.assertGreaterEqual(hoja.max_row, len(n611) + 1)
        libro = load_workbook(io.BytesIO(self.admin.get(f'/aula/eventos/{ev.pk}/preguntas/planilla/?de=vacia').content))
        h = libro['Preguntas']
        h.append(['7.º', '', 'Euclides', 'Ángulos', '¿Cuánto suman los ángulos de un cuadrilátero?', '180°', '360°', '270°', '', '', '', '', '', 'B'])
        h.append(['', 'Expertos', 'Newton', '', '¿Cuánto es 2^10?', '1024', '512', '', '', '', '', '', '', 'A'])
        h.append(['8', '', '', '', 'Sin respuesta marcada', 'a', 'b', '', '', '', '', '', '', 'Z'])
        out = io.BytesIO(); libro.save(out)
        r = self.admin.post(f'/aula/eventos/{ev.pk}/preguntas/planilla/', {'archivo': SimpleUploadedFile('p.xlsx', out.getvalue()), 'ciclo': 'exploradores', 'categoria': 'newton'}, follow=True)
        self.assertContains(r, 'Se agregaron 2 pregunta(s)'); self.assertContains(r, '1 fila(s) con problemas')
        ev.refresh_from_db()
        cuadri = next(x for x in ev.preguntas if 'cuadrilátero' in x['texto'])
        self.assertEqual((cuadri['ciclo'], cuadri['categoria'], cuadri['grado']), ('exploradores', 'euclides', 7))
        self.assertEqual(next(x for x in ev.preguntas if '2^10' in x['texto'])['ciclo'], 'expertos')
        # La pregunta de competencia de Ana (7.º) es de su grado
        self.admin.post(conf, {'accion': 'activar'})
        ana = self.cliente(self.ana.user)
        self.post(ana, f'/aula/eventos/{ev.pk}/registro/', {'eventos': [{'seq': 1, 'tipo': 'inicio'}]})
        p = ParticipacionEvento.objects.get(evento=ev, estudiante=self.ana)
        grado = int(self.ana.curso.grado)
        p.puntos, p.preguntas_hechas = 5, 0
        p.save()
        q = ana.get(f'/aula/eventos/{ev.pk}/pregunta/').json()['pregunta']
        x = next(x for x in ev.preguntas if x['texto'] == q['texto'])
        self.assertIn(x.get('grado'), (grado, None))
        # Retos arcade con el banco del grado (sin las preguntas de competencia)
        self.admin.post(conf, {'accion': 'arcade', 'arcade': 'operaciones'})
        d = ana.get(f'/aula/eventos/{ev.pk}/').context['datos']
        self.assertIsNone(d['arcade_preguntas'])
        self.admin.post(conf, {'accion': 'arcade', 'arcade': 'banco'})
        d = ana.get(f'/aula/eventos/{ev.pk}/').context['datos']
        competencia = {x['texto'] for x in ev.preguntas}
        self.assertFalse(any(q['texto'] in competencia for q in d['arcade_preguntas']))      # nunca las de competencia
        ev.refresh_from_db(); ev.preguntas = [x for x in ev.preguntas if x.get('origen') != 'Banco olimpiada 6.º–11.º']; ev.save()
        d = ana.get(f'/aula/eventos/{ev.pk}/').context['datos']
        textos_grado = {p['texto'] for p in banco if p['grado'] == grado}
        self.assertTrue(d['arcade_preguntas'] and all(q['texto'] in textos_grado for q in d['arcade_preguntas']))

    def test_fechas_de_inscripcion_y_prueba(self):
        """Inscripciones hasta una fecha; la prueba solo se presenta entre las fechas del evento."""
        from datetime import timedelta
        from django.test import Client
        from django.utils import timezone
        ev = self.crear('Olimpiada Zona Norte')
        conf = f'/aula/eventos/{ev.pk}/configurar/'
        self.admin.post(conf, {'accion': 'alcance', 'alcance': 'codigo'})
        self.admin.post(conf, {'accion': 'activar'})
        self.admin.post(conf, {'accion': 'inscripciones_abrir', 'abrir': '1'})
        ev.refresh_from_db()
        f = lambda d: timezone.localtime(timezone.now() + timedelta(days=d)).strftime('%Y-%m-%dT%H:%M')
        # Inscripciones cerradas (ayer) y prueba que abre mañana
        self.admin.post(conf, {'accion': 'fechas', 'inscripcion_hasta': f(-1), 'prueba_desde': f(1), 'prueba_hasta': f(3)})
        url = f'/aula/eventos/c/{ev.codigo}/'
        datos = {'nombre': 'Pedro Pérez', 'institucion': 'Colegio Otro', 'grado': '7', 'documento': '1000555', 'autoriza': 'on'}
        c = Client(HTTP_HOST='testserver')
        self.assertContains(c.post(url, datos), 'Las inscripciones cerraron')
        self.assertFalse(ParticipacionEvento.objects.filter(evento=ev).exists())
        # Se abren las inscripciones: se inscribe, pero la prueba aún no abre
        self.admin.post(conf, {'accion': 'fechas', 'inscripcion_hasta': f(1), 'prueba_desde': f(1), 'prueba_hasta': f(3)})
        c.post(url, datos)
        self.assertTrue(ParticipacionEvento.objects.filter(evento=ev).exists())
        self.assertContains(c.get(f'/aula/eventos/{ev.pk}/'), 'La prueba abre el')
        r = c.post(f'/aula/eventos/{ev.pk}/registro/', json.dumps({'eventos': [{'seq': 1, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 0, 't': 9}]}), content_type='application/json').json()
        self.assertTrue(r.get('prueba'))
        # Dentro de las fechas: se juega
        self.admin.post(conf, {'accion': 'fechas', 'inscripcion_hasta': f(-1), 'prueba_desde': f(-1), 'prueba_hasta': f(3)})
        r = c.post(f'/aula/eventos/{ev.pk}/registro/', json.dumps({'eventos': [{'seq': 1, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 0, 't': 9}]}), content_type='application/json').json()
        self.assertEqual(r['puntos'], 1)
        # Ya cerró: aviso
        self.admin.post(conf, {'accion': 'fechas', 'prueba_desde': f(-5), 'prueba_hasta': f(-2)})
        self.assertContains(c.get(f'/aula/eventos/{ev.pk}/'), 'La prueba cerró el')
        # El organizador siempre puede probar
        self.assertEqual(self.admin.get(f'/aula/eventos/{ev.pk}/').status_code, 200)

    def test_codigo_de_seguridad_y_un_equipo_a_la_vez(self):
        """Inscrito antes de que empiece: ve su código; vuelve con documento + código sin perder lo que lleva,
        y al entrar desde otro equipo el anterior queda fuera."""
        from django.test import Client
        ev = self.crear('Olimpiada con código')
        conf = f'/aula/eventos/{ev.pk}/configurar/'
        self.admin.post(conf, {'accion': 'alcance', 'alcance': 'codigo'})
        self.admin.post(conf, {'accion': 'activar'})               # apagado (crear lo deja activo o no: se fuerza abajo)
        Evento.objects.filter(pk=ev.pk).update(activo=False); ev.refresh_from_db()
        self.admin.post(conf, {'accion': 'inscripciones_abrir', 'abrir': '1'})
        url = f'/aula/eventos/c/{ev.codigo}/'
        cel = Client(HTTP_HOST='testserver')
        cel.post(url, {'nombre': 'Sara Gómez', 'institucion': 'IE Norte', 'grado': '8', 'documento': '1099888777', 'autoriza': 'on'})
        p = ParticipacionEvento.objects.get(evento=ev)
        r = cel.get(url)
        self.assertContains(r, p.datos['clave']); self.assertContains(r, 'todavía no empieza')
        self.assertRedirects(cel.get(f'/aula/eventos/{ev.pk}/'), url, fetch_redirect_response=False)   # apagado: a su inscripción
        # Se cierran las inscripciones: ella igual entra
        self.admin.post(conf, {'accion': 'inscripciones_abrir', 'abrir': '0'})
        self.admin.post(conf, {'accion': 'activar'})
        ParticipacionEvento.objects.filter(pk=p.pk).update(puntos=7)
        pc = Client(HTTP_HOST='testserver')
        self.assertContains(pc.post(url, {'accion': 'recuperar', 'documento': '1099888777', 'clave': 'XXXXXX'}), 'código de seguridad')
        r = pc.post(url, {'accion': 'recuperar', 'documento': '1.099.888.777', 'clave': p.datos['clave'].lower()})
        self.assertRedirects(r, url, fetch_redirect_response=False)
        self.assertRedirects(pc.get(url), f'/aula/eventos/{ev.pk}/', fetch_redirect_response=False)
        p.refresh_from_db(); self.assertEqual(p.puntos, 7)                                          # no perdió nada
        self.assertEqual(pc.get(f'/aula/eventos/{ev.pk}/').status_code, 200)
        # El celular quedó fuera: vuelve a la página para entrar con documento y código
        self.assertRedirects(cel.get(f'/aula/eventos/{ev.pk}/'), url, fetch_redirect_response=False)

    def test_programar_inicio(self):
        """El organizador programa la hora de inicio: el evento se activa solo a esa hora."""
        from datetime import timedelta
        from django.utils import timezone
        from aula.models import Evento
        ev = self.crear('Olimpiada programada')
        conf = f'/aula/eventos/{ev.pk}/configurar/'
        f = lambda m: timezone.localtime(timezone.now() + timedelta(minutes=m)).strftime('%Y-%m-%dT%H:%M')
        self.assertContains(self.admin.get(conf), 'Programar inicio')
        # Una hora pasada no se acepta
        self.admin.post(conf, {'accion': 'programar', 'activar_en': f(-60)})
        ev.refresh_from_db(); self.assertFalse(ev.config.get('activar_en'))
        # Para mañana: queda PROGRAMADO y apagado
        self.admin.post(conf, {'accion': 'programar', 'activar_en': f(24 * 60)})
        ev.refresh_from_db(); self.assertFalse(ev.activo); self.assertTrue(ev.config['activar_en'])
        self.assertContains(self.admin.get(conf), 'PROGRAMADO')
        self.assertContains(self.admin.get('/aula/eventos/'), 'PROGRAMADO')
        # Quitar lo programado
        self.admin.post(conf, {'accion': 'programar', 'cancelar': '1'})
        ev.refresh_from_db(); self.assertFalse(ev.config['activar_en'])
        # Llega la hora (se simula guardándola en el pasado): al entrar alguien, el evento ya está activo
        Evento.objects.filter(pk=ev.pk).update(config=dict(ev.config, activar_en=f(-1)))
        self.admin.get('/aula/eventos/')
        ev.refresh_from_db(); self.assertTrue(ev.activo); self.assertFalse(ev.config['activar_en'])
        # Activar o apagar a mano quita lo programado
        self.admin.post(conf, {'accion': 'activar'})                       # apaga
        self.admin.post(conf, {'accion': 'programar', 'activar_en': f(120)})
        self.admin.post(conf, {'accion': 'activar'})                       # activa ya
        ev.refresh_from_db(); self.assertTrue(ev.activo); self.assertFalse(ev.config['activar_en'])

    def test_veedores_ven_resultados_en_vivo(self):
        """Profesores (o grupos) invitados ven resultados y ranking en vivo con su enlace, sin poder cambiar nada."""
        from django.core import mail
        from django.test import Client
        ev = self.crear('Olimpiada Zona Norte')
        conf = f'/aula/eventos/{ev.pk}/configurar/'
        self.admin.post(conf, {'accion': 'activar'})
        ana = self.cliente(self.ana.user)
        self.post(ana, f'/aula/eventos/{ev.pk}/registro/', {'eventos': [{'seq': 1, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 0, 't': 9}]})
        mail.outbox = []
        self.admin.post(conf, {'accion': 'veedor', 'nombre': 'Luis Pérez', 'correo': 'luis@colegio.edu.co', 'grupo': 'Jurado', 'enviar': 'on'})
        self.admin.post(conf, {'accion': 'veedores', 'grupo': 'Rectores', 'lista': 'Ana Ruiz, ana@colegio.edu.co\nMarta Gil; marta@liceo.edu.co\n\n', 'enviar': 'on'})
        self.admin.post(conf, {'accion': 'veedor_grupo', 'grupo': 'Docentes de matemáticas'})
        ev.refresh_from_db()
        vs = ev.config['veedores']
        self.assertEqual((len(vs), len(mail.outbox)), (4, 3))
        self.assertIn('/aula/eventos/v/', mail.outbox[0].body)
        self.assertEqual(sorted({v['grupo'] for v in vs}), ['Docentes de matemáticas', 'Jurado', 'Rectores'])
        r = self.admin.get(conf)
        self.assertContains(r, 'Marta Gil'); self.assertContains(r, 'Enlace del grupo')
        # El veedor (sin cuenta) ve los resultados y el ranking en vivo
        luis = Client(HTTP_HOST='testserver')
        tok = vs[0]['token']
        r = luis.get(f'/aula/eventos/v/{tok}/')
        self.assertContains(r, 'Vista de veedor'); self.assertContains(r, 'Ana Prueba')
        self.assertNotContains(r, '/configurar/'); self.assertNotContains(r, '/diplomas/')
        j = luis.get(f'/aula/eventos/v/{tok}/en-vivo/?json=1').json()
        self.assertIn('Ana Prueba', [f['nombre'] for t in j['tablas'] for f in t['filas']])
        self.assertIn('text/csv', luis.get(f'/aula/eventos/v/{tok}/?csv=1')['Content-Type'])
        # Pero no puede configurar ni ver las grabaciones o las inscripciones
        self.assertEqual(luis.get(conf).status_code, 302)
        self.assertEqual(luis.get(f'/aula/eventos/{ev.pk}/inscripciones/').status_code, 302)
        # Pausar y quitar
        self.admin.post(conf, {'accion': 'veedor_activo', 'token': tok})
        self.assertEqual(luis.get(f'/aula/eventos/v/{tok}/').status_code, 404)
        self.admin.post(conf, {'accion': 'veedor_activo', 'token': tok})
        self.assertEqual(luis.get(f'/aula/eventos/v/{tok}/').status_code, 200)
        self.admin.post(conf, {'accion': 'veedor_quitar', 'token': tok})
        self.assertEqual(luis.get(f'/aula/eventos/v/{tok}/').status_code, 404)
        self.assertEqual(luis.get('/aula/eventos/v/inventado1234567890/').status_code, 404)

    def test_inscripcion_escoge_colegio_de_la_lista_nacional(self):
        """Departamento → Municipio → Colegio con el directorio del MEN; si no está, se escribe el nombre."""
        from django.test import Client
        from salon_digital.models import Cuenta
        from aula import colegios_dane as CD
        u = User.objects.create_user('lina', password='x', first_name='Lina')
        Cuenta.objects.create(usuario=u, slug='lina', nombre_publico='Lina', municipio_dane='73411')
        docente = Client(HTTP_HOST='testserver'); docente.force_login(u)
        docente.post('/aula/eventos/', {'titulo': 'Olimpiada del norte'})
        ev = Evento.objects.get(titulo='Olimpiada del norte')
        docente.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'inscripciones_abrir', 'abrir': '1'})
        anon = Client(HTTP_HOST='testserver')
        r = anon.get(f'/aula/eventos/c/{ev.codigo}/')
        self.assertContains(r, 'Departamento'); self.assertContains(r, '>Tolima<')
        self.assertContains(r, 'data-mun="73411"')                     # arranca en el municipio del organizador
        # La lista de colegios del municipio (pública, también en el subdominio de un colegio sin Mi Salón)
        lista = Client(HTTP_HOST='b.localhost').get('/aula/eventos/colegios/?mun=73411').json()['colegios']
        self.assertGreater(len(lista), 10)
        isidro = next(c for c in lista if 'ISIDRO PARRA' in c['nombre'])
        self.assertTrue(isidro['oficial'])
        self.assertEqual(CD.buscar(isidro['dane'])['municipio'], '73411')
        # Buscar por palabras (sin tildes ni mayúsculas), en todo el país o en el municipio; también por código DANE
        b = lambda q, mun='': anon.get('/aula/eventos/colegios/', {'q': q, 'mun': mun}).json()['colegios']
        r = b('isidro PARRA')
        self.assertEqual([(c['dane'], c['lugar']) for c in r], [(isidro['dane'], 'Líbano, Tolima')])
        self.assertTrue(all(c['municipio'] == '73411' for c in b('institucion educativa', '73411')))
        self.assertEqual(len(b('san jose')), 30)                     # máximo 30 resultados
        self.assertEqual(b(isidro['dane'])[0]['nombre'], isidro['nombre'])
        self.assertEqual(b('x'), [])
        # Escoge el colegio: se guarda el nombre oficial, el municipio y el código DANE
        anon.post(f'/aula/eventos/c/{ev.codigo}/', {'nombre': 'Pedro Pérez', 'municipio_dane': '73411', 'colegio_dane': isidro['dane'],
                                                     'institucion': 'lo que sea', 'grado': '7', 'documento': '1000123', 'autoriza': 'on'})
        p = ParticipacionEvento.objects.get(evento=ev, datos__documento='1000123')
        self.assertEqual(p.institucion, isidro['nombre'])
        self.assertEqual((p.datos['ciudad'], p.datos['dane'], p.datos['municipio_dane']), ('Líbano, Tolima', isidro['dane'], '73411'))
        # No está en la lista: escribe el nombre
        Client(HTTP_HOST='testserver').post(f'/aula/eventos/c/{ev.codigo}/', {
            'nombre': 'Sara Gómez', 'municipio_dane': '73411', 'colegio_dane': 'otro', 'institucion': 'Escuela Rural La Plata',
            'grado': '8', 'documento': '1000456', 'autoriza': 'on'})
        p = ParticipacionEvento.objects.get(evento=ev, datos__documento='1000456')
        self.assertEqual((p.institucion, p.datos['ciudad'], p.datos['dane']), ('Escuela Rural La Plata', 'Líbano, Tolima', ''))
        # «otro» sin nombre: no se inscribe
        r = Client(HTTP_HOST='testserver').post(f'/aula/eventos/c/{ev.codigo}/', {
            'nombre': 'Juan Díaz', 'municipio_dane': '73411', 'colegio_dane': 'otro', 'institucion': '', 'grado': '8',
            'documento': '1000789', 'autoriza': 'on'})
        self.assertContains(r, 'su institución')

    def test_veedor_sin_plan_ni_modulo(self):
        """El enlace del veedor abre siempre: sin cuenta, con una cuenta sin plan y aunque el colegio no tenga
        Mi Salón Virtual (Premium) activo."""
        from django.test import Client
        from salon_digital.models import Cuenta
        ev = self.crear('Olimpiada abierta')
        conf = f'/aula/eventos/{ev.pk}/configurar/'
        self.admin.post(conf, {'accion': 'activar'})
        self.post(self.cliente(self.ana.user), f'/aula/eventos/{ev.pk}/registro/', {'eventos': [{'seq': 1, 'tipo': 'punto', 'juego': 'tangram', 'nivel': 0, 't': 9}]})
        self.admin.post(conf, {'accion': 'veedor', 'nombre': 'Rector invitado'})
        ev.refresh_from_db()
        tok = ev.config['veedores'][0]['token']
        self.a.modulos_activos = [m for m in self.a.modulos_activos if m != 'salon']
        self.a.save(update_fields=['modulos_activos'])
        gratis = User.objects.create_user('profe_gratis', password='x')
        Cuenta.objects.create(usuario=gratis, slug='gratis', nombre_publico='Gratis', estado='verificada', plan='gratis')
        for host in ('a.localhost', 'b.localhost', 'testserver'):
            for quien in (None, gratis, self.u_docente):
                c = Client(HTTP_HOST=host)
                if quien:
                    c.force_login(quien)
                r = c.get(f'/aula/eventos/v/{tok}/')
                self.assertContains(r, 'Vista de veedor', msg_prefix=f'{host} {quien}')
                self.assertContains(r, 'Ana Prueba')
                r = c.get(f'/aula/eventos/v/{tok}/en-vivo/')
                self.assertContains(r, 'vista de veedor')
                j = c.get(f'/aula/eventos/v/{tok}/en-vivo/?json=1').json()
                self.assertIn('Ana Prueba', [f['nombre'] for t in j['tablas'] for f in t['filas']])
        # El resto de Mi Salón Virtual sigue cerrado en ese colegio
        self.assertEqual(self.cliente(self.rectora).get(f'/aula/eventos/{ev.pk}/resultados/').status_code, 403)

    def test_podio_de_colegios(self):
        """De cada colegio cuenta solo su mejor estudiante de cada nivel; el colegio suma esos puntos (con el peso del nivel)."""
        from django.test import Client
        ev = self.crear('Olimpiada Zona Norte')
        conf = f'/aula/eventos/{ev.pk}/configurar/'
        self.admin.post(conf, {'accion': 'alcance', 'alcance': 'codigo'})
        self.admin.post(conf, {'accion': 'activar'})
        ev.refresh_from_db()
        def inscrito(nombre, colegio, grado, puntos, seg):
            return ParticipacionEvento.objects.create(evento=ev, nombre=nombre, institucion=colegio, grado=grado,
                                                      ciclo={6: 'exploradores', 8: 'investigadores', 10: 'expertos'}[grado],
                                                      puntos=puntos, segundos_ultimo_punto=seg, token=nombre)
        # San José: el mejor de Exploradores tiene 10 (el de 9 no cuenta) y el de Expertos 6 → 16
        inscrito('Ana Uno', 'Colegio San José', 6, 10, 600); inscrito('Beto Dos', 'colegio san jose', 6, 9, 500)
        inscrito('Caro Tres', 'Colegio San José', 10, 6, 700)
        # Liceo: un representante por nivel en los tres niveles: 7 + 5 + 4 = 16, pero con menos tiempo → gana el desempate
        inscrito('Dani Cuatro', 'Liceo Nacional', 6, 7, 300); inscrito('Eva Cinco', 'Liceo Nacional', 8, 5, 300)
        inscrito('Fede Seis', 'Liceo Nacional', 10, 4, 300)
        inscrito('Gabi Siete', 'Institución Técnica', 8, 20, 900)
        from aula.views_eventos import podio_colegios
        p = podio_colegios(ev)
        self.assertEqual([(x['colegio'], x['puntaje']) for x in p], [('Institución Técnica', 20), ('Liceo Nacional', 16), ('Colegio San José', 16)])
        sj = p[2]
        self.assertEqual(dict(sj['por_nivel'])['Exploradores']['nombre'], 'Ana Uno')        # solo el mejor del nivel
        self.assertIsNone(dict(sj['por_nivel'])['Investigadores'])
        # Peso por nivel: Expertos vale el doble
        self.admin.post(conf, {'accion': 'podio_colegios', 'activo': 'on', 'peso_exploradores': '1', 'peso_investigadores': '1', 'peso_expertos': '2'})
        ev.refresh_from_db()
        p = podio_colegios(ev)
        self.assertEqual([(x['colegio'], x['puntaje']) for x in p][:2], [('Colegio San José', 22), ('Liceo Nacional', 20)])
        # Se ve en resultados, en el CSV, en vivo y para los veedores
        r = self.admin.get(f'/aula/eventos/{ev.pk}/resultados/')
        self.assertContains(r, 'Podio de colegios'); self.assertContains(r, 'Liceo Nacional')
        self.assertIn('Colegio San José', self.admin.get(f'/aula/eventos/{ev.pk}/resultados/?csv=colegios').content.decode())
        j = self.admin.get(f'/aula/eventos/{ev.pk}/en-vivo/?json=1').json()
        self.assertEqual(j['colegios'][0]['colegio'], 'Colegio San José')
        self.admin.post(conf, {'accion': 'veedor_grupo', 'grupo': 'Rectores'})
        ev.refresh_from_db()
        r = Client(HTTP_HOST='testserver').get(f"/aula/eventos/v/{ev.config['veedores'][0]['token']}/")
        self.assertContains(r, 'Podio de colegios'); self.assertNotContains(r, 'peso_expertos')
        # Diplomas para los primeros colegios
        r = self.admin.get(f'/aula/eventos/{ev.pk}/diplomas/?tipo=colegios&n=3')
        self.assertContains(r, 'podio de colegios'); self.assertContains(r, 'Colegio San José')
        # Se puede ocultar
        self.admin.post(conf, {'accion': 'podio_colegios'})
        self.assertNotContains(self.admin.get(f'/aula/eventos/{ev.pk}/resultados/'), 'Puntaje del colegio')

    def test_preguntas_para_los_retos_de_juego(self):
        """Las preguntas se cargan para la competencia o para los retos arcade; los arcade usan las de juego del grado
        (y el banco si faltan), nunca las de competencia; y hay pausa de 30 s."""
        ev = self.crear('Olimpiada Zona Norte')
        conf = f'/aula/eventos/{ev.pk}/configurar/'
        self.admin.post(conf, {'accion': 'activar'})
        texto = '\n\n'.join(f'{k}. ¿Capital número {k}?\nA) Uno\n*B) Dos\nC) Tres' for k in range(1, 6))
        self.admin.post(conf, {'accion': 'pegar', 'ciclo': 'exploradores', 'categoria': 'newton', 'texto': texto, 'uso': 'juegos'})
        self.admin.post(conf, {'accion': 'pegar', 'ciclo': 'exploradores', 'categoria': 'euclides', 'texto': '1. ¿Pregunta de competencia?\nA) x\n*B) y', 'uso': 'competencia'})
        # La misma pregunta no puede estar en las dos
        self.admin.post(conf, {'accion': 'pegar', 'ciclo': 'exploradores', 'categoria': 'newton', 'texto': '1. ¿Pregunta de competencia?\nA) x\n*B) y', 'uso': 'juegos'})
        ev.refresh_from_db()
        juego = [x for x in ev.preguntas if x.get('uso') == 'juegos']
        self.assertEqual(len(juego), 5)
        self.assertEqual(sum(1 for x in ev.preguntas if x['texto'] == '¿Pregunta de competencia?'), 1)
        self.assertContains(self.admin.get(conf), 'Retos de juego')
        # Por defecto los arcade usan preguntas: primero las de juego del grupo, luego el banco de su grado
        ana = self.cliente(self.ana.user)
        d = ana.get(f'/aula/eventos/{ev.pk}/').context['datos']
        textos = [q['texto'] for q in d['arcade_preguntas']]
        self.assertTrue(set(x['texto'] for x in juego) <= set(textos[:5]))
        competencia = {x['texto'] for x in ev.preguntas if x.get('uso') != 'juegos'}
        self.assertFalse(competencia & set(textos))
        self.assertGreater(len(textos), 5)                     # se completan con el banco 6.º–11.º
        # «Solo las cargadas para los juegos» y «operaciones»
        self.admin.post(conf, {'accion': 'arcade', 'arcade': 'propias'})
        d = ana.get(f'/aula/eventos/{ev.pk}/').context['datos']
        self.assertEqual(sorted(q['texto'] for q in d['arcade_preguntas']), sorted(x['texto'] for x in juego))
        self.admin.post(conf, {'accion': 'arcade', 'arcade': 'operaciones'})
        self.assertIsNone(ana.get(f'/aula/eventos/{ev.pk}/').context['datos']['arcade_preguntas'])
        # Las preguntas de juego nunca salen como pregunta de competencia
        self.post(ana, f'/aula/eventos/{ev.pk}/registro/', {'eventos': [{'seq': 1, 'tipo': 'inicio'}]})
        p = ParticipacionEvento.objects.get(evento=ev, estudiante=self.ana)
        p.puntos = 5; p.save()
        for _ in range(4):
            q = ana.get(f'/aula/eventos/{ev.pk}/pregunta/').json()['pregunta']
            self.assertNotIn(q['texto'], {x['texto'] for x in juego})
        # El banco 6.º–11.º también se puede cargar para los retos de juego
        self.admin.post(conf, {'accion': 'banco_611', 'uso': 'juegos'})
        ev.refresh_from_db()
        self.assertGreater(sum(1 for x in ev.preguntas if x.get('uso') == 'juegos'), 200)
        # Botón de pausa en la olimpiada
        self.assertContains(ana.get(f'/aula/eventos/{ev.pk}/'), 'id="ol-pausa"')

    def test_administrar_preguntas(self):
        """Ver todas las preguntas; eliminar, pasar a la competencia o al arcade, una por una o varias a la vez,
        sin dañar lo que llevan los participantes."""
        ev = self.crear('Olimpiada Zona Norte')
        conf = f'/aula/eventos/{ev.pk}/configurar/'
        self.admin.post(conf, {'accion': 'activar'})
        texto = '\n\n'.join(f'{k}. ¿Pregunta {k}?\nA) no\n*B) sí' for k in range(1, 7))
        ev.refresh_from_db(); ev.preguntas = []; ev.save()
        self.admin.post(conf, {'accion': 'pegar', 'ciclo': 'exploradores', 'categoria': 'newton', 'texto': texto, 'uso': 'competencia'})
        ev.refresh_from_db()
        url = f'/aula/eventos/{ev.pk}/preguntas/'
        r = self.admin.get(url)
        self.assertContains(r, '¿Pregunta 6?'); self.assertContains(r, 'Seleccionar todas (6)')
        sel = {f['x']['texto']: f['valor'] for f in r.context['filas']}
        # Ana tiene pendiente la pregunta 5 y ya vio la 6
        self.post(self.cliente(self.ana.user), f'/aula/eventos/{ev.pk}/registro/', {'eventos': [{'seq': 1, 'tipo': 'inicio'}]})
        p = ParticipacionEvento.objects.get(evento=ev, estudiante=self.ana)
        p.pendiente, p.vistas = {'i': 4, 'orden': [0, 1], 'categoria': 'newton'}, [5]
        p.save()
        # Una sola (menú ⋮): pasar la 1 al arcade
        self.admin.post(url, {'accion': 'juegos', 'sel': [sel['¿Pregunta 1?']]})
        ev.refresh_from_db()
        self.assertEqual(ev.preguntas[0].get('uso'), 'juegos')
        # Varias: eliminar la 2 y la 3 → la pendiente (5) y la vista (6) se corren de lugar
        self.admin.post(url, {'accion': 'eliminar', 'sel': [sel['¿Pregunta 2?'], sel['¿Pregunta 3?']]})
        ev.refresh_from_db(); p.refresh_from_db()
        self.assertEqual([x['texto'] for x in ev.preguntas], ['¿Pregunta 1?', '¿Pregunta 4?', '¿Pregunta 5?', '¿Pregunta 6?'])
        self.assertEqual(ev.preguntas[p.pendiente['i']]['texto'], '¿Pregunta 5?')
        self.assertEqual([ev.preguntas[i]['texto'] for i in p.vistas], ['¿Pregunta 6?'])
        # Pasar al arcade la que Ana tiene pendiente: se le quita (le saldrá otra)
        sel = {f['x']['texto']: f['valor'] for f in self.admin.get(url).context['filas']}
        self.admin.post(url, {'accion': 'juegos', 'sel': [sel['¿Pregunta 5?'], sel['¿Pregunta 4?']]})
        p.refresh_from_db(); self.assertEqual(p.pendiente, {})
        # Volver a la competencia varias; filtros
        self.admin.post(url, {'accion': 'competencia', 'sel': [sel['¿Pregunta 4?']]})
        ev.refresh_from_db()
        self.assertEqual(sorted(x['texto'] for x in ev.preguntas if x.get('uso') == 'juegos'), ['¿Pregunta 1?', '¿Pregunta 5?'])
        self.assertEqual(len(self.admin.get(url + '?uso=juegos').context['filas']), 2)
        self.assertEqual(len(self.admin.get(url + '?q=pregunta 6').context['filas']), 1)
        # Si la lista cambió (marca vieja), no toca otra pregunta
        self.admin.post(url, {'accion': 'eliminar', 'sel': ['0:marcavieja']})
        ev.refresh_from_db(); self.assertEqual(len(ev.preguntas), 4)
        # Solo organizadores
        self.assertEqual(self.cliente(self.ana.user).get(url).status_code, 403)
        self.assertContains(self.admin.get(conf), 'Ver y administrar todas')


def _test_banco_calculo(self):
        """Banco de 10.º y 11.º (funciones, límites, derivadas; sin integrales) en juegos, banco del docente y eventos."""
        from aula import bancos_juegos, planilla_preguntas
        from aula.models import PreguntaBanco
        todas = planilla_preguntas.banco_calculo()
        self.assertGreaterEqual(len(todas), 120)
        self.assertFalse([p for p in todas if 'integral' in p['texto'].lower() or '∫' in p['texto']])
        self.assertTrue(all(sum(o['correcta'] for o in p['opciones']) == 1 and len(p['opciones']) == 4 for p in todas))
        once = bancos_juegos.preguntas('calculo11', 10)
        self.assertEqual(len(once), 10)
        textos11 = {p['texto'] for p in todas if p['grado'] == 11}
        self.assertTrue(all(p['texto'] in textos11 for p in once))
        self.assertIn('calculo10', bancos_juegos.BANCOS)
        # Al banco del docente, con su grado y tema
        self.admin.post('/aula/banco/', {'accion': 'calculo'})
        self.assertEqual(PreguntaBanco.objects.filter(tema__startswith='Cálculo 11.º').count(), len(textos11))
        self.assertTrue(PreguntaBanco.objects.filter(tema='Cálculo 11.º · Derivadas', grado=11).exists())
        # Planilla de Excel
        r = self.admin.get('/aula/banco/planilla/?de=calculo')
        self.assertEqual(r.status_code, 200); self.assertIn('banco 10 y 11', r['Content-Disposition'])
        # A un evento
        ev = self.crear('Olimpiada de cálculo')
        self.admin.post(f'/aula/eventos/{ev.pk}/configurar/', {'accion': 'banco_calculo', 'uso': 'competencia'})
        ev.refresh_from_db()
        self.assertTrue(any('lím (x→2)' in p['texto'] for p in ev.preguntas))


Olimpiada.test_banco_calculo = _test_banco_calculo

def _test_corregir_datos(self):
    """Los muchachos escriben mal el colegio: el organizador corrige los datos de una inscripción o unifica varias."""
    ev = self.crear('Intercolegial')
    ev.config = dict(ev.config or {}, inscripcion={'abierta': True, 'aprobacion': True, 'cupo_colegio': 0, 'cupo_nivel': 0})
    ev.save(update_fields=['config'])
    nueva = lambda nombre, inst, doc, grado=7: ParticipacionEvento.objects.create(
        evento=ev, nombre=nombre, institucion=inst, grado=grado, ciclo='exploradores' if grado <= 7 else 'avanzados',
        token=nombre, estado='aprobada', datos={'documento': doc, 'ciudad': 'Ibague'})
    a = nueva('Pedro Perez', 'Col San Jose', '100001')
    b = nueva('María Gómez', 'colegio sanjose', '100002')
    c = nueva('Luis Mora', 'Colegio San José', '100003')
    url = f'/aula/eventos/{ev.pk}/inscripciones/'
    r = self.admin.get(url + '?estado=todas')
    self.assertContains(r, 'id="ed-%d"' % a.pk); self.assertContains(r, 'Unificar o corregir instituciones')
    self.admin.post(url, {'accion': 'editar', 'pid': a.pk, 'nombre': 'Pedro  Pérez', 'documento': '1.000.01', 'institucion': 'Colegio San José',
                          'ciudad': 'Ibagué', 'grado': '7', 'contacto': '3001234567', 'acompanante': 'Prof. Rosa'})
    a.refresh_from_db()
    self.assertEqual((a.nombre, a.institucion, a.datos['documento'], a.datos['ciudad'], a.datos['acompanante']),
                     ('Pedro Pérez', 'Colegio San José', '100001', 'Ibagué', 'Prof. Rosa'))
    # No se puede poner el documento de otro ni dejar el nombre vacío
    self.admin.post(url, {'accion': 'editar', 'pid': a.pk, 'nombre': 'Pedro Pérez', 'documento': '100002', 'institucion': 'X', 'grado': '7'})
    self.admin.post(url, {'accion': 'editar', 'pid': a.pk, 'nombre': '', 'documento': '100001', 'institucion': 'X', 'grado': '7'})
    a.refresh_from_db(); self.assertEqual(a.institucion, 'Colegio San José')
    # Unificar: «colegio sanjose» pasa a llamarse como los demás
    self.admin.post(url, {'accion': 'unificar', 'viejo': ['colegio sanjose', 'Colegio San José'], 'nuevo': 'I.E. Colegio San José'})
    self.assertEqual(set(ParticipacionEvento.objects.filter(evento=ev).values_list('institucion', flat=True)), {'I.E. Colegio San José'})
    # Unificar escogiendo de la lista oficial: queda el nombre oficial con su código DANE y su municipio
    self.assertContains(self.admin.get(url + '?estado=todas'), 'lista oficial de colegios')
    self.admin.post(url, {'accion': 'unificar', 'viejo': ['I.E. Colegio San José'], 'nuevo': 'lo que sea', 'dane': '305001003599'})
    for p in ParticipacionEvento.objects.filter(evento=ev):
        self.assertEqual((p.institucion, p.datos['dane'], p.datos['municipio_dane']), ('COLEGIO SAN JOSE DE LA SALLE', '305001003599', '05001'))
        self.assertEqual(p.datos['documento'][:3], '100')                  # lo demás de la inscripción no se toca
    # Solo el organizador
    self.assertEqual(self.cliente(self.ana.user).post(url, {'accion': 'editar', 'pid': b.pk, 'nombre': 'Hack'}).status_code, 403)

def _test_capturas(self):
    """Las capturas se agrupan por colegio (sin importar cómo lo escribieron) y se bajan en un .zip por colegio."""
    import io, zipfile
    from django.core.files.uploadedfile import SimpleUploadedFile
    from aula.models import GrabacionEvento
    ev = self.crear('Intercolegial')
    nueva = lambda nombre, inst, acomp='': ParticipacionEvento.objects.create(
        evento=ev, nombre=nombre, institucion=inst, grado=7, ciclo='exploradores', token=nombre, estado='aprobada',
        datos={'documento': nombre[:6], 'acompanante': acomp})
    a, b, c = nueva('Pedro Pérez', 'Colegio San José', 'Prof. Rosa'), nueva('María Gómez', 'colegio  san jose'), nueva('Luis Mora', 'Liceo Nacional')
    for p, n in ((a, 1), (a, 2), (b, 1), (c, 1)):
        GrabacionEvento.objects.create(participacion=p, numero=n, archivo=SimpleUploadedFile(f'p{n}.jpg', b'JPG%d' % n),
                                       tipo='image/jpeg', bytes=4)
    url = f'/aula/eventos/{ev.pk}/grabaciones/colegios/'
    r = self.admin.get(url)
    nombres = [g['nombre'] for g in r.context['colegios']]
    self.assertEqual(len(nombres), 2); self.assertIn('Liceo Nacional', nombres)
    san = next(g for g in r.context['colegios'] if g['clave'] == 'colegio san jose')
    self.assertEqual((len(san['personas']), san['n'], san['docentes']), (2, 3, ['Prof. Rosa']))
    self.assertContains(r, 'Prof. Rosa')
    self.assertEqual(len(self.admin.get(url + '?q=liceo').context['colegios']), 1)
    # ZIP del colegio: una carpeta por estudiante, sin los de otros colegios
    r = self.admin.get(url + '?zip=colegio+san+jose')
    z = zipfile.ZipFile(io.BytesIO(b''.join(r.streaming_content)))
    self.assertEqual(sorted(n.split('/')[0] for n in z.namelist()), ['María Gómez', 'Pedro Pérez', 'Pedro Pérez'])
    self.assertEqual(self.admin.get(url + '?zip=otro').status_code, 404)
    # Para la nube: solo los de ese colegio, con su carpeta
    d = self.admin.get(f'/aula/eventos/{ev.pk}/grabaciones/nube/?colegio=liceo+nacional').json()
    self.assertEqual((d['colegio'], [x['nombre'] for x in d['personas']]), ('Liceo Nacional', ['Luis Mora']))
    self.assertEqual(self.cliente(self.ana.user).get(url).status_code, 403)
    self.assertContains(self.admin.get(f'/aula/eventos/{ev.pk}/resultados/'), 'Capturas por colegio')


Olimpiada.test_corregir_datos_de_inscritos_y_unificar_colegios = _test_corregir_datos
Olimpiada.test_capturas_por_colegio = _test_capturas
