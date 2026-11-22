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


class DescargarTodo(InformesIcfes):
    """Todos los informes de un examen (o los escogidos) en un solo ZIP."""

    def _zip(self, datos):
        import io
        import zipfile
        r = self.c.post(f'/puntoexacto/{self.mat.id}/informes/descargar/', datos)
        self.assertEqual(r['Content-Type'], 'application/zip')
        return zipfile.ZipFile(io.BytesIO(r.content))

    def test_un_pdf_por_estudiante(self):
        from pypdf import PdfReader
        import io
        ids = list(self.mat.hojas.values_list('id', flat=True))
        z = self._zip({'tipos': ['general', 'informes', 'hojas', 'excel'], 'modo': 'separado', 'hojas': ids})
        nombres = sorted(z.namelist())
        self.assertIn('Informe general (total).pdf', nombres)
        self.assertIn('Resultados.xlsx', nombres)
        self.assertEqual(len([n for n in nombres if n.startswith('Informes por estudiante/')]), 3)
        self.assertEqual(len([n for n in nombres if n.startswith('Hojas calificadas/')]), 3)
        # Cada informe individual es de su estudiante.
        for n in nombres:
            if n.startswith('Informes por estudiante/'):
                texto = PdfReader(io.BytesIO(z.read(n))).pages[0].extract_text()
                self.assertIn(n.split('/')[1][:-4], texto)

    def test_solo_los_escogidos_y_todo_junto(self):
        ana = self.mat.hojas.get(estudiante=self.estudiantes[0])
        z = self._zip({'tipos': ['informes', 'hojas'], 'modo': 'junto', 'hojas': [ana.id]})
        self.assertEqual(sorted(z.namelist()), ['Hojas calificadas.pdf', 'Informes por estudiante.pdf'])
        import io
        from pypdf import PdfReader
        self.assertEqual(len(PdfReader(io.BytesIO(z.read('Hojas calificadas.pdf'))).pages), 1)

    def test_sin_escoger_nada(self):
        r = self.c.post(f'/puntoexacto/{self.mat.id}/informes/descargar/', {'tipos': ['informes']})
        self.assertRedirects(r, f'/puntoexacto/{self.mat.id}/resultados/', fetch_redirect_response=False)
        pagina = self.c.get(f'/puntoexacto/{self.mat.id}/resultados/')
        self.assertContains(pagina, 'Descargar informes')
        self.assertContains(pagina, 'name="hojas"')


class InformePorGrado(InformesIcfes):
    """Un examen con estudiantes de dos grados: informe total, de cada grado y de cada curso."""

    def setUp(self):
        super().setUp()
        from notas.models import Curso
        self.c701 = Curso.objects.create(colegio=self.a, nombre='701', grado=7, subgrupo='1')
        self.dani = self.crear_estudiante('dani', curso=self.c701)
        self._hoja(self.mat, self.dani, 'ABCD')

    # Las del examen base cuentan con tres estudiantes; aquí hay un cuarto.
    test_puntajes_niveles_y_percentil = None
    test_unir_examenes = None
    test_pdf_general_y_por_estudiante = None

    def test_zip_con_grados_y_cursos(self):
        import io
        import zipfile
        from pypdf import PdfReader
        ids = list(self.mat.hojas.values_list('id', flat=True))
        r = self.c.post(f'/puntoexacto/{self.mat.id}/informes/descargar/',
                        {'tipos': ['general', 'grados', 'cursos'], 'modo': 'separado', 'hojas': ids})
        z = zipfile.ZipFile(io.BytesIO(r.content))
        nombres = sorted(z.namelist())
        self.assertEqual(nombres, ['Informe general (total).pdf', 'Informes por curso/Curso 601.pdf',
                                   'Informes por curso/Curso 701.pdf', 'Informes por grado/Grado 6.pdf',
                                   'Informes por grado/Grado 7.pdf'])
        texto7 = ''.join(p.extract_text() for p in PdfReader(io.BytesIO(z.read('Informes por grado/Grado 7.pdf'))).pages)
        self.assertIn('Grado 7', texto7)
        self.assertIn('Prueba Dani', texto7)
        self.assertNotIn('Prueba Ana', texto7)
        total = ''.join(p.extract_text() for p in PdfReader(io.BytesIO(z.read('Informe general (total).pdf'))).pages)
        self.assertIn('Prueba Dani', total)
        self.assertIn('Prueba Ana', total)

    def test_total_es_solo_lo_escogido(self):
        import io
        import zipfile
        from pypdf import PdfReader
        r = self.c.post(f'/puntoexacto/{self.mat.id}/informes/descargar/',
                        {'tipos': ['general'], 'hojas': [self.mat.hojas.get(estudiante=self.dani).id]})
        texto = ''.join(p.extract_text() for p in PdfReader(io.BytesIO(
            zipfile.ZipFile(io.BytesIO(r.content)).read('Informe general (total).pdf'))).pages)
        self.assertIn('Prueba Dani', texto)
        self.assertNotIn('Prueba Ana', texto)

    def test_botones_por_grado(self):
        pagina = self.c.get(f'/puntoexacto/{self.mat.id}/resultados/')
        self.assertContains(pagina, '?grado=Grado%207')
        self.assertContains(pagina, 'value="grados"')
        r = self.c.get(f'/puntoexacto/{self.mat.id}/informe/?grado=Grado%207')
        self.assertEqual(r['Content-Type'], 'application/pdf')
        u = PruebaUnida.objects.create(titulo='Simulacro', colegio=self.a)
        u.examenes.set([self.mat, self.lec])
        self.assertContains(self.c.get(f'/puntoexacto/unida/{u.pk}/'), '?grado=Grado%206')
        self.assertTrue(self.c.get(f'/puntoexacto/unida/{u.pk}/informe/?grado=Grado%207').content.startswith(b'%PDF'))


