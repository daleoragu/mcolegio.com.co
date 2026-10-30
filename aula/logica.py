"""Reglas del aula virtual: quién entra, cómo se calcula la nota y cómo pasa a la planilla."""
import io
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from django.db import transaction
from django.utils import timezone

from .models import Aula, Criterio, Entrega, Instrumento, Nivel

UN_DECIMAL = Decimal('0.1')
MAX_ARCHIVO_MB = 10
MAX_FOTOS = 12
NIVELES_POR_DEFECTO = [('BAJO', Decimal('2.0')), ('BÁSICO', Decimal('3.5')), ('ALTO', Decimal('4.3')),
                       ('SUPERIOR', Decimal('5.0'))]


# ---------------------------------------------------------------------------
# Quién está mirando
# ---------------------------------------------------------------------------
@dataclass
class Contexto:
    aula: Aula
    rol: str                       # 'docente' | 'estudiante'
    usuario: object = None
    estudiante: object = None      # notas.Estudiante
    integrante: object = None      # salon_digital.Integrante

    @property
    def es_docente(self):
        return self.rol == 'docente'

    @property
    def nombre(self):
        if self.integrante is not None:
            return self.integrante.completo
        if self.usuario is not None:
            return self.usuario.get_full_name() or self.usuario.username
        return ''

    @property
    def base(self):
        return 'aula/base_salon.html' if self.aula.es_salon else 'notas/base.html'


def contexto(request, aula):
    """El Contexto de quien mira, o None si no tiene que ver con esta aula."""
    user = request.user
    if aula.asignacion_id:
        if getattr(request, 'colegio', None) is None or aula.colegio_id != request.colegio.id:
            return None
        if not user.is_authenticated:
            return None
        from notas.permisos import es_admin
        asig = aula.asignacion
        if (asig.docente_id and asig.docente.user_id == user.id) or es_admin(request):
            return Contexto(aula, 'docente', usuario=user)
        est = getattr(user, 'estudiante', None)
        if est is not None and est.colegio_id == aula.colegio_id and est.curso_id == asig.curso_id and est.is_active:
            return Contexto(aula, 'estudiante', usuario=user, estudiante=est)
        return None
    if aula.grupo_id:
        if user.is_authenticated and aula.grupo.propietario.usuario_id == user.id:
            return Contexto(aula, 'docente', usuario=user)
        from salon_digital import identidad
        from salon_digital.models import Integrante
        datos = identidad.leer(request)
        if datos and datos.get('grupo') == aula.grupo_id:
            integrante = Integrante.objects.filter(pk=datos.get('integrante'), grupo=aula.grupo,
                                                   activo=True).first()
            if integrante:
                return Contexto(aula, 'estudiante', integrante=integrante)
    return None


def aula_de_asignacion(asignacion):
    aula, _ = Aula.objects.get_or_create(asignacion=asignacion, defaults={'colegio': asignacion.colegio})
    return aula


def aula_de_grupo(grupo):
    aula, _ = Aula.objects.get_or_create(grupo=grupo)
    return aula


def estudiantes(aula):
    """Los de la clase: estudiantes del curso o integrantes del grupo, ordenados por apellido."""
    if aula.asignacion_id:
        from notas.models import Estudiante
        return list(Estudiante.objects.filter(curso=aula.asignacion.curso, is_active=True)
                    .select_related('user').order_by('user__last_name', 'user__first_name'))
    if aula.grupo_id:
        return list(aula.grupo.integrantes.filter(activo=True))
    return []


def nombre_de(persona):
    if hasattr(persona, 'completo'):
        return persona.completo
    u = persona.user
    return f'{u.last_name} {u.first_name}'.strip() or u.username


def filtro_persona(persona):
    """{'estudiante': x} o {'integrante': x}, para buscar su entrega."""
    return {'integrante': persona} if hasattr(persona, 'completo') else {'estudiante': persona}


# ---------------------------------------------------------------------------
# Escala de notas
# ---------------------------------------------------------------------------
def rango(aula):
    """(mínima, máxima) de las notas: la escala del colegio, o 1–5 en Salón Digital."""
    if aula.colegio_id:
        from notas.boletin.ponderacion import rango_notas
        return rango_notas(aula.colegio)
    return Decimal('1'), Decimal('5')


