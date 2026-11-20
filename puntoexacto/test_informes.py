# -*- coding: utf-8 -*-
"""Informes tipo ICFES (general y por estudiante) y pruebas unidas.

    python manage.py test puntoexacto
"""
from notas.tests.base import ColegioDePrueba

from . import informes as INF
from .calificacion import calificar_hoja
from .models import Examen, Hoja, PruebaUnida, Respuesta


class InformesIcfes(ColegioDePrueba):

    def setUp(self):
        self.c = self.cliente(self.u_docente)
        self.mat = self._examen('Simulacro Matemáticas', 'ABCD')
        self.lec = self._examen('Simulacro Lectura crítica', 'DCBA')
        ana, beto, caro = self.estudiantes
        # Matemáticas: Ana 4/4, Beto 2/4, Caro 0/4 (una en blanco). Lectura: Ana 2/4, Beto 4/4 y Caro no la presentó.
        self._hoja(self.mat, ana, 'ABCD')
        self._hoja(self.mat, beto, 'ABAA')
        self._hoja(self.mat, caro, 'BCA ')
        self._hoja(self.lec, ana, 'DCAD')
        self._hoja(self.lec, beto, 'DCBA')

    def _examen(self, titulo, clave):
        self.c.post('/puntoexacto/nuevo/', {
            'titulo': titulo, 'fecha': '2026-11-10', 'componente': 'SABER',
            'numero_preguntas': '4', 'numero_opciones': '4', 'hojas_por_pagina': '1',
            'asignacion': self.asig.id, 'cursos': [self.curso.id],
            'metodo': 'con_piso', 'nota_todo_mal': '1', 'nota_nada_marcado': '1', 'opciones_por_pregunta': '{}'})
        ex = Examen.objects.get(titulo=titulo)
        datos = {'metodo': 'con_piso'}
        for n, letra in zip(range(1, 5), clave):
            datos.update({f'correcta_{n}': letra, f'opciones_{n}': '4', f'puntos_{n}': '1'})
        self.c.post(f'/puntoexacto/{ex.id}/clave/', datos)
        return ex

    def _hoja(self, ex, est, marcas):
        h, _ = Hoja.objects.get_or_create(examen=ex, estudiante=est, defaults={'identificador': f'PE-{ex.id}-{est.id}'})
        for p, m in zip(ex.preguntas.order_by('numero'), marcas):
            Respuesta.objects.update_or_create(hoja=h, pregunta=p, defaults={'marcada': m.strip()})
        calificar_hoja(h)
        return h

    def test_puntajes_niveles_y_percentil(self):
        d = INF.construir([self.mat, self.lec])
        self.assertEqual([a['prueba'] for a in d['areas']], ['MAT', 'LC'])
        por = {p['nombre'].split()[-1]: p for p in d['personas']}
        ana = por['Ana']
        self.assertEqual([v['puntaje'] for v in ana['areas'].values()], [100, 50])
        self.assertEqual(ana['global'], 375)                 # (100·3 + 50·3) / 6 × 5
        self.assertEqual(ana['areas'][d['areas'][0]['clave']]['nivel'], 'Nivel 4')
        self.assertFalse(por['Caro']['completo'])
        self.assertEqual(por['Caro']['global'], 0)
        self.assertEqual(d['personas'][0]['nombre'], ana['nombre'])   # ordenados por global
        self.assertGreater(ana['percentil'], por['Caro']['percentil'])
        e = INF.de_estudiante(d, por['Caro']['clave'])
        self.assertEqual(len(e['falladas']), 4)
        self.assertIn('sin marcar', [f['marcada'] for f in e['falladas']])
        self.assertTrue(e['conclusiones'])

    def test_pdf_general_y_por_estudiante(self):
        r = self.c.get(f'/puntoexacto/{self.mat.id}/informe/')
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertTrue(r.content.startswith(b'%PDF'))
        r = self.c.get(f'/puntoexacto/{self.mat.id}/informe/estudiantes/')
        self.assertTrue(r.content.startswith(b'%PDF'))
        clave = f'e{self.estudiantes[0].id}'
        self.assertTrue(self.c.get(f'/puntoexacto/{self.mat.id}/informe/estudiante/{clave}/').content.startswith(b'%PDF'))
        self.assertEqual(self.c.get(f'/puntoexacto/{self.mat.id}/informe/estudiante/e999999/').status_code, 404)
        pagina = self.c.get(f'/puntoexacto/{self.mat.id}/resultados/')
        self.assertContains(pagina, f'/puntoexacto/{self.mat.id}/informe/estudiante/{clave}/')
        self.assertContains(pagina, 'Informe general (PDF)')

    def test_unir_examenes(self):
        r = self.c.post('/puntoexacto/unidas/', {'titulo': 'Simulacro noviembre', 'examenes': [self.mat.id]})
        self.assertContains(r, 'al menos dos')
        r = self.c.post('/puntoexacto/unidas/', {'titulo': 'Simulacro noviembre', 'examenes': [self.mat.id, self.lec.id]})
        u = PruebaUnida.objects.get()
        self.assertRedirects(r, f'/puntoexacto/unida/{u.pk}/', fetch_redirect_response=False)
        pagina = self.c.get(f'/puntoexacto/unida/{u.pk}/')
        self.assertContains(pagina, 'Prueba Ana')
        self.assertContains(pagina, 'incompleto')
        # Lectura pasa a «no es de Saber 11»: pesa 1 y el global de Ana cambia.
        d = INF.construir([self.mat, self.lec])
        clave_lec = d['areas'][1]['clave']
        self.c.post(f'/puntoexacto/unida/{u.pk}/', {f'area-{clave_lec}': 'NO', f'area-{d["areas"][0]["clave"]}': 'MAT'})
        u.refresh_from_db()
        self.assertEqual(u.areas[clave_lec], 'NO')
        d = INF.construir([self.mat, self.lec], u.titulo, u.areas)
        self.assertEqual(d['areas'][1]['prueba'], '')
        self.assertEqual(d['personas'][0]['global'], 438)    # (100·3 + 50·1) / 4 × 5 = 437,5
        self.assertTrue(self.c.get(f'/puntoexacto/unida/{u.pk}/informe/').content.startswith(b'%PDF'))
        self.assertTrue(self.c.get(f'/puntoexacto/unida/{u.pk}/estudiantes/').content.startswith(b'%PDF'))
        # Otro colegio no la ve.
        self.assertIn(self.cliente(self.u_docente, host='b.localhost').get(f'/puntoexacto/unida/{u.pk}/').status_code, (403, 404))
        self.c.post(f'/puntoexacto/unida/{u.pk}/', {'accion': 'eliminar'})
        self.assertFalse(PruebaUnida.objects.exists())
        self.assertEqual(Examen.objects.count(), 2)


