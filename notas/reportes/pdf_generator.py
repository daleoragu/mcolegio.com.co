# notas/reportes/pdf_generator.py
import datetime
from django.template.loader import render_to_string

from .base_generator import BaseReportGenerator
from .utils import get_meses_for_periodo, get_asistencia_data_for_report

# El servidor no tiene locale en español: strftime('%B') saldría en inglés.
MESES_ES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto',
            'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']


try:
    from weasyprint import HTML
    PDF_SUPPORT = True
except ImportError:
    HTML = None
    PDF_SUPPORT = False

class AsistenciaPDFGenerator(BaseReportGenerator):
    """
    Genera un REPORTE de asistencia en PDF con encabezado dinámico, repetido en cada página
    y con el estilo exacto de la sábana de notas.
    """
    def generate_report(self, request, asignacion, periodo, mes_seleccionado: str):
        if not PDF_SUPPORT:
            return None, "La librería 'WeasyPrint' no está instalada en el servidor."

        reportes_por_mes = []
        meses_a_procesar = []
        
        if mes_seleccionado and mes_seleccionado.lower() != 'todos':
            try:
                mes_num = int(mes_seleccionado)
                meses_a_procesar.append(mes_num)
            except (ValueError, TypeError):
                pass
        else:
            meses_tuplas = get_meses_for_periodo(periodo)
            meses_a_procesar = [mes[0] for mes in meses_tuplas]

        for mes_num in meses_a_procesar:
            nombre_mes_str = MESES_ES[mes_num]
            nombre_completo = f"{nombre_mes_str} {periodo.fecha_inicio.year}"
            
            estudiantes, fechas, resumen = get_asistencia_data_for_report(asignacion, periodo, mes_num)
            
            if estudiantes and fechas:
                tabla_asistencia = []
                for estudiante in estudiantes:
                    nombre_formateado = f"{estudiante.user.last_name.upper()} {estudiante.user.first_name.upper()}"
                    fila_estudiante = {'nombre': nombre_formateado, 'estados': []}
                    for fecha in fechas:
                        estado = resumen.get(estudiante.id, {}).get(fecha, '')
                        fila_estudiante['estados'].append(estado)
                    tabla_asistencia.append(fila_estudiante)
                
                reportes_por_mes.append({
                    'nombre_mes': nombre_completo,
                    'fechas': fechas,
                    'tabla_asistencia': tabla_asistencia,
                })

        if not reportes_por_mes:
            return None, "No se encontraron datos de asistencia para los criterios seleccionados."

        header_html = self._get_pdf_header_html(request)
        body_html = render_to_string('notas/reportes/cuerpo_reporte_asistencia.html', {
            'asignacion': asignacion,
            'periodo': periodo,
            'reportes_por_mes': reportes_por_mes,
        })

        final_html = self._build_final_html(header_html, body_html)
        base_url = request.build_absolute_uri('/')
        pdf_file = HTML(string=final_html, base_url=base_url).write_pdf()

        return pdf_file, None

    def _build_final_html(self, header, body):
        """
        Construye el HTML final del PDF con estilos corregidos para encabezado repetido
        y espaciado de texto ajustado.
        """
        return f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    /* --- Definición de la página y el método para repetir el encabezado --- */
                    @page {{ 
                        size: letter landscape;
                        margin: 4.5cm 1.0cm 1.0cm 1.0cm; /* Margen superior amplio para el encabezado */

                        /* Coloca el contenido del encabezado en la parte superior de cada página */
                        @top-center {{
                            content: element(header_content);
                        }}
                    }}

                    /* --- FUENTE TRADICIONAL (Arial o Helvetica) --- */
                    body {{ 
                        font-family: 'Helvetica', Arial, sans-serif; 
                        font-size: 9pt; 
                        color: #333;
                    }}

                    /* --- ESTILOS PARA EL ENCABEZADO --- */
                    /* Esta regla "saca" el div del flujo normal para que pueda ser usado en @page */
                    #header_content {{
                        position: running(header_content);
                    }}

                    /* Estilos para la tabla del encabezado (idénticos a sabana_pdf.html) */
                    #header_content table {{
                        width: 100%;
                        border-collapse: collapse;
                        border: none;
                    }}
                    #header_content td {{
                        vertical-align: middle;
                        text-align: center;
                        padding: 0; /* Sin padding para controlar mejor el espacio */
                        border: none;
                    }}
                    #header_content .logo-cell {{
                        width: 10%;
                    }}
                    #header_content .info-cell {{
                        width: 80%;
                    }}
                    /* --- CORRECCIÓN DE INTERLINEADO --- */
                    #header_content .info-cell p {{
                        margin: 0; /* Se quita el margen del párrafo */
                        padding: 1px 0; /* Se usa un padding mínimo */
                        line-height: 0.3; /* Se reduce la altura de la línea */
                        font-size: 3pt;
                    }}
                    #header_content .info-cell p.main-title {{
                        font-weight: bold;
                        font-size: 12pt;
                    }}
                    #header_content .escudo {{ 
                        max-height: 100px; 
                        max-width: 100px; 
                    }}

                    /* Estilos para la tabla de asistencia */
                    .tabla-asistencia {{ 
                        width: 100%; 
                        border-collapse: collapse; 
                        margin-top: 15px; 
                    }}
                    .tabla-asistencia th, .tabla-asistencia td {{ 
                        border: 1px solid #999; 
                        padding: 4px;
                        text-align: center; 
                        font-size: 8pt;
                    }}
                    .tabla-asistencia th {{ 
                        background-color: #f2f2f2; 
                        font-weight: bold;
                    }}
                    .nombre-estudiante {{ 
                        text-align: left;
                        width: 25% !important;
                        font-size: 9pt !important;
                        padding-left: 5px;
                    }}

                    /* Estilo para forzar salto de página por mes */
                    .reporte-mensual {{
                        page-break-after: always;
                    }}
                    .reporte-mensual:last-child {{
                        page-break-after: auto;
                    }}
                </style>
            </head>
            <body>
                <!-- Este div es el que WeasyPrint usará para el encabezado en CADA página -->
                <div id="header_content">{header}</div>
                
                <!-- El cuerpo del reporte fluye aquí, después del espacio del margen superior -->
                {body}
            </body>
        </html>
        """
