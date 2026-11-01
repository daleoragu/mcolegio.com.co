"""Arma el .zip de la copia de seguridad de una persona: páginas que se abren en cualquier navegador
(sin la plataforma) y, si la persona quiere, las fotos, notas de voz y adjuntos.

Cada parte va por separado: si una falla, las demás igual quedan en la copia y el error se anota en
el índice. Solo entra lo que la persona puede ver en la plataforma.
"""
import csv
import io
import json
import logging
import os
import shutil
import tempfile
import zipfile
from html import escape

from django.db.models import Q
from django.utils import timezone

log = logging.getLogger('mcolegio.copias')

MAX_MEDIOS = 300 * 1024 * 1024          # más de esto en fotos y audios ya no se agrega (se avisa)

ESTILO = """<style>
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;color:#1d2433;background:#f6f8fb;margin:0;line-height:1.5}
main{max-width:860px;margin:auto;background:#fff;min-height:100vh;padding:18px 22px;box-sizing:border-box}
h1{font-size:1.4rem;color:#1f3a68;margin:.2em 0}h2{font-size:1.1rem;color:#1f3a68;border-bottom:1px solid #e3e7ef;padding-bottom:4px;margin-top:24px}
a{color:#1f3a68}.muted{color:#6b7280;font-size:.85rem}
table{border-collapse:collapse;width:100%;font-size:.9rem}td,th{border:1px solid #e3e7ef;padding:5px 7px;text-align:left;vertical-align:top}th{background:#f1f4fa}
.muro{background:#efeae2;padding:10px;border-radius:10px}.msg{max-width:80%;margin:6px 0}.msg .b{background:#fff;border-radius:10px;padding:6px 10px;white-space:pre-wrap;box-shadow:0 1px 1px rgba(0,0,0,.08)}
.msg.mio{margin-left:auto}.msg.mio .b{background:#d9fdd3}.msg .m{font-size:.72rem;color:#667085;margin:1px 4px}.msg img{max-width:260px;display:block;border-radius:8px}
.tarjeta{border:1px solid #e3e7ef;border-radius:10px;padding:10px 14px;margin:10px 0}.error{color:#b42318}
</style>"""


def _pagina(titulo, cuerpo, volver='../index.html'):
    enlace = f'<p class="muted"><a href="{volver}">&larr; Volver al índice</a></p>' if volver else ''
    return (f'<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" '
            f'content="width=device-width,initial-scale=1"><title>{escape(titulo)}</title>{ESTILO}</head>'
            f'<body><main>{enlace}<h1>{escape(titulo)}</h1>{cuerpo}</main></body></html>')


def _hora(dt):
    return timezone.localtime(dt).strftime('%d/%m/%Y %I:%M %p').lower() if dt else ''


def _nombre(u):
    return (u.get_full_name() or u.username) if u else '—'


def _archivo_seguro(texto, largo=50):
    limpio = ''.join(c if c.isalnum() or c in '-_ ' else '' for c in (texto or ''))
    return '-'.join(limpio.split())[:largo] or 'sin-nombre'


