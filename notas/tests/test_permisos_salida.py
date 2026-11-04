"""Módulo Permisos: dar el pase, verificarlo con el carné o buscando, el regreso y los avisos."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from notas.models import Curso, Docente, Notificacion, PermisoSalida, VerificacionPermiso

from .base import CLAVE, ColegioDePrueba


class PermisosSalida(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos or []) + ['permisos']
        cls.a.save(update_fields=['modulos_activos'])
        cls.ana, cls.beto, cls.caro = cls.estudiantes
        cls.otro_profe = User.objects.create_user('otro', password=CLAVE, first_name='Olga', last_name='Otra')
        Docente.objects.create(colegio=cls.a, user=cls.otro_profe)

    def setUp(self):
        self.profe = self.cliente(self.u_docente)

    def dar(self, est=None, destino='BANO', minutos='10', cliente=None):
        return (cliente or self.profe).post('/permisos/dar/', {'estudiante': (est or self.ana).id, 'destino': destino,
                                                               'minutos': minutos, 'asignacion': self.asig.id})

    def test_dar_permiso_y_aviso_al_estudiante(self):
        self.dar()
        p = PermisoSalida.objects.get()
        self.assertEqual((p.estudiante, p.otorgado_por, p.destino, p.asignacion), (self.ana, self.u_docente, 'BANO', self.asig))
        self.assertAlmostEqual((p.vence - p.inicio).total_seconds(), 600, delta=5)
        self.assertTrue(Notificacion.objects.filter(destinatario=self.ana.user, mensaje__contains='Tienes permiso').exists())
        # Lo ve en su panel y en su carné
        c = self.cliente(self.ana.user)
        self.assertContains(c.get('/mi-carne/'), 'Tienes permiso para salir: Baño')
        self.assertContains(c.get('/dashboard/', follow=True), 'Tienes permiso para salir')

    def test_no_dos_permisos_a_la_vez(self):
        self.dar()
        self.dar(destino='ENFERMERIA')
        self.assertEqual(PermisoSalida.objects.count(), 1)

    def test_docente_ajeno_no_da_permiso(self):
        self.dar(cliente=self.cliente(self.otro_profe))
        self.assertFalse(PermisoSalida.objects.exists())

    def test_salida_del_colegio_solo_directivos(self):
        self.dar(destino='SALIDA')
        self.assertFalse(PermisoSalida.objects.exists())
        self.dar(destino='SALIDA', cliente=self.cliente(self.rectora))
        p = PermisoSalida.objects.get()
        self.assertEqual(timezone.localtime(p.vence).date(), timezone.localdate())

    def test_verificar_con_el_carne(self):
        otro = self.cliente(self.otro_profe)          # cualquier docente verifica
        codigo = self.ana.asegurar_codigo_carnet()
        j = otro.post('/permisos/verificar/', {'texto': f'https://a.mcolegio.com.co/c/{codigo}/'}).json()
        self.assertEqual(j['resultado'], 'SIN_PERMISO')
        self.dar()
        j = otro.post('/permisos/verificar/', {'texto': codigo}).json()
        self.assertEqual(j['resultado'], 'CON_PERMISO')
        self.assertEqual(j['permiso']['destino'], 'Baño')
        self.assertIn('Pedro Profe', j['permiso']['otorgado_por'])
        # Vencido
        PermisoSalida.objects.update(vence=timezone.now() - timedelta(minutes=7))
        j = otro.post('/permisos/verificar/', {'texto': codigo}).json()
        self.assertEqual(j['resultado'], 'VENCIDO')
        self.assertGreaterEqual(j['permiso']['vencido_hace'], 6)
        self.assertEqual(VerificacionPermiso.objects.count(), 3)

    def test_verificar_buscando_sin_carne(self):
        self.dar()
        otro = self.cliente(self.otro_profe)
        r = otro.get('/permisos/buscar/', {'q': 'ana prueba'}).json()
        self.assertEqual([(e['id'], e['con_permiso']) for e in r['estudiantes']], [(self.ana.id, True)])
        j = otro.post('/permisos/verificar/', {'estudiante': self.ana.id}).json()
        self.assertEqual(j['resultado'], 'CON_PERMISO')

    def test_escanear_con_la_camara_del_celular(self):
        codigo = self.beto.asegurar_codigo_carnet()
        r = self.cliente(self.otro_profe).get(f'/c/{codigo}/')
        self.assertContains(r, 'No tiene permiso')
        self.assertContains(r, 'Avisar al director de grupo')
        # Sin el módulo, el QR sigue funcionando como antes (pide el PIN)
        self.a.modulos_activos = [m for m in self.a.modulos_activos if m != 'permisos']
        self.a.save(update_fields=['modulos_activos'])
        self.assertContains(self.cliente(self.otro_profe).get(f'/c/{codigo}/'), 'Escribe tu PIN')

    def test_reportar_posible_evasion(self):
        otro = self.cliente(self.otro_profe)
        j = otro.post('/permisos/verificar/', {'estudiante': self.beto.id}).json()
        r = otro.post(f'/permisos/verificacion/{j["verificacion"]}/reportar/').json()
        self.assertTrue(r['ok'])
        avisados = set(Notificacion.objects.filter(mensaje__contains='Posible evasión').values_list('destinatario', flat=True))
        self.assertEqual(avisados, {self.rectora.id, self.u_docente.id})      # administración y director de grupo
        self.assertTrue(VerificacionPermiso.objects.get().reportado)

    def test_regreso_y_quien_esta_fuera(self):
        self.dar()
        r = self.profe.get(f'/permisos/?asignacion={self.asig.id}')
        self.assertContains(r, 'Fuera del salón ahora')
        self.assertContains(r, 'Regresó')
        r = self.profe.get(f'/docente/asistencia/?asignacion_id={self.asig.id}&fecha={timezone.localdate().isoformat()}')
        self.assertContains(r, 'Fuera del salón con permiso')
        p = PermisoSalida.objects.get()
        self.profe.post(f'/permisos/{p.pk}/regreso/')
        p.refresh_from_db()
        self.assertIsNotNone(p.regreso)
        self.assertEqual(p.regreso_marcado_por, self.u_docente)
        self.assertEqual(self.cliente(self.otro_profe).post('/permisos/verificar/', {'estudiante': self.ana.id}).json()['resultado'],
                         'SIN_PERMISO')

    def test_historial_para_directivos(self):
        self.dar()
        r = self.cliente(self.rectora).get('/permisos/historial/')
        self.assertContains(r, 'Prueba Ana')
        self.assertEqual(self.cliente(self.otro_profe).get('/permisos/historial/').status_code, 403)

    def test_estudiante_no_entra(self):
        self.assertEqual(self.cliente(self.ana.user).get('/permisos/').status_code, 403)
        self.assertEqual(self.cliente(self.ana.user).post('/permisos/verificar/', {'estudiante': self.beto.id}).status_code, 403)

    def test_modulo_apagado(self):
        self.a.modulos_activos = []
        self.a.save(update_fields=['modulos_activos'])
        r = self.profe.get('/permisos/')
        self.assertNotEqual(r.status_code, 200)
