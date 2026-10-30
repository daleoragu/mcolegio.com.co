"""Tareas, material y actividades para algunos estudiantes, y el globo rojo de novedades."""
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from aula import logica
from aula.models import Actividad, Aula, Material, Publicacion, Tarea, Visto
from notas.models import Notificacion
from notas.tests.base import ColegioDePrueba

MEDIA = tempfile.mkdtemp(prefix='aula-para-')


@override_settings(MEDIA_ROOT=MEDIA)
class ParaAlgunos(ColegioDePrueba):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])

    def setUp(self):
        self.ana, self.beto, self.caro = self.estudiantes
        self.profe = self.cliente(self.u_docente)
        self.profe.get(f'/aula/asignacion/{self.asig.id}/')
        self.aula = Aula.objects.get(asignacion=self.asig)
        self.base = f'/aula/{self.aula.pk}'

    def test_tarea_solo_para_un_estudiante(self):
        # «Solo algunos» sin escoger a nadie: no se guarda
        self.profe.post(f'{self.base}/tareas/nueva/', {'titulo': 'Taller', 'publicada': 'on', 'para_modo': 'algunos'})
        self.assertFalse(Tarea.objects.exists())
        # El formulario sugiere al estudiante que llega por el enlace ?para=
        r = self.profe.get(f'{self.base}/tareas/nueva/?para=e{self.ana.id}')
        self.assertContains(r, f'value="e{self.ana.id}" checked')

        r = self.profe.post(f'{self.base}/tareas/nueva/', {
            'titulo': 'Taller PIAR', 'publicada': 'on', 'para_modo': 'algunos',
            'para': [f'e{self.ana.id}', 'e999999']})
        t = Tarea.objects.get()
        self.assertEqual(t.para, [f'e{self.ana.id}'])
        avisos = Notificacion.objects.filter(mensaje__contains='Taller PIAR')
        self.assertEqual(list(avisos.values_list('destinatario_id', flat=True)), [self.ana.user_id])

        ana, beto = self.cliente(self.ana.user), self.cliente(self.beto.user)
        self.assertContains(ana.get(f'{self.base}/tareas/'), 'Taller PIAR')
        self.assertContains(ana.get(f'{self.base}/tareas/{t.pk}/'), 'solo para usted')
        self.assertNotContains(beto.get(f'{self.base}/tareas/'), 'Taller PIAR')
        self.assertNotContains(beto.get(f'{self.base}/'), 'Taller PIAR')
        self.assertContains(ana.get(f'{self.base}/'), 'Taller PIAR')
        self.assertEqual(beto.get(f'{self.base}/tareas/{t.pk}/').status_code, 404)
        self.assertEqual(beto.post(f'{self.base}/tareas/{t.pk}/entregar/', {'texto': 'x'}).status_code, 404)
        self.assertTrue(Publicacion.objects.filter(tarea=t).exists())

        # El docente ve solo a Ana en la lista de entregas
        r = self.profe.get(f'{self.base}/tareas/{t.pk}/')
        self.assertContains(r, 'Solo para:')
        self.assertEqual(len(r.context['filas']), 1)
        self.assertContains(self.profe.get(f'{self.base}/tareas/'), 'Solo 1 estudiante')

        # Editarla para toda la clase
        self.profe.post(f'{self.base}/tareas/{t.pk}/editar/', {'titulo': 'Taller PIAR', 'publicada': 'on',
                                                              'para_modo': 'todos'})
        t.refresh_from_db()
        self.assertEqual(t.para, [])
        self.assertEqual(beto.get(f'{self.base}/tareas/{t.pk}/').status_code, 200)

    def test_material_y_actividad_para_algunos(self):
        self.profe.post(f'{self.base}/material/', {
            'titulo': 'Guía para ponerse al día', 'enlace': 'https://example.com/guia',
            'para_modo': 'algunos', 'para': [f'e{self.beto.id}', f'e{self.caro.id}'],
            'archivo': SimpleUploadedFile('guia.pdf', b'%PDF-1.4')})
        m = Material.objects.get()
        self.assertEqual(sorted(m.para), sorted([f'e{self.beto.id}', f'e{self.caro.id}']))
        ana, beto = self.cliente(self.ana.user), self.cliente(self.beto.user)
        self.assertNotContains(ana.get(f'{self.base}/material/'), 'ponerse al día')
        self.assertContains(beto.get(f'{self.base}/material/'), 'ponerse al día')
        self.assertEqual(ana.get(f'{self.base}/archivo/mat/{m.pk}/').status_code, 404)
        self.assertEqual(beto.get(f'{self.base}/archivo/mat/{m.pk}/').status_code, 302)
        self.assertContains(self.profe.get(f'{self.base}/material/'), 'Solo 2 estudiantes')
        self.assertEqual(Notificacion.objects.filter(mensaje__contains='ponerse al día').count(), 2)

        self.profe.post(f'{self.base}/actividades/', {
            'titulo': 'GeoGebra', 'enlace': 'https://www.geogebra.org/m/abc',
            'para_modo': 'algunos', 'para': [f'e{self.ana.id}']})
        a = Actividad.objects.get()
        self.assertContains(ana.get(f'{self.base}/actividades/'), 'GeoGebra')
        self.assertNotContains(beto.get(f'{self.base}/actividades/'), 'GeoGebra')
        self.assertEqual(beto.get(f'{self.base}/actividades/{a.pk}/').status_code, 404)

    def test_globo_rojo_de_novedades(self):
        ana = self.cliente(self.ana.user)
        self.profe.post(f'{self.base}/', {'texto': 'Bienvenidos'})
        self.profe.post(f'{self.base}/material/', {'titulo': 'Video', 'enlace': 'https://example.com/v'})
        self.profe.post(f'{self.base}/tareas/nueva/', {'titulo': 'Taller 1', 'publicada': 'on'})
        self.profe.post(f'{self.base}/tareas/nueva/', {'titulo': 'Solo Beto', 'publicada': 'on',
                                                      'para_modo': 'algunos', 'para': [f'e{self.beto.id}']})
        self.assertEqual(logica.novedades(self.aula, self.ana),
                         {'muro': 1, 'material': 1, 'tareas': 1, 'actividades': 0, 'cuestionarios': 0})
        r = ana.get('/aula/')
        self.assertContains(r, 'au-globo esquina')
        self.assertEqual(r.context['asignaciones'][0].nuevos, 3)

        # Abre el material: ya no cuenta, pero en las pestañas sigue el globo de las tareas
        r = ana.get(f'{self.base}/material/')
        self.assertEqual(r.context['nuevos']['material'], 0)
        self.assertEqual(r.context['nuevos']['tareas'], 1)
        ana.get(f'{self.base}/')
        ana.get(f'{self.base}/tareas/')
        self.assertEqual(sum(logica.novedades(self.aula, self.ana).values()), 0)
        self.assertEqual(Visto.objects.filter(estudiante=self.ana).count(), 1)
        self.assertNotContains(ana.get('/aula/'), 'au-globo esquina')

        # Algo nuevo vuelve a prender el globo
        self.profe.post(f'{self.base}/tareas/nueva/', {'titulo': 'Taller 2', 'publicada': 'on'})
        self.assertEqual(logica.novedades(self.aula, self.ana)['tareas'], 1)
        # El docente no tiene globos
        self.assertNotIn('nuevos', self.profe.get(f'{self.base}/tareas/').context)