class Copia:
    def __init__(self, usuario, medios=True):
        self.usuario = usuario
        self.medios = medios
        # En el disco temporal y no en la memoria: una copia con muchas fotos no debe llenar la RAM del servidor.
        self.buffer = tempfile.SpooledTemporaryFile(max_size=4 * 1024 * 1024)
        self.zip = zipfile.ZipFile(self.buffer, 'w', zipfile.ZIP_DEFLATED)
        self.peso_medios = 0
        self.medios_omitidos = 0
        self.indice = []           # (titulo, ruta o '', detalle)
        self.errores = []

    def texto(self, ruta, contenido):
        self.zip.writestr(ruta, contenido.encode('utf-8') if isinstance(contenido, str) else contenido)

    def medio(self, ruta, campo):
        """Copia un archivo (FieldFile) dentro del .zip; '' si no se agregó."""
        if not self.medios or not campo:
            return ''
        try:
            tam = campo.size
        except Exception:
            tam = 0
        if self.peso_medios + tam > MAX_MEDIOS:
            self.medios_omitidos += 1
            return ''
        ext = os.path.splitext(campo.name)[1].lower()[:8]
        ruta = ruta + ext
        info = zipfile.ZipInfo(ruta, date_time=timezone.localtime().timetuple()[:6])   # sin comprimir: ya lo están
        try:
            with campo.open('rb') as origen, self.zip.open(info, 'w') as destino:
                shutil.copyfileobj(origen, destino, 1024 * 1024)
        except Exception:
            log.warning('Copia: no se pudo leer %s', getattr(campo, 'name', ''))
            return ''
        self.peso_medios += tam or self.zip.getinfo(ruta).file_size
        return ruta

    def parte(self, nombre, funcion, *args):
        try:
            funcion(self, *args)
        except Exception as e:          # una parte que falla no daña las demás
            log.exception('Copia de %s: falló «%s»', self.usuario.pk, nombre)
            self.errores.append(f'{nombre}: {e.__class__.__name__}')

    def cerrar(self):
        filas = ''
        for t, r, d in self.indice:
            enlace = f'<a href="{escape(r)}">{escape(t)}</a>' if r else escape(t)
            detalle = f' <span class="muted">· {escape(d)}</span>' if d else ''
            filas += f'<li>{enlace}{detalle}</li>'
        avisos = ''
        if self.medios_omitidos:
            avisos += (f'<p class="error">{self.medios_omitidos} archivo(s) no se agregaron porque la copia pasaba de '
                       f'{MAX_MEDIOS // 1024 // 1024} MB. Siguen en la plataforma.</p>')
        if not self.medios:
            avisos += '<p class="muted">Esta copia no trae fotos, notas de voz ni adjuntos (así lo escogió).</p>'
        if self.errores:
            avisos += '<p class="error">No se pudieron copiar: ' + escape('; '.join(self.errores)) + '</p>'
        cuerpo = (f'<p>Copia de seguridad de <b>{escape(_nombre(self.usuario))}</b> hecha el {_hora(timezone.now())}. '
                  'Se abre con cualquier navegador, sin internet y sin entrar a la plataforma.</p>'
                  f'{avisos}<ul>{filas or "<li>No hay nada que copiar todavía.</li>"}</ul>'
                  '<p class="muted">Guarde este archivo en un lugar seguro: tiene información personal.</p>')
        self.texto('index.html', _pagina('Copia de seguridad · mcolegio', cuerpo, volver=''))
        self.zip.close()
        tam = self.buffer.tell()
        self.buffer.seek(0)
        return self.buffer, tam


# ---------------------------------------------------------------------------
# Partes
# ---------------------------------------------------------------------------
def _burbujas(copia, mensajes, carpeta_medios, es_mio, autor_de):
    html = []
    for m in mensajes:
        cuerpo = ''
        if m.tipo == 'foto' and m.archivo:
            ruta = copia.medio(f'{carpeta_medios}/{m.pk}-foto', m.archivo)
            cuerpo += f'<img src="../{escape(ruta)}" alt="Foto">' if ruta else '<i>[Foto]</i><br>'
        elif m.tipo == 'voz' and m.archivo:
            ruta = copia.medio(f'{carpeta_medios}/{m.pk}-voz', m.archivo)
            cuerpo += (f'<audio controls src="../{escape(ruta)}"></audio>' if ruta
                       else f'<i>[Nota de voz · {m.duracion} s]</i><br>')
        cuerpo += escape(m.texto or '')
        clase = 'msg mio' if es_mio(m) else 'msg'
        html.append(f'<div class="{clase}"><div class="m"><b>{escape(autor_de(m))}</b> · {_hora(m.creado)}</div>'
                    f'<div class="b">{cuerpo}</div></div>')
    return '<div class="muro">' + ''.join(html) + '</div>' if html else '<p class="muted">Sin mensajes.</p>'


