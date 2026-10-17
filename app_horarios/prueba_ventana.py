"""Prueba de la ventana (se corre en Windows antes de empaquetar).

Abre la app con el archivo de ejemplo, pone condiciones, genera, cambia de
vista y exporta, sin que nadie toque nada. Si algo falla, termina con error.
"""
import os
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import generador_horarios as g                      # noqa: E402
from horarios.proyecto import Proyecto               # noqa: E402

app = g.App()
app.withdraw()
app.cargar(Proyecto.abrir_datos(os.path.join(AQUI, 'ejemplo_datos.mch')))
assert len(app.nb.tabs()) == 5, app.nb.tabs()
# 1. Datos
assert app.tv_asig.get_children()
# 2. Materias: marcar la primera como bloque doble
mid = app.tv_mat.get_children()[0]
app.p.regla(int(mid))['doble'] = True
app._llenar_materias()
# 3. Docentes
app.lb_doc.selection_set(0)
app._ver_docente()
d = app.docs[0]
j = app.p.jornadas_de_docente(d['id'])[0]
fr = [f for f in app.p.datos.franjas_de(j['id']) if not f['descanso']][0]
app.p.alternar_no_puede(d['id'], j['dias'][0], fr['id'])
app._ver_docente()
# 4. Fijar una clase
app.cb_curso.current(0)
app._curso_fija()
app.cb_asig.current(0)
app.cb_dia.current(1)
app.cb_hora.current(1)
g.messagebox.showwarning = lambda *a, **k: print('aviso:', a[1:])
app._fijar()
assert app.tv_fijas.get_children(), 'no quedó la clase fijada'
# 5. Generar (sin hilo, para la prueba) y ver
app.p.generar(cuantas=2, segundos=3)
app._llenar_alternativas()
app.update()
app._ver()
assert app.rejilla.winfo_children(), 'no se dibujó el horario'
app.cb_ver.current(1)
app._opciones_ver()
assert app.rejilla.winfo_children()
alt = app._alt()
assert alt and alt['horas_sin_ubicar'] == 0 and not alt['choques'], alt
tmp = tempfile.mkdtemp()
app.p.exportar_resultado(alt, os.path.join(tmp, 'h.mchr'))
app.p.exportar_excel(alt, os.path.join(tmp, 'h.xlsx'))
app.p.guardar(os.path.join(tmp, 'p.mchp'))
app.destroy()
print('VENTANA OK')
