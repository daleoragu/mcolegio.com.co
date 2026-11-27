"""Boletín en PDF: cada área no se parte entre dos hojas, la firma no queda sola y el área de una sola
asignatura sale como las demás (franja del área + fila del docente, sin repetir el nombre)."""
import copy

from django.template.loader import render_to_string

from notas import componentes as comp

from .base import ColegioDePrueba


class BoletinPaginas(ColegioDePrueba):

    def datos(self):
        from notas.boletin.logic import get_datos_boletin_curso
        from notas.models import AreaConocimiento, PonderacionAreaMateria
        area, _ = AreaConocimiento.objects.get_or_create(colegio=self.a, nombre='MATEMÁTICAS')
        PonderacionAreaMateria.objects.get_or_create(colegio=self.a, area=area, materia=self.materia,
                                                     defaults={'peso_porcentual': 100})
        return get_datos_boletin_curso(self.a, self.curso, self.p1)

    def html(self, boletines):
        from notas.boletin.ponderacion import ajustes
        return render_to_string('notas/boletin/boletin_pdf.html', {
            'boletines': boletines, 'curso': self.curso, 'periodo': self.p1, 'colegio': self.a,
            'ajustes': ajustes(self.a), 'componentes': comp.componentes(self.a)})

    def test_area_de_una_asignatura_en_dos_filas(self):
        datos = self.datos()
        html = self.html(datos[:1])
        self.assertIn('class="bloque-area"', html)
        self.assertIn('class="cierre-boletin"', html)
        self.assertIn('MATEMÁTICAS', html)
        self.assertIn('Docente:', html)

    def test_areas_y_firma_no_se_parten(self):
        from weasyprint import HTML
        datos = self.datos()[:1]
        b = datos[0]
        area = b['areas'][0]
        # Muchas áreas con varios logros: el boletín ocupa más de una hoja.
        b['areas'] = [copy.deepcopy(area) for _ in range(14)]
        for i, a in enumerate(b['areas']):
            a['nombre'] = f'AREA {i:02d}'
        doc = HTML(string=self.html(datos)).render()
        import os
        if os.environ.get('BOLETIN_MUESTRA'):
            doc.write_pdf(os.environ['BOLETIN_MUESTRA'])
        self.assertGreater(len(doc.pages), 1)
        texto = [' '.join(caja.text for caja in self._cajas(p._page_box) if getattr(caja, 'text', None))
                 for p in doc.pages]
        for i in range(14):
            hojas = [n for n, t in enumerate(texto) if f'AREA {i:02d}' in t]
            self.assertEqual(len(hojas), 1, f'AREA {i:02d} en las hojas {hojas}')
        # La firma nunca queda sola: la acompaña al menos la última área.
        firma = [n for n, t in enumerate(texto) if 'Director(a) de Grupo' in t]
        self.assertEqual(len(firma), 1)
        self.assertIn('AREA 13', texto[firma[0]])

    def _cajas(self, caja):
        yield caja
        for hija in getattr(caja, 'children', []):
            yield from self._cajas(hija)
