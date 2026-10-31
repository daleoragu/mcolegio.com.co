"""Fase 4: sopa de letras y crucigrama, créditos de IA, acciones fijas, saldo con Wompi y biblioteca."""
import hashlib
import io
import json
import os
import shutil
import tempfile
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings

from aula.models import Aula, Entrega, Instrumento, Tarea
from materiales import bloques as B
from materiales import calificar as C
from materiales import creditos as K
from materiales import juegos as J
from materiales import wompi
from materiales.models import (CuentaIA, Documento, Imagen, MaterialCompartido, MovimientoIA, Recarga)
from notas.models import Docente
from notas.tests.base import ColegioDePrueba

MEDIA = tempfile.mkdtemp(prefix='materiales-f4-')
IA_LISTA = {'ANTHROPIC_API_KEY': 'clave-de-prueba'}
WOMPI = {'WOMPI_PUBLIC_KEY': 'pub_test_x', 'WOMPI_INTEGRITY_SECRET': 'secreto-int', 'WOMPI_EVENTS_SECRET': 'secreto-ev'}


def png():
    from PIL import Image
    salida = io.BytesIO()
    Image.new('RGB', (300, 200), (40, 120, 200)).save(salida, format='PNG')
    return SimpleUploadedFile('g.png', salida.getvalue(), content_type='image/png')


def respuesta_ia(obj):
    """Lo que devolvería el proveedor: (texto, tokens de entrada, tokens de salida)."""
    return (json.dumps(obj, ensure_ascii=False), 1200, 900)


class Juegos(SimpleTestCase):

    def test_sopa(self):
        c = B.limpiar({'bloques': [{'id': 's1', 'tipo': 'pregunta', 'modo': 'sopa',
                                    'palabras': ['Fracción', 'numerador', 'denominador', 'entero', 'mitad', 'x']}]}, set())
        b = c['bloques'][0]
        self.assertEqual(b['palabras'], ['FRACCION', 'NUMERADOR', 'DENOMINADOR', 'ENTERO', 'MITAD'])   # 'X' es muy corta
        self.assertEqual(len(b['ubicaciones']), 5)
        self.assertEqual(len(b['filas']), len(b['filas'][0]))
        # La misma semilla da la misma cuadrícula
        self.assertEqual(B.limpiar({'bloques': [dict(b)]}, set())['bloques'][0]['filas'], b['filas'])
        u = b['ubicaciones'][0]
        celdas = J.celdas_de(u)
        al_reves = [celdas[-1][0], celdas[-1][1], celdas[0][0], celdas[0][1]]
        r = C.calificar(c, {'s1': [al_reves, [0, 0, 0, 1]]})
        self.assertEqual(r['detalle']['s1']['obtenidos'], round(C.Decimal(1) / 5, 2))
        self.assertIn('FRACCION', C.respuesta_correcta_texto(b))

    def test_crucigrama(self):
        c = B.limpiar({'bloques': [{'id': 'c1', 'tipo': 'pregunta', 'modo': 'crucigrama', 'puntos': 4, 'pares': [
            ['río', 'Agua que corre'], ['montaña', 'Gran elevación'], ['mar', 'Agua salada'], ['lago', 'Agua quieta']]}]},
            set())
        b = c['bloques'][0]
        self.assertEqual(len(b['palabras']) + len(b['fuera']), 4)
        celdas = J.celdas_crucigrama(b)
        todo = {f'{f}-{col}': letra.lower() for (f, col), letra in celdas.items()}
        self.assertEqual(C.calificar(c, {'c1': todo})['obtenidos'], C.Decimal(4))
        # Una letra mala daña solo las palabras que pasan por ella
        f, col = next(iter(celdas))
        malo = dict(todo, **{f'{f}-{col}': 'z'})
        self.assertLess(C.calificar(c, {'c1': malo})['obtenidos'], C.Decimal(4))
        tablero = J.tablero_crucigrama(b)
        self.assertEqual(sum(1 for fila in tablero for x in fila if x), len(celdas))


