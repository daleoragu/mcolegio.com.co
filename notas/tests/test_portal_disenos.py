# notas/tests/test_portal_disenos.py
"""Los diseños del portal: todos se dibujan, con los colores del colegio, y se pueden probar."""
from notas.models import Colegio, Noticia, Sede

from .base import ColegioDePrueba


class DisenosPortal(ColegioDePrueba):

    def setUp(self):
        Noticia.objects.create(colegio=self.a, titulo='Feria de la ciencia', resumen='Ganamos el primer lugar',
                               cuerpo='...', estado='PUBLICADO')
        Sede.objects.create(colegio=self.a, nombre='Sede Norte', direccion='Calle 1')
        self.a.lema = 'Amor a la verdad'
        self.a.save()

    def test_todos_los_disenos_se_dibujan(self):
        for valor, _ in Colegio.LAYOUT_CHOICES:
            Colegio.objects.filter(pk=self.a.pk).update(layout_portal=valor)
            r = self.cliente().get('/')
            self.assertEqual(r.status_code, 200, valor)
            h = r.content.decode()
            self.assertIn('id="dynamicMainContent"', h, valor)        # el menú sigue funcionando
            self.assertIn('data-action="noticias"', h, valor)
            self.assertIn('#7B1E3A', h, valor)                         # los colores del colegio
            if valor in Colegio.DISENOS_CON_INICIO:
                self.assertIn('data-servidor="1"', h, valor)
                self.assertIn(f'diseno-{valor}', h, valor)
                self.assertIn('Feria de la ciencia', h, valor)         # inicio con noticias reales

    def test_vista_previa_solo_para_administradores(self):
        visitante = self.cliente().get('/?diseno=revista').content.decode()
        self.assertNotIn('diseno-revista', visitante)
        admin = self.cliente(self.rectora).get('/?diseno=revista').content.decode()
        self.assertIn('diseno-revista', admin)
        self.assertIn('Usar este diseño', admin)
        r = self.cliente(self.rectora).post('/admin/portal/diseno/', {'diseno': 'revista'})
        self.assertEqual(r.status_code, 302)
        self.a.refresh_from_db()
        self.assertEqual(self.a.layout_portal, 'revista')
        # Un docente no lo cambia.
        self.cliente(self.u_docente).post('/admin/portal/diseno/', {'diseno': 'mosaico'})
        self.a.refresh_from_db()
        self.assertEqual(self.a.layout_portal, 'revista')

    def test_selector_en_personalizacion(self):
        h = self.cliente(self.rectora).get('/admin/portal/personalizacion/').content.decode()
        for valor, _ in Colegio.LAYOUT_CHOICES:
            self.assertIn(f'value="{valor}"', h)
        self.assertIn('Ver en mi portal', h)
