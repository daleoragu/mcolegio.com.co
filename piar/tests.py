# -*- coding: utf-8 -*-
"""PIAR: quién lo crea, quién llena qué, el avance, el acta y la familia."""
import datetime

from notas.models import AsignacionDocente, Docente, Materia
from notas.tests.base import CLAVE, ColegioDePrueba
from django.contrib.auth.models import User

from . import logica
from .models import AjustePiar, ConfiguracionPiar, Piar

HOY = datetime.date(2026, 6, 1)


class PiarTests(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ana = cls.estudiantes[0]
        u = User.objects.create_user('otra', password=CLAVE, first_name='Olga', last_name='Otra')
        cls.otra = Docente.objects.create(colegio=cls.a, user=u)
        cls.ingles = Materia.objects.create(colegio=cls.a, nombre='Inglés')
        AsignacionDocente.objects.create(colegio=cls.a, docente=cls.otra, materia=cls.ingles, curso=cls.curso)
        u2 = User.objects.create_user('ajena', password=CLAVE)
        cls.ajena = Docente.objects.create(colegio=cls.a, user=u2)   # sin clases en el curso

    def _crear(self, ano=2026):
        return logica.crear(self.ana, ano, self.rectora)[0]

    def test_crear_marca_inclusion_y_copia_el_ano_anterior(self):
        viejo = Piar.objects.create(colegio=self.a, estudiante=self.ana, ano_lectivo=2025, categoria='TEA',
                                    fortalezas='Memoria visual', compromisos_familia='Terapias')
        piar, copiado = logica.crear(self.ana, 2026, self.rectora)
        self.assertTrue(copiado)
        self.assertEqual((piar.categoria, piar.fortalezas, piar.compromisos_familia), ('TEA', 'Memoria visual', ''))
        self.ana.refresh_from_db()
        self.assertTrue(self.ana.es_inclusion)
        self.assertEqual(logica.crear(self.ana, 2026)[0], piar)        # no duplica
        self.assertNotEqual(piar, viejo)

    def test_panel_y_quien_puede_crear(self):
        c = self.cliente(self.rectora)
        r = c.get('/piar/?q=ana')
        self.assertContains(r, 'Crear PIAR')
        r = c.post('/piar/', {'accion': 'crear', 'estudiante': self.ana.id})
        piar = Piar.objects.get()
        self.assertRedirects(r, f'/piar/{piar.pk}/', fetch_redirect_response=False)
        self.assertContains(c.get('/piar/'), 'En elaboración')
        # Un docente sin dirección de grupo ni rol de apoyo no crea.
        beto = self.estudiantes[1]
        self.assertEqual(self.cliente(self.otra.user).post('/piar/', {'accion': 'crear', 'estudiante': beto.id}).status_code, 403)
        # El director de grupo sí.
        self.cliente(self.u_docente).post('/piar/', {'accion': 'crear', 'estudiante': beto.id})
        self.assertTrue(Piar.objects.filter(estudiante=beto).exists())

    def test_cada_docente_llena_solo_su_asignatura(self):
        piar = self._crear()
        otra = self.cliente(self.otra.user)
        url_ing = f'/piar/{piar.pk}/ajuste/{self.ingles.pk}/{self.p1.pk}/'
        url_mat = f'/piar/{piar.pk}/ajuste/{self.materia.pk}/{self.p1.pk}/'
        self.assertEqual(otra.get(url_ing).status_code, 200)
        self.assertEqual(otra.get(url_mat).status_code, 403)
        otra.post(url_ing, {'objetivos': 'Saludos', 'tipos': ['DIDACTICO', 'EVALUATIVO'], 'ajustes': 'Tarjetas con imágenes'})
        aj = AjustePiar.objects.get()
        self.assertEqual((aj.docente, aj.tipos_texto()), (self.otra, 'Didácticos, Evaluativos'))
        # La docente ve el PIAR pero no edita la información general.
        r = otra.get(f'/piar/{piar.pk}/')
        self.assertNotContains(r, 'Guardar información')
        otra.post(f'/piar/{piar.pk}/', {'que': 'general', 'categoria': 'FISICA'})
        piar.refresh_from_db()
        self.assertEqual(piar.categoria, '')
        # Una docente sin clases en el curso no lo ve.
        self.assertEqual(self.cliente(self.ajena.user).get(f'/piar/{piar.pk}/').status_code, 403)

    def test_docente_de_apoyo_coordina_todo(self):
        piar = self._crear()
        ConfiguracionPiar.de(self.a).docentes_apoyo.add(self.ajena)
        c = self.cliente(self.ajena.user)
        self.assertContains(c.get(f'/piar/{piar.pk}/'), 'Guardar información')
        self.assertEqual(c.get(f'/piar/{piar.pk}/ajuste/{self.materia.pk}/{self.p2.pk}/').status_code, 200)

    def test_traer_ajustes_del_periodo_anterior(self):
        piar = self._crear()
        AjustePiar.objects.create(piar=piar, materia=self.materia, periodo=self.p1, ajustes='Ábaco y tiempo extra')
        r = self.cliente(self.u_docente).get(f'/piar/{piar.pk}/ajuste/{self.materia.pk}/{self.p2.pk}/?copiar=1')
        self.assertContains(r, 'Ábaco y tiempo extra')

    def test_avance_y_pendientes(self):
        piar = self._crear()
        listos, esperado, _ = logica.avance(piar, hoy=self.p2.fecha_inicio)
        self.assertEqual((listos, esperado), (0, 4))                    # 2 asignaturas × 2 periodos empezados
        AjustePiar.objects.create(piar=piar, materia=self.materia, periodo=self.p1, ajustes='x')
        AjustePiar.objects.create(piar=piar, materia=self.materia, periodo=self.p2, ajustes='')   # empezado, no cuenta
        self.assertEqual(logica.avance(piar, hoy=self.p2.fecha_inicio)[:2], (1, 4))
        # Al docente de Matemáticas solo le falta el segundo periodo; a la de Inglés, los dos.
        self.assertContains(self.cliente(self.u_docente).get('/piar/'), 'Matemáticas · Segundo Periodo')
        r = self.cliente(self.otra.user).get('/piar/')
        self.assertContains(r, 'Inglés · Primer Periodo')
        self.assertNotContains(r, 'Matemáticas ·')

    def test_acta_deja_vigente_y_familia_descarga(self):
        piar = self._crear()
        fam = self.cliente(self.ana.user)
        self.assertEqual(fam.get(f'/piar/{piar.pk}/piar.pdf').status_code, 403)   # aún no compartido
        self.cliente(self.rectora).post(f'/piar/{piar.pk}/', {'que': 'acta', 'compromisos_familia': 'Asistir a terapias',
                                                              'fecha_acta': '2026-03-10', 'compartido_familia': 'on'})
        piar.refresh_from_db()
        self.assertEqual(piar.estado, 'VIGENTE')
        self.assertContains(fam.get('/piar/mi-piar/'), 'PIAR 2026')
        for url in (f'/piar/{piar.pk}/piar.pdf', f'/piar/{piar.pk}/acta.pdf'):
            r = fam.get(url)
            self.assertEqual((r.status_code, r['Content-Type']), (200, 'application/pdf'))
        # Otro estudiante no.
        self.assertEqual(self.cliente(self.estudiantes[1].user).get(f'/piar/{piar.pk}/piar.pdf').status_code, 403)

    def test_modulo_apagado(self):
        self.a.modulos_activos = ['circulares']
        self.a.save()
        self.assertEqual(self.cliente(self.rectora).get('/piar/').status_code, 403)
        self.assertNotContains(self.cliente(self.rectora).get('/panel-administrador/'), '/piar/')

    def test_menus(self):
        self._crear()
        self.assertContains(self.cliente(self.u_docente).get('/panel-docente/'), "/piar/")
        self.assertContains(self.cliente(self.ana.user).get('/panel-estudiante/', follow=True), 'Mi PIAR')


class MigracionesDeModulos(ColegioDePrueba):
    """Al instalar: cartera apagada en los colegios que ya existían, PIAR encendido (salvo plan Básico)."""

    def test_cartera_apagada_y_piar_encendido(self):
        import importlib
        from django.apps import apps
        self.a.modulos_activos = ['portal', 'actas', 'cartera']
        self.a.save()
        self.b.modulos_activos = ['circulares', 'certificados']
        self.b.save()
        importlib.import_module('cartera.migrations.0002_apagada_en_colegios_existentes').apagar(apps, None)
        importlib.import_module('piar.migrations.0002_encender_piar').encender(apps, None)
        self.a.refresh_from_db()
        self.b.refresh_from_db()
        self.assertEqual(self.a.modulos_activos, ['portal', 'actas', 'piar'])
        self.assertEqual(self.b.modulos_activos, ['circulares', 'certificados'])
