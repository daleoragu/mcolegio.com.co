"""Elecciones escolares: preparar, votar una sola vez, voto secreto, mesa de votación, resultados y acta."""
from django.contrib.auth.models import User

from notas.models import Curso, Notificacion
from notas.tests.base import ColegioDePrueba

from .models import Candidato, Cargo, Eleccion, Papeleta, VotoEmitido


class Elecciones(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos or []) + ['elecciones']
        cls.a.save(update_fields=['modulos_activos'])
        cls.ana, cls.beto, cls.caro = cls.estudiantes
        cls.otro_curso = Curso.objects.create(colegio=cls.a, nombre='1101', grado=11, subgrupo='1')
        cls.dora = cls.crear_estudiante('dora', curso=cls.otro_curso)

    def _preparar(self):
        rectora = self.cliente(self.rectora)
        rectora.post('/votaciones/', {'nombre': 'Gobierno escolar 2027', 'plantilla': 'on'})
        e = Eleccion.objects.get()
        personero, contralor, vocero = list(e.cargos.all())
        url = f'/votaciones/{e.pk}/'
        rectora.post(url, {'accion': 'candidato', 'cargo': personero.pk, 'estudiante': self.dora.pk, 'propuesta': 'Más deporte'})
        rectora.post(url, {'accion': 'candidato', 'cargo': personero.pk, 'estudiante': self.caro.pk})
        rectora.post(url, {'accion': 'candidato', 'cargo': contralor.pk, 'estudiante': self.beto.pk})
        rectora.post(url, {'accion': 'candidato', 'cargo': vocero.pk, 'estudiante': self.ana.pk})       # vocero de 601
        rectora.post(url, {'accion': 'candidato', 'cargo': vocero.pk, 'estudiante': self.dora.pk})      # vocero de 1101
        return rectora, e, personero, contralor, vocero

    def test_preparar_abrir_votar_y_cerrar(self):
        rectora, e, personero, contralor, vocero = self._preparar()
        self.assertEqual(list(personero.candidatos.values_list('numero', flat=True)), [1, 2])
        self.assertEqual(set(vocero.candidatos.values_list('numero', flat=True)), {1})          # numerados por curso
        # Un estudiante no prepara elecciones ni ve resultados
        est = self.cliente(self.ana.user)
        self.assertEqual(est.get(f'/votaciones/{e.pk}/').status_code, 403)
        self.assertEqual(est.get(f'/votaciones/{e.pk}/resultados/').status_code, 403)
        # Abrir: avisa a los estudiantes
        rectora.post(f'/votaciones/{e.pk}/', {'accion': 'abrir'})
        e.refresh_from_db()
        self.assertEqual(e.estado, 'abierta')
        self.assertTrue(Notificacion.objects.filter(destinatario=self.ana.user, url='/votaciones/').exists())
        # El tarjetón de Ana: personero, contralor y SOLO el vocero de su curso
        r = est.get(f'/votaciones/{e.pk}/votar/')
        self.assertContains(r, 'Personero')
        self.assertContains(r, 'Más deporte')
        ana_vocero = vocero.candidatos.get(curso=self.curso)
        dora_vocero = vocero.candidatos.get(curso=self.otro_curso)
        self.assertNotContains(r, f'value="{dora_vocero.pk}"')
        # Si falta un cargo, no se guarda nada
        r = est.post(f'/votaciones/{e.pk}/votar/', {f'cargo-{personero.pk}': personero.candidatos.first().pk})
        self.assertContains(r, 'Escoja una opción')
        self.assertFalse(VotoEmitido.objects.exists())
        # No puede votar por el vocero de otro curso
        voto = {f'cargo-{personero.pk}': personero.candidatos.get(numero=1).pk, f'cargo-{contralor.pk}': 'blanco',
                f'cargo-{vocero.pk}': dora_vocero.pk}
        self.assertContains(est.post(f'/votaciones/{e.pk}/votar/', voto), 'Escoja una opción')
        voto[f'cargo-{vocero.pk}'] = ana_vocero.pk
        self.assertContains(est.post(f'/votaciones/{e.pk}/votar/', voto), 'Voto registrado')
        self.assertEqual(Papeleta.objects.count(), 3)
        self.assertEqual(Papeleta.objects.filter(cargo=contralor, candidato__isnull=True).count(), 1)   # en blanco
        # Una sola vez
        self.assertContains(est.post(f'/votaciones/{e.pk}/votar/', voto), 'ya votó')
        self.assertEqual(VotoEmitido.objects.count(), 1)
        self.assertEqual(Papeleta.objects.count(), 3)
        # Voto secreto: la papeleta no tiene a la persona ni la hora
        campos = {f.name for f in Papeleta._meta.get_fields()}
        self.assertFalse(campos & {'usuario', 'votante', 'creado', 'estudiante'})
        # Resultados y acta
        r = rectora.get(f'/votaciones/{e.pk}/resultados/')
        self.assertContains(r, 'votaron 1 de 4')
        self.assertEqual(rectora.get(f'/votaciones/{e.pk}/acta/').status_code, 302)      # aún abierta
        rectora.post(f'/votaciones/{e.pk}/', {'accion': 'cerrar'})
        r = rectora.get(f'/votaciones/{e.pk}/acta/')
        self.assertContains(r, 'ACTA DE ESCRUTINIO')
        self.assertContains(r, 'ELEGIDO(A)')
        # Cerrada: ya no se vota
        self.assertEqual(self.cliente(self.beto.user).post(f'/votaciones/{e.pk}/votar/', voto).status_code, 302)

    def test_mesa_de_votacion(self):
        rectora, e, personero, contralor, vocero = self._preparar()
        rectora.post(f'/votaciones/{e.pk}/', {'accion': 'abrir'})
        jurado = self.cliente(self.u_docente)                  # un docente abre la mesa
        url = f'/votaciones/{e.pk}/mesa/'
        self.assertContains(jurado.post(url, {'accion': 'buscar', 'usuario': 'nadie'}), 'No hay un estudiante')
        jurado.post(url, {'accion': 'buscar', 'usuario': 'beto'})
        r = jurado.get(url)
        self.assertContains(r, 'Vota: ')
        voto = {f'cargo-{personero.pk}': personero.candidatos.get(numero=2).pk, f'cargo-{contralor.pk}': contralor.candidatos.first().pk,
                f'cargo-{vocero.pk}': vocero.candidatos.get(curso=self.curso).pk}
        self.assertContains(jurado.post(url, voto), 'Siguiente votante')
        v = VotoEmitido.objects.get(usuario=self.beto.user)
        self.assertEqual((v.medio, v.jurado), ('mesa', self.u_docente))
        self.assertContains(jurado.post(url, {'accion': 'buscar', 'usuario': 'beto'}), 'ya votó')
        # Un estudiante no puede abrir la mesa
        self.assertEqual(self.cliente(self.ana.user).get(url).status_code, 403)

    def test_cargo_de_docentes_y_grados(self):
        rectora = self.cliente(self.rectora)
        rectora.post('/votaciones/', {'nombre': 'Consejo directivo'})
        e = Eleccion.objects.get()
        url = f'/votaciones/{e.pk}/'
        rectora.post(url, {'accion': 'cargo', 'nombre': 'Representante de los docentes', 'votan': 'docentes', 'blanco': 'on'})
        rectora.post(url, {'accion': 'cargo', 'nombre': 'Representante de los estudiantes', 'votan': 'grados',
                           'desde': '11', 'hasta': '11', 'blanco': 'on'})
        doc_cargo, est_cargo = list(e.cargos.all())
        rectora.post(url, {'accion': 'candidato', 'cargo': doc_cargo.pk, 'nombre': 'Pedro Profe'})
        rectora.post(url, {'accion': 'candidato', 'cargo': est_cargo.pk, 'estudiante': self.dora.pk})
        rectora.post(url, {'accion': 'abrir'})
        profe = self.cliente(self.u_docente)
        r = profe.get(f'/votaciones/{e.pk}/votar/')
        self.assertContains(r, 'Representante de los docentes')
        self.assertNotContains(r, 'Representante de los estudiantes')
        # Ana es de 6°: no vota al representante de 11°
        self.assertEqual(self.cliente(self.ana.user).get(f'/votaciones/{e.pk}/votar/').status_code, 302)
        self.assertContains(self.cliente(self.dora.user).get(f'/votaciones/{e.pk}/votar/'), 'Representante de los estudiantes')

    def test_no_abre_sin_candidatos_y_modulo(self):
        rectora = self.cliente(self.rectora)
        rectora.post('/votaciones/', {'plantilla': 'on'})
        e = Eleccion.objects.get()
        rectora.post(f'/votaciones/{e.pk}/', {'accion': 'abrir'})
        e.refresh_from_db()
        self.assertEqual(e.estado, 'preparacion')
        self.assertContains(self.cliente(self.ana.user).get('/votaciones/'), 'No hay votaciones abiertas')
        self.a.modulos_activos = [m for m in self.a.modulos_activos if m != 'elecciones']
        self.a.save(update_fields=['modulos_activos'])
        self.assertEqual(self.cliente(self.ana.user).get('/votaciones/').status_code, 403)


