"""Mis materiales: lista, editor, imágenes, exportar a PDF y Word, y publicar en el aula."""
import io
import json
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db.models import Q, Sum
from django.http import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from . import bloques as B
from . import exportar, plantillas
from .models import Documento, EncabezadoDocente, Imagen

MB = 1024 * 1024
MAX_SUBIDA = 10 * MB
MAX_LADO = 1600
MAX_PIXELES = 40_000_000


# ---------------------------------------------------------------------------
# Quién entra
# ---------------------------------------------------------------------------
class Acceso:
    def __init__(self, request):
        self.request = request
        self.colegio = getattr(request, 'colegio', None)
        self.cuenta = None
        self.ok = False
        user = request.user
        if not user.is_authenticated:
            return
        if self.colegio is not None:
            from notas.permisos import es_admin
            from notas.models import Docente
            self.admin = es_admin(request)
            self.ok = self.admin or Docente.objects.filter(user=user, colegio=self.colegio).exists()
        else:
            self.admin = False
            self.cuenta = getattr(user, 'cuenta_salon', None)
            # El dueño de la plataforma entra para armar el banco libre de mcolegio.
            self.ok = self.cuenta is not None or user.is_superuser

    @property
    def base(self):
        return 'notas/base.html' if self.colegio is not None else 'aula/base_salon.html'

    @property
    def es_individual(self):
        return self.colegio is None

    def documentos(self):
        return Documento.objects.filter(propietario=self.request.user, colegio=self.colegio)

    def plantillas_formato(self):
        """Los documentos que sirven de formato: los del colegio, o los que el docente marcó como suyos."""
        if self.colegio is not None:
            return Documento.objects.filter(colegio=self.colegio, plantilla_colegio=True)
        return self.documentos().filter(plantilla_colegio=True)

    def cuota(self):
        return cuota_nube(self.request.user, self.cuenta if self.colegio is None else None)

    def usado(self):
        return usado_nube(self.request.user)

    def encabezado(self):
        if self.colegio is not None:
            return None
        return EncabezadoDocente.objects.filter(usuario=self.request.user).first()

    def docente(self):
        u = self.request.user
        return u.get_full_name() or u.username

    def aulas(self):
        from aula.models import Aula
        if self.colegio is not None:
            return list(Aula.objects.filter(asignacion__docente__user=self.request.user, colegio=self.colegio)
                        .select_related('asignacion__materia', 'asignacion__curso'))
        if self.cuenta is not None:
            return list(Aula.objects.filter(grupo__propietario=self.cuenta).select_related('grupo'))
        return []


def cuota_nube(user, cuenta):
    """Los bytes de nube del docente: los de su plan individual (cuenta) o 2 GB en un colegio, más lo que compró."""
    from .creditos import nube_extra_bytes, plan_de
    if cuenta is not None:
        from salon_digital.models import PLANES
        base = PLANES[cuenta.nivel]['nube_mb'] * MB
        if plan_de(user, None) == 'individual_ia':          # compró el plan con IA con su saldo
            base = max(base, 5 * 1024 * MB)
    else:
        base = 2048 * MB
    return base + nube_extra_bytes(user)


def usado_nube(user):
    """Lo que ocupa: las imágenes de sus materiales y las de sus tableros de clase."""
    from aula.models import ImagenTablero
    return ((Imagen.objects.filter(propietario=user).aggregate(t=Sum('peso'))['t'] or 0)
            + (ImagenTablero.objects.filter(tablero__autor=user).aggregate(t=Sum('peso'))['t'] or 0))


def vista(fn):
    @login_required
    def envoltura(request, *args, **kwargs):
        a = Acceso(request)
        if not a.ok:
            return HttpResponseForbidden('Mis materiales es para los docentes.')
        return fn(request, a, *args, **kwargs)
    envoltura.__name__ = fn.__name__
    return envoltura


def _doc(a, pk):
    return get_object_or_404(a.documentos(), pk=pk)


def _nube_docente(request):
    """Qué nubes del docente (Drive u OneDrive) están configuradas, como en el cuadernillo de PuntoExacto."""
    from puntoexacto.views import _nube_config
    datos = _nube_config(request)
    return {'google': datos['google'], 'onedrive': datos['onedrive']}


def _nube(a):
    usado, cuota = a.usado(), a.cuota()
    return {'usado_mb': round(usado / MB, 1), 'cuota_mb': round(cuota / MB),
            'porcentaje': min(100, round(usado * 100 / cuota)) if cuota else 0}


# ---------------------------------------------------------------------------
# Lista y creación
# ---------------------------------------------------------------------------
MODELOS = ('abp', 'retos', 'caso', 'invertida', 'cooperativo')


