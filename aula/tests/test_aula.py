"""Aula virtual: muro, tareas con rúbrica, entrega con fotos, paso a la planilla y Salón Digital."""
import io
import shutil
import tempfile
from decimal import Decimal

import openpyxl
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings

from aula import logica
from aula.models import Aula, Comentario, Entrega, Instrumento, Publicacion, Tarea
from notas.models import Curso, Notificacion, NotaDetallada, Calificacion
from notas.tests.base import CLAVE, ColegioDePrueba

MEDIA = tempfile.mkdtemp(prefix='aula-pruebas-')


def foto(nombre='hoja.png'):
    from PIL import Image
    salida = io.BytesIO()
    Image.new('RGB', (400, 300), (240, 240, 240)).save(salida, format='PNG')
    return SimpleUploadedFile(nombre, salida.getvalue(), content_type='image/png')


@override_settings(MEDIA_ROOT=MEDIA)
class AulaDelColegio(ColegioDePrueba):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # Mi Salón Virtual es del plan Premium: se activa para el colegio de prueba.
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def setUp(self):
        self.ana = self.estudiantes[0]
        self.docente_c = self.cliente(self.u_docente)

    def abrir(self):
        r = self.docente_c.get(f'/aula/asignacion/{self.asig.id}/')
        self.assertEqual(r.status_code, 302)
        return Aula.objects.get(asignacion=self.asig)

    def test_inicio_y_permisos(self):
        r = self.docente_c.get('/aula/')
        self.assertContains(r, 'Matemáticas')
        aula = self.abrir()
        self.assertEqual(self.cliente(self.ana.user).get(f'/aula/{aula.pk}/').status_code, 200)
        # Un estudiante de otro curso no entra
        c702 = Curso.objects.create(colegio=self.a, nombre='702', grado=7, subgrupo='2')
        otro = self.crear_estudiante('otro', curso=c702)
        self.assertEqual(self.cliente(otro.user).get(f'/aula/{aula.pk}/').status_code, 403)
        # Ni alguien de otro colegio
        self.assertNotEqual(self.cliente(self.ana.user, host='b.localhost').get(f'/aula/{aula.pk}/').status_code, 200)
        # El estudiante no publica
        self.cliente(self.ana.user).post(f'/aula/{aula.pk}/', {'texto': 'Hola'})
        self.assertFalse(Publicacion.objects.exists())

    def test_muro_avisa_y_comentarios(self):
        aula = self.abrir()
        r = self.docente_c.post(f'/aula/{aula.pk}/', {'texto': 'Bienvenidos a la clase'})
        self.assertEqual(r.status_code, 302)
        pub = Publicacion.objects.get()
        self.assertEqual(Notificacion.objects.filter(mensaje__contains='nueva publicación').count(), 3)
        est = self.cliente(self.ana.user)
        est.post(f'/aula/{aula.pk}/publicacion/{pub.pk}/comentar/', {'texto': '¡Gracias profe!'})
        self.assertEqual(Comentario.objects.get().nombre, 'Ana Prueba')
        # El docente apaga los comentarios
        self.docente_c.post(f'/aula/{aula.pk}/clase/', {'enlace_clase': 'meet.google.com/abc-defg-hij'})
        aula.refresh_from_db()
        self.assertFalse(aula.comentarios_activos)
        self.assertEqual(aula.enlace_clase, 'https://meet.google.com/abc-defg-hij')
        self.assertEqual(aula.plataforma, 'meet')
        est.post(f'/aula/{aula.pk}/publicacion/{pub.pk}/comentar/', {'texto': 'otro'})
        self.assertEqual(Comentario.objects.count(), 1)
        self.assertContains(est.get(f'/aula/{aula.pk}/'), 'Unirse a la clase en vivo')

    def test_material_con_archivo_y_video(self):
        aula = self.abrir()
        self.docente_c.post(f'/aula/{aula.pk}/material/', {
            'titulo': 'Guía 1', 'unidad': 'Funciones', 'archivo': SimpleUploadedFile('guia.pdf', b'%PDF-1.4 x')})
        self.docente_c.post(f'/aula/{aula.pk}/material/', {
            'titulo': 'Video', 'enlace': 'https://youtu.be/dQw4w9WgXcQ'})
        r = self.cliente(self.ana.user).get(f'/aula/{aula.pk}/material/')
        self.assertContains(r, 'Guía 1')
        self.assertContains(r, 'youtube-nocookie.com/embed/dQw4w9WgXcQ')
        m = aula.materiales.get(titulo='Guía 1')
        r = self.cliente(self.ana.user).get(f'/aula/{aula.pk}/archivo/mat/{m.pk}/')
        self.assertEqual(r.status_code, 302)

    def test_tarea_con_rubrica_entrega_calificacion_y_planilla(self):
        aula = self.abrir()
        inst = logica.desde_plantilla(self.u_docente, self.a, 'guia')
        self.assertEqual([n.nombre for n in inst.niveles.all()], ['BAJO', 'BÁSICO', 'ALTO', 'SUPERIOR'])
        r = self.docente_c.post(f'/aula/{aula.pk}/tareas/nueva/', {
            'titulo': 'Guía 3', 'instrucciones': 'Resolver', 'instrumento': inst.pk, 'periodo': self.p1.pk,
            'componente': 'SABER', 'publicada': 'on', 'acepta_tardias': 'on'})
        self.assertEqual(r.status_code, 302)
        tarea = Tarea.objects.get()
        self.assertTrue(Publicacion.objects.filter(tarea=tarea).exists())

        # Ana entrega dos fotos: quedan en un solo PDF
        est = self.cliente(self.ana.user)
        est.post(f'/aula/{aula.pk}/tareas/{tarea.pk}/entregar/', {'fotos': [foto('a.png'), foto('b.png')]})
        e = Entrega.objects.get()
        self.assertTrue(e.nombre_archivo.endswith('.pdf'))
        with e.archivo.open('rb') as f:
            self.assertTrue(f.read(5).startswith(b'%PDF'))

        # El docente califica: Superior en todo menos un criterio en Básico
        criterios = list(inst.criterios.all())
        niveles = list(inst.niveles.all())
        datos = {f'c{cr.id}': niveles[3].id for cr in criterios}
        datos[f'c{criterios[0].id}'] = niveles[1].id
        datos['comentario'] = 'Muy bien'
        r = self.docente_c.post(f'/aula/{aula.pk}/tareas/{tarea.pk}/calificar/e{self.ana.id}/', datos)
        e.refresh_from_db()
        # (3,5 + 5 + 5 + 5) / 4 = 4,6
        self.assertEqual(e.nota, Decimal('4.6'))
        self.assertEqual(e.estado, 'calificada')
        self.assertContains(est.get(f'/aula/{aula.pk}/tareas/{tarea.pk}/'), 'Muy bien')

        # A la planilla
        self.docente_c.post(f'/aula/{aula.pk}/tareas/{tarea.pk}/planilla/')
        nd = NotaDetallada.objects.get(calificacion_promedio__estudiante=self.ana, descripcion='Guía 3')
        self.assertEqual(nd.valor_nota, Decimal('4.6'))
        self.assertEqual(nd.calificacion_promedio.tipo_nota, 'SABER')
        definitiva = Calificacion.objects.get(estudiante=self.ana, periodo=self.p1, tipo_nota='PROM_PERIODO')
        self.assertEqual(definitiva.valor_nota, Decimal('2.76'))      # 4,6 × 60 % (HACER sin notas)
        tarea.refresh_from_db()
        self.assertIsNotNone(tarea.pasada_planilla)

        # Pasarla otra vez no duplica la nota
        self.docente_c.post(f'/aula/{aula.pk}/tareas/{tarea.pk}/planilla/')
        self.assertEqual(NotaDetallada.objects.filter(calificacion_promedio__estudiante=self.ana,
                                                      descripcion='Guía 3').count(), 1)

    def test_grilla_y_nota_directa(self):
        aula = self.abrir()
        lista = logica.desde_plantilla(self.u_docente, self.a, 'cuaderno')
        tarea = Tarea.objects.create(aula=aula, titulo='Cuaderno', instrumento=lista)
        crits = list(lista.criterios.all())
        datos = {}
        for k, cr in enumerate(crits):        # beto cumple 3 de 5; ana todo
            datos[f'e{self.ana.id}-{cr.id}'] = 'si'
            datos[f'e{self.estudiantes[1].id}-{cr.id}'] = 'si' if k < 3 else 'no'
        self.docente_c.post(f'/aula/{aula.pk}/tareas/{tarea.pk}/grilla/', datos)
        notas = {e.estudiante_id: e.nota for e in Entrega.objects.all()}
        self.assertEqual(notas[self.ana.id], Decimal('5.0'))
        self.assertEqual(notas[self.estudiantes[1].id], Decimal('3.4'))     # 1 + 4 × 3/5
        # Nota directa
        t2 = Tarea.objects.create(aula=aula, titulo='Quiz')
        self.docente_c.post(f'/aula/{aula.pk}/tareas/{t2.pk}/calificar/e{self.ana.id}/', {'nota': '4,2'})
        self.assertEqual(Entrega.objects.get(tarea=t2).nota, Decimal('4.2'))
        r = self.docente_c.get(f'/aula/{aula.pk}/calificaciones/?formato=excel')
        ws = openpyxl.load_workbook(io.BytesIO(r.content)).active
        self.assertEqual(ws['C3'].value, 'Cuaderno')

    def test_importar_rubistar_y_editar(self):
        pegado = ('CATEGORY\tPeso\t4\t3\t2\t1\n'
                  'Contenido\t2\tCompleto\tCasi\tPoco\tNada\n'
                  'Ortografía\t1\tSin errores\tPocos\tVarios\tMuchos\n')
        r = self.docente_c.post('/aula/instrumentos/', {'accion': 'importar', 'nombre': 'Ensayo', 'tabla': pegado})
        self.assertEqual(r.status_code, 302)
        inst = Instrumento.objects.get(nombre='Ensayo')
        niveles = list(inst.niveles.all())
        self.assertEqual(len(niveles), 4)
        self.assertEqual(niveles[0].valor, Decimal('2.0'))       # el «1» de RubiStar = el nivel más bajo
        contenido = inst.criterios.get(nombre='Contenido')
        self.assertEqual(contenido.peso, Decimal('2'))
        self.assertEqual(contenido.descriptor(niveles[0]), 'Nada')
        self.assertEqual(contenido.descriptor(niveles[3]), 'Completo')
        # Excel
        libro = openpyxl.Workbook()
        hoja = libro.active
        hoja.append(['Criterio', 'Superior', 'Alto', 'Básico', 'Bajo'])
        hoja.append(['Dominio', 'a', 'b', 'c', 'd'])
        salida = io.BytesIO()
        libro.save(salida)
        archivo = SimpleUploadedFile('r.xlsx', salida.getvalue())
        self.docente_c.post('/aula/instrumentos/', {'accion': 'importar', 'nombre': 'Expo', 'archivo': archivo})
        expo = Instrumento.objects.get(nombre='Expo')
        self.assertEqual([n.nombre for n in expo.niveles.all()], ['BAJO', 'BÁSICO', 'ALTO', 'SUPERIOR'])
        # Editar: cambiar un valor y agregar un criterio
        url = f'/aula/instrumentos/{expo.pk}/'
        self.docente_c.post(url, {
            'nombre': 'Exposición', 'nivel_nombre': ['BAJO', 'BÁSICO', 'ALTO', 'SUPERIOR'],
            'nivel_valor': ['1,5', '3.5', '4.3', '5'], 'crit_nombre': ['Dominio', 'Voz'], 'crit_peso': ['1', '1'],
            'desc_1_3': 'Se escucha muy bien'})
        expo.refresh_from_db()
        self.assertEqual(expo.nombre, 'Exposición')
        self.assertEqual(expo.niveles.first().valor, Decimal('1.5'))
        self.assertEqual(expo.criterios.count(), 2)
        self.assertEqual(expo.criterios.get(nombre='Voz').descriptor(expo.niveles.last()), 'Se escucha muy bien')

    def test_lista_de_chequeo_calculo(self):
        inst = logica.crear_instrumento(self.u_docente, self.a, 'L', 'lista', [('a', 1), ('b', 1), ('c', 2)])
        crs = list(inst.criterios.all())
        sel = {str(crs[0].id): True, str(crs[1].id): False, str(crs[2].id): True}
        nota, completa = logica.calcular_nota(inst, sel, Decimal('1'), Decimal('5'))
        self.assertTrue(completa)
        self.assertEqual(nota, Decimal('4.0'))      # 3 de 4 → 1 + 4 × 0,75