class BorrarElecciones(ColegioDePrueba):
    """Una elección creada por error se puede borrar, aunque ya tenga votos."""
    _preparar = Elecciones._preparar

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos or []) + ['elecciones']
        cls.a.save(update_fields=['modulos_activos'])
        cls.ana, cls.beto, cls.caro = cls.estudiantes
        cls.otro_curso = Curso.objects.create(colegio=cls.a, nombre='1101', grado=11, subgrupo='1')
        cls.dora = cls.crear_estudiante('dora', curso=cls.otro_curso)

    def test_borrar_en_preparacion(self):
        rectora, e, *_ = self._preparar()
        rectora.post(f'/votaciones/{e.pk}/', {'accion': 'eliminar'})
        self.assertFalse(Eleccion.objects.exists())
        self.assertFalse(Cargo.objects.exists())

    def test_abierta_con_votos_pide_escribir_eliminar(self):
        rectora, e, personero, contralor, vocero = self._preparar()
        rectora.post(f'/votaciones/{e.pk}/', {'accion': 'abrir'})
        e.refresh_from_db()
        self.assertEqual(e.estado, 'abierta')
        ana = self.cliente(self.ana.user)
        ana.post(f'/votaciones/{e.pk}/votar/', {f'cargo-{personero.pk}': personero.candidatos.first().pk,
                                                f'cargo-{contralor.pk}': contralor.candidatos.first().pk,
                                                f'cargo-{vocero.pk}': vocero.candidatos.filter(curso=self.curso).first().pk})
        self.assertEqual(VotoEmitido.objects.count(), 1)
        rectora.post(f'/votaciones/{e.pk}/', {'accion': 'eliminar'})
        self.assertTrue(Eleccion.objects.exists())
        rectora.post(f'/votaciones/{e.pk}/', {'accion': 'eliminar', 'confirmacion': 'eliminar'})
        self.assertFalse(Eleccion.objects.exists())
        self.assertFalse(VotoEmitido.objects.exists())
        self.assertFalse(Papeleta.objects.exists())

    def test_superusuario_puede_borrar(self):
        _, e, *_ = self._preparar()
        self.cliente(self.super).post(f'/votaciones/{e.pk}/', {'accion': 'eliminar'})
        self.assertFalse(Eleccion.objects.exists())

    def test_docente_o_estudiante_no_borran(self):
        _, e, *_ = self._preparar()
        self.cliente(self.u_docente).post(f'/votaciones/{e.pk}/', {'accion': 'eliminar'})
        self.cliente(self.ana.user).post(f'/votaciones/{e.pk}/', {'accion': 'eliminar'})
        self.assertTrue(Eleccion.objects.exists())


