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


class JuegosEnLaSalaYEnVivo(MisJuegos):
    def test_compartir_en_la_sala_probar_e_importar(self):
        from chat.models import Publicacion
        from chat.views_colegas import perfil_de
        from django.utils import timezone
        self.crear()
        j = JuegoMaterial.objects.get()
        p = perfil_de(self.u); p.normas_aceptadas = timezone.now(); p.save()
        r = self.c.get(f'/chat/colegas/muro/?escribir=1&compartir=j{j.pk}')
        self.assertContains(r, f'value="j{j.pk}" selected')
        self.c.post('/chat/colegas/muro/', {'tipo': 'actividad', 'pagina': f'j{j.pk}', 'titulo': '', 'texto': '', 'visibilidad': 'todos'})
        pub = Publicacion.objects.get()
        self.assertEqual(pub.juego, j)
        # Otro docente lo prueba e importa
        otro = User.objects.create_user('beto')
        Cuenta.objects.create(usuario=otro, slug='beto', nombre_publico='Beto', estado='verificada', plan='ilimitado')
        c2 = Client(HTTP_HOST='localhost'); c2.force_login(otro)
        r = c2.get('/chat/colegas/muro/')
        self.assertContains(r, 'Importar a Mis juegos')
        self.assertContains(c2.get(f'/materiales/juegos/sala/{pub.pk}/'), 'aula/juegos/laberinto.js')
        c2.post(f'/materiales/juegos/sala/{pub.pk}/importar/')
        copia = JuegoMaterial.objects.get(propietario=otro)
        self.assertEqual(copia.preguntas, j.preguntas)
        pub.refresh_from_db()
        self.assertEqual(pub.copias, 1)

    def test_jugarlo_en_vivo(self):
        from aula.models import Cuestionario, SesionVivo
        g = Grupo.objects.create(propietario=self.cuenta, nombre='7-01')
        aula = Aula.objects.create(grupo=g)
        self.crear()
        j = JuegoMaterial.objects.get()
        r = self.c.post(f'/materiales/juegos/{j.pk}/vivo/', {'aula': aula.pk})
        q = Cuestionario.objects.get(aula=aula)
        s = SesionVivo.objects.get(cuestionario=q)
        self.assertRedirects(r, f'/aula/{aula.pk}/vivo/{s.pk}/', fetch_redirect_response=False)
        self.assertEqual(q.preguntas.count(), 2)
        self.assertTrue(q.preguntas.first().opciones.filter(correcta=True).exists())

    def test_boton_de_ia_en_el_editor(self):
        self.assertContains(self.c.get('/materiales/juegos/'), "ia: '/materiales/ia/actividad/'")


class ColorPorArea(ColorDocumentos):
    def test_color_por_area(self):
        import json
        self.c.post('/materiales/encabezado/', {'config': json.dumps({'color': '#7c3aed', 'por_area': [
            {'area': 'Matemáticas', 'color': '#2563eb'}, {'area': 'Ciencias naturales', 'color': '#15803d'}]})})
        enc = EncabezadoDocente.objects.get(usuario=self.u)
        self.assertEqual(enc.color_para('matematicas'), '#2563eb')
        self.assertEqual(enc.color_para('Ciencias Naturales y Ed. Ambiental'), '#15803d')
        self.assertEqual(enc.color_para('Inglés'), '#7c3aed')            # sin regla: el color general
        self.c.post('/materiales/nuevo/', {'tipo': 'taller', 'area': 'Matemáticas'})
        doc = Documento.objects.get(propietario=self.u)
        self.assertEqual(doc.contenido['opciones']['color'], '#2563eb')
        self.assertContains(self.c.get(f'/materiales/{doc.pk}/'), 'mm-colores-area')


