"""Compartir lo que hace el docente: con una de sus clases (toda o algunos estudiantes) o con un colega.

Sirve igual en el colegio y en el plan individual (Mi Salón Virtual):
  · Con una clase: se hace una copia en esa clase, para todos o para los estudiantes que escoja.
  · Con un colega (en el colegio, los compañeros docentes; en el plan individual, «Mis colegas»): le llega un aviso
    y en «Compartido conmigo» lo agrega a la clase que quiera, también escogiendo estudiantes.

Qué se comparte: actividades interactivas, clases invertidas, publicaciones del muro del aula y talleres HTML de
«Actividades y pruebas» (los de un solo archivo; un sitio .zip se comparte con su enlace).
"""
from django.core.files.base import ContentFile
from django.http import Http404
from django.urls import reverse

from . import logica
from .models import Actividad, Aula, ClaseInvertida, CompartidoDocente, Publicacion

TIPOS = dict(CompartidoDocente.TIPOS)


def _acceso(request):
    from materiales.views import Acceso
    return Acceso(request)


def mis_aulas(request):
    """Las clases del docente (en el plan individual, una por cada grupo)."""
    a = _acceso(request)
    if a.colegio is None and a.cuenta is not None:
        for g in a.cuenta.grupos.filter(activo=True):
            logica.aula_de_grupo(g)
    return a.aulas()


def colegas(request):
    """A quién le puede compartir: compañeros del colegio o sus colegas del plan individual."""
    from chat.views_colegas import nombre_de
    from materiales.views_equipo import candidatos
    a = _acceso(request)
    if not a.ok:
        return []
    return [{'id': u.pk, 'nombre': nombre_de(u)} for u in candidatos(a).order_by('first_name', 'last_name')[:300]]


def _es_suya(request, aula):
    return aula.pk in {x.pk for x in mis_aulas(request)}


def objeto(request, tipo, oid, recibido=False):
    """El objeto a compartir. Si no es del docente (y no se lo compartieron), 404.
    Lo del muro de la comunidad lo puede compartir cualquier docente que lo vea (es de otro docente)."""
    if tipo == 'muro':
        from chat.models import Publicacion as PubMuro
        from chat.views_colegas import es_docente
        from chat.views_muro import visibles
        if not es_docente(request.user):
            raise Http404
        qs = PubMuro.objects.filter(oculta=False) if recibido else visibles(request.user)
        obj = qs.filter(pk=oid).select_related('autor', 'pagina', 'documento').first()
        if obj is None:
            raise Http404
        return obj
    if tipo == 'pagina':
        from salon_digital.models import PaginaPublicada
        obj = PaginaPublicada.objects.filter(pk=oid).select_related('propietario__usuario').first()
        if obj is None or (not recibido and obj.propietario.usuario_id != request.user.pk):
            raise Http404
        return obj
    modelo = {'actividad': Actividad, 'invertida': ClaseInvertida, 'publicacion': Publicacion}.get(tipo)
    if modelo is None:
        raise Http404
    obj = modelo.objects.filter(pk=oid).select_related('aula').first()
    if obj is None or (not recibido and not _es_suya(request, obj.aula)):
        raise Http404
    return obj


def titulo_de(tipo, obj):
    if tipo == 'muro':
        return obj.titulo
    if tipo == 'publicacion':
        return (obj.texto or obj.nombre_archivo or 'Publicación').strip()[:120]
    return obj.titulo


def se_puede_copiar(tipo, obj):
    if tipo == 'muro' and obj.tipo == 'actividad':
        return bool(obj.pagina) and obj.pagina.tipo == 'html'
    return not (tipo == 'pagina' and obj.tipo != 'html')


def para_todos(tipo, obj):
    """¿Va siempre a toda la clase? (lo que termina como publicación del muro del aula)"""
    if tipo == 'publicacion':
        return True
    if tipo == 'muro':
        return not (obj.tipo == 'actividad' and obj.pagina) and not obj.documento
    return False


def _copiar_archivo(campo_origen, campo_destino, nombre):
    if not campo_origen:
        return False
    with campo_origen.open('rb') as fh:
        campo_destino.save(nombre, ContentFile(fh.read()), save=False)
    return True


