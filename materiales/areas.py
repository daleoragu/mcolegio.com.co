"""Las áreas de los materiales: una lista fija (las áreas obligatorias de la Ley 115, art. 23 y 31) y, dentro de cada una,
la asignatura que el docente escriba con su propio nombre (Danzas, Música, Química, Geometría…).

Así el filtro agrupa aunque cada profe escriba distinto: «artistica», «Artes» y «Danzas» quedan en Educación Artística,
y «Danzas» se conserva como asignatura.
"""
import re
import unicodedata

# (nombre corto que se guarda, nombre oficial que se muestra en la lista)
AREAS = [
    ('Matemáticas', 'Matemáticas'),
    ('Lenguaje', 'Humanidades: Lengua Castellana'),
    ('Inglés', 'Humanidades: Idiomas Extranjeros'),
    ('Ciencias Naturales', 'Ciencias Naturales y Educación Ambiental'),
    ('Ciencias Sociales', 'Ciencias Sociales, Historia, Geografía, Constitución y Democracia'),
    ('Educación Artística', 'Educación Artística y Cultural'),
    ('Ética y Valores', 'Educación Ética y en Valores Humanos'),
    ('Educación Física', 'Educación Física, Recreación y Deportes'),
    ('Educación Religiosa', 'Educación Religiosa'),
    ('Tecnología e Informática', 'Tecnología e Informática'),
    ('Filosofía', 'Filosofía (media)'),
    ('Ciencias Económicas y Políticas', 'Ciencias Económicas y Políticas (media)'),
    ('Preescolar', 'Preescolar: dimensiones del desarrollo'),
    ('Otra', 'Otra área'),
]
NOMBRES = [a for a, _ in AREAS]

# Palabras que delatan el área (sin tildes, en minúscula). Se prueban primero las frases más largas.
_CLAVES = {
    'Matemáticas': ['matematica', 'matematicas', 'geometria', 'estadistica', 'aritmetica', 'algebra', 'trigonometria', 'calculo',
                    'precalculo', 'pre calculo', 'pensamiento matematico', 'razonamiento matematico'],
    'Lenguaje': ['lenguaje', 'castellano', 'espanol', 'lengua castellana', 'lectura', 'lectoescritura', 'comunicacion', 'literatura',
                 'lectura critica', 'plan lector', 'humanidades', 'lengua materna', 'produccion textual', 'oralidad'],
    'Inglés': ['ingles', 'english', 'idioma extranjero', 'idiomas extranjeros', 'idiomas', 'frances', 'bilinguismo', 'segunda lengua'],
    'Ciencias Naturales': ['naturales', 'ciencias naturales', 'biologia', 'quimica', 'fisica', 'educacion ambiental', 'ambiental',
                           'ciencias', 'ecologia', 'ciencias naturales y educacion ambiental', 'laboratorio'],
    'Ciencias Sociales': ['sociales', 'ciencias sociales', 'historia', 'geografia', 'democracia', 'catedra de la paz', 'constitucion',
                          'competencias ciudadanas', 'catedra afrocolombiana', 'estudios afrocolombianos', 'civica', 'urbanidad'],
    'Educación Artística': ['artistica', 'artisticas', 'artes', 'arte', 'danza', 'danzas', 'musica', 'teatro', 'dibujo', 'pintura',
                            'manualidades', 'plastica', 'artes plasticas', 'educacion artistica', 'educacion artistica y cultural',
                            'cultura', 'folclor', 'folclore', 'canto', 'coro', 'banda'],
    'Ética y Valores': ['etica', 'valores', 'etica y valores', 'convivencia', 'proyecto de vida', 'educacion etica'],
    'Educación Física': ['educacion fisica', 'edufisica', 'deporte', 'deportes', 'recreacion', 'actividad fisica', 'futbol',
                         'atletismo', 'gimnasia'],
    'Educación Religiosa': ['religion', 'religiosa', 'educacion religiosa', 'catequesis', 'formacion religiosa'],
    'Tecnología e Informática': ['tecnologia', 'informatica', 'sistemas', 'computacion', 'tecnologia e informatica', 'robotica',
                                 'programacion', 'tic', 'ofimatica'],
    'Filosofía': ['filosofia', 'logica'],
    'Ciencias Económicas y Políticas': ['economia', 'politica', 'ciencias politicas', 'ciencias economicas', 'ciencias economicas y politicas',
                                        'emprendimiento'],
    'Preescolar': ['preescolar', 'transicion', 'jardin', 'dimension', 'dimensiones', 'prejardin', 'dimension comunicativa',
                   'dimension cognitiva', 'dimension corporal', 'dimension estetica', 'dimension socioafectiva'],
}
# Palabras que solo repiten el nombre del área: no se guardan como asignatura
_GENERICOS = {'matematica', 'matematicas', 'lenguaje', 'castellano', 'lengua castellana', 'espanol', 'humanidades', 'ingles',
              'idiomas', 'idioma extranjero', 'naturales', 'ciencias naturales', 'ciencias', 'ciencias naturales y educacion ambiental',
              'sociales', 'ciencias sociales', 'artistica', 'artisticas', 'artes', 'arte', 'educacion artistica',
              'educacion artistica y cultural', 'etica', 'valores', 'etica y valores', 'educacion etica', 'educacion fisica', 'edufisica',
              'religion', 'religiosa', 'educacion religiosa', 'tecnologia', 'informatica', 'tecnologia e informatica',
              'filosofia', 'preescolar', 'otra', 'otra area', 'ciencias economicas y politicas'}
_FRASES = sorted(((frase, area) for area, frases in _CLAVES.items() for frase in frases), key=lambda t: -len(t[0]))


def normal(texto):
    t = unicodedata.normalize('NFKD', texto or '').encode('ascii', 'ignore').decode().lower()
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', t).split())


_POR_NORMAL = {normal(a): a for a in NOMBRES}
_POR_NORMAL.update({normal(oficial): a for a, oficial in AREAS})


def clasificar(texto):
    """De lo que escribió el docente saca (área de la lista, asignatura). Si no se entiende: ('', texto)."""
    original = ' '.join((texto or '').split())[:80]
    t = normal(original)
    if not t:
        return '', ''
    if t in _POR_NORMAL:
        return _POR_NORMAL[t], ''
    palabras = f' {t} '
    for frase, area in _FRASES:
        if f' {frase} ' in palabras:
            return area, ('' if t in _GENERICOS else original)
    return '', original


def de_la_lista(area):
    """El área tal como se guarda: una de la lista (o vacía si no corresponde a ninguna)."""
    if area in NOMBRES:
        return area
    return clasificar(area)[0]
