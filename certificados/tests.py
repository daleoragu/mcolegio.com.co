# -*- coding: utf-8 -*-
"""Certificados: datos por año, años anteriores desde Excel, QR de verificación y entrega a las familias."""
from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook

from notas.models import (AreaConocimiento, Calificacion, Estudiante, FichaEstudiante, HistorialMatricula,
                          PonderacionAreaMateria)
from notas.tests.base import ColegioDePrueba

from . import logica
from .models import CalificacionHistorica, CertificadoEmitido, ConfiguracionCertificados, SolicitudCertificado


def _excel(filas, cabecera=None):
    wb = Workbook()
    ws = wb.active
    ws.title = 'Notas'
    ws.append(cabecera or [c[1] for c in logica.COLUMNAS])
    for f in filas:
        ws.append(f)
    buf = BytesIO()
    wb.save(buf)
    return SimpleUploadedFile('notas.xlsx', buf.getvalue())


class Certificados(ColegioDePrueba):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        area = AreaConocimiento.objects.create(colegio=cls.a, nombre='Matemáticas')
        PonderacionAreaMateria.objects.create(colegio=cls.a, area=area, materia=cls.materia, peso_porcentual=100)
        cls.ana = cls.estudiantes[0]
        FichaEstudiante.objects.create(estudiante=cls.ana, numero_documento='1110555', tipo_documento='TI')
        for p, v in ((cls.p1, '4.0'), (cls.p2, '4.4')):
            Calificacion.objects.create(colegio=cls.a, estudiante=cls.ana, materia=cls.materia, periodo=p,
                                        tipo_nota='PROM_PERIODO', valor_nota=Decimal(v))

    # --- Datos ---------------------------------------------------------------
    def test_ano_en_curso_sale_de_la_plataforma_y_es_parcial(self):
        self.assertEqual(logica.anos_disponibles(self.ana), [2026])
        c = logica.contenido_calificaciones(self.ana, 2026)
        self.assertTrue(c['parcial'])
        self.assertEqual(c['areas'][0]['nombre'], 'MATEMÁTICAS')
        self.assertEqual(c['areas'][0]['nota'], '4,2')
        self.assertEqual(c['areas'][0]['desempeno'], 'ALTO')
        self.assertEqual(c['documento'], '1110555')
        self.assertIn('Sexto', c['grado'])

    def test_sin_notas_no_hay_certificado(self):
        with self.assertRaises(logica.SinDatos):
            logica.contenido_calificaciones(self.ana, 2015)

    def test_emitir_guarda_copia_y_codigo(self):
        cert = logica.emitir(self.ana, 'CALIFICACIONES', 2026, self.rectora)
        self.assertEqual(len(cert.codigo), 12)
        self.assertEqual(cert.contenido['colegio'], 'Colegio A')
        self.assertEqual(cert.contenido['firma_nombre'], '')  # sin firma configurada ni admin principal
        # Lo emitido no cambia si después cambian las notas.
        Calificacion.objects.filter(estudiante=self.ana).update(valor_nota=Decimal('1.0'))
        cert.refresh_from_db()
        self.assertEqual(cert.contenido['areas'][0]['nota'], '4,2')

    def test_estudio_solo_para_matriculados(self):
        self.assertEqual(logica.emitir(self.ana, 'ESTUDIO').contenido['ano'], 2026)
        ex = self.estudiantes[1]
        ex.is_active = False
        ex.save()
        with self.assertRaises(logica.SinDatos):
            logica.emitir(ex, 'ESTUDIO')

    # --- Excel ---------------------------------------------------------------
    def test_importar_anos_anteriores_y_crear_exalumno(self):
        archivo = _excel([
            [1110555, '', '', 2019, 'Sexto', 'Matemáticas', '', 5, 4.6, '', 'Promovido'],
            ['1110555', '', '', 2019, 'Sexto', 'Humanidades', 'Lengua castellana', 4, '3,5', '', ''],
            ['1110555', '', '', 2019, 'Sexto', 'Humanidades', 'Inglés', 2, 4.4, '', ''],
            [99887766.0, 'Gómez Ruiz', 'Luis', 2010, 'Undécimo', 'Física', '', 3, 3.2, 'Básico', 'Graduado'],
        ])
        resumen, errores = logica.importar_excel(archivo, self.a, self.rectora)
        self.assertEqual(errores, [])
        self.assertEqual(resumen, {'estudiantes': 2, 'anos': 2, 'filas': 4, 'exalumnos_creados': 1})
        self.assertEqual(logica.anos_disponibles(self.ana), [2026, 2019])
        c = logica.contenido_calificaciones(self.ana, 2019)
        self.assertEqual(c['grado'], 'Sexto')
        hum = next(a for a in c['areas'] if a['nombre'] == 'HUMANIDADES')
        # Sin fila del área: promedio por intensidad horaria (3,5*4 + 4,4*2) / 6 = 3,8
        self.assertEqual((hum['nota'], hum['ih'], hum['desempeno']), ('3,8', 6, 'BÁSICO'))
        self.assertIn('PROMOVIDO', c['resultado'])
        luis = Estudiante.objects.get(ficha__numero_documento='99887766')
        self.assertFalse(luis.is_active)
        self.assertFalse(luis.user.is_active)
        self.assertEqual(HistorialMatricula.objects.get(estudiante=luis).resultado, 'GRADUADO')
        # Volver a subir el mismo año reemplaza, no duplica.
        logica.importar_excel(_excel([['1110555', '', '', 2019, 'Sexto', 'Matemáticas', '', 5, 4.0, '', '']]),
                              self.a, self.rectora)
        self.assertEqual(CalificacionHistorica.objects.filter(estudiante=self.ana, ano_lectivo=2019).count(), 1)

    def test_importar_con_errores_no_guarda_nada(self):
        resumen, errores = logica.importar_excel(_excel([
            ['1110555', '', '', 2019, 'Sexto', 'Matemáticas', '', 5, 4.6, '', ''],
            ['1110555', '', '', 2019, 'Sexto', 'Ciencias', '', 5, 9.0, '', ''],
            ['5555', '', '', 2018, 'Quinto', 'Ciencias', '', 5, 4.0, '', ''],
        ]), self.a, self.rectora)
        self.assertIsNone(resumen)
        self.assertTrue(any('Fila 3' in e and 'fuera de la escala' in e for e in errores))
        self.assertTrue(any('5555' in e for e in errores))
        self.assertFalse(CalificacionHistorica.objects.exists())

    def test_importar_sin_columnas_obligatorias(self):
        with self.assertRaises(logica.SinDatos):
            list(logica.importar_excel(_excel([['x']], cabecera=['Nombre']), self.a, self.rectora))

    # --- Pantallas ------------------------------------------------------------
    def test_secretaria_genera_pdf_y_se_verifica(self):
        c = self.cliente(self.rectora)
        self.assertContains(c.get('/certificados/?q=prueba'), 'Ana')
        self.assertContains(c.get(f'/certificados/estudiante/{self.ana.id}/'), '2026')
        r = c.post(f'/certificados/estudiante/{self.ana.id}/generar/', {'tipo': 'CALIFICACIONES', 'ano': 2026})
        cert = CertificadoEmitido.objects.get()
        self.assertRedirects(r, f'/certificados/{cert.codigo}/pdf/', fetch_redirect_response=False)
        pagina = self.cliente().get(f'/certificados/verificar/{cert.codigo}/')
        self.assertContains(pagina, 'Certificado auténtico')
        self.assertContains(pagina, '•••0555')
        self.assertNotContains(pagina, '1110555')     # el documento sale oculto
        c.post(f'/certificados/{cert.codigo}/anular/', {'motivo': 'Error en el nombre'})
        self.assertContains(self.cliente().get(f'/certificados/verificar/{cert.codigo}/'), 'ANULADO')
        self.assertContains(self.cliente().get('/certificados/verificar/NOEXISTE1234/'), 'No existe')

    def test_el_estudiante_no_ve_certificados_ajenos(self):
        cert = logica.emitir(self.ana, 'ESTUDIO')
        beto = self.estudiantes[1]
        self.assertEqual(self.cliente(beto.user).get(f'/certificados/{cert.codigo}/pdf/').status_code, 403)
        self.assertEqual(self.cliente(self.u_docente).get('/certificados/').status_code, 403)

    def test_familia_pide_y_secretaria_aprueba(self):
        fam = self.cliente(self.ana.user)
        self.assertContains(fam.get('/certificados/mis-certificados/'), 'Pedir')
        fam.post('/certificados/mis-certificados/pedir/', {'tipo': 'CALIFICACIONES', 'ano': 2026, 'motivo': 'Traslado'})
        fam.post('/certificados/mis-certificados/pedir/', {'tipo': 'CALIFICACIONES', 'ano': 2026})
        sol = SolicitudCertificado.objects.get()           # no se duplica
        self.assertEqual(sol.motivo, 'Traslado')
        self.assertContains(self.cliente(self.rectora).get('/certificados/'), 'Solicitudes de las familias')
        self.cliente(self.rectora).post(f'/certificados/solicitud/{sol.id}/resolver/', {'accion': 'aprobar'})
        sol.refresh_from_db()
        self.assertEqual(sol.estado, 'APROBADA')
        self.assertContains(fam.get('/certificados/mis-certificados/'), sol.certificado.codigo)

    def test_descarga_libre_y_solo_secretaria(self):
        conf = ConfiguracionCertificados.de(self.a)
        conf.modo_entrega = 'LIBRE'
        conf.save()
        r = self.cliente(self.ana.user).post('/certificados/mis-certificados/pedir/', {'tipo': 'ESTUDIO'})
        self.assertEqual(r.status_code, 302)
        self.assertIn('/pdf/', r['Location'])
        conf.modo_entrega = 'SECRETARIA'
        conf.save()
        self.cliente(self.ana.user).post('/certificados/mis-certificados/pedir/', {'tipo': 'ESTUDIO'})
        self.assertEqual(CertificadoEmitido.objects.count(), 1)
        self.assertFalse(SolicitudCertificado.objects.exists())

    def test_plantilla_y_direcciones_viejas(self):
        c = self.cliente(self.rectora)
        self.assertEqual(c.get('/certificados/importar/plantilla/').status_code, 200)
        self.assertRedirects(c.get('/herramientas/certificados/'), '/certificados/', fetch_redirect_response=False)