class HojasCalificadas(InformesIcfes):
    """La hoja de cada estudiante con lo bueno, lo malo y la nota, para devolvérsela."""

    def test_pdf_con_una_pagina_por_estudiante(self):
        import io
        import os
        from pypdf import PdfReader
        r = self.c.get(f'/puntoexacto/{self.mat.id}/hojas-calificadas/')
        self.assertEqual(r['Content-Type'], 'application/pdf')
        pdf = PdfReader(io.BytesIO(r.content))
        self.assertEqual(len(pdf.pages), 3)
        texto = pdf.pages[0].extract_text()
        self.assertIn('bien', texto)
        if os.environ.get('PE_SAL'):
            open(os.path.join(os.environ['PE_SAL'], 'hojas_calificadas.pdf'), 'wb').write(r.content)
        hoja = self.mat.hojas.first()
        r = self.c.get(f'/puntoexacto/{self.mat.id}/hoja/{hoja.id}/calificada/')
        self.assertEqual(len(PdfReader(io.BytesIO(r.content)).pages), 1)
        self.assertContains(self.c.get(f'/puntoexacto/{self.mat.id}/resultados/'), f'/hoja/{hoja.id}/calificada/')
        # Una hoja de otro colegio no se deja ver.
        self.assertIn(self.cliente(self.u_docente, host='b.localhost')
                      .get(f'/puntoexacto/{self.mat.id}/hoja/{hoja.id}/calificada/').status_code, (403, 404))

    def test_como_va_el_grupo(self):
        d = self.c.get(f'/puntoexacto/{self.mat.id}/en-vivo/').json()
        print('VIVO', d)
        self.assertEqual(d['n'], 3)
        self.assertEqual(len(d['preguntas']), 4)
        self.assertEqual(d['falladas'][0]['pct'], min(q['pct'] for q in d['preguntas']))
