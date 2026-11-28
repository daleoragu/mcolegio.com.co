"""Indicadores de inclusión: cada estudiante de inclusión ve en el boletín los suyos; los demás, los del curso."""
import json

from django.template.loader import render_to_string

from notas import componentes as comp
from notas.models import AreaConocimiento, IndicadorLogroPeriodo, PonderacionAreaMateria

from .base import ColegioDePrueba


class IndicadoresDeInclusion(ColegioDePrueba):

    def setUp(self):
        area = AreaConocimiento.objects.create(colegio=self.a, nombre='Matemáticas')
        PonderacionAreaMateria.objects.create(colegio=self.a, area=area, materia=self.materia, peso_porcentual=100)
        IndicadorLogroPeriodo.objects.create(colegio=self.a, asignacion=self.asig, periodo=self.p1,
                                             descripcion='Resuelve problemas con fracciones')
        self.ana, self.beto, self.caro = self.estudiantes
        for e in (self.ana, self.beto):
            e.es_inclusion = True
            e.save()

    def guardar(self, obs):
        datos = {'asignacion_id': self.asig.id, 'periodo_id': self.p1.id, 'estudiantes': [
            {'id': str(e.id), 'notas': {'saber': [{'descripcion': 'N1', 'valor': '4'}]}, 'inasistencias': '0',
             'observacion': '', 'observacion_inclusion': obs.get(e.id, '')} for e in self.estudiantes]}
        r = self.cliente(self.u_docente).post('/docente/ingresar-notas/', json.dumps(datos),
                                              content_type='application/json')
        self.assertEqual(r.json().get('status'), 'success', r.content)

    def boletin(self, est):
        from notas.boletin.logic import get_datos_boletin_curso
        from notas.boletin.ponderacion import ajustes
        datos = get_datos_boletin_curso(self.a, self.curso, self.p1, est)
        return render_to_string('notas/boletin/boletin_pdf.html', {
            'boletines': datos, 'curso': self.curso, 'periodo': self.p1, 'colegio': self.a,
            'ajustes': ajustes(self.a), 'componentes': comp.componentes(self.a)})

    def test_cada_uno_con_los_suyos(self):
        self.guardar({self.ana.id: 'Cuenta hasta 20 con material concreto\nReconoce los números del 1 al 10',
                      self.beto.id: 'Suma con apoyo visual'})
        ana, beto, caro = (self.boletin(e) for e in self.estudiantes)
        self.assertIn('Cuenta hasta 20 con material concreto', ana)
        self.assertIn('Reconoce los números del 1 al 10', ana)
        self.assertNotIn('Suma con apoyo visual', ana)
        self.assertNotIn('resuelve problemas con fracciones', ana.lower())
        self.assertIn('Suma con apoyo visual', beto)
        self.assertNotIn('Cuenta hasta 20', beto)
        self.assertIn('resuelve problemas con fracciones', caro.lower())          # sin inclusión: los del curso
        self.assertNotIn('Suma con apoyo visual', caro)

    def test_si_no_hay_en_la_planilla_usa_los_objetivos_del_piar(self):
        from piar.models import AjustePiar, Piar
        piar = Piar.objects.create(colegio=self.a, estudiante=self.beto, ano_lectivo=2026)
        AjustePiar.objects.create(piar=piar, materia=self.materia, periodo=self.p1,
                                  objetivos='Identifica figuras planas\n- Cuenta de 2 en 2')
        self.guardar({self.ana.id: 'Cuenta hasta 20 con material concreto'})
        beto = self.boletin(self.beto)
        self.assertIn('Identifica figuras planas', beto)
        self.assertIn('• Cuenta de 2 en 2', beto)
        self.assertNotIn('resuelve problemas con fracciones', beto.lower())
        # Lo de la planilla manda sobre el PIAR
        self.assertIn('Cuenta hasta 20 con material concreto', self.boletin(self.ana))