class DescargarUnida(InformesIcfes):
    """El ZIP de informes también para una prueba unida (varios exámenes)."""

    def setUp(self):
        super().setUp()
        self.u = PruebaUnida.objects.create(titulo='Simulacro noviembre', colegio=self.a)
        self.u.examenes.set([self.mat, self.lec])

    test_unir_examenes = None          # la base crea su propia prueba unida

    def _zip(self, datos):
        import io
        import zipfile
        r = self.c.post(f'/puntoexacto/unida/{self.u.pk}/descargar/', datos)
        self.assertEqual(r['Content-Type'], 'application/zip')
        return zipfile.ZipFile(io.BytesIO(r.content))

    def test_todo_separado(self):
        import io
        from pypdf import PdfReader
        claves = [f'e{e.id}' for e in self.estudiantes]
        pagina = self.c.get(f'/puntoexacto/unida/{self.u.pk}/')
        self.assertContains(pagina, 'Descargar informes')
        self.assertContains(pagina, f'name="personas" value="{claves[0]}"')
        z = self._zip({'tipos': ['general', 'informes', 'hojas', 'excel'], 'modo': 'separado', 'personas': claves})
        nombres = sorted(z.namelist())
        self.assertIn('Informe general (total).pdf', nombres)
        self.assertEqual(len([n for n in nombres if n.startswith('Informes por estudiante/')]), 3)
        hojas = [n for n in nombres if n.startswith('Hojas calificadas/')]
        self.assertEqual(len(hojas), 3)
        self.assertEqual(len([n for n in nombres if n.endswith('.xlsx')]), 2)        # un Excel por examen
        # Ana presentó los dos exámenes: su PDF trae sus dos hojas.
        ana = next(n for n in hojas if 'Ana' in n)
        self.assertEqual(len(PdfReader(io.BytesIO(z.read(ana))).pages), 2)
        texto = PdfReader(io.BytesIO(z.read(next(n for n in nombres if n.startswith('Informes por estudiante/') and 'Ana' in n)))).pages[0].extract_text()
        self.assertIn('Ana', texto)

    def test_escogidos_y_junto(self):
        z = self._zip({'tipos': ['informes', 'hojas'], 'modo': 'junto', 'personas': [f'e{self.estudiantes[0].id}']})
        self.assertEqual(sorted(z.namelist()), ['Hojas calificadas - Simulacro Lectura crítica.pdf',
                                                'Hojas calificadas - Simulacro Matemáticas.pdf',
                                                'Informes por estudiante.pdf'])

    def test_sin_escoger(self):
        r = self.c.post(f'/puntoexacto/unida/{self.u.pk}/descargar/', {'tipos': ['informes']})
        self.assertRedirects(r, f'/puntoexacto/unida/{self.u.pk}/', fetch_redirect_response=False)


