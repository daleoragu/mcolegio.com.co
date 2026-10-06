# notas/senales.py
"""Avisos automáticos que nacen de un cambio en los datos.

Estudiante nuevo en un curso -> aviso a los docentes de ese curso.
Sirve sobre todo a quien trabaja la planilla en Excel sin internet: su Excel
no tiene al estudiante nuevo, así que tiene que descargarlo otra vez.

Se dispara cuando un estudiante se crea con curso o cambia de curso. La
promoción de fin de año mueve a todos con bulk_update, que no dispara
señales: así no llueven cientos de avisos en diciembre.
"""
import logging
from datetime import timedelta

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from .models import AsignacionDocente, Estudiante
from .models.comunicaciones import Notificacion

logger = logging.getLogger('mcolegio.avisos')
VENTANA = timedelta(hours=6)   # varios estudiantes seguidos -> un solo aviso por docente


@receiver(pre_save, sender=Estudiante)
def _recordar_curso_anterior(sender, instance, **kwargs):
    if instance.pk:
        instance._curso_anterior_id = (Estudiante.objects.filter(pk=instance.pk)
                                       .values_list('curso_id', flat=True).first())
    else:
        instance._curso_anterior_id = None


@receiver(post_save, sender=Estudiante)
def avisar_estudiante_nuevo(sender, instance, created, raw=False, **kwargs):
    if raw or not instance.curso_id or not instance.is_active:
        return
    if not created and getattr(instance, '_curso_anterior_id', None) == instance.curso_id:
        return
    try:
        avisar_docentes_del_curso(instance)
    except Exception:
        # Un aviso que falla nunca debe impedir matricular a un estudiante.
        logger.exception('No se pudo avisar a los docentes del estudiante %s', instance.pk)


def avisar_docentes_del_curso(estudiante):
    curso = estudiante.curso
    nombre = (estudiante.user.get_full_name() or estudiante.user.username).strip()
    usuarios = {a.docente.user for a in AsignacionDocente.objects.filter(
        colegio_id=estudiante.colegio_id, curso=curso).select_related('docente__user') if a.docente_id}
    try:
        url = reverse('notas:mis_planillas')
    except Exception:
        url = None
    desde = timezone.now() - VENTANA
    marca = f'en {curso.nombre}'
    for u in usuarios:
        # Si ya tiene un aviso sin leer de este curso, se suma ahí en vez de
        # mandar uno por estudiante.
        previo = (Notificacion.objects.filter(destinatario=u, colegio_id=estudiante.colegio_id, leido=False,
                                              tipo='PLANILLA', fecha_creacion__gte=desde,
                                              mensaje__contains=marca).order_by('-fecha_creacion').first())
        if previo:
            cuantos = previo.mensaje.split(' ')[0]
            n = int(cuantos) + 1 if cuantos.isdigit() else 2
            previo.mensaje = (f'{n} estudiantes nuevos {marca}. Si llena la planilla en Excel, '
                              f'descárguela de nuevo para que salgan.')[:255]
            previo.save(update_fields=['mensaje'])
        else:
            Notificacion.objects.create(
                colegio_id=estudiante.colegio_id, destinatario=u, tipo='PLANILLA', url=url,
                mensaje=(f'Nuevo estudiante {marca}: {nombre}. Si llena la planilla en Excel, '
                         f'descárguela de nuevo para que salga.')[:255])
