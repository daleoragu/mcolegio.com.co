# -*- coding: utf-8 -*-
"""Prematrícula: de la familia en el portal a la matrícula aprobada."""
import datetime
import io
import zipfile

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from notas.models import Curso, Estudiante, FichaEstudiante, Sede
from notas.tests.base import ColegioDePrueba

from . import logica
from .models import Configuracion, Documento, PreguntaEncuesta, Requisito, Solicitud

PDF = b'%PDF-1.4 prueba'


class Prematricula(ColegioDePrueba):

    def setUp(self):
        self.familia = self.cliente()                       # sin usuario
        self.admin = self.cliente(self.rectora)
        self.conf = logica.configuracion_de(self.a)
        self.conf.abierta = True
        self.conf.ano_lectivo = 2027
        self.conf.save()
        self.curso7 = Curso.objects.create(colegio=self.a, nombre='701', grado=7)

    def datos(self, **extra):
        d = {'grado': '7', 'nombres': 'Mateo', 'apellidos': 'Rojas Díaz', 'tipo_documento': 'TI',
             'numero_documento': '1105000111', 'fecha_nacimiento': '2014-03-02',
             'acudiente_nombre': 'Claudia Díaz', 'acudiente_celular': '3105551234',
             'acudiente_correo': 'claudia@example.com', 'eps': 'Nueva EPS', 'rh': 'O+',
             'acepta': 'on'}
        for r in Requisito.objects.filter(colegio=self.a, obligatorio=True, pide_archivo=True):
            if r.aplica_a('NUEVO'):
                d[f'doc_{r.id}'] = SimpleUploadedFile(f'doc{r.id}.pdf', PDF, 'application/pdf')
        for p in PreguntaEncuesta.objects.filter(colegio=self.a):
            if p.tipo == 'VARIAS':
                d[f'enc_{p.id}'] = p.lista_opciones()[:2]
            elif p.tipo == 'TEXTO':
                d[f'enc_{p.id}'] = 'Gracias'
            else:
                d[f'enc_{p.id}'] = p.lista_opciones()[0]
        d.update(extra)
        return d

    def test_configuracion_inicial_trae_requisitos_y_encuesta(self):
        self.assertGreaterEqual(Requisito.objects.filter(colegio=self.a).count(), 5)
        self.assertGreaterEqual(PreguntaEncuesta.objects.filter(colegio=self.a).count(), 5)

    def test_portal_muestra_el_enlace_solo_si_esta_abierta(self):
        self.assertIn('/prematricula/', self.familia.get('/').content.decode())
        self.conf.abierta = False
        self.conf.save()
        self.assertNotIn('/prematricula/"', self.familia.get('/').content.decode())
        self.assertContains(self.familia.get('/prematricula/'), 'no está abierta')
        self.assertRedirects(self.familia.get('/prematricula/formulario/nuevo/'), '/prematricula/',
                             fetch_redirect_response=False)

    @override_settings(EMAIL_HOST='smtp.example.com')
    def test_flujo_completo_estudiante_nuevo(self):
        r = self.familia.post('/prematricula/formulario/nuevo/', self.datos())
        self.assertEqual(r.status_code, 302, r.content.decode()[:3000])
        s = Solicitud.objects.get()
        self.assertEqual((s.estado, s.ano_lectivo, s.grado), ('RECIBIDA', 2027, 7))
        self.assertTrue(s.radicado.startswith(f'PM{self.a.id}-2027-'))
        self.assertEqual(s.documentos.count(), len([x for x in s.requisitos() if x.obligatorio and x.pide_archivo]))
        self.assertTrue(s.encuesta)
        self.assertEqual(len(mail.outbox), 1)                 # acuse de recibo
        estado = self.familia.get(r['Location'])
        self.assertContains(estado, s.radicado)

        # Los documentos no tienen enlace público: solo la secretaría.
        d = Documento.objects.first()
        self.assertNotEqual(self.familia.get(f'/prematricula/gestion/documento/{d.id}/').status_code, 200)
        self.assertEqual(self.admin.get(f'/prematricula/gestion/documento/{d.id}/').status_code, 200)

        # Sin curso no se aprueba.
        reqs = {f'req_{x.id}': 'on' for x in s.requisitos()}
        self.admin.post(f'/prematricula/gestion/{s.id}/', {'accion': 'aprobar', **reqs})
        s.refresh_from_db()
        self.assertNotEqual(s.estado, 'APROBADA')
        # Con curso y requisitos, sí: se crea el estudiante, inactivo hasta 2027.
        self.admin.post(f'/prematricula/gestion/{s.id}/', {'accion': 'aprobar', 'curso_asignado': self.curso7.id, **reqs})
        s.refresh_from_db()
        self.assertEqual(s.estado, 'APROBADA')
        est = s.estudiante_creado
        self.assertEqual((est.curso, est.colegio, est.is_active), (self.curso7, self.a, False))
        self.assertEqual(est.ficha.numero_documento, '1105000111')
        self.assertEqual(est.ficha.email_acudiente, 'claudia@example.com')
        self.assertIn('Usuario de la plataforma', mail.outbox[-1].body)
        # Activar al empezar el año.
        self.admin.post('/prematricula/gestion/activar/', {'ano': 2027})
        est.refresh_from_db()
        self.assertTrue(est.is_active)

    def test_faltan_requisitos_no_deja_aprobar_sin_confirmar(self):
        self.familia.post('/prematricula/formulario/nuevo/', self.datos())
        s = Solicitud.objects.get()
        self.admin.post(f'/prematricula/gestion/{s.id}/', {'accion': 'aprobar', 'curso_asignado': self.curso7.id})
        s.refresh_from_db()
        self.assertNotEqual(s.estado, 'APROBADA')
        self.admin.post(f'/prematricula/gestion/{s.id}/', {'accion': 'aprobar', 'curso_asignado': self.curso7.id,
                                                          'aprobar_igual': 'on'})
        s.refresh_from_db()
        self.assertEqual(s.estado, 'APROBADA')

    def test_falta_algo_y_la_familia_sube_lo_que_falta(self):
        datos = self.datos()
        opcional = Requisito.objects.filter(colegio=self.a, obligatorio=False, pide_archivo=True, para='TODOS').first()
        self.familia.post('/prematricula/formulario/nuevo/', datos)
        s = Solicitud.objects.get()
        self.admin.post(f'/prematricula/gestion/{s.id}/', {'accion': 'pendiente', 'mensaje_familia': 'Falta la foto'})
        s.refresh_from_db()
        self.assertEqual(s.estado, 'PENDIENTE')
        enlace = f'/prematricula/solicitud/{logica.token_consulta(s)}/'
        self.assertContains(self.familia.get(enlace), 'Falta la foto')
        self.familia.post(enlace, {f'doc_{opcional.id}': SimpleUploadedFile('foto.jpg', b'x', 'image/jpeg')})
        s.refresh_from_db()
        self.assertEqual(s.estado, 'REVISION')
        self.assertTrue(s.documentos.filter(requisito=opcional).exists())

    def test_archivos_no_permitidos(self):
        r = Requisito.objects.filter(colegio=self.a, obligatorio=True, pide_archivo=True).first()
        datos = self.datos(**{f'doc_{r.id}': SimpleUploadedFile('virus.exe', b'MZ', 'application/octet-stream')})
        resp = self.familia.post('/prematricula/formulario/nuevo/', datos)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Solicitud.objects.exists())

    def test_estudiante_antiguo(self):
        est = self.estudiantes[0]
        FichaEstudiante.objects.update_or_create(estudiante=est, defaults={
            'numero_documento': '999', 'fecha_nacimiento': datetime.date(2013, 5, 1),
            'nombre_acudiente': 'Abuela', 'celular_acudiente': '3000000000'})
        # Documento sin la fecha correcta: no entra.
        r = self.familia.post('/prematricula/antiguo/', {'documento': '999', 'fecha_nacimiento': '2013-05-02'})
        self.assertContains(r, 'No encontramos')
        r = self.familia.post('/prematricula/antiguo/', {'documento': '999', 'fecha_nacimiento': '2013-05-01'})
        self.assertRedirects(r, '/prematricula/formulario/antiguo/', fetch_redirect_response=False)
        h = self.familia.get('/prematricula/formulario/antiguo/').content.decode()
        self.assertIn('Abuela', h)                       # trae sus datos
        datos = self.datos(numero_documento='otro', acudiente_nombre='Abuela Ana')
        for k in [k for k in datos if k.startswith('doc_')]:
            datos.pop(k)
        for r in Requisito.objects.filter(colegio=self.a, obligatorio=True, pide_archivo=True):
            if r.aplica_a('ANTIGUO'):
                datos[f'doc_{r.id}'] = SimpleUploadedFile('a.pdf', PDF, 'application/pdf')
        r = self.familia.post('/prematricula/formulario/antiguo/', datos)
        self.assertEqual(r.status_code, 302, r.content.decode()[:3000])
        s = Solicitud.objects.get()
        self.assertEqual((s.tipo, s.estudiante_antiguo, s.numero_documento), ('ANTIGUO', est, '999'))
        self.admin.post(f'/prematricula/gestion/{s.id}/', {'accion': 'aprobar', 'aprobar_igual': 'on'})
        est.ficha.refresh_from_db()
        self.assertEqual(est.ficha.nombre_acudiente, 'Abuela Ana')
        self.assertEqual(Estudiante.objects.filter(colegio=self.a).count(), 3)   # no creó otro

    def test_documento_repetido_no_crea_duplicado(self):
        FichaEstudiante.objects.update_or_create(estudiante=self.estudiantes[1], defaults={'numero_documento': '1105000111'})
        self.familia.post('/prematricula/formulario/nuevo/', self.datos())
        s = Solicitud.objects.get()
        r = self.admin.post(f'/prematricula/gestion/{s.id}/', {'accion': 'aprobar', 'curso_asignado': self.curso7.id,
                                                              'aprobar_igual': 'on'}, follow=True)
        self.assertContains(r, 'Ya hay un estudiante con el documento')
        s.refresh_from_db()
        self.assertNotEqual(s.estado, 'APROBADA')

    def test_gestion_solo_admin_y_de_su_colegio(self):
        self.familia.post('/prematricula/formulario/nuevo/', self.datos())
        s = Solicitud.objects.get()
        self.assertNotEqual(self.cliente(self.u_docente).get('/prematricula/gestion/').status_code, 200)
        self.assertEqual(self.cliente(self.super, host='b.localhost').get(f'/prematricula/gestion/{s.id}/').status_code, 404)

    def test_panel_excel_encuesta_zip_y_configuracion(self):
        self.familia.post('/prematricula/formulario/nuevo/', self.datos())
        s = Solicitud.objects.get()
        self.assertContains(self.admin.get('/prematricula/gestion/'), 'Rojas Díaz')
        self.assertContains(self.admin.get(f'/prematricula/gestion/{s.id}/'), 'Nueva EPS')
        r = self.admin.get('/prematricula/gestion/exportar/')
        import openpyxl
        hoja = openpyxl.load_workbook(io.BytesIO(r.content)).active
        self.assertEqual(hoja.cell(row=2, column=8).value, 'Rojas Díaz')
        self.assertContains(self.admin.get('/prematricula/gestion/encuesta/'), '¿Cómo se enteró del colegio?')
        z = zipfile.ZipFile(io.BytesIO(self.admin.get(f'/prematricula/gestion/{s.id}/documentos.zip').content))
        self.assertTrue(z.namelist())
        self.assertEqual(self.admin.get('/prematricula/gestion/configuracion/').status_code, 200)

    def test_sede_y_jornada_si_hay_varias(self):
        Sede.objects.create(colegio=self.a, nombre='Norte', jornadas='MANANA')
        Sede.objects.create(colegio=self.a, nombre='Sur', jornadas='TARDE')
        h = self.familia.get('/prematricula/formulario/nuevo/').content.decode()
        self.assertIn('name="sede"', h)
        self.assertIn('name="jornada"', h)


class Habilitar(ColegioDePrueba):

    def test_arranca_deshabilitada_y_el_admin_la_habilita(self):
        admin = self.cliente(self.rectora)
        conf = logica.configuracion_de(self.a)
        self.assertFalse(conf.abierta)                                 # nunca sale sola
        self.assertNotIn('/prematricula/"', self.cliente().get('/').content.decode())
        self.assertContains(admin.get('/prematricula/gestion/'), 'Habilitar en el portal')
        # Un docente no puede habilitarla.
        self.cliente(self.u_docente).post('/prematricula/gestion/habilitar/', {'abrir': '1'})
        conf.refresh_from_db()
        self.assertFalse(conf.abierta)
        admin.post('/prematricula/gestion/habilitar/', {'abrir': '1'})
        conf.refresh_from_db()
        self.assertTrue(conf.abierta)
        self.assertIn('/prematricula/', self.cliente().get('/').content.decode())
        admin.post('/prematricula/gestion/habilitar/', {'abrir': '0'})
        conf.refresh_from_db()
        self.assertFalse(conf.abierta)