def _copiar_de_muro(pub, aula, para, usuario, request):
    """Lo de la comunidad, a una clase: la actividad HTML como actividad interactiva, el recurso de Mis materiales
    como PDF en Material (con el encabezado de su autor) y lo demás como publicación del muro del aula."""
    from .models import Material
    from chat.views_colegas import nombre_de
    autor = nombre_de(pub.autor)
    if pub.tipo == 'actividad' and pub.pagina:
        nuevo, url = copiar('pagina', pub.pagina, aula, para, usuario)
        if not nuevo.descripcion:
            nuevo.descripcion = f'De {autor}'[:300]
            nuevo.save(update_fields=['descripcion'])
        return nuevo, url
    if pub.documento:
        from materiales import exportar
        from materiales.models import EncabezadoDocente
        doc = pub.documento
        datos = exportar.pdf(request, doc, colegio=None, encabezado=EncabezadoDocente.objects.filter(usuario=doc.propietario).first(),
                             docente=nombre_de(doc.propietario))
        nombre = exportar.nombre_archivo(doc, 'pdf')
        m = Material(aula=aula, titulo=pub.titulo[:150], unidad='Comunidad docente', tipo='archivo', para=para,
                     descripcion=f'{doc.get_tipo_display()} · de {autor}'[:300])
        m.archivo.save(nombre, ContentFile(datos), save=False)
        m.nombre_archivo = nombre[:150]
        m.save()
        return m, reverse('aula:material', args=[aula.pk])
    texto = f'{pub.titulo}\n\n{pub.texto}'.strip() + f'\n\n(Compartido de la comunidad docente: {autor})'
    nuevo = Publicacion(aula=aula, autor=usuario, texto=texto[:5000], enlace=pub.enlace or '')
    if pub.imagen and _copiar_archivo(pub.imagen, nuevo.archivo, 'imagen.jpg'):
        nuevo.nombre_archivo = 'imagen.jpg'
    nuevo.save()
    return nuevo, reverse('aula:muro', args=[aula.pk])


def copiar(tipo, obj, aula, para, usuario, request=None):
    """Una copia en la clase «aula» para «para» (vacío = toda la clase). Devuelve (nuevo, url)."""
    if tipo == 'muro':
        return _copiar_de_muro(obj, aula, para, usuario, request)
    if tipo == 'actividad':
        nuevo = Actividad(aula=aula, titulo=obj.titulo, descripcion=obj.descripcion, enlace=obj.enlace,
                          califica=obj.califica, para=para)
        if _copiar_archivo(obj.archivo, nuevo.archivo, obj.nombre_archivo or 'actividad.html'):
            nuevo.nombre_archivo = obj.nombre_archivo
        nuevo.save()
        return nuevo, reverse('aula:actividad', args=[aula.pk, nuevo.pk])
    if tipo == 'invertida':
        nuevo = ClaseInvertida.objects.create(aula=aula, titulo=obj.titulo, video=obj.video, instrucciones=obj.instrucciones,
                                              texto_preguntas=obj.texto_preguntas, preguntas=obj.preguntas, para=para)
        return nuevo, reverse('aula:invertida', args=[aula.pk, nuevo.pk])
    if tipo == 'publicacion':
        nuevo = Publicacion(aula=aula, autor=usuario, texto=obj.texto, enlace=obj.enlace)
        if _copiar_archivo(obj.archivo, nuevo.archivo, obj.nombre_archivo or 'archivo'):
            nuevo.nombre_archivo = obj.nombre_archivo
        nuevo.save()
        return nuevo, reverse('aula:muro', args=[aula.pk])
    if tipo == 'pagina':
        from django.core.files.storage import default_storage
        nuevo = Actividad(aula=aula, titulo=obj.titulo[:60], descripcion=(obj.descripcion or '')[:300], para=para)
        with default_storage.open(obj.ruta_contenido, 'rb') as fh:
            nuevo.archivo.save('actividad.html', ContentFile(fh.read()), save=False)
        nuevo.nombre_archivo = f'{obj.titulo[:140]}.html'
        nuevo.save()
        return nuevo, reverse('aula:actividad', args=[aula.pk, nuevo.pk])
    raise Http404


def leer_destino(request, con_para=True):
    """(aula, para, error) del formulario «Con una de mis clases». Las publicaciones del muro van a toda la clase."""
    aula = next((x for x in mis_aulas(request) if str(x.pk) == (request.POST.get('aula') or '')), None)
    if aula is None:
        return None, [], 'Escoja una de sus clases.'
    if not con_para:
        return aula, [], ''
    para, error = logica.leer_para(request, aula)
    return aula, para, error
