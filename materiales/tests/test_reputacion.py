"""Biblioteca: estrellas, comentarios, puntos del material, reputación y nivel del autor, premios y orden."""
from django.contrib.auth.models import User

from materiales import creditos as K
from materiales import reputacion as R
from materiales.models import ComentarioMaterial, Documento, MaterialCompartido, MovimientoIA
from notas.models import Docente
from notas.tests.base import ColegioDePrueba


class PuntosYComentarios(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for c in (cls.a, cls.b):
            c.modulos_activos = list(c.modulos_activos or []) + ['salon']
            c.save(update_fields=['modulos_activos'])
        cls.u_b = User.objects.create_user('profeb', password='x', first_name='Berta', last_name='Bé')
        Docente.objects.create(colegio=cls.b, user=cls.u_b)
        cls.u_c = User.objects.create_user('profec', password='x', first_name='Ciro', last_name='Ce')
        Docente.objects.create(colegio=cls.a, user=cls.u_c)

    def _publicado(self, titulo='Taller de fracciones'):
        doc = Documento.objects.create(propietario=self.u_docente, colegio=self.a, titulo=titulo, tipo='taller',
                                       contenido={'bloques': []})
        return MaterialCompartido.objects.create(documento=doc, autor=self.u_docente, colegio=self.a, alcance='comunidad',
                                                 estado='publicado', titulo=titulo, tipo='taller', contenido={'bloques': []})

    def test_usar_calificar_y_comentar_dan_puntos_y_premios(self):
        m = self._publicado()
        otra = self.cliente(self.u_b, host='b.localhost')
        otra.post(f'/materiales/biblioteca/{m.pk}/usar/')                          # 3
        otra.post(f'/materiales/biblioteca/{m.pk}/valorar/', {'estrellas': '5'})   # +5
        r = otra.post(f'/materiales/biblioteca/{m.pk}/comentar/', {'texto': 'Me sirvió en 7.º, le quité el punto 4.'})  # +1
        self.assertRedirects(r, f'/materiales/biblioteca/{m.pk}/#comentarios', fetch_redirect_response=False)
        m.refresh_from_db()
        self.assertEqual(m.puntos, 9)
        self.assertEqual(R.reputacion(self.u_docente), 9)
        pagina = otra.get(f'/materiales/biblioteca/{m.pk}/')
        self.assertContains(pagina, 'Me sirvió en 7.º'); self.assertContains(pagina, '9</b> puntos')
        # Cambiar la calificación no suma dos veces
        otra.post(f'/materiales/biblioteca/{m.pk}/valorar/', {'estrellas': '3'})
        m.refresh_from_db()
        self.assertEqual(m.puntos, 7)
        # Lo que hace el propio autor no le da puntos
        self.cliente(self.u_docente).post(f'/materiales/biblioteca/{m.pk}/comentar/', {'texto': 'Gracias, Berta.'})
        m.refresh_from_db()
        self.assertEqual((m.puntos, m.comentarios.count()), (7, 2))
        # Al llegar a 30 puntos: nivel Bronce y 30 créditos de regalo, una sola vez
        MaterialCompartido.objects.filter(pk=m.pk).update(usos=10)
        R.actualizar(m)
        R.actualizar(m)
        self.assertEqual(R.nivel(R.reputacion(self.u_docente))['nombre'], 'Bronce')
        self.assertEqual(MovimientoIA.objects.filter(usuario=self.u_docente, detalle=R.PREFIJO_PREMIO + 'Bronce').count(), 1)
        self.assertEqual(K.estado(self.u_docente, self.a)['extra'], 30)
        autor = self.cliente(self.u_docente).get(f'/materiales/biblioteca/autor/{self.u_docente.pk}/')
        self.assertContains(autor, 'Nivel Bronce'); self.assertContains(autor, 'para <b>Plata</b>')

    def test_borrar_comentario_y_orden(self):
        m1, m2 = self._publicado('Uno'), self._publicado('Dos')
        otra = self.cliente(self.u_b, host='b.localhost')
        otra.post(f'/materiales/biblioteca/{m1.pk}/comentar/', {'texto': 'Bien'})
        c = ComentarioMaterial.objects.get()
        # Otro docente no lo puede borrar; quien lo escribió sí
        self.assertEqual(self.cliente(self.u_c).post(f'/materiales/biblioteca/{m1.pk}/comentario/{c.pk}/borrar/').status_code, 404)
        self.assertTrue(ComentarioMaterial.objects.filter(pk=c.pk).exists())
        otra.post(f'/materiales/biblioteca/{m1.pk}/comentar/', {'texto': 'Bien otra vez'})
        c2 = ComentarioMaterial.objects.get(texto='Bien otra vez')
        otra.post(f'/materiales/biblioteca/{m1.pk}/comentario/{c2.pk}/borrar/')
        self.assertFalse(ComentarioMaterial.objects.filter(pk=c2.pk).exists())
        # Orden: más puntos y mejor calificados (promedio, sin calificación al final)
        otra.post(f'/materiales/biblioteca/{m2.pk}/usar/')
        otra.post(f'/materiales/biblioteca/{m2.pk}/valorar/', {'estrellas': '2'})
        orden = [x.titulo for x in otra.get('/materiales/biblioteca/?orden=puntos').context['materiales']]
        self.assertEqual(orden[:2], ['Dos', 'Uno'])
        otra.post(f'/materiales/biblioteca/{m1.pk}/valorar/', {'estrellas': '5'})
        orden = [x.titulo for x in otra.get('/materiales/biblioteca/?orden=estrellas').context['materiales']]
        self.assertEqual(orden[:2], ['Uno', 'Dos'])