def chat_colegio(copia):
    from chat.models import Conversacion
    from chat.views import _titulo
    u = copia.usuario
    convs = Conversacion.objects.filter(participantes__usuario=u).distinct().prefetch_related('participantes__usuario')
    n = 0
    lista = []
    for conv in convs:
        mensajes = conv.mensajes.filter(eliminado=False).select_related('autor')
        if not mensajes.exists():
            continue
        titulo = _titulo(conv, u)
        ruta = f'chat/{conv.pk}-{_archivo_seguro(titulo)}.html'
        cuerpo = _burbujas(copia, mensajes, 'chat/medios', lambda m: m.autor_id == u.pk, lambda m: _nombre(m.autor))
        copia.texto(ruta, _pagina(f'{titulo} · {conv.get_tipo_display()}', f'<p class="muted">{escape(conv.colegio.nombre)}</p>{cuerpo}'))
        lista.append(f'<li><a href="{escape(ruta.split("/", 1)[1])}">{escape(titulo)}</a> <span class="muted">· {conv.mensajes.filter(eliminado=False).count()} mensajes</span></li>')
        n += 1
    if n:
        copia.texto('chat/index.html', _pagina('Chat del colegio', f'<ul>{"".join(lista)}</ul>'))
        copia.indice.append(('Chat del colegio', 'chat/index.html', f'{n} conversaciones'))


def chat_salon(copia):
    cuenta = getattr(copia.usuario, 'cuenta_salon', None)
    if cuenta is None:
        return
    from chat.models import ConversacionSalon
    lista, n = [], 0
    nombre_docente = _nombre(copia.usuario)
    for conv in ConversacionSalon.objects.filter(grupo__propietario=cuenta).select_related('grupo', 'integrante'):
        mensajes = conv.mensajes.filter(eliminado=False).select_related('integrante')
        if not mensajes.exists():
            continue
        titulo = f'{conv.grupo.nombre} · {conv.integrante.completo if conv.integrante else "Todo el grupo"}'
        ruta = f'chat-salon/{conv.pk}-{_archivo_seguro(titulo)}.html'
        cuerpo = _burbujas(copia, mensajes, 'chat-salon/medios', lambda m: m.integrante_id is None,
                           lambda m: nombre_docente if m.integrante_id is None else m.integrante.completo)
        copia.texto(ruta, _pagina(titulo, cuerpo))
        lista.append(f'<li><a href="{escape(ruta.split("/", 1)[1])}">{escape(titulo)}</a></li>')
        n += 1
    if n:
        copia.texto('chat-salon/index.html', _pagina('Chat de Mi Salón Virtual', f'<ul>{"".join(lista)}</ul>'))
        copia.indice.append(('Chat de Mi Salón Virtual', 'chat-salon/index.html', f'{n} conversaciones'))


def circulares(copia):
    from circulares.models import Circular, Lectura
    u = copia.usuario
    qs = (Circular.objects.filter(Q(lecturas__usuario=u) | Q(autor=u), publicada__isnull=False)
          .distinct().select_related('colegio').order_by('-publicada'))
    partes = []
    for c in qs:
        lectura = Lectura.objects.filter(circular=c, usuario=u).first()
        adj = ''
        if c.adjunto:
            ruta = copia.medio(f'circulares/adjuntos/{c.pk}-{_archivo_seguro(c.titulo, 30)}', c.adjunto)
            adj = f'<p>Adjunto: <a href="{escape(ruta.split("/", 1)[1])}">abrir</a></p>' if ruta else '<p class="muted">Tiene un adjunto (está en la plataforma).</p>'
        estado = ''
        if lectura and lectura.confirmada:
            estado = f' · confirmada el {_hora(lectura.confirmada)}'
        partes.append(f'<div class="tarjeta"><b>Circular {c.numero} · {escape(c.titulo)}</b>'
                      f'<div class="muted">{escape(c.colegio.nombre)} · {_hora(c.publicada)}{estado}</div>'
                      f'<div style="white-space:pre-wrap">{escape(c.cuerpo)}</div>{adj}</div>')
    if partes:
        copia.texto('circulares/index.html', _pagina('Circulares', ''.join(partes)))
        copia.indice.append(('Circulares', 'circulares/index.html', f'{len(partes)} circulares'))


def correo_interno(copia):
    from notas.models import Mensaje
    u = copia.usuario
    qs = (Mensaje.objects.filter(Q(remitente=u) | Q(destinatario=u), estado='ENVIADO')
          .select_related('remitente', 'destinatario').order_by('-fecha_envio')[:3000])
    partes = [f'<div class="tarjeta"><b>{escape(m.asunto)}</b><div class="muted">De {escape(_nombre(m.remitente))} '
              f'para {escape(_nombre(m.destinatario))} · {_hora(m.fecha_envio)}</div>'
              f'<div style="white-space:pre-wrap">{escape(m.cuerpo)}</div></div>' for m in qs]
    if partes:
        copia.texto('correo/index.html', _pagina('Correo interno', ''.join(partes)))
        copia.indice.append(('Correo interno', 'correo/index.html', f'{len(partes)} mensajes'))