class ColoresInstitucionales(InformesIcfes):
    """Los informes toman los colores de la paleta del portal del colegio."""

    test_puntajes_niveles_y_percentil = test_unir_examenes = test_pdf_general_y_por_estudiante = None

    def tema(self):
        from django.test import RequestFactory
        from .views_informes import _tema
        r = RequestFactory().get('/')
        self.a.refresh_from_db()
        r.colegio = self.a
        return _tema(r)

    def poner(self, **colores):
        for k, v in colores.items():
            setattr(self.a, k, v)
        self.a.save()

    def test_el_principal_es_la_barra_superior(self):
        self.poner(color_topbar='#7a1020', color_topbar_texto='#ffffff', color_primario='#d4a017')
        t = self.tema()
        self.assertEqual(t['primario'], '#7a1020')
        self.assertEqual(t['texto'], '#ffffff')
        self.assertEqual(t['secundario'], '#d4a017')

    def test_primario_por_defecto_no_cuenta_como_segundo(self):
        self.poner(color_primario='#0D6EFD', color_topbar='#14532d', color_topbar_texto='#ffffff',
                   color_secundario='#6C757D', color_footer='#b91c1c')
        t = self.tema()
        self.assertEqual(t['primario'], '#14532d')
        self.assertEqual(t['secundario'], '#b91c1c')

    def test_texto_ilegible_se_corrige(self):
        self.poner(color_topbar='#0b3d91', color_topbar_texto='#0a0a40')      # azul oscuro con texto casi igual
        t = self.tema()
        self.assertEqual(t['primario'], '#0b3d91')
        self.assertEqual(t['texto'], '#ffffff')

    def test_barra_blanca_usa_el_primario(self):
        self.poner(color_topbar='#ffffff', color_primario='#7a1020', color_texto_primario='#ffffff')
        self.assertEqual(self.tema()['primario'], '#7a1020')

    def test_los_pdf_llevan_los_colores(self):
        import io
        self.poner(color_topbar='#7a1020', color_primario='#d4a017')
        from django.template.loader import render_to_string
        from . import informes as INF2
        from .views_informes import _ctx_general
        from django.test import RequestFactory
        r = RequestFactory().get('/')
        r.colegio = self.a
        r.user = self.u_docente
        html = render_to_string('puntoexacto/informe_general_pdf.html', _ctx_general(r, INF2.construir([self.mat])))
        self.assertIn('#7a1020', html)
        self.assertIn('#d4a017', html)
        pdf = self.c.get(f'/puntoexacto/{self.mat.id}/informe/estudiantes/')
        self.assertTrue(pdf.content.startswith(b'%PDF'))


class DocenteSinColegio(ColegioDePrueba):
    """Plan individual: el informe sale con el color, el logo y las líneas de «Mi encabezado»."""

    def test_color_y_encabezado_del_docente(self):
        import io
        from django.contrib.auth.models import User
        from django.core.files.base import ContentFile
        from django.test import Client, RequestFactory
        from PIL import Image
        from materiales.models import EncabezadoDocente
        from salon_digital.models import Cuenta
        from .views_informes import _institucion, _tema
        u = User.objects.create_user('profe_ind', password='x', first_name='Laura', last_name='Ríos')
        Cuenta.objects.create(usuario=u, slug='laura', nombre_publico='Laura Ríos', estado='verificada',
                              plan='ilimitado', institucion='I. E. Los Andes')
        enc = EncabezadoDocente.objects.create(usuario=u, config={'color': '#0f5132', 'lineas': [
            {'texto': 'Laura Ríos · Matemáticas', 'negrilla': True, 'tam': 'grande'}]})
        b = io.BytesIO(); Image.new('RGB', (40, 40), (200, 0, 0)).save(b, 'PNG')
        enc.logo.save('escudo.png', ContentFile(b.getvalue()))
        r = RequestFactory().get('/')
        r.user = u
        t = _tema(r)
        self.assertEqual(t['primario'], '#0f5132')
        self.assertTrue(t['logo'].startswith('data:image/png;base64,'))
        self.assertEqual(t['encabezado'], enc)
        self.assertEqual(_institucion(r), 'I. E. Los Andes')
        from django.template.loader import render_to_string
        html = render_to_string('puntoexacto/informe_general_pdf.html',
                                {'d': {'titulo': 'Prueba', 'examenes': [], 'areas': [], 'preguntas': []},
                                 'r': {}, 'tema': t, 'institucion': 'I. E. Los Andes'})
        self.assertIn('Laura Ríos · Matemáticas', html)
        self.assertIn('#0f5132', html)
        self.assertIn('enc-docente', html)

    def test_sin_mi_encabezado_sale_el_azul(self):
        from django.contrib.auth.models import User
        from django.test import RequestFactory
        from .views_informes import _tema
        r = RequestFactory().get('/')
        r.user = User.objects.create_user('otro', password='x')
        t = _tema(r)
        self.assertEqual(t['primario'], '#1e3a8a')
        self.assertIsNone(t['encabezado'])


