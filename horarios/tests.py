# -*- coding: utf-8 -*-
"""Horarios: jornadas, datos para el generador, el generador, importar, publicar y «Mi horario»."""
import datetime
import io
import json

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook

from notas.models import AsignacionDocente, Docente, Materia
from notas.models.comunicaciones import Notificacion
from notas.modulos import TODOS
from notas.tests.base import CLAVE, ColegioDePrueba

from . import intercambio, nucleo
from .models import Franja, Horario, Jornada, Sesion


class Base(ColegioDePrueba):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(TODOS)          # Premium
        cls.a.save()
        cls.asig.intensidad_horaria_semanal = 4
        cls.asig.save()
        u = User.objects.create_user('ingles', password=CLAVE, first_name='Inés', last_name='Inglés')
        cls.doc2 = Docente.objects.create(colegio=cls.a, user=u)
        cls.ingles = Materia.objects.create(colegio=cls.a, nombre='Inglés')
        cls.asig2 = AsignacionDocente.objects.create(colegio=cls.a, docente=cls.doc2, materia=cls.ingles, curso=cls.curso,
                                                     intensidad_horaria_semanal=3)
        cls.j = Jornada.objects.create(colegio=cls.a, nombre='Mañana', dias=[1, 2, 3, 4, 5])
        cls.j.cursos.add(cls.curso)
        t = [('07:00', '07:55'), ('07:55', '08:50'), ('08:50', '09:20', True), ('09:20', '10:15'), ('10:15', '11:10')]
        cls.f = []
        for i, x in enumerate(t):
            cls.f.append(Franja.objects.create(jornada=cls.j, orden=i, inicio=x[0], fin=x[1], descanso=len(x) > 2))


class Generador(Base):

    def test_exportar_generar_importar_publicar(self):
        c = self.cliente(self.rectora)
        r = c.get('/horarios/generador/datos/')
        self.assertIn('.mch', r['Content-Disposition'])
        datos = nucleo.Datos(nucleo.leer_json(r.content.decode(), nucleo.TIPO_DATOS))
        self.assertEqual(datos.ih(self.asig.id), 4)
        self.assertEqual(nucleo.diagnostico(datos, nucleo.condiciones_vacias()), [])
        cond = nucleo.condiciones_vacias()
        cond['fijas'] = [{'asignacion': self.asig.id, 'dia': 1, 'franja': self.f[0].id}]
        cond['docentes'][str(self.doc2.id)] = {'no_puede': [f'{d}-{self.f[0].id}' for d in range(1, 6)]}
        cond['materias'][str(self.materia.id)] = {'doble': True}
        res = nucleo.generar(datos, cond, segundos=2, semilla=1)
        self.assertEqual(res['sin_ubicar'], [])
        self.assertEqual(nucleo.revisar(datos, res['sesiones'], cond), [])
        ses = res['sesiones']
        self.assertIn({'asignacion': self.asig.id, 'curso': self.curso.id, 'dia': 1, 'franja': self.f[0].id, 'fijada': True}, ses)
        self.assertFalse(any(s['asignacion'] == self.asig2.id and s['franja'] == self.f[0].id for s in ses))
        archivo = json.dumps(nucleo.resultado(datos, ses, 'Alternativa 1', {'huecos': res['huecos']})).encode()
        r = c.post('/horarios/importar/', {'archivo': SimpleUploadedFile('h.mchr', archivo)})
        h = Horario.objects.get()
        self.assertRedirects(r, f'/horarios/{h.pk}/', fetch_redirect_response=False)
        self.assertEqual(h.sesiones.count(), 7)
        self.assertContains(c.get(f'/horarios/{h.pk}/'), 'Publicar y avisar')
        self.assertContains(c.get(f'/horarios/{h.pk}/?ver=docente&id={self.doc2.id}'), self.curso.nombre)
        c.post(f'/horarios/{h.pk}/accion/', {'que': 'publicar'})
        h.refresh_from_db()
        self.assertEqual(h.estado, 'PUBLICADO')
        avisados = set(Notificacion.objects.values_list('destinatario_id', flat=True))
        self.assertTrue({self.u_docente.id, self.doc2.user_id, self.estudiantes[0].user_id} <= avisados)
        self.assertContains(self.cliente(self.estudiantes[0].user).get('/horarios/mi-horario/'), 'Inglés')
        self.assertContains(self.cliente(self.doc2.user).get('/horarios/mi-horario/'), self.curso.nombre)
        self.assertEqual(c.get(f'/horarios/{h.pk}/pdf/')['Content-Type'], 'application/pdf')

    def test_archivo_ajeno_o_alterado(self):
        d = intercambio.datos_del_colegio(self.a)
        r = nucleo.resultado(nucleo.Datos(d), [], 'x')
        r['origen']['firma'] = 'falsa'
        resp = self.cliente(self.rectora).post('/horarios/importar/', {'archivo': SimpleUploadedFile(
            'h.mchr', json.dumps(r).encode())}, follow=True)
        self.assertContains(resp, 'no salió de los datos exportados')
        self.assertFalse(Horario.objects.exists())

    def test_no_publica_con_choques(self):
        h = Horario.objects.create(colegio=self.a, nombre='Malo')
        Sesion.objects.create(horario=h, curso=self.curso, asignacion=self.asig, dia=1, franja=self.f[0])
        otro = self.crear_estudiante  # noqa
        from notas.models import Curso
        c2 = Curso.objects.create(colegio=self.a, nombre='602', grado=6, subgrupo='2')
        self.j.cursos.add(c2)
        a3 = AsignacionDocente.objects.create(colegio=self.a, docente=self.docente, materia=self.ingles, curso=c2,
                                              intensidad_horaria_semanal=1)
        Sesion.objects.create(horario=h, curso=c2, asignacion=a3, dia=1, franja=self.f[0])
        r = self.cliente(self.rectora).get(f'/horarios/{h.pk}/')
        self.assertContains(r, 'queda en dos clases')
        self.cliente(self.rectora).post(f'/horarios/{h.pk}/accion/', {'que': 'publicar'})
        h.refresh_from_db()
        self.assertEqual(h.estado, 'BORRADOR')

    def test_premium_y_modulo(self):
        self.a.modulos_activos = [m for m in TODOS if m != 'generador_horarios']
        self.a.save()
        c = self.cliente(self.rectora)
        self.assertEqual(c.get('/horarios/generador/datos/').status_code, 403)
        self.assertContains(c.get('/horarios/'), 'plan Premium')
        self.a.modulos_activos = ['circulares']
        self.a.save()
        self.assertEqual(c.get('/horarios/').status_code, 403)


