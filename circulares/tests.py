# -*- coding: utf-8 -*-
"""Circulares: publicar a quien corresponde, leer, confirmar y ver quién falta."""
from notas.models import Curso, FichaEstudiante, Notificacion
from notas.tests.base import ColegioDePrueba

from .models import Circular, Lectura


class Circulares(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.otro = Curso.objects.create(colegio=cls.a, nombre='701', grado=7)
        cls.dani = cls.crear_estudiante('dani', curso=cls.otro)
        FichaEstudiante.objects.create(estudiante=cls.estudiantes[0], celular_madre='3001234567')

    def _publicar(self, **datos):
        base = {'titulo': 'Salida pedagógica', 'cuerpo': 'El viernes salimos al museo.', 'para': 'FAMILIAS',
                'pide_confirmacion': 'on', 'accion': 'publicar'}
        base.update(datos)
        return self.cliente(self.rectora).post('/circulares/gestion/nueva/', base)

    def test_publicar_a_todas_las_familias(self):
        self._publicar()
        c = Circular.objects.get()
        self.assertEqual(c.numero, 1)
        self.assertEqual(c.lecturas.count(), 4)            # ana, beto, caro y dani
        self.assertEqual(Notificacion.objects.filter(mensaje__contains='Salida pedagógica').count(), 4)
        self._publicar(titulo='Otra')
        self.assertEqual(Circular.objects.get(titulo='Otra').numero, 2)

    def test_solo_algunos_cursos_y_docentes(self):
        self._publicar(para='CURSOS', cursos=[self.otro.id])
        self.assertEqual(list(Lectura.objects.values_list('usuario__username', flat=True)), ['dani'])
        self._publicar(titulo='Para profes', para='DOCENTES')
        self.assertEqual(list(Circular.objects.get(titulo='Para profes').lecturas.values_list('usuario__username', flat=True)), ['profe'])

    def test_cursos_sin_escoger_no_se_publica(self):
        self._publicar(para='CURSOS')
        self.assertFalse(Circular.objects.exists())

    def test_la_familia_abre_y_confirma(self):
        self._publicar()
        c = Circular.objects.get()
        ana = self.cliente(self.estudiantes[0].user)
        self.assertContains(ana.get('/circulares/'), 'Nueva')
        self.assertContains(ana.get(f'/circulares/{c.id}/'), 'El viernes salimos al museo.')
        ana.post(f'/circulares/{c.id}/confirmar/', {'nombre': 'Marta (mamá)'})
        l = Lectura.objects.get(usuario=self.estudiantes[0].user)
        self.assertIsNotNone(l.abierta)
        self.assertEqual(l.quien_confirma, 'Marta (mamá)')
        # Quien no es destinatario no la ve.
        self.assertEqual(self.cliente(self.u_docente).get(f'/circulares/{c.id}/').status_code, 404)

    def test_detalle_muestra_pendientes_con_whatsapp(self):
        self._publicar()
        c = Circular.objects.get()
        r = self.cliente(self.rectora).get(f'/circulares/gestion/{c.id}/')
        self.assertContains(r, 'https://wa.me/573001234567')
        self.assertEqual(r.context['resumen']['total'], 4)

    def test_borrador_no_le_llega_a_nadie(self):
        self._publicar(accion='borrador')
        c = Circular.objects.get()
        self.assertTrue(c.es_borrador)
        self.assertFalse(c.lecturas.exists())
        self.assertEqual(self.cliente(self.u_docente).get('/circulares/gestion/').status_code, 403)

    def test_curso_sin_estudiantes_queda_en_borrador(self):
        vacio = Curso.objects.create(colegio=self.a, nombre='1101', grado=11)
        self._publicar(para='CURSOS', cursos=[vacio.id])
        self.assertTrue(Circular.objects.get().es_borrador)