class AulaSalonDigital(ColegioDePrueba):

    def test_grupo_codigo_entrega_y_planilla(self):
        from salon_digital.models import Cuenta, Grupo, Integrante
        u = User.objects.create_user('libre', password=CLAVE, first_name='Lina', last_name='Libre')
        cuenta = Cuenta.objects.create(usuario=u, slug='lina', nombre_publico='Lina Libre', estado='verificada')
        grupo = Grupo.objects.create(propietario=cuenta, nombre='7-01')
        luis = Integrante.objects.create(grupo=grupo, apellidos='Pérez', nombres='Luis')
        Integrante.objects.create(grupo=grupo, apellidos='Gómez', nombres='Sara')

        profe = Client(HTTP_HOST='localhost')
        profe.force_login(u)
        self.assertContains(profe.get('/aula/'), '7-01')
        r = profe.get(f'/aula/grupo/{grupo.pk}/')
        aula = Aula.objects.get(grupo=grupo)
        self.assertEqual(r.url, f'/aula/{aula.pk}/')
        tarea = Tarea.objects.create(aula=aula, titulo='Lectura')

        est = Client(HTTP_HOST='localhost')
        r = est.get(f'/aula/{aula.pk}/')
        self.assertEqual(r.url, f'/aula/{aula.pk}/entrar/')
        r = est.get(f'/aula/{aula.pk}/entrar/', {'codigo': 'MAL123'})
        self.assertContains(r, 'no corresponde')
        r = est.get(f'/aula/{aula.pk}/entrar/', {'codigo': grupo.codigo.lower()})
        self.assertContains(r, 'Pérez Luis')
        est.post(f'/aula/{aula.pk}/entrar/', {'codigo': grupo.codigo, 'integrante': luis.pk})
        self.assertEqual(est.get(f'/aula/{aula.pk}/').status_code, 200)
        est.post(f'/aula/{aula.pk}/tareas/{tarea.pk}/entregar/', {'texto': 'Mi resumen'})
        e = Entrega.objects.get()
        self.assertEqual(e.integrante, luis)

        profe.post(f'/aula/{aula.pk}/tareas/{tarea.pk}/calificar/i{luis.pk}/', {'nota': '4.5'})
        e.refresh_from_db()
        self.assertEqual(e.nota, Decimal('4.5'))
        r = profe.get(f'/aula/{aula.pk}/calificaciones/')
        self.assertContains(r, 'Pérez Luis')
        # El estudiante no ve las calificaciones de todos
        self.assertEqual(est.get(f'/aula/{aula.pk}/calificaciones/').status_code, 403)
        # Pasar a planilla no aplica en Salón Digital
        self.assertEqual(logica.pasar_a_planilla(tarea)[0], 0)

        # Escala propia del docente: de 1 a 10, el bajo hasta 5,9
        r = profe.post('/aula/escala/', {'nombre': ['bajo', 'básico', 'alto', 'superior', ''],
                                         'min': ['1', '6', '8', '9,5', ''], 'max': ['5,9', '7,9', '9,4', '10', '']})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(logica.rango(aula), (Decimal('1.0'), Decimal('10.0')))
        self.assertEqual(logica.desempeno(aula, Decimal('4.5')), 'BAJO')
        self.assertEqual(logica.desempeno(aula, Decimal('8.5')), 'ALTO')
        rub = logica.desde_plantilla(u, None, 'exposicion')
        self.assertEqual([(n.nombre, n.valor) for n in rub.niveles.all()],
                         [('BAJO', Decimal('3.5')), ('BÁSICO', Decimal('7.0')), ('ALTO', Decimal('8.7')),
                          ('SUPERIOR', Decimal('10.0'))])
        profe.post(f'/aula/{aula.pk}/tareas/{tarea.pk}/calificar/i{luis.pk}/', {'nota': '9'})
        e.refresh_from_db()
        self.assertEqual(e.nota, Decimal('9'))
        self.assertContains(profe.get(f'/aula/{aula.pk}/calificaciones/'), 'ALTO')
        # Rangos cruzados: no se guarda
        r = profe.post('/aula/escala/', {'nombre': ['A', 'B'], 'min': ['1', '3'], 'max': ['4', '5']})
        self.assertContains(r, 'se cruzan')


