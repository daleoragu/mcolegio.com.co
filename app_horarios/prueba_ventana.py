"""Prueba de la ventana (se corre en Windows antes de empaquetar).

Abre la app con el archivo de ejemplo, pone reglas, arrastra fichas, genera,
completa, cambia de vista y exporta, sin que nadie toque nada.
"""
import os
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import generador_horarios as g                      # noqa: E402
from horarios.proyecto import Proyecto               # noqa: E402

g.messagebox.showwarning = lambda *a, **k: print('aviso:', a[1:])
g.messagebox.showinfo = lambda *a, **k: print('info:', a[1:])
g.messagebox.askyesno = lambda *a, **k: True

app = g.App()
app.withdraw()
app.cargar(Proyecto.abrir_datos(os.path.join(AQUI, 'ejemplo_datos.mch')))
assert len(app.nb.tabs()) == 5, app.nb.tabs()
p = app.p
D = p.datos
# 1. Datos: horas extra y bloques
a0 = sorted(D.asignaciones)[0]
p.asig(a0)['extra'] = True
p.asig(a0)['bloques'] = '2+1'
app._llenar_datos()
assert app.tv_asig.get_children()
# 2. Reglas
p.cond['permanencia_horas'] = 6
p.cond['espacios'].append({'nombre': 'Sala de sistemas', 'capacidad': 1})
mid = sorted(D.materias)[0]
p.regla(mid)['bloques'] = '2+2'
app._llenar_materias()
# 3. Docentes: casillas de tres estados y día completo
app.lb_doc.selection_set(0)
app._ver_docente()
d = app.docs[0]
j = p.jornadas_de_docente(d['id'])[0]
fr = [f for f in D.franjas_de(j['id']) if not f['descanso']][0]
assert p.siguiente_estado(d['id'], j['dias'][0], fr['id']) == 'no_puede'
app._dia_docente(d['id'], j['dias'][-1])
app._dia_docente(d['id'], j['dias'][-1])
# 4. Reuniones y clases simultáneas
app._reuniones_area()
if p.cond['reuniones']:
    p.cond['reuniones'][0]['jefe'] = p.cond['reuniones'][0]['docentes'][0]
app._llenar_grupos()
# 5. Horario: en blanco, arrastrar fichas, generar y completar
app.nb.select(4)
app._en_blanco()
app.update()
alt = app._alt()
assert alt and alt.get('manual')
cid = app.quien_l[0][1]
pend = p.pendientes(alt, cid)
assert pend, 'no hay fichas por ubicar'
jc = D.jornadas[D.jornada_de_curso[cid]]
clase = [f for f in D.franjas_de(jc['id']) if not f['descanso']]
app.soltar({'tipo': 'nueva', 'asig': pend[0][0]['id']}, ('celda', jc['dias'][1], clase[0]['id']))
assert len(alt['sesiones']) == 1, alt['sesiones']
app.soltar({'tipo': 'puesta', 'i': 0}, ('celda', jc['dias'][2], clase[1]['id']))
assert alt['sesiones'][0]['dia'] == jc['dias'][2]
app.soltar({'tipo': 'nueva', 'asig': pend[0][0]['id']}, ('celda', jc['dias'][2], clase[1]['id']))   # ocupada
assert 'ya tiene' in app.estado.cget('text'), app.estado.cget('text')
assert app.rejilla.winfo_children()
nuevo = p.completar(alt, segundos=3)
app._llenar_alternativas()
app.update()
assert nuevo['horas_sin_ubicar'] == 0, nuevo['sin_ubicar']
assert not nuevo['choques'], nuevo['choques']
p.generar(cuantas=2, segundos=3, base=nuevo)
app._llenar_alternativas()
app.update()
app._ver()
app.cb_ver.current(1)
app._opciones_ver()
assert app.rejilla.winfo_children()
alt = app._alt()
assert alt and alt['horas_sin_ubicar'] == 0 and not alt['choques'], alt.get('sin_ubicar')
tmp = tempfile.mkdtemp()
p.exportar_resultado(alt, os.path.join(tmp, 'h.mchr'))
p.exportar_excel(alt, os.path.join(tmp, 'h.xlsx'))
p.guardar(os.path.join(tmp, 'p.mchp'))
Proyecto.abrir(os.path.join(tmp, 'p.mchp'))
app.destroy()
print('VENTANA OK')
