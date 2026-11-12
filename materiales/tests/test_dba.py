"""DBA oficiales: catálogo, selector en el editor, filtro de la biblioteca y material semilla de Matemáticas 6.º y 7.º."""
from io import StringIO

from django.core.management import call_command
from django.test import SimpleTestCase

from materiales import bloques as B
from materiales import calificar as C
from materiales.dba import catalogo as K
from materiales.models import Documento, Imagen, MaterialCompartido
from materiales.semilla import armar, banco
from notas.tests.base import ColegioDePrueba


class Catalogo(SimpleTestCase):
    def test_matematicas_completo(self):
        cuenta = {g: len(K.dbas('Matemáticas', g)) for g in range(1, 12)}
        self.assertEqual(sum(cuenta.values()), 119)
        self.assertEqual((cuenta[6], cuenta[7]), (12, 9))
        for g in range(1, 12):
            self.assertEqual([d['n'] for d in K.dbas('Matemáticas', g)], list(range(1, cuenta[g] + 1)))

    def test_nombres_y_codigos(self):
        self.assertEqual(K.clave_area('Geometría'), 'MAT')
        self.assertEqual(K.clave_area('Ética y valores'), '')
        for texto, g in (('6.º', 6), ('Sexto', 6), ('601', 6), ('1001', 10), ('', None), ('Transición', None)):
            self.assertEqual(K.grado_num(texto), g, texto)
        d = K.buscar('MAT-7-4')
        self.assertEqual((d['grado'], d['n']), (7, 4))
        self.assertIn('escalas', d['enunciado'])
        self.assertTrue(K.etiqueta('MAT-7-4').startswith('DBA 4 · Matemáticas 7.º: Utiliza escalas'))
        self.assertIsNone(K.buscar('MAT-7-40')); self.assertIsNone(K.buscar('xx'))

    def test_semilla_valida(self):
        for g, n in ((6, 12), (7, 9)):
            docs = armar.documentos(g)
            self.assertEqual(len(docs), 2 * n)
            for d in docs:
                for b in d['bloques']:
                    if b['tipo'] == 'pregunta' and b['modo'] == 'numerica':
                        self.assertIsNotNone(C.numero(b['respuesta']), b['enunciado'])
                    if b['tipo'] == 'pregunta' and b['modo'] == 'unica':
                        self.assertEqual(len(set(b['opciones'])), len(b['opciones']))
                normales = [b for b in d['bloques'] if b['tipo'] != '_grafica']
                self.assertEqual(len(B.limpiar({'bloques': normales}, set())['bloques']), len(normales), d['titulo'])
        # Cada guía lleva el DBA oficial tal cual
        guia = armar.documentos(7)[6]
        self.assertIn(K.buscar('MAT-7-4')['enunciado'], guia['bloques'][1]['html'])

    def test_banco_etiquetado(self):
        r6, r7 = banco.resumen(6), banco.resumen(7)
        self.assertEqual(r6[2]['MCM'], 3)
        self.assertEqual(r7[1]['Números enteros'], 6)
        olimpiada = banco.bloques(7, 1)
        self.assertEqual(len(olimpiada), 10)
        self.assertTrue(all(b['modo'] == 'unica' and 0 <= b['correcta'] < len(b['opciones']) for b in olimpiada))

    def test_menos_tipografico(self):
        self.assertEqual(C.numero('−7'), C.numero('-7'))


