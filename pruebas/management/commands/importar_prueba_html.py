# pruebas/management/commands/importar_prueba_html.py
"""
Importa una prueba desde los archivos HTML autónomos generados antes de la
plataforma (los que llevan dentro `const PRUEBAS = {...}, FIGS = {...}`).

Las preguntas pasan a la base de datos y las imágenes en base64 se suben al
bucket de Spaces como archivos reales.

Uso:
    python manage.py importar_prueba_html "ruta/al/archivo.html" \
        --colegio general-santander --codigo MAT7-2026
"""
import base64
import json
import re
import unicodedata

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from notas.models import Colegio
from pruebas.models import Prueba, Pregunta, Opcion, LETRAS

AREAS_POR_PALABRA = {
    'matematica': 'MAT', 'matematicas': 'MAT',
    'lenguaje': 'LEN', 'lectura': 'LEN', 'espanol': 'LEN',
    'ciencias': 'CIE', 'naturales': 'CIE',
    'sociales': 'SOC',
    'ingles': 'ING',
}

GRADOS_POR_PALABRA = {
    'primero': 1, 'segundo': 2, 'tercero': 3, 'cuarto': 4, 'quinto': 5,
    'sexto': 6, 'septimo': 7, 'octavo': 8, 'noveno': 9, 'decimo': 10,
    'undecimo': 11, 'once': 11,
}

EXT_POR_MIME = {
    'image/png': '.png', 'image/jpeg': '.jpg', 'image/jpg': '.jpg',
    'image/gif': '.gif', 'image/webp': '.webp', 'image/svg+xml': '.svg',
}


def sin_tildes(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto or '')
        if unicodedata.category(c) != 'Mn'
    ).lower()


def extraer_objeto_js(fuente, nombre):
    """Devuelve el texto del objeto/array JS asignado a `nombre`.

    Recorre el texto contando llaves y corchetes, ignorando los que aparecen
    dentro de cadenas, para encontrar dónde termina la estructura.
    """
    patron = re.compile(r'\b' + re.escape(nombre) + r'\s*=\s*([\{\[])')
    m = patron.search(fuente)
    if not m:
        return None

    inicio = m.start(1)
    pares = {'{': '}', '[': ']'}
    pila = [pares[fuente[inicio]]]
    i = inicio + 1
    en_cadena = None
    escapado = False

    while i < len(fuente) and pila:
        c = fuente[i]
        if en_cadena:
            if escapado:
                escapado = False
            elif c == '\\':
                escapado = True
            elif c == en_cadena:
                en_cadena = None
        elif c in '"\'':
            en_cadena = c
        elif c in '{[':
            pila.append(pares[c])
        elif c in '}]':
            if c != pila[-1]:
                raise CommandError(f'El objeto {nombre} está mal formado en el HTML.')
            pila.pop()
        i += 1

    if pila:
        raise CommandError(f'No se encontró el final del objeto {nombre}.')
    return fuente[inicio:i]


def objeto_js_simple_a_dict(texto):
    """Convierte {NV:'Numérico', GM:'Geométrico'} en un dict de Python."""
    if not texto:
        return {}
    resultado = {}
    for clave, valor in re.findall(r"([A-Za-z_][\w]*)\s*:\s*'([^']*)'", texto):
        resultado[clave] = valor
    for clave, valor in re.findall(r'"([^"]+)"\s*:\s*"([^"]*)"', texto):
        resultado[clave] = valor
    return resultado


def guardar_data_uri(campo_archivo, data_uri, nombre_base):
    """Decodifica un data:image/...;base64,... y lo guarda en el storage."""
    m = re.match(r'data:([^;,]+)(;base64)?,(.*)', data_uri or '', re.DOTALL)
    if not m:
        return False
    mime, es_base64, carga = m.group(1), m.group(2), m.group(3)
    try:
        binario = base64.b64decode(carga) if es_base64 else carga.encode('utf-8')
    except Exception:
        return False

    nombre = nombre_base
    if '.' not in nombre:
        nombre += EXT_POR_MIME.get(mime.lower(), '.png')
    campo_archivo.save(nombre, ContentFile(binario), save=False)
    return True


