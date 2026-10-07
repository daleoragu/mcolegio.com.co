# notas/tests/test_sedes.py
"""Sedes del colegio: gestión, cursos por sede, portal y filtros."""
from django.urls import reverse

from notas.models import Curso, Sede

from .base import ColegioDePrueba


class Sedes(ColegioDePrueba):

    def setUp(self):
        self.c = self.cliente(self.rectora)

    def crear(self, **datos):
        base = {'nombre': 'Sede Norte', 'activa': 'on', 'jornadas': ['MANANA', 'TARDE'],
                'niveles': ['PRI'], 'direccion': 'Calle 1 # 2-3', 'telefono': '300 123 4567'}
        base.update(datos)
        return self.c.post('/admin/sedes/crear/', base)

    def test_crear_sede_y_la_primera_es_la_principal(self):
        r = self.crear(cursos_enviados='1', cursos=[self.curso.id])
        self.assertRedirects(r, '/admin/sedes/', fetch_redirect_response=False)
        sede = Sede.objects.get()
        self.assertEqual(sede.colegio, self.a)
        self.assertTrue(sede.es_principal)
        self.assertEqual(sede.lista_jornadas(), ['Mañana', 'Tarde'])
        self.curso.refresh_from_db()
        self.assertEqual(self.curso.sede, sede)
        h = self.c.get('/admin/sedes/').content.decode()
        self.assertIn('Sede Norte', h)
        self.assertIn('1</strong> curso', h)

    def test_solo_una_principal_y_nombres_sin_repetir(self):
        self.crear()
        self.crear(nombre='Sede Sur', es_principal='on')
        self.assertEqual(list(Sede.objects.filter(es_principal=True).values_list('nombre', flat=True)),
                         ['Sede Sur'])
        r = self.crear(nombre='sede norte')
        self.assertContains(r, 'Ya hay una sede llamada')

    def test_un_docente_no_entra_a_sedes(self):
        r = self.cliente(self.u_docente).get('/admin/sedes/')
        self.assertNotEqual(r.status_code, 200)

    def test_otro_colegio_no_ve_ni_edita_sedes_ajenas(self):
        ajena = Sede.objects.create(colegio=self.b, nombre='Ajena')
        self.assertEqual(self.c.get(f'/admin/sedes/{ajena.id}/editar/').status_code, 404)
        self.assertNotIn('Ajena', self.c.get('/admin/sedes/').content.decode())

    def test_eliminar_sede_deja_los_cursos_sin_sede(self):
        sede = Sede.objects.create(colegio=self.a, nombre='Rural')
        self.curso.sede = sede
        self.curso.save()
        self.c.post(f'/admin/sedes/{sede.id}/eliminar/')
        self.curso.refresh_from_db()
        self.assertIsNone(self.curso.sede)

    def test_formulario_de_curso_pide_sede_solo_si_hay(self):
        self.assertNotIn('name="sede"', self.c.get('/admin/gestion-academica/cursos/crear/').content.decode())
        norte = Sede.objects.create(colegio=self.a, nombre='Norte')
        sur = Sede.objects.create(colegio=self.a, nombre='Sur')
        self.assertIn('name="sede"', self.c.get('/admin/gestion-academica/cursos/crear/').content.decode())
        # PRIMERO grado único en la Norte y en la Sur: se permite, con nombres distintos.
        r1 = self.c.post('/admin/gestion-academica/cursos/crear/',
                         {'sede': norte.id, 'grado': '1', 'subgrupo': '', 'nombre': 'PRIMERO NORTE',
                          'formato_nombre': ''})
        self.assertEqual(r1.status_code, 302, r1.content.decode()[:2000])
        r2 = self.c.post('/admin/gestion-academica/cursos/crear/',
                         {'sede': sur.id, 'grado': '1', 'subgrupo': '', 'nombre': 'PRIMERO SUR',
                          'formato_nombre': ''})
        self.assertEqual(r2.status_code, 302)
        # En la misma sede, no.
        r3 = self.c.post('/admin/gestion-academica/cursos/crear/',
                         {'sede': sur.id, 'grado': '1', 'subgrupo': '', 'nombre': 'PRIMERO B',
                          'formato_nombre': ''})
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(Curso.objects.get(nombre='PRIMERO SUR').sede, sur)

    def test_promocion_sugiere_curso_de_la_misma_sede(self):
        norte = Sede.objects.create(colegio=self.a, nombre='Norte')
        sur = Sede.objects.create(colegio=self.a, nombre='Sur')
        c1n = Curso.objects.create(colegio=self.a, nombre='PRIMERO NORTE', grado=1, sede=norte)
        Curso.objects.create(colegio=self.a, nombre='SEGUNDO SUR', grado=2, sede=sur)
        c2n = Curso.objects.create(colegio=self.a, nombre='SEGUNDO NORTE', grado=2, sede=norte)
        self.assertEqual(c1n.curso_siguiente_sugerido(), c2n)

    def test_portal_muestra_solo_las_sedes_activas(self):
        Sede.objects.create(colegio=self.a, nombre='Sede Visible', direccion='Cra 5',
                            enlace_mapa='https://maps.app.goo.gl/x', jornadas='MANANA')
        Sede.objects.create(colegio=self.a, nombre='Sede Cerrada', activa=False)
        Sede.objects.create(colegio=self.b, nombre='De otro colegio')
        h = self.cliente().get('/ajax/sedes/').content.decode()
        self.assertIn('Sede Visible', h)
        self.assertIn('Cómo llegar', h)
        self.assertIn('Mañana', h)
        self.assertNotIn('Sede Cerrada', h)
        self.assertNotIn('De otro colegio', h)

    def test_filtros_por_sede(self):
        norte = Sede.objects.create(colegio=self.a, nombre='Norte')
        Sede.objects.create(colegio=self.a, nombre='Sur')
        self.curso.sede = norte
        self.curso.save()
        otro = Curso.objects.create(colegio=self.a, nombre='701', grado=7)
        # Alertas: al escoger la sede solo quedan sus cursos.
        r = self.c.get('/alertas-tempranas/', {'sede': norte.id})
        self.assertEqual(r.status_code, 200)
        self.assertEqual([c.id for c in r.context['cursos']], [self.curso.id])
        self.assertNotIn(otro, r.context['cursos'])
        # Boletines, sábana y estadísticas: selector de sede y cada curso con su sede.
        for url in ('/reportes/selector-boletin/', reverse('notas:selector_sabana'),
                    reverse('notas:panel_estadisticas')):
            h = self.c.get(url).content.decode()
            self.assertIn('Todas las sedes', h, url)
            self.assertIn(f'data-sede="{norte.id}"', h, url)

    def test_sin_varias_sedes_no_sale_el_filtro(self):
        Sede.objects.create(colegio=self.a, nombre='Única')
        h = self.c.get('/reportes/selector-boletin/').content.decode()
        self.assertNotIn('Todas las sedes', h)

    def test_boletin_dice_la_sede(self):
        for nombre in ('boletin_pdf', 'boletin_prescolar_pdf', 'boletin_final_pdf',
                       'boletin_prescolar_final_pdf'):
            texto = open(f'notas/templates/notas/boletin/{nombre}.html', encoding='utf-8').read()
            self.assertIn('{{ curso.sede.nombre }}', texto, nombre)
