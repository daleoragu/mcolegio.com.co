"""PuntoExacto · informes en PDF al estilo ICFES (por estudiante y general) y pruebas unidas (varios exámenes)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone

from . import graficas_informe as GR
from . import informes as INF
from .models import PruebaUnida
from .views import _cuenta_de, _examen_o_404, _examenes_visibles, personal_requerido


# ----------------------------------------------------------------------------- piezas comunes
def _pdf(request, plantilla, ctx, nombre):
    from weasyprint import HTML
    html = render_to_string(plantilla, ctx, request=request)
    r = HttpResponse(HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(), content_type='application/pdf')
    r['Content-Disposition'] = f'inline; filename="{nombre}.pdf"'
    return r


def _luz(hexa):
    """Luminancia relativa (0 oscuro · 1 claro) de un color #rrggbb."""
    try:
        r, g, b = (int(hexa.lstrip('#')[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except (ValueError, AttributeError):
        return 0
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _hex(c):
    """'#abc' o '#aabbcc' -> '#aabbcc' en minúsculas; cualquier otra cosa -> ''."""
    c = (c or '').strip().lower()
    if len(c) == 4 and c.startswith('#'):
        c = '#' + ''.join(ch * 2 for ch in c[1:])
    if len(c) == 7 and c.startswith('#') and all(ch in '0123456789abcdef' for ch in c[1:]):
        return c
    return ''


def _saturacion(c):
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return max(r, g, b) - min(r, g, b)


def _distintos(a, b):
    """Dos colores que se ven distintos (no dos tonos casi iguales)."""
    return sum(abs(int(a[i:i + 2], 16) - int(b[i:i + 2], 16)) for i in (1, 3, 5)) > 90


def _texto_sobre(fondo, preferido=''):
    """El texto que se lee sobre ese fondo: el que puso el colegio si contrasta; si no, blanco o casi negro."""
    oscuro = _luz(fondo) < 0.55
    pref = _hex(preferido)
    if pref and abs(_luz(pref) - _luz(fondo)) > 0.45:
        return pref
    return '#ffffff' if oscuro else '#0f172a'


# Los valores con que nace un colegio: si siguen así, el colegio no escogió ese color.
_POR_DEFECTO = {'color_primario': '#0d6efd', 'color_secundario': '#6c757d', 'color_topbar': '#343a40',
                'color_footer': '#212529'}


def _tema(request):
    """Los colores institucionales del colegio, tomados de la paleta de su portal, y su escudo.

    Principal: el fondo de la barra superior (el color más fuerte del colegio), con el texto de la barra.
    Segundo color: el primero que el colegio sí escogió entre el primario del portal, el secundario y el pie de
    página, que tenga color (no un gris) y se distinga del principal. En el plan individual, los de Mi Salón Virtual.
    """
    col = getattr(request, 'colegio', None)
    primario, texto, secundario, logo = '#1e3a8a', '#ffffff', '#f59e0b', ''
    if col:
        barra = _hex(col.color_topbar)
        if barra and _luz(barra) <= 0.75:
            primario, texto = barra, _texto_sobre(barra, col.color_topbar_texto)
        else:
            # Barra blanca o muy clara: el primario del portal hace de principal.
            p = _hex(col.color_primario)
            if p and _luz(p) <= 0.75:
                primario, texto = p, _texto_sobre(p, col.color_texto_primario)
        propios = []
        for campo in ('color_primario', 'color_secundario', 'color_footer'):
            v = _hex(getattr(col, campo, ''))
            if v and v != _POR_DEFECTO[campo] and _luz(v) <= 0.85 and _saturacion(v) > 0.18:
                propios.append(v)
        icono = _hex(col.color_iconos_topbar)
        if icono and _luz(icono) <= 0.85:
            propios.append(icono)
        otros = [c for c in propios if c != primario and _distintos(c, primario)]
        secundario = otros[0] if otros else primario
        if col.logo_izquierdo:
            try:
                import base64
                import mimetypes
                with col.logo_izquierdo.open('rb') as f:
                    tipo = mimetypes.guess_type(col.logo_izquierdo.name)[0] or 'image/png'
                    logo = f'data:{tipo};base64,{base64.b64encode(f.read()).decode()}'
            except Exception:
                logo = ''
    encabezado, rutas = None, {}
    if not col and getattr(request, 'user', None) is not None and request.user.is_authenticated:
        # Docente sin colegio: el color, el logo y las líneas de «Mi encabezado».
        from materiales.models import EncabezadoDocente
        encabezado = EncabezadoDocente.objects.filter(usuario=request.user).first()
        if encabezado is not None:
            c = _hex(encabezado.color)
            if c and _luz(c) <= 0.75:
                primario, texto = c, _texto_sobre(c)
            secundario = primario          # un solo color: el que el docente escogió para sus documentos
            for campo in ('logo', 'logo2'):
                rutas[campo] = _datos_de_imagen(getattr(encabezado, campo, None))
            logo = rutas.get('logo') or rutas.get('logo2') or ''
            if not encabezado.tiene_algo:
                encabezado = None
    if _luz(primario) > 0.75:             # un primario muy claro no sirve de fondo para títulos: se usa el azul
        primario, texto = '#1e3a8a', '#ffffff'
    return {'primario': primario, 'texto': texto, 'secundario': secundario, 'acento': secundario,
            'acento_txt': secundario if _luz(secundario) < 0.55 else primario, 'logo': logo,
            'encabezado': encabezado, 'rutas': rutas}


def _datos_de_imagen(archivo):
    """Un archivo de imagen guardado -> data: URI (WeasyPrint no puede leer el almacenamiento privado)."""
    if not archivo:
        return ''
    try:
        import base64
        import mimetypes
        with archivo.open('rb') as f:
            tipo = mimetypes.guess_type(archivo.name)[0] or 'image/png'
            return f'data:{tipo};base64,{base64.b64encode(f.read()).decode()}'
    except Exception:
        return ''


def _institucion(request):
    col = getattr(request, 'colegio', None)
    if col:
        return col.nombre
    cuenta = _cuenta_de(request)
    if not cuenta:
        return ''
    return (cuenta.institucion or '').strip() or request.user.get_full_name() or request.user.username


def _ctx_general(request, datos):
    globales = [p['global'] for p in datos['personas']]
    preguntas = sorted(datos['preguntas'], key=lambda q: q['pct'])
    tema = _tema(request)
    c = tema['primario']
    return {'d': datos, 'r': datos['resumen'], 'institucion': _institucion(request), 'hoy': timezone.localdate(), 'tema': tema,
            'g_areas': GR.barras_areas(datos['areas'], color=c, color2=tema['secundario']), 'g_niveles': GR.niveles_areas(datos['areas'], color=c),
            'g_hist': GR.histograma(globales, color=c), 'dificiles': preguntas[:10], 'faciles': preguntas[::-1][:5],
            'revisar': [q for q in datos['preguntas'] if q['disc'] is not None and q['disc'] < 0],
            'que_dice': INF.QUE_DICE_NIVEL, 'varias_areas': len(datos['areas']) > 1}


def _ctx_estudiante(datos, clave, tema):
    e = INF.de_estudiante(datos, clave)
    if e is None:
        raise Http404
    c = tema['primario']
    e['g_areas'] = GR.barras_areas(e['areas'], [a['puntaje'] for a in e['areas']], color=c, color2=tema['secundario'])
    e['g_percentil'] = GR.barra_percentil(e['persona']['percentil'], c)
    for a in e['areas']:
        a['g_percentil'] = GR.barra_percentil(a['percentil'], c)
        a['g_escalera'] = GR.escalera(a['niveles_nombres'], a['escalon'], c)
    e['recomendaciones'] = INF.recomendaciones(e['areas'])
    return e


def _fechas(datos):
    f = sorted(ex.fecha for ex in datos['examenes'] if ex.fecha)
    return {'fecha_desde': f[0] if f else None, 'fecha_hasta': f[-1] if f else None}


def grupos_de(hojas):
    """Los grados y los cursos que hay entre estas hojas (para ofrecer un informe de cada uno)."""
    def clave_orden(t):
        num = ''.join(ch for ch in t if ch.isdigit())
        return (int(num) if num else 999, t)
    grados = sorted({INF.grado_de(h) for h in hojas}, key=clave_orden)
    cursos = sorted({INF.curso_de(h) for h in hojas}, key=clave_orden)
    return grados, cursos


def _filtro(request):
    """?grado= o ?curso=: (función para INF.construir, texto para el título)."""
    grado, curso = request.GET.get('grado'), request.GET.get('curso')
    if grado:
        return (lambda h: INF.grado_de(h) == grado), grado
    if curso:
        return (lambda h: INF.curso_de(h) == curso), f'Curso {curso}'
    return None, ''


def _nombre_archivo(t):
    return ''.join(ch for ch in t if ch.isalnum() or ch in ' -_.')[:80].strip() or 'informe'


# ----------------------------------------------------------------------------- informes por nota (escala de valoración)
def _por_nota(request):
    return request.GET.get('estilo') == 'nota' or request.POST.get('estilo') == 'nota'


def _ctx_nota(request, datos, **extra):
    return {'d': datos, 'institucion': _institucion(request), 'hoy': timezone.localdate(), 'tema': _tema(request), **extra}


def _html_nota_cursos(request, examen, incluir=None, titulo=None):
    from . import informes_nota as INFN
    d = INFN.construir(examen, incluir=incluir, titulo=titulo)
    return d, render_to_string('puntoexacto/informe_nota_cursos_pdf.html', _ctx_nota(request, d), request=request)


def _html_nota_estudiantes(request, examen, incluir=None, claves=None):
    from . import informes_nota as INFN
    d = INFN.construir(examen, incluir=incluir)
    lista = d['filas'] if claves is None else [f for k in claves for f in d['filas'] if f['clave'] == k]
    return d, lista, render_to_string('puntoexacto/informe_nota_estudiantes_pdf.html', _ctx_nota(request, d, lista=lista),
                                      request=request)


def _pdf_html(html, request, nombre):
    from weasyprint import HTML
    r = HttpResponse(HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(), content_type='application/pdf')
    r['Content-Disposition'] = f'inline; filename="{nombre}.pdf"'
    return r


# ----------------------------------------------------------------------------- un examen
@login_required
@personal_requerido
def informe_general(request, examen_id):
    examen = _examen_o_404(request, examen_id)
    incluir, sufijo = _filtro(request)
    titulo = f'{examen.titulo} · {sufijo}' if sufijo else examen.titulo
    if _por_nota(request):
        d, html = _html_nota_cursos(request, examen, incluir, titulo)
        if not d['filas']:
            messages.info(request, 'Todavía no hay hojas calificadas para hacer el informe.')
            return redirect('puntoexacto:resultados', examen_id=examen.id)
        return _pdf_html(html, request, f'Informe por nota - {_nombre_archivo(titulo)}')
    datos = INF.construir([examen], titulo, incluir=incluir)
    if not datos['personas']:
        messages.info(request, 'Todavía no hay hojas calificadas para hacer el informe.')
        return redirect('puntoexacto:resultados', examen_id=examen.id)
    return _pdf(request, 'puntoexacto/informe_general_pdf.html', _ctx_general(request, datos), f'Informe general - {_nombre_archivo(titulo)}')


@login_required
@personal_requerido
def informe_estudiante(request, examen_id, clave):
    examen = _examen_o_404(request, examen_id)
    if _por_nota(request):
        d, lista, html = _html_nota_estudiantes(request, examen, claves=[clave])
        if not lista:
            raise Http404
        return _pdf_html(html, request, f'Informe por nota - {_nombre_archivo(lista[0]["nombre"])}')
    datos = INF.construir([examen])
    tema = _tema(request)
    e = _ctx_estudiante(datos, clave, tema)
    return _pdf(request, 'puntoexacto/informe_estudiantes_pdf.html',
                {'d': datos, 'lista': [e], 'institucion': _institucion(request), 'hoy': timezone.localdate(), 'tema': tema, **_fechas(datos)},
                f'Informe - {_nombre_archivo(e["persona"]["nombre"])}')


@login_required
@personal_requerido
def informes_estudiantes(request, examen_id):
    """Los informes de todos los estudiantes en un solo PDF (uno tras otro), para imprimir o repartir."""
    examen = _examen_o_404(request, examen_id)
    curso = request.GET.get('curso')
    if _por_nota(request):
        d, lista, html = _html_nota_estudiantes(request, examen, incluir=(lambda h: INF.curso_de(h) == curso) if curso else None)
        if not lista:
            messages.info(request, 'Todavía no hay hojas calificadas para hacer los informes.')
            return redirect('puntoexacto:resultados', examen_id=examen.id)
        return _pdf_html(html, request, f'Informes por nota - {_nombre_archivo(examen.titulo)}')
    datos = INF.construir([examen])
    tema = _tema(request)
    lista = [_ctx_estudiante(datos, p['clave'], tema) for p in sorted(datos['personas'], key=lambda p: (p['curso'], p['nombre']))
             if not curso or p['curso'] == curso]
    if not lista:
        messages.info(request, 'Todavía no hay hojas calificadas para hacer los informes.')
        return redirect('puntoexacto:resultados', examen_id=examen.id)
    return _pdf(request, 'puntoexacto/informe_estudiantes_pdf.html',
                {'d': datos, 'lista': lista, 'institucion': _institucion(request), 'hoy': timezone.localdate(), 'tema': tema, **_fechas(datos)},
                f'Informes por estudiante - {_nombre_archivo(examen.titulo)}')


# ----------------------------------------------------------------------------- hojas calificadas
def _respuesta_pdf(pdf, nombre):
    r = HttpResponse(pdf, content_type='application/pdf')
    r['Content-Disposition'] = f'inline; filename="{nombre}.pdf"'
    return r


@login_required
@personal_requerido
def hoja_calificada(request, examen_id, hoja_id):
    """La hoja de un estudiante con lo bueno, lo malo y la nota, para devolvérsela."""
    from . import hoja_calificada as HC
    examen = _examen_o_404(request, examen_id)
    hoja = get_object_or_404(examen.hojas.select_related('estudiante__user', 'estudiante__curso__sede'), pk=hoja_id)
    pdf = HC.pdf_calificadas(examen, [hoja])
    if pdf is None:
        raise Http404
    return _respuesta_pdf(pdf, f'Hoja calificada - {_nombre_archivo(hoja.nombre)}')


@login_required
@personal_requerido
def hojas_calificadas(request, examen_id):
    """Las hojas calificadas de todos (una por página), en el orden en que se reparten; ?curso= para un salón."""
    from . import hoja_calificada as HC
    from . import hojas as hojas_mod
    examen = _examen_o_404(request, examen_id)
    lista = list(examen.hojas.filter(estado__in=('calificada', 'revisar'))
                 .select_related('estudiante__user', 'estudiante__curso__sede')
                 .order_by('estudiante__curso__grado', 'estudiante__curso__nombre',
                           'estudiante__user__last_name', 'estudiante__user__first_name', 'nombre_libre', 'identificador'))
    curso = request.GET.get('curso')
    if curso:
        lista = [h for h in lista if (getattr(hojas_mod.curso_de_hoja(h), 'nombre', '') == curso)]
    pdf = HC.pdf_calificadas(examen, lista)
    if pdf is None:
        messages.info(request, 'Todavía no hay hojas calificadas.')
        return redirect('puntoexacto:resultados', examen_id=examen.id)
    return _respuesta_pdf(pdf, f'Hojas calificadas - {_nombre_archivo(examen.titulo)}')


@login_required
@personal_requerido
def en_vivo(request, examen_id):
    """Cómo va el grupo mientras se califica: promedio, acierto por pregunta y las más falladas (JSON)."""
    from collections import Counter
    examen = _examen_o_404(request, examen_id)
    hojas = list(examen.hojas.filter(estado__in=('calificada', 'revisar')).prefetch_related('respuestas'))
    preguntas = list(examen.preguntas.filter(anulada=False, es_control=False).order_by('numero'))
    n = len(hojas)
    filas = []
    for p in preguntas:
        marcas = [next((r.marcada for r in h.respuestas.all() if r.pregunta_id == p.id), '') for h in hojas]
        bien = sum(1 for m in marcas if p.acierta(m))
        otras = Counter(m for m in marcas if m and not p.acierta(m) and m != '?' and len(m) == 1)
        dis = otras.most_common(1)[0] if otras else None
        filas.append({'numero': p.numero, 'pct': round(100 * bien / n) if n else 0, 'correcta': p.rotulo(p.correcta),
                      'distractor': [p.rotulo(dis[0]), round(100 * dis[1] / n)] if dis else None})
    notas = [float(h.nota) for h in hojas if h.nota is not None]
    return JsonResponse({
        'n': n, 'total': examen.hojas.exclude(estado='ausente').count(),
        'promedio': round(sum(notas) / len(notas), 2) if notas else None,
        'preguntas': filas,
        'falladas': sorted([f for f in filas if n], key=lambda f: f['pct'])[:5],
    })


# ----------------------------------------------------------------------------- todo de una vez (ZIP)
# Con un curso completo (o varios) el ZIP tardaba más de lo que el servidor deja a una petición y se cortaba.
# El navegador pide primero el «plan» (qué partes hay) y luego cada parte por separado: el total, cada grado,
# cada curso y los estudiantes de a POR_LOTE. Cada parte tarda unos segundos; el navegador las une en un ZIP.
POR_LOTE = 12


def _plan_zip(tipos, grados, cursos, ids_estudiantes, nombre_zip):
    partes = []
    if tipos & {'general', 'excel'}:
        partes.append({'que': 'general'})
    for t, valores in (('grados', grados), ('cursos', cursos)):
        if t in tipos:
            partes += [{'que': t, 'valor': v} for v in valores]
    if tipos & {'informes', 'hojas'}:
        for i in range(0, len(ids_estudiantes), POR_LOTE):
            partes.append({'que': 'estudiantes', 'lote': ids_estudiantes[i:i + POR_LOTE], 'n': i // POR_LOTE + 1})
    return JsonResponse({'ok': True, 'partes': partes, 'nombre': nombre_zip, 'lotes': sum(1 for x in partes if x['que'] == 'estudiantes')})


def _parte_pedida(request):
    import json
    try:
        parte = json.loads(request.POST.get('parte') or 'null')
    except ValueError:
        return None
    if not isinstance(parte, dict) or parte.get('que') not in ('general', 'grados', 'cursos', 'estudiantes'):
        return None
    return parte


def _respuesta_zip(contenido, nombre):
    r = HttpResponse(contenido, content_type='application/zip')
    r['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return r


def _nombre_unico(nombre, usados):
    base, n = _nombre_archivo(nombre) or 'estudiante', 2
    final = base
    while final.lower() in usados:
        final = f'{base} ({n})'
        n += 1
    usados.add(final.lower())
    return final


@login_required
@personal_requerido
def descargar_informes(request, examen_id):
    """Los informes escogidos de los estudiantes escogidos, en un solo ZIP.

    tipos: general (el total de los escogidos), grados y cursos (un informe general de cada uno),
           informes (uno por estudiante), hojas (hoja calificada), excel.
    modo: «separado» (un PDF por estudiante, en carpetas) o «junto» (un PDF por tipo con todos).
    Los informes de todos se arman en una sola pasada de WeasyPrint y luego se cortan por estudiante:
    armarlos uno por uno tardaba demasiado con un curso completo.
    """
    examen = _examen_o_404(request, examen_id)
    if request.method != 'POST':
        return redirect('puntoexacto:resultados', examen_id=examen.id)
    tipos = set(request.POST.getlist('tipos'))
    separado = request.POST.get('modo', 'separado') != 'junto'
    ids = {int(x) for x in request.POST.getlist('hojas') if x.isdigit()}
    hojas = [h for h in examen.hojas.filter(estado__in=('calificada', 'revisar'))
             .select_related('estudiante__user', 'estudiante__curso__sede')
             .order_by('estudiante__curso__grado', 'estudiante__curso__nombre', 'estudiante__user__last_name',
                       'estudiante__user__first_name', 'nombre_libre', 'identificador') if h.id in ids]
    if not tipos or (not hojas and tipos - {'excel'}):
        messages.warning(request, 'Escoja qué descargar y al menos un estudiante con hoja calificada.')
        return redirect('puntoexacto:resultados', examen_id=examen.id)

    escogidas = {h.id for h in hojas}
    nombre_zip = f'Informes - {_nombre_archivo(examen.titulo)}.zip'
    if request.POST.get('plan') == '1':
        grados, cursos = grupos_de(hojas)
        return _plan_zip(tipos, grados, cursos, [h.id for h in hojas], nombre_zip)
    parte, sufijo, del_lote = _parte_pedida(request), '', hojas
    if parte and parte['que'] == 'estudiantes':
        lote = {int(x) for x in parte.get('lote') or [] if str(x).isdigit()}
        del_lote = [h for h in hojas if h.id in lote]
        sufijo = f' (parte {int(parte.get("n") or 1)})'
    contenido = _armar_zip(request, [examen], examen.titulo, None, lambda h: h.id in escogidas,
                           [INF._clave_persona(h) for h in del_lote], {examen.id: del_lote}, tipos, separado,
                           por_nota=_por_nota(request), solo=parte, sufijo=sufijo)
    return _respuesta_zip(contenido, nombre_zip)


def _paginas_por_estudiante(doc):
    """[(n, páginas)]: cada estudiante empieza en la página con su ancla «est-N»."""
    grupos, actual, numero = [], None, None
    for pagina in doc.pages:
        nums = [int(a[4:]) for a in pagina.anchors if a.startswith('est-') and a[4:].isdigit()]
        nuevo = max(nums) if nums else None
        if nuevo is not None and nuevo != numero:
            numero, actual = nuevo, []
            grupos.append((nuevo, actual))
        if actual is not None:
            actual.append(pagina)
    return grupos


def _armar_zip(request, examenes, titulo, areas, incluir, claves, hojas_por_examen, tipos, separado, por_nota=False,
               solo=None, sufijo=''):
    """El ZIP de informes, para un examen o para una prueba unida (varios exámenes).

    incluir: hoja -> bool (los escogidos). claves: las personas escogidas, en el orden de los informes.
    hojas_por_examen: {examen.id: [hojas escogidas]} para las hojas calificadas.
    solo: una PARTE del ZIP (lo pide el navegador por partes y las une): {'que': 'general'} (el total y el Excel),
          {'que': 'grados'|'cursos', 'valor': v} (el informe de ese grado o curso) o {'que': 'estudiantes'} (los
          informes y hojas de las personas de «claves» / «hojas_por_examen», que ya vienen recortadas al lote).
    sufijo: se pone al nombre de los PDF «todos juntos» de un lote, para que no se pisen al unir las partes.
    """
    def quiere(t):
        if t not in tipos:
            return False
        if solo is None:
            return True
        return {'general': 'general', 'excel': 'general', 'grados': 'grados', 'cursos': 'cursos',
                'informes': 'estudiantes', 'hojas': 'estudiantes'}[t] == solo.get('que')

    import io
    import zipfile

    from pypdf import PdfReader, PdfWriter
    from weasyprint import HTML

    from . import hoja_calificada as HC
    from .views import exportar

    varios = len(examenes) > 1
    por_nota = por_nota and not varios           # el informe por nota es de un examen solo (sin unir)
    buf = io.BytesIO()
    zf = zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED)
    datos = None
    if (quiere('general') or quiere('informes')) and not por_nota:
        datos = INF.construir(examenes, titulo, areas, incluir=incluir)

    def general(d, archivo):
        html = render_to_string('puntoexacto/informe_general_pdf.html', _ctx_general(request, d), request=request)
        zf.writestr(archivo, HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf())

    def escribir_pdf(html, archivo):
        zf.writestr(archivo, HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf())

    if por_nota:
        examen = examenes[0]
        if quiere('general'):
            d, html = _html_nota_cursos(request, examen, incluir, titulo)
            if d['filas']:
                escribir_pdf(html, 'Informe por nota (total).pdf')
    elif quiere('general') and datos and datos['personas']:
        general(datos, 'Informe general (total).pdf')
    # Un informe general por grado y por curso, con solo los escogidos de cada uno.
    todas = [h for hs in hojas_por_examen.values() for h in hs]
    grados, cursos = grupos_de(todas)
    for tipo, carpeta, valores, de in (('grados', 'Informes por grado', grados, INF.grado_de),
                                       ('cursos', 'Informes por curso', cursos, INF.curso_de)):
        if not quiere(tipo):
            continue
        for v in valores:
            if solo is not None and solo.get('valor') != v:
                continue
            nombre_v = v if tipo == "grados" else "Curso " + v
            filtro_v = (lambda h, v=v, de=de: incluir(h) and de(h) == v)
            if por_nota:
                d, html = _html_nota_cursos(request, examenes[0], filtro_v, f'{titulo} · {nombre_v}')
                if d['filas']:
                    escribir_pdf(html, f'{carpeta}/{_nombre_archivo(nombre_v)}.pdf')
                continue
            d = INF.construir(examenes, f'{titulo} · {nombre_v}', areas, incluir=filtro_v)
            if d['personas']:
                general(d, f'{carpeta}/{_nombre_archivo(nombre_v)}.pdf')

    if quiere('informes') and por_nota:
        d, lista, html = _html_nota_estudiantes(request, examenes[0], incluir=incluir, claves=list(dict.fromkeys(claves)))
        if lista:
            doc = HTML(string=html, base_url=request.build_absolute_uri('/')).render()
            if not separado:
                zf.writestr(f'Informes por estudiante{sufijo}.pdf', doc.write_pdf())
            else:
                usados = set()
                for n, paginas in _paginas_por_estudiante(doc):
                    zf.writestr(f'Informes por estudiante/{_nombre_unico(lista[n - 1]["nombre"], usados)}.pdf',
                                doc.copy(paginas).write_pdf())

    if quiere('informes') and datos:
        tema = _tema(request)
        lista, vistos = [], set()
        for k in claves:
            if k in vistos or not any(p['clave'] == k for p in datos['personas']):
                continue
            vistos.add(k)
            lista.append(_ctx_estudiante(datos, k, tema))
        if lista:
            html = render_to_string('puntoexacto/informe_estudiantes_pdf.html',
                                    {'d': datos, 'lista': lista, 'institucion': _institucion(request),
                                     'hoy': timezone.localdate(), 'tema': tema, **_fechas(datos)}, request=request)
            doc = HTML(string=html, base_url=request.build_absolute_uri('/')).render()
            if not separado:
                zf.writestr(f'Informes por estudiante{sufijo}.pdf', doc.write_pdf())
            else:
                # Cada estudiante empieza en la página que tiene su ancla «est-N».
                # (el ancla de un estudiante aparece en todas sus páginas: se cambia de grupo cuando cambia el número)
                grupos, actual, numero = [], None, None
                for pagina in doc.pages:
                    nums = [int(a[4:]) for a in pagina.anchors if a.startswith('est-') and a[4:].isdigit()]
                    nuevo = max(nums) if nums else None
                    if nuevo is not None and nuevo != numero:
                        numero, actual = nuevo, []
                        grupos.append((nuevo, actual))
                    if actual is not None:
                        actual.append(pagina)
                usados = set()
                for n, paginas in grupos:
                    e = lista[n - 1]
                    nombre = _nombre_unico(e['persona']['nombre'], usados)
                    zf.writestr(f'Informes por estudiante/{nombre}.pdf', doc.copy(paginas).write_pdf())

    if quiere('hojas'):
        # En una prueba unida, cada estudiante tiene una hoja por examen: van todas juntas en su PDF.
        por_persona, nombres, orden = {}, {}, []
        usados_junto = set()
        for ex in examenes:
            hs = hojas_por_examen.get(ex.id) or []
            pdf = HC.pdf_calificadas(ex, hs) if hs else None
            if not pdf:
                continue
            if not separado:
                nombre = 'Hojas calificadas' + (f' - {_nombre_unico(ex.titulo, usados_junto)}' if varios else '') + sufijo
                zf.writestr(f'{nombre}.pdf', pdf)
                continue
            for pagina, h in zip(PdfReader(io.BytesIO(pdf)).pages, hs):
                k = INF._clave_persona(h)
                if k not in por_persona:
                    por_persona[k], nombres[k] = [], h.nombre
                    orden.append(k)
                por_persona[k].append(pagina)
        usados = set()
        for k in orden:
            w = PdfWriter()
            for pagina in por_persona[k]:
                w.add_page(pagina)
            b = io.BytesIO()
            w.write(b)
            zf.writestr(f'Hojas calificadas/{_nombre_unico(nombres[k], usados)}.pdf', b.getvalue())

    if quiere('excel'):
        usados = set()
        for ex in examenes:
            nombre = f'Resultados - {_nombre_unico(ex.titulo, usados)}.xlsx' if varios else 'Resultados.xlsx'
            zf.writestr(nombre, exportar(request, ex.id).content)
    zf.close()
    return buf.getvalue()


# ----------------------------------------------------------------------------- pruebas unidas
def _unidas_visibles(request):
    col = getattr(request, 'colegio', None)
    if col:
        return PruebaUnida.objects.filter(colegio=col)
    cuenta = _cuenta_de(request)
    return PruebaUnida.objects.filter(cuenta=cuenta) if cuenta else PruebaUnida.objects.none()


def _unida_o_404(request, pk):
    u = get_object_or_404(_unidas_visibles(request), pk=pk)
    visibles = set(_examenes_visibles(request).values_list('id', flat=True))
    examenes = list(u.examenes.all().order_by('fecha', 'id'))
    if any(e.id not in visibles for e in examenes):
        raise Http404          # tiene un examen que este usuario no puede ver
    return u, examenes


@login_required
@personal_requerido
def unidas(request):
    """Lista de pruebas unidas y formulario para unir exámenes."""
    visibles = _examenes_visibles(request).filter(archivado=False).order_by('-fecha')
    if request.method == 'POST':
        ids = [int(x) for x in request.POST.getlist('examenes') if x.isdigit()]
        escogidos = list(visibles.filter(id__in=ids))
        titulo = ' '.join((request.POST.get('titulo') or '').split())[:160]
        if len(escogidos) < 2:
            messages.warning(request, 'Escoja al menos dos exámenes para unirlos.')
        elif not titulo:
            messages.warning(request, 'Póngale un nombre a la prueba (por ejemplo «Simulacro Saber 11 · noviembre»).')
        else:
            u = PruebaUnida.objects.create(titulo=titulo, colegio=getattr(request, 'colegio', None),
                                           cuenta=None if getattr(request, 'colegio', None) else _cuenta_de(request),
                                           creador=request.user)
            u.examenes.set(escogidos)
            messages.success(request, f'Listo: «{titulo}» une {len(escogidos)} exámenes.')
            return redirect('puntoexacto:unida', pk=u.pk)
    return render(request, 'puntoexacto/unidas.html', {'unidas': _unidas_visibles(request).prefetch_related('examenes'),
                                                       'examenes': visibles})


@login_required
@personal_requerido
def unida(request, pk):
    u, examenes = _unida_o_404(request, pk)
    if request.method == 'POST':
        if request.POST.get('accion') == 'eliminar':
            u.delete()
            messages.info(request, 'Prueba unida eliminada (los exámenes no cambian).')
            return redirect('puntoexacto:unidas')
        areas = {}
        for k, v in request.POST.items():
            if k.startswith('area-') and (v in INF.PRUEBAS or v == 'NO'):
                areas[k[5:]] = v
        u.areas = areas
        u.save(update_fields=['areas'])
        messages.success(request, 'Áreas guardadas.')
        return redirect('puntoexacto:unida', pk=u.pk)
    datos = INF.construir(examenes, u.titulo, u.areas)
    todas = [h for p in datos['personas'] for h in p['hojas'].values()]
    grados, cursos = grupos_de(todas)
    return render(request, 'puntoexacto/unida.html', {'u': u, 'examenes': examenes, 'd': datos, 'pruebas': INF.PRUEBAS,
                                                      'grados': grados, 'cursos': cursos})


@login_required
@personal_requerido
def unida_general(request, pk):
    u, examenes = _unida_o_404(request, pk)
    incluir, sufijo = _filtro(request)
    titulo = f'{u.titulo} · {sufijo}' if sufijo else u.titulo
    datos = INF.construir(examenes, titulo, u.areas, incluir=incluir)
    if not datos['personas']:
        messages.info(request, 'Todavía no hay hojas calificadas en estos exámenes.')
        return redirect('puntoexacto:unida', pk=u.pk)
    return _pdf(request, 'puntoexacto/informe_general_pdf.html', _ctx_general(request, datos), f'Informe general - {_nombre_archivo(titulo)}')


@login_required
@personal_requerido
def unida_estudiantes(request, pk, clave=None):
    u, examenes = _unida_o_404(request, pk)
    datos = INF.construir(examenes, u.titulo, u.areas)
    curso = request.GET.get('curso')
    claves = [clave] if clave else [p['clave'] for p in sorted(datos['personas'], key=lambda p: (p['curso'], p['nombre']))
                                    if not curso or p['curso'] == curso]
    tema = _tema(request)
    lista = [_ctx_estudiante(datos, k, tema) for k in claves]
    if not lista:
        messages.info(request, 'Todavía no hay hojas calificadas en estos exámenes.')
        return redirect('puntoexacto:unida', pk=u.pk)
    nombre = lista[0]['persona']['nombre'] if clave else u.titulo
    return _pdf(request, 'puntoexacto/informe_estudiantes_pdf.html',
                {'d': datos, 'lista': lista, 'institucion': _institucion(request), 'hoy': timezone.localdate(), 'tema': tema, **_fechas(datos)},
                f'Informe - {_nombre_archivo(nombre)}')


@login_required
@personal_requerido
def unida_descargar(request, pk):
    """Lo mismo que «Descargar informes» de un examen, para una prueba unida: los estudiantes se escogen por persona
    (cada uno puede tener una hoja en cada examen)."""
    u, examenes = _unida_o_404(request, pk)
    if request.method != 'POST':
        return redirect('puntoexacto:unida', pk=u.pk)
    tipos = set(request.POST.getlist('tipos'))
    separado = request.POST.get('modo', 'separado') != 'junto'
    escogidas = set(request.POST.getlist('personas'))
    orden = ('estudiante__curso__grado', 'estudiante__curso__nombre', 'estudiante__user__last_name',
             'estudiante__user__first_name', 'nombre_libre', 'identificador')
    hojas_por_examen, claves = {}, []
    for ex in examenes:
        hs = [h for h in ex.hojas.filter(estado__in=('calificada', 'revisar'))
              .select_related('estudiante__user', 'estudiante__curso__sede').order_by(*orden)
              if INF._clave_persona(h) in escogidas]
        hojas_por_examen[ex.id] = hs
        for h in hs:
            k = INF._clave_persona(h)
            if k not in claves:
                claves.append(k)
    if not tipos or (not claves and tipos - {'excel'}):
        messages.warning(request, 'Escoja qué descargar y al menos un estudiante.')
        return redirect('puntoexacto:unida', pk=u.pk)
    nombre_zip = f'Informes - {_nombre_archivo(u.titulo)}.zip'
    if request.POST.get('plan') == '1':
        grados, cursos = grupos_de([h for hs in hojas_por_examen.values() for h in hs])
        return _plan_zip(tipos, grados, cursos, claves, nombre_zip)
    parte, sufijo = _parte_pedida(request), ''
    if parte and parte['que'] == 'estudiantes':
        lote = {str(x) for x in parte.get('lote') or []}
        claves = [k for k in claves if k in lote]
        hojas_por_examen = {e: [h for h in hs if INF._clave_persona(h) in lote] for e, hs in hojas_por_examen.items()}
        sufijo = f' (parte {int(parte.get("n") or 1)})'
    contenido = _armar_zip(request, examenes, u.titulo, u.areas, lambda h: INF._clave_persona(h) in escogidas,
                           claves, hojas_por_examen, tipos, separado, solo=parte, sufijo=sufijo)
    return _respuesta_zip(contenido, nombre_zip)
