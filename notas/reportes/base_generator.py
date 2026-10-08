# notas/reportes/base_generator.py
import os
from openpyxl.styles import Font, Alignment
from openpyxl.drawing.image import Image as OpenpyxlImage
from django.template.loader import render_to_string

class BaseReportGenerator:
    """
    Clase base para generadores de reportes.
    Contiene la lógica común para añadir un encabezado estandarizado.
    """
    def __init__(self, colegio):
        if not colegio:
            raise ValueError("Se requiere un objeto 'colegio' para inicializar el generador.")
        self.colegio = colegio

    def _get_pdf_header_html(self, request):
        """
        Renderiza el template del encabezado a HTML para usarlo en un PDF.
        """
        context = {'colegio': self.colegio}
        return render_to_string('notas/fragmentos/encabezado_pdf.html', context, request=request)

    def _add_excel_header(self, worksheet):
        """
        Añade el encabezado visual (logos y texto) a una hoja de cálculo de openpyxl.
        """
        # --- 1. Configuración de la página ---
        # Definir altura de las filas del encabezado
        for i in range(1, 7):
            worksheet.row_dimensions[i].height = 18

        # Ancho de columnas
        worksheet.column_dimensions['A'].width = 20
        worksheet.column_dimensions['P'].width = 20
        for i in range(2, 16): # Columnas B a O
            ws_col_letter = worksheet.cell(row=1, column=i).column_letter
            worksheet.column_dimensions[ws_col_letter].width = 8

        # --- 2. Insertar Logos (en celdas no combinadas) ---
        try:
            if self.colegio.logo_izquierdo and os.path.exists(self.colegio.logo_izquierdo.path):
                img_izq = OpenpyxlImage(self.colegio.logo_izquierdo.path)
                img_izq.height = 90
                img_izq.width = 90
                worksheet.add_image(img_izq, 'A1')
        except (ValueError, FileNotFoundError) as e:
            print(f"ADVERTENCIA: No se pudo cargar el logo izquierdo: {e}")

        try:
            if self.colegio.logo_derecho and os.path.exists(self.colegio.logo_derecho.path):
                img_der = OpenpyxlImage(self.colegio.logo_derecho.path)
                img_der.height = 90
                img_der.width = 90
                worksheet.add_image(img_der, 'P1')
        except (ValueError, FileNotFoundError) as e:
            print(f"ADVERTENCIA: No se pudo cargar el logo derecho: {e}")

        # --- 3. Insertar Texto del Encabezado ---
        # --- CORRECCIÓN: Se combina solo el área de texto, sin superponer con los logos ---
        worksheet.merge_cells('B1:O6')
        # Se escribe en la celda superior izquierda (B1) de la combinación
        cell = worksheet['B1']
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        lineas = [
            self.colegio.linea_encabezado_1,
            self.colegio.linea_encabezado_2,
            self.colegio.linea_encabezado_3,
            self.colegio.linea_encabezado_4,
            getattr(self.colegio, 'linea_encabezado_5', None),
        ]
        texto_completo = "\n".join(filter(None, lineas))
        
        # Se asigna el valor a la celda B1
        cell.value = texto_completo
        
        if self.colegio.linea_encabezado_1:
            cell.font = Font(
                name=self.colegio.linea_encabezado_1_fuente or 'Arial', 
                size=self.colegio.linea_encabezado_1_tamano or 12, 
                bold=self.colegio.linea_encabezado_1_negrilla or False, 
                italic=self.colegio.linea_encabezado_1_cursiva or False
            )