@vista
def lista(request, a):
    from .models import Colaborador
    from .views_equipo import nombre
    invitaciones = [(c, nombre(c.documento.propietario)) for c in Colaborador.objects.filter(
        usuario=request.user, estado='pendiente', documento__colegio=a.colegio).select_related('documento__propietario')]
    conmigo = [(c, nombre(c.documento.propietario)) for c in Colaborador.objects.filter(
        usuario=request.user, estado='aceptada', documento__colegio=a.colegio).select_related('documento__propietario')
        .order_by('-documento__actualizado')]
    return render(request, 'materiales/lista.html', {
        'base': a.base, 'acceso': a, 'documentos': a.documentos().prefetch_related('colaboradores'), 'nube': _nube(a),
        'formatos': a.plantillas_formato().select_related('propietario'),
        'tipos': [t for t in Documento.TIPOS if t[0] not in MODELOS and t[0] not in plantillas.FORMATOS],
        'modelos': [t for t in Documento.TIPOS if t[0] in MODELOS],
        'formatos_tipos': [t for t in Documento.TIPOS if t[0] in plantillas.FORMATOS],
        'invitaciones': invitaciones, 'conmigo': conmigo, 'aulas': a.aulas(), **_contexto_ia(request, a)})


@require_POST
@vista
def nuevo(request, a):
    tipo = request.POST.get('tipo') or 'libre'
    if tipo not in dict(Documento.TIPOS):
        tipo = 'libre'
    base = None
    if tipo == 'institucional':
        base = a.plantillas_formato().filter(pk=request.POST.get('base') or 0).first()
        if base is None:
            messages.warning(request, 'Todavía no hay un formato guardado. Arme una guía y márquela como formato.')
            return redirect('materiales:lista')
    from salon_digital.limites import a_planes, cupo_materiales
    if not cupo_materiales(request.user, a.colegio):
        return a_planes(request, 'materiales', 'estandar')
    titulo = (request.POST.get('titulo') or '').strip()[:150] or dict(Documento.TIPOS)[tipo]
    doc = Documento.objects.create(propietario=request.user, colegio=a.colegio, titulo=titulo, tipo=tipo,
                                   area=(request.POST.get('area') or (base.area if base else ''))[:80],
                                   grado=(request.POST.get('grado') or '')[:40],
                                   contenido=_con_mi_color(request.user, plantillas.contenido_inicial(tipo, base), base,
                                                           area=request.POST.get('area') or '', grado=request.POST.get('grado') or ''))
    return redirect('materiales:editor', pk=doc.pk)


def _reglas_color(usuario):
    enc = EncabezadoDocente.objects.filter(usuario=usuario).first()
    return enc.por_area if enc is not None else []


def _con_mi_color(usuario, contenido, base=None, area='', grado=''):
    """Un documento nuevo sale con el color que el docente escogió en «Mi encabezado»: el de su área o grado si
    tiene una regla, o su color general (el formato base manda su propio color)."""
    if base is None:
        enc = EncabezadoDocente.objects.filter(usuario=usuario).first()
        color = enc.color_para(area, grado) if enc is not None else B.COLOR_DEFECTO
        if color != B.COLOR_DEFECTO:
            contenido = dict(contenido)
            contenido['opciones'] = dict(contenido.get('opciones') or {}, color=color)
    return contenido


@require_POST
@vista
def accion(request, a, pk):
    from .views_equipo import doc_equipo
    doc, rol = doc_equipo(a, pk)
    que = request.POST.get('accion')
    # Los colaboradores pueden duplicar (copia propia) y publicar en sus propias aulas; lo demás es del dueño.
    if rol != 'dueno' and que not in ('duplicar', 'publicar', 'ficha', 'enviar'):
        messages.warning(request, 'Esa acción es solo del dueño del material.')
        return redirect('materiales:editor', pk=pk)
    if que == 'eliminar':
        doc.delete()
        messages.info(request, f'«{doc.titulo}» eliminado.')
        return redirect('materiales:lista')
    if que == 'duplicar':
        from salon_digital.limites import a_planes, cupo_materiales
        if not cupo_materiales(request.user, a.colegio):
            return a_planes(request, 'materiales', 'estandar')
        contenido = doc.contenido
        if rol != 'dueno':
            contenido = _copiar_imagenes(request.user, doc)
        copia = Documento.objects.create(propietario=request.user, colegio=a.colegio, titulo=f'{doc.titulo[:140]} (copia)',
                                         tipo=doc.tipo, area=doc.area, grado=doc.grado, periodo=doc.periodo,
                                         contenido=contenido)
        return redirect('materiales:editor', pk=copia.pk)
    if que == 'formato':
        if a.colegio is not None and not a.admin:
            messages.warning(request, 'Solo el rector o el coordinador marcan el formato del colegio.')
        else:
            doc.plantilla_colegio = not doc.plantilla_colegio
            doc.save(update_fields=['plantilla_colegio'])
            messages.success(request, 'Guardado como formato.' if doc.plantilla_colegio else 'Ya no es un formato.')
        return redirect('materiales:lista')
    if que == 'publicar':
        return _publicar(request, a, doc)
    if que == 'enviar':
        return _enviar(request, a, doc)
    if que == 'puntoexacto':
        return _puntoexacto(request, a, doc)
    if que == 'ficha':
        return _asignar_ficha(request, a, doc)
    return redirect('materiales:editor', pk=pk)


