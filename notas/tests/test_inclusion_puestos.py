"""Estudiantes de inclusión: puesto general, aparte o sin puesto; y si cuentan en el promedio del curso."""
from django.urls import reverse

from notas import estadisticas_logic, inclusion
from notas.boletin.ponderacion import en_lote
from notas.models import ConfiguracionCalificaciones, Mensaje

from .base import ColegioDePrueba


class PuestosDeInclusion(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ana, cls.beto, cls.caro = cls.estudiantes
        cls.beto.es_inclusion = True
        cls.beto.save()

    def _filas(self):
        # beto (inclusión) tiene el mejor promedio
        return [{'e': self.ana, 'p': 4.0}, {'e': self.beto, 'p': 4.8}, {'e': self.caro, 'p': 3.5}]

    def _modo(self, modo, en_promedio=True):
        ConfiguracionCalificaciones.objects.update_or_create(
            colegio=self.a, defaults={'inclusion_puesto': modo, 'inclusion_en_promedio_curso': en_promedio})

    def _puestos(self, empates=False):
        filas = self._filas()
        with en_lote():
            inclusion.asignar_puestos(filas, self.a, lambda f: f['p'], lambda f: f['e'], 'puesto', empates=empates)
        return [f['puesto'] for f in filas]

    def test_por_defecto_compiten_con_todos(self):
        self.assertEqual(self._puestos(), [2, 1, 3])

    def test_puesto_aparte(self):
        self._modo('APARTE')
        self.assertEqual(self._puestos(), [1, '1 (inclusión)', 2])
        with en_lote():
            podio = inclusion.para_podio(self._filas(), self.a, lambda f: f['e'])
        self.assertNotIn(self.beto, [f['e'] for f in podio])

    def test_sin_puesto(self):
        self._modo('SIN')
        self.assertEqual(self._puestos(), [1, '—', 2])

    def test_empates_comparten_puesto(self):
        filas = [{'e': self.ana, 'p': 4.0}, {'e': self.caro, 'p': 4.0}, {'e': self.beto, 'p': 3.0}]
        with en_lote():
            inclusion.asignar_puestos(filas, self.a, lambda f: f['p'], lambda f: f['e'], 'puesto', empates=True)
        self.assertEqual([f['puesto'] for f in filas], [1, 1, 3])

    def test_promedio_del_curso_con_o_sin_inclusion(self):
        self.assertEqual(estadisticas_logic._filtro_inclusion({'colegio': self.a}), {})
        self._modo('GENERAL', en_promedio=False)
        with en_lote():
            self.assertEqual(estadisticas_logic._filtro_inclusion({'colegio': self.a}), {'es_inclusion': False})
            self.assertEqual(estadisticas_logic._filtro_inclusion({'colegio': self.a, 'inclusion': 'solo'}, 'estudiante__'),
                             {'estudiante__es_inclusion': True})
            self.assertEqual(estadisticas_logic._filtro_inclusion({'colegio': self.a, 'inclusion': 'todos'}), {})

    def test_se_configura_en_calificaciones(self):
        r = self.cliente(self.rectora).get(reverse('notas:configuracion_calificaciones'))
        self.assertContains(r, 'name="inclusion_puesto"')
        self.assertContains(r, 'name="inclusion_en_promedio_curso"')


class CorreoEnPanelAdministrador(ColegioDePrueba):

    def test_icono_de_correo_con_mensajes_sin_leer(self):
        Mensaje.objects.create(colegio=self.a, remitente=self.u_docente, destinatario=self.rectora,
                               asunto='Hola', cuerpo='Reunión mañana', estado='ENVIADO')
        r = self.cliente(self.rectora).get(reverse('notas:admin_dashboard'))
        self.assertContains(r, reverse('notas:bandeja_entrada'))
        self.assertEqual(r.context['correo_sin_leer'], 1)
        self.assertContains(r, reverse('notas:familias'))
