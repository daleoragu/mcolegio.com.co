"""Mis juegos (crear, probar y enviar sin grupo) y el color de los documentos."""
from django.contrib.auth.models import User
from django.test import Client, TestCase

from aula.models import Aula, JuegoAula, ResultadoJuegoAula
from materiales import bloques as B
from materiales.models import Documento, EncabezadoDocente, JuegoMaterial
from salon_digital.models import Cuenta, Grupo, Integrante

PREGUNTAS = '1. ¿Cuánto es 1/2 + 1/2?\nA) 2\n*B) 1\nC) 1/4\n\n2. ¿Qué es mayor?\n*A) 1/2\nB) 1/3\nC) 1/4'


class MisJuegos(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.u = User.objects.create_user('profe', password='x', first_name='Ana')
        cls.cuenta = Cuenta.objects.create(usuario=cls.u, slug='ana', nombre_publico='Ana', estado='verificada', plan='ilimitado')

    def setUp(self):
        self.c = Client(HTTP_HOST='localhost')
        self.c.force_login(self.u)

    def crear(self, **datos):
        datos = {'titulo': 'Fracciones', 'tipo': 'laberinto', 'preguntas': PREGUNTAS, 'segundos': '20', 'velocidad': 'normal', **datos}
        return self.c.post('/materiales/juegos/', datos)

    def test_crear_y_probar_sin_grupo(self):
        self.assertFalse(Grupo.objects.exists())
        r = self.c.get('/materiales/juegos/')
        self.assertContains(r, 'Mis juegos')
        self.assertContains(r, 'Escape de la selva')                # juegos de lógica para probar
        self.crear()
        j = JuegoMaterial.objects.get()
        self.assertEqual(len(j.preguntas), 2)
        r = self.c.get(f'/materiales/juegos/{j.pk}/probar/')
        self.assertContains(r, 'aula/juegos/laberinto.js')
        self.assertContains(r, 'prueba del docente')
        self.assertContains(r, 'const URL_RESULTADO = null')       # la prueba no guarda nota
        for url in ('/materiales/juegos/ejemplo/penaltis/', '/materiales/juegos/ejemplo/tanques/', '/materiales/juegos/ejemplo/animaplano/',
                    '/materiales/juegos/logica/tangram/', '/materiales/juegos/logica/selva_movil/'):
            self.assertEqual(self.c.get(url).status_code, 200, url)
        self.assertEqual(self.c.get('/materiales/juegos/ejemplo/otro/').status_code, 404)

    def test_preguntas_malas_no_se_guardan(self):
        r = self.crear(preguntas='1. Sin opciones')
        self.assertEqual(r.status_code, 200)
        self.assertFalse(JuegoMaterial.objects.exists())
        self.assertContains(r, 'Revise las preguntas')

    def test_enviar_editar_y_actualizar_copias(self):
        g1 = Grupo.objects.create(propietario=self.cuenta, nombre='7-01')
        g2 = Grupo.objects.create(propietario=self.cuenta, nombre='7-02')
        a1, a2 = Aula.objects.create(grupo=g1), Aula.objects.create(grupo=g2)
        self.crear()
        j = JuegoMaterial.objects.get()
        self.c.post(f'/materiales/juegos/{j.pk}/enviar/', {'aulas': [a1.pk, a2.pk]})
        self.assertEqual(JuegoAula.objects.count(), 2)
        j.refresh_from_db()
        self.assertEqual(set(j.enviados), {str(a1.pk), str(a2.pk)})
        # En 7-01 ya jugó una estudiante: allá no se cambian las preguntas; en 7-02 sí
        copia1 = JuegoAula.objects.get(aula=a1)
        ResultadoJuegoAula.objects.create(juego=copia1, integrante=Integrante.objects.create(grupo=g1, nombres='Eva', apellidos='Paz'),
                                          aciertos=1, total=2)
        nuevo = PREGUNTAS + '\n\n3. ¿2 + 2?\n*A) 4\nB) 5'
        self.c.post(f'/materiales/juegos/{j.pk}/', {'titulo': 'Fracciones 2', 'tipo': 'laberinto', 'preguntas': nuevo, 'segundos': '20'})
        self.assertEqual(len(JuegoAula.objects.get(aula=a2).preguntas), 3)
        self.assertEqual(len(JuegoAula.objects.get(aula=a1).preguntas), 2)
        # Volver a enviar a 7-01 crea otro juego (el anterior conserva sus notas)
        self.c.post(f'/materiales/juegos/{j.pk}/enviar/', {'aulas': [a1.pk]})
        self.assertEqual(JuegoAula.objects.filter(aula=a1).count(), 2)

    def test_no_se_tocan_juegos_ni_clases_ajenas(self):
        otro = User.objects.create_user('otro')
        cuenta2 = Cuenta.objects.create(usuario=otro, slug='otro', nombre_publico='Otro', estado='verificada')
        ajena = Aula.objects.create(grupo=Grupo.objects.create(propietario=cuenta2, nombre='9-01'))
        j_ajeno = JuegoMaterial.objects.create(propietario=otro, titulo='Ajeno', preguntas=[])
        self.assertEqual(self.c.get(f'/materiales/juegos/{j_ajeno.pk}/probar/').status_code, 404)
        self.crear()
        j = JuegoMaterial.objects.get(propietario=self.u)
        self.c.post(f'/materiales/juegos/{j.pk}/enviar/', {'aulas': [ajena.pk]})
        self.assertFalse(JuegoAula.objects.filter(aula=ajena).exists())


class ColorDocumentos(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.u = User.objects.create_user('profe', password='x')
        Cuenta.objects.create(usuario=cls.u, slug='ana', nombre_publico='Ana', estado='verificada', plan='ilimitado')

    def setUp(self):
        self.c = Client(HTTP_HOST='localhost')
        self.c.force_login(self.u)

    def test_color_valido_y_mezcla(self):
        self.assertEqual(B.color_valido('#15803D'), '#15803d')
        self.assertEqual(B.color_valido('red; background:url(x)'), B.COLOR_DEFECTO)
        self.assertEqual(B.mezclar('#000000', .5), '#808080')
        self.assertEqual(B.limpiar({'opciones': {'color': '#be185d'}}, set())['opciones']['color'], '#be185d')

    def test_el_pdf_y_el_word_usan_el_color(self):
        from materiales import exportar
        doc = Documento(propietario=self.u, titulo='Guía', tipo='guia',
                        contenido={'bloques': [{'tipo': 'seccion', 'titulo': 'Exploración', 'indicacion': ''}],
                                   'opciones': {'color': '#15803d'}})
        ctx = exportar.contexto(doc)
        self.assertEqual(ctx['color'], '#15803d')
        from django.template.loader import render_to_string
        html = render_to_string('materiales/documento_pdf.html', dict(ctx, colegio=None, encabezado=None, marca='', pie_lineas=[], rutas={}))
        self.assertIn('#15803d', html)
        self.assertNotIn('#1f3a68', html)

    def test_mi_color_por_defecto_en_documentos_nuevos(self):
        import json
        self.c.post('/materiales/encabezado/', {'config': json.dumps({'lineas': [{'texto': 'IE Zona Norte'}], 'color': '#7c3aed'})})
        self.assertEqual(EncabezadoDocente.objects.get(usuario=self.u).color, '#7c3aed')
        self.c.post('/materiales/nuevo/', {'tipo': 'taller'})
        doc = Documento.objects.get(propietario=self.u)
        self.assertEqual(doc.contenido['opciones']['color'], '#7c3aed')
        self.assertContains(self.c.get(f'/materiales/{doc.pk}/'), 'id="mm-colores"')