def _copiar_imagenes(usuario, doc):
    """Copia propia de las imágenes de otros docentes (para que la copia de un colaborador no dependa de ellas)."""
    import copy
    contenido = copy.deepcopy(doc.contenido)
    ajenas = {i.pk: i for i in Imagen.objects.filter(pk__in=B.imagenes_usadas(contenido)).exclude(propietario=usuario)}
    nuevas = {}
    for pk, img in ajenas.items():
        try:
            with img.archivo.open('rb') as fh:
                datos = fh.read()
        except Exception:
            continue
        n = Imagen(propietario=usuario, ancho=img.ancho, alto=img.alto, peso=img.peso)
        n.archivo.save('imagen' + (os.path.splitext(img.archivo.name)[1] or '.jpg'), ContentFile(datos), save=False)
        n.save()
        nuevas[pk] = n.pk
    for b in contenido.get('bloques', []):
        if b.get('imagen') in nuevas:
            b['imagen'] = nuevas[b['imagen']]
    return contenido


def _asignar_ficha(request, a, doc):
    """Copia el documento como una tarea del aula que el estudiante resuelve en línea."""
    from aula.models import Tarea
    from . import calificar as C
    aulas = {str(x.pk): x for x in a.aulas()}
    aula = aulas.get(request.POST.get('aula') or '')
    if aula is None:
        messages.error(request, 'Escoja una de sus aulas.')
        return redirect('materiales:editor', pk=doc.pk)
    contenido = B.limpiar(doc.contenido, B.imagenes_usadas(doc.contenido))
    if not C.preguntas(contenido):
        messages.error(request, 'El documento no tiene preguntas para resolver.')
        return redirect('materiales:editor', pk=doc.pk)

    def entero(nombre, defecto, minimo, maximo):
        try:
            return max(minimo, min(maximo, int(request.POST.get(nombre) or defecto)))
        except ValueError:
            return defecto
    config = {'modo': 'formativa' if request.POST.get('modo') == 'formativa' else 'puntos',
              'intentos': entero('intentos', 1, 0, 10), 'tiempo': entero('tiempo', 0, 0, 300),
              'mostrar': 'nunca' if request.POST.get('mostrar') == 'nunca' else 'al_terminar',
              'documento': doc.pk}
    t = Tarea.objects.create(aula=aula, titulo=doc.titulo[:60], instrucciones=B.texto_plano(request.POST.get('instrucciones'), 2000),
                             ficha=contenido, ficha_config=config, publicada=False)
    messages.success(request, 'Ficha copiada al aula como tarea. Revise la fecha, el periodo, para quién es '
                              'y márquela como publicada.')
    return redirect('aula:tarea_editar', pk=aula.pk, tid=t.pk)


def _volver(request, defecto):
    v = request.POST.get('volver') or ''
    return redirect(v if v.startswith('/') and not v.startswith('//') else defecto)


def _enviar(request, a, doc):
    """Envía el material a uno o varios grupos: el PDF al Material del aula (si ya estaba, se actualiza) y/o
    una tarea para resolver en línea (queda como borrador para que el docente revise fecha y periodo)."""
    from aula import logica
    from aula.models import Material, Tarea
    from . import calificar as C
    aulas = {str(x.pk): x for x in a.aulas()}
    escogidas = [aulas[k] for k in request.POST.getlist('aula') if k in aulas]
    como = set(request.POST.getlist('como')) & {'pdf', 'tarea'}
    defecto = 'materiales:lista'
    if not escogidas or not como:
        messages.error(request, 'Escoja al menos un grupo y cómo enviarlo (PDF o tarea).')
        return _volver(request, defecto)
    unidad = B.texto_plano(request.POST.get('unidad'), 80) or doc.area or 'Mis materiales'
    hechos = []
    if 'pdf' in como:
        datos = exportar.pdf(request, doc, colegio=a.colegio, encabezado=a.encabezado(), docente=a.docente(),
                             modo=request.POST.get('modo'))
        nombre = exportar.nombre_archivo(doc, 'pdf')
        for aula in escogidas:
            m = Material.objects.filter(aula=aula, titulo=doc.titulo[:150], nombre_archivo=nombre[:150], tipo='archivo').first()
            nuevo = m is None
            if nuevo:
                m = Material(aula=aula, titulo=doc.titulo[:150], tipo='archivo')
            elif m.archivo:
                m.archivo.delete(save=False)
            m.unidad = unidad
            m.descripcion = ' · '.join(x for x in (doc.get_tipo_display(), doc.grado and f'Grado {doc.grado}') if x)[:300]
            m.archivo.save(nombre, ContentFile(datos), save=False)
            m.nombre_archivo = nombre[:150]
            m.save()
            logica.avisar_estudiantes(aula, f'{aula.titulo}: {"nuevo material" if nuevo else "material actualizado"} «{m.titulo}»',
                                      request.build_absolute_uri(f'/aula/{aula.pk}/material/'))
        hechos.append(f'PDF en el Material de {len(escogidas)} grupo(s)')
    if 'tarea' in como:
        contenido = B.limpiar(doc.contenido, B.imagenes_usadas(doc.contenido))
        if not C.preguntas(contenido):
            messages.warning(request, 'No se creó la tarea: el material no tiene preguntas para resolver.')
        else:
            for aula in escogidas:
                Tarea.objects.create(aula=aula, titulo=doc.titulo[:60], ficha=contenido, publicada=False,
                                     ficha_config={'modo': 'puntos', 'intentos': 1, 'tiempo': 0, 'mostrar': 'al_terminar',
                                                   'documento': doc.pk})
            hechos.append(f'tarea en borrador en {len(escogidas)} grupo(s): revise su fecha y periodo y publíquela')
    if hechos:
        messages.success(request, f'«{doc.titulo}» enviado: ' + '; '.join(hechos) + '.')
    return _volver(request, defecto)