class Command(BaseCommand):
    help = 'Importa una prueba desde un archivo HTML autónomo al módulo de pruebas.'

    def add_arguments(self, parser):
        parser.add_argument('archivo', help='Ruta del archivo .html')
        parser.add_argument('--colegio', required=True, help='Slug del colegio')
        parser.add_argument('--codigo', help='Código de acceso. Si se omite se genera.')
        parser.add_argument('--titulo', help='Título. Por defecto, el <title> del HTML.')
        parser.add_argument('--area', choices=[c for c, _ in Prueba.AREA_CHOICES])
        parser.add_argument('--grado', type=int)
        parser.add_argument('--sede', default='Sede Principal')
        parser.add_argument(
            '--reemplazar', action='store_true',
            help='Si ya existe una prueba con ese código, borra sus preguntas y las vuelve a cargar.',
        )

    def handle(self, *args, **op):
        try:
            with open(op['archivo'], encoding='utf-8', errors='replace') as fh:
                html = fh.read()
        except OSError as e:
            raise CommandError(f'No se pudo leer el archivo: {e}')

        try:
            colegio = Colegio.objects.get(slug=op['colegio'])
        except Colegio.DoesNotExist:
            disponibles = ', '.join(Colegio.objects.values_list('slug', flat=True)) or 'ninguno'
            raise CommandError(f'No existe el colegio "{op["colegio"]}". Disponibles: {disponibles}')

        # --- Título, área y grado ---
        m_title = re.search(r'<title>(.*?)</title>', html, re.S)
        titulo_html = (m_title.group(1).strip() if m_title else 'Prueba')
        titulo = op['titulo'] or titulo_html
        plano = sin_tildes(titulo_html)

        area = op['area']
        if not area:
            for palabra, codigo in AREAS_POR_PALABRA.items():
                if palabra in plano:
                    area = codigo
                    break
            area = area or 'OTR'

        grado = op['grado']
        if not grado:
            for palabra, numero in GRADOS_POR_PALABRA.items():
                if palabra in plano:
                    grado = numero
                    break
            if not grado:
                m_num = re.search(r'\b(\d{1,2})\s*°', titulo_html)
                grado = int(m_num.group(1)) if m_num else 0
        if not grado:
            raise CommandError('No se pudo deducir el grado. Indícalo con --grado.')

        codigo = (op['codigo'] or f'{area}{grado}').upper()

        # --- Datos incrustados en el HTML ---
        crudo_pruebas = extraer_objeto_js(html, 'PRUEBAS')
        if not crudo_pruebas:
            raise CommandError('El archivo no contiene un objeto PRUEBAS. ¿Es uno de las pruebas generadas?')
        try:
            datos = json.loads(crudo_pruebas)
        except json.JSONDecodeError as e:
            raise CommandError(f'El objeto PRUEBAS no es JSON válido: {e}')

        figs = {}
        crudo_figs = extraer_objeto_js(html, 'FIGS')
        if crudo_figs:
            try:
                figs = json.loads(crudo_figs)
            except json.JSONDecodeError:
                self.stdout.write(self.style.WARNING('No se pudieron leer las imágenes (FIGS).'))

        nombres_comp = objeto_js_simple_a_dict(extraer_objeto_js(html, 'COMPN'))

        preguntas = []
        for lista in datos.values():
            preguntas.extend(lista)
        if not preguntas:
            raise CommandError('El objeto PRUEBAS está vacío.')

        # --- Carga ---
        with transaction.atomic():
            prueba, creada = Prueba.objects.get_or_create(
                colegio=colegio,
                codigo=codigo,
                defaults={
                    'titulo': titulo,
                    'area': area,
                    'grado': grado,
                    'descripcion': (
                        'Lee todo el enunciado y mira la imagen o la tabla antes de escoger. '
                        'Revisa las cuatro opciones y descarta las que no pueden ser. '
                        'No hay tiempo límite, pero trabaja sin distraerte.'
                    ),
                },
            )

            if not creada:
                if not op['reemplazar']:
                    raise CommandError(
                        f'Ya existe la prueba con código {codigo}. '
                        f'Usa --reemplazar para volver a cargar sus preguntas.'
                    )
                prueba.preguntas.all().delete()
                prueba.titulo, prueba.area, prueba.grado = titulo, area, grado
                prueba.save()

            total_imagenes = 0
            for i, q in enumerate(preguntas, start=1):
                sigla = (q.get('comp') or '').strip()
                obj = Pregunta(
                    prueba=prueba,
                    orden=i,
                    codigo_origen=str(q.get('id') or ''),
                    competencia=sigla,
                    competencia_nombre=nombres_comp.get(sigla, ''),
                    tema=(q.get('tema') or '')[:200],
                    aprendizaje=q.get('apr') or '',
                    enunciado=q.get('enun') or '',
                    pregunta=q.get('preg') or '',
                    tabla=q.get('tabla') or None,
                    clave=(q.get('clave') or 'A').strip().upper()[:1],
                    explicacion=q.get('expl') or '',
                    analisis_error=q.get('err') or '',
                    pct_referencia=q.get('pct'),
                )

                nombre_fig = q.get('fig')
                if nombre_fig and figs.get(nombre_fig):
                    if guardar_data_uri(obj.imagen, figs[nombre_fig], f'{codigo}-p{i}-{nombre_fig}'):
                        total_imagenes += 1

                obj.save()

                ops_fig = q.get('opsFig') or []
                for k, texto in enumerate(q.get('ops') or []):
                    opcion = Opcion(pregunta=obj, letra=LETRAS[k], texto=texto or '')
                    if k < len(ops_fig) and ops_fig[k] and figs.get(ops_fig[k]):
                        if guardar_data_uri(opcion.imagen, figs[ops_fig[k]], f'{codigo}-p{i}-{LETRAS[k]}-{ops_fig[k]}'):
                            total_imagenes += 1
                    opcion.save()

        self.stdout.write(self.style.SUCCESS(
            f'✅ {prueba.titulo}\n'
            f'   Código de acceso : {prueba.codigo}\n'
            f'   Colegio          : {colegio.nombre}\n'
            f'   Preguntas        : {len(preguntas)}\n'
            f'   Imágenes subidas : {total_imagenes}\n'
            f'   Enlace           : /pruebas/{prueba.slug}/'
        ))