class FormatosGenericos(ColorDocumentos):
    def test_crear_cada_formato_y_exportar(self):
        from materiales import exportar, plantillas
        for tipo in plantillas.FORMATOS:
            self.c.post('/materiales/nuevo/', {'tipo': tipo})
            doc = Documento.objects.filter(propietario=self.u, tipo=tipo).get()
            r = self.c.get(f'/materiales/{doc.pk}/')
            self.assertContains(r, 'Llenar el formato')
            self.assertTrue(any(b['tipo'] == 'tabla' for b in doc.contenido['bloques']), tipo)
            self.assertTrue(exportar.docx(doc).startswith(b'PK'), tipo)
        piar = Documento.objects.get(propietario=self.u, tipo='piar')
        self.assertTrue(any(b.get('privada') for b in piar.contenido['bloques']))
        self.assertContains(self.c.get('/materiales/'), 'Formatos para llenar')

    def test_llenar_solo_celdas_vacias_y_nunca_las_privadas(self):
        import json
        from unittest import mock
        from materiales import ia
        self.c.post('/materiales/nuevo/', {'tipo': 'piar'})
        doc = Documento.objects.get(propietario=self.u, tipo='piar')
        contenido = B.limpiar(doc.contenido, set())
        privada = next(b for b in contenido['bloques'] if b.get('privada'))
        ajustes = next(b for b in contenido['bloques'] if b['tipo'] == 'tabla' and b['filas'][0][0] == 'Área')
        ajustes['filas'][1][1] = 'Lo escribió el docente'
        doc.contenido = contenido
        doc.save()
        enviados = []

        def falsa_api(sistema, mensaje, tokens):
            enviados.append(mensaje)
            respuesta = {'tablas': {
                ajustes['id']: [[c or 'IA' for c in f] for f in ajustes['filas']],
                privada['id']: [['Nombre del estudiante', 'Juanito Pérez']],      # intento de llenar la privada: no entra
            }}
            return json.dumps(respuesta), 100, 100
        with mock.patch.object(ia, 'disponible', return_value=True), mock.patch.object(ia, '_llamar_api', side_effect=falsa_api), \
                mock.patch('materiales.creditos.cobrar') as cobrar, mock.patch('materiales.creditos.anotar_consumo'):
            cobrar.return_value = None
            r = self.c.post('/materiales/ia/llenar/', json.dumps({'documento': doc.pk, 'tema': 'fracciones'}), content_type='application/json')
        j = r.json()
        self.assertTrue(j['ok'], j)
        self.assertNotIn('Nombre del estudiante', enviados[0])           # la tabla privada no se envió
        nuevos = {b['id']: b for b in j['reemplazar']}
        self.assertEqual(nuevos[ajustes['id']]['filas'][1][1], 'Lo escribió el docente')
        self.assertEqual(nuevos[ajustes['id']]['filas'][1][2], 'IA')
        self.assertEqual(nuevos[privada['id']]['filas'][0][1], '')


class ColorDeLetraYRelleno(ColorDocumentos):
    def test_texto_con_color_y_relleno(self):
        L = B.limpiar_html
        self.assertEqual(L('<p>Hola <span style="color: rgb(220, 38, 38); background-color: rgb(254, 240, 138);">x</span></p>'),
                         '<p>Hola <span style="color:#dc2626;background-color:#fef08a">x</span></p>')
        self.assertEqual(L('<font color="#2563EB">azul</font>'), '<span style="color:#2563eb">azul</span>')
        # Nada fuera de los dos colores: sin posiciones, sin url(), sin eventos
        self.assertEqual(L('<span style="position:fixed;background:url(javascript:x)" onclick="y()">z</span>'), 'z')
        self.assertEqual(L('<span style="background-color:transparent">t</span>'), 't')
        self.assertEqual(L('<span><b>a</b></span>c'), '<b>a</b>c')

    def test_celdas_con_relleno_en_pdf_y_word(self):
        import io
        import zipfile
        from materiales import exportar
        contenido = {'bloques': [{'id': 't1', 'tipo': 'tabla', 'encabezado': True, 'filas': [['Momento', 'Actividad'], ['Inicio', 'Lectura']],
                                  'estilos': {'1-0': {'f': '#BFDBFE', 'c': 'rgb(31,58,104)'}, '9-9': {'f': '#000000'}, '0-0': {'f': 'red'}}},
                                 {'id': 'x', 'tipo': 'texto', 'html': '<p><span style="color:#dc2626">Rojo</span></p>'}]}
        limpio = B.limpiar(contenido, set())
        self.assertEqual(limpio['bloques'][0]['estilos'], {'1-0': {'f': '#bfdbfe', 'c': '#1f3a68'}})   # fuera la celda que no existe y el color inválido
        doc = Documento(propietario=self.u, titulo='Prueba', tipo='planeacion', contenido=limpio)
        ctx = exportar.contexto(doc)
        self.assertEqual(ctx['bloques'][0]['filas_estilo'][1][0], ('Inicio', 'background:#bfdbfe;color:#1f3a68'))
        x = zipfile.ZipFile(io.BytesIO(exportar.docx(doc))).read('word/document.xml').decode().upper()
        self.assertIn('BFDBFE', x)
        self.assertIn('DC2626', x)
        doc.save()
        self.assertContains(self.c.get(f'/materiales/{doc.pk}/'), 'mm-colorbtn')
