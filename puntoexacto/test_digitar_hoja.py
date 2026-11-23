"""Digitar respuestas sobre la hoja de respuestas digital (como está impresa) en vez de la lista."""
import re

from notas.tests.base import ColegioDePrueba

from . import hojas as H
from .models import Examen, Hoja


class HojaDigital(ColegioDePrueba):
    def test_burbujas_donde_estan_en_la_hoja_y_guarda(self):
        c = self.cliente(self.rectora)
        c.post('/puntoexacto/nuevo/', {'titulo': 'Sesión 2', 'fecha': '2026-10-06', 'componente': 'SABER',
                                       'numero_preguntas': '42', 'numero_opciones': '4', 'hojas_por_pagina': '4',
                                       'metodo': 'con_piso', 'nota_todo_mal': '1', 'nota_nada_marcado': '1', 'opciones_por_pregunta': '{}'})
        ex = Examen.objects.get()
        h = Hoja.objects.create(examen=ex, identificador='PE-00001-0001', nombre_libre='Ana')
        r = c.get(f'/puntoexacto/{ex.id}/hoja/{h.id}/digitar/')
        html = r.content.decode()
        self.assertIn('id="pe-hojad"', html)
        burbujas = re.findall(r'<g class="bur" data-n="(\d+)" data-l="([A-D])"><circle cx="([\d.]+)" cy="([\d.]+)"', html)
        self.assertEqual(len(burbujas), 42 * 4)
        # en el mismo sitio que en la hoja impresa (milímetros, con «y» hacia abajo)
        info = H.mapa_de_examen(ex)
        x, y = info['mapa']['22C']
        b = next(t for t in burbujas if t[0] == '22' and t[1] == 'C')
        self.assertAlmostEqual(float(b[2]), x, places=1)
        self.assertAlmostEqual(float(b[3]), info['hoja_h_mm'] - y, places=1)
        self.assertNotIn(',', re.search(r'viewBox="([^"]+)"', html).group(1))       # sin comas decimales
        # La lista sigue ahí (es lo que se envía) y guardar funciona igual
        self.assertIn('name="p_42"', html)
        datos = {f'p_{n}': '' for n in range(1, 43)}
        datos.update({'p_1': 'B', 'p_22': 'D', 'p_30': '?'})
        c.post(f'/puntoexacto/{ex.id}/hoja/{h.id}/digitar/', datos)
        h.refresh_from_db()
        from . import formas as F
        lectura = F.lectura_de(h, list(ex.preguntas.order_by('numero')))
        self.assertEqual((lectura['1'], lectura['22'], lectura['30']), ('B', 'D', '?'))
