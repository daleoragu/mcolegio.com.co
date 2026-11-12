"""Carga el material semilla de Matemáticas (guía + taller por DBA) como borradores de un docente.

    python manage.py cargar_semilla_matematicas --usuario luis --grados 6 7
    python manage.py cargar_semilla_matematicas --usuario profe --grados 7 --colegio sanjose     # en el colegio
    python manage.py cargar_semilla_matematicas --usuario luis --grados 6 --publicar   # además, al banco libre
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from materiales.semilla import armar


class Command(BaseCommand):
    help = 'Crea los borradores de las guías y talleres semilla de Matemáticas (y opcionalmente los publica en el banco libre).'

    def add_arguments(self, parser):
        parser.add_argument('--usuario', required=True, help='Docente dueño de los borradores.')
        parser.add_argument('--grados', nargs='+', type=int, default=[6, 7], choices=sorted(armar.MODULOS))
        parser.add_argument('--colegio', help='Slug del colegio, si el docente los va a ver desde el colegio (sin esto: su Salón Digital).')
        parser.add_argument('--publicar', action='store_true', help='Publicarlos de una vez en el banco libre.')

    def handle(self, *args, **o):
        u = User.objects.filter(username=o['usuario']).first()
        if u is None:
            raise CommandError(f'No existe el usuario «{o["usuario"]}».')
        if o['publicar'] and not u.is_superuser:
            raise CommandError('Solo un superusuario publica en el banco libre.')
        colegio = None
        if o.get('colegio'):
            from notas.models import Colegio
            colegio = Colegio.objects.filter(slug=o['colegio']).first()
            if colegio is None:
                raise CommandError(f'No existe el colegio «{o["colegio"]}».')
        total = 0
        with transaction.atomic():
            for g in o['grados']:
                docs = armar.guardar(u, g, publicar=o['publicar'], colegio=colegio)
                total += len(docs)
                self.stdout.write(f'{g}.º: {len(docs)} documentos')
        self.stdout.write(self.style.SUCCESS(
            f'Listo: {total} borradores en «Mis materiales» de {u.username}' + (' y publicados en el banco libre.' if o['publicar'] else '.')))
