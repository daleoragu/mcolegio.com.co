"""Carga el material semilla (guía + ficha/taller por DBA) como borradores de un docente.

    python manage.py cargar_semilla --usuario luis --area MAT --grados 1
    python manage.py cargar_semilla --usuario luis --area MAT --grados 1 --imagenes /ruta/banco-imagenes
    python manage.py cargar_semilla --usuario luis --area MAT --grados 6 7 --publicar     # además, al banco libre

Las imágenes de IA que no estén en --imagenes quedan como «Imagen pendiente»; cuando lleguen:
    python manage.py poner_imagenes_semilla --imagenes /ruta/banco-imagenes
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from materiales.semilla import armar


class Command(BaseCommand):
    help = 'Crea los borradores de las guías semilla de un área y unos grados (y opcionalmente los publica en el banco libre).'
    area_fija = None

    def add_arguments(self, parser):
        parser.add_argument('--usuario', required=True, help='Docente dueño de los borradores.')
        if not self.area_fija:
            parser.add_argument('--area', default='MAT', choices=sorted({a for a, _ in armar.MODULOS}))
        parser.add_argument('--grados', nargs='+', type=int, required=not self.area_fija, default=[6, 7] if self.area_fija else None)
        parser.add_argument('--colegio', help='Slug del colegio, si el docente los va a ver desde el colegio (sin esto: su Salón Digital).')
        parser.add_argument('--imagenes', nargs='*', default=[], help='Carpeta(s) con las imágenes del banco (m1-manzana.png…).')
        parser.add_argument('--publicar', action='store_true', help='Publicarlos de una vez en el banco libre.')

    def handle(self, *args, **o):
        area = self.area_fija or o['area']
        u = User.objects.filter(username=o['usuario']).first()
        if u is None:
            raise CommandError(f'No existe el usuario «{o["usuario"]}».')
        if o['publicar'] and not u.is_superuser:
            raise CommandError('Solo un superusuario publica en el banco libre.')
        faltan = [g for g in o['grados'] if (area, g) not in armar.MODULOS]
        if faltan:
            hay = sorted(g for a, g in armar.MODULOS if a == area)
            raise CommandError(f'No hay material semilla de {area} para {faltan}. Hay: {hay}.')
        colegio = None
        if o.get('colegio'):
            from notas.models import Colegio
            colegio = Colegio.objects.filter(slug=o['colegio']).first()
            if colegio is None:
                raise CommandError(f'No existe el colegio «{o["colegio"]}».')
        total = pendientes = 0
        with transaction.atomic():
            for g in o['grados']:
                docs = armar.guardar(u, g, publicar=o['publicar'], colegio=colegio, area=area, carpetas=o['imagenes'])
                n = sum(1 for d in docs for b in d.contenido['bloques']
                        if b['tipo'] == 'recuadro' and b.get('titulo', '').startswith(armar.PENDIENTE))
                total += len(docs)
                pendientes += n
                self.stdout.write(f'{area} {g}.º: {len(docs)} documentos' + (f' · {n} imágenes pendientes' if n else ''))
        self.stdout.write(self.style.SUCCESS(
            f'Listo: {total} borradores en «Mis materiales» de {u.username}' + (' y publicados en el banco libre.' if o['publicar'] else '.')))
        if pendientes:
            self.stdout.write(f'Cuando lleguen las imágenes: python manage.py poner_imagenes_semilla --imagenes <carpeta>')