class EnLaPlataforma(ColegioDePrueba):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def test_selector_del_editor(self):
        c = self.cliente(self.u_docente)
        j = c.get('/materiales/dba/', {'area': 'Matemáticas', 'grado': '601'}).json()
        self.assertTrue(j['tiene']); self.assertEqual(j['grado'], 6); self.assertEqual(len(j['dbas']), 12)
        self.assertEqual(j['dbas'][2]['codigo'], 'MAT-6-3')
        j = c.get('/materiales/dba/', {'area': 'Ética', 'grado': '6'}).json()
        self.assertFalse(j['tiene']); self.assertEqual(j['dbas'], [])

    def test_compartir_con_dba_y_filtrar(self):
        c = self.cliente(self.super)
        doc = Documento.objects.create(propietario=self.super, colegio=self.a, titulo='Escalas', tipo='taller', area='Matemáticas',
                                       grado='7.º', contenido={'bloques': [{'id': 'x1', 'tipo': 'texto', 'html': '<p>Hola</p>'}]})
        c.post(f'/materiales/{doc.pk}/compartir/', {'alcance': 'libre', 'acepto': 'on', 'dba_codigo': 'MAT-7-4'})
        m = MaterialCompartido.objects.get(documento=doc)
        self.assertEqual(m.dba_codigo, 'MAT-7-4'); self.assertTrue(m.dba.startswith('DBA 4 · Matemáticas 7.º'))
        # Un código inventado no se guarda
        c.post(f'/materiales/{doc.pk}/compartir/', {'alcance': 'libre', 'acepto': 'on', 'dba_codigo': 'MAT-7-99', 'dba': 'otro'})
        m.refresh_from_db(); self.assertEqual(m.dba_codigo, '')
        c.post(f'/materiales/{doc.pk}/compartir/', {'alcance': 'libre', 'acepto': 'on', 'dba_codigo': 'MAT-7-4'})
        otro = Documento.objects.create(propietario=self.super, colegio=self.a, titulo='Ecuaciones', tipo='taller', area='Matemáticas', grado='7.º',
                                        contenido={'bloques': [{'id': 'x1', 'tipo': 'texto', 'html': '<p>Hola</p>'}]})
        c.post(f'/materiales/{otro.pk}/compartir/', {'alcance': 'libre', 'acepto': 'on', 'dba_codigo': 'MAT-7-7'})
        ver = lambda q: sorted(x.titulo for x in c.get('/materiales/biblioteca/', q).context['materiales'])
        self.assertEqual(ver({'area': 'Matemáticas', 'grado': '7.º'}), ['Ecuaciones', 'Escalas'])
        self.assertEqual(ver({'area': 'Matemáticas', 'grado': '7.º', 'dba': 'MAT-7-4'}), ['Escalas'])
        r = c.get('/materiales/biblioteca/', {'area': 'Matemáticas', 'grado': '7.º'})
        self.assertContains(r, 'MAT-7-7')

    def test_cargar_semilla(self):
        with self.assertRaises(Exception):
            call_command('cargar_semilla_matematicas', '--usuario', 'profe', '--grados', '7', '--publicar', stdout=StringIO())
        call_command('cargar_semilla_matematicas', '--usuario', 'profe', '--grados', '7', '--colegio', 'a', stdout=StringIO())
        docs = Documento.objects.filter(propietario=self.u_docente)
        self.assertEqual(docs.count(), 18)
        self.assertEqual(MaterialCompartido.objects.count(), 0)
        # Las gráficas quedan como imágenes editables del docente
        imgs = Imagen.objects.filter(propietario=self.u_docente)
        self.assertEqual(imgs.count(), 3)
        self.assertTrue(all(i.grafica for i in imgs))
        guia = docs.get(titulo__startswith='Vistas de objetos')
        self.assertEqual([b['tipo'] for b in guia.contenido['bloques']].count('imagen'), 1)
        self.assertEqual(guia.grado, '7.º')
        c = self.cliente(self.u_docente)
        self.assertEqual(c.get(f'/materiales/{guia.pk}/').status_code, 200)
        self.assertEqual(c.get(f'/materiales/{guia.pk}/pdf/').status_code, 200)
        # El dueño publica de una vez en el banco libre, con su DBA
        call_command('cargar_semilla_matematicas', '--usuario', 'dueno', '--grados', '6', '--publicar', stdout=StringIO())
        pub = MaterialCompartido.objects.filter(alcance='libre', estado='publicado')
        self.assertEqual(pub.count(), 24)
        self.assertEqual(sorted({m.dba_codigo for m in pub}), sorted(f'MAT-6-{n}' for n in range(1, 13)))


