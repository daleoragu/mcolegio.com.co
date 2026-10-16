"""Códigos del SIMAT (Ministerio de Educación).

Tomados del manual de usuario del SIMAT. Si el SIMAT de su secretaría usa otro
código para algo, se corrige en «Configuración SIMAT → Códigos» sin tocar el
programa.
"""
import re
import unicodedata

TIPO_DOCUMENTO = [
    ('1', 'Cédula de ciudadanía'), ('2', 'Tarjeta de identidad'), ('3', 'Cédula de extranjería'),
    ('5', 'Registro civil de nacimiento'), ('6', 'NIP'), ('7', 'NUIP'),
    ('8', 'Número asignado por la Secretaría de Educación'), ('9', 'Certificado cabildo'),
]
# Tipo de la ficha del estudiante -> código SIMAT
TIPO_DESDE_FICHA = {'CC': '1', 'TI': '2', 'CE': '3', 'RC': '5', 'OT': '8'}
FICHA_DESDE_TIPO = {'1': 'CC', '2': 'TI', '3': 'CE', '5': 'RC', '6': 'RC', '7': 'RC', '8': 'OT', '9': 'OT'}

GENERO = [('F', 'Femenino'), ('M', 'Masculino')]
ESTRATO = [('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('9', 'No aplica')]
ZONA = [('1', 'Urbana'), ('2', 'Rural')]
VULNERABILIDAD = [('9', 'No aplica'), ('1', 'En situación de desplazamiento'),
                  ('2', 'Desvinculado de grupos armados'), ('3', 'Hijo de adultos desmovilizados')]
DISCAPACIDAD = [
    ('99', 'No aplica'), ('1', 'Sordera profunda'), ('2', 'Hipoacusia o baja audición'), ('3', 'Baja visión'),
    ('4', 'Ceguera'), ('5', 'Parálisis cerebral'), ('6', 'Lesión neuromuscular'), ('7', 'Autismo'),
    ('8', 'Deficiencia cognitiva'), ('9', 'Síndrome de Down'), ('10', 'Múltiple'),
]
# Categoría del PIAR -> código de discapacidad (se puede corregir en la configuración)
DISCAPACIDAD_DESDE_PIAR = {
    'FISICA': '6', 'AUDITIVA_LSC': '1', 'AUDITIVA_CAST': '2', 'VISUAL_BAJA': '3', 'VISUAL_CEGUERA': '4',
    'SORDOCEGUERA': '10', 'INTELECTUAL': '8', 'PSICOSOCIAL': '99', 'TEA': '7', 'SISTEMICA': '99',
    'MULTIPLE': '10', 'TALENTO': '99', 'APRENDIZAJE': '99', 'PROCESO': '99',
}
CAPACIDAD = [('9', 'No aplica'), ('1', 'Superdotado'), ('2', 'Talento científico'), ('3', 'Talento tecnológico'),
             ('4', 'Talento subjetivo')]
JORNADA = [('1', 'Completa'), ('2', 'Mañana'), ('3', 'Tarde'), ('4', 'Nocturna'), ('5', 'Fin de semana'),
           ('6', 'Única')]
# Jornada de la sede (notas.Sede.JORNADAS) -> código
JORNADA_DESDE_SEDE = {'MANANA': '2', 'TARDE': '3', 'NOCHE': '4', 'FIN_SEMANA': '5', 'UNICA': '6'}
CARACTER = [('0', 'No aplica'), ('1', 'Académico'), ('2', 'Técnico')]
ESPECIALIDAD = [('00', 'No aplica'), ('05', 'Académico'), ('06', 'Industrial'), ('07', 'Otro'), ('08', 'Comercial'),
                ('09', 'Pedagógico'), ('10', 'Agropecuario'), ('16', 'Promoción social')]
METODOLOGIA = [('1', 'Educación tradicional'), ('2', 'Escuela nueva'), ('3', 'Postprimaria'),
               ('4', 'Telesecundaria'), ('5', 'SER'), ('7', 'SAT'), ('8', 'Etnoeducación'),
               ('9', 'Aceleración del aprendizaje'), ('10', 'Jóvenes y adultos (Decreto 3011)'),
               ('11', 'Preescolar escolarizado'), ('12', 'Preescolar no escolarizado'), ('13', 'SAT presencial')]
SITUACION_ANTERIOR = [('', 'Calcular sola'), ('0', 'No estudió el año anterior'), ('1', 'Aprobó'), ('2', 'Reprobó'),
                      ('8', 'No culminó estudios')]
FUENTE_RECURSOS = [('1', 'SGP (Sistema General de Participaciones)'), ('2', 'FNR (Fondo Nacional de Regalías)'),
                   ('3', 'Recursos adicionales MEN'), ('4', 'Otros recursos de la Nación'), ('5', 'Recursos propios')]
SI_NO = [('N', 'No'), ('S', 'Sí')]

# Grados: los de la plataforma ya usan el mismo número que el SIMAT (-2 a 11).
GRADO_POR_NOMBRE = {
    'PREJARDIN': -2, 'PRE_JARDIN': -2, 'JARDIN': -1, 'JARDIN_I': -1, 'KINDER': -1, 'TRANSICION': 0,
    'JARDIN_II': 0, 'GRADO_0': 0, 'PRIMERO': 1, 'SEGUNDO': 2, 'TERCERO': 3, 'CUARTO': 4, 'QUINTO': 5,
    'SEXTO': 6, 'SEPTIMO': 7, 'OCTAVO': 8, 'NOVENO': 9, 'DECIMO': 10, 'ONCE': 11, 'UNDECIMO': 11,
}


def normalizar(texto):
    """«Primer Apellido» -> PRIMER_APELLIDO, sin tildes ni signos."""
    t = unicodedata.normalize('NFKD', str(texto or '')).encode('ascii', 'ignore').decode()
    return re.sub(r'_+', '_', re.sub(r'[^A-Z0-9]', '_', t.upper())).strip('_')


def nombres(lista):
    return dict(lista)