def _destinos_examen(a):
    """Asignaturas (colegio) o grupos (plan individual) donde se puede aplicar el examen."""
    if a.colegio is not None:
        from notas.models import AsignacionDocente, PeriodoAcademico
        asignaciones = AsignacionDocente.objects.filter(colegio=a.colegio).select_related('materia', 'curso')
        if not a.admin:
            asignaciones = asignaciones.filter(docente__user=a.request.user)
        periodos = list(PeriodoAcademico.objects.filter(colegio=a.colegio).order_by('-ano_lectivo', 'orden')[:8])
        return {'asignaciones': list(asignaciones.order_by('curso__nombre', 'materia__nombre')), 'periodos': periodos,
                'periodo_activo': next((p for p in periodos if p.esta_activo), None)}
    if a.cuenta is not None:
        return {'grupos': list(a.cuenta.grupos.filter(activo=True).order_by('nombre'))}
    return {}


def _puntoexacto(request, a, doc):
    from . import puntoexacto as pe
    destinos = _destinos_examen(a)
    asignacion = grupo = periodo = None
    if doc.examen_id is None:
        if a.colegio is not None:
            asignacion = next((x for x in destinos['asignaciones'] if str(x.pk) == request.POST.get('asignacion')), None)
            periodo = next((x for x in destinos['periodos'] if str(x.pk) == request.POST.get('periodo')), None)
        else:
            grupo = next((x for x in destinos.get('grupos', []) if str(x.pk) == request.POST.get('grupo')), None)
    examen, error = pe.sincronizar(doc, request, asignacion=asignacion, grupo=grupo, periodo=periodo)
    if error:
        messages.error(request, error)
    else:
        messages.success(request, f'Examen de PuntoExacto listo con {examen.numero_preguntas} preguntas y su clave. '
                                  'Ahora prepare e imprima las hojas de respuesta.')
    return redirect('materiales:editor', pk=doc.pk)


def _publicar(request, a, doc):
    from aula import logica
    from aula.models import Material
    aulas = {str(x.pk): x for x in a.aulas()}
    aula = aulas.get(request.POST.get('aula') or '')
    if aula is None:
        messages.error(request, 'Escoja una de sus aulas.')
        return redirect('materiales:editor', pk=doc.pk)
    datos = exportar.pdf(request, doc, colegio=a.colegio, encabezado=a.encabezado(), docente=a.docente(),
                         modo=request.POST.get('modo'))
    m = Material(aula=aula, titulo=doc.titulo[:150], unidad='Mis materiales', tipo='archivo',
                 descripcion=' · '.join(x for x in (doc.area, doc.grado and f'Grado {doc.grado}') if x)[:300])
    nombre = exportar.nombre_archivo(doc, 'pdf')
    m.archivo.save(nombre, ContentFile(datos), save=False)
    m.nombre_archivo = nombre[:150]
    m.save()
    logica.avisar_estudiantes(aula, f'{aula.titulo}: nuevo material «{m.titulo}»',
                              request.build_absolute_uri(f'/aula/{aula.pk}/material/'))
    messages.success(request, f'Publicado en el material de {aula.titulo}.')
    return redirect('materiales:editor', pk=doc.pk)


# ---------------------------------------------------------------------------
# Editor
# ---------------------------------------------------------------------------
@vista
def editor(request, a, pk):
    from .views_equipo import doc_equipo, nombre
    doc, rol = doc_equipo(a, pk)
    usadas = list(Imagen.objects.filter(propietario_id__in=doc.equipo_ids(), pk__in=B.imagenes_usadas(doc.contenido)))
    imagenes = {i.pk: request.build_absolute_uri(f'/materiales/imagen/{i.pk}/') + (f'?v={i.peso}' if i.grafica else '')
                for i in usadas}
    graficas = {i.pk: i.grafica for i in usadas if i.grafica and i.propietario_id == request.user.pk}
    recortes = {i.pk: dict(i.recorte, url_origen=request.build_absolute_uri(f'/materiales/imagen/{i.recorte["origen"]}/'))
                for i in usadas if i.recorte and i.recorte.get('origen')}
    return render(request, 'materiales/editor.html', {
        'graficas': graficas, 'recortes': recortes,
        'rol': rol, 'solo_ver': rol == 'ver', 'dueno_nombre': nombre(doc.propietario),
        'base': a.base, 'acceso': a, 'doc': doc, 'contenido': doc.contenido, 'imagenes': imagenes,
        'aulas': a.aulas(), 'nube': _nube(a), 'tipos': Documento.TIPOS, 'nube_docente': _nube_docente(request),
        'destinos': _destinos_examen(a), 'modos_pregunta': B.MODOS_PREGUNTA, 'colores': B.COLORES,
        'es_formato': doc.tipo in plantillas.FORMATOS,
        'colores_texto': [('c', 'Color de letra'), ('f', 'Relleno')],
        # (color de letra, color de relleno suave) para las paletas
        'paleta': [('#000000', '#fef08a'), ('#1f3a68', '#bbf7d0'), ('#2563eb', '#bfdbfe'), ('#0f766e', '#99f6e4'),
                   ('#15803d', '#d9f99d'), ('#7c3aed', '#ddd6fe'), ('#be185d', '#fbcfe8'), ('#dc2626', '#fecaca'),
                   ('#ea580c', '#fed7aa'), ('#ca8a04', '#fde68a'), ('#6b7280', '#e5e7eb'), ('#ffffff', '#f1f5f9')],
        'colores_area': _reglas_color(request.user),
        'examen': doc.examen if doc.examen_id else None, **_contexto_ia(request, a, doc)})


