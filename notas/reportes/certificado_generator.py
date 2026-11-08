# notas/reportes/certificado_generator.py

from django.template.loader import render_to_string
from django.utils import timezone
from io import BytesIO
from ..utils.numero_a_letras import numero_a_letras # Utilidad para convertir números a texto

# Es necesario tener instalada la librería WeasyPrint
# pip install WeasyPrint
from ..perezoso import CSS, HTML  # WeasyPrint se carga al generar el PDF, no al arrancar

class CertificadoPDFGenerator:
    """
    Genera un certificado de estudios en formato PDF para un estudiante.
    """
    def __init__(self, colegio):
        if HTML is None:
            raise ImportError("La librería WeasyPrint no está instalada. Por favor, ejecute: pip install WeasyPrint")
        self.colegio = colegio

    def _get_nombre_mes(self, mes_num):
        meses = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
        ]
        return meses[mes_num - 1]

    def generate_report(self, request, estudiante):
        """
        Renderiza la plantilla HTML del certificado y la convierte a PDF.
        """
        hoy = timezone.now().date()
        
        context = {
            'colegio': self.colegio,
            'estudiante': estudiante,
            'dia_actual': numero_a_letras(hoy.day).upper(),
            'mes_actual': self._get_nombre_mes(hoy.month).upper(),
            'ano_actual': numero_a_letras(hoy.year).upper(),
            'fecha_larga': f"a los {hoy.day} días del mes de {self._get_nombre_mes(hoy.month)} de {hoy.year}",
            'logo_url': request.build_absolute_uri(self.colegio.escudo.url) if self.colegio.escudo else None,
        }

        # Renderizar la plantilla HTML con el contexto
        html_string = render_to_string('notas/admin_tools/certificado_estudio.html', context)
        
        # Crear el PDF en memoria
        pdf_file = BytesIO()
        html = HTML(string=html_string, base_url=request.build_absolute_uri())
        html.write_pdf(pdf_file)
        
        # Regresar al inicio del buffer
        pdf_file.seek(0)
        
        return pdf_file, None # Devuelve el archivo y ningún error
