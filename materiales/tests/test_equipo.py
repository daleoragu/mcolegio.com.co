"""Mis materiales: modelos pedagógicos (ABP, retos, caso, invertida, cooperativo) y trabajo en equipo."""
import json
import shutil
import tempfile

from django.contrib.auth.models import User
from django.test import Client, override_settings

from materiales.models import Colaborador, Documento, Imagen
from notas.models import AsignacionDocente, Docente, Materia, Notificacion
from notas.tests.base import CLAVE, ColegioDePrueba

from .test_materiales import png

MEDIA = tempfile.mkdtemp(prefix='materiales-equipo-')


@override_settings(MEDIA_ROOT=MEDIA)
class Equipo(ColegioDePrueba):

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.a.modulos_activos = list(cls.a.modulos_activos) + ['salon']
        cls.a.save(update_fields=['modulos_activos'])
        cls.u_ana = User.objects.create_user('ana_ciencias', password=CLAVE, first_name='Ana', last_name='Ciencias')
        cls.ana = Docente.objects.create(colegio=cls.a, user=cls.u_ana)
        ciencias = Materia.objects.create(colegio=cls.a, nombre='Ciencias naturales', usar_ponderacion_equitativa=False)
        AsignacionDocente.objects.create(colegio=cls.a, docente=cls.ana, materia=ciencias, curso=cls.asig.curso)
        cls.u_lejos = User.objects.create_user('de_otro', password=CLAVE, first_name='Otro', last_name='Colegio')
        Docente.objects.create(colegio=cls.b, user=cls.u_lejos)

    def setUp(self):
        self.profe = self.cliente(self.u_docente)
        self.ana_c = self.cliente(self.u_ana)

    def test_modelos_pedagogicos(self):
        self.assertContains(self.profe.get('/materiales/'), 'Modelos pedagógicos')
        for tipo, rastro in [('abp', 'Pregunta impulsora'), ('retos', 'Pregunta esencial'), ('caso', 'Alternativas de solución'),
                             ('invertida', 'Antes de clase'), ('cooperativo', 'rompecabezas')]:
            self.profe.post('/materiales/nuevo/', {'tipo': tipo, 'titulo': f'Guía {tipo}'})
            doc = Documento.objects.latest('pk')
            self.assertEqual(doc.tipo, tipo)
            texto = json.dumps(doc.contenido, ensure_ascii=False)
            self.assertIn(rastro, texto)
            self.assertTrue(any(b['tipo'] == 'tabla' for b in doc.contenido['bloques']))
            self.assertTrue(self.profe.get(f'/materiales/{doc.pk}/pdf/').content.startswith(b'%PDF'))
        abp = Documento.objects.get(tipo='abp')
        self.assertIn('Superior', json.dumps(abp.contenido, ensure_ascii=False))     # rúbrica con la escala nacional

    def test_invitar_buscar_aceptar_y_editar_juntos(self):
        self.profe.post('/materiales/nuevo/', {'tipo': 'abp', 'titulo': 'Proyecto del agua'})
        doc = Documento.objects.latest('pk')
        url = f'/materiales/{doc.pk}/equipo/'
        # Búsqueda por área: aparece Ana (Ciencias naturales); nunca un docente de otro colegio ni estudiantes
        j = self.profe.get(url, {'area': 'Ciencias'}).json()
        self.assertEqual([e['nombre'] for e in j['encontrados']], ['Ana Ciencias'])
        self.assertIn('Ciencias naturales', j['areas'])
        todos = {e['nombre'] for e in self.profe.get(url, {'todos': 1}).json()['encontrados']}
        self.assertNotIn('Otro Colegio', todos); self.assertFalse(any('Estudiante' in n for n in todos))
        r = self.profe.post(url, {'accion': 'invitar', 'usuario': self.u_lejos.pk})
        self.assertEqual(r.status_code, 400)
        # Invitar → aviso → aceptar
        self.profe.post(url, {'accion': 'invitar', 'usuario': self.u_ana.pk, 'permiso': 'editar'})
        self.assertTrue(Notificacion.objects.filter(destinatario=self.u_ana, mensaje__contains='Proyecto del agua').exists())
        self.assertEqual(self.ana_c.get(f'/materiales/{doc.pk}/').status_code, 404)        # aún no acepta
        self.assertContains(self.ana_c.get('/materiales/'), 'Lo invitaron a construir')
        c = Colaborador.objects.get()
        self.ana_c.post(f'/materiales/invitacion/{c.pk}/', {'accion': 'aceptar'})
        self.assertContains(self.ana_c.get('/materiales/'), 'Construyo con otros docentes')
        self.assertContains(self.ana_c.get(f'/materiales/{doc.pk}/'), 'De Pedro Profe')
        # Ana edita y guarda
        r = self.ana_c.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'titulo': 'Proyecto del agua', 'version': 0,
            'contenido': {'bloques': [{'tipo': 'texto', 'html': '<p>Aporte de Ana</p>'}]}}), content_type='application/json')
        self.assertTrue(r.json()['ok']); self.assertEqual(r.json()['version'], 1)
        # El dueño, con su copia vieja (versión 0), no le borra el aporte: recibe aviso de conflicto
        r = self.profe.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'titulo': 'Proyecto del agua', 'version': 0,
            'contenido': {'bloques': [{'tipo': 'texto', 'html': '<p>Viejo</p>'}]}}), content_type='application/json')
        self.assertEqual(r.status_code, 409); self.assertIn('Ana Ciencias', r.json()['error'])
        doc.refresh_from_db(); self.assertIn('Aporte de Ana', json.dumps(doc.contenido))
        # El editor sabe quién está y en qué versión va
        e = self.profe.get(f'/materiales/{doc.pk}/estado/').json()
        self.assertEqual(e['version'], 1); self.assertTrue(e['editado_por_otro'])
        # Solo el dueño borra
        self.ana_c.post(f'/materiales/{doc.pk}/accion/', {'accion': 'eliminar'})
        self.assertTrue(Documento.objects.filter(pk=doc.pk).exists())
        # Solo ver: no guarda
        self.profe.post(url, {'accion': 'permiso', 'colaborador': c.pk, 'permiso': 'ver'})
        r = self.ana_c.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'version': 1, 'contenido': {'bloques': []}}),
                            content_type='application/json')
        self.assertEqual(r.status_code, 403)
        self.assertContains(self.ana_c.get(f'/materiales/{doc.pk}/'), 'solo ver')
        self.assertTrue(self.ana_c.get(f'/materiales/{doc.pk}/pdf/').content.startswith(b'%PDF'))
        # Salir del equipo
        self.ana_c.post(f'/materiales/invitacion/{c.pk}/', {'accion': 'salir'})
        self.assertFalse(Colaborador.objects.exists())

    def test_imagenes_del_equipo_y_copia_propia(self):
        self.profe.post('/materiales/nuevo/', {'tipo': 'libre', 'titulo': 'Con foto'})
        doc = Documento.objects.latest('pk')
        img = self.profe.post('/materiales/imagen/', {'imagen': png()}).json()['id']
        self.profe.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'titulo': 'Con foto', 'version': 0,
            'contenido': {'bloques': [{'tipo': 'imagen', 'imagen': img, 'ancho': 60}]}}), content_type='application/json')
        Colaborador.objects.create(documento=doc, usuario=self.u_ana, estado='aceptada')
        # Ana ve la imagen del dueño y, al guardar, no se pierde
        self.assertEqual(self.ana_c.get(f'/materiales/imagen/{img}/').status_code, 302)
        doc.refresh_from_db()
        r = self.ana_c.post(f'/materiales/{doc.pk}/guardar/', json.dumps({'titulo': 'Con foto', 'version': doc.version,
            'contenido': doc.contenido}), content_type='application/json')
        doc.refresh_from_db(); self.assertEqual(doc.contenido['bloques'][0]['imagen'], img)
        # Un docente ajeno no la ve
        self.assertIn(self.cliente(self.u_lejos, host='b.localhost').get(f'/materiales/imagen/{img}/').status_code, (403, 404))
        # La copia de Ana tiene su propia imagen
        self.ana_c.post(f'/materiales/{doc.pk}/accion/', {'accion': 'duplicar'})
        copia = Documento.objects.filter(propietario=self.u_ana).get()
        nueva = copia.contenido['bloques'][0]['imagen']
        self.assertNotEqual(nueva, img); self.assertEqual(Imagen.objects.get(pk=nueva).propietario, self.u_ana)

    def test_plan_individual_con_colegas(self):
        from chat.models import Colega
        from salon_digital.models import Cuenta
        u1 = User.objects.create_user('lina', password=CLAVE, first_name='Lina', last_name='Libre')
        u2 = User.objects.create_user('mario', password=CLAVE, first_name='Mario', last_name='Mate')
        u3 = User.objects.create_user('nora', password=CLAVE, first_name='Nora', last_name='Nada')
        for u in (u1, u2, u3):
            Cuenta.objects.create(usuario=u, slug=u.username, nombre_publico=u.get_full_name(), estado='verificada')
        Colega.objects.create(de=u1, para=u2, estado='aceptada')
        c = Client(HTTP_HOST='localhost'); c.force_login(u1)
        c.post('/materiales/nuevo/', {'tipo': 'caso', 'titulo': 'Caso del río'})
        doc = Documento.objects.get(propietario=u1)
        j = c.get(f'/materiales/{doc.pk}/equipo/', {'todos': 1}).json()
        self.assertEqual([e['nombre'] for e in j['encontrados']], ['Mario Mate'])       # solo sus colegas
        self.assertEqual(c.post(f'/materiales/{doc.pk}/equipo/', {'accion': 'invitar', 'usuario': u3.pk}).status_code, 400)
        self.assertTrue(c.post(f'/materiales/{doc.pk}/equipo/', {'accion': 'invitar', 'usuario': u2.pk}).json()['ok'])

    def test_enviar_a_grupos_y_traer_desde_el_aula(self):
        from aula.models import Aula, Material, Tarea
        from notas.models import Curso
        self.profe.get(f'/aula/asignacion/{self.asig.id}/')
        aula1 = Aula.objects.get(asignacion=self.asig)
        curso2 = Curso.objects.create(colegio=self.a, nombre='Otro curso', grado=self.asig.curso.grado)
        asig2 = AsignacionDocente.objects.create(colegio=self.a, docente=self.asig.docente, materia=self.asig.materia, curso=curso2)
        self.profe.get(f'/aula/asignacion/{asig2.id}/')
        aula2 = Aula.objects.get(asignacion=asig2)
        self.profe.post('/materiales/nuevo/', {'tipo': 'taller', 'titulo': 'Taller de fracciones'})
        doc = Documento.objects.latest('pk')
        lista = self.profe.get('/materiales/')
        self.assertContains(lista, 'Enviar a mis grupos'); self.assertContains(lista, 'no</b> lo ven')
        # A los dos grupos de una vez, como PDF y como tarea
        r = self.profe.post(f'/materiales/{doc.pk}/accion/', {'accion': 'enviar', 'aula': [aula1.pk, aula2.pk],
                                                               'como': ['pdf', 'tarea'], 'unidad': 'Unidad 2', 'volver': '/materiales/'})
        self.assertRedirects(r, '/materiales/', fetch_redirect_response=False)
        self.assertEqual(Material.objects.filter(titulo='Taller de fracciones').count(), 2)
        self.assertEqual(Material.objects.get(aula=aula2).unidad, 'Unidad 2')
        # El taller tiene preguntas → una tarea en borrador por grupo; si no tuviera, solo un aviso
        self.assertEqual(Tarea.objects.filter(titulo='Taller de fracciones', publicada=False).count(),
                         2 if Tarea.objects.filter(titulo='Taller de fracciones').exists() else 0)
        # Enviar otra vez actualiza, no duplica
        self.profe.post(f'/materiales/{doc.pk}/accion/', {'accion': 'enviar', 'aula': [aula1.pk], 'como': ['pdf']})
        self.assertEqual(Material.objects.filter(aula=aula1, titulo='Taller de fracciones').count(), 1)
        # Un aula ajena no se acepta; sin «cómo» tampoco
        self.profe.post(f'/materiales/{doc.pk}/accion/', {'accion': 'enviar', 'aula': [999999], 'como': ['pdf']})
        self.profe.post(f'/materiales/{doc.pk}/accion/', {'accion': 'enviar', 'aula': [aula1.pk]})
        self.assertEqual(Material.objects.filter(titulo='Taller de fracciones').count(), 2)
        # Desde el aula: pestaña «Traer de Mis materiales» con sus guías; vuelve al Material del aula
        p = self.profe.get(f'/aula/{aula1.pk}/material/')
        self.assertContains(p, 'Traer de Mis materiales'); self.assertContains(p, 'Taller de fracciones')
        self.assertContains(p, 'ven sus estudiantes')
        Material.objects.all().delete()
        r = self.profe.post(f'/materiales/{doc.pk}/accion/', {'accion': 'enviar', 'aula': aula1.pk, 'como': 'pdf',
                                                               'volver': f'/aula/{aula1.pk}/material/'})
        self.assertRedirects(r, f'/aula/{aula1.pk}/material/', fetch_redirect_response=False)
        self.assertTrue(Material.objects.filter(aula=aula1).exists())
        # «volver» externo se ignora
        r = self.profe.post(f'/materiales/{doc.pk}/accion/', {'accion': 'enviar', 'aula': aula1.pk, 'como': 'pdf',
                                                               'volver': '//malo.com/'})
        self.assertEqual(r['Location'], '/materiales/')
        # El estudiante ve el material, pero no la pestaña del docente
        est = self.cliente(self.estudiantes[0].user).get(f'/aula/{aula1.pk}/material/')
        self.assertContains(est, 'Taller de fracciones'); self.assertNotContains(est, 'Traer de Mis materiales')