def niveles_sugeridos(colegio):
    """Los niveles de la escala del colegio con un valor representativo; si no tiene, los de siempre."""
    if colegio is not None:
        from notas.models import EscalaValoracion
        escala = list(EscalaValoracion.objects.filter(colegio=colegio).order_by('valor_minimo'))
        if len(escala) >= 2:
            salida = []
            for i, e in enumerate(escala):
                if i == len(escala) - 1:
                    valor = e.valor_maximo
                else:
                    valor = ((e.valor_minimo + e.valor_maximo) / 2).quantize(UN_DECIMAL, rounding=ROUND_HALF_UP)
                salida.append((e.nombre_desempeno.upper(), valor))
            return salida
    return list(NIVELES_POR_DEFECTO)


def calcular_nota(instrumento, seleccion, minima, maxima):
    """(nota, completa). Rúbrica: promedio ponderado de los niveles. Lista: % cumplido llevado a la escala."""
    criterios = list(instrumento.criterios.all())
    if not criterios:
        return None, False
    seleccion = seleccion or {}
    if instrumento.tipo == 'lista':
        total = sum(c.peso for c in criterios)
        cumplido = sum(c.peso for c in criterios if seleccion.get(str(c.id)) is True)
        completa = all(str(c.id) in seleccion for c in criterios)
        if total <= 0:
            return None, False
        nota = minima + (maxima - minima) * cumplido / total
        return nota.quantize(UN_DECIMAL, rounding=ROUND_HALF_UP), completa
    niveles = {n.id: n for n in instrumento.niveles.all()}
    suma, pesos = Decimal('0'), Decimal('0')
    for c in criterios:
        nivel = niveles.get(_entero(seleccion.get(str(c.id))))
        if nivel is not None:
            suma += nivel.valor * c.peso
            pesos += c.peso
    if pesos <= 0:
        return None, False
    nota = (suma / pesos).quantize(UN_DECIMAL, rounding=ROUND_HALF_UP)
    nota = max(minima, min(maxima, nota))
    return nota, pesos == sum(c.peso for c in criterios)