@override_settings(MEDIA_ROOT=MEDIA)
class CreditosYAsistente(ColegioDePrueba):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def test_bolsas_saldo_y_devolucion(self):
        u = self.u_docente
        est = K.estado(u, self.a)
        self.assertEqual((est['plan'], est['dia'], est['mes']), ('premium', 5, 150))
        self.assertEqual(K.cobrar(u, self.a, 'rubrica', 3).bolsa, 'dia')
        self.assertEqual(K.cobrar(u, self.a, 'guia', 8).bolsa, 'mes')      # al día le quedan 2: sale entero del mes
        est = K.estado(u, self.a)
        self.assertEqual((est['dia'], est['mes']), (2, 142))
        with mock.patch.dict(K.CUPOS, {'premium': (0, 0)}):
            with self.assertRaises(K.SinCreditos):
                K.cobrar(u, self.a, 'guia', 8)
            K.abonar(u, 1000)
            with self.assertRaises(K.SinCreditos):           # no se usa el saldo sin permiso
                K.cobrar(u, self.a, 'guia', 8)
            mov = K.cobrar(u, self.a, 'guia', 8, usar_saldo=True)
            self.assertEqual((mov.bolsa, mov.pesos, CuentaIA.objects.get(usuario=u).saldo), ('saldo', -160, 840))
            K.devolver(mov, 'prueba')
            self.assertEqual(CuentaIA.objects.get(usuario=u).saldo, 1000)
            # «Sin preguntar» respeta el tope del mes
            CuentaIA.objects.filter(usuario=u).update(saldo_sin_preguntar=True, tope_mes=100)
            with self.assertRaises(K.SinCreditos):
                K.cobrar(u, self.a, 'guia', 8)
            CuentaIA.objects.filter(usuario=u).update(tope_mes=1000)
            self.assertEqual(K.cobrar(u, self.a, 'guia', 8).bolsa, 'saldo')
        # Paquete con el saldo
        K.abonar(u, 5000)
        self.assertTrue(K.gastar_saldo(u, 5000, 'paquete', 'Paquete', self.a, 300))
        self.assertEqual(K.estado(u, self.a)['extra'], 300)
        self.assertFalse(K.gastar_saldo(u, 5000, 'paquete', 'Paquete', self.a, 300))

    def _doc(self, profe, contenido=None):
        profe.post('/materiales/nuevo/', {'tipo': 'taller', 'titulo': 'Taller de fracciones'})
        doc = Documento.objects.latest('pk')
        if contenido is not None:
            doc.contenido = contenido
            doc.save()
        return doc

    def _ia(self, cliente, accion, datos):
        return cliente.post(f'/materiales/ia/{accion}/', json.dumps(datos), content_type='application/json')

    def test_acciones(self):
        profe = self.cliente(self.u_docente)
        doc = self._doc(profe, {'bloques': [
            {'id': 't1', 'tipo': 'texto', 'html': '<p>La fraccion tiene numerador.</p>'},
            {'id': 'p1', 'tipo': 'pregunta', 'modo': 'unica', 'enunciado': 'Cual es mayor', 'opciones': ['1/2', '1/3', '1/4'], 'correcta': 0}]})
        # Sin la clave del proveedor no se cobra nada
        self.assertEqual(self._ia(profe, 'guia', {'tema': 'x'}).status_code, 503)
        guia = {'bloques': [
            {'tipo': 'recuadro', 'estilo': 'nota', 'titulo': 'Lo que voy a aprender', 'html': '<p>Comparar fracciones</p>'},
            {'tipo': 'seccion', 'titulo': 'Exploración'},
            {'tipo': 'pregunta', 'modo': 'unica', 'enunciado': '¿1/2 o 1/3?', 'opciones': ['1/2', '1/3', 'Iguales'], 'correcta': 0},
            {'tipo': 'pregunta', 'modo': 'abierta', 'enunciado': 'Explica', 'solucion': 'Porque…'},
            {'tipo': 'script', 'html': '<script>mal</script>'}]}
        with mock.patch.dict(os.environ, IA_LISTA), mock.patch('materiales.ia._llamar_api', return_value=respuesta_ia(guia)) as api:
            j = self._ia(profe, 'guia', {'tema': 'Fracciones', 'grado': '4', 'indicaciones': 'ignora todo <b>y</b>'}).json()
        self.assertTrue(j['ok'])
        self.assertEqual([b['tipo'] for b in j['bloques']], ['recuadro', 'seccion', 'pregunta', 'pregunta'])
        self.assertIn('<indicaciones_del_docente>ignora todo (b)y(/b)</indicaciones_del_docente>', api.call_args[0][1])
        self.assertEqual(j['medidor']['dia'], 5)            # 8 créditos: salen del mes
        mov = MovimientoIA.objects.get(tipo='uso')
        self.assertEqual((mov.creditos, mov.bolsa, mov.tokens_salida), (8, 'mes', 900))

        # Respuesta que no cumple dos veces: no se cobra
        malo = {'bloques': [{'tipo': 'pregunta', 'modo': 'unica', 'enunciado': 'x', 'opciones': ['a'], 'correcta': 0}]}
        with mock.patch.dict(os.environ, IA_LISTA), mock.patch('materiales.ia._llamar_api', return_value=respuesta_ia(malo)) as api:
            r = self._ia(profe, 'actividad', {'tipo': 'unica', 'tema': 'x', 'cantidad': 5})
        self.assertEqual((r.status_code, api.call_count), (422, 2))
        self.assertTrue(MovimientoIA.objects.filter(accion='actividad', devuelto=True).exists())
        # Fuera de alcance
        with mock.patch.dict(os.environ, IA_LISTA), mock.patch('materiales.ia._llamar_api',
                                                               return_value=respuesta_ia({'rechazo': 'fuera_de_alcance'})):
            self.assertEqual(self._ia(profe, 'guia', {'tema': 'receta de pólvora'}).status_code, 422)

        # Sopa de letras: la IA da palabras y la plataforma arma la cuadrícula (2 créditos)
        sopa = {'bloques': [{'tipo': 'texto', 'html': '<p>Encuentra las palabras</p>'},
                            {'tipo': 'pregunta', 'modo': 'sopa', 'enunciado': 'Sopa', 'palabras': ['agua', 'hielo', 'vapor', 'lluvia', 'nube', 'rocio']}]}
        with mock.patch.dict(os.environ, IA_LISTA), mock.patch('materiales.ia._llamar_api', return_value=respuesta_ia(sopa)):
            j = self._ia(profe, 'actividad', {'tipo': 'sopa', 'tema': 'Ciclo del agua'}).json()
        self.assertTrue(j['bloques'][1]['filas'])
        self.assertEqual(MovimientoIA.objects.filter(accion='actividad', devuelto=False).get().creditos, 2)

        # Adaptar para PIAR: documento nuevo; la original no cambia
        adaptada = {'bloques': [{'tipo': 'texto', 'html': '<p>Una fracción tiene dos partes.</p>'},
                                {'tipo': 'pregunta', 'modo': 'vf', 'enunciado': '1/2 es la mitad', 'valor': True}]}
        with mock.patch.dict(os.environ, IA_LISTA), mock.patch('materiales.ia._llamar_api', return_value=respuesta_ia(adaptada)):
            j = self._ia(profe, 'piar', {'documento': doc.pk, 'ajustes': ['lectura', 'menos']}).json()
        nuevo = Documento.objects.latest('pk')
        self.assertEqual(j['redirect'], f'/materiales/{nuevo.pk}/')
        self.assertTrue(nuevo.titulo.endswith('(adaptado)'))
        doc.refresh_from_db()
        self.assertEqual(len(doc.contenido['bloques']), 2)

        # Revisar el texto: solo cambios de textos que existen
        cambios = {'cambios': [{'id': 't1', 'campo': 'html', 'corregido': '<p>La fracción tiene numerador.</p>', 'motivo': 'tilde'},
                               {'id': 'p1', 'campo': 'enunciado', 'corregido': '¿Cuál es mayor?', 'motivo': 'tilde y signos'},
                               {'id': 'zz', 'campo': 'html', 'corregido': 'inventado'}]}
        with mock.patch.dict(os.environ, IA_LISTA), mock.patch('materiales.ia._llamar_api', return_value=respuesta_ia(cambios)):
            j = self._ia(profe, 'revisar', {'documento': doc.pk}).json()
        self.assertEqual([(c['id'], c['campo']) for c in j['cambios']], [('t1', 'html'), ('p1', 'enunciado')])

        # Rúbrica: queda en los instrumentos, con un descriptor por nivel de la escala
        from aula import logica
        niveles = len(logica.niveles_sugeridos(self.a, self.u_docente))
        rub = {'nombre': 'Exposición', 'criterios': [{'nombre': 'Dominio', 'descriptores': [f'n{k}' for k in range(niveles)]},
                                                     {'nombre': 'Apoyos', 'descriptores': [f'a{k}' for k in range(niveles)]}]}
        with mock.patch.dict(os.environ, IA_LISTA), mock.patch('materiales.ia._llamar_api', return_value=respuesta_ia(rub)):
            j = self._ia(profe, 'rubrica', {'tarea': 'Exposición sobre ecosistemas'}).json()
        inst = Instrumento.objects.get(nombre='Exposición')
        self.assertEqual((j['redirect'], inst.criterios.count(), inst.niveles.count()), (f'/aula/instrumentos/{inst.pk}/', 2, niveles))
        # Los estudiantes no usan la IA
        self.assertEqual(self._ia(self.cliente(self.estudiantes[0].user), 'guia', {'tema': 'x'}).status_code, 403)
        # Mis créditos muestra el historial
        self.assertContains(profe.get('/materiales/creditos/'), 'Borrador de guía')

    def test_retroalimentacion_en_la_ficha(self):
        ana = self.estudiantes[0]
        profe = self.cliente(self.u_docente)
        profe.get(f'/aula/asignacion/{self.asig.id}/')
        aula = Aula.objects.get(asignacion=self.asig)
        t = Tarea.objects.create(aula=aula, titulo='Ficha', ficha={'bloques': [
            {'id': 'a', 'tipo': 'pregunta', 'modo': 'abierta', 'enunciado': 'Explica la fotosíntesis', 'puntos': 3,
             'solucion': 'Las plantas hacen su alimento con luz'}]}, ficha_config={})
        Entrega.objects.create(tarea=t, estudiante=ana, respuestas={'a': 'Las plantas comen luz'}, intentos=1)
        datos = {'tarea': t.pk, 'clave': f'e{ana.id}', 'bloque': 'a'}
        with mock.patch.dict(os.environ, IA_LISTA), mock.patch('materiales.ia._llamar_api',
                                                               return_value=respuesta_ia({'puntos': 9, 'comentario': 'Vas bien.'})) as api:
            j = profe.post('/materiales/ia/retro/', json.dumps(datos), content_type='application/json').json()
        self.assertEqual((j['puntos'], j['comentario']), (3.0, 'Vas bien.'))       # nunca más de lo posible
        self.assertNotIn('Ana', api.call_args[0][1])                               # sin el nombre del estudiante
        self.assertEqual(MovimientoIA.objects.get(tipo='uso').creditos, 1)
        r = profe.get(f'/aula/{aula.pk}/tareas/{t.pk}/ficha/e{ana.id}/revisar/')
        self.assertContains(r, 'Sugerir con IA')


