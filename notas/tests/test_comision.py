"""Promoción: promedio mínimo cuando se pierden áreas y notas que pone la comisión de evaluación."""
from decimal import Decimal

from django.template.loader import render_to_string
from django.urls import reverse

from notas.boletin.logic import get_datos_boletin_final
from notas.models import (AreaConocimiento, AsignacionDocente, Calificacion, ConfiguracionSistema, Materia,
                          NotaComision, PonderacionAreaMateria)

from .base import ColegioDePrueba


class Comision(ColegioDePrueba):

    def setUp(self):
        self.ingles = Materia.objects.create(colegio=self.a, nombre='Inglés')
        for nombre, materia in (('Humanidades', self.ingles), ('Matemáticas', self.materia)):
            area = AreaConocimiento.objects.create(colegio=self.a, nombre=nombre)
            PonderacionAreaMateria.objects.create(colegio=self.a, area=area, materia=materia, peso_porcentual=100)
        AsignacionDocente.objects.create(colegio=self.a, docente=self.docente, materia=self.ingles, curso=self.curso)
        self.ana = self.estudiantes[0]
        self.conf, _ = ConfiguracionSistema.objects.get_or_create(colegio=self.a)
        self.conf.max_areas_reprobadas = 1
        self.conf.save()

    def nota(self, materia, valor, periodo, tipo='PROM_PERIODO'):
        Calificacion.objects.update_or_create(colegio=self.a, estudiante=self.ana, materia=materia, periodo=periodo,
                                              tipo_nota=tipo, defaults={'valor_nota': Decimal(valor)})

    def boletin(self):
        return get_datos_boletin_final(self.a, self.curso, 2026, self.ana)[0][0]

    def url(self):
        return reverse('notas:comision_estudiante', args=[self.ana.id]) + '?ano=2026'

    # --- Regla del promedio ----------------------------------------------------

    def test_promedio_minimo_solo_cuando_pierde_areas(self):
        for p in (self.p1, self.p2):
            self.nota(self.ingles, '2.5', p)
            self.nota(self.materia, '4.0', p)
        self.assertEqual(self.boletin()['estado_promocion'], 'PROMOVIDO')      # 1 área perdida, sin promedio
        self.conf.promedio_minimo_promocion = Decimal('3.50')
        self.conf.save()
        b = self.boletin()
        self.assertEqual(b['estado_promocion'], 'NO PROMOVIDO')               # promedio 3,25 < 3,50
        self.assertIn('promedio general (3,25)', b['motivo_promocion'])
        # Sin áreas perdidas el promedio no cuenta.
        for p in (self.p1, self.p2):
            self.nota(self.ingles, '3.0', p)
            self.nota(self.materia, '3.0', p)
        self.assertEqual(self.boletin()['estado_promocion'], 'PROMOVIDO')

    def test_panel_guarda_el_promedio(self):
        self.a.admin_general = self.super
        r = self.cliente(self.super).post(reverse('notas:panel_control_promocion'),
                                          {'max_areas_reprobadas': '2', 'promedio_minimo_promocion': '3,5'})
        self.assertEqual(r.status_code, 302)
        self.conf.refresh_from_db()
        self.assertEqual((self.conf.max_areas_reprobadas, self.conf.promedio_minimo_promocion), (2, Decimal('3.50')))

    # --- La comisión -----------------------------------------------------------

    def perder_dos(self):
        for p in (self.p1, self.p2):
            self.nota(self.ingles, '2.5', p)
            self.nota(self.materia, '2.8', p)
        self.assertEqual(self.boletin()['estado_promocion'], 'NO PROMOVIDO')

    def test_pantalla_muestra_lo_que_necesita(self):
        self.perder_dos()
        r = self.cliente(self.rectora).get(self.url())
        self.assertContains(r, 'Inglés')
        self.assertContains(r, 'Necesita para aprobar: <strong>3,0</strong>', count=2)
        self.assertContains(r, 'name="niv_%d_%d"' % (self.ingles.id, self.p1.id))
        # Y desde la promoción se llega con un enlace.
        r = self.cliente(self.rectora).get(reverse('notas:promocion_anual') + '?ano=2026')
        self.assertContains(r, self.url())

    def test_nota_de_comision(self):
        self.perder_dos()
        r = self.cliente(self.rectora).post(self.url(), {
            'ano': '2026', 'acta': 'Acta 05', 'materia': [self.ingles.id],
            f'modo_{self.ingles.id}': 'comision', f'comision_{self.ingles.id}': '3,0'})
        self.assertEqual(r.status_code, 302)
        n = NotaComision.objects.get(estudiante=self.ana, materia=self.ingles, ano_lectivo=2026)
        self.assertEqual((n.valor_nota, n.acta), (Decimal('3.0'), 'Acta 05'))
        b = self.boletin()
        self.assertEqual(b['estado_promocion'], 'PROMOVIDO')                  # queda 1 área perdida (máx. 1)
        self.assertTrue(b['por_comision'])
        html = render_to_string('notas/boletin/boletin_final_pdf.html', {
            'boletines': [b], 'nombres_periodos': ['PRIMERO', 'SEGUNDO'], 'curso': self.curso,
            'ano_lectivo': 2026, 'colegio': self.a})
        self.assertIn('(3,0 Comisión)', html)
        self.assertIn('PROMOVIDO POR DECISIÓN DE LA COMISIÓN', html)
        # Vaciarla la quita.
        self.cliente(self.rectora).post(self.url(), {'ano': '2026', 'materia': [self.ingles.id],
                                                     f'modo_{self.ingles.id}': 'comision', f'comision_{self.ingles.id}': ''})
        self.assertFalse(NotaComision.objects.exists())

    def test_comision_no_acepta_menos_de_la_minima(self):
        self.perder_dos()
        r = self.cliente(self.rectora).post(self.url(), {
            'ano': '2026', 'materia': [self.ingles.id],
            f'modo_{self.ingles.id}': 'comision', f'comision_{self.ingles.id}': '2,9'}, follow=True)
        self.assertContains(r, 'debe estar entre')
        self.assertFalse(NotaComision.objects.exists())

    def test_nivelacion_por_periodos(self):
        self.perder_dos()
        NotaComision.objects.create(colegio=self.a, estudiante=self.ana, materia=self.materia, ano_lectivo=2026,
                                    valor_nota=Decimal('3.0'))
        r = self.cliente(self.rectora).post(self.url(), {
            'ano': '2026', 'materia': [self.materia.id], f'modo_{self.materia.id}': 'nivelacion',
            f'niv_{self.materia.id}_{self.p1.id}': '', f'niv_{self.materia.id}_{self.p2.id}': '3,2'})
        self.assertEqual(r.status_code, 302)
        self.assertFalse(NotaComision.objects.exists())                         # pasa a mandar la nivelación
        niv = Calificacion.objects.get(estudiante=self.ana, materia=self.materia, periodo=self.p2, tipo_nota='NIVELACION')
        self.assertEqual(niv.valor_nota, Decimal('3.2'))
        mat = next(m for a in self.boletin()['areas'] for m in a['materias'] if m['materia_id'] == self.materia.id)
        self.assertEqual(mat['definitiva_recuperada'], Decimal('3.0'))         # (2,8 + 3,2) / 2
        self.assertEqual(self.boletin()['estado_promocion'], 'PROMOVIDO')

    def test_solo_administradores(self):
        r = self.cliente(self.u_docente).get(self.url())
        self.assertNotEqual(r.status_code, 200)
