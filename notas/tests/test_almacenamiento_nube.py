"""En producción los archivos están en DigitalOcean Spaces, que no tiene ruta en disco (.path)."""
import inspect
import io
import tempfile

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.test import override_settings

from .base import ColegioDePrueba

CARPETA = tempfile.mkdtemp(prefix='nube-')


class SinRutas(FileSystemStorage):
    """Como Spaces: guarda y abre archivos, pero .path no existe."""

    def __init__(self, **kw):
        super().__init__(location=CARPETA, **kw)

    def path(self, name):
        if inspect.currentframe().f_back.f_globals.get('__name__', '').startswith('django.core.files.storage'):
            return super().path(name)
        raise NotImplementedError("This backend doesn't support absolute paths.")


@override_settings(STORAGES={'default': {'BACKEND': 'notas.tests.test_almacenamiento_nube.SinRutas'},
                             'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}})
class ReportesConArchivosEnLaNube(ColegioDePrueba):

    def test_planilla_de_asistencia_en_excel_con_logos(self):
        from PIL import Image
        b = io.BytesIO()
        Image.new('RGB', (40, 40), 'red').save(b, 'PNG')
        self.a.logo_izquierdo.save('logo.png', ContentFile(b.getvalue()), save=True)
        r = self.cliente(self.u_docente).get(
            f'/docente/reportes/asistencia/excel/?asignacion_id={self.asig.id}&periodo_id={self.p1.id}&mes=todos')
        self.assertEqual(r.status_code, 200)
        import openpyxl
        libro = openpyxl.load_workbook(io.BytesIO(r.content))
        self.assertTrue(libro.active._images)                 # el logo sí quedó en la hoja
