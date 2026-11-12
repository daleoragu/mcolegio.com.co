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
