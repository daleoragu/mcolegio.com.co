"""La copia de seguridad de la base de datos: se guarda comprimida y se conservan las más recientes."""
import gzip
import json
import tempfile
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import override_settings

from .base import ColegioDePrueba


class RespaldoBD(ColegioDePrueba):

    def test_guarda_la_copia_y_conserva_las_mas_recientes(self):
        with tempfile.TemporaryDirectory() as carpeta, override_settings(RESPALDOS_DIR=carpeta):
            # Copias viejas de días anteriores
            for dia in range(1, 6):
                Path(carpeta, f'mcolegio_2026-01-0{dia}_0300.json.gz').write_bytes(gzip.compress(b'[]'))
            Path(carpeta, 'otro_archivo.txt').write_text('no se toca')
            salida = StringIO()
            call_command('respaldo_bd', conservar=3, stdout=salida)
            self.assertIn('Copia guardada', salida.getvalue())

            nombres = sorted(p.name for p in Path(carpeta).iterdir())
            copias = [n for n in nombres if n.startswith('mcolegio_')]
            self.assertEqual(len(copias), 3)
            self.assertIn('otro_archivo.txt', nombres)
            self.assertNotIn('mcolegio_2026-01-01_0300.json.gz', nombres)

            nueva = max(copias)
            datos = json.loads(gzip.decompress(Path(carpeta, nueva).read_bytes()))
            modelos = {d['model'] for d in datos}
            self.assertIn('notas.colegio', modelos)
            self.assertIn('notas.estudiante', modelos)
            self.assertNotIn('contenttypes.contenttype', modelos)
            self.assertTrue(any(d['model'] == 'notas.colegio' and d['fields']['nombre'] == 'Colegio A' for d in datos))

            salida = StringIO()
            call_command('respaldo_bd', listar=True, stdout=salida)
            self.assertIn('3 copia(s)', salida.getvalue())