def _entero(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def desempeno(aula, nota):
    if nota is None or not aula.colegio_id:
        return ''
    from notas import escalas
    asig = aula.asignacion
    return escalas.de(aula.colegio).desempeno(nota, asig.materia_id, asig.curso.grado)


# ---------------------------------------------------------------------------
# Instrumentos: crear, plantillas e importar
# ---------------------------------------------------------------------------
PLANTILLAS = {
    'guia': ('Guía de trabajo', 'rubrica', [
        'Desarrolla todos los puntos de la guía',
        'Procedimientos claros y correctos',
        'Presentación, orden y letra legible',
        'Entrega a tiempo']),
    'exposicion': ('Exposición oral', 'rubrica', [
        'Dominio del tema',
        'Claridad y orden de las ideas',
        'Material de apoyo',
        'Manejo del tiempo',
        'Responde las preguntas']),
    'laboratorio': ('Informe de laboratorio', 'rubrica', [
        'Planteamiento y objetivos',
        'Procedimiento y toma de datos',
        'Análisis de resultados',
        'Conclusiones',
        'Presentación del informe']),
    'proyecto': ('Proyecto', 'rubrica', [
        'Planeación y cumplimiento de etapas',
        'Calidad del producto final',
        'Trabajo en equipo',
        'Socialización']),
    'escrito': ('Texto escrito o ensayo', 'rubrica', [
        'Idea principal y argumentos',
        'Coherencia y cohesión',
        'Ortografía y redacción',
        'Uso de fuentes']),
    'cuaderno': ('Revisión de cuaderno', 'lista', [
        'Tiene todas las clases',
        'Fecha y título en cada clase',
        'Ejercicios resueltos',
        'Correcciones hechas',
        'Orden y presentación']),
    'grupo': ('Trabajo en grupo (coevaluación)', 'lista', [
        'Aportó ideas',
        'Cumplió con su parte',
        'Escuchó a los compañeros',
        'Llegó a tiempo a los encuentros']),
}

# Descriptores escalonados a partir del criterio, del nivel más bajo al más alto.
GRADACION = ['No lo logra o no lo presenta', 'Lo logra de forma parcial',
             'Lo logra en su mayoría', 'Lo logra por completo y con calidad']


def gradacion(n):
    """n frases de menor a mayor para rellenar los descriptores."""
    if n <= 1:
        return GRADACION[-1:]
    if n == len(GRADACION):
        return list(GRADACION)
    idx = [round(i * (len(GRADACION) - 1) / (n - 1)) for i in range(n)]
    return [GRADACION[i] for i in idx]


@transaction.atomic
def crear_instrumento(propietario, colegio, nombre, tipo, criterios, niveles=None, descriptores=None):
    """criterios: [(nombre, peso)]; niveles: [(nombre, valor)] de menor a mayor;
    descriptores: [[texto por nivel] por criterio] (opcional)."""
    inst = Instrumento.objects.create(propietario=propietario, colegio=colegio, nombre=nombre[:120], tipo=tipo)
    objs_niveles = []
    if tipo == 'rubrica':
        for i, (n, v) in enumerate(niveles or niveles_sugeridos(colegio)):
            objs_niveles.append(Nivel.objects.create(instrumento=inst, nombre=str(n)[:40], valor=Decimal(v), orden=i))
    for i, (n, p) in enumerate(criterios):
        textos = (descriptores[i] if descriptores and i < len(descriptores) else None) or \
            (gradacion(len(objs_niveles)) if objs_niveles else [])
        Criterio.objects.create(
            instrumento=inst, nombre=str(n)[:200], peso=Decimal(p or 1), orden=i,
            descriptores={str(nv.id): (textos[k] if k < len(textos) else '') for k, nv in enumerate(objs_niveles)})
    return inst


def desde_plantilla(propietario, colegio, clave):
    nombre, tipo, criterios = PLANTILLAS[clave]
    return crear_instrumento(propietario, colegio, nombre, tipo, [(c, 1) for c in criterios])


def leer_tabla(texto=None, archivo=None):
    """Filas (lista de listas de texto) de una tabla pegada (RubiStar, Word, Excel) o de un .xlsx."""
    filas = []
    if archivo is not None:
        import openpyxl
        libro = openpyxl.load_workbook(archivo, read_only=True, data_only=True)
        hoja = libro.worksheets[0]
        for fila in hoja.iter_rows(values_only=True):
            celdas = ['' if v is None else str(v).strip() for v in fila]
            if any(celdas):
                filas.append(celdas)
    else:
        for linea in (texto or '').splitlines():
            if not linea.strip():
                continue
            if '\t' in linea:
                celdas = linea.split('\t')
            elif '|' in linea:
                celdas = linea.strip().strip('|').split('|')
            elif ';' in linea:
                celdas = linea.split(';')
            else:
                celdas = [linea]
            filas.append([c.strip() for c in celdas])
    # quitar columnas vacías al final
    ancho = max((len(f) for f in filas), default=0)
    while ancho and all((len(f) < ancho or not f[ancho - 1]) for f in filas):
        ancho -= 1
    return [(f + [''] * ancho)[:ancho] for f in filas]


def _numero(texto):
    try:
        return Decimal(str(texto).replace(',', '.').replace('%', '').strip())
    except Exception:
        return None


def interpretar_tabla(filas, colegio=None):
    """De una tabla a (criterios, niveles, descriptores, tipo) listos para crear_instrumento.

    Primera fila = encabezados: «Criterio» (o «Category» de RubiStar), una columna
    opcional «Peso» o «%», y un encabezado por nivel («4», «3»… o «Superior», «Alto»…).
    Sin columnas de nivel, es una lista de chequeo.
    """
    if not filas:
        raise ValueError('La tabla está vacía.')
    encabezado = [c.strip() for c in filas[0]]
    cuerpo = [f for f in filas[1:] if f and f[0].strip()]
    if not cuerpo:
        raise ValueError('La tabla necesita una fila de encabezados y al menos un criterio.')
    col_peso = next((i for i, h in enumerate(encabezado) if i > 0 and (('peso' in h.lower()) or h.strip() == '%')),
                    None)
    cols_nivel = [i for i in range(1, len(encabezado)) if i != col_peso and encabezado[i]]
    criterios = []
    for f in cuerpo:
        peso = _numero(f[col_peso]) if col_peso is not None else None
        criterios.append((f[0].strip()[:200], peso if peso and peso > 0 else Decimal('1')))
    if not cols_nivel:
        return criterios, None, None, 'lista'

    nombres = [encabezado[i] for i in cols_nivel]
    numeros = [_numero(n) for n in nombres]
    # RubiStar va de mayor a menor (4, 3, 2, 1); la plataforma guarda de menor a mayor.
    if all(n is not None for n in numeros) and numeros[0] > numeros[-1]:
        cols_nivel, nombres, numeros = cols_nivel[::-1], nombres[::-1], numeros[::-1]
    elif all(n is None for n in numeros) and _parece_descendente(nombres):
        cols_nivel, nombres = cols_nivel[::-1], nombres[::-1]
        numeros = [None] * len(nombres)

    sugeridos = niveles_sugeridos(colegio)
    niveles = []
    for k, nombre in enumerate(nombres):
        # Valor: el del nivel de la escala en el mismo puesto (el más bajo con el más bajo).
        pos = round(k * (len(sugeridos) - 1) / max(1, len(nombres) - 1)) if len(nombres) > 1 else len(sugeridos) - 1
        nombre_nivel, valor = sugeridos[pos]
        etiqueta = nombre if numeros[k] is None else nombre_nivel
        niveles.append((etiqueta.upper()[:40], valor))
    descriptores = [[f[i].strip() for i in cols_nivel] for f in cuerpo]
    return criterios, niveles, descriptores, 'rubrica'


def _parece_descendente(nombres):
    orden = ['superior', 'excelente', 'alto', 'bueno', 'básico', 'basico', 'aceptable', 'bajo', 'insuficiente',
             'deficiente']
    pos = [next((i for i, o in enumerate(orden) if o in n.lower()), None) for n in nombres]
    pos = [p for p in pos if p is not None]
    return len(pos) >= 2 and pos[0] < pos[-1]


# ---------------------------------------------------------------------------
# Archivos
# ---------------------------------------------------------------------------
def imagenes_a_pdf(archivos):
    """Las fotos del cuaderno, achicadas, en un solo PDF. Devuelve bytes."""
    from PIL import Image, ImageOps
    paginas = []
    for f in archivos:
        img = Image.open(f)
        img = ImageOps.exif_transpose(img).convert('RGB')
        img.thumbnail((1600, 1600))
        paginas.append(img)
    if not paginas:
        return b''
    salida = io.BytesIO()
    paginas[0].save(salida, format='PDF', save_all=True, append_images=paginas[1:], resolution=150, quality=75)
    return salida.getvalue()


def es_imagen(nombre):
    return (nombre or '').lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.heic', '.gif'))


def muy_grande(archivo):
    return archivo is not None and archivo.size > MAX_ARCHIVO_MB * 1024 * 1024


# ---------------------------------------------------------------------------
# Horario de la clase en vivo
# ---------------------------------------------------------------------------
def horario_de(aula):
    """[{'dia', 'texto', 'hoy', 'ahora'}] de las clases de la asignación en el horario publicado."""
    if not aula.asignacion_id:
        return []
    try:
        from horarios.models import DIAS, Sesion
    except Exception:
        return []
    sesiones = (Sesion.objects.filter(horario__colegio=aula.colegio, horario__estado='PUBLICADO',
                                      asignacion=aula.asignacion)
                .select_related('franja').order_by('dia', 'franja__inicio'))
    nombres = dict(DIAS)
    ahora = timezone.localtime()
    salida = []
    for s in sesiones:
        hoy = s.dia == ahora.isoweekday()
        en_curso = False
        if hoy:
            inicio = ahora.replace(hour=s.franja.inicio.hour, minute=s.franja.inicio.minute, second=0)
            fin = ahora.replace(hour=s.franja.fin.hour, minute=s.franja.fin.minute, second=0)
            en_curso = (inicio - timezone.timedelta(minutes=10)) <= ahora <= fin
        salida.append({'dia': nombres.get(s.dia, ''), 'texto': s.franja.texto, 'hoy': hoy, 'ahora': en_curso})
    return salida


# ---------------------------------------------------------------------------
# Avisos
# ---------------------------------------------------------------------------
def avisar_estudiantes(aula, mensaje, url):
    """Notificación (y push al celular) a los estudiantes del curso. En Salón Digital no hay cuentas."""
    if not aula.asignacion_id:
        return 0
    from notas.models import Notificacion
    avisos = [Notificacion(colegio=aula.colegio, destinatario_id=e.user_id, mensaje=mensaje[:255], url=url,
                           tipo='GENERAL') for e in estudiantes(aula)]
    Notificacion.objects.bulk_create(avisos)
    return len(avisos)


# ---------------------------------------------------------------------------
# Paso a la planilla del colegio
# ---------------------------------------------------------------------------
def componentes_de(aula):
    """[(código, nombre)] de los componentes que cuentan en la asignación."""
    if not aula.asignacion_id:
        return []
    from notas.planillas.columnas import componentes_activos
    return [(c, n) for c, n, _ in componentes_activos(aula.asignacion)]


@transaction.atomic
def pasar_a_planilla(tarea):
    """Copia las notas calificadas de la tarea a su columna en la planilla. Devuelve (pasadas, error)."""
    aula = tarea.aula
    if not aula.asignacion_id:
        return 0, 'Esta aula no tiene planilla del colegio.'
    if not tarea.periodo_id or not tarea.componente:
        return 0, 'Escoja el periodo y el componente de la tarea antes de pasarla a la planilla.'
    if not tarea.periodo.esta_activo:
        return 0, f'El {tarea.periodo} está cerrado: la planilla no recibe notas.'
    from notas.planillas.columnas import (columnas_del_plan, componentes_activos, guardar_plan,
                                          limpiar_columnas, notas_guardadas)
    from notas.planillas.guardar import guardar_estudiante
    asig = aula.asignacion
    activos = [c for c, _, _ in componentes_activos(asig)]
    if tarea.componente not in activos:
        return 0, 'Ese componente no cuenta en esta asignatura.'
    columna = limpiar_columnas([tarea.titulo])[0]

    entregas = [e for e in tarea.entregas.filter(estudiante__isnull=False, nota__isnull=False)
                .select_related('estudiante')]
    if not entregas:
        return 0, 'Todavía no hay entregas calificadas.'

    columnas = columnas_del_plan(asig, tarea.periodo, tarea.componente)
    if columna not in columnas:
        guardar_plan(asig, tarea.periodo, tarea.componente, columnas + [columna])

    minima, maxima = rango(aula)
    pasadas = 0
    for e in entregas:
        por_componente = {}
        for codigo in activos:
            notas = notas_guardadas(asig, tarea.periodo, codigo, [e.estudiante]).get(e.estudiante.id, [])
            if codigo == tarea.componente:
                notas = [(d, v) for d, v in notas if d != columna]
                notas.append((columna, max(minima, min(maxima, e.nota))))
            por_componente[codigo] = notas
        guardar_estudiante(aula.colegio, asig, tarea.periodo, e.estudiante, por_componente)
        pasadas += 1
    tarea.pasada_planilla = timezone.now()
    tarea.save(update_fields=['pasada_planilla'])
    return pasadas, ''


# ---------------------------------------------------------------------------
# Planilla propia (Salón Digital) y resumen de calificaciones
# ---------------------------------------------------------------------------
def tabla_calificaciones(aula):
    """{'tareas': [...], 'filas': [{'nombre', 'notas': [nota|None…], 'promedio'}]}"""
    tareas = list(aula.tareas.filter(publicada=True).order_by('creada'))
    personas = estudiantes(aula)
    clave = 'integrante_id' if aula.es_salon else 'estudiante_id'
    notas = {(getattr(e, clave), e.tarea_id): e.nota
             for e in Entrega.objects.filter(tarea__in=tareas, nota__isnull=False)}
    filas = []
    for p in personas:
        fila = [notas.get((p.id, t.id)) for t in tareas]
        validas = [n for n in fila if n is not None]
        prom = (sum(validas) / len(validas)).quantize(UN_DECIMAL, rounding=ROUND_HALF_UP) if validas else None
        filas.append({'persona': p, 'nombre': nombre_de(p), 'notas': fila, 'promedio': prom})
    return {'tareas': tareas, 'filas': filas}


def excel_calificaciones(aula):
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    datos = tabla_calificaciones(aula)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Calificaciones'
    ws.append([f'{aula.titulo} · {aula.subtitulo}'])
    ws['A1'].font = Font(bold=True, size=13)
    ws.append([])
    ws.append(['N.º', 'Estudiante'] + [t.titulo for t in datos['tareas']] + ['Promedio'])
    for c in ws[3]:
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = PatternFill('solid', start_color='1F3A68')
        c.alignment = Alignment(horizontal='center', wrap_text=True)
    for i, f in enumerate(datos['filas'], 1):
        ws.append([i, f['nombre']] + [float(n) if n is not None else None for n in f['notas']]
                  + [float(f['promedio']) if f['promedio'] is not None else None])
    ws.column_dimensions['B'].width = 36
    salida = io.BytesIO()
    wb.save(salida)
    return salida.getvalue()


def entrega_de(tarea, persona) -> Optional[Entrega]:
    return tarea.entregas.filter(**filtro_persona(persona)).first()
