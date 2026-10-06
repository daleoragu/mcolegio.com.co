# notas/tests/test_cursos_promocion_alertas.py
"""Nombres de cursos, promoción de fin de año y alertas tempranas."""
from decimal import Decimal

from django.urls import reverse

from notas.alertas import alertas_de_curso
from notas.boletin.logic import estudiantes_del_curso_en
from notas.models import Calificacion, Curso, HistorialMatricula, Materia, AsignacionDocente
from notas.models.perfiles import clave_subgrupo, nombre_curso_sugerido

from .base import ColegioDePrueba


class NombresDeCurso(ColegioDePrueba):

    def test_formatos(self):
        self.assertEqual(nombre_curso_sugerido(7, '1', '701'), '701')
        self.assertEqual(nombre_curso_sugerido(7, '1', '71'), '71')
        self.assertEqual(nombre_curso_sugerido(7, '1', '7-1'), '7-1')
        self.assertEqual(nombre_curso_sugerido(7, 'a', '7-1'), '7-A')
        self.assertEqual(nombre_curso_sugerido(7, ''), 'SÉPTIMO')

    def test_1_y_01_son_el_mismo_grupo(self):
        self.assertEqual(clave_subgrupo('01'), clave_subgrupo('1'))

    def test_601_pasa_a_71(self):
        destino = Curso.objects.create(colegio=self.a, nombre='71', grado=7, subgrupo='1')
        self.assertEqual(self.curso.curso_siguiente_sugerido(), destino)


class Promocion(ColegioDePrueba):

    def test_promover_guarda_historial_y_se_puede_deshacer(self):
        destino = Curso.objects.create(colegio=self.a, nombre='701', grado=7, subgrupo='1')
        ana, beto, _ = self.estudiantes
        c = self.cliente(self.rectora)
        datos = {'ano': '2026', 'accion': 'promover', f'destino_{self.curso.id}': str(destino.id)}
        for e in self.estudiantes:
            datos[f'resultado_{e.id}'] = 'NO_PROMOVIDO' if e == beto else 'PROMOVIDO'
        self.assertEqual(c.post(reverse('notas:promocion_anual'), datos).status_code, 302)
        ana.refresh_from_db(); beto.refresh_from_db()
        self.assertEqual(ana.curso, destino)
        self.assertEqual(beto.curso, self.curso)
        # El boletín 2026 del 601 sigue siendo de quienes estuvieron ahí
        self.assertEqual(set(estudiantes_del_curso_en(self.a, self.curso, 2026)), set(self.estudiantes))
        c.post(reverse('notas:promocion_anual'), {'ano': '2026', 'accion': 'deshacer'})
        ana.refresh_from_db()
        self.assertEqual(ana.curso, self.curso)
        self.assertFalse(HistorialMatricula.objects.exists())


class Alertas(ColegioDePrueba):

    def test_riesgo_por_materias_perdidas(self):
        ana = self.estudiantes[0]
        otras = [Materia.objects.create(colegio=self.a, nombre=n) for n in ('Lenguaje', 'Ciencias')]
        for m in otras:
            AsignacionDocente.objects.create(colegio=self.a, docente=self.docente, materia=m, curso=self.curso)
        for m in [self.materia] + otras:
            Calificacion.objects.create(colegio=self.a, estudiante=ana, materia=m, periodo=self.p1,
                                        tipo_nota='PROM_PERIODO', valor_nota=Decimal('2.0'))
        fila = next(f for f in alertas_de_curso(self.a, self.curso, 2026, self.p1) if f['estudiante'] == ana)
        self.assertEqual(fila['n'], 3)
        self.assertEqual(fila['riesgo'], 'alto')     # más de 2 permitidas

    def test_la_nivelacion_cuenta(self):
        beto = self.estudiantes[1]
        Calificacion.objects.create(colegio=self.a, estudiante=beto, materia=self.materia, periodo=self.p1,
                                    tipo_nota='PROM_PERIODO', valor_nota=Decimal('2.0'))
        Calificacion.objects.create(colegio=self.a, estudiante=beto, materia=self.materia, periodo=self.p1,
                                    tipo_nota='NIVELACION', valor_nota=Decimal('3.5'))
        fila = next(f for f in alertas_de_curso(self.a, self.curso, 2026, self.p1) if f['estudiante'] == beto)
        self.assertEqual(fila['riesgo'], 'ok')
