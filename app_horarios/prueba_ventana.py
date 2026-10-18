"""Prueba de la ventana (se corre en Windows antes de empaquetar).

Abre la app con el archivo de ejemplo, pone reglas, arrastra fichas, genera,
completa, cambia de vista y exporta, sin que nadie toque nada.
"""
import faulthandler
import os
import sys
import tempfile

# Si algo se queda esperando, a los 8 minutos muestra dónde y termina (para verlo en GitHub)
faulthandler.dump_traceback_later(480, exit=True)

# La consola de Windows no siempre es UTF-8: que los avisos con ✔ / ✖ no rompan la prueba.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except AttributeError:
    pass

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import generador_horarios as g                      # noqa: E402
from horarios.proyecto import Proyecto               # noqa: E402



def prueba():
    g.messagebox.showwarning = lambda *a, **k: print('aviso:', a[1:])
    g.messagebox.showinfo = lambda *a, **k: print('info:', a[1:])
    g.messagebox.askyesno = lambda *a, **k: True
    g.messagebox.askyesnocancel = lambda *a, **k: True
    g.messagebox.showerror = lambda *a, **k: print('ERROR:', a[1:], flush=True)

    app = g.App()
    app.withdraw()
    app.cargar(Proyecto.abrir_datos(os.path.join(AQUI, 'ejemplo_datos.mch')))
    assert len(app.nb.tabs()) == 6, app.nb.tabs()
    p = app.p
    D = p.datos
    assert p.disponibilidad_plataforma(), 'el ejemplo trae disponibilidad'
    did_disp = list(p.disponibilidad_plataforma())[0]
    assert p.docente(did_disp)['no_puede'] and p.docente(did_disp).get('nota')
    # 1. Datos: horas extra y bloques
    a0 = sorted(D.asignaciones)[0]
    p.asig(a0)['extra'] = True
    p.asig(a0)['bloques'] = '2+1'
    app._llenar_datos()
    assert app.tv_asig.get_children()
    # Filtros de la tabla de clases (grado, área, docente y buscar)
    total = len(app.tv_asig.get_children())
    primera = D.asignaciones[sorted(D.asignaciones)[0]]
    assert app.filtro_datos(primera)
    assert total == len(D.asignaciones)
    # Botón de dividir en bloques automáticamente
    app._dividir_bloques()
    assert any(p.asig(x).get('bloques') for x in D.asignaciones), 'no dividió ninguna clase'
    # 2. Reglas
    p.cond['permanencia_horas'] = 6
    p.cond['espacios'].append({'nombre': 'Sala de sistemas', 'capacidad': 1})
    mid = sorted(D.materias)[0]
    p.regla(mid)['bloques'] = '2+2'
    app._llenar_materias()
    p.cond['pesos']['hueco'] = 8
    p.cond['pesos']['equilibrio'] = 7
    # Si tiene la 7.ª no tiene la 1.ª (como preferencia: el ejemplo no tiene docentes para que sea obligatoria)
    assert p.cond['excluyente']['activa'] is False
    p.cond['excluyente'].update(activa=True, a=1, b=7, obligatoria=False)
    # Prioridad a los bloques (2+2+1…) para las materias sin bloques propios
    p.cond['bloques_general'].update(activa=True, desde=2)
    app._llenar_materias()
    assert p.cond['bloques_general']['activa']
    # 3. Docentes: casillas de tres estados y día completo
    app.lb_doc.selection_set(0)
    app._ver_docente()
    d = app.docs[0]
    j = p.jornadas_de_docente(d['id'])[0]
    fr = [f for f in D.franjas_de(j['id']) if not f['descanso']][0]
    p.poner_celda(d['id'], j['dias'][0], fr['id'], 'libre')
    assert p.siguiente_estado(d['id'], j['dias'][0], fr['id']) == 'no_puede'
    assert p.siguiente_estado(d['id'], j['dias'][0], fr['id']) == 'prefiere_no'
    assert p.siguiente_estado(d['id'], j['dias'][0], fr['id']) == 'evitar'
    assert p.siguiente_estado(d['id'], j['dias'][0], fr['id']) == 'libre'
    app._dia_docente(d['id'], j['dias'][-1])
    app._dia_docente(d['id'], j['dias'][-1])
    p.docente(d['id'])['dia_libre'] = True
    app._ver_docente()
    p.docente(d['id'])['sin_excluyente'] = False
    # Cursos: horas sin clase
    app.lb_doc.selection_clear(0, 'end')
    app.lb_doc.selection_set(len(app.docs))
    app._ver_docente()
    c0 = app.cursos_l[0]
    jc0 = D.jornadas[D.jornada_de_curso[c0['id']]]
    ult = [f for f in D.franjas_de(jc0['id']) if not f['descanso']][-1]
    assert p.alternar_celda_curso(c0['id'], jc0['dias'][-1], ult['id'])
    # 4. Reuniones y clases simultáneas
    app._reuniones_area()
    if p.cond['reuniones']:
        p.cond['reuniones'][0]['jefe'] = p.cond['reuniones'][0]['docentes'][0]
    app._llenar_grupos()
    # Multigrado (Escuela Nueva): dos cursos que ven clase juntos
    cs = [c['id'] for c in D.crudo['cursos'] if c['id'] in D.jornada_de_curso][:2]
    assert p.agregar_multigrado('Sede rural', cs) is None
    app._llenar_grupos()
    assert app.tv_mg.get_children()
    del p.cond['multigrado'][0]
    app._llenar_grupos()
    # 5. Actividades complementarias y descansos
    p.cond['actividades'].append({'nombre': 'Atención a padres', 'horas': 1, 'max_dia': 1, 'docentes': []})
    p.cond['acompanamiento']['zonas'].append({'nombre': 'Patio', 'cuantos': 1})
    app._llenar_tareas()
    assert app.tv_act.get_children() and app.tv_zon.get_children()
    # 6. Horario: en blanco, arrastrar fichas, generar y completar
    app.nb.select(5)
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
    # Colores al escoger una ficha: verde libre, amarillo ocupada (se puede reemplazar), rojo no se puede
    otra = pend[1][0]['id'] if len(pend) > 1 else pend[0][0]['id']
    app.escoger({'tipo': 'nueva', 'asig': otra})
    assert app._mapa[(jc['dias'][2], clase[1]['id'])] == 'ocupado', app._mapa[(jc['dias'][2], clase[1]['id'])]
    assert 'libre' in app._mapa.values()
    assert app.rejilla.winfo_children()
    app.tocar_celda(('celda', jc['dias'][3], clase[2]['id']))         # tocar una casilla con la ficha escogida
    assert len(alt['sesiones']) == 2, alt['sesiones']
    # Amarillo: reemplazar (la que estaba vuelve a «por ubicar»)
    app.soltar({'tipo': 'nueva', 'asig': otra}, ('celda', jc['dias'][2], clase[1]['id']))
    assert 'reemplazada' in app.estado.cget('text') or 'intercambiadas' in app.estado.cget('text'), app.estado.cget('text')
    # Rojo: si la ficha está fijada 🔒 no se puede
    k = next(k for k, x in enumerate(alt['sesiones']) if x['dia'] == jc['dias'][2] and x['franja'] == clase[1]['id'])
    p.alternar_fijada(alt, k) if not alt['sesiones'][k].get('fijada') else None
    app.escoger({'tipo': 'nueva', 'asig': pend[0][0]['id']})
    assert app._mapa[(jc['dias'][2], clase[1]['id'])] == 'imposible'
    app.soltar({'tipo': 'nueva', 'asig': pend[0][0]['id']}, ('celda', jc['dias'][2], clase[1]['id']))
    assert 'fijada' in app.estado.cget('text'), app.estado.cget('text')
    # Ficha de bloque de 2 horas: se ubica completa, en cualquier orden respecto a la hora suelta
    con_bloque = next((x for x, _ in p.pendientes(alt, cid) if 2 in p.piezas_pendientes(alt, x['id'])), None)
    if con_bloque:
        app.escoger({'tipo': 'nueva', 'asig': con_bloque['id'], 'largo': 2})
        inicio = next(((d, f) for (d, f), e in app._mapa.items() if e == 'libre'), None)
        if inicio:
            antes_b = len(alt['sesiones'])
            app.soltar({'tipo': 'nueva', 'asig': con_bloque['id'], 'largo': 2}, ('celda', inicio[0], inicio[1]))
            print('bloque:', app.estado.cget('text'))
            assert len(alt['sesiones']) == antes_b + 2, app.estado.cget('text')
    # «Ubicar de a una hora» (lo que hace el menú del clic derecho; el menú no se abre en la prueba
    # porque en Windows se queda esperando un clic)
    app.sueltas.add(pend[0][0]['id'])
    app._ver()
    app.sueltas.discard(pend[0][0]['id'])
    # ¿Bloques partidos por el descanso? Se pregunta una vez
    p.cond['bloque_descanso'] = None
    app._preguntar_descanso()
    assert p.cond['bloque_descanso'] is True
    # Varias pestañas y una ventana aparte: todas muestran el mismo horario
    v2 = app.nueva_pestana(tipo=1)
    v3 = app.nueva_ventana()
    assert len(app.vistas) == 3 and v2.rejilla.winfo_children() and v3.rejilla.winfo_children()
    app.escoger({'tipo': 'nueva', 'asig': pend[0][0]['id']})
    # Cada pestaña puede mostrar otro horario (para compararlos)
    if len(p.alternativas) > 1:
        v2.cb_alt.current(1)
        v2._cambio_alt()
        assert v2.alt() is p.alternativas[1] and app.vistas[0].alt() is p.alternativas[0]
    # Filtro por grado en la vista
    v2.cb_ver.current(0)
    v2.opciones()
    if len(v2.filtros) > 1:
        v2.cb_filtro.current(1)
        v2.opciones(conservar_filtro=True)
        assert v2.quien_l
    app.cerrar_vista(v2)
    assert len(app.vistas) == 2
    app.quitar_seleccion()
    nuevo = p.completar(alt, segundos=8)
    app._llenar_alternativas()
    app.update()
    assert nuevo['horas_sin_ubicar'] == 0, nuevo['sin_ubicar']
    assert not nuevo['choques'], nuevo['choques']
    p.generar(cuantas=2, segundos=8, base=nuevo)
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
    assert alt['actividades'] and alt['acompanamientos'], (alt['actividades'], alt['acompanamientos'])
    assert not any(s for s in alt['sesiones'] if D.asignaciones[s['asignacion']]['curso'] == c0['id']
                   and s['dia'] == jc0['dias'][-1] and s['franja'] == ult['id'])
    # Armar desde la vista del docente: sus fichas pendientes se arrastran a su cuadrícula
    blanco = p.en_blanco()
    app._llenar_alternativas()
    app.cb_ver.current(1)
    app._opciones_ver()
    did = app.quien_l[app.cb_quien.current()][1]
    pd = p.pendientes_docente(blanco, did)
    assert pd, 'el docente no tiene fichas por ubicar'
    a1 = pd[0][0]
    jd = D.jornadas[D.jornada_de_curso[a1['curso']]]
    hora = [f for f in D.franjas_de(jd['id']) if not f['descanso']][2]
    antes_n = len(blanco['sesiones'])
    app.soltar({'tipo': 'nueva', 'asig': a1['id']}, ('celda', jd['dias'][0], hora['id']))
    print('docente:', app.estado.cget('text'))
    assert len(blanco['sesiones']) == antes_n + 1, blanco['sesiones']
    assert app.paleta.winfo_children()
    p.alternativas.remove(blanco)
    app._llenar_alternativas()
    # Intercambiar dos fichas del mismo curso arrastrando una sobre la otra
    app.cb_ver.current(0)
    app._opciones_ver()
    cid = app.quien_l[app.cb_quien.current()][1]
    mias = [k for k, s in enumerate(alt['sesiones']) if D.asignaciones[s['asignacion']]['curso'] == cid]
    k1 = mias[0]
    k2 = next(k for k in mias if alt['sesiones'][k]['asignacion'] != alt['sesiones'][k1]['asignacion'])
    antes = (alt['sesiones'][k1]['asignacion'], alt['sesiones'][k2]['asignacion'])
    app.soltar({'tipo': 'puesta', 'i': k1}, ('celda', alt['sesiones'][k2]['dia'], alt['sesiones'][k2]['franja']))
    print('intercambio:', app.estado.cget('text'))
    app.update()
    app.cb_ver.current(1)
    app._opciones_ver()
    app.update()
    print('paso:', 'Asistente cuando fal', flush=True)
    # Asistente cuando faltan horas: más tiempo, cambiar condiciones, consejos
    vacio = p.en_blanco()
    app._llenar_alternativas()
    assert vacio['horas_sin_ubicar'] > 0
    w = app.asistente(vacio)
    assert w is not None and app.sug_asistente, 'el asistente no sugirió nada'
    for _, var in app.sug_asistente:
        var.set(False)
    app.sug_asistente[0][1].set(True)
    app.generando = True                     # que no lance el generador en la prueba
    app._asistente_aplicar()
    app.generando = False
    assert app.ventana_asistente is None and len(app.nb.tabs()) == 6, app.nb.tabs()
    assert 'cambio' in app.estado.cget('text'), app.estado.cget('text')
    app.asistente(vacio)
    app._asistente_a_mano()
    p.alternativas.remove(vacio)
    app._llenar_alternativas()
    print('paso:', 'Zoom: agranda', flush=True)
    # Zoom: agranda y achica la cuadrícula
    v0 = app.vista_actual()
    app.zoom_todas(0.3)
    assert abs(v0.zoom - 1.3) < 1e-9 and v0._necesario > 600, (v0.zoom, v0._necesario)
    v0.cambiar_zoom(-2)
    assert v0.zoom == 0.5
    app.zoom_todas(None)
    assert v0.zoom == 1.0
    print('paso:', 'Varias cuadrículas e', flush=True)
    # Varias cuadrículas en una ventana (4): cada una con un curso distinto
    antes_v = len(app.vistas)
    mos = app.mosaico(4)
    assert len(mos) == 4 and len(app.vistas) == antes_v + 4
    cursos_m = [m.quien_l[m.cb_quien.current()] for m in mos]
    assert len(set(cursos_m)) == min(4, len(mos[0].quien_l)), cursos_m
    assert all(m.rejilla.winfo_children() for m in mos)
    mos[0].ventana.cerrar()
    assert len(app.vistas) == antes_v
    print('paso:', 'Deshacer un cambio', flush=True)
    # Deshacer un cambio a mano
    alt = app._alt()
    k = next(k for k, x in enumerate(alt['sesiones']) if not x.get('fijada'))
    antes_s = [dict(x) for x in alt['sesiones']]
    app.soltar({'tipo': 'puesta', 'i': k}, ('paleta',))
    assert len(alt['sesiones']) == len(antes_s) - 1
    app.deshacer()
    assert alt['sesiones'] == antes_s, 'no deshizo'
    print('paso:', 'Generar de verdad', flush=True)
    # Generar de verdad (en otro hilo), viendo lo que acomoda, y detener
    import time as _t
    app.var_alt.set(2)
    app.var_seg.set(30)
    app.var_vivo.set(True)
    app.generar()
    assert app.generando
    t0 = _t.monotonic()
    vio = False
    while app.generando and _t.monotonic() - t0 < 60:
        _t.sleep(0.3)
        app._revisar_cola()
        if app.alt_vivo is not None:
            vio = True
            assert app._alt() is app.alt_vivo and app._alt()['vivo']
            app.escoger({'tipo': 'nueva', 'asig': a0})          # mientras genera, solo se mira
            assert 'Espere' in app.estado.cget('text'), app.estado.cget('text')
            app.detener()
    assert vio, 'no mostró lo que iba acomodando'
    assert not app.generando and app.alt_vivo is None
    assert p.alternativas[0].get('detenido'), 'no se detuvo'
    assert _t.monotonic() - t0 < 25, _t.monotonic() - t0
    print('detenido:', app.lbl_prog.cget('text'))
    p.guardar(os.path.join(tmp, 'p.mchp'))
    Proyecto.abrir(os.path.join(tmp, 'p.mchp'))
    app.destroy()
    print('VENTANA OK')


try:
    prueba()
except BaseException:
    import traceback
    t = traceback.format_exc()
    print(t)
    # En GitHub sale como anotación del error (se ve sin abrir el registro completo).
    print('::error::' + t.replace('%', '%25').replace('\r', '').replace('\n', '%0A'))
    sys.exit(1)