def _contexto_ia(request, a, doc=None):
    from . import creditos, ia
    from .models import MaterialCompartido
    datos = {'med': creditos.estado(request.user, a.colegio), 'ia_lista': ia.disponible(),
             'ia_costos': {k: v['creditos'] for k, v in ia.ACCIONES.items()},
             'banco_ia': [(k, v[0]) for k, v in ia.BANCO.items()], 'ajustes_piar': ia.AJUSTES_PIAR,
             'pesos_credito': creditos.PESOS_POR_CREDITO}
    if doc is not None:
        datos['compartidos'] = list(MaterialCompartido.objects.filter(documento=doc))
    return datos


@require_POST
@vista
def guardar(request, a, pk):
    from .views_equipo import doc_equipo, nombre
    doc, rol = doc_equipo(a, pk)
    if rol == 'ver':
        return JsonResponse({'ok': False, 'error': 'Puede ver este material, pero no editarlo.'}, status=403)
    try:
        datos = json.loads(request.body or '{}')
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'Datos dañados.'}, status=400)
    # Otro docente del equipo guardó después de que este abrió su copia: no se le borra lo suyo.
    try:
        base = int(datos.get('version'))
    except (TypeError, ValueError):
        base = None
    if base is not None and base != doc.version and doc.editado_por_id not in (None, request.user.pk):
        return JsonResponse({'ok': False, 'conflicto': True, 'version': doc.version, 'por': nombre(doc.editado_por),
                             'error': f'{nombre(doc.editado_por)} guardó cambios en este material. Recargue para verlos '
                                      'antes de seguir (lo que usted escribió después de la última vez que se guardó '
                                      'podría perderse: cópielo si es largo).'}, status=409)
    validas = set(Imagen.objects.filter(propietario_id__in=doc.equipo_ids()).values_list('pk', flat=True))
    doc.contenido = B.limpiar(datos.get('contenido'), validas)
    doc.titulo = B.texto_plano(datos.get('titulo'), 150) or doc.titulo
    doc.area = B.texto_plano(datos.get('area'), 80)
    doc.grado = B.texto_plano(datos.get('grado'), 40)
    doc.periodo = B.texto_plano(datos.get('periodo'), 40)
    doc.version += 1
    doc.editado_por = request.user
    doc.save()
    fuera = [p for b in doc.contenido['bloques'] if b.get('modo') in ('sopa', 'crucigrama') for p in b.get('fuera') or []]
    aviso = f'No cupieron en la cuadrícula: {", ".join(fuera[:8])}' if fuera else ''
    return JsonResponse({'ok': True, 'guardado': doc.actualizado.isoformat(), 'aviso': aviso, 'version': doc.version})


# ---------------------------------------------------------------------------
# Imágenes
# ---------------------------------------------------------------------------
def preparar_imagen(archivo):
    """(bytes, extensión, ancho, alto) de la imagen reducida a 1600 px; ValueError si no sirve."""
    from PIL import Image, ImageOps
    datos = archivo.read(MAX_SUBIDA + 1)
    if len(datos) > MAX_SUBIDA:
        raise ValueError('La imagen pasa de 10 MB.')
    try:
        im = Image.open(io.BytesIO(datos))
        if im.size[0] * im.size[1] > MAX_PIXELES:
            raise ValueError('La imagen es demasiado grande.')
        im.load()
        im = ImageOps.exif_transpose(im)
    except ValueError:
        raise
    except Exception:
        raise ValueError('Ese archivo no es una imagen.')
    im.thumbnail((MAX_LADO, MAX_LADO * 3))
    transparente = im.mode in ('RGBA', 'LA', 'P') and (im.mode != 'P' or 'transparency' in im.info)
    salida = io.BytesIO()
    if transparente:
        im.convert('RGBA').save(salida, 'PNG', optimize=True)
        ext = '.png'
    else:
        im.convert('RGB').save(salida, 'JPEG', quality=85, optimize=True)
        ext = '.jpg'
    return salida.getvalue(), ext, im.size[0], im.size[1]


