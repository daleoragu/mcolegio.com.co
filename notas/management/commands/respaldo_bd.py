# notas/management/commands/respaldo_bd.py
"""Copia de seguridad de toda la base de datos.

Guarda un archivo comprimido (mcolegio_AAAA-MM-DD_HHMM.json.gz) con todos los
datos y conserva solo los más recientes.

  * En producción (con Spaces configurado) va a la carpeta privada
    «respaldos/» del Space: NO es pública aunque las imágenes sí lo sean.
    Se descarga desde el panel de DigitalOcean (Spaces → el bucket → respaldos).
  * En el computador, sin Spaces, va a la carpeta «respaldos/» del proyecto.

Uso:
    python manage.py respaldo_bd               # copia y deja las 14 más recientes
    python manage.py respaldo_bd --conservar 30
    python manage.py respaldo_bd --listar

Pensado para correr cada noche como tarea programada (Job) de App Platform,
porque la base de datos «Dev» de DigitalOcean no tiene copias automáticas.

Restaurar (en una base vacía, después de `python manage.py migrate`):
    gunzip mcolegio_AAAA-MM-DD_HHMM.json.gz
    python manage.py loaddata mcolegio_AAAA-MM-DD_HHMM.json
"""
import gzip
import io
import os

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.utils import timezone

PREFIJO = 'mcolegio_'
CARPETA = 'respaldos'
# Lo que se vuelve a crear solo con `migrate` o que no hace falta guardar.
EXCLUIR = ['contenttypes', 'auth.permission', 'sessions', 'admin.logentry']
# La base «Dev» de DigitalOcean tiene 1 GB de disco.
LIMITE_DEV_BYTES = 1024 ** 3


def almacen():
    """Dónde se guardan las copias: Spaces privado en producción, una carpeta local si no."""
    if getattr(settings, 'RESPALDOS_DIR', None):
        from django.core.files.storage import FileSystemStorage
        return FileSystemStorage(location=str(settings.RESPALDOS_DIR))
    if os.getenv('DO_SPACES_BUCKET_NAME'):
        from storages.backends.s3boto3 import S3Boto3Storage
        region = os.getenv('DO_SPACES_REGION')
        return S3Boto3Storage(
            access_key=os.getenv('DO_SPACES_ACCESS_KEY'),
            secret_key=os.getenv('DO_SPACES_SECRET_KEY'),
            bucket_name=os.getenv('DO_SPACES_BUCKET_NAME'),
            region_name=region,
            endpoint_url=f'https://{region}.digitaloceanspaces.com',
            location=CARPETA,
            default_acl='private',          # nunca pública
            querystring_auth=True,
            file_overwrite=True,
        )
    from django.core.files.storage import FileSystemStorage
    return FileSystemStorage(location=str(settings.BASE_DIR / CARPETA))


def copias(storage):
    try:
        _, archivos = storage.listdir('')
    except FileNotFoundError:
        return []
    return sorted(a for a in archivos if a.startswith(PREFIJO) and a.endswith('.json.gz'))


def tamano_base():
    """Bytes que ocupa la base (solo PostgreSQL); None si no se puede saber."""
    if connection.vendor != 'postgresql':
        return None
    with connection.cursor() as c:
        c.execute('SELECT pg_database_size(current_database())')
        return c.fetchone()[0]


def _mb(n):
    return f'{n / 1024 / 1024:.1f} MB'


class Command(BaseCommand):
    help = 'Copia de seguridad de toda la base de datos (comprimida), conservando las más recientes.'

    def add_arguments(self, parser):
        parser.add_argument('--conservar', type=int, default=14, help='Cuántas copias guardar (14 por defecto).')
        parser.add_argument('--listar', action='store_true', help='Solo muestra las copias que hay.')

    def handle(self, *args, **opciones):
        storage = almacen()
        if opciones['listar']:
            lista = copias(storage)
            for nombre in lista:
                self.stdout.write(f'  {nombre}  ({_mb(storage.size(nombre))})')
            self.stdout.write(f'{len(lista)} copia(s).')
            return

        if opciones['conservar'] < 1:
            raise CommandError('--conservar debe ser 1 o más.')

        nombre = f'{PREFIJO}{timezone.localtime():%Y-%m-%d_%H%M}.json.gz'
        crudo = io.BytesIO()
        with gzip.GzipFile(fileobj=crudo, mode='wb') as comprimido:
            texto = io.TextIOWrapper(comprimido, encoding='utf-8')
            call_command('dumpdata', natural_foreign=True, natural_primary=True, exclude=EXCLUIR,
                         stdout=texto, verbosity=0)
            texto.flush()
            texto.detach()
        datos = crudo.getvalue()
        if storage.exists(nombre):
            storage.delete(nombre)
        storage.save(nombre, ContentFile(datos))
        self.stdout.write(self.style.SUCCESS(f'Copia guardada: {CARPETA}/{nombre} ({_mb(len(datos))} comprimida).'))

        # Solo las más recientes.
        lista = copias(storage)
        sobran = lista[:-opciones['conservar']] if len(lista) > opciones['conservar'] else []
        for viejo in sobran:
            storage.delete(viejo)
        if sobran:
            self.stdout.write(f'Se borraron {len(sobran)} copia(s) antigua(s); quedan {len(lista) - len(sobran)}.')

        # Aviso del disco de la base «Dev» (1 GB).
        tam = tamano_base()
        if tam is not None:
            uso = tam / LIMITE_DEV_BYTES * 100
            self.stdout.write(f'Tamaño de la base: {_mb(tam)} ({uso:.0f} % de 1 GB).')
            if uso >= 80:
                self.stdout.write(self.style.WARNING(
                    'ATENCIÓN: la base de datos pasa del 80 % de su disco de 1 GB. Hay que ampliarla pronto.'))
