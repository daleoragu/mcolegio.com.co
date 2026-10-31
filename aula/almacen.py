"""Dónde se guardan los archivos del aula.

En producción van al Space, pero PRIVADOS (enlace firmado que vence), no
públicos como las imágenes del portal: son guías, tareas y trabajos de los
estudiantes. En el computador, en la carpeta media de siempre.
"""
import os
import uuid

from django.core.files.storage import default_storage


def privado():
    if os.getenv('DO_SPACES_BUCKET_NAME'):
        from storages.backends.s3boto3 import S3Boto3Storage
        region = os.getenv('DO_SPACES_REGION')
        return S3Boto3Storage(
            access_key=os.getenv('DO_SPACES_ACCESS_KEY'),
            secret_key=os.getenv('DO_SPACES_SECRET_KEY'),
            bucket_name=os.getenv('DO_SPACES_BUCKET_NAME'),
            region_name=region,
            endpoint_url=f'https://{region}.digitaloceanspaces.com',
            location='aula',
            default_acl='private',
            querystring_auth=True,
            querystring_expire=6 * 3600,
            file_overwrite=False,
        )
    return default_storage


def _ruta(carpeta, nombre):
    base, ext = os.path.splitext(nombre or 'archivo')
    base = ''.join(c for c in base if c.isalnum() or c in '-_')[:40] or 'archivo'
    return f'{carpeta}/{uuid.uuid4().hex[:12]}-{base}{ext.lower()[:8]}'


def ruta_publicacion(instancia, nombre):
    return _ruta(f'aula/{instancia.aula_id}/muro', nombre)


def ruta_material(instancia, nombre):
    return _ruta(f'aula/{instancia.aula_id}/material', nombre)


def ruta_tarea(instancia, nombre):
    return _ruta(f'aula/{instancia.aula_id}/tareas', nombre)


def ruta_entrega(instancia, nombre):
    return _ruta(f'aula/entregas/{instancia.tarea_id}', nombre)


def ruta_ficha(instancia, nombre):
    """Fotos y audios que el estudiante manda como respuesta de una ficha."""
    return _ruta(f'aula/fichas/{instancia.entrega.tarea_id}', nombre)