class Plataforma(Base):

    def test_crear_jornada_con_horas(self):
        c = self.cliente(self.rectora)
        r = c.post('/horarios/jornada/nueva/', {'accion': 'generar_franjas', 'nombre': 'Tarde', 'dias': ['1', '2', '3'],
                                                 'g_inicio': '12:30', 'g_duracion': '50', 'g_clases': '5',
                                                 'g_descanso_tras': '2', 'g_descanso_min': '20'})
        j = Jornada.objects.get(nombre='Tarde')
        fr = list(j.franjas.all())
        self.assertEqual(len(fr), 6)
        self.assertTrue(fr[2].descanso)
        self.assertEqual((fr[3].inicio, j.dias), (datetime.time(14, 30), [1, 2, 3]))

    def test_importar_excel(self):
        wb = Workbook()
        ws = wb.active
        ws.append(['Curso', 'Día', 'Hora', 'Asignatura'])
        ws.append([self.curso.nombre, 'Lunes', 1, 'Matemáticas'])
        ws.append([self.curso.nombre, 'martes', '09:20', 'ingles'])
        ws.append([self.curso.nombre, 'Miércoles', 9, 'Matemáticas'])
        b = io.BytesIO()
        wb.save(b)
        r = self.cliente(self.rectora).post('/horarios/importar/', {'archivo': SimpleUploadedFile('ghc.xlsx', b.getvalue())},
                                            follow=True)
        h = Horario.objects.get()
        self.assertEqual(set(h.sesiones.values_list('dia', 'franja_id')), {(1, self.f[0].id), (2, self.f[3].id)})
        self.assertContains(r, 'Fila 4')

    def test_mi_horario_sin_publicar_y_menus(self):
        self.assertContains(self.cliente(self.u_docente).get('/horarios/mi-horario/'), 'todavía no ha publicado')
        self.assertContains(self.cliente(self.rectora).get('/panel-administrador/'), '/horarios/')
        self.assertContains(self.cliente(self.u_docente).get('/panel-docente/'), '/horarios/mi-horario/')


class AppDeEscritorio(Base):
    """La lógica de la app de Windows (sin la ventana)."""

    def test_proyecto_completo(self):
        import os
        import tempfile
        from .proyecto import Proyecto
        tmp = tempfile.mkdtemp()
        ruta = os.path.join(tmp, 'datos.mch')
        with open(ruta, 'wb') as fh:
            fh.write(intercambio.archivo_datos(self.a))
        p = Proyecto.abrir_datos(ruta)
        self.assertIsNone(p.agregar_fija(self.asig.id, 2, self.f[1].id))
        self.assertIn('dos clases', p.agregar_fija(self.asig2.id, 2, self.f[1].id))
        self.assertIn('no es de la jornada', p.agregar_fija(self.asig.id, 2, self.f[2].id))   # el descanso
        self.assertTrue(p.alternar_no_puede(self.doc2.id, 1, self.f[0].id))
        p.regla(self.ingles.id)['primeras'] = True
        p.poner_ih(self.asig2.id, 2)
        alts = p.generar(cuantas=2, segundos=1)
        self.assertEqual(len(alts), 2)
        self.assertEqual(alts[0]['horas_sin_ubicar'], 0)
        self.assertEqual(alts[0]['choques'], [])
        self.assertEqual(sum(1 for s in alts[0]['sesiones'] if s['asignacion'] == self.asig2.id), 2)
        t = p.tabla_curso(alts[0], self.curso.id)
        self.assertEqual(len(t['filas']), 5)
        self.assertEqual(len(p.tablas_docente(alts[0], self.doc2.id)), 1)
        p.guardar(os.path.join(tmp, 'p.mchp'))
        p2 = Proyecto.abrir(os.path.join(tmp, 'p.mchp'))
        self.assertEqual(len(p2.cond['fijas']), 1)
        p2 = p2.actualizar_datos(ruta)
        self.assertEqual(p2.cond['ih'], {str(self.asig2.id): 2})
        p.exportar_excel(alts[0], os.path.join(tmp, 'h.xlsx'))
        salida = os.path.join(tmp, 'h.mchr')
        p.exportar_resultado(alts[0], salida)
        with open(salida, 'rb') as fh:
            r = self.cliente(self.rectora).post('/horarios/importar/', {'archivo': SimpleUploadedFile('h.mchr', fh.read())})
        h = Horario.objects.get()
        self.assertEqual(h.sesiones.count(), 6)
        self.assertEqual(h.informe['choques'], [])