def estudiante(copia):
    from notas.models import Asistencia, Calificacion, Estudiante, RegistroObservador
    for est in Estudiante.objects.filter(user=copia.usuario).select_related('colegio', 'curso'):
        notas = (Calificacion.objects.filter(estudiante=est, tipo_nota__in=('PROM_PERIODO', 'NIVELACION'))
                 .select_related('materia', 'periodo').order_by('periodo__ano_lectivo', 'periodo__orden', 'materia__nombre'))
        filas = ''.join(f'<tr><td>{n.periodo.ano_lectivo}</td><td>{escape(n.periodo.get_nombre_display())}</td>'
                        f'<td>{escape(n.materia.nombre)}</td><td>{escape(n.get_tipo_nota_display())}</td>'
                        f'<td><b>{n.valor_nota}</b></td><td>{escape(n.observacion or "")}</td></tr>' for n in notas)
        tabla = (f'<table><tr><th>Año</th><th>Periodo</th><th>Asignatura</th><th>Nota</th><th>Valor</th>'
                 f'<th>Observación</th></tr>{filas}</table>' if filas else '<p class="muted">Sin notas registradas.</p>')
        fallas = Asistencia.objects.filter(estudiante=est, estado__in=('A', 'T')).select_related('asignacion__materia')
        f_filas = ''.join(f'<tr><td>{a.fecha:%d/%m/%Y}</td><td>{escape(a.asignacion.materia.nombre)}</td>'
                          f'<td>{escape(a.get_estado_display())}</td><td>{"Sí" if a.justificada else "No"}</td></tr>'
                          for a in fallas[:2000])
        obs = RegistroObservador.objects.filter(estudiante=est).order_by('-fecha_suceso')
        o_partes = ''.join(f'<div class="tarjeta"><b>{r.fecha_suceso:%d/%m/%Y} · {escape(r.get_tipo_display())}</b>'
                           f'<div style="white-space:pre-wrap">{escape(r.descripcion)}</div>'
                           f'{f"<p><i>Descargo:</i> {escape(r.descargo_estudiante)}</p>" if r.descargo_estudiante else ""}</div>'
                           for r in obs)
        cuerpo = (f'<p class="muted">{escape(est.colegio.nombre)}{f" · Curso {escape(est.curso.nombre)}" if est.curso_id else ""}</p>'
                  f'<h2>Notas</h2>{tabla}'
                  f'<h2>Inasistencias y llegadas tarde</h2>'
                  + (f'<table><tr><th>Fecha</th><th>Asignatura</th><th>Estado</th><th>Justificada</th></tr>{f_filas}</table>'
                     if f_filas else '<p class="muted">Sin registros.</p>')
                  + f'<h2>Observador</h2>{o_partes or "<p class=muted>Sin registros.</p>"}')
        ruta = f'estudiante/{est.pk}-{_archivo_seguro(est.colegio.nombre, 30)}.html'
        copia.texto(ruta, _pagina(f'Notas y seguimiento · {_nombre(copia.usuario)}', cuerpo))
        copia.indice.append(('Notas, asistencia y observador', ruta, est.colegio.nombre))


