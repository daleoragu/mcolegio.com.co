# -*- coding: utf-8 -*-
"""Compartir un examen con otros docentes y la nota previa de la cámara.

    python manage.py test puntoexacto
"""
import json

from django.contrib.auth.models import User

from notas.models import Docente, Notificacion
from notas.tests.base import ColegioDePrueba

from .models import Bloque, Cuadernillo, Examen, Forma, Hoja


class CompartirExamen(ColegioDePrueba):

    def setUp(self):
        self.c = self.cliente(self.u_docente)
        self.c.post('/puntoexacto/nuevo/', {
            'titulo': 'Parcial de fracciones', 'fecha': '2026-10-06', 'componente': 'SABER',
            'numero_preguntas': '4', 'numero_opciones': '4', 'hojas_por_pagina': '1',
            'asignacion': self.asig.id, 'cursos': [self.curso.id],
            'metodo': 'con_piso', 'nota_todo_mal': '1', 'nota_nada_marcado': '1',
            'opciones_por_pregunta': '{}'})
        self.ex = Examen.objects.get()
        datos = {'metodo': 'con_piso'}
        for n, letra in zip(range(1, 5), 'ABCD'):
            datos.update({f'correcta_{n}': letra, f'opciones_{n}': '4', f'puntos_{n}': '1'})
        self.c.post(f'/puntoexacto/{self.ex.id}/clave/', datos)
        self.u2 = User.objects.create_user('profe2', password='x', first_name='Lina', last_name='Ruiz')
        self.docente2 = Docente.objects.create(colegio=self.a, user=self.u2)

    def test_cada_docente_recibe_su_copia(self):
        b = Bloque.objects.create(examen=self.ex, nombre='Fracciones', orden=1)
        self.ex.preguntas.filter(numero__lte=2).update(bloque=b)
        Forma.objects.create(examen=self.ex, letra='B', orden=[{'pregunta': n, 'opciones': 'ABCD'} for n in (2, 1, 4, 3)])
        Cuadernillo.objects.create(examen=self.ex, contenido={'preguntas': [{'texto': '¿1/2 + 1/4?'}]})
        Hoja.objects.create(examen=self.ex, identificador='PE-X-1', nombre_libre='Ana')

        pagina = self.c.get(f'/puntoexacto/{self.ex.id}/compartir/')
        self.assertContains(pagina, 'Lina Ruiz')
        self.assertNotContains(pagina, f'name="docentes" value="{self.docente.id}"')   # no a sí mismo
        r = self.c.post(f'/puntoexacto/{self.ex.id}/compartir/', {'docentes': [self.docente2.id]})
        self.assertRedirects(r, '/puntoexacto/', fetch_redirect_response=False)

        copia = Examen.objects.get(docente=self.docente2)
        self.assertEqual(copia.titulo, 'Parcial de fracciones')
        self.assertEqual(copia.compartido_por, self.docente)
        self.assertIsNone(copia.asignacion)
        self.assertFalse(copia.cursos.exists())
        self.assertEqual(copia.hojas.count(), 0)               # no se llevan hojas ni notas
        self.assertEqual(list(copia.preguntas.order_by('numero').values_list('correcta', flat=True)),
                         ['A', 'B', 'C', 'D'])
        bloque2 = copia.bloques.get()
        self.assertNotEqual(bloque2.id, b.id)
        self.assertEqual(copia.preguntas.filter(bloque=bloque2).count(), 2)
        self.assertEqual(copia.formas.get().letra, 'B')
        self.assertEqual(copia.cuadernillo.contenido['preguntas'][0]['texto'], '¿1/2 + 1/4?')
        # El original sigue igual y con su hoja.
        self.assertEqual(self.ex.hojas.count(), 1)
        self.assertEqual(self.ex.preguntas.filter(bloque=b).count(), 2)
        # La otra docente lo ve en su lista, con quién se lo compartió, y le llega el aviso.
        otra = self.cliente(self.u2)
        lista = otra.get('/puntoexacto/')
        self.assertContains(lista, 'Compartido por Pedro Profe')
        self.assertContains(lista, 'Escoja su asignatura')
        self.assertTrue(Notificacion.objects.filter(destinatario=self.u2).exists())
        self.assertEqual(otra.get(f'/puntoexacto/{copia.id}/editar/').status_code, 200)
        self.assertEqual(otra.get(f'/puntoexacto/{copia.id}/clave/').status_code, 200)
        # Lo que ella cambia no toca el original.
        copia.preguntas.filter(numero=1).update(correcta='D')
        self.assertEqual(self.ex.preguntas.get(numero=1).correcta, 'A')

    def test_sin_escoger_a_nadie_no_pasa_nada(self):
        r = self.c.post(f'/puntoexacto/{self.ex.id}/compartir/', {})
        self.assertContains(r, 'Escoja al menos un docente')
        self.assertEqual(Examen.objects.count(), 1)

    def test_no_se_comparte_un_examen_ajeno(self):
        self.assertEqual(self.cliente(self.u2).get(f'/puntoexacto/{self.ex.id}/compartir/').status_code, 404)

    def test_nota_previa_no_guarda_nada(self):
        antes = Hoja.objects.count()
        r = self.c.post(f'/puntoexacto/{self.ex.id}/escanear/nota/',
                        json.dumps({'respuestas': {'1': 'A', '2': 'B', '3': 'A', '4': ''}, 'forma': 'A'}),
                        content_type='application/json').json()
        self.assertTrue(r['ok'])
        self.assertEqual((r['buenas'], r['malas'], r['blancas'], r['total']), (2, 1, 1, 4))
        self.assertEqual(r['clave'], {'1': 'A', '2': 'B', '3': 'C', '4': 'D'})
        self.assertEqual(Hoja.objects.count(), antes)
        todo_bien = self.c.post(f'/puntoexacto/{self.ex.id}/escanear/nota/',
                                json.dumps({'respuestas': {'1': 'A', '2': 'B', '3': 'C', '4': 'D'}}),
                                content_type='application/json').json()
        self.assertEqual(todo_bien['nota'], str(self.ex.nota_maxima))
