"""Arma los documentos semilla (guía + taller por DBA) y los guarda como borradores de un docente.

Las gráficas se dibujan con el Graficador y quedan como imágenes editables (Imagen.grafica), igual que si el docente
las hubiera hecho en el editor.
"""
import io

from django.core.files.base import ContentFile

from ..dba import catalogo as K
from . import banco, base, matematicas_6, matematicas_7

MODULOS = {6: matematicas_6, 7: matematicas_7}


def unidades(grado):
    """[(dba del catálogo con «codigo», unidad)] en orden de DBA."""
    grado = int(grado)
    salida = []
    for n, u in sorted(MODULOS[grado].unidades().items()):
        codigo = f'MAT-{grado}-{n}'
        d = K.buscar(codigo)
        if d is None:
            raise ValueError(f'{codigo} no está en el catálogo')
        salida.append((dict(d, codigo=codigo), u))
    return salida


def documentos(grado):
    """[{titulo, tipo, dba, bloques}] del grado: primero la guía y luego el taller de cada DBA."""
    salida = []
    for d, u in unidades(grado):
        guia = base.guia(d, u['tema'], u['objetivo'], u['explora'], u['aprende'], u['recuerda'], u['practica'])
        olimpiada = banco.bloques(grado, d['n'])
        preguntas = list(u['taller'])
        if olimpiada:
            preguntas += [base.seccion('Preguntas tipo olimpiada', 'Marca la respuesta correcta.'), *olimpiada]
        taller = base.taller(d, u['tema'], preguntas)
        salida.append({'titulo': u['tema'][:150], 'tipo': 'guia_momentos', 'dba': d, 'tema': u['tema'], 'bloques': guia})
        salida.append({'titulo': f'Taller · {u["tema"]}'[:150], 'tipo': 'taller', 'dba': d, 'tema': u['tema'],
                       'bloques': taller})
    return salida


def _imagen_grafica(usuario, b):
    from .. import graficas as G
    from ..models import Imagen
    from PIL import Image as PILImage
    spec = G.limpiar(b['grafica'])
    datos, _, errores = G.dibujar(spec, 'png', dpi=200)
    if errores:
        raise ValueError(f'gráfica con errores: {errores}')
    ancho, alto = PILImage.open(io.BytesIO(datos)).size
    img = Imagen(propietario=usuario, ancho=ancho, alto=alto, peso=len(datos), grafica=spec)
    img.archivo.save('grafica.png', ContentFile(datos), save=False)
    img.save()
    return {'id': b['id'], 'tipo': 'imagen', 'imagen': img.pk, 'ancho': b['ancho'], 'pie': b['pie'],
            'alinear': 'centro', 'ajuste': 'linea'}


def guardar(usuario, grado, publicar=False, colegio=None):
    """Crea los borradores (y, si publicar, los materiales del banco libre). Devuelve los Documentos creados."""
    from .. import bloques as B
    from .. import calificar as C
    from ..models import Documento, MaterialCompartido
    creados = []
    for item in documentos(grado):
        bloques = [_imagen_grafica(usuario, b) if b['tipo'] == '_grafica' else b for b in item['bloques']]
        imagenes = {b['imagen'] for b in bloques if b['tipo'] == 'imagen'}
        contenido = B.limpiar({'bloques': bloques}, imagenes)
        d = item['dba']
        doc = Documento.objects.create(propietario=usuario, colegio=colegio, titulo=item['titulo'], tipo=item['tipo'],
                                       area='Matemáticas', grado=f'{grado}.º', contenido=contenido)
        creados.append(doc)
        if publicar:
            MaterialCompartido.objects.create(
                documento=doc, autor=usuario, alcance='libre', estado='publicado', titulo=doc.titulo, tipo=doc.tipo,
                area=doc.area, grado=doc.grado, contenido=contenido, tema=item['tema'][:120],
                dba_codigo=d['codigo'], dba=K.etiqueta(d['codigo']),
                descripcion=f'Material semilla de mcolegio alrededor del DBA {d["n"]} de Matemáticas {grado}.º.',
                preguntas=len([b for b in C.preguntas(contenido) if b.get('modo') != 'hoja']))
    return creados
