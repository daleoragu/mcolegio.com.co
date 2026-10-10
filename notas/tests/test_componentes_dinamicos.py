"""Componentes de evaluación: cada colegio decide cuántos tiene (1, 3, 5…) y cómo se llaman."""
from decimal import Decimal

from django.template.loader import render_to_string

from notas import componentes as comp
from notas.models import Calificacion
from notas.models.academicos import ConfiguracionCalificaciones
from notas.planillas.columnas import componentes_activos
from notas.planillas.guardar import guardar_estudiante

from .base import ColegioDePrueba

URL = '/admin/componentes-evaluacion/'


class ComponentesDinamicos(ColegioDePrueba):

    def enviar(self, filas, usuario=None):
        datos = {'codigo': [f[0] for f in filas], 'nombre': [f[1] for f in filas],
                 'abreviatura': [f[2] if len(f) > 2 else '' for f in filas]}
        return self.cliente(usuario or self.rectora).post(URL, datos)

    def fresca(self):
        from notas.models import AsignacionDocente
        return AsignacionDocente.objects.get(pk=self.asig.pk)

    def pesos(self):
        return comp.pesos(self.fresca())

    def columnas_boletin(self, html):
        # Un boletín por estudiante: se cuentan las columnas de uno.
        return html.count('class="th-comp"') // len(self.estudiantes)

    def ingreso(self):
        return self.cliente(self.u_docente).get(
            f'/docente/ingresar-notas/?asignacion_id={self.asig.id}&periodo_id={self.p1.id}')

    def boletin(self):
        from notas.boletin.logic import get_datos_boletin_curso
        from notas.models import AreaConocimiento, PonderacionAreaMateria
        area, _ = AreaConocimiento.objects.get_or_create(colegio=self.a, nombre='MATEMÁTICAS')
        PonderacionAreaMateria.objects.get_or_create(colegio=self.a, area=area, materia=self.materia,
                                                     defaults={'peso_porcentual': 100})
        from notas.boletin.ponderacion import ajustes
        datos = get_datos_boletin_curso(self.a, self.curso, self.p1)
        return render_to_string('notas/boletin/boletin_pdf.html', {
            'boletines': datos, 'curso': self.curso, 'periodo': self.p1, 'colegio': self.a,
            'ajustes': ajustes(self.a), 'componentes': comp.componentes(self.a)})

    # --- Lo de siempre sigue igual ------------------------------------------

    def test_arranca_con_los_tres_de_siempre(self):
        r = self.cliente(self.rectora).get(URL)
        self.assertContains(r, 'Agregar componente')
        self.assertEqual(comp.codigos(self.a), ['SER', 'SABER', 'HACER'])
        self.assertEqual(self.pesos(), {'SER': 0, 'SABER': 60, 'HACER': 40})

    def test_renombrar_sale_en_todas_partes(self):
        r = self.enviar([('SER', 'Actitudinal', 'ACT.'), ('SABER', 'Cognitivo'), ('HACER', 'Procedimental', 'PROC.')])
        self.assertEqual(r.status_code, 302)
        conf = ConfiguracionCalificaciones.objects.get(colegio=self.a)
        self.assertEqual((conf.etiqueta_saber, conf.abreviatura_hacer), ('Cognitivo', 'PROC.'))
        self.assertEqual([n for _, n, _ in componentes_activos(self.fresca())], ['Cognitivo', 'Procedimental'])
        self.assertContains(self.ingreso(), '"lbl_saber": "Cognitivo"')
        html = self.boletin()
        for texto in ('ACT.', 'COGNITIVO', 'PROC.'):
            self.assertIn(texto, html)
        self.assertEqual(self.columnas_boletin(html), 3)

    # --- Agregar, quitar, reordenar -----------------------------------------

    def test_quitar_dos_y_agregar_uno(self):
        r = self.enviar([('', 'Proyecto'), ('SABER', 'Cognitivo', 'COG.')])
        self.assertEqual(r.status_code, 302)
        self.assertEqual(comp.codigos(self.a), ['C4', 'SABER'])          # en el orden de la pantalla
        # Lo que pesaba HACER (40) pasa a SABER; el nuevo arranca en 0.
        self.assertEqual(self.pesos(), {'C4': 0, 'SABER': 100})
        self.assertEqual([c for c, _, _ in componentes_activos(self.fresca())], ['SABER'])
        # Se le pone porcentaje al nuevo y ya cuenta en la definitiva.
        self.materia.refresh_from_db()
        comp.fijar_pesos(self.materia, {'C4': 30, 'SABER': 70})
        self.materia.full_clean()
        self.materia.save()
        ana = self.estudiantes[0]
        final = guardar_estudiante(self.a, self.fresca(), self.p1, ana, {'SABER': [('N1', '4')], 'C4': [('N1', '3')]})
        self.assertEqual(final, Decimal('3.70'))
        self.assertEqual(Calificacion.objects.get(estudiante=ana, tipo_nota='C4').valor_nota, Decimal('3.00'))
        # Ingreso en línea: dos componentes, con su nombre y peso.
        r = self.ingreso()
        self.assertContains(r, '"componentes"')
        self.assertContains(r, 'id="p-c4"', count=0)       # sin permiso de porcentajes no sale el panel
        self.assertContains(r, '"tipo": "c4"')
        # Boletín: dos columnas, en orden, y las filas de logros abarcan la tabla entera.
        html = self.boletin()
        self.assertEqual(self.columnas_boletin(html), 2)
        self.assertLess(html.index('PROYECTO'), html.index('COG.'))
        self.assertIn('colspan="8"', html)        # logros: 6 columnas fijas + 2 componentes
        self.assertIn('<td class="nota">3,0</td>', html.replace('3,00', '3,0'))

    def test_un_solo_componente(self):
        self.enviar([('SABER', 'Nota')])
        self.assertEqual(self.pesos(), {'SABER': 100})
        ana = self.estudiantes[0]
        self.assertEqual(guardar_estudiante(self.a, self.fresca(), self.p1, ana, {'SABER': [('N1', '4.5')]}),
                         Decimal('4.50'))
        self.assertEqual(self.columnas_boletin(self.boletin()), 1)

    def test_cinco_componentes_y_equitativa(self):
        self.enviar([('SER', 'Ser'), ('SABER', 'Saber'), ('HACER', 'Hacer'), ('', 'Convivir'), ('', 'Emprender')])
        self.assertEqual(comp.codigos(self.a), ['SER', 'SABER', 'HACER', 'C4', 'C5'])
        self.materia.refresh_from_db()
        self.materia.usar_ponderacion_equitativa = True
        self.materia.save()
        pesos = self.pesos()
        self.assertEqual(list(pesos.values()), [Decimal('20.00')] * 5)
        self.assertEqual(sum(pesos.values()), 100)

    def test_no_se_quita_un_componente_con_notas(self):
        guardar_estudiante(self.a, self.asig, self.p1, self.estudiantes[0], {'HACER': [('N1', '4')]})
        r = self.enviar([('SER', 'SER'), ('SABER', 'SABER')])
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'no se puede quitar')
        self.assertContains(r, 'Matemáticas')
        self.assertIn('HACER', comp.codigos(self.a))
        # Renombrarlo sí se puede.
        self.assertEqual(self.enviar([('SER', 'SER'), ('SABER', 'SABER'), ('HACER', 'Práctico')]).status_code, 302)
        self.assertEqual(comp.nombre(self.a, 'HACER'), 'Práctico')

    def test_un_codigo_con_notas_viejas_no_se_reusa(self):
        comp.componentes(self.a)
        Calificacion.objects.create(colegio=self.a, estudiante=self.estudiantes[0], materia=self.materia,
                                    periodo=self.p1, tipo_nota='C4', valor_nota=Decimal('4'))
        self.enviar([('SER', 'SER'), ('SABER', 'SABER'), ('HACER', 'HACER'), ('', 'Nuevo')])
        self.assertEqual(comp.codigos(self.a)[-1], 'C5')

    def test_validaciones(self):
        self.assertContains(self.enviar([('SER', 'Saber'), ('SABER', 'saber')]), 'nombre distinto')
        self.assertContains(self.cliente(self.rectora).post(URL, {}), 'al menos un componente')
        self.assertContains(self.enviar([('SER', 'Ser'), ('XYZ', 'Raro')]), 'Recargue la página')
        # Un código de otro colegio no se puede tocar.
        comp.componentes(self.b)
        self.assertContains(self.enviar([('SER', 'Ser'), ('', '')]), 'Escriba el nombre')
        self.assertEqual(comp.codigos(self.a), ['SER', 'SABER', 'HACER'])

    def test_solo_administradores(self):
        self.assertEqual(self.cliente(self.u_docente).get(URL).status_code, 403)
        self.assertEqual(self.enviar([('SER', 'X')], usuario=self.u_docente).status_code, 403)
        self.assertEqual(comp.nombre(self.a, 'SER'), 'SER')

    def test_unificar_materias(self):
        self.materia.etiqueta_saber = 'Examen'
        self.materia.save()
        c = self.cliente(self.rectora)
        self.assertContains(c.get(URL), 'Examen')
        c.post(URL, {'accion': 'unificar'})
        self.materia.refresh_from_db()
        self.assertEqual(self.materia.etiqueta_saber, 'SABER')

    # --- Porcentajes y PuntoExacto ------------------------------------------

    def test_porcentajes_y_formulario_de_materia(self):
        self.enviar([('SABER', 'Cognitivo'), ('', 'Proyecto')])
        c = self.cliente(self.rectora)
        r = c.get('/admin/configuracion-calificaciones/')
        self.assertContains(r, 'Cognitivo (%)')
        self.assertContains(r, 'Proyecto (%)')
        r = c.post(f'/admin/gestion-academica/materias/editar/{self.materia.id}/', {
            'nombre': 'Matemáticas', 'abreviatura': 'MAT', 'promedia_en_boletin': 'on',
            'etiqueta_saber': '', 'p_SABER': '55', 'p_C4': '40'})
        self.assertContains(r, 'suman 95')
        r = c.post(f'/admin/gestion-academica/materias/editar/{self.materia.id}/', {
            'nombre': 'Matemáticas', 'abreviatura': 'MAT', 'promedia_en_boletin': 'on',
            'etiqueta_saber': '', 'p_SABER': '60', 'p_C4': '40'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.pesos(), {'SABER': 60, 'C4': 40})

    def test_docente_ajusta_porcentajes_de_todos(self):
        import json
        self.enviar([('SABER', 'Cognitivo'), ('', 'Proyecto')])
        ConfiguracionCalificaciones.objects.filter(colegio=self.a).update(docente_puede_modificar=True)
        self.assertContains(self.ingreso(), 'id="p-c4"')
        r = self.cliente(self.u_docente).post('/docente/ingresar-notas/', json.dumps({
            'asignacion_id': self.asig.id, 'periodo_id': self.p1.id, 'estudiantes': [],
            'porcentajes': {'saber': '75', 'c4': '25'}}), content_type='application/json')
        self.assertEqual(r.status_code, 200, r.content)
        self.asig.refresh_from_db()
        self.assertEqual(self.pesos(), {'SABER': 75, 'C4': 25})

    def test_puntoexacto_ofrece_los_del_colegio(self):
        self.enviar([('SABER', 'Cognitivo'), ('', 'Proyecto')])
        r = self.cliente(self.u_docente).get('/puntoexacto/nuevo/')
        self.assertContains(r, '>Proyecto<')
        self.assertNotContains(r, '>HACER<')


class PermisoDelDocente(ColegioDePrueba):

    def test_con_permiso_el_docente_ve_los_de_la_materia_hasta_que_pone_los_suyos(self):
        import json
        ConfiguracionCalificaciones.objects.update_or_create(colegio=self.a, defaults={'docente_puede_modificar': True})
        from notas.models import AsignacionDocente
        asig = AsignacionDocente.objects.get(pk=self.asig.pk)
        self.assertTrue(asig.usar_ponderacion_equitativa)       # así quedan las asignaciones nuevas o importadas
        self.assertEqual(comp.pesos(asig), {'SER': 0, 'SABER': 60, 'HACER': 40})   # los de la materia, no 33/33/33
        r = self.cliente(self.u_docente).get(
            f'/docente/ingresar-notas/?asignacion_id={self.asig.id}&periodo_id={self.p1.id}')
        self.assertContains(r, 'id="p-saber" value="60"')
        self.assertContains(r, 'id="p-hacer" value="40"')
        self.cliente(self.u_docente).post('/docente/ingresar-notas/', json.dumps({
            'asignacion_id': self.asig.id, 'periodo_id': self.p1.id, 'estudiantes': [],
            'porcentajes': {'ser': '10', 'saber': '50', 'hacer': '40'}}), content_type='application/json')
        self.assertEqual(comp.pesos(AsignacionDocente.objects.get(pk=self.asig.pk)), {'SER': 10, 'SABER': 50, 'HACER': 40})

    def test_equitativa_en_enteros_que_suman_100(self):
        ConfiguracionCalificaciones.objects.update_or_create(colegio=self.a, defaults={'docente_puede_modificar': True})
        self.materia.usar_ponderacion_equitativa = True
        self.materia.save()
        r = self.cliente(self.u_docente).get(
            f'/docente/ingresar-notas/?asignacion_id={self.asig.id}&periodo_id={self.p1.id}').content.decode()
        import re
        valores = [int(v) for v in re.findall(r'class="form-control form-control-sm porcentaje-input" id="p-\w+" value="(\d+)"', r)]
        self.assertEqual(sum(valores), 100, valores)


class CarruselOrden(ColegioDePrueba):

    def test_subir_bajar_y_editar(self):
        from notas.models import ImagenCarrusel
        imgs = [ImagenCarrusel.objects.create(colegio=self.a, titulo=t, orden=0, imagen_enlace='https://x.co/a.jpg')
                for t in ('Uno', 'Dos', 'Tres')]
        c = self.cliente(self.rectora)
        h = c.get('/admin/portal/carrusel/').content.decode()
        self.assertIn(f'/admin/portal/carrusel/editar/{imgs[0].pk}/', h)       # antes el botón era href="#"
        c.post(f'/admin/portal/carrusel/mover/{imgs[2].pk}/subir/')
        orden = list(ImagenCarrusel.objects.filter(colegio=self.a).order_by('orden').values_list('titulo', flat=True))
        self.assertEqual(orden, ['Uno', 'Tres', 'Dos'])
        r = c.post(f'/admin/portal/carrusel/editar/{imgs[0].pk}/', {'titulo': 'Uno', 'subtitulo': '', 'orden': '9',
                                                                   'visible': 'on', 'enlace_pegado': 'https://x.co/a.jpg'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(ImagenCarrusel.objects.get(pk=imgs[0].pk).orden, 9)