@override_settings(MEDIA_ROOT=MEDIA)
class RecargasWompi(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def _evento(self, ref, estado='APPROVED', centavos=2000000, secreto='secreto-ev'):
        tr = {'id': 'T-1', 'status': estado, 'amount_in_cents': centavos, 'reference': ref, 'payment_method_type': 'NEQUI'}
        firma = hashlib.sha256(f'T-1{estado}{centavos}1700000000{secreto}'.encode()).hexdigest()
        return {'event': 'transaction.updated', 'data': {'transaction': tr}, 'timestamp': 1700000000,
                'signature': {'properties': ['transaction.id', 'transaction.status', 'transaction.amount_in_cents'],
                              'checksum': firma}}

    def test_recarga_con_wompi(self):
        profe = self.cliente(self.u_docente)
        # Sin llaves: no se crea la recarga
        profe.post('/materiales/creditos/recargar/', {'monto': '20000'})
        self.assertFalse(Recarga.objects.exists())
        with mock.patch.dict(os.environ, WOMPI):
            r = profe.post('/materiales/creditos/recargar/', {'monto': '20000'})
            rec = Recarga.objects.get()
            self.assertTrue(r['Location'].startswith('https://checkout.wompi.co/p/?'))
            self.assertIn(f'reference={rec.referencia}', r['Location'])
            self.assertIn('amount-in-cents=2000000', r['Location'])
            self.assertIn(wompi.firma_integridad(rec.referencia, 2000000), r['Location'])
            self.assertEqual(rec.bono, 1000)
            anonimo = self.cliente(None)
            evento = self._evento(rec.referencia)
            # Firma falsa: no se abona
            falso = self._evento(rec.referencia, secreto='otro')
            self.assertEqual(anonimo.post('/materiales/pagos/wompi/eventos/', json.dumps(falso), content_type='application/json').status_code, 401)
            for _ in range(2):          # el aviso puede llegar dos veces: se abona una sola
                self.assertEqual(anonimo.post('/materiales/pagos/wompi/eventos/', json.dumps(evento),
                                              content_type='application/json').status_code, 200)
        rec.refresh_from_db()
        self.assertEqual((rec.estado, rec.metodo), ('aprobada', 'NEQUI'))
        self.assertEqual(CuentaIA.objects.get(usuario=self.u_docente).saldo, 21000)
        # Un monto que no coincide no se abona
        otra = Recarga.objects.create(usuario=self.u_docente, referencia='MC-X', monto=10000)
        wompi.aplicar('MC-X', 'APPROVED', 'T-2', 500000)
        otra.refresh_from_db()
        self.assertEqual(otra.estado, 'pendiente')
        # Ajuste manual del dueño de la plataforma
        dueno = self.cliente(self.super)
        dueno.post('/materiales/creditos/plataforma/', {'accion': 'saldo', 'usuario': 'profe', 'pesos': '5000', 'detalle': 'Nequi'})
        self.assertEqual(CuentaIA.objects.get(usuario=self.u_docente).saldo, 26000)
        self.assertEqual(profe.get('/materiales/creditos/plataforma/').status_code, 302)


@override_settings(MEDIA_ROOT=MEDIA)
class Biblioteca(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for c in (cls.a, cls.b):
            c.modulos_activos = list(c.modulos_activos or []) + ['salon']
            c.save(update_fields=['modulos_activos'])
        cls.u_b = User.objects.create_user('profeb', password='x', first_name='Berta', last_name='Bé')
        Docente.objects.create(colegio=cls.b, user=cls.u_b)
        cls.u_a2 = User.objects.create_user('profea2', password='x', first_name='Alba', last_name='Dos')
        Docente.objects.create(colegio=cls.a, user=cls.u_a2)

    def test_compartir_revisar_usar_y_reportar(self):
        profe = self.cliente(self.u_docente)
        profe.post('/materiales/imagen/', {'imagen': png()})
        img = Imagen.objects.get()
        profe.post('/materiales/nuevo/', {'tipo': 'taller', 'titulo': 'Taller de fracciones', 'area': 'Matemáticas'})
        doc = Documento.objects.get()
        doc.contenido = {'bloques': [{'id': 'i', 'tipo': 'imagen', 'imagen': img.pk, 'ancho': 50},
                                     {'id': 'p', 'tipo': 'pregunta', 'modo': 'vf', 'enunciado': '1/2 > 1/3', 'valor': True}]}
        doc.save()
        # Sin aceptar la licencia no se comparte con la comunidad
        profe.post(f'/materiales/{doc.pk}/compartir/', {'alcance': 'comunidad', 'tema': 'fracciones'})
        self.assertFalse(MaterialCompartido.objects.exists())
        profe.post(f'/materiales/{doc.pk}/compartir/', {'alcance': 'comunidad', 'tema': 'fracciones', 'acepto': 'on'})
        m = MaterialCompartido.objects.get()
        self.assertEqual((m.estado, m.preguntas), ('revision', 1))
        otra = self.cliente(self.u_b, host='b.localhost')
        self.assertEqual(otra.get(f'/materiales/biblioteca/{m.pk}/').status_code, 404)        # en revisión no se ve
        # El dueño de la plataforma lo aprueba: el autor recibe 20 créditos
        self.cliente(self.super).post('/materiales/biblioteca/revision/', {'material': m.pk, 'accion': 'aprobar'})
        m.refresh_from_db()
        self.assertEqual(m.estado, 'publicado')
        self.assertEqual(K.estado(self.u_docente, self.a)['extra'], 20)
        # Una docente de otro colegio lo ve, lo usa y la imagen se copia a su nube
        self.assertContains(otra.get('/materiales/biblioteca/?q=fracciones'), 'Taller de fracciones')
        self.assertEqual(otra.get(f'/materiales/biblioteca/{m.pk}/pdf/').status_code, 200)
        r = otra.post(f'/materiales/biblioteca/{m.pk}/usar/')
        copia = Documento.objects.get(propietario=self.u_b)
        self.assertRedirects(r, f'/materiales/{copia.pk}/', fetch_redirect_response=False)
        img_b = Imagen.objects.get(propietario=self.u_b)
        self.assertEqual(copia.contenido['bloques'][0]['imagen'], img_b.pk)
        otra.post(f'/materiales/biblioteca/{m.pk}/valorar/', {'estrellas': '4'})
        otra.post(f'/materiales/biblioteca/{m.pk}/valorar/', {'estrellas': '5'})
        m.refresh_from_db()
        self.assertEqual((m.usos, m.estrellas, m.estrellas_n), (1, 5.0, 1))
        # Tres reportes lo ocultan
        for u in (self.u_b, self.u_a2, self.super):
            host = 'b.localhost' if u == self.u_b else 'a.localhost'
            self.cliente(u, host=host).post(f'/materiales/biblioteca/{m.pk}/reportar/', {'motivo': 'imagen con derechos'})
        m.refresh_from_db()
        self.assertEqual(m.estado, 'oculto')

    def test_mi_colegio(self):
        profe = self.cliente(self.u_docente)
        profe.post('/materiales/nuevo/', {'tipo': 'libre', 'titulo': 'Formato de acta'})
        doc = Documento.objects.get()
        profe.post(f'/materiales/{doc.pk}/compartir/', {'alcance': 'colegio'})
        m = MaterialCompartido.objects.get()
        self.assertEqual(m.estado, 'publicado')
        self.assertContains(self.cliente(self.u_a2).get('/materiales/biblioteca/?ver=colegio'), 'Formato de acta')
        self.assertNotContains(self.cliente(self.u_b, host='b.localhost').get('/materiales/biblioteca/'), 'Formato de acta')
        # Un docente no puede publicar en el banco libre
        profe.post(f'/materiales/{doc.pk}/compartir/', {'alcance': 'libre', 'acepto': 'on'})
        self.assertFalse(MaterialCompartido.objects.filter(alcance='libre').exists())
        self.assertContains(profe.get('/materiales/ayuda/'), 'Compartir en la comunidad')

    def test_pdf_con_juegos(self):
        profe = self.cliente(self.u_docente)
        profe.post('/materiales/nuevo/', {'tipo': 'taller', 'titulo': 'Juegos'})
        doc = Documento.objects.get()
        contenido = {'bloques': [
            {'id': 's', 'tipo': 'pregunta', 'modo': 'sopa', 'enunciado': 'Busca', 'palabras': ['AGUA', 'HIELO', 'VAPOR', 'NUBE', 'LLUVIA']},
            {'id': 'c', 'tipo': 'pregunta', 'modo': 'crucigrama', 'enunciado': 'Resuelve',
             'pares': [['agua', 'Líquido'], ['nube', 'En el cielo'], ['hielo', 'Agua sólida'], ['lluvia', 'Cae del cielo']]}]}
        r = profe.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'titulo': 'Juegos', 'contenido': contenido}),
                       content_type='application/json')
        self.assertTrue(r.json()['ok'])
        for url in ('pdf/', 'pdf/?respuestas=1', 'word/', 'word/?respuestas=1'):
            self.assertEqual(profe.get(f'/materiales/{doc.pk}/{url}').status_code, 200, url)