class SemillaPrimero(ColegioDePrueba):
    """Matemáticas 1.º: imágenes del banco (pendientes, colecciones exactas, pictogramas) y los dibujos de mcolegio."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def _banco(self, carpeta, ids):
        from PIL import Image as PILImage, ImageDraw
        for i in ids:
            im = PILImage.new('RGB', (400, 400), 'white')
            ImageDraw.Draw(im).ellipse([100, 100, 300, 300], fill=(230, 57, 70))
            im.save(f'{carpeta}/{i}.png')

    def test_dibujos_exactos_en_png(self):
        from pathlib import Path
        from materiales.semilla import dibujos as D
        ids = {b['img'] for d in armar.documentos(1) for b in d['bloques'] if b['tipo'] == '_imagen' and b['img'].startswith('d-')}
        self.assertGreater(len(ids), 20)
        for i in ids:
            self.assertTrue((Path(armar.CARPETA_DIBUJOS) / D.archivo(i)).exists(), f'falta el PNG de {i}: corra png_dibujos.py')
            self.assertIn('<svg', D.generar(i))

    def test_cargar_con_imagenes_pendientes_y_ponerlas(self):
        import tempfile
        from materiales.semilla import imagenes as I
        from PIL import Image as PILImage
        with tempfile.TemporaryDirectory() as tmp:
            self._banco(tmp, ['m1-manzana', 'm1-mango', 'm1-banano'])           # solo algunas
            call_command('cargar_semilla', '--usuario', 'profe', '--area', 'MAT', '--grados', '1', '--colegio', 'a',
                         '--imagenes', tmp, stdout=StringIO())
            docs = Documento.objects.filter(propietario=self.u_docente, grado='1.º')
            self.assertEqual(docs.count(), 20)
            guia = docs.get(titulo='Los números están en todas partes')
            self.assertEqual(guia.contenido['opciones']['letra'], 14)             # letra grande en 1.º
            tipos = [b['tipo'] for b in guia.contenido['bloques']]
            self.assertIn('imagen', tipos)                                         # dibujos de mcolegio y la colección de manzanas
            pendientes = [b for b in guia.contenido['bloques'] if b['tipo'] == 'recuadro' and b['titulo'].startswith('Imagen pendiente: ')]
            self.assertTrue(any(b['titulo'] == 'Imagen pendiente: m1-uso-tienda' for b in pendientes))
            # La colección de 4 manzanas es exacta: una imagen con 4 manzanas en fila
            proporciones = []
            for b in guia.contenido['bloques']:
                if b['tipo'] == 'imagen':
                    with PILImage.open(Imagen.objects.get(pk=b['imagen']).archivo) as im:
                        proporciones.append(round(im.width / im.height, 1))
            self.assertIn(3.6, proporciones)                                       # 4 manzanas en una fila
            # Llegan las demás imágenes: se ponen solas
            self._banco(tmp, [x['id'] for x in I.catalogo() if x['origen'] == 'ia'])
            out = StringIO()
            call_command('poner_imagenes_semilla', '--imagenes', tmp, stdout=out)
            self.assertIn('Quedan 0 pendientes', out.getvalue())
            guia.refresh_from_db()
            self.assertFalse(any(b['tipo'] == 'recuadro' and b['titulo'].startswith('Imagen pendiente') for b in guia.contenido['bloques']))
            c = self.cliente(self.u_docente)
            self.assertEqual(c.get(f'/materiales/{guia.pk}/pdf/').status_code, 200)

    def test_catalogos_dba_activos(self):
        for area, n in (('Lengua Castellana', 8), ('Ciencias Naturales', 4), ('Ciencias Sociales', 8), ('Matemáticas', 10)):
            self.assertEqual(len(K.dbas(area, '1.º')), n, area)
        ev = K.buscar('MAT-1-10')['evidencias']
        self.assertEqual(ev[0], 'Identifica en fichas u objetos reales los valores de la variable en estudio.')
        self.assertTrue(K.buscar('SOC-6-5')['evidencias'][2].startswith('Compara la estructura social, política y económica'))


class PdfConEmojis(SimpleTestCase):
    def test_emoji_nuevo_no_tumba_el_pdf(self):
        from weasyprint import HTML
        from materiales.exportar import escribir_pdf
        self.assertTrue(escribir_pdf(HTML(string='<p>Imagen 🖼 y corazón 🫶</p>')).startswith(b'%PDF'))


class SemillaOtrasAreas(ColegioDePrueba):
    def test_lenguaje_naturales_sociales_1(self):
        from materiales.semilla import imagenes as I
        for area, n, nombre in (('LEN', 16, 'Lenguaje'), ('NAT', 8, 'Ciencias Naturales'), ('SOC', 16, 'Ciencias Sociales')):
            call_command('cargar_semilla', '--usuario', 'profe', '--area', area, '--grados', '1', '--colegio', 'a', stdout=StringIO())
            docs = Documento.objects.filter(propietario=self.u_docente, area=nombre)
            self.assertEqual(docs.count(), n, area)
            guia = docs.filter(tipo='guia_momentos').first()
            self.assertIn(f'(MEN, {nombre})', str(guia.contenido))
        # Toda imagen que piden las guías está en el catálogo con su prompt
        ids = {b['img'].split('×')[0] for (a, g) in armar.MODULOS if g == 1 for d in armar.documentos(g, a) for b in d['bloques']
               if b['tipo'] == '_imagen' and not b['img'].startswith(('d-', 'pict:'))}
        self.assertTrue(all(I.por_id(i) and I.por_id(i)['prompt'] for i in ids))
        self.assertEqual(K.buscar('SOC-1-7')['evidencias'][-1], 'Reconoce la importancia del trabajo en equipo para el logro de las metas comunes.')

    def test_segundo_grado(self):
        for area, n in (('MAT', 22), ('LEN', 16), ('NAT', 8), ('SOC', 16)):
            antes = Documento.objects.filter(propietario=self.u_docente).count()
            call_command('cargar_semilla', '--usuario', 'profe', '--area', area, '--grados', '2', '--colegio', 'a', stdout=StringIO())
            self.assertEqual(Documento.objects.filter(propietario=self.u_docente).count() - antes, n, area)
        self.assertTrue(Documento.objects.filter(grado='2.º', titulo='Números hasta 999: comparo y ordeno').exists())
        self.assertIn('aplicación,', ' '.join(K.buscar('MAT-2-3')['evidencias']))
        self.assertIn('que éstas traen', ' '.join(K.buscar('SOC-2-5')['evidencias']))

    def test_tercero_a_quinto(self):
        esperado = {('MAT', 3): 22, ('LEN', 3): 16, ('NAT', 3): 12, ('SOC', 3): 16, ('MAT', 4): 22, ('LEN', 4): 16, ('NAT', 4): 14,
                    ('SOC', 4): 16, ('MAT', 5): 24, ('LEN', 5): 16, ('NAT', 5): 8, ('SOC', 5): 16}
        for (area, g), n in esperado.items():
            self.assertEqual(len(armar.documentos(g, area)), n, (area, g))
        antes = Documento.objects.count()
        call_command('cargar_semilla', '--usuario', 'profe', '--area', 'MAT', '--grados', '5', '--colegio', 'a', stdout=StringIO())
        self.assertEqual(Documento.objects.count() - antes, 24)
        d = Documento.objects.get(titulo='El plano cartesiano y los mapas')
        self.assertEqual(d.grado, '5.º')
        self.assertNotIn('letra', {k: v for k, v in d.contenido['opciones'].items() if v == 14})   # letra normal desde 4.º
        # Los mapas son oficiales (IGAC), no de IA
        from materiales.semilla import imagenes as I
        self.assertEqual(I.por_id('s5-regiones-naturales')['origen'], 'oficial')
        self.assertIn('IGAC', I.por_id('s5-regiones-naturales')['prompt'])
        self.assertIn('instrumentos', K.buscar('MAT-4-5')['enunciado'])

    def test_sexto_a_noveno(self):
        for (area, g), n in {('MAT', 8): 24, ('MAT', 9): 22, ('LEN', 6): 16, ('LEN', 9): 16, ('NAT', 6): 10, ('NAT', 9): 12, ('SOC', 7): 16, ('SOC', 9): 16}.items():
            self.assertEqual(len(armar.documentos(g, area)), n, (area, g))
        antes = Documento.objects.count()
        call_command('cargar_semilla', '--usuario', 'profe', '--area', 'NAT', '--grados', '9', '--colegio', 'a', stdout=StringIO())
        self.assertEqual(Documento.objects.count() - antes, 12)
        self.assertTrue(Documento.objects.filter(titulo='Genética mendeliana', area='Ciencias Naturales', grado='9.º').exists())
        from materiales.semilla import imagenes as I
        self.assertIn('secundaria', I.por_id('n9-adn')['prompt'])
        self.assertNotIn('6 años', I.por_id('s7-acueducto')['prompt'])
        self.assertIn('Comprende', K.buscar('SOC-7-7')['enunciado'])
