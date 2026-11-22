# -*- coding: utf-8 -*-
"""Preguntas con dos respuestas correctas y hojas donde el estudiante marcó dos."""
from notas.tests.base import ColegioDePrueba

from . import formas as formas_mod
from .calificacion import calificar_hoja
from .models import Examen, Hoja


class VariasCorrectas(ColegioDePrueba):

    def setUp(self):
        self.c = self.cliente(self.rectora)
        self.c.post('/puntoexacto/nuevo/', {
            'titulo': 'Parcial', 'fecha': '2026-10-06', 'componente': 'SABER',
            'numero_preguntas': '4', 'numero_opciones': '4', 'hojas_por_pagina': '1',
            'metodo': 'con_piso', 'nota_todo_mal': '1', 'nota_nada_marcado': '1',
            'opciones_por_pregunta': '{}'})
        self.ex = Examen.objects.get()
        datos = {'metodo': 'con_piso'}
        for n, letra in zip(range(1, 5), 'ABCD'):
            datos.update({f'correcta_{n}': letra, f'opciones_{n}': '4', f'puntos_{n}': '1'})
        datos['tambien_1'] = ['C']                  # en la 1 también vale la C
        r = self.c.post(f'/puntoexacto/{self.ex.id}/clave/', datos)
        self.assertNotEqual(r.status_code, 400)

    def nota(self, lectura):
        hoja = Hoja.objects.create(examen=self.ex, identificador=f'PE-{Hoja.objects.count() + 1}', nombre_libre='Ana')
        formas_mod.guardar_lectura(hoja, lectura)
        calificar_hoja(hoja)
        hoja.refresh_from_db()
        return hoja

    def test_la_clave_guarda_la_otra_correcta(self):
        p = self.ex.preguntas.get(numero=1)
        self.assertEqual(p.correcta, 'A')
        self.assertEqual(sorted(p.letras_correctas()), ['A', 'C'])
        self.assertTrue(p.tiene_otra_correcta)
        self.assertEqual(p.rotulo_correctas(), 'A o C')
        self.assertFalse(self.ex.preguntas.get(numero=2).tiene_otra_correcta)
        h = self.c.get(f'/puntoexacto/{self.ex.id}/clave/').content.decode()
        self.assertIn('name="tambien_1"', h)
        self.assertIn('+ Otra correcta', h)

    def test_cualquiera_de_las_dos_vale(self):
        con_a = self.nota({'1': 'A', '2': 'B', '3': 'C', '4': 'D'})
        con_c = self.nota({'1': 'C', '2': 'B', '3': 'C', '4': 'D'})
        self.assertEqual(con_a.nota, self.ex.nota_maxima)
        self.assertEqual(con_c.nota, self.ex.nota_maxima)

    def test_marcar_las_dos_correctas_vale_y_una_mala_no(self):
        dos_buenas = self.nota({'1': 'CA', '2': 'B', '3': 'C', '4': 'D'})
        self.assertEqual(dos_buenas.respuestas.get(pregunta__numero=1).marcada, 'AC')
        self.assertEqual(dos_buenas.nota, self.ex.nota_maxima)
        una_mala = self.nota({'1': 'AB', '2': 'B', '3': 'C', '4': 'D'})
        self.assertLess(una_mala.nota, self.ex.nota_maxima)
        # En una pregunta con una sola correcta, dos marcadas no valen.
        doble = self.nota({'1': 'A', '2': 'BC', '3': 'C', '4': 'D'})
        self.assertLess(doble.nota, self.ex.nota_maxima)

    def test_letra_que_no_existe_se_descarta(self):
        h = self.nota({'1': 'AZ', '2': 'B', '3': 'C', '4': 'D'})
        self.assertFalse(h.respuestas.filter(pregunta__numero=1).exclude(marcada='').exists())

    def test_quitar_la_otra_correcta(self):
        datos = {'metodo': 'con_piso'}
        for n, letra in zip(range(1, 5), 'ABCD'):
            datos.update({f'correcta_{n}': letra, f'opciones_{n}': '4', f'puntos_{n}': '1'})
        self.c.post(f'/puntoexacto/{self.ex.id}/clave/', datos)
        self.assertEqual(self.ex.preguntas.get(numero=1).letras_correctas(), ['A'])


