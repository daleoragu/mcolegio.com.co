# -*- coding: utf-8 -*-
"""Cargar la clave de un cuadernillo desde CSV, Excel o Word, y preguntas de control."""
import io
import zipfile

from django.core.files.uploadedfile import SimpleUploadedFile

from notas.models import Materia
from notas.tests.base import ColegioDePrueba

from .models import Examen, Forma, Hoja

CSV = """pregunta,clave,area,competencia,componente,control
1,A,Ciencias naturales,Uso comprensivo,Entorno vivo,no
2,B,Ciencias naturales,Indagación,Ciencia, tecnología y sociedad,no
3,D,Ciencias naturales,Control,Control de lectura,si
4,C,Sociales y ciudadanas,Pensamiento social,Espacial y ambiental,no
5,A,Sociales y ciudadanas,Perspectivas,Ético-político,no
"""


def docx_con_tabla(filas):
    """Un .docx mínimo con una tabla, como la de especificaciones del colegio."""
    w = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    celdas = ''.join(
        '<w:tr>' + ''.join(f'<w:tc><w:p><w:r><w:t>{c}</w:t></w:r></w:p></w:tc>' for c in fila) + '</w:tr>'
        for fila in filas)
    doc = (f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{w}"><w:body>'
           f'<w:p><w:r><w:t>Clave y especificaciones</w:t></w:r></w:p><w:tbl>{celdas}</w:tbl>'
           f'</w:body></w:document>')
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        z.writestr('[Content_Types].xml', '<Types/>')
        z.writestr('word/document.xml', doc)
    return b.getvalue()


