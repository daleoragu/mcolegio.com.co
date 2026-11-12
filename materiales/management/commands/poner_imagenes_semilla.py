"""Pone las imágenes del banco en los recuadros «Imagen pendiente» de las guías semilla (borradores y banco libre).

    python manage.py poner_imagenes_semilla --imagenes /ruta/banco-imagenes
    python manage.py poner_imagenes_semilla --imagenes /ruta/banco-imagenes --usuario luis
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from materiales.models import Documento, MaterialCompartido
from materiales.semilla import armar


class Command(BaseCommand):
    help = 'Cambia los recuadros «Imagen pendiente» por las imágenes que ya están en la carpeta.'

    def add_arguments(self, parser):
        parser.add_argument('--imagenes', nargs='+', required=True, help='Carpeta(s) con las imágenes (m1-manzana.png…).')
        parser.add_argument('--usuario', help='Solo los documentos de este docente.')

    def handle(self, *args, **o):
        docs = Documento.objects.filter(contenido__icontains=armar.PENDIENTE)
        if o.get('usuario'):
            docs = docs.filter(propietario__username=o['usuario'])
        n_docs = n_img = 0
        with transaction.atomic():
            for doc in docs:
                puestas = armar.poner_pendientes(doc, o['imagenes'])
                if puestas:
                    n_docs += 1
                    n_img += puestas
                    for m in MaterialCompartido.objects.filter(documento=doc):
                        m.contenido = doc.contenido
                        m.save(update_fields=['contenido'])
        quedan = sum(str(d.contenido).count(armar.PENDIENTE) for d in Documento.objects.filter(contenido__icontains=armar.PENDIENTE))
        self.stdout.write(self.style.SUCCESS(f'{n_img} imágenes puestas en {n_docs} documentos. Quedan {quedan} pendientes.'))