@require_POST
@vista
def imagen_subir(request, a):
    archivo = request.FILES.get('imagen')
    if archivo is None:
        return JsonResponse({'ok': False, 'error': 'No llegó ninguna imagen.'}, status=400)
    try:
        datos, ext, ancho, alto = preparar_imagen(archivo)
    except ValueError as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    if a.usado() + len(datos) > a.cuota():
        return JsonResponse({'ok': False, 'error': f'Su nube está llena ({round(a.cuota() / MB)} MB). '
                                                  'Libere espacio o amplíe su plan.'}, status=400)
    img = Imagen(propietario=request.user, ancho=ancho, alto=alto, peso=len(datos))
    img.archivo.save(f'imagen{ext}', ContentFile(datos), save=False)
    img.save()
    return JsonResponse({'ok': True, 'id': img.pk, 'url': request.build_absolute_uri(f'/materiales/imagen/{img.pk}/'),
                         'nube': _nube(a)})


def _imagen_visible(request, a, pk):
    img = get_object_or_404(Imagen, pk=pk)
    if img.propietario_id != request.user.pk:
        # una imagen de otro docente del equipo, puesta en un material que este docente construye con él
        from .views_equipo import accesibles
        if not any(pk in B.imagenes_usadas(d.contenido) for d in accesibles(a).exclude(propietario=request.user)
                   .filter(Q(propietario=img.propietario) | Q(colaboradores__usuario=img.propietario)).distinct()[:200]):
            raise Http404
    return img


@vista
def imagen_ver(request, a, pk):
    return redirect(_imagen_visible(request, a, pk).archivo.url)


@require_POST
@vista
def imagen_recortar(request, a, pk):
    """Recorta (y gira) una imagen: queda una imagen nueva del docente y la original se guarda para volver a recortar
    o restaurarla. Siempre se recorta desde la original, así no se pierde calidad al recortar varias veces.
    POST JSON {x, y, w, h} (fracciones 0..1 de la imagen ya girada) y giro (0, 90, 180, 270)."""
    from PIL import Image as PILImage, ImageOps
    img = _imagen_visible(request, a, pk)
    if img.grafica:
        return JsonResponse({'ok': False, 'error': 'Las gráficas se cambian con «Editar gráfica».'}, status=400)
    origen = img
    if img.recorte and img.recorte.get('origen'):
        origen = Imagen.objects.filter(pk=img.recorte['origen']).first() or img
        if origen.pk != img.pk:
            origen = _imagen_visible(request, a, origen.pk)
    try:
        d = json.loads(request.body or b'{}')
        x, y, w, h = (max(0.0, min(1.0, float(d.get(k, v)))) for k, v in (('x', 0), ('y', 0), ('w', 1), ('h', 1)))
        giro = int(d.get('giro') or 0) % 360
    except (TypeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'Recorte inválido.'}, status=400)
    if giro not in (0, 90, 180, 270):
        giro = 0
    if d.get('restaurar'):
        return JsonResponse({'ok': True, 'id': origen.pk, 'url': request.build_absolute_uri(f'/materiales/imagen/{origen.pk}/'),
                             'recorte': None})
    w, h = min(w, 1 - x), min(h, 1 - y)
    if w < .02 or h < .02:
        return JsonResponse({'ok': False, 'error': 'El recorte es demasiado pequeño.'}, status=400)
    with origen.archivo.open('rb') as f:
        foto = ImageOps.exif_transpose(PILImage.open(f))
        foto.load()
    if giro:
        foto = foto.rotate(-giro, expand=True)          # PIL gira al revés de las agujas del reloj
    W, H = foto.size
    caja = (round(x * W), round(y * H), round((x + w) * W), round((y + h) * H))
    foto = foto.crop(caja)
    salida = io.BytesIO()
    if foto.mode in ('RGBA', 'LA', 'P'):
        foto.save(salida, 'PNG', optimize=True)
        ext = '.png'
    else:
        foto.convert('RGB').save(salida, 'JPEG', quality=88, optimize=True)
        ext = '.jpg'
    datos = salida.getvalue()
    if a.usado() + len(datos) > a.cuota():
        return JsonResponse({'ok': False, 'error': f'Su nube está llena ({round(a.cuota() / MB)} MB).'}, status=400)
    nueva = Imagen(propietario=request.user, ancho=foto.size[0], alto=foto.size[1], peso=len(datos),
                   recorte={'origen': origen.pk, 'x': round(x, 4), 'y': round(y, 4), 'w': round(w, 4), 'h': round(h, 4), 'giro': giro})
    nueva.archivo.save(f'recorte{ext}', ContentFile(datos), save=False)
    nueva.save()
    return JsonResponse({'ok': True, 'id': nueva.pk, 'url': request.build_absolute_uri(f'/materiales/imagen/{nueva.pk}/'),
                         'recorte': dict(nueva.recorte, url_origen=request.build_absolute_uri(f'/materiales/imagen/{origen.pk}/')),
                         'nube': _nube(a)})