class GrupoSalonEditable(ColegioDePrueba):
    """El docente edita su grupo ya creado: agrega estudiantes, corrige nombres, cambia PIN, ve cómo entran
    e imprime tarjetas; con «Pedir el PIN al entrar» nadie entra con el nombre de otro."""

    def test_editar_grupo_y_entrar_con_pin(self):
        from django.core.cache import cache
        from salon_digital.models import Cuenta, Grupo, Integrante
        cache.clear()
        u = User.objects.create_user('libre2', password=CLAVE, first_name='Lina')
        cuenta = Cuenta.objects.create(usuario=u, slug='lina2', nombre_publico='Lina', estado='verificada')
        grupo = Grupo.objects.create(propietario=cuenta, nombre='8-02')
        profe = Client(HTTP_HOST='localhost'); profe.force_login(u)
        profe.get(f'/aula/grupo/{grupo.pk}/')                 # crea el aula del grupo
        aula = Aula.objects.get(grupo=grupo)
        g = f'/salon_digital/grupos/{grupo.pk}/'
        # Agregar uno por uno (y el repetido no se duplica)
        r = profe.post(g, {'uno': '1', 'apellidos': 'Pérez Ruiz', 'nombres': 'Luis'}, follow=True)
        luis = Integrante.objects.get(grupo=grupo, nombres='Luis')
        self.assertContains(r, f'Su PIN es {luis.pin_chat}')
        profe.post(g, {'uno': '1', 'apellidos': 'pérez ruiz', 'nombres': 'luis'})
        self.assertEqual(grupo.integrantes.count(), 1)
        profe.post(g, {'pegar': '1', 'lista': 'Gómez, Sara\nTorres Díaz, Ana María'})
        self.assertEqual(grupo.integrantes.filter(activo=True).count(), 3)
        # La página muestra cómo entran: enlace con el código, PIN de cada uno
        r = profe.get(g)
        self.assertContains(r, 'Cómo entran sus estudiantes')
        self.assertContains(r, f'/aula/{aula.pk}/entrar/?codigo={grupo.codigo}')
        self.assertContains(r, luis.pin_chat)
        # Editar el nombre, PIN nuevo, quitar y volver a agregar
        profe.post(f'{g}estudiante/{luis.pk}/editar/', {'apellidos': 'Pérez Ruiz', 'nombres': 'Luis Felipe'})
        luis.refresh_from_db(); self.assertEqual(luis.completo, 'Pérez Ruiz Luis Felipe')
        viejo = luis.pin_chat
        for _ in range(5):          # un PIN nuevo (al azar: puede repetir; se intenta unas veces)
            profe.post(f'{g}estudiante/{luis.pk}/pin/')
            luis.refresh_from_db()
            if luis.pin_chat != viejo:
                break
        self.assertNotEqual(luis.pin_chat, viejo)
        sara = Integrante.objects.get(grupo=grupo, apellidos='Gómez')
        profe.post(f'{g}quitar/{sara.pk}/')
        self.assertContains(profe.get(g), 'Retirados del grupo')
        profe.post(f'{g}estudiante/{sara.pk}/volver/')
        sara.refresh_from_db(); self.assertTrue(sara.activo)
        # Tarjetas para imprimir (con QR, código y PIN)
        r = profe.get(f'{g}tarjetas/')
        self.assertContains(r, 'data:image/png;base64,'); self.assertContains(r, grupo.codigo); self.assertContains(r, luis.pin_chat)
        # Otro docente no puede tocar el grupo
        otro = User.objects.create_user('otro', password=CLAVE)
        Cuenta.objects.create(usuario=otro, slug='otro', nombre_publico='Otro', estado='verificada')
        intruso = Client(HTTP_HOST='localhost'); intruso.force_login(otro)
        self.assertEqual(intruso.post(f'{g}estudiante/{luis.pk}/editar/', {'apellidos': 'X'}).status_code, 404)
        # Sin «pedir PIN»: entra con código y nombre
        est = Client(HTTP_HOST='localhost')
        est.post(f'/aula/{aula.pk}/entrar/', {'codigo': grupo.codigo, 'integrante': sara.pk})
        self.assertEqual(est.get(f'/aula/{aula.pk}/').status_code, 200)
        # Con «pedir PIN»: el PIN equivocado no deja entrar; el suyo sí
        profe.post(f'{g}editar/', {'nombre': '8-02', 'descripcion': '', 'activo': 'on', 'pedir_pin': 'on'})
        grupo.refresh_from_db(); self.assertTrue(grupo.pedir_pin)
        est2 = Client(HTTP_HOST='localhost')
        r = est2.get(f'/aula/{aula.pk}/entrar/', {'codigo': grupo.codigo})
        self.assertContains(r, 'name="pin"')
        malo = '0000' if luis.pin_chat != '0000' else '1111'
        r = est2.post(f'/aula/{aula.pk}/entrar/', {'codigo': grupo.codigo, 'integrante': luis.pk, 'pin': malo})
        self.assertContains(r, 'Ese PIN no es el suyo')
        self.assertEqual(est2.get(f'/aula/{aula.pk}/').status_code, 302)
        est2.post(f'/aula/{aula.pk}/entrar/', {'codigo': grupo.codigo, 'integrante': luis.pk, 'pin': luis.pin_chat})
        self.assertEqual(est2.get(f'/aula/{aula.pk}/').status_code, 200)
        # Demasiados intentos: se bloquea un rato
        est3 = Client(HTTP_HOST='localhost')
        for _ in range(8):
            est3.post(f'/aula/{aula.pk}/entrar/', {'codigo': grupo.codigo, 'integrante': sara.pk, 'pin': '9999' if sara.pin_chat != '9999' else '8888'})
        r = est3.post(f'/aula/{aula.pk}/entrar/', {'codigo': grupo.codigo, 'integrante': sara.pk, 'pin': sara.pin_chat})
        self.assertContains(r, 'Demasiados intentos')
