"""Excusas de las fallas: la familia envía, el director de grupo o la coordinación aprueba y la asistencia queda bloqueada."""
import json
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from notas import excusas as EX
from notas.models import AdministradorColegio, AsignacionDocente, Asistencia, Excusa, Materia, Notificacion
from django.contrib.auth.models import User

from .base import CLAVE, ColegioDePrueba


def dia_habil_anterior(dia, n=1):
    while n:
        dia -= timedelta(days=1)
        if dia.weekday() < 5:
            n -= 1
    return dia


class Excusas(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ana, cls.beto, cls.caro = cls.estudiantes
        cls.sociales = Materia.objects.create(colegio=cls.a, nombre='Sociales')
        cls.asig2 = AsignacionDocente.objects.create(colegio=cls.a, docente=cls.docente, materia=cls.sociales, curso=cls.curso)
        cls.coord = User.objects.create_user('coord', password=CLAVE, first_name='Carla', last_name='Coordinadora')
        AdministradorColegio.objects.create(user=cls.coord, colegio=cls.a, cargo='COORDINADOR')

    def setUp(self):
        self.hoy = timezone.localdate()
        self.ayer = dia_habil_anterior(self.hoy)
        self.familia = self.cliente(self.ana.user)

    def enviar(self, desde=None, hasta='', **extra):
        datos = {'motivo': 'ENFERMEDAD', 'desde': (desde or self.ayer).isoformat(),
                 'hasta': hasta.isoformat() if hasta else '', 'explicacion': 'Tuvo fiebre'}
        datos.update(extra)
        return self.familia.post('/estudiante/mis-excusas/', datos)

    def test_enviar_avisa_al_director_y_a_la_coordinacion(self):
        foto = SimpleUploadedFile('incapacidad.jpg', b'\xff\xd8\xff' + b'0' * 50, content_type='image/jpeg')
        r = self.enviar(soporte=foto)
        self.assertRedirects(r, '/estudiante/mis-excusas/', fetch_redirect_response=False)
        e = Excusa.objects.get()
        self.assertEqual((e.estado, e.desde, e.hasta, e.enviada_por), ('PENDIENTE', self.ayer, self.ayer, self.ana.user))
        self.assertTrue(e.soporte)
        avisados = set(Notificacion.objects.filter(mensaje__contains='Excusa para revisar').values_list('destinatario', flat=True))
        self.assertEqual(avisados, {self.u_docente.id, self.coord.id})      # la rectora no, porque hay coordinación

    def test_fuera_de_plazo_no_se_envia(self):
        viejo = dia_habil_anterior(self.hoy, 5)
        r = self.enviar(desde=viejo)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'plazo para enviar esta excusa venció')
        self.assertFalse(Excusa.objects.exists())

    def test_se_puede_enviar_antes_de_faltar(self):
        manana = self.hoy + timedelta(days=1)
        while manana.weekday() >= 5:
            manana += timedelta(days=1)
        self.enviar(desde=manana, motivo='CITA')
        self.assertEqual(Excusa.objects.get().motivo, 'CITA')

    def test_aprobar_bloquea_la_asistencia(self):
        # Ese día ya tenía falla en Matemáticas y estaba presente en nada más
        Asistencia.objects.create(colegio=self.a, estudiante=self.ana, asignacion=self.asig, fecha=self.ayer, estado='A')
        self.enviar()
        e = Excusa.objects.get()
        r = self.cliente(self.u_docente).post(f'/excusas/{e.pk}/', {'accion': 'aprobar', 'desde': self.ayer.isoformat(),
                                                                    'hasta': self.ayer.isoformat()})
        e.refresh_from_db()
        self.assertEqual((e.estado, e.revisada_por), ('APROBADA', self.u_docente))
        dia = Asistencia.objects.filter(estudiante=self.ana, fecha=self.ayer)
        self.assertEqual(dia.count(), 2)                       # las dos clases del curso
        self.assertTrue(all(a.estado == 'A' and a.justificada and a.excusa_id == e.pk for a in dia))
        self.assertEqual(len(e.asistencias_creadas), 1)        # Sociales la creó la excusa
        self.assertTrue(Notificacion.objects.filter(destinatario=self.ana.user, mensaje__contains='aprobada').exists())
        self.assertTrue(Notificacion.objects.filter(destinatario=self.u_docente, mensaje__contains='excusa aprobada').exists())
        # El docente no la puede cambiar
        r = self.cliente(self.u_docente).post('/ajax/guardar-inasistencia/', json.dumps({
            'estudiante_id': self.ana.id, 'asignacion_id': self.asig.id, 'fecha': self.ayer.isoformat(), 'estado': 'P'}),
            content_type='application/json')
        self.assertEqual(r.status_code, 409)
        self.assertEqual(Asistencia.objects.get(estudiante=self.ana, asignacion=self.asig, fecha=self.ayer).estado, 'A')
        # En la toma de asistencia sale bloqueado
        r = self.cliente(self.u_docente).get(f'/docente/asistencia/?asignacion_id={self.asig.id}&fecha={self.ayer.isoformat()}')
        self.assertContains(r, 'Excusado')

    def test_presente_ese_dia_no_se_toca(self):
        Asistencia.objects.create(colegio=self.a, estudiante=self.ana, asignacion=self.asig, fecha=self.ayer, estado='T')
        self.enviar()
        e = Excusa.objects.get()
        EX.aprobar(e, self.coord, self.ayer, self.ayer)
        self.assertEqual(Asistencia.objects.get(estudiante=self.ana, asignacion=self.asig, fecha=self.ayer).estado, 'T')
        self.assertTrue(Asistencia.objects.get(estudiante=self.ana, asignacion=self.asig2, fecha=self.ayer).justificada)

    def test_ajustar_fechas_y_fines_de_semana(self):
        lunes = self.hoy - timedelta(days=self.hoy.weekday())
        e = Excusa.objects.create(colegio=self.a, estudiante=self.ana, desde=lunes - timedelta(days=7),
                                  hasta=lunes - timedelta(days=1))
        EX.aprobar(e, self.coord, lunes - timedelta(days=7), lunes - timedelta(days=1))   # lunes a domingo
        dias = set(Asistencia.objects.filter(excusa=e).values_list('fecha', flat=True))
        self.assertEqual(len(dias), 5)                           # sin sábado ni domingo

    def test_rechazar_pide_motivo_y_avisa(self):
        self.enviar()
        e = Excusa.objects.get()
        c = self.cliente(self.coord)
        c.post(f'/excusas/{e.pk}/', {'accion': 'rechazar', 'respuesta': ''})
        e.refresh_from_db()
        self.assertEqual(e.estado, 'PENDIENTE')
        c.post(f'/excusas/{e.pk}/', {'accion': 'rechazar', 'respuesta': 'Falta la incapacidad'})
        e.refresh_from_db()
        self.assertEqual(e.estado, 'RECHAZADA')
        self.assertTrue(Notificacion.objects.filter(destinatario=self.ana.user, mensaje__contains='Falta la incapacidad').exists())
        self.assertFalse(Asistencia.objects.exists())

    def test_anular_deshace(self):
        Asistencia.objects.create(colegio=self.a, estudiante=self.ana, asignacion=self.asig, fecha=self.ayer, estado='A')
        self.enviar()
        e = Excusa.objects.get()
        EX.aprobar(e, self.coord, self.ayer, self.ayer)
        self.cliente(self.coord).post(f'/excusas/{e.pk}/', {'accion': 'anular'})
        e.refresh_from_db()
        self.assertEqual(e.estado, 'ANULADA')
        quedan = Asistencia.objects.filter(estudiante=self.ana, fecha=self.ayer)
        self.assertEqual(quedan.count(), 1)                    # la que ya existía; la creada se borró
        self.assertFalse(quedan.get().justificada)

    def test_quien_ve_y_aprueba(self):
        self.enviar()
        e = Excusa.objects.get()
        self.assertEqual(self.cliente(self.beto.user).get(f'/excusas/{e.pk}/').status_code, 404)
        self.assertEqual(self.cliente(self.beto.user).get('/excusas/').status_code, 403)
        otro = User.objects.create_user('otro', password=CLAVE)
        from notas.models import Docente
        Docente.objects.create(colegio=self.a, user=otro)
        self.assertEqual(self.cliente(otro).get('/excusas/').status_code, 403)
        # La familia la ve pero no la aprueba
        self.familia.post(f'/excusas/{e.pk}/', {'accion': 'aprobar'})
        e.refresh_from_db()
        self.assertEqual(e.estado, 'PENDIENTE')
        self.assertContains(self.cliente(self.u_docente).get('/excusas/'), 'Ana')
        self.assertContains(self.cliente(self.rectora).get('/excusas/'), 'Ana')

    def test_la_familia_cancela_si_esta_pendiente(self):
        self.enviar()
        e = Excusa.objects.get()
        self.familia.post(f'/excusas/{e.pk}/', {'accion': 'cancelar'})
        self.assertFalse(Excusa.objects.exists())

    def test_registrar_en_papel_sin_plazo(self):
        viejo = dia_habil_anterior(self.hoy, 8)
        self.cliente(self.coord).post('/excusas/', {'accion': 'registrar', 'estudiante': self.beto.id, 'motivo': 'CALAMIDAD',
                                                    'desde': viejo.isoformat(), 'explicacion': 'Trajo la carta'})
        e = Excusa.objects.get()
        self.assertEqual((e.estudiante, e.enviada_por, e.fuera_de_plazo), (self.beto, self.coord, True))

    def test_boletin_cuenta_las_excusadas(self):
        from notas.boletin.logic import get_datos_boletin_curso
        from notas.models import AreaConocimiento, PonderacionAreaMateria
        area = AreaConocimiento.objects.create(colegio=self.a, nombre='Matemáticas')
        PonderacionAreaMateria.objects.create(colegio=self.a, area=area, materia=self.materia, peso_porcentual=100)
        self.p1.fecha_inicio, self.p1.fecha_fin = self.hoy - timedelta(days=60), self.hoy + timedelta(days=5)
        self.p1.save()
        otro = dia_habil_anterior(self.ayer)
        Asistencia.objects.create(colegio=self.a, estudiante=self.ana, asignacion=self.asig, fecha=otro, estado='A')
        Asistencia.objects.create(colegio=self.a, estudiante=self.ana, asignacion=self.asig, fecha=self.ayer, estado='A')
        e = Excusa.objects.create(colegio=self.a, estudiante=self.ana, desde=self.ayer, hasta=self.ayer)
        EX.aprobar(e, self.coord, self.ayer, self.ayer)
        datos = get_datos_boletin_curso(self.a, self.curso, self.p1, estudiante_especifico=self.ana)
        datos = datos[0] if isinstance(datos, list) else next(iter(datos.values()))
        mate = next(m for area in datos['areas'] for m in area['materias'] if m['nombre'] == 'Matemáticas')
        self.assertEqual((mate['inasistencias'], mate['inasistencias_excusa']), (2, 1))

    def test_plazo_configurable(self):
        self.cliente(self.rectora).post('/excusas/', {'accion': 'plazo', 'dias': '5'})
        self.a.refresh_from_db()
        self.assertEqual(self.a.dias_plazo_excusa, 5)
        self.cliente(self.u_docente).post('/excusas/', {'accion': 'plazo', 'dias': '0'})   # el director no lo cambia
        self.a.refresh_from_db()
        self.assertEqual(self.a.dias_plazo_excusa, 5)

    def test_paginas(self):
        self.assertContains(self.familia.get('/estudiante/mis-excusas/'), 'Enviar una excusa')
        self.assertContains(self.cliente(self.u_docente).get('/dashboard/', follow=True), '/excusas/')

    def test_el_kiosko_respeta_la_excusa(self):
        e = Excusa.objects.create(colegio=self.a, estudiante=self.ana, desde=self.hoy, hasta=self.hoy)
        if self.hoy.weekday() >= 5:
            return                                   # fin de semana: no hay día hábil que bloquear
        EX.aprobar(e, self.coord, self.hoy, self.hoy)
        c = self.cliente(self.u_docente)
        c.post('/asistencia/kiosko/', {'asignacion_id': self.asig.id})
        j = c.post('/asistencia/kiosko/registrar/', {'codigo': self.ana.asegurar_codigo_carnet()}).json()
        self.assertFalse(j['ok'])
        self.assertIn('excusa', j['mensaje'])
        self.assertEqual(Asistencia.objects.get(estudiante=self.ana, asignacion=self.asig, fecha=self.hoy).estado, 'A')