def docente(copia):
    from notas.models import AsignacionDocente, Calificacion, Estudiante
    asigs = (AsignacionDocente.objects.filter(docente__user=copia.usuario)
             .select_related('materia', 'curso', 'colegio').order_by('curso__nombre', 'materia__nombre'))
    lista = []
    for a in asigs:
        notas = (Calificacion.objects.filter(materia=a.materia, estudiante__curso=a.curso, colegio=a.colegio,
                                             tipo_nota__in=('PROM_PERIODO', 'NIVELACION'))
                 .select_related('estudiante__user', 'periodo').order_by('periodo__ano_lectivo', 'periodo__orden'))
        periodos, tabla = [], {}
        for n in notas:
            p = f'{n.periodo.ano_lectivo} {n.periodo.get_nombre_display()}' + (' (nivelación)' if n.tipo_nota == 'NIVELACION' else '')
            if p not in periodos:
                periodos.append(p)
            tabla.setdefault(n.estudiante_id, {})[p] = str(n.valor_nota).replace('.', ',')
        salida = io.StringIO()
        w = csv.writer(salida, delimiter=';')
        w.writerow(['Estudiante'] + periodos)
        for est in Estudiante.objects.filter(curso=a.curso, colegio=a.colegio).select_related('user'):
            w.writerow([_nombre(est.user)] + [tabla.get(est.pk, {}).get(p, '') for p in periodos])
        ruta = f'docente/notas-{_archivo_seguro(a.curso.nombre, 12)}-{_archivo_seguro(a.materia.nombre, 30)}.csv'
        copia.texto(ruta, '﻿' + salida.getvalue())       # con BOM: Excel lo abre con tildes
        lista.append(f'<li><a href="{escape(ruta.split("/", 1)[1])}">{escape(a.materia.nombre)} · {escape(a.curso.nombre)}</a></li>')
    if lista:
        copia.texto('docente/index.html', _pagina('Notas de mis asignaturas',
                                                  '<p class="muted">Se abren con Excel o Google Sheets.</p>'
                                                  f'<ul>{"".join(lista)}</ul>'))
        copia.indice.append(('Notas de mis asignaturas', 'docente/index.html', f'{len(lista)} planillas'))


def materiales(copia):
    from materiales.models import Documento
    docs = Documento.objects.filter(propietario=copia.usuario)
    lista = []
    for d in docs:
        ruta = f'materiales/{d.pk}-{_archivo_seguro(d.titulo)}.json'
        copia.texto(ruta, json.dumps({'titulo': d.titulo, 'tipo': d.tipo, 'contenido': d.contenido},
                                     ensure_ascii=False, indent=1, default=str))
        lista.append(f'<li><a href="{escape(ruta.split("/", 1)[1])}">{escape(d.titulo)}</a></li>')
    if lista:
        copia.texto('materiales/index.html', _pagina('Mis materiales', '<p class="muted">El contenido de cada guía o '
                                                     'actividad, para recuperarlo si hiciera falta.</p>'
                                                     f'<ul>{"".join(lista)}</ul>'))
        copia.indice.append(('Mis materiales', 'materiales/index.html', f'{len(lista)} documentos'))


def datos(copia):
    u = copia.usuario
    from notas.models import AdministradorColegio, Docente, Estudiante
    roles = ([f'Directivo · {a.colegio.nombre}' for a in AdministradorColegio.objects.filter(user=u).select_related('colegio')]
             + [f'Docente · {d.colegio.nombre}' for d in Docente.objects.filter(user=u).select_related('colegio')]
             + [f'Estudiante · {e.colegio.nombre}' for e in Estudiante.objects.filter(user=u).select_related('colegio')])
    if getattr(u, 'cuenta_salon', None) is not None:
        roles.append('Docente · Mi Salón Virtual')
    cuerpo = (f'<table><tr><th>Nombre</th><td>{escape(_nombre(u))}</td></tr><tr><th>Usuario</th><td>{escape(u.username)}</td></tr>'
              f'<tr><th>Correo</th><td>{escape(u.email or "—")}</td></tr>'
              f'<tr><th>En la plataforma</th><td>{"<br>".join(escape(r) for r in roles) or "—"}</td></tr></table>')
    copia.texto('mis-datos.html', _pagina('Mis datos', cuerpo, volver='index.html'))
    copia.indice.append(('Mis datos', 'mis-datos.html', ''))


PARTES = [('Mis datos', datos), ('Chat del colegio', chat_colegio), ('Chat de Mi Salón Virtual', chat_salon),
          ('Circulares', circulares), ('Correo interno', correo_interno), ('Notas del estudiante', estudiante),
          ('Notas de mis asignaturas', docente), ('Mis materiales', materiales)]


def armar(usuario, medios=True):
    """(archivo temporal abierto en el inicio, tamaño) del .zip con todo lo de esta persona."""
    copia = Copia(usuario, medios=medios)
    for nombre, funcion in PARTES:
        copia.parte(nombre, funcion)
    return copia.cerrar()
