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