class HojaEnBlanco(VariasCorrectas):
    """Una hoja sin nada marcado es «No presentó»: no recibe la nota más baja ni mueve el promedio."""

    test_la_clave_guarda_la_otra_correcta = test_cualquiera_de_las_dos_vale = None
    test_marcar_las_dos_correctas_vale_y_una_mala_no = test_letra_que_no_existe_se_descarta = None
    test_quitar_la_otra_correcta = None

    def guardar(self, hoja, respuestas, **extra):
        import json
        return self.c.post(f'/puntoexacto/{self.ex.id}/escanear/guardar/', json.dumps(
            {'hoja_id': hoja.id, 'respuestas': respuestas, **extra}), content_type='application/json').json()

    def test_en_blanco_queda_no_presento(self):
        from . import analisis
        buena = Hoja.objects.create(examen=self.ex, identificador='PE-B1', nombre_libre='Ana')
        blanca = Hoja.objects.create(examen=self.ex, identificador='PE-B2', nombre_libre='Beto')
        self.guardar(buena, {'1': 'A', '2': 'B', '3': 'C', '4': 'D'})
        d = self.guardar(blanca, {'1': '', '2': '', '3': '', '4': ''})
        self.assertTrue(d['ok']); self.assertTrue(d['ausente'])
        blanca.refresh_from_db()
        self.assertEqual((blanca.estado, blanca.nota), ('ausente', None))
        res = analisis.analizar(self.ex)['resumen']
        self.assertEqual(res['calificadas'], 1)                 # el promedio es solo el de Ana
        self.assertEqual(str(res['promedio']), str(self.ex.nota_maxima))

    def test_calificar_aunque_este_en_blanco(self):
        blanca = Hoja.objects.create(examen=self.ex, identificador='PE-B3', nombre_libre='Caro')
        d = self.guardar(blanca, {'1': '', '2': ''}, en_blanco=True)
        self.assertFalse(d.get('ausente'))
        blanca.refresh_from_db()
        self.assertEqual(blanca.estado, 'calificada')
        self.assertEqual(blanca.nota, self.ex.nota_nada_marcado)

    def test_cambiar_la_clave_no_califica_las_no_escaneadas(self):
        pendiente = Hoja.objects.create(examen=self.ex, identificador='PE-B4', nombre_libre='Dani')
        from .calificacion import calificar_examen
        calificar_examen(self.ex)
        pendiente.refresh_from_db()
        self.assertEqual((pendiente.estado, pendiente.nota), ('pendiente', None))

    def test_digitar_en_blanco(self):
        h = Hoja.objects.create(examen=self.ex, identificador='PE-B5', nombre_libre='Eva')
        self.c.post(f'/puntoexacto/{self.ex.id}/hoja/{h.id}/digitar/', {'p_1': '', 'p_2': ''})
        h.refresh_from_db(); self.assertEqual(h.estado, 'ausente')
        self.c.post(f'/puntoexacto/{self.ex.id}/hoja/{h.id}/digitar/', {'p_1': '', 'en_blanco': 'on'})
        h.refresh_from_db(); self.assertEqual((h.estado, h.nota), ('calificada', self.ex.nota_nada_marcado))

    def test_migracion_arregla_las_que_ya_tenian_nota(self):
        import importlib
        from django.apps import apps
        mig = importlib.import_module('puntoexacto.migrations.0014_hoja_en_blanco_no_presento')
        h = Hoja.objects.create(examen=self.ex, identificador='PE-B6', nombre_libre='Fer', estado='calificada', nota=1)
        mig.blancas_a_no_presento(apps, None)
        h.refresh_from_db()
        self.assertEqual((h.estado, h.nota), ('ausente', None))


class BuscadorDeExamenes(ColegioDePrueba):
    """La lista de exámenes se filtra por grado, curso y materia, del más reciente al más antiguo."""

    def test_filtros(self):
        from notas.models import AsignacionDocente, Curso, Materia
        c = self.cliente(self.rectora)
        c701 = Curso.objects.create(colegio=self.a, nombre='701', grado=7, subgrupo='1')
        c702 = Curso.objects.create(colegio=self.a, nombre='702', grado=7, subgrupo='2')
        bio = Materia.objects.create(colegio=self.a, nombre='Biología')
        asig7 = AsignacionDocente.objects.create(colegio=self.a, docente=self.docente, materia=bio, curso=c701)
        e6 = Examen.objects.create(colegio=self.a, titulo='Fracciones', fecha='2026-10-01', asignacion=self.asig)
        e6.cursos.set([self.curso])
        e7 = Examen.objects.create(colegio=self.a, titulo='Célula', fecha='2026-11-01', asignacion=asig7)
        e7.cursos.set([c701, c702])
        Examen.objects.create(colegio=self.a, titulo='Sin curso', fecha='2026-09-01')
        r = c.get('/puntoexacto/')
        self.assertEqual([e.titulo for e in r.context['examenes']], ['Célula', 'Fracciones', 'Sin curso'])   # más reciente primero
        self.assertEqual([(g, n) for g, _, n in r.context['grados']], [('6', 1), ('7', 1)])
        self.assertContains(r, '?grado=7')
        r = c.get('/puntoexacto/?grado=7')
        self.assertEqual([e.titulo for e in r.context['examenes']], ['Célula'])
        self.assertEqual([n for _, n, _ in r.context['cursos']], ['701', '702'])
        r = c.get(f'/puntoexacto/?grado=7&curso=c{c702.pk}')
        self.assertEqual([e.titulo for e in r.context['examenes']], ['Célula'])
        r = c.get('/puntoexacto/?materia=Biología')
        self.assertEqual([e.titulo for e in r.context['examenes']], ['Célula'])
        r = c.get('/puntoexacto/?grado=sin')
        self.assertEqual([e.titulo for e in r.context['examenes']], ['Sin curso'])
        self.assertContains(c.get('/puntoexacto/?grado=6&materia=Biología'), 'Quitar filtros')

    def test_grado_del_nombre_del_grupo(self):
        from .views import _grado_de_nombre
        self.assertEqual([_grado_de_nombre(x) for x in ('601', '1102', '7-01', 'Grado 9', 'Sexto')], [6, 11, 7, 9, None])