class InformesPorNota(InformesIcfes):
    """El otro tipo de informe: por nota, con la escala de valoración del área (sin unir exámenes)."""

    test_puntajes_niveles_y_percentil = test_unir_examenes = test_pdf_general_y_por_estudiante = None

    def test_desempenos_con_la_escala_del_colegio(self):
        from . import informes_nota as INFN
        d = INFN.construir(self.mat)
        por = {f['nombre'].split()[-1]: f for f in d['filas']}
        self.assertEqual(por['Ana']['nota'], self.mat.nota_maxima)
        self.assertEqual(por['Ana']['nivel']['nombre'], 'SUPERIOR')
        self.assertEqual(por['Caro']['nivel']['nombre'], 'BAJO')
        self.assertFalse(d['referencia'])                           # usa la escala del colegio, no la de referencia
        r = d['total']['resumen']
        self.assertEqual(r['n'], 3)
        self.assertEqual(sum(x['n'] for x in r['distribucion']), 3)
        self.assertEqual(r['aprobados'] + r['reprobados'], 3)
        self.assertEqual(len(por['Caro']['falladas']), 4)
        self.assertIn('sin marcar', [x['marcada'] for x in por['Caro']['falladas']])

    def test_pdf_por_nota(self):
        import io
        from pypdf import PdfReader
        r = self.c.get(f'/puntoexacto/{self.mat.id}/informe/?estilo=nota')
        self.assertEqual(r['Content-Type'], 'application/pdf')
        texto = ''.join(p.extract_text() for p in PdfReader(io.BytesIO(r.content)).pages)
        self.assertIn('POR NOTA', texto)
        self.assertIn('Prueba Beto', texto)
        self.assertIn('SUPERIOR', texto)
        r = self.c.get(f'/puntoexacto/{self.mat.id}/informe/estudiantes/?estilo=nota')
        self.assertEqual(len(PdfReader(io.BytesIO(r.content)).pages), 3)      # una página por estudiante
        clave = f'e{self.estudiantes[0].id}'
        self.assertTrue(self.c.get(f'/puntoexacto/{self.mat.id}/informe/estudiante/{clave}/?estilo=nota').content.startswith(b'%PDF'))
        pagina = self.c.get(f'/puntoexacto/{self.mat.id}/resultados/')
        self.assertContains(pagina, 'Por nota (escala de valoración)')
        self.assertContains(pagina, 'Estilo ICFES')

    def test_zip_por_nota(self):
        import io
        import zipfile
        ids = list(self.mat.hojas.values_list('id', flat=True))
        r = self.c.post(f'/puntoexacto/{self.mat.id}/informes/descargar/',
                        {'tipos': ['general', 'informes', 'cursos'], 'modo': 'separado', 'hojas': ids, 'estilo': 'nota'})
        nombres = sorted(zipfile.ZipFile(io.BytesIO(r.content)).namelist())
        self.assertIn('Informe por nota (total).pdf', nombres)
        self.assertEqual(len([n for n in nombres if n.startswith('Informes por estudiante/')]), 3)

    def test_sin_escala_usa_la_de_referencia(self):
        from notas.models import EscalaValoracion
        from . import informes_nota as INFN
        EscalaValoracion.objects.filter(colegio=self.a).delete()
        d = INFN.construir(self.mat)
        self.assertTrue(d['referencia'])
        self.assertEqual([n['nombre'] for n in d['niveles']], ['BAJO', 'BÁSICO', 'ALTO', 'SUPERIOR'])
