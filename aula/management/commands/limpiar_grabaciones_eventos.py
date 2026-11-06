"""Borra las grabaciones de cámara y micrófono de los eventos que ya cumplieron sus días de guarda.

Correrlo una vez al día (por ejemplo en el cron del servidor):  python manage.py limpiar_grabaciones_eventos
"""
from django.core.management.base import BaseCommand

from aula.models import Evento, GrabacionEvento
from aula.views_eventos import limpiar_grabaciones


class Command(BaseCommand):
    help = 'Borra las grabaciones de los eventos que ya cumplieron los días de guarda.'

    def handle(self, *args, **opciones):
        total = 0
        for ev in Evento.objects.filter(pk__in=GrabacionEvento.objects.values('participacion__evento')):
            total += limpiar_grabaciones(ev)
        self.stdout.write(f'Se borraron {total} trozo(s) de grabación vencidos.')
