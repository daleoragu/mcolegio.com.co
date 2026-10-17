"""mcolegio · Generador de horarios (aplicación de Windows).

Funciona sin internet:
  1. Abra el archivo de datos (.mch) que descargó de la plataforma.
  2. Revise los datos y ponga las reglas: bloques, permanencia, horas extra,
     sedes, espacios, docentes y cursos, reuniones de área, clases simultáneas,
     actividades complementarias, acompañamiento de descansos y prioridades.
  3. Arme el horario: arrastre fichas a mano, genere alternativas o combine
     (fije lo que quiera y deje que el generador complete el resto).
  4. Guarde la alternativa (.mchr) y súbala en la plataforma.
"""
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))

from horarios import nucleo                     # noqa: E402
from horarios.proyecto import Proyecto           # noqa: E402

VERSION = '2.2'
TITULO = 'mcolegio · Generador de horarios'
AZUL, AZUL_CLARO, GRIS, BLANCO = '#3730a3', '#e0e7ff', '#f1f5f9', '#ffffff'
VERDE, ROJO, AMARILLO = '#dcfce7', '#fecaca', '#fef08a'
NARANJA = '#fdba74'
FIJA, SUELTA, REUNION = '#c7d2fe', '#ede9fe', '#fde68a'
ACTIVIDAD, TURNO = '#bbf7d0', '#a5f3fc'
COLOR_ESTADO = {'libre': VERDE, 'no_puede': ROJO, 'prefiere_no': AMARILLO, 'evitar': NARANJA}
TEXTO_ESTADO = {'libre': '', 'no_puede': 'No puede', 'prefiere_no': 'Mejor no', 'evitar': 'Mejor no +'}
ICONO = {'error': '✖ ', 'aviso': '⚠ ', 'info': 'ℹ '}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITULO)
        self.geometry('1260x800')
        self.minsize(1040, 660)
        self.p = None
        self.cola = queue.Queue()
        self.generando = False
        self._arr = None
        estilo = ttk.Style(self)
        try:
            estilo.theme_use('vista')
        except tk.TclError:
            estilo.theme_use('clam')
        estilo.configure('Titulo.TLabel', font=('Segoe UI', 13, 'bold'))
        estilo.configure('Sub.TLabel', font=('Segoe UI', 10, 'bold'))
        estilo.configure('Ayuda.TLabel', foreground='#555')
        estilo.configure('Treeview', rowheight=24)
        self._barra()
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill='both', expand=True, padx=8, pady=(0, 4))
        self.estado = ttk.Label(self, text='', anchor='w', padding=(10, 2))
        self.estado.pack(fill='x')
        self._bienvenida()
        self.protocol('WM_DELETE_WINDOW', self.salir)

    # ------------------------------------------------------------------
    def avisar(self, texto, error=False):
        self.estado.configure(text=texto, foreground='#b42318' if error else '#14532d')

    def _barra(self):
        b = ttk.Frame(self, padding=8)
        b.pack(fill='x')
        ttk.Button(b, text='📂 Abrir datos del colegio (.mch)', command=self.abrir_datos).pack(side='left')
        ttk.Button(b, text='Abrir proyecto', command=self.abrir_proyecto).pack(side='left', padx=4)
        ttk.Button(b, text='💾 Guardar proyecto', command=self.guardar).pack(side='left')
        ttk.Button(b, text='Actualizar datos', command=self.actualizar_datos).pack(side='left', padx=4)
        self.lbl_colegio = ttk.Label(b, text='Sin datos abiertos', style='Titulo.TLabel')
        self.lbl_colegio.pack(side='right')

    def _bienvenida(self):
        f = ttk.Frame(self.nb, padding=30)
        self.nb.add(f, text='Inicio')
        ttk.Label(f, text='Generador de horarios', style='Titulo.TLabel').pack(anchor='w')
        texto = ('1. En la plataforma, entre a Horarios y descargue «Datos del colegio (.mch)».\n'
                 '   (Si pidió a los docentes su disponibilidad en la plataforma, ya viene en ese archivo.)\n'
                 '2. Aquí, toque «Abrir datos del colegio» y escoja ese archivo.\n'
                 '3. Pestañas 1 a 5: revise los datos y ponga las reglas del colegio.\n'
                 '4. Pestaña 6: arrastre fichas a mano, genere alternativas o combine las dos cosas.\n'
                 '5. Guarde la alternativa «para la plataforma» (.mchr) y súbala en Horarios → Importar.\n\n'
                 'Consejo: ponga «no puede» solo cuando de verdad no se pueda. Para lo demás use «mejor no»:\n'
                 'así el generador tiene espacio para moverse y encuentra horarios mejores.\n\n'
                 'Guarde el proyecto (.mchp) para seguir otro día sin perder lo que lleva.')
        ttk.Label(f, text=texto, justify='left').pack(anchor='w', pady=12)
        ttk.Button(f, text='📂 Abrir datos del colegio', command=self.abrir_datos).pack(anchor='w')
        ttk.Label(f, text=f'Versión {VERSION}', style='Ayuda.TLabel').pack(anchor='w', pady=(20, 0))

    def cargar(self, proyecto):
        self.p = proyecto
        self.lbl_colegio.config(text=self.p.datos.colegio['nombre'])
        for t in self.nb.tabs():
            self.nb.forget(t)
        self.tab_datos()
        self.tab_reglas()
        self.tab_docentes()
        self.tab_grupos()
        self.tab_tareas()
        self.tab_horario()
        self.nb.select(0)
        disp = len(self.p.disponibilidad_plataforma())
        self.avisar('Datos abiertos. Empiece por revisar la pestaña 1.' +
                    (f' Trae la disponibilidad que marcaron {disp} docente(s) en la plataforma.' if disp else ''))

    # --- Archivos -------------------------------------------------------
    def abrir_datos(self):
        ruta = filedialog.askopenfilename(title='Datos del colegio', filetypes=[('Datos de mcolegio', '*.mch'), ('Todos', '*.*')])
        if ruta:
            try:
                self.cargar(Proyecto.abrir_datos(ruta))
            except (nucleo.ArchivoInvalido, OSError, KeyError) as e:
                messagebox.showerror(TITULO, f'No se pudo abrir: {e}')

    def abrir_proyecto(self):
        ruta = filedialog.askopenfilename(title='Proyecto', filetypes=[('Proyecto de horario', '*.mchp'), ('Todos', '*.*')])
        if ruta:
            try:
                self.cargar(Proyecto.abrir(ruta))
            except (nucleo.ArchivoInvalido, OSError, KeyError) as e:
                messagebox.showerror(TITULO, f'No se pudo abrir: {e}')

    def guardar(self):
        if not self.p:
            return
        ruta = self.p.ruta or filedialog.asksaveasfilename(title='Guardar proyecto', defaultextension='.mchp',
                                                           filetypes=[('Proyecto de horario', '*.mchp')],
                                                           initialfile='horario.mchp')
        if ruta:
            self.p.guardar(ruta)
            self.avisar(f'Proyecto guardado en {ruta}')

    def actualizar_datos(self):
        if not self.p:
            return self.abrir_datos()
        ruta = filedialog.askopenfilename(title='Datos nuevos del colegio', filetypes=[('Datos de mcolegio', '*.mch')])
        if ruta:
            try:
                self.cargar(self.p.actualizar_datos(ruta))
                self.avisar('Datos actualizados. Se conservaron las reglas.')
            except (nucleo.ArchivoInvalido, OSError) as e:
                messagebox.showerror(TITULO, str(e))

    def salir(self):
        if self.generando and not messagebox.askyesno(TITULO, 'Se está generando un horario. ¿Salir de todas formas?'):
            return
        self.destroy()

    # Utilidades de tablas
    def _tabla(self, padre, columnas, alto=None):
        marco = ttk.Frame(padre)
        tv = ttk.Treeview(marco, columns=[c for c, _, _ in columnas], show='headings', height=alto or 10)
        for c, t, w in columnas:
            tv.heading(c, text=t)
            tv.column(c, width=w, anchor='w' if w > 120 else 'center')
        sb = ttk.Scrollbar(marco, orient='vertical', command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        tv.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        return marco, tv

    def _numero(self, padre, texto, valor, desde, hasta, al_cambiar, paso=1):
        f = ttk.Frame(padre)
        ttk.Label(f, text=texto).pack(side='left')
        var = tk.StringVar(value=str(valor))
        sp = ttk.Spinbox(f, from_=desde, to=hasta, increment=paso, width=5, textvariable=var)
        sp.pack(side='left', padx=6)

        def cambio(*_):
            try:
                al_cambiar(float(var.get()) if paso != 1 else int(var.get()))
            except ValueError:
                pass
        var.trace_add('write', cambio)
        return f

    # --- 1. Datos ---------------------------------------------------------
    def tab_datos(self):
        f = ttk.Frame(self.nb, padding=10)
        self.nb.add(f, text='1. Datos')
        ttk.Label(f, text='Doble clic en una columna para cambiarla. «Bloques»: cómo se reparten las horas, '
                          'por ejemplo 2+2+1 (vacío = lo de la materia).', style='Ayuda.TLabel').pack(anchor='w')
        cuerpo = ttk.Panedwindow(f, orient='horizontal')
        cuerpo.pack(fill='both', expand=True, pady=6)
        marco, self.tv_asig = self._tabla(cuerpo, [
            ('curso', 'Curso', 80), ('materia', 'Materia', 170), ('docente', 'Docente', 190), ('horas', 'Horas', 55),
            ('bloques', 'Bloques', 80), ('extra', 'Hora extra', 85), ('partir', 'Si no cabe', 90)], 20)
        cuerpo.add(marco, weight=3)
        self.tv_asig.bind('<Double-1>', self._editar_asig)
        der = ttk.Frame(cuerpo, padding=(10, 0))
        cuerpo.add(der, weight=2)
        ttk.Label(der, text='Revisión', style='Titulo.TLabel').pack(anchor='w')
        self.txt_diag = tk.Text(der, wrap='word', height=20, relief='flat', background=GRIS, font=('Segoe UI', 9))
        self.txt_diag.pack(fill='both', expand=True)
        self._llenar_datos()

    def _llenar_datos(self):
        D, c = self.p.datos, self.p.cond
        self.tv_asig.delete(*self.tv_asig.get_children())
        orden = {x['id']: i for i, x in enumerate(D.crudo['cursos'])}
        for a in sorted(D.asignaciones.values(), key=lambda a: (orden.get(a['curso'], 0), D.nombre_materia(a['materia']))):
            r = c['asignaciones'].get(str(a['id']), {})
            self.tv_asig.insert('', 'end', iid=str(a['id']), values=(
                D.nombre_curso(a['curso']), D.nombre_materia(a['materia']), D.nombre_docente(a.get('docente')),
                D.ih(a['id'], c), r.get('bloques') or '', 'Sí' if r.get('extra') else '',
                'No partir' if r.get('dividir') is False else 'Partir'))
        diag = nucleo.diagnostico(D, c)
        t = self.txt_diag
        t.config(state='normal')
        t.delete('1.0', 'end')
        t.insert('end', f'{len(D.cursos)} cursos · {len(D.docentes)} docentes · {len(D.asignaciones)} asignaciones\n\n')
        t.insert('end', '✔ Todo listo para generar.\n\n' if not diag else '')
        for nivel in ('error', 'aviso', 'info'):
            for n, texto in diag:
                if n == nivel:
                    t.insert('end', ICONO[nivel] + texto + '\n')
        if diag:
            t.insert('end', '\n✖ impide generar completo · ⚠ puede dificultar · ℹ para tener en cuenta\n')
        t.insert('end', '\nCarga de los docentes (clase + extra):\n')
        for d in sorted(D.docentes.values(), key=lambda d: d['nombre']):
            base, extra, sedes = self.p.resumen_docente(d['id'])
            if base or extra:
                t.insert('end', f'  {d["nombre"]}: {base} h' + (f' + {extra} extra' if extra else '') +
                         (f' · sedes: {", ".join(sedes)}' if len(sedes) > 1 else '') + '\n')
        t.config(state='disabled')

    def _editar_asig(self, ev):
        aid = self.tv_asig.identify_row(ev.y)
        col = self.tv_asig.identify_column(ev.x)
        if not aid:
            return
        aid = int(aid)
        r = self.p.asig(aid)
        if col == '#4':
            n = simpledialog.askinteger(TITULO, 'Horas semanales:', initialvalue=self.p.datos.ih(aid, self.p.cond),
                                        minvalue=0, maxvalue=20, parent=self)
            if n is not None:
                self.p.poner_ih(aid, n)
        elif col == '#5':
            t = simpledialog.askstring(TITULO, 'Bloques (ej.: 2+2+1). Vacío = lo de la materia:',
                                       initialvalue=r.get('bloques') or '', parent=self)
            if t is not None:
                if t.strip() and not nucleo.patron(t):
                    messagebox.showwarning(TITULO, 'Escríbalo así: 2+2+1 (bloques de 1 a 4 horas).')
                else:
                    r['bloques'] = t.strip()
        elif col == '#6':
            r['extra'] = not r.get('extra')
        elif col == '#7':
            r['dividir'] = r.get('dividir') is False
        self._llenar_datos()

    # --- 2. Reglas ---------------------------------------------------------
    def tab_reglas(self):
        c = self.p.cond
        f = ttk.Frame(self.nb, padding=10)
        self.nb.add(f, text='2. Reglas')
        gen = ttk.LabelFrame(f, text='Reglas generales', padding=10)
        gen.pack(fill='x')

        def poner(k):
            return lambda v: c.__setitem__(k, v)
        self._numero(gen, 'Permanencia diaria de los docentes (horas, 0 = sin control; oficiales: 6):',
                     c.get('permanencia_horas') or 0, 0, 12, poner('permanencia_horas'), 0.5).grid(row=0, column=0, sticky='w')
        self._numero(gen, 'Minutos para cambiar de sede:', c.get('desplazamiento') or 0, 0, 180,
                     poner('desplazamiento')).grid(row=0, column=1, sticky='w', padx=20)
        self._numero(gen, 'Máximo de horas seguidas de un docente (0 = sin límite):', c.get('max_seguidas') or 0, 0, 10,
                     poner('max_seguidas')).grid(row=1, column=0, sticky='w', pady=4)
        self._numero(gen, 'Máximo de horas de una materia en un día:', c.get('max_por_dia') or 2, 1, 6,
                     poner('max_por_dia')).grid(row=1, column=1, sticky='w', padx=20)
        ex = c.setdefault('excluyente', {'activa': False, 'a': 1, 'b': 7, 'obligatoria': True})
        fila_ex = ttk.Frame(gen)
        fila_ex.grid(row=2, column=0, columnspan=2, sticky='w', pady=(6, 0))
        var_ex = tk.BooleanVar(value=bool(ex.get('activa')))
        ttk.Checkbutton(fila_ex, text='Si un docente tiene la hora', variable=var_ex,
                        command=lambda: ex.__setitem__('activa', var_ex.get())).pack(side='left')
        var_b = tk.StringVar(value=str(ex.get('b') or 7))
        ttk.Spinbox(fila_ex, from_=1, to=12, width=3, textvariable=var_b).pack(side='left', padx=4)
        ttk.Label(fila_ex, text='no tiene la hora').pack(side='left')
        var_a = tk.StringVar(value=str(ex.get('a') or 1))
        ttk.Spinbox(fila_ex, from_=1, to=12, width=3, textvariable=var_a).pack(side='left', padx=4)
        ttk.Label(fila_ex, text='el mismo día ·').pack(side='left')
        cb_ex = ttk.Combobox(fila_ex, state='readonly', width=14, values=['Obligatorio', 'Si se puede'])
        cb_ex.current(0 if ex.get('obligatoria', True) else 1)
        cb_ex.pack(side='left', padx=4)
        cb_ex.bind('<<ComboboxSelected>>', lambda e: ex.__setitem__('obligatoria', cb_ex.current() == 0))

        def horas_ex(*_):
            for clave, var in (('a', var_a), ('b', var_b)):
                try:
                    ex[clave] = max(1, int(var.get()))
                except ValueError:
                    pass
        var_a.trace_add('write', horas_ex)
        var_b.trace_add('write', horas_ex)
        ttk.Label(fila_ex, text='(si la jornada tiene menos horas, cuenta la última)', style='Ayuda.TLabel').pack(side='left', padx=6)
        pri = ttk.LabelFrame(f, text='Prioridades al mejorar el horario (0 = no importa · 5 = normal · 10 = muy importante)',
                             padding=8)
        pri.pack(fill='x', pady=(8, 0))
        pesos = c.setdefault('pesos', {})
        for k, (clave, texto) in enumerate(nucleo.CRITERIOS):
            fila, col = divmod(k, 2)
            ttk.Label(pri, text=texto).grid(row=fila, column=col * 2, sticky='w', padx=(0 if col == 0 else 20, 4))
            var = tk.IntVar(value=int(pesos.get(clave, 5)))
            esc = tk.Scale(pri, from_=0, to=10, orient='horizontal', length=150, showvalue=True, variable=var,
                           command=lambda v, clave=clave: pesos.__setitem__(clave, int(float(v))))
            esc.grid(row=fila, column=col * 2 + 1, sticky='w')
        cuerpo = ttk.Frame(f)
        cuerpo.pack(fill='both', expand=True, pady=8)
        izq = ttk.LabelFrame(cuerpo, text='Materias (doble clic para cambiar)', padding=6)
        izq.pack(side='left', fill='both', expand=True)
        marco, self.tv_mat = self._tabla(izq, [
            ('materia', 'Materia', 170), ('area', 'Área', 120), ('bloques', 'Bloques', 80), ('max', 'Máx./día', 70),
            ('primeras', 'Primeras horas', 100), ('ultima', 'Evitar última', 95), ('espacio', 'Espacio', 120)], 16)
        marco.pack(fill='both', expand=True)
        self.tv_mat.bind('<Double-1>', self._editar_materia)
        der = ttk.LabelFrame(cuerpo, text='Espacios compartidos', padding=6)
        der.pack(side='left', fill='y', padx=(8, 0))
        ttk.Label(der, text='Sala de sistemas, laboratorio,\ncancha… y cuántos cursos caben.', style='Ayuda.TLabel').pack(anchor='w')
        self.lb_esp = tk.Listbox(der, width=30, height=10)
        self.lb_esp.pack(fill='y', expand=True, pady=4)
        ttk.Button(der, text='Agregar espacio', command=self._agregar_espacio).pack(fill='x')
        ttk.Button(der, text='Quitar', command=self._quitar_espacio).pack(fill='x', pady=2)
        self._llenar_materias()

    def _llenar_materias(self):
        D = self.p.datos
        self.tv_mat.delete(*self.tv_mat.get_children())
        for m in sorted(D.materias.values(), key=lambda m: m['nombre']):
            r = self.p.cond['materias'].get(str(m['id']), {})
            self.tv_mat.insert('', 'end', iid=str(m['id']), values=(
                m['nombre'], m.get('area', ''), r.get('bloques') or ('2+2…' if r.get('doble') else '1+1…'),
                r.get('max_dia') or 'General', 'Sí' if r.get('primeras') else '', 'Sí' if r.get('ultimas') else '',
                r.get('espacio') or ''))
        self.lb_esp.delete(0, 'end')
        for e in self.p.cond['espacios']:
            self.lb_esp.insert('end', f"{e['nombre']} · {e.get('capacidad', 1)} curso(s)")

    def _editar_materia(self, ev):
        mid = self.tv_mat.identify_row(ev.y)
        col = self.tv_mat.identify_column(ev.x)
        if not mid:
            return
        r = self.p.regla(int(mid))
        if col == '#3':
            t = simpledialog.askstring(TITULO, 'Bloques de la materia (ej.: 2+2 ó 2+1). Vacío = horas sueltas:',
                                       initialvalue=r.get('bloques') or '', parent=self)
            if t is not None:
                if t.strip() and not nucleo.patron(t):
                    return messagebox.showwarning(TITULO, 'Escríbalo así: 2+2+1 (bloques de 1 a 4 horas).')
                r['bloques'] = t.strip()
                r.pop('doble', None)
        elif col == '#4':
            n = simpledialog.askinteger(TITULO, 'Máximo de horas por día (0 = el general):',
                                        initialvalue=r.get('max_dia') or 0, minvalue=0, maxvalue=6, parent=self)
            if n is not None:
                r['max_dia'] = n or None
        elif col == '#5':
            r['primeras'] = not r.get('primeras')
        elif col == '#6':
            r['ultimas'] = not r.get('ultimas')
        elif col == '#7':
            nombres = [e['nombre'] for e in self.p.cond['espacios']]
            if not nombres:
                return messagebox.showinfo(TITULO, 'Primero agregue los espacios (a la derecha).')
            t = simpledialog.askstring(TITULO, 'Espacio que necesita (vacío = ninguno):\n' + ', '.join(nombres),
                                       initialvalue=r.get('espacio') or '', parent=self)
            if t is not None:
                if t.strip() and t.strip() not in nombres:
                    return messagebox.showwarning(TITULO, 'Escriba el nombre tal como está en la lista de espacios.')
                r['espacio'] = t.strip()
        self._llenar_materias()

    def _agregar_espacio(self):
        n = simpledialog.askstring(TITULO, 'Nombre del espacio (ej.: Sala de sistemas):', parent=self)
        if not n or not n.strip():
            return
        cap = simpledialog.askinteger(TITULO, '¿Cuántos cursos caben a la vez?', initialvalue=1, minvalue=1, maxvalue=10,
                                      parent=self) or 1
        self.p.cond['espacios'].append({'nombre': n.strip(), 'capacidad': cap})
        self._llenar_materias()

    def _quitar_espacio(self):
        sel = self.lb_esp.curselection()
        if sel:
            del self.p.cond['espacios'][sel[0]]
            self._llenar_materias()

    # --- 3. Docentes --------------------------------------------------------
    def tab_docentes(self):
        f = ttk.Frame(self.nb, padding=10)
        self.nb.add(f, text='3. Docentes y cursos')
        izq = ttk.Frame(f)
        izq.pack(side='left', fill='y')
        ttk.Label(izq, text='Docentes y, al final, cursos').pack(anchor='w')
        self.lb_doc = tk.Listbox(izq, width=34, exportselection=False)
        self.lb_doc.pack(fill='y', expand=True)
        con_clases = {a.get('docente') for a in self.p.datos.asignaciones.values()}
        self.docs = [d for d in sorted(self.p.datos.docentes.values(), key=lambda d: d['nombre']) if d['id'] in con_clases]
        self.cursos_l = [c for c in self.p.datos.crudo['cursos'] if c['id'] in self.p.datos.jornada_de_curso]
        disp = self.p.disponibilidad_plataforma()
        for d in self.docs:
            self.lb_doc.insert('end', d['nombre'] + ('  ✉' if d['id'] in disp else ''))
        for c in self.cursos_l:
            self.lb_doc.insert('end', f'Curso {c["nombre"]}')
            self.lb_doc.itemconfig('end', foreground='#3730a3')
        self.lb_doc.bind('<<ListboxSelect>>', lambda e: self._ver_docente())
        if disp:
            ttk.Label(izq, text=f'✉ = marcó su disponibilidad en la plataforma ({len(disp)})', style='Ayuda.TLabel').pack(anchor='w')
            ttk.Button(izq, text='Volver a traer la disponibilidad', command=self._traer_disp).pack(fill='x', pady=2)
        self.panel_doc = ttk.Frame(f, padding=(14, 0))
        self.panel_doc.pack(side='left', fill='both', expand=True)
        ttk.Label(self.panel_doc, text='Escoja un docente.', style='Ayuda.TLabel').pack(anchor='w')

    def _traer_disp(self):
        if messagebox.askyesno(TITULO, 'Se reemplazan las horas marcadas aquí por las que cada docente marcó en la '
                                       'plataforma. ¿Seguir?'):
            n = self.p.traer_disponibilidad()
            self.avisar(f'Disponibilidad de {n} docente(s) actualizada.')
            self._ver_docente()

    def _ver_docente(self):
        sel = self.lb_doc.curselection()
        if not sel:
            return
        for w in self.panel_doc.winfo_children():
            w.destroy()
        if sel[0] >= len(self.docs):
            return self._ver_curso(self.cursos_l[sel[0] - len(self.docs)])
        d = self.docs[sel[0]]
        base, extra, sedes = self.p.resumen_docente(d['id'])
        ttk.Label(self.panel_doc, text=d['nombre'], style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(self.panel_doc, text=f'{base} horas de clase' + (f' + {extra} extra' if extra else '') +
                  f' · {", ".join(sedes)}', style='Ayuda.TLabel').pack(anchor='w')
        ttk.Label(self.panel_doc, text='Toque una casilla: verde = puede, rojo = no puede, amarillo = mejor no, '
                                       'naranja = mejor no (fuerte). Toque el día para cambiar el día completo.',
                  style='Ayuda.TLabel').pack(anchor='w', pady=(4, 6))
        r = self.p.docente(d['id'])
        if r.get('nota'):
            ttk.Label(self.panel_doc, text=f'✉ Nota del docente: {r["nota"]}', foreground='#3730a3',
                      wraplength=700).pack(anchor='w', pady=(0, 4))
        for j in self.p.jornadas_de_docente(d['id']):
            ttk.Label(self.panel_doc, text=j['nombre'], style='Sub.TLabel').pack(anchor='w', pady=(6, 2))
            g = tk.Frame(self.panel_doc)
            g.pack(anchor='w')
            for c, dia in enumerate(j['dias'], start=1):
                tk.Button(g, text=nucleo.DIAS[dia], width=11, relief='groove',
                          command=lambda dia=dia: self._dia_docente(d['id'], dia)).grid(row=0, column=c, padx=1)
            fila = 1
            for fr in self.p.datos.franjas_de(j['id']):
                tk.Label(g, text=fr['inicio'], width=7, anchor='e').grid(row=fila, column=0, padx=4)
                for c, dia in enumerate(j['dias'], start=1):
                    if fr['descanso']:
                        tk.Label(g, text='descanso', fg='#999', width=11).grid(row=fila, column=c)
                        continue
                    est = self.p.estado_celda(d['id'], dia, fr['id'])
                    b = tk.Button(g, width=10, relief='flat', bg=COLOR_ESTADO[est], text=TEXTO_ESTADO[est])
                    b.configure(command=lambda b=b, dia=dia, fid=fr['id']: self._celda_docente(d['id'], dia, fid, b))
                    b.grid(row=fila, column=c, padx=1, pady=1)
                fila += 1
        abajo = ttk.Frame(self.panel_doc)
        abajo.pack(anchor='w', pady=10)

        def guardar(k):
            return lambda v: r.__setitem__(k, v or None)
        self._numero(abajo, 'Máximo de clases por día (0 = sin límite):', r.get('max_dia') or 0, 0, 12,
                     guardar('max_dia')).pack(anchor='w')
        self._numero(abajo, 'Máximo de horas seguidas (0 = la regla general):', r.get('max_seguidas') or 0, 0, 10,
                     guardar('max_seguidas')).pack(anchor='w', pady=2)
        self._numero(abajo, 'Permanencia de este docente (horas, 0 = la regla general):', r.get('permanencia') or 0, 0, 14,
                     guardar('permanencia'), 0.5).pack(anchor='w')
        var_libre = tk.BooleanVar(value=bool(r.get('dia_libre')))
        ttk.Checkbutton(abajo, text='Pide un día sin clases a la semana (si se puede)', variable=var_libre,
                        command=lambda: r.__setitem__('dia_libre', var_libre.get())).pack(anchor='w', pady=(4, 0))
        ex = self.p.cond.get('excluyente') or {}
        if ex.get('activa'):
            var_sin = tk.BooleanVar(value=bool(r.get('sin_excluyente')))
            ttk.Checkbutton(abajo, text=f'A este docente no se le aplica la regla de la hora {ex.get("b")} y la hora {ex.get("a")}',
                            variable=var_sin, command=lambda: r.__setitem__('sin_excluyente', var_sin.get())).pack(anchor='w')

    def _ver_curso(self, c):
        ttk.Label(self.panel_doc, text=f'Curso {c["nombre"]}', style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(self.panel_doc, text='Marque en rojo las horas en que este curso NO tiene clase (sale temprano, '
                                       'actividad fija, etc.). El generador no le pondrá clases ahí.',
                  style='Ayuda.TLabel', wraplength=700).pack(anchor='w', pady=(4, 6))
        jid = self.p.datos.jornada_de_curso[c['id']]
        j = self.p.datos.jornadas[jid]
        g = tk.Frame(self.panel_doc)
        g.pack(anchor='w')
        for col, dia in enumerate(j['dias'], start=1):
            tk.Label(g, text=nucleo.DIAS[dia], width=11).grid(row=0, column=col)
        for fila, fr in enumerate(self.p.datos.franjas_de(jid), start=1):
            tk.Label(g, text=fr['inicio'], width=7, anchor='e').grid(row=fila, column=0, padx=4)
            for col, dia in enumerate(j['dias'], start=1):
                if fr['descanso']:
                    tk.Label(g, text='descanso', fg='#999', width=11).grid(row=fila, column=col)
                    continue
                no = self.p.celda_curso(c['id'], dia, fr['id'])
                b = tk.Button(g, width=10, relief='flat', bg=ROJO if no else VERDE, text='Sin clase' if no else '')
                b.configure(command=lambda b=b, dia=dia, fid=fr['id']: self._celda_curso(c['id'], dia, fid, b))
                b.grid(row=fila, column=col, padx=1, pady=1)

    def _celda_curso(self, cid, dia, fid, boton):
        no = self.p.alternar_celda_curso(cid, dia, fid)
        boton.configure(bg=ROJO if no else VERDE, text='Sin clase' if no else '')

    def _celda_docente(self, did, dia, fid, boton):
        est = self.p.siguiente_estado(did, dia, fid)
        boton.configure(bg=COLOR_ESTADO[est], text=TEXTO_ESTADO[est])

    def _dia_docente(self, did, dia):
        estados = [self.p.estado_celda(did, dia, f['id']) for j in self.p.jornadas_de_docente(did) if dia in j['dias']
                   for f in j['franjas'] if not f['descanso']]
        nuevo = 'libre' if estados and all(e == 'no_puede' for e in estados) else 'no_puede'
        self.p.marcar_dia(did, dia, nuevo)
        self._ver_docente()

    # --- 4. Reuniones y grupos -----------------------------------------------
    def tab_grupos(self):
        f = ttk.Frame(self.nb, padding=10)
        self.nb.add(f, text='4. Reuniones y clases juntas')
        reu = ttk.LabelFrame(f, text='Reuniones de área: se busca una hora en que puedan todos (o la mayoría); '
                                     'si no, una segunda reunión con el jefe de área', padding=6)
        reu.pack(fill='both', expand=True)
        marco, self.tv_reu = self._tabla(reu, [('nombre', 'Reunión', 200), ('docentes', 'Docentes', 70),
                                               ('jefe', 'Jefe de área', 180), ('hora', 'Hora', 360)], 7)
        marco.pack(fill='both', expand=True)
        bot = ttk.Frame(reu)
        bot.pack(fill='x', pady=4)
        ttk.Button(bot, text='Crear una por área', command=self._reuniones_area).pack(side='left')
        ttk.Button(bot, text='Nueva', command=lambda: self._editar_reunion(None)).pack(side='left', padx=4)
        ttk.Button(bot, text='Editar', command=self._editar_reunion_sel).pack(side='left')
        ttk.Button(bot, text='Quitar', command=self._quitar_reunion).pack(side='left', padx=4)
        ttk.Button(bot, text='🔎 Buscar horas', command=self._llenar_grupos).pack(side='left')
        sim = ttk.LabelFrame(f, text='Clases simultáneas: van a la misma hora (inglés por niveles, media técnica, '
                                     'educación física de dos cursos…)', padding=6)
        sim.pack(fill='both', expand=True, pady=(8, 0))
        marco, self.tv_sim = self._tabla(sim, [('nombre', 'Nombre', 200), ('clases', 'Clases', 620)], 6)
        marco.pack(fill='both', expand=True)
        bot = ttk.Frame(sim)
        bot.pack(fill='x', pady=4)
        ttk.Button(bot, text='Nueva', command=self._nueva_simultanea).pack(side='left')
        ttk.Button(bot, text='Quitar', command=self._quitar_simultanea).pack(side='left', padx=4)
        self._llenar_grupos()

    def _llenar_grupos(self):
        D = self.p.datos
        horas = {r['nombre']: r for r in self.p.ver_reuniones()}
        self.tv_reu.delete(*self.tv_reu.get_children())
        for i, r in enumerate(self.p.cond['reuniones']):
            h = horas.get(r.get('nombre') or 'Reunión de área')
            texto = '—'
            if h:
                texto = self.p.texto_reuniones({'reuniones': [h]})[0].split(': ', 1)[-1]
            self.tv_reu.insert('', 'end', iid=str(i), values=(r.get('nombre'), len(r.get('docentes', [])),
                                                              D.nombre_docente(r.get('jefe')) if r.get('jefe') else '—', texto))
        self.tv_sim.delete(*self.tv_sim.get_children())
        for i, g in enumerate(self.p.cond['simultaneas']):
            clases = [f"{D.nombre_curso(D.asignaciones[a]['curso'])} {D.nombre_materia(D.asignaciones[a]['materia'])}"
                      for a in g['asignaciones'] if a in D.asignaciones]
            self.tv_sim.insert('', 'end', iid=str(i), values=(g.get('nombre'), ' + '.join(clases)))

    def _reuniones_area(self):
        n = self.p.reuniones_por_area()
        if not n:
            messagebox.showinfo(TITULO, 'No hay áreas nuevas con dos o más docentes. Revise que las materias tengan '
                                        'su área en la plataforma.')
        self._llenar_grupos()
        self.avisar(f'{n} reunión(es) creada(s). Escoja el jefe de área de cada una con «Editar».')

    def _editar_reunion_sel(self):
        sel = self.tv_reu.focus()
        if sel:
            self._editar_reunion(int(sel))

    def _editar_reunion(self, i):
        D = self.p.datos
        r = self.p.cond['reuniones'][i] if i is not None else {'nombre': 'Reunión de área', 'docentes': [], 'jefe': None,
                                                               'modo': 'auto', 'dos': True}
        v = tk.Toplevel(self)
        v.title('Reunión de área')
        v.transient(self)
        v.grab_set()
        cuerpo = ttk.Frame(v, padding=12)
        cuerpo.pack(fill='both', expand=True)
        ttk.Label(cuerpo, text='Nombre').grid(row=0, column=0, sticky='w')
        e_nom = ttk.Entry(cuerpo, width=40)
        e_nom.insert(0, r.get('nombre') or '')
        e_nom.grid(row=0, column=1, sticky='w')
        docs = sorted(D.docentes.values(), key=lambda d: d['nombre'])
        ttk.Label(cuerpo, text='Docentes (Ctrl + clic para escoger varios)').grid(row=1, column=0, columnspan=2, sticky='w', pady=(8, 2))
        lb = tk.Listbox(cuerpo, selectmode='extended', height=12, width=50, exportselection=False)
        for k, d in enumerate(docs):
            lb.insert('end', d['nombre'])
            if d['id'] in r.get('docentes', []):
                lb.selection_set(k)
        lb.grid(row=2, column=0, columnspan=2, sticky='we')
        ttk.Label(cuerpo, text='Jefe de área').grid(row=3, column=0, sticky='w', pady=(8, 0))
        cb_jefe = ttk.Combobox(cuerpo, state='readonly', width=37, values=['(ninguno)'] + [d['nombre'] for d in docs])
        cb_jefe.current(next((k + 1 for k, d in enumerate(docs) if d['id'] == r.get('jefe')), 0))
        cb_jefe.grid(row=3, column=1, sticky='w', pady=(8, 0))
        var_dos = tk.BooleanVar(value=r.get('dos', True))
        ttk.Checkbutton(cuerpo, text='Si no pueden todos, hacer una segunda reunión con el jefe', variable=var_dos).grid(
            row=4, column=0, columnspan=2, sticky='w', pady=4)
        var_fija = tk.BooleanVar(value=r.get('modo') == 'fija')
        ttk.Checkbutton(cuerpo, text='Poner yo el día y la hora:', variable=var_fija).grid(row=5, column=0, sticky='w')
        fila = ttk.Frame(cuerpo)
        fila.grid(row=5, column=1, sticky='w')
        cb_dia = ttk.Combobox(fila, state='readonly', width=11, values=[nucleo.DIAS[d] for d in range(1, 7)])
        cb_dia.current(max(0, int(r.get('dia') or 1) - 1))
        cb_dia.pack(side='left')
        horas = sorted({f['inicio'] for f in D.franjas.values() if not f['descanso']})
        cb_hora = ttk.Combobox(fila, state='readonly', width=7, values=horas)
        if r.get('hora') in horas:
            cb_hora.set(r['hora'])
        elif horas:
            cb_hora.current(len(horas) - 1)
        cb_hora.pack(side='left', padx=4)

        def aceptar():
            r['nombre'] = e_nom.get().strip() or 'Reunión de área'
            r['docentes'] = [docs[k]['id'] for k in lb.curselection()]
            r['jefe'] = docs[cb_jefe.current() - 1]['id'] if cb_jefe.current() > 0 else None
            r['dos'] = var_dos.get()
            r['modo'] = 'fija' if var_fija.get() else 'auto'
            r['dia'] = cb_dia.current() + 1
            r['hora'] = cb_hora.get()
            if i is None:
                self.p.cond['reuniones'].append(r)
            v.destroy()
            self._llenar_grupos()
        ttk.Button(cuerpo, text='Guardar', command=aceptar).grid(row=6, column=1, sticky='e', pady=10)

    def _quitar_reunion(self):
        sel = self.tv_reu.focus()
        if sel:
            del self.p.cond['reuniones'][int(sel)]
            self._llenar_grupos()

    def _nueva_simultanea(self):
        D = self.p.datos
        asigs = sorted(D.asignaciones.values(), key=lambda a: (D.nombre_materia(a['materia']), D.nombre_curso(a['curso'])))
        v = tk.Toplevel(self)
        v.title('Clases simultáneas')
        v.transient(self)
        v.grab_set()
        cuerpo = ttk.Frame(v, padding=12)
        cuerpo.pack(fill='both', expand=True)
        ttk.Label(cuerpo, text='Nombre (ej.: Inglés por niveles 6.º)').pack(anchor='w')
        e = ttk.Entry(cuerpo, width=50)
        e.pack(anchor='w')
        ttk.Label(cuerpo, text='Escoja las clases que van a la misma hora (Ctrl + clic):').pack(anchor='w', pady=(8, 2))
        lb = tk.Listbox(cuerpo, selectmode='extended', height=16, width=70, exportselection=False)
        for a in asigs:
            lb.insert('end', f"{D.nombre_materia(a['materia'])} · {D.nombre_curso(a['curso'])} · "
                             f"{D.nombre_docente(a.get('docente'))} ({D.ih(a['id'], self.p.cond)} h)")
        lb.pack(fill='both', expand=True)

        def aceptar():
            m = self.p.agregar_simultanea(e.get().strip(), [asigs[k]['id'] for k in lb.curselection()])
            if m and 'Quedó' not in m:
                return messagebox.showwarning(TITULO, m, parent=v)
            if m:
                messagebox.showinfo(TITULO, m, parent=v)
            v.destroy()
            self._llenar_grupos()
        ttk.Button(cuerpo, text='Guardar', command=aceptar).pack(anchor='e', pady=8)

    def _quitar_simultanea(self):
        sel = self.tv_sim.focus()
        if sel:
            del self.p.cond['simultaneas'][int(sel)]
            self._llenar_grupos()

    # --- 5. Otras tareas: actividades complementarias y descansos -------------
    def tab_tareas(self):
        f = ttk.Frame(self.nb, padding=10)
        self.nb.add(f, text='5. Actividades y descansos')
        act = ttk.LabelFrame(f, text='Actividades complementarias: atención a padres, planeación, proyectos… '
                                     'Se ubican después de las clases, primero en los huecos de cada docente.', padding=6)
        act.pack(fill='both', expand=True)
        marco, self.tv_act = self._tabla(act, [('nombre', 'Actividad', 220), ('docentes', 'Docentes', 260),
                                               ('horas', 'Horas/semana', 95), ('max', 'Máx./día', 70)], 6)
        marco.pack(fill='both', expand=True)
        bot = ttk.Frame(act)
        bot.pack(fill='x', pady=4)
        ttk.Button(bot, text='Nueva', command=self._nueva_actividad).pack(side='left')
        ttk.Button(bot, text='Quitar', command=self._quitar_actividad).pack(side='left', padx=4)
        des = ttk.LabelFrame(f, text='Acompañamiento de descansos: zonas (patio, tienda, baños…) y cuántos docentes '
                                     'cuidan cada una. Se escogen docentes que tienen clase justo antes o después.', padding=6)
        des.pack(fill='both', expand=True, pady=(8, 0))
        ac = self.p.cond.setdefault('acompanamiento', {'zonas': [], 'max_semana': 2})
        marco, self.tv_zon = self._tabla(des, [('zona', 'Zona', 260), ('cuantos', 'Docentes por descanso', 160)], 5)
        marco.pack(fill='both', expand=True)
        bot = ttk.Frame(des)
        bot.pack(fill='x', pady=4)
        ttk.Button(bot, text='Agregar zona', command=self._nueva_zona).pack(side='left')
        ttk.Button(bot, text='Quitar', command=self._quitar_zona).pack(side='left', padx=4)
        self._numero(bot, '   Máximo de turnos por docente a la semana:', ac.get('max_semana') or 2, 1, 15,
                     lambda v: ac.__setitem__('max_semana', v)).pack(side='left')
        self._llenar_tareas()

    def _llenar_tareas(self):
        D = self.p.datos
        self.tv_act.delete(*self.tv_act.get_children())
        for i, a in enumerate(self.p.cond['actividades']):
            quienes = 'Todos' if not a.get('docentes') else ', '.join(D.nombre_docente(x) for x in a['docentes'][:4]) + (
                f' y {len(a["docentes"]) - 4} más' if len(a['docentes']) > 4 else '')
            self.tv_act.insert('', 'end', iid=str(i), values=(a.get('nombre'), quienes, a.get('horas'), a.get('max_dia') or 1))
        self.tv_zon.delete(*self.tv_zon.get_children())
        for i, z in enumerate(self.p.cond['acompanamiento']['zonas']):
            self.tv_zon.insert('', 'end', iid=str(i), values=(z['nombre'], z.get('cuantos', 1)))

    def _nueva_actividad(self):
        D = self.p.datos
        v = tk.Toplevel(self)
        v.title('Actividad complementaria')
        v.transient(self)
        v.grab_set()
        cuerpo = ttk.Frame(v, padding=12)
        cuerpo.pack(fill='both', expand=True)
        ttk.Label(cuerpo, text='Nombre (ej.: Atención a padres)').grid(row=0, column=0, sticky='w')
        e = ttk.Entry(cuerpo, width=40)
        e.insert(0, 'Atención a padres')
        e.grid(row=0, column=1, sticky='w')
        var_h, var_m = tk.IntVar(value=1), tk.IntVar(value=1)
        ttk.Label(cuerpo, text='Horas a la semana').grid(row=1, column=0, sticky='w', pady=4)
        ttk.Spinbox(cuerpo, from_=1, to=10, width=5, textvariable=var_h).grid(row=1, column=1, sticky='w')
        ttk.Label(cuerpo, text='Máximo por día').grid(row=2, column=0, sticky='w')
        ttk.Spinbox(cuerpo, from_=1, to=6, width=5, textvariable=var_m).grid(row=2, column=1, sticky='w')
        ttk.Label(cuerpo, text='Docentes (ninguno escogido = todos)').grid(row=3, column=0, columnspan=2, sticky='w', pady=(8, 2))
        docs = sorted(D.docentes.values(), key=lambda d: d['nombre'])
        lb = tk.Listbox(cuerpo, selectmode='extended', height=12, width=50, exportselection=False)
        for d in docs:
            lb.insert('end', d['nombre'])
        lb.grid(row=4, column=0, columnspan=2, sticky='we')

        def aceptar():
            try:
                h, m = int(var_h.get()), int(var_m.get())
            except (ValueError, tk.TclError):
                h, m = 1, 1
            self.p.cond['actividades'].append({'nombre': e.get().strip() or 'Actividad', 'horas': max(1, h),
                                               'max_dia': max(1, m), 'docentes': [docs[k]['id'] for k in lb.curselection()]})
            v.destroy()
            self._llenar_tareas()
        ttk.Button(cuerpo, text='Guardar', command=aceptar).grid(row=5, column=1, sticky='e', pady=8)

    def _quitar_actividad(self):
        sel = self.tv_act.focus()
        if sel:
            del self.p.cond['actividades'][int(sel)]
            self._llenar_tareas()

    def _nueva_zona(self):
        n = simpledialog.askstring(TITULO, 'Nombre de la zona (ej.: Patio principal):', parent=self)
        if not n or not n.strip():
            return
        k = simpledialog.askinteger(TITULO, '¿Cuántos docentes la cuidan en cada descanso?', initialvalue=1, minvalue=1,
                                    maxvalue=10, parent=self) or 1
        self.p.cond['acompanamiento']['zonas'].append({'nombre': n.strip(), 'cuantos': k})
        self._llenar_tareas()

    def _quitar_zona(self):
        sel = self.tv_zon.focus()
        if sel:
            del self.p.cond['acompanamiento']['zonas'][int(sel)]
            self._llenar_tareas()

    # --- 6. Horario -----------------------------------------------------------
    def tab_horario(self):
        f = ttk.Frame(self.nb, padding=8)
        self.nb.add(f, text='6. Horario')
        arriba = ttk.Frame(f)
        arriba.pack(fill='x')
        ttk.Button(arriba, text='📝 Horario en blanco (armar a mano)', command=self._en_blanco).pack(side='left')
        ttk.Separator(arriba, orient='vertical').pack(side='left', fill='y', padx=8)
        ttk.Label(arriba, text='Alternativas:').pack(side='left')
        self.var_alt = tk.IntVar(value=3)
        ttk.Spinbox(arriba, from_=1, to=3, width=3, textvariable=self.var_alt).pack(side='left', padx=4)
        ttk.Label(arriba, text='Segundos c/u:').pack(side='left')
        self.var_seg = tk.IntVar(value=60)
        ttk.Spinbox(arriba, from_=15, to=600, increment=15, width=5, textvariable=self.var_seg).pack(side='left', padx=4)
        self.btn_gen = ttk.Button(arriba, text='▶ Generar', command=self.generar)
        self.btn_gen.pack(side='left', padx=6)
        self.barra = ttk.Progressbar(arriba, length=200, mode='determinate')
        self.barra.pack(side='left')
        self.lbl_prog = ttk.Label(arriba, text='', style='Ayuda.TLabel')
        self.lbl_prog.pack(side='left', padx=6)

        cuerpo = ttk.Panedwindow(f, orient='horizontal')
        cuerpo.pack(fill='both', expand=True, pady=6)
        izq = ttk.Frame(cuerpo)
        cuerpo.add(izq, weight=1)
        marco, self.tv_alt = self._tabla(izq, [('alt', 'Horario', 150), ('sin', 'Faltan', 50), ('huecos', 'Huecos', 55)], 6)
        marco.pack(fill='x')
        self.tv_alt.bind('<<TreeviewSelect>>', lambda e: self._ver())
        for texto, cmd in (('Completar lo que falta', self._completar),
                           ('Regenerar lo no fijado', lambda: self._completar(solo_fijadas=True)),
                           ('💾 Guardar para la plataforma (.mchr)', self._exportar),
                           ('Exportar a Excel', self._excel), ('Quitar este horario', self._quitar_alt)):
            ttk.Button(izq, text=texto, command=cmd).pack(fill='x', pady=1)
        ttk.Label(izq, text='Avisos', style='Sub.TLabel').pack(anchor='w', pady=(8, 0))
        self.txt_avisos = tk.Text(izq, wrap='word', height=14, width=34, relief='flat', background=GRIS, font=('Segoe UI', 9))
        self.txt_avisos.pack(fill='both', expand=True)

        der = ttk.Frame(cuerpo)
        cuerpo.add(der, weight=4)
        sel = ttk.Frame(der)
        sel.pack(fill='x')
        self.cb_ver = ttk.Combobox(sel, state='readonly', values=['Por curso', 'Por docente'], width=12)
        self.cb_ver.current(0)
        self.cb_quien = ttk.Combobox(sel, state='readonly', width=36)
        self.cb_ver.pack(side='left')
        self.cb_quien.pack(side='left', padx=6)
        self.cb_ver.bind('<<ComboboxSelected>>', lambda e: self._opciones_ver())
        self.cb_quien.bind('<<ComboboxSelected>>', lambda e: self._ver())
        ttk.Label(sel, text='Arme por curso o por docente: arrastre las fichas (sobre otra: intercambiar). Clic derecho: fijar o quitar. 🔒 = fijada.',
                  style='Ayuda.TLabel').pack(side='left', padx=8)
        abajo = ttk.Frame(der)
        abajo.pack(fill='both', expand=True, pady=4)
        self.paleta = tk.Frame(abajo, background=GRIS, width=190)
        self.paleta.pack(side='left', fill='y')
        self.paleta.pack_propagate(False)
        self.paleta.destino = ('paleta',)
        marco = ttk.Frame(abajo)
        marco.pack(side='left', fill='both', expand=True, padx=(6, 0))
        self.lienzo = tk.Canvas(marco, background=BLANCO, highlightthickness=0)
        sy = ttk.Scrollbar(marco, orient='vertical', command=self.lienzo.yview)
        self.lienzo.configure(yscrollcommand=sy.set)
        sy.pack(side='right', fill='y')
        self.lienzo.pack(side='left', fill='both', expand=True)
        self.rejilla = tk.Frame(self.lienzo, background=BLANCO)
        self.lienzo.create_window((0, 0), window=self.rejilla, anchor='nw')
        self.rejilla.bind('<Configure>', lambda e: self.lienzo.configure(scrollregion=self.lienzo.bbox('all')))
        self._opciones_ver()
        self._llenar_alternativas()

    def _en_blanco(self):
        self.p.en_blanco()
        self._llenar_alternativas()
        self.avisar('Horario en blanco: arrastre las fichas de la izquierda a la cuadrícula.')

    def generar(self):
        if self.generando:
            return
        errores = [t for n, t in nucleo.diagnostico(self.p.datos, self.p.cond) if n == 'error']
        if errores and not messagebox.askyesno(TITULO, 'Hay problemas en los datos:\n\n' + '\n'.join(errores[:6]) +
                                               '\n\nAsí pueden quedar clases sin ubicar. ¿Generar de todas formas?'):
            return
        base = self._alt()
        fijadas = sum(1 for s in (base or {}).get('sesiones', []) if s.get('fijada'))
        if fijadas and not messagebox.askyesno(TITULO, f'Se van a respetar las {fijadas} fichas fijadas (🔒) del '
                                                        f'horario «{base["nombre"]}». ¿Seguir?'):
            base = None
        self._lanzar(lambda av: self.p.generar(max(1, min(3, self.var_alt.get())), max(5, self.var_seg.get()), av,
                                               base=base if fijadas else None))

    def _completar(self, solo_fijadas=False):
        alt = self._alt()
        if not alt:
            return messagebox.showinfo(TITULO, 'Escoja un horario de la lista.')
        self._lanzar(lambda av: self.p.completar(alt, max(5, self.var_seg.get()), av, solo_fijadas=solo_fijadas))

    def _lanzar(self, trabajo):
        self.generando = True
        self.btn_gen.configure(state='disabled')

        def correr():
            try:
                trabajo(lambda pct, txt: self.cola.put(('avance', pct, txt)))
                self.cola.put(('listo', None, None))
            except Exception as e:
                self.cola.put(('error', 0, str(e)))
        threading.Thread(target=correr, daemon=True).start()
        self.after(200, self._revisar_cola)

    def _revisar_cola(self):
        try:
            while True:
                tipo, pct, txt = self.cola.get_nowait()
                if tipo == 'avance':
                    self.barra['value'] = pct
                    self.lbl_prog.configure(text=txt)
                else:
                    self.generando = False
                    self.btn_gen.configure(state='normal')
                    if tipo == 'listo':
                        self.barra['value'] = 100
                        self.lbl_prog.configure(text='Listo')
                        self._llenar_alternativas()
                        self.avisar('Listo. Revise el horario; puede seguir ajustándolo con las fichas.')
                    else:
                        messagebox.showerror(TITULO, f'No se pudo generar: {txt}')
                    return
        except queue.Empty:
            pass
        self.after(200, self._revisar_cola)

    def _llenar_alternativas(self, elegir=0):
        self.tv_alt.delete(*self.tv_alt.get_children())
        for i, a in enumerate(self.p.alternativas):
            self.tv_alt.insert('', 'end', iid=str(i), values=(a.get('nombre'), a.get('horas_sin_ubicar', 0),
                                                              a.get('huecos') if a.get('huecos') is not None else '—'))
        if self.p.alternativas:
            self.tv_alt.selection_set(str(min(elegir, len(self.p.alternativas) - 1)))
        else:
            self._ver()

    def _alt(self):
        sel = self.tv_alt.selection() if hasattr(self, 'tv_alt') else ()
        return self.p.alternativas[int(sel[0])] if sel and int(sel[0]) < len(self.p.alternativas) else None

    def _opciones_ver(self):
        D = self.p.datos
        if self.cb_ver.current() == 1:
            self.quien_l = [('d', d['id']) for d in sorted(D.docentes.values(), key=lambda d: d['nombre'])
                            if d['id'] in {a.get('docente') for a in D.asignaciones.values()}]
            nombres = [D.nombre_docente(x) for _, x in self.quien_l]
        else:
            self.quien_l = [('c', c['id']) for c in D.crudo['cursos'] if c['id'] in D.jornada_de_curso]
            nombres = [D.nombre_curso(x) for _, x in self.quien_l]
        self.cb_quien.configure(values=nombres)
        if nombres:
            self.cb_quien.current(0)
        self._ver()

    def _ver(self):
        for w in list(self.rejilla.winfo_children()) + list(self.paleta.winfo_children()):
            w.destroy()
        alt = self._alt()
        self._avisos(alt)
        if not alt or self.cb_quien.current() < 0:
            tk.Label(self.rejilla, text='Genere un horario o cree uno en blanco para verlo aquí.', bg=BLANCO,
                     fg='#666').grid(padx=20, pady=20)
            return
        tipo, ident = self.quien_l[self.cb_quien.current()]
        editable = True                      # se arma igual desde un curso o desde un docente
        D = self.p.datos
        tk.Label(self.paleta, text='Fichas por ubicar', bg=GRIS, font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=6, pady=4)
        if tipo == 'c':
            pend = self.p.pendientes(alt, ident)
            textos = [f"{D.nombre_materia(a['materia'])} ×{n}\n{D.nombre_docente(a.get('docente'))}" for a, n in pend]
        else:
            pend = self.p.pendientes_docente(alt, ident)
            textos = [f"{D.nombre_curso(a['curso'])} · {D.nombre_materia(a['materia'])} ×{n}" for a, n in pend]
        for (a, n), texto in zip(pend, textos):
            self._ficha(self.paleta, texto, SUELTA, {'tipo': 'nueva', 'asig': a['id']}).pack(fill='x', padx=6, pady=2)
        if not pend:
            tk.Label(self.paleta, text='✔ Todas ubicadas', bg=GRIS, fg='#14532d').pack(anchor='w', padx=6)
        tk.Label(self.paleta, text='Suelte aquí una ficha\npara sacarla del horario.', bg=GRIS, fg='#888',
                 font=('Segoe UI', 8)).pack(side='bottom', pady=6)
        tablas = [self.p.tabla_curso(alt, ident)] if tipo == 'c' else self.p.tablas_docente(alt, ident)
        fila = 0
        for t in tablas:
            if not t:
                continue
            if len(tablas) > 1:
                tk.Label(self.rejilla, text=t['jornada']['nombre'], font=('Segoe UI', 10, 'bold'), bg=BLANCO).grid(
                    row=fila, column=0, sticky='w', pady=(8, 2))
                fila += 1
            for c, (_, nombre) in enumerate(t['dias'], start=1):
                tk.Label(self.rejilla, text=nombre, font=('Segoe UI', 9, 'bold'), bg=AZUL, fg='white', width=19).grid(
                    row=fila, column=c, padx=1, pady=1, sticky='nsew')
            fila += 1
            for fr, celdas in t['filas']:
                tk.Label(self.rejilla, text=f"{fr['inicio']}\n{fr['fin']}", bg=BLANCO, fg='#555', width=6).grid(row=fila, column=0)
                if fr['descanso'] and not any(celdas):
                    tk.Label(self.rejilla, text=fr.get('etiqueta') or 'Descanso', bg=GRIS, fg='#888').grid(
                        row=fila, column=1, columnspan=len(t['dias']), sticky='nsew', padx=1, pady=1)
                elif fr['descanso']:
                    for c, xs in enumerate(celdas, start=1):
                        texto = '\n'.join(f"{x['titulo']}" for x in xs) or (fr.get('etiqueta') or 'Descanso')
                        tk.Label(self.rejilla, text=texto, bg=TURNO if xs else GRIS, fg='#0f172a' if xs else '#888',
                                 font=('Segoe UI', 8)).grid(row=fila, column=c, sticky='nsew', padx=1, pady=1)
                else:
                    for c, ((dia, _), xs) in enumerate(zip(t['dias'], celdas), start=1):
                        celda = tk.Frame(self.rejilla, bg=GRIS if not xs else BLANCO, width=150, height=48,
                                         highlightthickness=1, highlightbackground='#e2e8f0')
                        celda.grid(row=fila, column=c, padx=1, pady=1, sticky='nsew')
                        celda.grid_propagate(False)
                        celda.pack_propagate(False)
                        celda.destino = ('celda', dia, fr['id'])
                        for x in xs:
                            color = (REUNION if x.get('reunion') else ACTIVIDAD if x.get('actividad')
                                     else FIJA if x['fijada'] else SUELTA)
                            texto = ('🔒 ' if x.get('i') is not None and x['fijada'] else '') + f"{x['titulo']}\n{x['sub']}"
                            datos = {'tipo': 'puesta', 'i': x['i']} if editable and x.get('i') is not None else None
                            self._ficha(celda, texto, color, datos).pack(fill='both', expand=True)
                fila += 1

    def _avisos(self, alt):
        t = self.txt_avisos
        t.config(state='normal')
        t.delete('1.0', 'end')
        if alt:
            sin = self.p.sin_ubicar_texto(alt)
            t.insert('end', f"Horas sin ubicar: {alt.get('horas_sin_ubicar', 0)}\n")
            for x in sin[:12]:
                t.insert('end', f'  • {x}\n')
            for c in alt.get('choques', [])[:8]:
                t.insert('end', f'✖ {c}\n')
            reus = self.p.texto_reuniones(alt)
            if reus:
                t.insert('end', '\nReuniones:\n')
                for r in reus:
                    t.insert('end', f'  • {r}\n')
            dif = self.p.texto_dificiles(alt)
            if dif and alt.get('horas_sin_ubicar'):
                t.insert('end', '\nLo que más costó ubicar (revise sus condiciones):\n')
                for x in dif[:6]:
                    t.insert('end', f'  • {x}\n')
            if alt.get('actividades'):
                t.insert('end', f"\nActividades complementarias ubicadas: {len(alt['actividades'])}\n")
            if alt.get('acompanamientos'):
                t.insert('end', f"Turnos de descanso repartidos: {len(alt['acompanamientos'])} (véalos por docente o en Excel)\n")
            for x in (alt.get('avisos_extra') or [])[:8]:
                t.insert('end', f'⚠ {x}\n')
            if alt.get('divididas'):
                D = self.p.datos
                t.insert('end', '\nBloques que se partieron porque no cabían:\n')
                for a in alt['divididas']:
                    if a in D.asignaciones:
                        t.insert('end', f"  • {D.nombre_materia(D.asignaciones[a]['materia'])} "
                                        f"{D.nombre_curso(D.asignaciones[a]['curso'])}\n")
        t.config(state='disabled')

    # Fichas que se arrastran
    def _ficha(self, padre, texto, color, datos):
        lbl = tk.Label(padre, text=texto, bg=color, font=('Segoe UI', 8), justify='center', wraplength=140,
                       relief='raised' if datos else 'flat', bd=1, cursor='hand2' if datos else '')
        if datos:
            lbl.bind('<ButtonPress-1>', lambda e: self._tomar(e, datos, texto, color))
            lbl.bind('<B1-Motion>', self._arrastrar)
            lbl.bind('<ButtonRelease-1>', self._soltar_evento)
            if datos['tipo'] == 'puesta':
                lbl.bind('<Button-3>', lambda e: self._menu_ficha(e, datos['i']))
        return lbl

    def _tomar(self, e, datos, texto, color):
        self._arr = {'datos': datos, 'x': e.x_root, 'y': e.y_root, 'texto': texto, 'color': color, 'ventana': None}

    def _arrastrar(self, e):
        a = self._arr
        if not a:
            return
        if a['ventana'] is None and abs(e.x_root - a['x']) + abs(e.y_root - a['y']) > 6:
            v = tk.Toplevel(self)
            v.overrideredirect(True)
            v.attributes('-topmost', True)
            tk.Label(v, text=a['texto'], bg=a['color'], font=('Segoe UI', 8), relief='solid', bd=1, padx=6, pady=3).pack()
            a['ventana'] = v
        if a['ventana'] is not None:
            a['ventana'].geometry(f'+{e.x_root + 8}+{e.y_root + 8}')

    def _soltar_evento(self, e):
        a, self._arr = self._arr, None
        if not a or a['ventana'] is None:
            return
        a['ventana'].destroy()
        w = self.winfo_containing(e.x_root, e.y_root)
        while w is not None and not hasattr(w, 'destino'):
            w = w.master
        if w is not None:
            self.soltar(a['datos'], w.destino)

    def soltar(self, datos, destino):
        """Aplica una ficha soltada en una celda o en la paleta."""
        alt = self._alt()
        if not alt:
            return
        motivo = None
        if destino[0] == 'paleta':
            if datos['tipo'] == 'puesta':
                self.p.quitar_ficha(alt, datos['i'])
                self.avisar('Ficha sacada del horario.')
        elif datos['tipo'] == 'nueva':
            motivo = self.p.poner_ficha(alt, datos['asig'], destino[1], destino[2])
        else:
            motivo = self.p.mover_ficha(alt, datos['i'], destino[1], destino[2])
            if motivo and ('ya tiene' in motivo or 'ya está en' in motivo) and messagebox.askyesno(
                    TITULO, motivo + '\n\n¿Intercambiar las dos fichas de lugar?'):
                motivo = self.p.intercambiar(alt, datos['i'], destino[1], destino[2])
                if not motivo:
                    self.avisar('✔ Fichas intercambiadas.')
                    self._actualizar_fila()
                    return self._ver()
        if motivo:
            self.avisar('✖ ' + motivo, error=True)
            self.bell()
        elif destino[0] == 'celda':
            self.avisar('✔ Ficha ubicada y fijada (🔒).')
        self._actualizar_fila()
        self._ver()

    def _actualizar_fila(self):
        alt = self._alt()
        sel = self.tv_alt.selection()
        if alt and sel:
            self.tv_alt.item(sel[0], values=(alt.get('nombre'), alt.get('horas_sin_ubicar', 0),
                                             alt.get('huecos') if alt.get('huecos') is not None else '—'))

    def _menu_ficha(self, e, i):
        alt = self._alt()
        if not alt:
            return
        m = tk.Menu(self, tearoff=0)
        fijada = alt['sesiones'][i].get('fijada')
        m.add_command(label='Soltar (el generador la puede mover)' if fijada else 'Fijar 🔒 (el generador no la mueve)',
                      command=lambda: (self.p.alternar_fijada(alt, i), self._ver()))
        m.add_command(label='Quitar del horario', command=lambda: self.soltar({'tipo': 'puesta', 'i': i}, ('paleta',)))
        m.tk_popup(e.x_root, e.y_root)

    def _exportar(self):
        alt = self._alt()
        if not alt:
            return messagebox.showwarning(TITULO, 'Escoja un horario de la lista.')
        if alt.get('choques'):
            return messagebox.showwarning(TITULO, 'Este horario tiene choques: corríjalos antes de guardarlo.')
        if alt.get('horas_sin_ubicar') and not messagebox.askyesno(
                TITULO, f"Quedan {alt['horas_sin_ubicar']} horas sin ubicar. ¿Guardarlo de todas formas?"):
            return
        nombre = alt.get('nombre', 'horario').replace(' ', '_').replace('(', '').replace(')', '').lower()
        ruta = filedialog.asksaveasfilename(title='Guardar para la plataforma', defaultextension='.mchr',
                                            filetypes=[('Horario para mcolegio', '*.mchr')], initialfile=f'{nombre}.mchr')
        if ruta:
            self.p.exportar_resultado(alt, ruta)
            messagebox.showinfo(TITULO, 'Listo. Súbalo en la plataforma: Horarios → Importar un horario.')

    def _excel(self):
        alt = self._alt()
        if not alt:
            return
        ruta = filedialog.asksaveasfilename(title='Exportar a Excel', defaultextension='.xlsx',
                                            filetypes=[('Excel', '*.xlsx')], initialfile='horario.xlsx')
        if ruta:
            try:
                self.p.exportar_excel(alt, ruta)
                self.avisar('Excel guardado.')
            except Exception as e:
                messagebox.showerror(TITULO, f'No se pudo guardar el Excel: {e}')

    def _quitar_alt(self):
        sel = self.tv_alt.selection()
        if sel and messagebox.askyesno(TITULO, '¿Quitar este horario de la lista?'):
            del self.p.alternativas[int(sel[0])]
            self._llenar_alternativas()


def main():
    App().mainloop()


if __name__ == '__main__':
    main()