# ---------------------------------------------------------------------------
# Exportar
# ---------------------------------------------------------------------------
@xframe_options_sameorigin
@vista
def pdf(request, a, pk):
    from .views_equipo import doc_equipo
    doc, _ = doc_equipo(a, pk)
    respuestas = request.GET.get('respuestas') == '1'
    datos = exportar.pdf(request, doc, colegio=a.colegio, encabezado=a.encabezado(), docente=a.docente(),
                         modo=request.GET.get('modo'), respuestas=respuestas)
    r = HttpResponse(datos, content_type='application/pdf')
    disp = 'attachment' if request.GET.get('descargar') else 'inline'
    r['Content-Disposition'] = f'{disp}; filename="{exportar.nombre_archivo(doc, "pdf")}"'
    return r


@vista
def word(request, a, pk):
    from .views_equipo import doc_equipo
    doc, _ = doc_equipo(a, pk)
    datos = exportar.docx(doc, colegio=a.colegio, encabezado=a.encabezado(), docente=a.docente(),
                          modo=request.GET.get('modo'), respuestas=request.GET.get('respuestas') == '1')
    r = HttpResponse(datos, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    r['Content-Disposition'] = f'attachment; filename="{exportar.nombre_archivo(doc, "docx")}"'
    return r


@vista
def paginas(request, a, pk):
    from .views_equipo import doc_equipo
    doc, _ = doc_equipo(a, pk)
    return JsonResponse(exportar.paginas(request, doc, colegio=a.colegio, encabezado=a.encabezado(),
                                         docente=a.docente()))


# ---------------------------------------------------------------------------
# Encabezado del plan individual
# ---------------------------------------------------------------------------
def _config_encabezado(texto):
    """Valida lo que manda el editor del encabezado (JSON) y devuelve la configuración limpia."""
    try:
        cfg = json.loads(texto or '{}')
    except ValueError:
        cfg = {}
    if not isinstance(cfg, dict):
        cfg = {}
    E = EncabezadoDocente
    lineas = []
    for x in (cfg.get('lineas') or [])[:E.MAX_LINEAS]:
        if isinstance(x, dict) and B.texto_plano(x.get('texto'), 120):
            lineas.append({'texto': B.texto_plano(x.get('texto'), 120), 'negrilla': bool(x.get('negrilla')),
                           'tam': x.get('tam') if x.get('tam') in E.TAMANOS else 'normal'})
    pos = dict(E.POSICIONES)
    pie = cfg.get('pie') if isinstance(cfg.get('pie'), dict) else {}
    alinear = ('centro', 'izquierda', 'derecha')
    return {'lineas': lineas,
            'alinear': cfg.get('alinear') if cfg.get('alinear') in alinear else 'centro',
            'logo_pos': cfg.get('logo_pos') if cfg.get('logo_pos') in pos else 'izquierda',
            'logo2_pos': cfg.get('logo2_pos') if cfg.get('logo2_pos') in pos else 'derecha',
            'borde': bool(cfg.get('borde', True)),
            'color': B.color_valido(cfg.get('color')),
            # Color por área o grado: «Matemáticas» → azul, «Ciencias» → verde… (para los documentos nuevos)
            'por_area': [{'area': B.texto_plano(x.get('area'), 60), 'color': B.color_valido(x.get('color'))}
                         for x in (cfg.get('por_area') or [])[:12] if isinstance(x, dict) and B.texto_plano(x.get('area'), 60)],
            'pie': {'lineas': [B.texto_plano(x, 150) for x in (pie.get('lineas') or [])[:E.MAX_PIE] if B.texto_plano(x, 150)],
                    'alinear': pie.get('alinear') if pie.get('alinear') in alinear else 'centro',
                    'numero': bool(pie.get('numero', True))}}


@vista
def encabezado(request, a):
    if not a.es_individual:
        messages.info(request, 'En el colegio, los documentos llevan el encabezado del colegio '
                               '(el de los boletines). Lo cambia el administrador.')
        return redirect('materiales:lista')
    enc, _ = EncabezadoDocente.objects.get_or_create(usuario=request.user)
    if request.method == 'POST':
        enc.config = _config_encabezado(request.POST.get('config'))
        primeras = [f['texto'] for f in enc.config['lineas']][:3] + ['', '', '']
        enc.linea1, enc.linea2, enc.linea3 = primeras[:3]
        for campo in ('logo', 'logo2'):
            archivo = request.FILES.get(campo)
            if request.POST.get(f'quitar_{campo}') == 'on':
                setattr(enc, campo, '')
            elif archivo:
                try:
                    datos, ext, _, _ = preparar_imagen(archivo)
                    getattr(enc, campo).save(f'{campo}{ext}', ContentFile(datos), save=False)
                except ValueError as e:
                    messages.error(request, str(e))
        enc.save()
        messages.success(request, 'Encabezado y pie de página guardados.')
        if request.POST.get('muestra'):
            return redirect(f"{request.path}?muestra=1")
        return redirect('materiales:encabezado')
    if request.GET.get('muestra'):
        muestra = Documento(propietario=request.user, colegio=None, titulo='Guía de muestra', tipo='guia', area='Área',
                            grado='—', contenido={'bloques': [{'tipo': 'seccion', 'titulo': 'Exploración', 'indicacion': ''},
                                                              {'tipo': 'texto', 'html': '<p>Así se ven el encabezado, el pie '
                                                               'de página y el color de sus documentos.</p>'}],
                                                  'opciones': {'color': enc.color}})
        r = HttpResponse(exportar.pdf(request, muestra, colegio=None, encabezado=enc, docente=a.docente()), content_type='application/pdf')
        r['Content-Disposition'] = 'inline; filename="muestra-encabezado.pdf"'
        return r
    datos = {'lineas': enc.filas, 'alinear': enc.alinear, 'logo_pos': enc.logo_pos, 'logo2_pos': enc.logo2_pos,
             'borde': enc.borde, 'pie': enc.pie, 'color': enc.color, 'por_area': enc.por_area}
    return render(request, 'materiales/encabezado.html', {'base': a.base, 'acceso': a, 'enc': enc, 'datos': datos,
                                                         'posiciones': EncabezadoDocente.POSICIONES, 'colores': B.COLORES})


@vista
def encabezado_logo(request, a, cual):
    """El logo del encabezado del propio docente (para la vista previa)."""
    enc = EncabezadoDocente.objects.filter(usuario=request.user).first()
    archivo = getattr(enc, 'logo2' if cual == '2' else 'logo', None) if enc else None
    if not archivo:
        raise Http404
    import mimetypes
    return HttpResponse(archivo.open('rb').read(), content_type=mimetypes.guess_type(archivo.name)[0] or 'image/jpeg')


@vista
def ecuacion(request, a):
    """La imagen (SVG) de una ecuación para el editor: ?tex=\\frac{1}{2}. Si no se puede dibujar, 422."""
    from . import ecuaciones as E
    r = E.dibujar(request.GET.get('tex', ''))
    if r is None:
        return HttpResponse('No se pudo dibujar', status=422, content_type='text/plain; charset=utf-8')
    datos, ancho, alto, fondo = r
    resp = HttpResponse(datos, content_type='image/svg+xml')
    resp['Cache-Control'] = 'private, max-age=604800'
    resp['X-Alto'] = f'{(alto + 1) / E.TAM:.3f}'
    resp['X-Fondo'] = f'{(fondo + .5) / E.TAM:.3f}'
    return resp


# ---------------------------------------------------------------------------
# Graficador: gráficas de funciones y figuras que se insertan como imagen (y se pueden volver a editar)
# ---------------------------------------------------------------------------
@require_POST
@vista
def grafica_vista(request, a):
    """La vista previa mientras el docente arma la gráfica: el SVG, dónde quedaron los ejes (para ubicar los clics)
    y lo que no se pudo dibujar."""
    from . import graficas as G
    try:
        spec = json.loads(request.body or b'{}').get('grafica')
    except ValueError:
        spec = None
    svg, caja, errores = G.dibujar(spec, 'svg')
    return JsonResponse({'svg': svg.decode('utf-8'), 'caja': caja, 'errores': errores, 'grafica': G.limpiar(spec)})


@require_POST
@vista
def grafica_guardar(request, a):
    """Guarda la gráfica como imagen PNG del docente (nueva, o la misma imagen si la está editando)."""
    from . import graficas as G
    try:
        d = json.loads(request.body or b'{}')
    except ValueError:
        d = {}
    spec = G.limpiar(d.get('grafica'))
    if not spec['elementos']:
        return JsonResponse({'ok': False, 'error': 'La gráfica está vacía: agregue una función, un punto o una figura.'}, status=400)
    datos, _, errores = G.dibujar(spec, 'png', dpi=200)
    img = None
    if d.get('imagen'):
        img = Imagen.objects.filter(pk=d['imagen'], propietario=request.user, grafica__isnull=False).first()
    antes = img.peso if img else 0
    if a.usado() - antes + len(datos) > a.cuota():
        return JsonResponse({'ok': False, 'error': f'Su nube está llena ({round(a.cuota() / MB)} MB).'}, status=400)
    from PIL import Image as PILImage
    ancho, alto = PILImage.open(io.BytesIO(datos)).size
    if img is None:
        img = Imagen(propietario=request.user)
    elif img.archivo:
        img.archivo.delete(save=False)
    img.ancho, img.alto, img.peso, img.grafica = ancho, alto, len(datos), spec
    img.archivo.save('grafica.png', ContentFile(datos), save=False)
    img.save()
    return JsonResponse({'ok': True, 'id': img.pk, 'grafica': spec, 'errores': errores, 'nube': _nube(a),
                         'url': request.build_absolute_uri(f'/materiales/imagen/{img.pk}/') + f'?v={img.peso}'})


@vista
def dba_lista(request, a):
    """Los DBA oficiales de un área y un grado (?area=Matemáticas&grado=6.º) para el selector; si el área no tiene
    DBA (Ética, Artística…), «tiene» viene en falso y se pide la competencia o el desempeño en texto libre."""
    from .dba import catalogo as K
    lista = K.dbas(request.GET.get('area', ''), request.GET.get('grado', ''))
    return JsonResponse({'tiene': bool(K.clave_area(request.GET.get('area', ''))), 'grado': K.grado_num(request.GET.get('grado', '')),
                         'dbas': [{'codigo': d['codigo'], 'n': d['n'], 'enunciado': d['enunciado'], 'evidencias': d['evidencias']}
                                  for d in lista]})
