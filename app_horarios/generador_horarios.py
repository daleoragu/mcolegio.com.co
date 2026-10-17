"""mcolegio · Generador de horarios (aplicación de Windows).

Funciona sin internet:
  1. Abra el archivo de datos (.mch) que descargó de la plataforma.
  2. Ponga las condiciones: materias, docentes y clases fijadas.
  3. Genere hasta 3 alternativas y revíselas por curso o por docente.
  4. Guarde la que más le guste (.mchr) y súbala en la plataforma.

Todo el trabajo se puede guardar como proyecto (.mchp) y seguir otro día.
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

VERSION = '1.0'
TITULO = 'mcolegio · Generador de horarios'
AZUL, AZUL_CLARO, ROJO, VERDE, GRIS = '#3730a3', '#eef2ff', '#fde2e1', '#dcfce7', '#f1f5f9'


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITULO)
        self.geometry('1180x760')
        self.minsize(980, 620)
        self.p = None
        self.cola = queue.Queue()
        self.generando = False
        estilo = ttk.Style(self)
        try:
            estilo.theme_use('vista')
        except tk.TclError:
            estilo.theme_use('clam')
        estilo.configure('Titulo.TLabel', font=('Segoe UI', 13, 'bold'))
        estilo.configure('Ayuda.TLabel', foreground='#555')
        estilo.configure('Treeview', rowheight=24)
        self._barra()
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill='both', expand=True, padx=8, pady=(0, 8))
        self._bienvenida()
        self.protocol('WM_DELETE_WINDOW', self.salir)

    # ------------------------------------------------------------------
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
                 '2. Aquí, toque «Abrir datos del colegio» y escoja ese archivo.\n'
                 '3. Revise los datos y ponga las condiciones (materias, docentes, clases fijas).\n'
                 '4. En «Generar», cree las alternativas y revíselas.\n'
                 '5. Guarde la que escoja «para la plataforma» (.mchr) y súbala en Horarios → Importar.\n\n'
                 'Guarde el proyecto para seguir otro día sin perder las condiciones.')
        ttk.Label(f, text=texto, justify='left').pack(anchor='w', pady=12)
        ttk.Label(f, text=f'Versión {VERSION}', style='Ayuda.TLabel').pack(anchor='w')

    def _limpiar(self):
        for t in self.nb.tabs():
            self.nb.forget(t)

    def cargar(self, proyecto):
        self.p = proyecto
        self.lbl_colegio.config(text=self.p.datos.colegio['nombre'])
        self._limpiar()
        self.tab_datos()
        self.tab_materias()
        self.tab_docentes()
        self.tab_fijas()
        self.tab_generar()
        self.nb.select(0)

    # --- Archivos -------------------------------------------------------
    def abrir_datos(self):
        ruta = filedialog.askopenfilename(title='Datos del colegio', filetypes=[('Datos de mcolegio', '*.mch'), ('Todos', '*.*')])
        if not ruta:
            return
        try:
            self.cargar(Proyecto.abrir_datos(ruta))
        except (nucleo.ArchivoInvalido, OSError, KeyError) as e:
            messagebox.showerror(TITULO, f'No se pudo abrir: {e}')

    def abrir_proyecto(self):
        ruta = filedialog.askopenfilename(title='Proyecto', filetypes=[('Proyecto de horario', '*.mchp'), ('Todos', '*.*')])
        if not ruta:
            return
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
            messagebox.showinfo(TITULO, 'Proyecto guardado.')

    def actualizar_datos(self):
        if not self.p:
            return self.abrir_datos()
        ruta = filedialog.askopenfilename(title='Datos nuevos del colegio', filetypes=[('Datos de mcolegio', '*.mch')])
        if ruta:
            try:
                self.cargar(self.p.actualizar_datos(ruta))
                messagebox.showinfo(TITULO, 'Datos actualizados. Se conservaron las condiciones.')
            except (nucleo.ArchivoInvalido, OSError) as e:
                messagebox.showerror(TITULO, str(e))

    def salir(self):
        if self.generando and not messagebox.askyesno(TITULO, 'Se está generando un horario. ¿Salir de todas formas?'):
            return
        self.destroy()

    # --- 1. Datos ---------------------------------------------------------
    def tab_datos(self):
        D = self.p.datos
        f = ttk.Frame(self.nb, padding=10)
        self.nb.add(f, text='1. Revisar datos')
        ttk.Label(f, text='Revise las horas semanales de cada materia (doble clic para cambiarlas).', style='Ayuda.TLabel').pack(anchor='w')
        cuerpo = ttk.Panedwindow(f, orient='horizontal')
        cuerpo.pack(fill='both', expand=True, pady=6)
        izq = ttk.Frame(cuerpo)
        cuerpo.add(izq, weight=3)
        self.tv_asig = ttk.Treeview(izq, columns=('curso', 'materia', 'docente', 'horas'), show='headings')
        for c, t, w in (('curso', 'Curso', 90), ('materia', 'Materia', 200), ('docente', 'Docente', 220), ('horas', 'Horas', 60)):
            self.tv_asig.heading(c, text=t)
            self.tv_asig.column(c, width=w, anchor='center' if c == 'horas' else 'w')
        sb = ttk.Scrollbar(izq, orient='vertical', command=self.tv_asig.yview)
        self.tv_asig.configure(yscrollcommand=sb.set)
        self.tv_asig.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        self.tv_asig.bind('<Double-1>', self._editar_ih)
        der = ttk.Frame(cuerpo, padding=(10, 0))
        cuerpo.add(der, weight=2)
        ttk.Label(der, text='Revisión', style='Titulo.TLabel').pack(anchor='w')
        self.txt_diag = tk.Text(der, wrap='word', height=20, relief='flat', background=GRIS)
        self.txt_diag.pack(fill='both', expand=True)
        self._llenar_datos()

    def _llenar_datos(self):
        D = self.p.datos
        self.tv_asig.delete(*self.tv_asig.get_children())
        orden = {c['id']: i for i, c in enumerate(D.crudo['cursos'])}
        for a in sorted(D.asignaciones.values(), key=lambda a: (orden.get(a['curso'], 0), D.nombre_materia(a['materia']))):
            self.tv_asig.insert('', 'end', iid=str(a['id']), values=(D.nombre_curso(a['curso']), D.nombre_materia(a['materia']),
                                                                     D.nombre_docente(a.get('docente')), D.ih(a['id'], self.p.cond)))
        diag = nucleo.diagnostico(D, self.p.cond)
        self.txt_diag.config(state='normal')
        self.txt_diag.delete('1.0', 'end')
        self.txt_diag.insert('end', f'{len(D.cursos)} cursos · {len(D.docentes)} docentes · {len(D.asignaciones)} asignaciones\n\n')
        if not diag:
            self.txt_diag.insert('end', '✔ Todo listo para generar.\n')
        for nivel, texto in diag:
            self.txt_diag.insert('end', ('✖ ' if nivel == 'error' else '• ') + texto + '\n')
        self.txt_diag.config(state='disabled')

    def _editar_ih(self, _ev):
        sel = self.tv_asig.focus()
        if not sel:
            return
        aid = int(sel)
        n = simpledialog.askinteger(TITULO, 'Horas semanales:', initialvalue=self.p.datos.ih(aid, self.p.cond),
                                    minvalue=0, maxvalue=20, parent=self)
        if n is not None:
            self.p.poner_ih(aid, n)
            self._llenar_datos()

    # --- 2. Materias -------------------------------------------------------
    def tab_materias(self):
        f = ttk.Frame(self.nb, padding=10)
        self.nb.add(f, text='2. Materias')
        arriba = ttk.Frame(f)
        arriba.pack(fill='x')
        ttk.Label(arriba, text='Máximo de horas de una materia en el mismo día (si no se dice otra cosa):').pack(side='left')
        self.var_max = tk.IntVar(value=int(self.p.cond.get('max_por_dia') or 2))
        sp = ttk.Spinbox(arriba, from_=1, to=6, width=4, textvariable=self.var_max,
                         command=lambda: self.p.cond.__setitem__('max_por_dia', self.var_max.get()))
        sp.pack(side='left', padx=6)
        ttk.Label(f, text='Doble clic en una columna para cambiarla.', style='Ayuda.TLabel').pack(anchor='w', pady=(6, 2))
        self.tv_mat = ttk.Treeview(f, columns=('materia', 'doble', 'max', 'primeras'), show='headings')
        for c, t, w in (('materia', 'Materia', 280), ('doble', 'En bloques de 2 horas', 170),
                        ('max', 'Máximo por día', 130), ('primeras', 'Preferir primeras horas', 180)):
            self.tv_mat.heading(c, text=t)
            self.tv_mat.column(c, width=w, anchor='w' if c == 'materia' else 'center')
        self.tv_mat.pack(fill='both', expand=True)
        self.tv_mat.bind('<Double-1>', self._editar_materia)
        self._llenar_materias()

    def _llenar_materias(self):
        D = self.p.datos
        self.tv_mat.delete(*self.tv_mat.get_children())
        for m in sorted(D.materias.values(), key=lambda m: m['nombre']):
            r = self.p.cond['materias'].get(str(m['id']), {})
            self.tv_mat.insert('', 'end', iid=str(m['id']), values=(
                m['nombre'], 'Sí' if r.get('doble') else '—', r.get('max_dia') or 'El general',
                'Sí' if r.get('primeras') else '—'))

    def _editar_materia(self, ev):
        mid = self.tv_mat.identify_row(ev.y)
        col = self.tv_mat.identify_column(ev.x)
        if not mid:
            return
        r = self.p.regla(int(mid))
        if col == '#2':
            r['doble'] = not r.get('doble')
        elif col == '#3':
            n = simpledialog.askinteger(TITULO, 'Máximo de horas por día (0 = el general):',
                                        initialvalue=r.get('max_dia') or 0, minvalue=0, maxvalue=6, parent=self)
            if n is not None:
                r['max_dia'] = n or None
        elif col == '#4':
            r['primeras'] = not r.get('primeras')
        self._llenar_materias()

    # --- 3. Docentes --------------------------------------------------------
    def tab_docentes(self):
        f = ttk.Frame(self.nb, padding=10)
        self.nb.add(f, text='3. Docentes')
        izq = ttk.Frame(f)
        izq.pack(side='left', fill='y')
        ttk.Label(izq, text='Docente').pack(anchor='w')
        self.lb_doc = tk.Listbox(izq, width=34, exportselection=False)
        self.lb_doc.pack(fill='y', expand=True)
        self.docs = sorted(self.p.datos.docentes.values(), key=lambda d: d['nombre'])
        con_clases = {a.get('docente') for a in self.p.datos.asignaciones.values()}
        self.docs = [d for d in self.docs if d['id'] in con_clases]
        for d in self.docs:
            self.lb_doc.insert('end', d['nombre'])
        self.lb_doc.bind('<<ListboxSelect>>', lambda e: self._ver_docente())
        self.panel_doc = ttk.Frame(f, padding=(14, 0))
        self.panel_doc.pack(side='left', fill='both', expand=True)
        ttk.Label(self.panel_doc, text='Escoja un docente para marcar las horas en que NO puede dar clase.',
                  style='Ayuda.TLabel').pack(anchor='w')

    def _ver_docente(self):
        sel = self.lb_doc.curselection()
        if not sel:
            return
        d = self.docs[sel[0]]
        for w in self.panel_doc.winfo_children():
            w.destroy()
        ttk.Label(self.panel_doc, text=d['nombre'], style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(self.panel_doc, text='Toque una casilla para marcarla en rojo (no puede). Otra vez para quitarla.',
                  style='Ayuda.TLabel').pack(anchor='w', pady=(0, 6))
        r = self.p.docente(d['id'])
        no = set(r.get('no_puede', []))
        for j in self.p.jornadas_de_docente(d['id']):
            ttk.Label(self.panel_doc, text=j['nombre']).pack(anchor='w', pady=(6, 2))
            g = tk.Frame(self.panel_doc)
            g.pack(anchor='w')
            for c, dia in enumerate(j['dias'], start=1):
                tk.Label(g, text=nucleo.DIAS[dia][:3], width=11).grid(row=0, column=c)
            fila = 1
            for fr in self.p.datos.franjas_de(j['id']):
                tk.Label(g, text=f"{fr['inicio']}", width=7, anchor='e').grid(row=fila, column=0, padx=4)
                for c, dia in enumerate(j['dias'], start=1):
                    if fr['descanso']:
                        tk.Label(g, text='descanso', fg='#999', width=11).grid(row=fila, column=c)
                        continue
                    clave = f'{dia}-{fr["id"]}'
                    b = tk.Button(g, width=10, relief='flat', bg=ROJO if clave in no else VERDE,
                                  text='No puede' if clave in no else '')
                    b.configure(command=lambda b=b, dia=dia, fid=fr['id']: self._alternar(d['id'], dia, fid, b))
                    b.grid(row=fila, column=c, padx=1, pady=1)
                fila += 1
        abajo = ttk.Frame(self.panel_doc)
        abajo.pack(anchor='w', pady=10)
        ttk.Label(abajo, text='Máximo de clases por día (0 = sin límite):').pack(side='left')
        var = tk.IntVar(value=r.get('max_dia') or 0)
        ttk.Spinbox(abajo, from_=0, to=12, width=4, textvariable=var,
                    command=lambda: r.__setitem__('max_dia', var.get() or None)).pack(side='left', padx=6)

    def _alternar(self, did, dia, fid, boton):
        marcado = self.p.alternar_no_puede(did, dia, fid)
        boton.configure(bg=ROJO if marcado else VERDE, text='No puede' if marcado else '')

    # --- 4. Clases fijas -------------------------------------------------------
    def tab_fijas(self):
        D = self.p.datos
        f = ttk.Frame(self.nb, padding=10)
        self.nb.add(f, text='4. Fijar clases')
        ttk.Label(f, text='Ubique a mano las clases que deben ir en un día y hora exactos. El generador no las mueve.',
                  style='Ayuda.TLabel').pack(anchor='w')
        form = ttk.Frame(f)
        form.pack(fill='x', pady=8)
        self.cursos_l = [c for c in D.crudo['cursos'] if c['id'] in D.jornada_de_curso]
        self.cb_curso = ttk.Combobox(form, state='readonly', width=14, values=[c['nombre'] for c in self.cursos_l])
        self.cb_asig = ttk.Combobox(form, state='readonly', width=42)
        self.cb_dia = ttk.Combobox(form, state='readonly', width=12)
        self.cb_hora = ttk.Combobox(form, state='readonly', width=14)
        for t, w in (('Curso', self.cb_curso), ('Materia y docente', self.cb_asig), ('Día', self.cb_dia), ('Hora', self.cb_hora)):
            ttk.Label(form, text=t).pack(side='left', padx=(8, 2))
            w.pack(side='left')
        ttk.Button(form, text='Fijar', command=self._fijar).pack(side='left', padx=8)
        self.cb_curso.bind('<<ComboboxSelected>>', lambda e: self._curso_fija())
        self.tv_fijas = ttk.Treeview(f, columns=('curso', 'materia', 'docente', 'dia', 'hora'), show='headings')
        for c, t in (('curso', 'Curso'), ('materia', 'Materia'), ('docente', 'Docente'), ('dia', 'Día'), ('hora', 'Hora')):
            self.tv_fijas.heading(c, text=t)
        self.tv_fijas.pack(fill='both', expand=True)
        ttk.Button(f, text='Quitar la seleccionada', command=self._quitar_fija).pack(anchor='e', pady=6)
        self._llenar_fijas()

    def _curso_fija(self):
        D = self.p.datos
        c = self.cursos_l[self.cb_curso.current()]
        self.asig_l = self.p.asignaciones_de_curso(c['id'])
        self.cb_asig.configure(values=[f"{D.nombre_materia(a['materia'])} · {D.nombre_docente(a.get('docente'))}" for a in self.asig_l])
        j = D.jornadas[D.jornada_de_curso[c['id']]]
        self.dias_l = j['dias']
        self.cb_dia.configure(values=[nucleo.DIAS[d] for d in self.dias_l])
        self.horas_l = [fr for fr in D.franjas_de(j['id']) if not fr['descanso']]
        self.cb_hora.configure(values=[f"{i}.ª · {fr['inicio']}" for i, fr in enumerate(self.horas_l, start=1)])
        for cb in (self.cb_asig, self.cb_dia, self.cb_hora):
            cb.set('')

    def _fijar(self):
        if min(self.cb_curso.current(), self.cb_asig.current(), self.cb_dia.current(), self.cb_hora.current()) < 0:
            messagebox.showwarning(TITULO, 'Escoja curso, materia, día y hora.')
            return
        motivo = self.p.agregar_fija(self.asig_l[self.cb_asig.current()]['id'], self.dias_l[self.cb_dia.current()],
                                     self.horas_l[self.cb_hora.current()]['id'])
        if motivo:
            messagebox.showwarning(TITULO, motivo)
        self._llenar_fijas()

    def _llenar_fijas(self):
        D = self.p.datos
        self.tv_fijas.delete(*self.tv_fijas.get_children())
        for i, fx in enumerate(self.p.cond['fijas']):
            a = D.asignaciones.get(int(fx['asignacion']))
            fr = D.franjas.get(int(fx['franja']))
            if a and fr:
                self.tv_fijas.insert('', 'end', iid=str(i), values=(D.nombre_curso(a['curso']), D.nombre_materia(a['materia']),
                                                                    D.nombre_docente(a.get('docente')),
                                                                    nucleo.DIAS[int(fx['dia'])], fr['inicio']))

    def _quitar_fija(self):
        sel = self.tv_fijas.focus()
        if sel:
            self.p.quitar_fija(int(sel))
            self._llenar_fijas()

    # --- 5. Generar y ver -------------------------------------------------------
    def tab_generar(self):
        f = ttk.Frame(self.nb, padding=10)
        self.nb.add(f, text='5. Generar y ver')
        arriba = ttk.Frame(f)
        arriba.pack(fill='x')
        ttk.Label(arriba, text='Alternativas:').pack(side='left')
        self.var_alt = tk.IntVar(value=3)
        ttk.Spinbox(arriba, from_=1, to=3, width=3, textvariable=self.var_alt).pack(side='left', padx=4)
        ttk.Label(arriba, text='Segundos por alternativa:').pack(side='left', padx=(10, 0))
        self.var_seg = tk.IntVar(value=60)
        ttk.Spinbox(arriba, from_=15, to=600, increment=15, width=5, textvariable=self.var_seg).pack(side='left', padx=4)
        self.btn_gen = ttk.Button(arriba, text='▶ Generar', command=self.generar)
        self.btn_gen.pack(side='left', padx=10)
        self.barra = ttk.Progressbar(arriba, length=240, mode='determinate')
        self.barra.pack(side='left')
        self.lbl_estado = ttk.Label(arriba, text='', style='Ayuda.TLabel')
        self.lbl_estado.pack(side='left', padx=8)
        medio = ttk.Frame(f)
        medio.pack(fill='x', pady=8)
        self.tv_alt = ttk.Treeview(medio, columns=('alt', 'sin', 'choques', 'huecos', 'costo'), show='headings', height=3)
        for c, t, w in (('alt', 'Alternativa', 130), ('sin', 'Horas sin ubicar', 130), ('choques', 'Choques', 90),
                        ('huecos', 'Horas sueltas de docentes', 190), ('costo', 'Puntaje (menor es mejor)', 180)):
            self.tv_alt.heading(c, text=t)
            self.tv_alt.column(c, width=w, anchor='center')
        self.tv_alt.pack(side='left', fill='x', expand=True)
        self.tv_alt.bind('<<TreeviewSelect>>', lambda e: self._ver())
        botones = ttk.Frame(medio)
        botones.pack(side='left', padx=8)
        ttk.Button(botones, text='Guardar para la plataforma (.mchr)', command=self._exportar).pack(fill='x')
        ttk.Button(botones, text='Exportar a Excel', command=self._excel).pack(fill='x', pady=4)
        sel = ttk.Frame(f)
        sel.pack(fill='x')
        self.cb_ver = ttk.Combobox(sel, state='readonly', values=['Por curso', 'Por docente'], width=12)
        self.cb_ver.current(0)
        self.cb_quien = ttk.Combobox(sel, state='readonly', width=40)
        self.cb_ver.pack(side='left')
        self.cb_quien.pack(side='left', padx=6)
        self.cb_ver.bind('<<ComboboxSelected>>', lambda e: self._opciones_ver())
        self.cb_quien.bind('<<ComboboxSelected>>', lambda e: self._ver())
        self.lbl_sin = ttk.Label(sel, text='', foreground='#b42318')
        self.lbl_sin.pack(side='left', padx=8)
        marco = ttk.Frame(f)
        marco.pack(fill='both', expand=True, pady=6)
        self.lienzo = tk.Canvas(marco, background='white', highlightthickness=0)
        sy = ttk.Scrollbar(marco, orient='vertical', command=self.lienzo.yview)
        self.lienzo.configure(yscrollcommand=sy.set)
        sy.pack(side='right', fill='y')
        self.lienzo.pack(side='left', fill='both', expand=True)
        self.rejilla = tk.Frame(self.lienzo, background='white')
        self.lienzo.create_window((0, 0), window=self.rejilla, anchor='nw')
        self.rejilla.bind('<Configure>', lambda e: self.lienzo.configure(scrollregion=self.lienzo.bbox('all')))
        self._opciones_ver()
        self._llenar_alternativas()

    def generar(self):
        if self.generando:
            return
        errores = [t for n, t in nucleo.diagnostico(self.p.datos, self.p.cond) if n == 'error']
        if errores and not messagebox.askyesno(TITULO, 'Hay problemas en los datos:\n\n' + '\n'.join(errores[:6]) +
                                               '\n\nAsí es posible que queden clases sin ubicar. ¿Generar de todas formas?'):
            return
        self.generando = True
        self.btn_gen.configure(state='disabled')
        cuantas, seg = max(1, min(3, self.var_alt.get())), max(5, self.var_seg.get())

        def trabajo():
            try:
                self.p.generar(cuantas, seg, avance=lambda pct, txt: self.cola.put(('avance', pct, txt)))
                self.cola.put(('listo', None, None))
            except Exception as e:                  # se muestra en la ventana, no se cae la app
                self.cola.put(('error', 0, str(e)))
        threading.Thread(target=trabajo, daemon=True).start()
        self.after(200, self._revisar_cola)

    def _revisar_cola(self):
        try:
            while True:
                tipo, pct, txt = self.cola.get_nowait()
                if tipo == 'avance':
                    self.barra['value'] = pct
                    self.lbl_estado.configure(text=txt)
                elif tipo == 'listo':
                    self.generando = False
                    self.btn_gen.configure(state='normal')
                    self.barra['value'] = 100
                    self.lbl_estado.configure(text='Listo. Revise las alternativas.')
                    self._llenar_alternativas()
                    return
                elif tipo == 'error':
                    self.generando = False
                    self.btn_gen.configure(state='normal')
                    messagebox.showerror(TITULO, f'No se pudo generar: {txt}')
                    return
        except queue.Empty:
            pass
        self.after(200, self._revisar_cola)

    def _llenar_alternativas(self):
        self.tv_alt.delete(*self.tv_alt.get_children())
        for i, a in enumerate(self.p.alternativas):
            self.tv_alt.insert('', 'end', iid=str(i), values=(a.get('nombre'), a.get('horas_sin_ubicar', 0),
                                                              len(a.get('choques', [])), a.get('huecos', 0), a.get('costo')))
        if self.p.alternativas:
            self.tv_alt.selection_set('0')

    def _alt(self):
        sel = self.tv_alt.selection()
        return self.p.alternativas[int(sel[0])] if sel and self.p.alternativas else None

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
        for w in self.rejilla.winfo_children():
            w.destroy()
        alt = self._alt()
        if not alt or self.cb_quien.current() < 0:
            tk.Label(self.rejilla, text='Genere un horario para verlo aquí.', bg='white', fg='#666').grid(padx=20, pady=20)
            return
        sin = self.p.sin_ubicar_texto(alt)
        self.lbl_sin.configure(text=('Sin ubicar: ' + '; '.join(sin[:4]) + ('…' if len(sin) > 4 else '')) if sin else '')
        tipo, ident = self.quien_l[self.cb_quien.current()]
        tablas = self.p.tablas_docente(alt, ident) if tipo == 'd' else [self.p.tabla_curso(alt, ident)]
        fila = 0
        for t in tablas:
            if not t:
                continue
            if len(tablas) > 1:
                tk.Label(self.rejilla, text=t['jornada']['nombre'], font=('Segoe UI', 10, 'bold'), bg='white').grid(
                    row=fila, column=0, sticky='w', pady=(8, 2))
                fila += 1
            for c, (_, nombre) in enumerate(t['dias'], start=1):
                tk.Label(self.rejilla, text=nombre, font=('Segoe UI', 9, 'bold'), bg=AZUL, fg='white', width=20).grid(
                    row=fila, column=c, padx=1, pady=1, sticky='nsew')
            fila += 1
            for fr, celdas in t['filas']:
                tk.Label(self.rejilla, text=f"{fr['inicio']}\n{fr['fin']}", bg='white', fg='#555', width=7).grid(
                    row=fila, column=0, sticky='e')
                if fr['descanso']:
                    tk.Label(self.rejilla, text=fr.get('etiqueta') or 'Descanso', bg=GRIS, fg='#888').grid(
                        row=fila, column=1, columnspan=len(t['dias']), sticky='nsew', padx=1, pady=1)
                else:
                    for c, x in enumerate(celdas, start=1):
                        texto = '\n'.join(f'{a}\n{b}' for a, b in x)
                        tk.Label(self.rejilla, text=texto, bg=AZUL_CLARO if x else GRIS, width=20, height=3,
                                 font=('Segoe UI', 8), justify='center', wraplength=150).grid(
                            row=fila, column=c, padx=1, pady=1, sticky='nsew')
                fila += 1

    def _exportar(self):
        alt = self._alt()
        if not alt:
            return messagebox.showwarning(TITULO, 'Primero genere y escoja una alternativa.')
        if alt.get('choques'):
            return messagebox.showwarning(TITULO, 'Esta alternativa tiene choques: escoja otra o genere de nuevo.')
        if alt.get('horas_sin_ubicar') and not messagebox.askyesno(
                TITULO, f"Quedan {alt['horas_sin_ubicar']} horas sin ubicar. ¿Guardarla de todas formas?"):
            return
        ruta = filedialog.asksaveasfilename(title='Guardar para la plataforma', defaultextension='.mchr',
                                            filetypes=[('Horario para mcolegio', '*.mchr')],
                                            initialfile=f"horario_{alt.get('nombre', '').replace(' ', '_').lower()}.mchr")
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
                messagebox.showinfo(TITULO, 'Excel guardado.')
            except Exception as e:
                messagebox.showerror(TITULO, f'No se pudo guardar el Excel: {e}')


def main():
    App().mainloop()


if __name__ == '__main__':
    main()