class CargarClave(ColegioDePrueba):

    def setUp(self):
        self.c = self.cliente(self.rectora)
        self.c.post('/puntoexacto/nuevo/', {
            'titulo': 'Simulacro 5.º sesión 2', 'fecha': '2026-10-20', 'componente': 'SABER',
            'numero_preguntas': '10', 'numero_opciones': '4', 'hojas_por_pagina': '1',
            'metodo': 'con_piso', 'nota_todo_mal': '1', 'nota_nada_marcado': '1',
            'opciones_por_pregunta': '{}'})
        self.ex = Examen.objects.get()

    def subir(self, contenido, nombre='clave.csv', **extra):
        datos = {'archivo': SimpleUploadedFile(nombre, contenido), 'crear_bloques': 'on', **extra}
        return self.c.post(f'/puntoexacto/{self.ex.id}/clave/importar/', datos)

    def test_csv_del_cuadernillo(self):
        Materia.objects.create(colegio=self.a, nombre='Ciencias Naturales')
        r = self.subir(CSV.encode('utf-8'))
        self.assertEqual(r.status_code, 302)
        self.ex.refresh_from_db()
        self.assertEqual(self.ex.numero_preguntas, 5)
        preguntas = list(self.ex.preguntas.order_by('numero'))
        self.assertEqual([p.correcta for p in preguntas], list('ABDCA'))
        # Un bloque por área, y el de ciencias amarrado a la materia del colegio.
        bloques = list(self.ex.bloques.all())
        self.assertEqual([b.nombre for b in bloques], ['Ciencias naturales', 'Sociales y ciudadanas'])
        self.assertEqual(bloques[0].materia.nombre, 'Ciencias Naturales')
        self.assertEqual([p.bloque.nombre for p in preguntas][3], 'Sociales y ciudadanas')
        # La coma sin comillas no partió el componente.
        self.assertEqual(preguntas[1].lista_etiquetas(), ['Indagación', 'Ciencia · tecnología y sociedad'])
        # La de control no suma, pero sigue en el examen.
        self.assertTrue(preguntas[2].es_control)
        self.assertEqual(preguntas[2].lista_etiquetas(), ['Control de lectura'])
        self.assertEqual(self.ex.preguntas_vigentes.count(), 4)

    def test_word_con_tabla_de_especificaciones(self):
        contenido = docx_con_tabla([
            ['N.º', 'Área', 'Clave', 'Competencia', 'Componente', 'DBA', 'Qué evalúa'],
            ['1', 'Ciencias naturales', 'A', 'Uso comprensivo', 'Entorno vivo', 'DBA 1', 'Reconoce…'],
            ['2', 'Ciencias naturales', 'D', 'Control', 'Control de lectura', '—', 'Pregunta de control'],
            ['3', 'Sociales y ciudadanas', 'B', 'Pensamiento social', 'Espacial y ambiental', 'DBA 2', '…'],
        ])
        r = self.subir(contenido, 'clave.docx')
        self.assertEqual(r.status_code, 302)
        preguntas = list(self.ex.preguntas.order_by('numero'))
        self.assertEqual([p.correcta for p in preguntas], list('ADB'))
        self.assertEqual([p.es_control for p in preguntas], [False, True, False])

    def test_excel_con_clave_de_otra_forma(self):
        import openpyxl
        libro = openpyxl.Workbook()
        h = libro.active
        h.append(['Pregunta', 'Clave', 'Clave B'])
        for n, a, b in [(1, 'A', 'C'), (2, 'B', 'A'), (3, 'C', 'D')]:
            h.append([n, a, b])
        b = io.BytesIO(); libro.save(b)
        self.subir(b.getvalue(), 'clave.xlsx')
        from . import formas as F
        forma = Forma.objects.get(examen=self.ex, letra='B')
        preguntas = list(self.ex.preguntas.order_by('numero'))
        self.assertEqual([c['correcta'] for c in F.clave_de(forma.orden, preguntas)], list('CAD'))

    def test_errores_no_tocan_el_examen(self):
        r = self.subir(b'pregunta,clave\n1,A\n3,Z\n')
        self.assertEqual(r.status_code, 302)
        self.ex.refresh_from_db()
        self.assertEqual(self.ex.numero_preguntas, 10)
        mensajes = [str(m) for m in r.wsgi_request._messages]
        self.assertTrue(any('no es una letra' in m for m in mensajes), mensajes)
        r = self.subir(b'numero;respuesta\n1;A\n3;B\n')
        self.assertTrue(any('sin saltos' in str(m) for m in r.wsgi_request._messages))

    def test_control_y_marca_r_en_resultados(self):
        self.subir(CSV.encode('utf-8'))
        hoja = Hoja.objects.create(examen=self.ex, identificador='PE-1', nombre_libre='Ana')
        # Acierta todo menos la de control (la 3 era D).
        self.c.post(f'/puntoexacto/{self.ex.id}/hoja/{hoja.id}/digitar/',
                    {'p_1': 'A', 'p_2': 'B', 'p_3': 'A', 'p_4': 'C', 'p_5': 'A'})
        hoja.refresh_from_db()
        self.assertEqual(hoja.nota, self.ex.nota_maxima)        # la de control no resta
        h = self.c.get(f'/puntoexacto/{self.ex.id}/resultados/').content.decode()
        self.assertIn('marcado R', h)
        self.assertIn('0/1', h)

    def test_exportar_y_volver_a_importar(self):
        self.subir(CSV.encode('utf-8'))
        r = self.c.get(f'/puntoexacto/{self.ex.id}/clave/exportar/?formato=csv')
        self.assertEqual(r.status_code, 200)
        texto = r.content.decode('utf-8-sig')
        self.assertIn('pregunta,clave,area,etiquetas,control', texto.splitlines()[0])
        self.assertIn('"Indagación, Ciencia · tecnología y sociedad"', texto)
        x = self.c.get(f'/puntoexacto/{self.ex.id}/clave/exportar/')
        self.assertEqual(x.status_code, 200)
        # El mismo archivo, de vuelta, deja el examen igual.
        antes = list(self.ex.preguntas.order_by('numero').values_list('correcta', 'etiquetas', 'es_control'))
        self.subir(texto.encode('utf-8'))
        despues = list(self.ex.preguntas.order_by('numero').values_list('correcta', 'etiquetas', 'es_control'))
        self.assertEqual(antes, despues)
