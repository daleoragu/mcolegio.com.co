"""Del cuadernillo a PuntoExacto: el examen con su clave, listo para imprimir las hojas y calificar con la cámara."""
import datetime

from django.db import transaction

from . import bloques as B

LETRAS = 'ABCDEFGH'


def preguntas_para_hoja(contenido):
    """[(número, opciones, letra correcta, control)] o un error en palabras.

    En la hoja de burbujas solo caben preguntas de selección con una respuesta (y verdadero o falso,
    que va como A = Verdadero, B = Falso)."""
    salida, problemas, n = [], [], 0
    for b in contenido.get('bloques', []):
        if b.get('tipo') != 'pregunta':
            continue
        n += 1
        modo = b.get('modo')
        if modo == 'vf':
            salida.append((n, 2, 'A' if b.get('valor') else 'B', bool(b.get('control'))))
        elif modo == 'unica':
            opciones = len(b.get('opciones') or [])
            if opciones < 2:
                problemas.append(f'la {n} tiene menos de dos opciones')
            elif b.get('correcta') is None:
                problemas.append(f'la {n} no tiene marcada la respuesta correcta')
            else:
                salida.append((n, min(opciones, 8), LETRAS[b['correcta']], bool(b.get('control'))))
        else:
            problemas.append(f'la {n} es de tipo «{B.MODOS_PREGUNTA.get(modo, modo)}», que no va en la hoja de burbujas')
    if not salida and not problemas:
        problemas.append('el cuadernillo no tiene preguntas')
    return salida, problemas


@transaction.atomic
def sincronizar(doc, request, asignacion=None, grupo=None, periodo=None):
    """Crea (o actualiza) el examen de PuntoExacto del documento. Devuelve (examen, error)."""
    from puntoexacto import calificacion as calif
    from puntoexacto.models import Examen, Pregunta
    contenido = B.limpiar(doc.contenido, B.imagenes_usadas(doc.contenido))
    lista, problemas = preguntas_para_hoja(contenido)
    if problemas:
        return None, 'Revise las preguntas: ' + '; '.join(problemas[:6]) + '.'
    maximo = max(o for _, o, _, _ in lista)
    examen = doc.examen
    if examen is None:
        examen = Examen(titulo=doc.titulo[:160], fecha=datetime.date.today())
        colegio = getattr(request, 'colegio', None)
        if colegio is not None:
            from notas.models import Docente
            from puntoexacto.forms import escala_del_colegio
            examen.colegio = colegio
            examen.docente = Docente.objects.filter(user=request.user, colegio=colegio).first()
            examen.asignacion = asignacion
            examen.periodo = periodo
            escala = escala_del_colegio(colegio)
            if escala:
                examen.nota_minima, examen.nota_maxima = escala
        else:
            from aula.logica import escala_docente
            examen.cuenta = getattr(request.user, 'cuenta_salon', None)
            examen.grupo = grupo
            escala = escala_docente(request.user)
            examen.nota_minima, examen.nota_maxima = escala[0][1], escala[-1][2]
    examen.titulo = doc.titulo[:160]
    examen.numero_preguntas = len(lista)
    examen.numero_opciones = maximo
    examen.save()
    existentes = {p.numero: p for p in examen.preguntas.all()}
    for numero, opciones, letra, control in lista:
        p = existentes.pop(numero, None) or Pregunta(examen=examen, numero=numero)
        p.correcta = letra
        p.es_control = control
        p.numero_opciones = opciones if opciones != maximo else None
        p.save()
    for sobrante in existentes.values():
        sobrante.delete()
    calif.calificar_examen(examen)
    if doc.examen_id != examen.pk:
        doc.examen = examen
        doc.save(update_fields=['examen'])
    return examen, ''