class Cabinas(ColegioDePrueba):
    """La cabina se vincula al celular del jurado y abre el tarjetón del carné que él escanea."""
    _preparar = Elecciones._preparar

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos or []) + ['elecciones']
        cls.a.save(update_fields=['modulos_activos'])
        cls.ana, cls.beto, cls.caro = cls.estudiantes
        cls.otro_curso = Curso.objects.create(colegio=cls.a, nombre='1101', grado=11, subgrupo='1')
        cls.dora = cls.crear_estudiante('dora', curso=cls.otro_curso)

    def setUp(self):
        rectora, self.e, self.personero, self.contralor, self.vocero = self._preparar()
        rectora.post(f'/votaciones/{self.e.pk}/', {'accion': 'abrir'})
        self.e.refresh_from_db()
        self.jurado = self.cliente(self.u_docente)
        self.equipo = self.cliente()                 # la tableta de la cabina, sin iniciar sesión

    def accion(self, **datos):
        return self.jurado.post(f'/votaciones/{self.e.pk}/jurado/accion/', datos).json()

    def carne(self, est):
        return f'https://a.mcolegio.com.co/c/{est.asegurar_codigo_carnet()}/'

    def vincular(self):
        from .models import Cabina
        r = self.equipo.get('/votaciones/cabina/')
        self.assertContains(r, 'Cabina de votación')
        cabina = Cabina.objects.latest('creada')
        j = self.accion(texto=f'https://a.mcolegio.com.co/votaciones/cabina/v/{cabina.vinculo}/')
        self.assertTrue(j['ok'], j)
        return cabina

    def test_vincular_escanear_carne_y_votar(self):
        self.vincular()
        r = self.equipo.get('/votaciones/cabina/')
        self.assertContains(r, 'Esperando al siguiente votante')
        self.assertEqual(self.equipo.get('/votaciones/cabina/estado/').json()['estado'], 'libre')
        j = self.accion(texto=self.carne(self.ana))
        self.assertTrue(j['ok'], j)
        self.assertIn('cabina 1', j['mensaje'])
        r = self.equipo.get('/votaciones/cabina/')
        self.assertContains(r, 'Vota: Ana Prueba')
        votos = {f'cargo-{self.personero.pk}': self.personero.candidatos.first().pk,
                 f'cargo-{self.contralor.pk}': 'blanco',
                 f'cargo-{self.vocero.pk}': self.vocero.candidatos.get(curso=self.curso).pk}
        r = self.equipo.post('/votaciones/cabina/', votos)
        self.assertContains(r, 'Voto registrado')
        v = VotoEmitido.objects.get(usuario=self.ana.user)
        self.assertEqual((v.medio, v.jurado), ('cabina', self.u_docente))
        self.assertEqual(Papeleta.objects.count(), 3)
        # Vuelve a quedar libre y no deja votar de nuevo
        self.assertEqual(self.equipo.get('/votaciones/cabina/estado/').json()['estado'], 'libre')
        j = self.accion(texto=self.carne(self.ana))
        self.assertFalse(j['ok'])
        self.assertIn('ya votó', j['mensaje'])

    def test_vincular_con_las_seis_cifras(self):
        from .models import Cabina
        self.equipo.get('/votaciones/cabina/')
        cabina = Cabina.objects.latest('creada')
        j = self.accion(texto=cabina.codigo)
        self.assertTrue(j['ok'], j)
        cabina.refresh_from_db()
        self.assertEqual(cabina.jurado, self.u_docente)

    def test_sin_cabina_libre(self):
        self.vincular()
        self.assertTrue(self.accion(texto=self.carne(self.ana))['ok'])
        j = self.accion(texto=self.carne(self.beto))
        self.assertFalse(j['ok'])
        self.assertIn('No hay cabinas libres', j['mensaje'])

    def test_liberar_no_guarda_voto(self):
        cabina = self.vincular()
        self.accion(texto=self.carne(self.ana))
        self.accion(accion='liberar', cabina=cabina.pk)
        self.assertContains(self.equipo.get('/votaciones/cabina/'), 'Esperando al siguiente votante')
        self.assertFalse(VotoEmitido.objects.exists())

    def test_la_cabina_sin_votante_no_vota(self):
        self.vincular()
        r = self.equipo.post('/votaciones/cabina/', {f'cargo-{self.personero.pk}': 'blanco'})
        self.assertFalse(VotoEmitido.objects.exists())
        self.assertEqual(r.status_code, 200)

    def test_estudiante_no_es_jurado(self):
        r = self.cliente(self.ana.user).post(f'/votaciones/{self.e.pk}/jurado/accion/', {'texto': self.carne(self.beto)})
        self.assertEqual(r.status_code, 403)

    def test_enlace_pide_confirmar(self):
        from .models import Cabina
        self.equipo.get('/votaciones/cabina/')
        cabina = Cabina.objects.latest('creada')
        r = self.jurado.get(f'/votaciones/cabina/v/{cabina.vinculo}/')
        self.assertContains(r, 'Vincular esta cabina')
        cabina.refresh_from_db()
        self.assertIsNone(cabina.jurado)
        self.jurado.post(f'/votaciones/cabina/v/{cabina.vinculo}/', {'eleccion': self.e.pk})
        cabina.refresh_from_db()
        self.assertEqual(cabina.jurado, self.u_docente)

    def test_pagina_del_jurado(self):
        r = self.jurado.get(f'/votaciones/{self.e.pk}/jurado/')
        self.assertContains(r, 'Mis cabinas')
        self.assertContains(r, 'lector_qr.js')

    def test_mesa_acepta_el_carne(self):
        r = self.jurado.post(f'/votaciones/{self.e.pk}/mesa/', {'accion': 'buscar', 'usuario': self.carne(self.beto)})
        self.assertRedirects(r, f'/votaciones/{self.e.pk}/mesa/', fetch_redirect_response=False)
        self.assertContains(self.jurado.get(f'/votaciones/{self.e.pk}/mesa/'), 'Vota: Beto Prueba')
