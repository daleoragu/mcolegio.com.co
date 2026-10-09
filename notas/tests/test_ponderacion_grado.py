"""Ponderación de áreas por grado: Física y Química no pesan igual en 6.° que en 10.°."""
from decimal import Decimal

from notas.models import (AreaConocimiento, AsignacionDocente, Calificacion, Curso, Materia, PonderacionAreaMateria,
                          PonderacionGrado)
from notas.pesos_area import pesos_areas

from .base import ColegioDePrueba
from .test_importar import xlsx

URL = '/admin/gestion-academica/ponderacion/'


class PonderacionPorGrado(ColegioDePrueba):

    def setUp(self):
        self.area = AreaConocimiento.objects.create(colegio=self.a, nombre='Ciencias Naturales')
        self.bio = Materia.objects.create(colegio=self.a, nombre='Biología', porcentaje_ser=0, porcentaje_saber=60,
                                          porcentaje_hacer=40)
        self.fis = Materia.objects.create(colegio=self.a, nombre='Física', porcentaje_ser=0, porcentaje_saber=60,
                                          porcentaje_hacer=40)
        for m in (self.bio, self.fis):
            PonderacionAreaMateria.objects.create(colegio=self.a, area=self.area, materia=m, peso_porcentual=50)
        self.c1001 = Curso.objects.create(colegio=self.a, nombre='1001', grado=10, subgrupo='01')
        for m in (self.bio, self.fis):
            AsignacionDocente.objects.create(colegio=self.a, docente=self.docente, materia=m, curso=self.c1001)
            AsignacionDocente.objects.create(colegio=self.a, docente=self.docente, materia=m, curso=self.curso)
        self.c = self.cliente(self.rectora)

    def test_un_grado_con_sus_propios_pesos(self):
        PonderacionGrado.objects.create(colegio=self.a, area=self.area, materia=self.bio, grado=10, peso_porcentual=20)
        PonderacionGrado.objects.create(colegio=self.a, area=self.area, materia=self.fis, grado=10, peso_porcentual=80)
        self.assertEqual(pesos_areas(self.a, 10)[(self.area.id, self.fis.id)], Decimal('80'))
        self.assertEqual(pesos_areas(self.a, 6)[(self.area.id, self.fis.id)], Decimal('50'))     # 6.° usa el general
        self.assertEqual(pesos_areas(self.a)[(self.area.id, self.fis.id)], Decimal('50'))

    def test_el_boletin_usa_los_pesos_del_grado(self):
        from notas.boletin.logic import get_datos_boletin_curso
        PonderacionGrado.objects.create(colegio=self.a, area=self.area, materia=self.bio, grado=10, peso_porcentual=20)
        PonderacionGrado.objects.create(colegio=self.a, area=self.area, materia=self.fis, grado=10, peso_porcentual=80)
        est10 = self.crear_estudiante('diego', curso=self.c1001)
        ana = self.estudiantes[0]
        for e in (est10, ana):
            Calificacion.objects.create(colegio=self.a, estudiante=e, materia=self.bio, periodo=self.p1,
                                        tipo_nota='PROM_PERIODO', valor_nota=Decimal('2.0'))
            Calificacion.objects.create(colegio=self.a, estudiante=e, materia=self.fis, periodo=self.p1,
                                        tipo_nota='PROM_PERIODO', valor_nota=Decimal('4.0'))

        def nota_area(curso, est):
            datos = get_datos_boletin_curso(self.a, curso, self.p1, est)
            return next(x for x in datos[0]['areas'] if x['nombre'].upper() == 'CIENCIAS NATURALES')['nota_final_area']
        self.assertEqual(nota_area(self.c1001, est10), Decimal('3.6'))     # 2×0,2 + 4×0,8
        self.assertEqual(nota_area(self.curso, ana), Decimal('3.0'))        # 6.°: mitad y mitad

    def test_pagina_general_y_por_grado(self):
        r = self.c.get(URL)
        self.assertContains(r, 'Todos los grados (generales)')
        self.assertContains(r, 'Décimo')
        r = self.c.post(URL, {'grado': '', f'peso-{self.area.id}-{self.bio.id}': '70',
                              f'peso-{self.area.id}-{self.fis.id}': '30'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(PonderacionAreaMateria.objects.get(materia=self.fis).peso_porcentual, Decimal('30'))
        self.assertFalse(PonderacionGrado.objects.exists())
        # Décimo con los suyos, y los mismos para Sexto.
        r = self.c.get(URL + '?grado=10')
        self.assertContains(r, 'General: 30 %')
        self.assertContains(r, 'Usa los generales')
        r = self.c.post(URL, {'grado': '10', f'peso-{self.area.id}-{self.bio.id}': '25',
                              f'peso-{self.area.id}-{self.fis.id}': '75', 'copiar_a': ['6']})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(pesos_areas(self.a, 10)[(self.area.id, self.fis.id)], Decimal('75'))
        self.assertEqual(pesos_areas(self.a, 6)[(self.area.id, self.fis.id)], Decimal('75'))
        self.assertEqual(PonderacionAreaMateria.objects.get(materia=self.fis).peso_porcentual, Decimal('30'))
        self.assertContains(self.c.get(URL + '?grado=10'), 'Propios de Décimo')
        # Volver al general.
        self.c.post(URL, {'grado': '10', 'accion': 'general'})
        self.assertEqual(pesos_areas(self.a, 10)[(self.area.id, self.fis.id)], Decimal('30'))
        self.assertEqual(pesos_areas(self.a, 6)[(self.area.id, self.fis.id)], Decimal('75'))

    def test_por_grado_solo_salen_las_materias_que_se_dictan(self):
        quim = Materia.objects.create(colegio=self.a, nombre='Química')
        PonderacionAreaMateria.objects.create(colegio=self.a, area=self.area, materia=quim, peso_porcentual=0)
        AsignacionDocente.objects.create(colegio=self.a, docente=self.docente, materia=quim, curso=self.c1001)
        self.assertContains(self.c.get(URL + '?grado=10'), 'Química')
        self.assertNotContains(self.c.get(URL + '?grado=6'), 'Química')

    def test_otro_colegio_no(self):
        otra = AreaConocimiento.objects.create(colegio=self.b, nombre='Ajena')
        mb = Materia.objects.create(colegio=self.b, nombre='Ajena')
        PonderacionAreaMateria.objects.create(colegio=self.b, area=otra, materia=mb, peso_porcentual=100)
        self.c.post(URL, {'grado': '10', f'peso-{otra.id}-{mb.id}': '5'})
        self.c.post(URL, {'grado': '', f'peso-{otra.id}-{mb.id}': '5'})
        self.assertFalse(PonderacionGrado.objects.exists())
        self.assertEqual(PonderacionAreaMateria.objects.get(area=otra).peso_porcentual, Decimal('100'))
        self.assertEqual(self.cliente(self.u_docente).get(URL).status_code, 302)

    def test_importar_por_grado_y_por_nivel(self):
        r = self.c.post('/admin/importacion/ponderacion/revisar/', {'archivo': xlsx(
            ['Área *', 'Materia *', 'Grado', 'Peso (%) *'], [
                ['Ciencias Naturales', 'Biología', '', '60'],
                ['Ciencias Naturales', 'Física', '', '40'],
                ['Ciencias Naturales', 'Biología', 'Media', '30'],
                ['Ciencias Naturales', 'Física', '10, 11', '70'],
                ['Ciencias Naturales', 'Física', 'Sexto', '45'],         # avisa: 6.° no suma 100
                ['Ciencias Naturales', 'Inglés', '', '10'],              # no es del área
                ['Ciencias Naturales', 'Biología', 'doce', '10'],
                ['Ciencias Naturales', 'Biología', '', 'mucho'],
            ])})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['resumen']['error'], 3)
        avisos = [a for x in r.context['resultados'] for a in x['avisos']]
        self.assertTrue(any('Sexto' in a and '45' in a for a in avisos), avisos)
        self.c.post('/admin/importacion/ponderacion/aplicar/')
        self.assertEqual(pesos_areas(self.a)[(self.area.id, self.bio.id)], Decimal('60'))
        self.assertEqual(pesos_areas(self.a, 11)[(self.area.id, self.bio.id)], Decimal('30'))
        self.assertEqual(pesos_areas(self.a, 11)[(self.area.id, self.fis.id)], Decimal('70'))
        self.assertEqual(pesos_areas(self.a, 6)[(self.area.id, self.fis.id)], Decimal('45'))
        # La plantilla con datos trae los generales y los de cada grado, y vuelve a entrar sin cambios.
        from django.core.files.uploadedfile import SimpleUploadedFile
        actual = self.c.get('/admin/importacion/ponderacion/plantilla/?datos=1').content
        r = self.c.post('/admin/importacion/ponderacion/revisar/', {'archivo': SimpleUploadedFile('a.xlsx', actual)})
        self.assertEqual(r.context['resumen']['error'], 0)
        self.assertEqual(r.context['resumen']['actualizar'], 0)
