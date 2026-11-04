"""La campana y los mensajes contrastan con la barra: automático (color contrario) o escogido por el colegio."""
from notas.colores import a_rgb, contraste, contrario, iconos_topbar

from .base import ColegioDePrueba


class ColorContrario(ColegioDePrueba):

    def test_siempre_contrasta(self):
        for fondo in ['#000000', '#343A40', '#7B1E3A', '#1F3A68', '#0D6EFD', '#198754', '#FFFFFF', '#FFD43B',
                      '#F2B632', '#6C757D', '#E83E8C', '#20C997']:
            color = contrario(fondo)
            self.assertGreaterEqual(contraste(a_rgb(color), a_rgb(fondo)), 4.5, f'{color} sobre {fondo}')

    def test_negro_o_gris_da_amarillo_y_blanco_da_oscuro(self):
        self.assertEqual(contrario('#000000'), '#FFD43B')
        self.assertEqual(contrario('#343A40'), '#FFD43B')
        self.assertEqual(contrario('#FFFFFF'), '#1F2937')

    def test_con_color_da_el_tono_opuesto(self):
        import colorsys
        h_fondo = colorsys.rgb_to_hls(*a_rgb('#7B1E3A'))[0]
        h_icono = colorsys.rgb_to_hls(*a_rgb(contrario('#7B1E3A')))[0]
        self.assertAlmostEqual(abs(h_fondo - h_icono), 0.5, delta=0.05)

    def test_color_invalido(self):
        self.assertEqual(contrario('rojo'), '#FFD43B')

    def test_manual_y_automatico(self):
        self.a.color_topbar = '#000000'
        self.assertEqual(iconos_topbar(self.a), '#FFD43B')
        self.a.iconos_topbar_auto, self.a.color_iconos_topbar = False, '#00ff00'
        self.assertEqual(iconos_topbar(self.a), '#00FF00')

    def test_la_barra_usa_el_color(self):
        self.a.color_topbar, self.a.iconos_topbar_auto = '#000000', True
        self.a.save()
        r = self.cliente(self.u_docente).get('/dashboard/', follow=True)
        self.assertContains(r, '--topbar-iconos: #FFD43B')
        self.assertContains(r, 'background-color: #DC3545')
        self.a.iconos_topbar_auto, self.a.color_iconos_topbar = False, '#FF00AA'
        self.a.save()
        self.assertContains(self.cliente(self.u_docente).get('/dashboard/', follow=True), '--topbar-iconos: #FF00AA')

    def test_el_portal_trae_la_opcion(self):
        r = self.cliente(self.rectora).get('/admin/portal/personalizacion/')
        self.assertContains(r, 'Color automático para la campana y los mensajes')
        self.assertContains(r, 'Así se ve la barra')
