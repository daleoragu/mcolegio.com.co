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
import copy
import os
import queue
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))

from horarios import impresion, nucleo         # noqa: E402
from horarios.proyecto import Proyecto           # noqa: E402

VERSION = '3.4.1'
TITULO = 'mcolegio · Generador de horarios'
AZUL, AZUL_CLARO, GRIS, BLANCO = '#3730a3', '#e0e7ff', '#f1f5f9', '#ffffff'
VERDE, ROJO, AMARILLO = '#dcfce7', '#fecaca', '#fef08a'
NARANJA = '#fdba74'
FIJA, SUELTA, REUNION = '#c7d2fe', '#ede9fe', '#fde68a'
BLOQUE = '#ddd6fe'
ACTIVIDAD, TURNO = '#bbf7d0', '#a5f3fc'
COLOR_ESTADO = {'libre': VERDE, 'no_puede': ROJO, 'prefiere_no': AMARILLO, 'evitar': NARANJA}
# Colores para distinguir áreas o docentes en la cuadrícula (claros, para que se lea el texto)
PALETA = ['#bfdbfe', '#bbf7d0', '#fde68a', '#fecaca', '#ddd6fe', '#a5f3fc', '#fbcfe8', '#fed7aa', '#d9f99d',
          '#c7d2fe', '#99f6e4', '#f5d0fe', '#e2e8f0', '#fef9c3', '#bae6fd', '#ffe4e6', '#dcfce7', '#e9d5ff']
COLOR_AREA = {'libre': VERDE, 'no_puede': ROJO, 'prefiere_no': AMARILLO}
TEXTO_AREA = {'libre': '', 'no_puede': 'No van', 'prefiere_no': 'Mejor no'}
TEXTO_ESTADO = {'libre': '', 'no_puede': 'No puede', 'prefiere_no': 'Mejor no', 'evitar': 'Mejor no +'}
ICONO = {'error': '✖ ', 'aviso': '⚠ ', 'info': 'ℹ '}
VERDE_SEL, AMARILLO_SEL, ROJO_SEL = '#4ade80', '#facc15', '#f87171'
COLOR_SEL = {'libre': VERDE_SEL, 'ocupado': AMARILLO_SEL, 'imposible': ROJO_SEL}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITULO)
        self.geometry('1260x800')
        self.minsize(1040, 660)
        try:
            self.state('zoomed')            # pantalla completa en Windows
        except tk.TclError:
            pass
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

    # Filtros por grado, área y docente (para las tablas)
    def _filtros(self, padre, cuales, al_cambiar):
        """Una fila de filtros. Devuelve una función acepta(asignacion) -> bool."""
        D = self.p.datos
        fila = ttk.Frame(padre)
        fila.pack(fill='x', pady=(4, 0))
        ttk.Label(fila, text='Filtrar:').pack(side='left')
        cajas = {}
        opciones = {}
        if 'grado' in cuales:
            gs = sorted({c.get('grado') for c in D.crudo['cursos']}, key=lambda g: (g is None, g if g is not None else 0))
            opciones['grado'] = [('', 'Todos los grados')] + [(g, nombre_grado(g)) for g in gs]
        if 'area' in cuales:
            opciones['area'] = [('', 'Todas las áreas')] + [(a, a) for a in sorted(D.areas)]
        if 'materia' in cuales:
            usadas = {a['materia'] for a in D.asignaciones.values()}
            opciones['materia'] = [('', 'Todas las materias')] + sorted(
                ((m, D.nombre_materia(m)) for m in usadas), key=lambda x: x[1])
        if 'docente' in cuales:
            con = {a.get('docente') for a in D.asignaciones.values() if a.get('docente')}
            opciones['docente'] = [('', 'Todos los docentes')] + [
                (d['id'], d['nombre']) for d in sorted(D.docentes.values(), key=lambda d: d['nombre']) if d['id'] in con]
        for clave in cuales:
            if clave == 'buscar':
                continue
            cb = ttk.Combobox(fila, state='readonly', width=24 if clave in ('docente', 'materia') else 18,
                              values=[n for _, n in opciones[clave]])
            cb.current(0)
            cb.pack(side='left', padx=3)
            cb.bind('<<ComboboxSelected>>', lambda e: al_cambiar())
            cajas[clave] = cb
        var_buscar = tk.StringVar()
        if 'buscar' in cuales:
            ttk.Label(fila, text='Buscar:').pack(side='left', padx=(8, 2))
            ttk.Entry(fila, textvariable=var_buscar, width=18).pack(side='left')
            var_buscar.trace_add('write', lambda *_: al_cambiar())

        def valor(clave):
            cb = cajas.get(clave)
            if cb is None:
                return ''
            k = cb.current()
            return opciones[clave][k][0] if k is not None and 0 <= k < len(opciones[clave]) else ''

        def acepta(a=None, materia=None, docente=None, curso=None):
            if a is not None:
                materia, docente, curso = a['materia'], a.get('docente'), a['curso']
            g, ar, d, m = valor('grado'), valor('area'), valor('docente'), valor('materia')
            if m != '' and materia is not None and materia != m:
                return False
            if g != '' and curso is not None and D.cursos.get(curso, {}).get('grado') != g:
                return False
            if ar != '' and materia is not None and D.materias.get(materia, {}).get('area') != ar:
                return False
            if d != '' and docente is not None and docente != d:
                return False
            q = (var_buscar.get() or '').strip().lower()
            if q:
                texto = ' '.join([D.nombre_curso(curso) if curso is not None else '',
                                  D.nombre_materia(materia) if materia is not None else '',
                                  D.nombre_docente(docente) if docente else '']).lower()
                if q not in texto:
                    return False
            return True
        acepta.valor = valor
        return acepta

    # --- 1. Datos ---------------------------------------------------------
    def tab_datos(self):
        f = ttk.Frame(self.nb, padding=10)
        self.nb.add(f, text='1. Datos')
        ttk.Label(f, text='Doble clic en una columna para cambiarla. «Bloques»: cómo se reparten las horas, '
                          'por ejemplo 2+2+1 (vacío = lo de la materia). «Hora extra»: cuántas de esas horas son extra '
                          '(no cuentan en la permanencia).', style='Ayuda.TLabel').pack(anchor='w')
        bot = ttk.Frame(f)
        bot.pack(anchor='w', pady=(4, 0))
        ttk.Button(bot, text='✂ Dividir en bloques automáticamente (2+2+1…)', command=self._dividir_bloques).pack(side='left')
        ttk.Button(bot, text='Quitar todos los bloques', command=self._quitar_bloques).pack(side='left', padx=4)
        ttk.Label(bot, text='Solo llena las clases que no tienen bloques; las que ya tienen se respetan.',
                  style='Ayuda.TLabel').pack(side='left', padx=6)
        self.filtro_datos = self._filtros(f, ('grado', 'area', 'materia', 'docente', 'buscar'), lambda: self._llenar_datos())
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
        filtro = getattr(self, 'filtro_datos', None)
        for a in sorted(D.asignaciones.values(), key=lambda a: (orden.get(a['curso'], 0), D.nombre_materia(a['materia']))):
            if filtro and not filtro(a):
                continue
            r = c['asignaciones'].get(str(a['id']), {})
            self.tv_asig.insert('', 'end', iid=str(a['id']), values=(
                D.nombre_curso(a['curso']), D.nombre_materia(a['materia']), D.nombre_docente(a.get('docente')),
                D.ih(a['id'], c), r.get('bloques') or '',
                (lambda k, n: '' if not k else ('Todas' if k >= n else f'{k} de {n}'))(
                    nucleo.horas_extra(c, a['id'], D.ih(a['id'], c)), D.ih(a['id'], c)),
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

    def _dividir_bloques(self):
        n = self.p.dividir_en_bloques()
        self._llenar_datos()
        self.avisar(f'{n} clase(s) quedaron en bloques de 2 horas. Puede cambiar cualquiera con doble clic en «Bloques».')

    def _quitar_bloques(self):
        if messagebox.askyesno(TITULO, '¿Quitar los bloques de todas las clases? Quedan en horas sueltas '
                                       '(o con los bloques de su materia, si los tiene).'):
            n = self.p.quitar_bloques()
            self._llenar_datos()
            self.avisar(f'Se quitaron los bloques de {n} clase(s).')

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
            ih = self.p.datos.ih(aid, self.p.cond)
            n = simpledialog.askinteger(TITULO, f'¿Cuántas de las {ih} horas son horas extra? (0 = ninguna)\n'
                                                'Las horas extra no cuentan en la permanencia del docente.',
                                        initialvalue=nucleo.horas_extra(self.p.cond, aid, ih), minvalue=0, maxvalue=ih,
                                        parent=self)
            if n is not None:
                r['extra_horas'] = n
                r.pop('extra', None)
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
        self._numero(gen, 'Con horas extra, el día del docente puede alargarse hasta (horas más de la permanencia; '
                          '0 = sin límite):', c.get('permanencia_extra', 2) or 0, 0, 6, poner('permanencia_extra'),
                     0.5).grid(row=5, column=0, columnspan=2, sticky='w', pady=(6, 0))
        comp = c.setdefault('compensar', {'activa': False, 'max': 1})
        fila_cp = ttk.Frame(gen)
        fila_cp.grid(row=7, column=0, columnspan=2, sticky='w', pady=(8, 0))
        var_cp = tk.BooleanVar(value=bool(comp.get('activa')))
        ttk.Checkbutton(fila_cp, text='Compensar: un docente SIN horas extra puede tener un día hasta',
                        variable=var_cp, command=lambda: comp.__setitem__('activa', var_cp.get())).pack(side='left')
        var_cpm = tk.StringVar(value=f"{float(comp.get('max') or 1):g}")
        ttk.Spinbox(fila_cp, from_=0.5, to=3, increment=0.5, width=4, textvariable=var_cpm).pack(side='left', padx=4)

        def cambio_cpm(*_):
            try:
                comp['max'] = max(0.5, float(var_cpm.get().replace(',', '.')))
            except ValueError:
                pass
        var_cpm.trace_add('write', cambio_cpm)
        ttk.Label(fila_cp, text='hora(s) más largo que su permanencia (o con la 1.ª y la última), si la semana no pasa de '
                                'permanencia × días').pack(side='left')
        ttk.Label(gen, text='Ej.: 6 h × 5 días = 30 h a la semana. Dos días de 7 h se pagan con un día de 4 h o con dos de '
                            '5 h, como mejor encaje. Un día sin clases cuenta 0 h.', style='Ayuda.TLabel').grid(row=8, column=0, columnspan=2,
                                                                                         sticky='w')
        ttk.Label(gen, text='Un docente con horas extra puede tener tantos «días largos» (más que su permanencia, o con la '
                            '1.ª y la última hora) como horas extra tenga: con 2 extra, máximo 2 días. Si caben dentro de '
                            'la jornada, mejor.', style='Ayuda.TLabel', wraplength=900).grid(row=6, column=0, columnspan=2,
                                                                                      sticky='w')
        bg = c.setdefault('bloques_general', {'activa': False, 'desde': 2})
        fila_bl = ttk.Frame(gen)
        fila_bl.grid(row=3, column=0, columnspan=2, sticky='w', pady=(6, 0))
        var_bl = tk.BooleanVar(value=bool(bg.get('activa')))

        def cambio_bloques():
            bg['activa'] = var_bl.get()
            self._llenar_materias()
        ttk.Checkbutton(fila_bl, text='Dar prioridad a los bloques: las materias de', variable=var_bl,
                        command=cambio_bloques).pack(side='left')
        var_desde = tk.StringVar(value=str(bg.get('desde') or 2))
        ttk.Spinbox(fila_bl, from_=2, to=10, width=3, textvariable=var_desde).pack(side='left', padx=4)

        def cambio_desde(*_):
            try:
                bg['desde'] = max(2, int(var_desde.get()))
            except ValueError:
                pass
        var_desde.trace_add('write', cambio_desde)
        ttk.Label(fila_bl, text='horas o más van en bloques de 2 horas seguidas (2+2+1…); si no cabe, se parte').pack(side='left')
        ttk.Label(fila_bl, text='· una materia con «1+1+1» en Bloques queda por fuera', style='Ayuda.TLabel').pack(side='left', padx=6)
        fila_bd = ttk.Frame(gen)
        fila_bd.grid(row=4, column=0, columnspan=2, sticky='w', pady=(6, 0))
        ttk.Label(fila_bd, text='¿Un bloque puede quedar partido por el descanso? (ej.: una hora antes y otra después)').pack(side='left')
        self.cb_bd = ttk.Combobox(fila_bd, state='readonly', width=30,
                                  values=['Preguntar al generar', 'Sí, puede quedar partido', 'No, siempre seguidas'])
        self.cb_bd.current({None: 0, True: 1, False: 2}.get(c.get('bloque_descanso'), 0))
        self.cb_bd.pack(side='left', padx=6)
        self.cb_bd.bind('<<ComboboxSelected>>',
                        lambda e: c.__setitem__('bloque_descanso', [None, True, False][self.cb_bd.current()]))
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
        self.filtro_mat = self._filtros(izq, ('area',), lambda: self._llenar_materias())
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
        filtro = getattr(self, 'filtro_mat', None)
        for m in sorted(D.materias.values(), key=lambda m: m['nombre']):
            if filtro and not filtro(materia=m['id']):
                continue
            r = self.p.cond['materias'].get(str(m['id']), {})
            self.tv_mat.insert('', 'end', iid=str(m['id']), values=(
                m['nombre'], m.get('area', ''),
                r.get('bloques') or ('2+2…' if r.get('doble') else
                                     '2+2… (general)' if (self.p.cond.get('bloques_general') or {}).get('activa') else '1+1…'),
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
        ttk.Label(izq, text='Docentes y, al final, cursos y áreas').pack(anchor='w')
        self.filtro_doc = self._filtros(izq, ('grado', 'area', 'materia', 'docente'), lambda: self._llenar_lista_docentes())
        marco_lb = ttk.Frame(izq)
        marco_lb.pack(fill='both', expand=True, anchor='w', pady=(4, 0))
        self.lb_doc = tk.Listbox(marco_lb, width=48, exportselection=False)
        sb_lb = ttk.Scrollbar(marco_lb, orient='vertical', command=self.lb_doc.yview)
        self.lb_doc.configure(yscrollcommand=sb_lb.set)
        sb_lb.pack(side='right', fill='y')
        self.lb_doc.pack(side='left', fill='both', expand=True)
        self.lb_doc.bind('<<ListboxSelect>>', lambda e: self._ver_docente())
        self._llenar_lista_docentes()
        disp = self.p.disponibilidad_plataforma()
        if disp:
            ttk.Label(izq, text=f'✉ = marcó su disponibilidad en la plataforma ({len(disp)})', style='Ayuda.TLabel').pack(anchor='w')
            ttk.Button(izq, text='Volver a traer la disponibilidad', command=self._traer_disp).pack(fill='x', pady=2)
        self.panel_doc = ttk.Frame(f, padding=(14, 0))
        self.panel_doc.pack(side='left', fill='both', expand=True)
        ttk.Label(self.panel_doc, text='Escoja un docente.', style='Ayuda.TLabel').pack(anchor='w')

    def _llenar_lista_docentes(self):
        D = self.p.datos
        filtro = self.filtro_doc
        # Un docente pasa el filtro si tiene alguna clase en ese grado y de esa área
        pasan = {a.get('docente') for a in D.asignaciones.values() if a.get('docente') and filtro(a)}
        self.docs = [d for d in sorted(D.docentes.values(), key=lambda d: d['nombre']) if d['id'] in pasan]
        g, m, dd = filtro.valor('grado'), filtro.valor('materia'), filtro.valor('docente')
        con_filtro = {a['curso'] for a in D.asignaciones.values() if filtro(a)} if (m != '' or dd != '') else None
        self.cursos_l = [c for c in D.crudo['cursos'] if c['id'] in D.jornada_de_curso and (g == '' or c.get('grado') == g)
                         and (con_filtro is None or c['id'] in con_filtro)]
        disp = self.p.disponibilidad_plataforma()
        self.lb_doc.delete(0, 'end')
        for d in self.docs:
            self.lb_doc.insert('end', d['nombre'] + ('  ✉' if d['id'] in disp else '')
                               + ('  (viaja)' if self.p.docente(d['id']).get('viaja') else ''))
        for c in self.cursos_l:
            self.lb_doc.insert('end', f'Curso {c["nombre"]}')
            self.lb_doc.itemconfig('end', foreground='#3730a3')
        ar = filtro.valor('area')
        de_filtro = ({D.materias.get(a['materia'], {}).get('area') for a in D.asignaciones.values() if filtro(a)}
                     if (m != '' or dd != '' or g != '') else None)
        self.areas_l = [x for x in sorted(D.areas) if (ar == '' or x == ar) and (de_filtro is None or x in de_filtro)]
        for x in self.areas_l:
            r = (self.p.cond.get('areas') or {}).get(x) or {}
            n = len(r.get('no_puede') or []) + len(r.get('prefiere_no') or [])
            self.lb_doc.insert('end', f'Área {x}' + (f'  ({n})' if n else ''))
            self.lb_doc.itemconfig('end', foreground='#047857')

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
        if sel[0] >= len(self.docs) + len(self.cursos_l):
            k = sel[0] - len(self.docs) - len(self.cursos_l)
            return self._ver_area(self.areas_l[k]) if k < len(self.areas_l) else None
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
        if extra:
            self._numero(abajo, f'Tiene {extra} hora(s) extra (hasta {extra} día(s) largo(s)): su día puede alargarse '
                                f'hasta (horas más; 0 = la regla general):',
                         r.get('permanencia_extra') or 0, 0, 6, guardar('permanencia_extra'), 0.5).pack(anchor='w', pady=2)
        fila_v = ttk.Frame(abajo)
        fila_v.pack(anchor='w', pady=(4, 0))
        var_viaja = tk.BooleanVar(value=bool(r.get('viaja')))
        modos = [('ambos', 'lunes primeras horas libres o viernes últimas horas libres'),
                 ('lunes', 'el lunes: primeras horas libres'), ('viernes', 'el viernes: últimas horas libres')]
        cb_viaja = ttk.Combobox(fila_v, state='readonly', width=52, values=[t for _, t in modos])
        cb_viaja.current([m for m, _ in modos].index(nucleo.modo_viaja(r.get('viaja'))))

        def cambio_viaja(*_):
            r['viaja'] = modos[cb_viaja.current()][0] if var_viaja.get() else False
            sel = self.lb_doc.curselection()
            self._llenar_lista_docentes()
            if sel:
                self.lb_doc.selection_set(sel[0])
        ttk.Checkbutton(fila_v, text='No vive en el municipio (viaja). Si le tocan días largos, compensar:',
                        variable=var_viaja, command=cambio_viaja).pack(side='left')
        cb_viaja.pack(side='left', padx=4)
        cb_viaja.bind('<<ComboboxSelected>>', cambio_viaja)
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

    def _ver_area(self, area):
        D = self.p.datos
        mats = ', '.join(sorted(D.nombre_materia(m) for m in D.areas.get(area, [])))
        ttk.Label(self.panel_doc, text=f'Área {area}', style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(self.panel_doc, text=f'Materias: {mats}', style='Ayuda.TLabel', wraplength=700).pack(anchor='w')
        ttk.Label(self.panel_doc, text='Toque una casilla: verde = puede, rojo = las clases del área NO van a esa hora, '
                                       'amarillo = mejor no. Vale para todos los cursos y docentes del área.',
                  style='Ayuda.TLabel', wraplength=700).pack(anchor='w', pady=(4, 6))
        for j in self.p.jornadas_de_area(area):
            ttk.Label(self.panel_doc, text=j['nombre'], style='Sub.TLabel').pack(anchor='w', pady=(6, 2))
            g = tk.Frame(self.panel_doc)
            g.pack(anchor='w')
            for col, dia in enumerate(j['dias'], start=1):
                tk.Label(g, text=nucleo.DIAS[dia], width=11).grid(row=0, column=col)
            for fila, fr in enumerate(D.franjas_de(j['id']), start=1):
                tk.Label(g, text=fr['inicio'], width=7, anchor='e').grid(row=fila, column=0, padx=4)
                for col, dia in enumerate(j['dias'], start=1):
                    if fr['descanso']:
                        tk.Label(g, text='descanso', fg='#999', width=11).grid(row=fila, column=col)
                        continue
                    est = self.p.estado_celda_area(area, dia, fr['id'])
                    b = tk.Button(g, width=10, relief='flat', bg=COLOR_AREA[est], text=TEXTO_AREA[est])
                    b.configure(command=lambda b=b, dia=dia, fid=fr['id']: self._celda_area(area, dia, fid, b))
                    b.grid(row=fila, column=col, padx=1, pady=1)

    def _celda_area(self, area, dia, fid, boton):
        est = self.p.siguiente_estado_area(area, dia, fid)
        boton.configure(bg=COLOR_AREA[est], text=TEXTO_AREA[est])

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
        var_juntas = tk.BooleanVar(value=bool(self.p.cond.get('reuniones_juntas')))

        def cambio_juntas():
            self.p.cond['reuniones_juntas'] = var_juntas.get()
            self._llenar_grupos()
        ttk.Checkbutton(reu, text='Todas las reuniones de área el mismo día y a la misma hora (ej.: la última hora del '
                                  'martes para todos)', variable=var_juntas, command=cambio_juntas).pack(anchor='w')
        marco, self.tv_reu = self._tabla(reu, [('nombre', 'Reunión', 200), ('docentes', 'Docentes', 70),
                                               ('jefe', 'Jefe de área', 180), ('hora', 'Hora', 360)], 7)
        marco.pack(fill='both', expand=True)
        bot = ttk.Frame(reu)
        bot.pack(fill='x', pady=4)
        ttk.Button(bot, text='Crear una por área', command=self._reuniones_area).pack(side='left')
        ttk.Button(bot, text='Nueva', command=lambda: self._editar_reunion(None)).pack(side='left', padx=4)
        ttk.Button(bot, text='Editar', command=self._editar_reunion_sel).pack(side='left')
        ttk.Button(bot, text='Quitar', command=self._quitar_reunion).pack(side='left', padx=4)
        ttk.Button(bot, text='Jefes de área', command=self._jefes_area).pack(side='left')
        ttk.Button(bot, text='🔎 Buscar horas', command=self._llenar_grupos).pack(side='left', padx=4)
        ttk.Button(bot, text='🤝 Buscar hora en el horario armado', command=self.reuniones_horario).pack(side='left')
        sim = ttk.LabelFrame(f, text='Clases simultáneas: van a la misma hora (inglés por niveles, media técnica, '
                                     'educación física de dos cursos…)', padding=6)
        sim.pack(fill='both', expand=True, pady=(8, 0))
        marco, self.tv_sim = self._tabla(sim, [('nombre', 'Nombre', 200), ('clases', 'Clases', 620)], 6)
        marco.pack(fill='both', expand=True)
        bot = ttk.Frame(sim)
        bot.pack(fill='x', pady=4)
        ttk.Button(bot, text='Nueva', command=self._nueva_simultanea).pack(side='left')
        ttk.Button(bot, text='Quitar', command=self._quitar_simultanea).pack(side='left', padx=4)
        mg = ttk.LabelFrame(f, text='Multigrado (Escuela Nueva): cursos que ven clase juntos, con el mismo docente y en la '
                                    'misma aula. La misma materia del mismo docente va a la misma hora para todo el grupo.',
                            padding=6)
        mg.pack(fill='both', expand=True, pady=(8, 0))
        marco, self.tv_mg = self._tabla(mg, [('nombre', 'Grupo', 200), ('cursos', 'Cursos', 620)], 4)
        marco.pack(fill='both', expand=True)
        bot = ttk.Frame(mg)
        bot.pack(fill='x', pady=4)
        ttk.Button(bot, text='Nuevo grupo', command=self._nuevo_multigrado).pack(side='left')
        ttk.Button(bot, text='Quitar', command=self._quitar_multigrado).pack(side='left', padx=4)
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
        if hasattr(self, 'tv_mg'):
            self.tv_mg.delete(*self.tv_mg.get_children())
            for i, g in enumerate(self.p.cond.get('multigrado', [])):
                self.tv_mg.insert('', 'end', iid=str(i), values=(
                    g.get('nombre'), ', '.join(D.nombre_curso(c) for c in g.get('cursos', []))))

    def _nuevo_multigrado(self):
        D = self.p.datos
        cursos = [c for c in D.crudo['cursos'] if c['id'] in D.jornada_de_curso]
        v = tk.Toplevel(self)
        v.title('Grupo multigrado')
        v.transient(self)
        v.grab_set()
        cuerpo = ttk.Frame(v, padding=12)
        cuerpo.pack(fill='both', expand=True)
        ttk.Label(cuerpo, text='Nombre (ej.: Sede La Esperanza 1.º a 5.º)').pack(anchor='w')
        e = ttk.Entry(cuerpo, width=50)
        e.pack(anchor='w')
        ttk.Label(cuerpo, text='Cursos que ven clase juntos (Ctrl + clic):').pack(anchor='w', pady=(8, 2))
        lb = tk.Listbox(cuerpo, selectmode='extended', height=14, width=50, exportselection=False)
        for c in cursos:
            lb.insert('end', f"{c['nombre']}" + (f" · {c.get('sede')}" if c.get('sede') else ''))
        lb.pack(fill='both', expand=True)
        ttk.Label(cuerpo, text='Para que vayan juntas, la materia de cada curso debe tener el mismo docente.',
                  style='Ayuda.TLabel').pack(anchor='w', pady=4)

        def aceptar():
            m = self.p.agregar_multigrado(e.get().strip(), [cursos[k]['id'] for k in lb.curselection()])
            if m:
                return messagebox.showwarning(TITULO, m, parent=v)
            v.destroy()
            self._llenar_grupos()
            self._llenar_datos()
        ttk.Button(cuerpo, text='Guardar', command=aceptar).pack(anchor='e', pady=8)

    def _quitar_multigrado(self):
        sel = self.tv_mg.focus()
        if sel:
            del self.p.cond['multigrado'][int(sel)]
            self._llenar_grupos()

    def _reuniones_area(self):
        n = self.p.reuniones_por_area()
        if not n:
            messagebox.showinfo(TITULO, 'No hay áreas nuevas con dos o más docentes. Revise que las materias tengan '
                                        'su área en la plataforma.')
        self._llenar_grupos()
        self.avisar(f'{n} reunión(es) creada(s). Escoja el jefe de cada área.')
        if n:
            self._jefes_area()

    def _jefes_area(self):
        """Una ventana con cada reunión y una lista para escoger su jefe de área (entre sus docentes)."""
        D = self.p.datos
        reus = self.p.cond.get('reuniones', [])
        if not reus:
            return messagebox.showinfo(TITULO, 'Primero cree las reuniones (por ejemplo, «Crear una por área»).')
        v = tk.Toplevel(self)
        v.title('Jefes de área')
        v.transient(self)
        cuerpo = ttk.Frame(v, padding=12)
        cuerpo.pack(fill='both', expand=True)
        ttk.Label(cuerpo, text='Escoja el jefe de cada área. El jefe siempre va a la reunión; si no pueden todos, se '
                               'hace una segunda con él.', style='Ayuda.TLabel', wraplength=560).grid(
            row=0, column=0, columnspan=2, sticky='w', pady=(0, 8))
        self.cb_jefes = []
        for k, r in enumerate(reus, start=1):
            miembros = sorted([int(x) for x in r.get('docentes', []) if int(x) in D.docentes], key=D.nombre_docente)
            ttk.Label(cuerpo, text=r.get('nombre') or 'Reunión').grid(row=k, column=0, sticky='w', padx=(0, 8), pady=1)
            cb = ttk.Combobox(cuerpo, state='readonly', width=40,
                              values=['(sin jefe)'] + [D.nombre_docente(d) for d in miembros])
            cb.current(miembros.index(int(r['jefe'])) + 1 if r.get('jefe') and int(r['jefe']) in miembros else 0)
            cb.grid(row=k, column=1, sticky='w', pady=1)
            self.cb_jefes.append((r, miembros, cb))

        def guardar():
            for r, miembros, cb in self.cb_jefes:
                r['jefe'] = miembros[cb.current() - 1] if cb.current() > 0 else None
            v.destroy()
            self._llenar_grupos()
            self.avisar('Jefes de área guardados.')
        self.guardar_jefes = guardar
        ttk.Button(cuerpo, text='Guardar', command=guardar).grid(row=len(reus) + 1, column=1, sticky='e', pady=10)
        return v

    def reuniones_horario(self):
        """Con el horario que se está viendo, busca la hora de cada reunión y ofrece mover las clases que estorban."""
        if self._esperar():
            return None
        alt = self._alt()
        if not alt:
            return messagebox.showinfo(TITULO, 'Primero arme o genere un horario (pestaña 6).')
        if not self.p.cond.get('reuniones'):
            return messagebox.showinfo(TITULO, 'No hay reuniones. Créelas en «4. Reuniones y clases juntas».')
        prop = self.p.reuniones_en_horario(alt)
        self.propuestas_reu = (alt, prop)
        v = tk.Toplevel(self)
        v.title('Reuniones en el horario')
        v.transient(self)
        cuerpo = ttk.Frame(v, padding=12)
        cuerpo.pack(fill='both', expand=True)
        ttk.Label(cuerpo, text=f'Horario «{alt.get("nombre", "Horario")}»', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        for t in self.p.texto_reuniones_en_horario(prop, alt):
            ttk.Label(cuerpo, text='• ' + t, wraplength=760).pack(anchor='w', pady=1)
        n = sum(len(ks) for x in prop for ks in x['mover'].values())
        abajo = ttk.Frame(cuerpo)
        abajo.pack(fill='x', pady=(10, 0))
        if n:
            ttk.Label(cuerpo, text=f'«Acomodar» deja cada reunión fija en esa hora, saca las {n} clase(s) que estorban y '
                                   'las vuelve a ubicar en otra hora (Completar lo que falta).', style='Ayuda.TLabel',
                      wraplength=760).pack(anchor='w', before=abajo)
        ttk.Button(abajo, text='🤝 Acomodar' if n else 'Dejar las reuniones en esas horas',
                   command=lambda: (v.destroy(), self._acomodar_reuniones())).pack(side='left')
        ttk.Button(abajo, text='Cerrar', command=v.destroy).pack(side='right')
        return v

    def _acomodar_reuniones(self):
        alt, prop = self.propuestas_reu
        if alt not in self.p.alternativas:
            return
        self._paso(alt)
        n = self.p.acomodar_reuniones(alt, prop)
        self._llenar_grupos()
        self._actualizar_fila()
        self._ver()
        self.nb.select(5)
        if n:
            self.avisar(f'Reuniones fijadas. {n} clase(s) salieron de esas horas; ubicándolas en otro lugar…')
            self._completar()
        else:
            self.avisar('Reuniones fijadas en esas horas.')

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
        dias_todos = sorted({d for j in D.jornadas.values() for d in j['dias']}) or [1, 2, 3, 4, 5]
        cb_dia = ttk.Combobox(fila, state='readonly', width=11, values=[nucleo.DIAS[d] for d in dias_todos])
        cb_dia.current(dias_todos.index(int(r['dia'])) if r.get('dia') and int(r['dia']) in dias_todos else 0)
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
            r['dia'] = dias_todos[max(0, cb_dia.current())]
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
        """Pantalla completa: arriba los botones, abajo las cuadrículas (pestañas). Cada pestaña
        escoge qué horario muestra, así se pueden comparar alternativas lado a lado."""
        f = ttk.Frame(self.nb, padding=(6, 4))
        self.nb.add(f, text='6. Horario')
        uno = ttk.Frame(f)
        uno.pack(fill='x')
        ttk.Button(uno, text='📝 En blanco', command=self._en_blanco).pack(side='left')
        ttk.Separator(uno, orient='vertical').pack(side='left', fill='y', padx=6)
        ttk.Label(uno, text='Alternativas:').pack(side='left')
        self.var_alt = tk.IntVar(value=3)
        ttk.Spinbox(uno, from_=1, to=3, width=3, textvariable=self.var_alt).pack(side='left', padx=3)
        ttk.Label(uno, text='Segundos:').pack(side='left')
        self.var_seg = tk.IntVar(value=60)
        ttk.Spinbox(uno, from_=15, to=3600, increment=15, width=5, textvariable=self.var_seg).pack(side='left', padx=3)
        self.btn_gen = ttk.Button(uno, text='▶ Generar', command=self.generar)
        self.btn_gen.pack(side='left', padx=4)
        ttk.Button(uno, text='Completar lo que falta', command=self._completar).pack(side='left', padx=2)
        ttk.Button(uno, text='Regenerar lo no fijado', command=lambda: self._completar(solo_fijadas=True)).pack(side='left', padx=2)
        self.btn_parar = ttk.Button(uno, text='⏹ Detener', command=self.detener, state='disabled')
        self.btn_parar.pack(side='left', padx=2)
        self.var_vivo = tk.BooleanVar(value=True)
        ttk.Checkbutton(uno, text='Ver en vivo', variable=self.var_vivo).pack(side='left', padx=4)
        self.barra = ttk.Progressbar(uno, length=110, mode='determinate')
        self.barra.pack(side='left', padx=6)
        self.lbl_prog = ttk.Label(uno, text='', style='Ayuda.TLabel')
        self.lbl_prog.pack(side='left')
        # Fila 2: revisar y editar (los colores van primero para que nunca queden por fuera de la pantalla)
        dos = ttk.Frame(f)
        dos.pack(fill='x', pady=(4, 0))
        tk.Label(dos, text=' no se puede ', bg=ROJO_SEL).pack(side='right', padx=1)
        tk.Label(dos, text=' ocupada: reemplazar ', bg=AMARILLO_SEL).pack(side='right', padx=1)
        tk.Label(dos, text=' libre ', bg=VERDE_SEL).pack(side='right', padx=1)
        ttk.Label(dos, text='Al escoger una ficha:', style='Ayuda.TLabel').pack(side='right', padx=(8, 3))
        self.btn_avisos = ttk.Button(dos, text='⚠ Avisos', command=self._alternar_avisos)
        self.btn_avisos.pack(side='left')
        ttk.Button(dos, text='🩺 ¿Por qué faltan horas?', command=self.asistente).pack(side='left', padx=3)
        ttk.Button(dos, text='↶ Deshacer', command=self.deshacer).pack(side='left', padx=3)
        ttk.Separator(dos, orient='vertical').pack(side='left', fill='y', padx=6)
        self.var_fijar = tk.BooleanVar(value=False)
        ttk.Checkbutton(dos, text='Fijar 🔒 lo que ubico a mano', variable=self.var_fijar).pack(side='left')
        self.btn_soltar = ttk.Button(dos, text='🔓 Soltar marcadas', command=lambda: self.fijar_marcadas(False))
        self.btn_soltar.pack(side='left', padx=(6, 0))
        ttk.Button(dos, text='🔒 Fijar marcadas', command=lambda: self.fijar_marcadas(True)).pack(side='left', padx=2)
        ttk.Button(dos, text='🔓 Soltar todo', command=self.soltar_todo).pack(side='left')
        # Fila 3: guardar, imprimir y vistas
        tres = ttk.Frame(f)
        tres.pack(fill='x', pady=(4, 0))
        self.filas_barra = [uno, dos, tres]
        # Zoom (todas las cuadrículas) · también Ctrl + rueda del mouse sobre una cuadrícula
        ttk.Button(tres, text='🔍+', width=4, command=lambda: self.zoom_todas(0.1)).pack(side='right')
        ttk.Button(tres, text='100%', width=5, command=lambda: self.zoom_todas(None)).pack(side='right', padx=1)
        ttk.Button(tres, text='🔍−', width=4, command=lambda: self.zoom_todas(-0.1)).pack(side='right')
        ttk.Label(tres, text='Tamaño:').pack(side='right', padx=(8, 2))
        ttk.Button(tres, text='💾 Guardar (.mchr)', command=self._exportar).pack(side='left')
        ttk.Button(tres, text='Excel', command=self._excel).pack(side='left', padx=3)
        ttk.Button(tres, text='📄 PDF por separado (.zip)', command=self._pdf_zip).pack(side='left')
        ttk.Button(tres, text='📄 PDF todo junto', command=self._pdf_todo).pack(side='left', padx=3)
        ttk.Button(tres, text='Renombrar', command=self._renombrar_alt).pack(side='left')
        ttk.Button(tres, text='Quitar', command=self._quitar_alt).pack(side='left', padx=3)
        ttk.Separator(tres, orient='vertical').pack(side='left', fill='y', padx=6)
        ttk.Button(tres, text='➕ Pestaña', command=self.nueva_pestana).pack(side='left')
        ttk.Button(tres, text='🗗 Ventana', command=self.nueva_ventana).pack(side='left', padx=3)
        self.cb_mosaico = ttk.Combobox(tres, state='readonly', width=3, values=['2', '4', '6', '9'])
        self.cb_mosaico.current(1)
        self.cb_mosaico.pack(side='left')
        ttk.Button(tres, text='▦ en una ventana', command=self.mosaico).pack(side='left', padx=(2, 3))
        ttk.Label(f, text='Toque una ficha para ver dónde cabe; arrástrela o toque una casilla vacía. Ctrl + clic: marcar '
                          'varias fichas (para soltarlas o fijarlas juntas). Clic derecho: fijar o quitar. Esc: soltar la '
                          'selección.',
                  style='Ayuda.TLabel').pack(anchor='w', pady=(2, 0))
        self.marco_avisos = ttk.Frame(f)
        self.txt_avisos = tk.Text(self.marco_avisos, wrap='word', height=8, relief='flat', background=GRIS,
                                  font=('Segoe UI', 9))
        self.txt_avisos.pack(fill='both', expand=True)
        self.avisos_visibles = False
        self.nb_vistas = ttk.Notebook(f)
        self.nb_vistas.pack(fill='both', expand=True, pady=(4, 0))
        self.nb_vistas.bind('<<NotebookTabChanged>>', lambda e: self._cambio_pestana())
        self.vistas = []
        self.sel = None
        self._mapa = None
        self.sueltas = set()            # clases que el usuario quiere ubicar de a una hora
        self.ventana_asistente = None   # «¿Por qué faltan horas?»
        self.sug_asistente = []
        self.parar_evt = threading.Event()
        self.alt_vivo = None            # lo que el generador lleva acomodado (solo para mirar)
        self._vivo_pendiente = None
        self._vivo_dibujado = 0.0
        self._historial = []            # para «Deshacer»
        self.marcadas = set()           # fichas marcadas con Ctrl + clic (índices en el horario _marcadas_alt)
        self._marcadas_alt = None
        self.bind('<Control-z>', self._tecla_deshacer)
        self.bind('<Control-Z>', self._tecla_deshacer)
        self.bind_all('<Control-MouseWheel>', self._zoom_rueda)
        self.bind('<Control-plus>', lambda e: self.zoom_todas(0.1))
        self.bind('<Control-equal>', lambda e: self.zoom_todas(0.1))
        self.bind('<Control-minus>', lambda e: self.zoom_todas(-0.1))
        self.bind('<Escape>', lambda e: self.quitar_seleccion())
        self.nueva_pestana()
        self._llenar_alternativas()

    def _alternar_avisos(self):
        if self.avisos_visibles:
            self.marco_avisos.pack_forget()
        else:
            self.marco_avisos.pack(fill='x', before=self.nb_vistas, pady=(4, 0))
        self.avisos_visibles = not self.avisos_visibles

    def _cambio_pestana(self):
        self._avisos(self._alt())
        self._pintar_seleccion()

    def _en_blanco(self):
        if self._esperar():
            return
        self.p.en_blanco()
        self._llenar_alternativas()
        self.avisar('Horario en blanco: arrastre las fichas de la izquierda a la cuadrícula.')

    def generar(self):
        if self._esperar():
            return
        errores = [t for n, t in nucleo.diagnostico(self.p.datos, self.p.cond) if n == 'error']
        if errores and not messagebox.askyesno(TITULO, 'Hay problemas en los datos:\n\n' + '\n'.join(errores[:6]) +
                                               '\n\nAsí pueden quedar clases sin ubicar. ¿Generar de todas formas?'):
            return
        self._preguntar_descanso()
        if self._preguntar_viajan():
            return
        base = self._alt()
        fijadas = sum(1 for s in (base or {}).get('sesiones', []) if s.get('fijada'))
        if fijadas and not messagebox.askyesno(TITULO, f'Se van a respetar las {fijadas} fichas fijadas (🔒) del '
                                                        f'horario «{base["nombre"]}». ¿Seguir?'):
            base = None
        n, seg = max(1, min(3, int(self.var_alt.get()))), max(5, int(self.var_seg.get()))   # se leen aquí, no en el hilo
        self._lanzar(lambda av, vv, pa: self.p.generar(n, seg, av, base=base if fijadas else None, vivo=vv, parar=pa))

    def _preguntar_viajan(self):
        """La primera vez que se genera con días largos, pregunta por los docentes que viven fuera.
        Devuelve True si el usuario quiere marcarlos antes de generar."""
        c = self.p.cond
        hay_largos = (c.get('compensar') or {}).get('activa') or any(
            nucleo.horas_extra(c, a['id'], self.p.datos.ih(a['id'], c)) for a in self.p.datos.asignaciones.values())
        if c.get('preguntado_viajan') or not hay_largos:
            return False
        c['preguntado_viajan'] = True
        if any(r.get('viaja') for r in c.get('docentes', {}).values()):
            return False
        if messagebox.askyesno(TITULO, '¿Hay docentes que NO viven en el municipio?\n\nSi les tocan días largos, el '
                                       'generador busca que la compensación les quede entrando tarde el lunes o '
                                       'saliendo temprano el viernes.\n\n«Sí»: lo llevo a «3. Docentes y cursos» para '
                                       'marcarlos (casilla 🚌).\n«No»: generar así.'):
            self.nb.select(2)
            self.avisar('Escoja cada docente que viaja y marque «🚌 No vive en el municipio». Luego genere de nuevo.')
            return True
        return False

    def _preguntar_descanso(self):
        """Si hay bloques y no se ha dicho, pregunta si un bloque puede quedar partido por el descanso."""
        c = self.p.cond
        if c.get('bloque_descanso') is not None or not self.p.hay_bloques():
            return
        r = messagebox.askyesno(TITULO, 'Hay clases en bloques (2 horas seguidas).\n\n'
                                        '¿Un bloque puede quedar partido por el descanso? Por ejemplo, una hora antes '
                                        'del descanso y la otra justo después.\n\n'
                                        '«Sí»: se permite (más fácil de ubicar).\n«No»: las dos horas siempre seguidas.\n\n'
                                        'Lo puede cambiar después en Reglas.')
        c['bloque_descanso'] = bool(r)
        if hasattr(self, 'cb_bd'):
            self.cb_bd.current(1 if r else 2)

    def _completar(self, solo_fijadas=False):
        if self._esperar():
            return
        alt = self._alt()
        if not alt:
            return messagebox.showinfo(TITULO, 'Escoja un horario de la lista.')
        self._preguntar_descanso()
        seg = max(5, int(self.var_seg.get()))
        self._lanzar(lambda av, vv, pa: self.p.completar(alt, seg, av, solo_fijadas=solo_fijadas, vivo=vv, parar=pa))

    def _esperar(self):
        """True (y avisa) si está generando: mientras tanto el horario solo se mira."""
        if self.generando:
            self.avisar('Espere a que termine de generar, o use ⏹ Detener.', error=True)
            return True
        return False

    def detener(self):
        if self.generando:
            self.parar_evt.set()
            self.lbl_prog.configure(text='Deteniendo… se queda con lo mejor que lleve')

    def _lanzar(self, trabajo):
        self.generando = True
        self.parar_evt.clear()
        self.alt_vivo = None
        self._vivo_pendiente = None
        self._t_inicio = time.monotonic()
        self.btn_gen.configure(state='disabled')
        self.btn_parar.configure(state='normal')
        self.quitar_seleccion(redibujar=False)
        ver = bool(self.var_vivo.get())

        def vivo(ses, nombre):
            self.cola.put(('vivo', ses, nombre))

        def correr():
            try:
                trabajo(lambda pct, txt: self.cola.put(('avance', pct, txt)), vivo if ver else None,
                        self.parar_evt.is_set)
                self.cola.put(('listo', None, None))
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.cola.put(('error', 0, f'{type(e).__name__}: {e}'))
        threading.Thread(target=correr, daemon=True).start()
        self.after(200, self._revisar_cola)

    def _revisar_cola(self):
        try:
            while True:
                tipo, pct, txt = self.cola.get_nowait()
                if tipo == 'avance':
                    self.barra['value'] = pct
                    seg = int(time.monotonic() - getattr(self, '_t_inicio', time.monotonic()))
                    self.lbl_prog.configure(text=f'{txt} ({seg} s)')
                elif tipo == 'vivo':
                    self._vivo_pendiente = (pct, txt)
                else:
                    self.generando = False
                    self.alt_vivo = None
                    self._vivo_pendiente = None
                    self.btn_gen.configure(state='normal')
                    self.btn_parar.configure(state='disabled')
                    if tipo == 'listo':
                        self.barra['value'] = 100
                        detenido = self.p.alternativas and self.p.alternativas[0].get('detenido')
                        usados = self.p.alternativas[0].get('segundos_usados') if self.p.alternativas else None
                        self.lbl_prog.configure(text=('Detenido' if detenido else 'Listo') +
                                                (f' en {usados:g} s' if usados else ''))
                        self._llenar_alternativas()
                        alt = self._alt()
                        if detenido:
                            self.avisar('⏹ Detenido: quedó lo mejor que llevaba. Puede completar lo que falta después.')
                        if alt and (alt.get('horas_sin_ubicar') or alt.get('choques')) and not self.avisos_visibles:
                            self._alternar_avisos()
                        if alt and alt.get('horas_sin_ubicar'):
                            self.avisar(f'Listo, pero quedaron {alt["horas_sin_ubicar"]} horas sin ubicar. '
                                        'Mire las sugerencias.', error=True)
                            self.asistente(alt)
                        else:
                            self.avisar('Listo. Revise el horario; puede seguir ajustándolo con las fichas.')
                    else:
                        self._ver()
                        messagebox.showerror(TITULO, f'No se pudo generar: {txt}')
                    return
        except queue.Empty:
            pass
        self._mostrar_vivo()
        self.after(200, self._revisar_cola)

    def _mostrar_vivo(self, ya=False):
        """Dibuja lo que el generador lleva acomodado (cada segundo y medio, para no trabar la ventana)."""
        if not self._vivo_pendiente or not self.generando:
            return
        if not ya and time.monotonic() - self._vivo_dibujado < 1.5:
            return
        ses, nombre = self._vivo_pendiente
        self._vivo_pendiente = None
        self._vivo_dibujado = time.monotonic()
        self.alt_vivo = self.p.en_vivo(ses, nombre)
        total = self.p.horas_totales()
        hechas = total - self.alt_vivo['horas_sin_ubicar']
        self.avisar(f'⏳ {nombre}: {hechas} de {total} horas acomodadas. Mientras genera, el horario solo se mira.')
        for v in list(self.vistas):
            v.dibujar()

    # --- Deshacer ------------------------------------------------------------------
    def _paso(self, alt):
        """Guarda cómo estaba el horario antes de un cambio a mano."""
        if alt and not alt.get('vivo'):
            self._historial.append((alt, copy.deepcopy(alt['sesiones'])))
            del self._historial[:-40]
        self.marcadas = set()           # los índices cambian con el cambio
        self._marcadas_alt = None

    def _tecla_deshacer(self, e):
        if e.widget.winfo_class() in ('Entry', 'TEntry', 'TSpinbox', 'Spinbox', 'Text', 'TCombobox'):
            return None                 # en una casilla de texto, Ctrl+Z es de la casilla
        self.deshacer()
        return 'break'

    # --- Marcar varias fichas (Ctrl + clic) y soltarlas o fijarlas juntas -----------------
    def marcar(self, datos):
        self._arr = None
        v = self._vista_de(datos)
        alt = v.alt()
        if not alt or alt.get('vivo'):
            return 'break'
        if alt is not self._marcadas_alt:
            self.marcadas, self._marcadas_alt = set(), alt
        i = datos['i']
        self.marcadas.symmetric_difference_update({i})
        self.btn_soltar.configure(text=f'🔓 Soltar marcadas ({len(self.marcadas)})' if self.marcadas
                                  else '🔓 Soltar marcadas')
        self.avisar(f'{len(self.marcadas)} ficha(s) marcada(s). Use «Soltar marcadas» o «Fijar marcadas».')
        for vv in self.vistas:
            if vv.alt() is alt:
                vv.dibujar()
        return 'break'

    def fijar_marcadas(self, fijar):
        if self._esperar():
            return
        alt = self._marcadas_alt
        if not alt or not self.marcadas or alt not in self.p.alternativas:
            return self.avisar('Primero marque fichas con Ctrl + clic.', error=True)
        marcadas = set(self.marcadas)
        self._paso(alt)
        n = self.p.fijar_varias(alt, marcadas, fijar)
        self.btn_soltar.configure(text='🔓 Soltar marcadas')
        self._ver()
        self.avisar(f'{n} ficha(s) {"fijada(s) 🔒" if fijar else "soltada(s) 🔓: el generador ya las puede mover"}.')

    def soltar_todo(self):
        if self._esperar():
            return
        alt = self._alt()
        if not alt:
            return
        n = sum(1 for s in alt['sesiones'] if s.get('fijada'))
        if not n:
            return self.avisar('Este horario no tiene fichas fijadas.')
        if not messagebox.askyesno(TITULO, f'¿Soltar las {n} fichas fijadas 🔒 de «{alt.get("nombre", "Horario")}»? '
                                           'Siguen en su lugar, pero el generador ya las puede mover.'):
            return
        self._paso(alt)
        self.p.fijar_varias(alt, None, False)
        self._ver()
        self.avisar(f'{n} ficha(s) soltada(s) 🔓.')

    # --- PDF ---------------------------------------------------------------------
    def _pdf_zip(self):
        if self._esperar():
            return
        alt = self._alt()
        if not alt:
            return messagebox.showinfo(TITULO, 'Escoja un horario.')
        nombre = impresion.nombre_archivo(f'Horarios {alt.get("nombre", "")}')
        ruta = filedialog.asksaveasfilename(title='PDF de cada curso y cada docente', defaultextension='.zip',
                                            filetypes=[('Archivo zip', '*.zip')], initialfile=f'{nombre}.zip')
        if not ruta:
            return
        try:
            n = impresion.zip_individuales(self.p, alt, ruta)
            self.avisar(f'Listo: {n} PDF en el zip (carpetas Cursos y Docentes).')
        except Exception as e:
            messagebox.showerror(TITULO, f'No se pudieron hacer los PDF: {e}')

    def _pdf_todo(self):
        if self._esperar():
            return
        alt = self._alt()
        if not alt:
            return messagebox.showinfo(TITULO, 'Escoja un horario.')
        carpeta = filedialog.askdirectory(title='Carpeta donde guardar los dos PDF (cursos y docentes)')
        if not carpeta:
            return
        base = impresion.nombre_archivo(alt.get('nombre', 'Horario'))
        rc = os.path.join(carpeta, f'Horarios de cursos - {base}.pdf')
        rd = os.path.join(carpeta, f'Horarios de docentes - {base}.pdf')
        try:
            nc, nd = impresion.todo_junto(self.p, alt, rc, rd)
            self.avisar(f'Listo: «{os.path.basename(rc)}» ({nc} cursos) y «{os.path.basename(rd)}» ({nd} docentes).')
        except Exception as e:
            messagebox.showerror(TITULO, f'No se pudieron hacer los PDF: {e}')

    def deshacer(self):
        if self._esperar():
            return
        while self._historial:
            alt, ses = self._historial.pop()
            if alt not in self.p.alternativas or ses == alt['sesiones']:
                continue
            alt['sesiones'] = ses
            self.p.revisar(alt)
            self.quitar_seleccion(redibujar=False)
            self._actualizar_fila()
            self._ver()
            return self.avisar('↶ Se deshizo el último cambio.')
        self.avisar('No hay nada que deshacer.')

    # --- Zoom y varias cuadrículas en una ventana ----------------------------------
    def zoom_todas(self, delta):
        for v in self.vistas:
            v.cambiar_zoom(delta)

    def _zoom_rueda(self, e):
        try:
            w = self.winfo_containing(e.x_root, e.y_root)
        except (tk.TclError, KeyError):
            w = None
        while w is not None and getattr(w, 'vista_duena', None) is None:
            w = getattr(w, 'master', None)
        v = getattr(w, 'vista_duena', None) if w is not None else None
        (v or self.vista_actual()).cambiar_zoom(0.1 if e.delta > 0 else -0.1)
        return 'break'

    def mosaico(self, n=None):
        """Una ventana con 2, 4, 6 o 9 cuadrículas (cada una escoge horario, curso o docente)."""
        try:
            n = int(n or self.cb_mosaico.get() or 4)
        except ValueError:
            n = 4
        filas, cols = {2: (1, 2), 4: (2, 2), 6: (2, 3), 9: (3, 3)}.get(n, (2, 2))
        w = tk.Toplevel(self)
        w.title(f'{TITULO} · {n} horarios')
        w.geometry('1300x850')
        try:
            w.state('zoomed')
        except tk.TclError:
            pass
        for r in range(filas):
            w.rowconfigure(r, weight=1, uniform='fila')
        for c in range(cols):
            w.columnconfigure(c, weight=1, uniform='col')
        idx = self.vista_actual().indice() if self.vistas else 0
        nuevas = []
        for k in range(filas * cols):
            marco = ttk.Frame(w, padding=3, relief='groove')
            marco.grid(row=k // cols, column=k % cols, sticky='nsew', padx=2, pady=2)
            v = Vista(self, marco, compacta=True)
            v.ventana = w
            v.zoom = {2: 0.9, 4: 0.8, 6: 0.7, 9: 0.6}.get(n, 0.8)
            v.idx = idx
            self.vistas.append(v)
            nuevas.append(v)
            v.poner_alternativas(self.nombres_alternativas(), None, redibujar=False)
            v.opciones()
            if v.quien_l:
                v.cb_quien.current(min(k, len(v.quien_l) - 1))     # cada una con el curso siguiente
                v.dibujar()

        def cerrar():
            for v in nuevas:
                if v in self.vistas:
                    self.vistas.remove(v)
            w.destroy()
        w.protocol('WM_DELETE_WINDOW', cerrar)
        w.bind('<Escape>', lambda e: self.quitar_seleccion())
        w.cerrar = cerrar
        return nuevas

    # --- Asistente: cuando quedan horas sin ubicar --------------------------------
    def asistente(self, alt=None):
        """Ventana con lo que faltó y qué hacer: más tiempo, aflojar condiciones o consejos."""
        if self._esperar():
            return None
        alt = alt or self._alt()
        if not alt:
            return messagebox.showinfo(TITULO, 'Escoja un horario de la lista.')
        faltan = self.p.sin_ubicar_texto(alt)
        if not faltan:
            return messagebox.showinfo(TITULO, 'En este horario no faltan horas por ubicar. 👍')
        viejo = self.ventana_asistente
        if viejo is not None:
            try:
                viejo.destroy()
            except tk.TclError:
                pass
        w = tk.Toplevel(self)
        self.ventana_asistente = w
        w.title('¿Por qué faltan horas?')
        w.transient(self)
        cuerpo = ttk.Frame(w, padding=12)
        cuerpo.pack(fill='both', expand=True)
        ttk.Label(cuerpo, text=f'Quedaron {alt["horas_sin_ubicar"]} horas sin ubicar en «{alt.get("nombre", "Horario")}»',
                  font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        ttk.Label(cuerpo, text='\n'.join('• ' + t for t in faltan[:8]) + (f'\n… y {len(faltan) - 8} más' if len(faltan) > 8 else ''),
                  style='Ayuda.TLabel').pack(anchor='w', pady=(2, 6))
        dificiles = self.p.texto_dificiles(alt)[:5]
        if dificiles:
            ttk.Label(cuerpo, text='Lo que más le costó ubicar: ' + '; '.join(dificiles), wraplength=640,
                      style='Ayuda.TLabel').pack(anchor='w', pady=(0, 6))
        seg = max(5, int(self.var_seg.get() or 60))
        mas = min(600, max(120, seg * 2))
        t1 = ttk.LabelFrame(cuerpo, text='1. Intentar con más tiempo', padding=8)
        t1.pack(fill='x', pady=4)
        ttk.Label(t1, text=f'Ahora usa {seg} segundos. Con más tiempo el generador prueba más combinaciones.',
                  wraplength=640).pack(anchor='w')
        fila = ttk.Frame(t1)
        fila.pack(anchor='w', pady=(4, 0))
        ttk.Button(fila, text=f'⏱ Completar lo que falta ({mas} s)',
                   command=lambda: self._asistente_tiempo(mas, completar=True)).pack(side='left')
        ttk.Button(fila, text=f'⏱ Generar de nuevo ({mas} s)',
                   command=lambda: self._asistente_tiempo(mas, completar=False)).pack(side='left', padx=6)
        sug = self.p.sugerencias(alt)
        self.sug_asistente = []
        t2 = ttk.LabelFrame(cuerpo, text='2. Cambiar condiciones (marque las que acepta)', padding=8)
        t2.pack(fill='x', pady=4)
        if sug:
            for k, s_ in enumerate(sug[:14]):
                var = tk.BooleanVar(value=k < 3)
                ttk.Checkbutton(t2, text=s_['texto'], variable=var).pack(anchor='w')
                self.sug_asistente.append((s_, var))
            if len(sug) > 14:
                ttk.Label(t2, text=f'(hay {len(sug) - 14} sugerencias más; aplique estas y vuelva a revisar)',
                          style='Ayuda.TLabel').pack(anchor='w')
            fila = ttk.Frame(t2)
            fila.pack(anchor='w', pady=(6, 0))
            ttk.Button(fila, text='Aplicar las marcadas y completar lo que falta',
                       command=lambda: self._asistente_aplicar(completar=True)).pack(side='left')
            ttk.Button(fila, text='Aplicar y generar de nuevo',
                       command=lambda: self._asistente_aplicar(completar=False)).pack(side='left', padx=6)
            ttk.Label(t2, text='Los cambios quedan en Reglas y Docentes; los puede deshacer allá.',
                      style='Ayuda.TLabel').pack(anchor='w', pady=(4, 0))
        else:
            ttk.Label(t2, text='No encontré una condición clara que aflojar. Pruebe con más tiempo o ubique a mano.',
                      wraplength=640).pack(anchor='w')
        t3 = ttk.LabelFrame(cuerpo, text='3. Consejos', padding=8)
        t3.pack(fill='x', pady=4)
        for t in self.p.CONSEJOS:
            ttk.Label(t3, text='• ' + t, wraplength=640).pack(anchor='w')
        abajo = ttk.Frame(cuerpo)
        abajo.pack(fill='x', pady=(8, 0))
        ttk.Button(abajo, text='✋ Ubicar a mano', command=self._asistente_a_mano).pack(side='left')
        ttk.Button(abajo, text='Cerrar', command=w.destroy).pack(side='right')
        return w

    def _cerrar_asistente(self):
        w = self.ventana_asistente
        self.ventana_asistente = None
        if w is not None:
            try:
                w.destroy()
            except tk.TclError:
                pass

    def _asistente_tiempo(self, segundos, completar=True):
        self._cerrar_asistente()
        self.var_seg.set(segundos)
        self._completar() if completar else self.generar()

    def _asistente_aplicar(self, completar=True):
        elegidas = [s_ for s_, var in self.sug_asistente if var.get()]
        if not elegidas:
            return messagebox.showinfo(TITULO, 'Marque al menos un cambio.')
        for s_ in elegidas:
            self.p.aplicar_sugerencia(s_)
        self._cerrar_asistente()
        self._refrescar_condiciones()
        self.avisar(f'Se aplicaron {len(elegidas)} cambio(s): ' + '; '.join(s_['texto'] for s_ in elegidas)[:300])
        if self.generando:
            return
        self._completar() if completar else self.generar()

    def _asistente_a_mano(self):
        self._cerrar_asistente()
        v = self.vista_actual()
        if v is not None and not v.var_paleta.get():
            v.var_paleta.set(True)
            v._mostrar_paleta()
        self.avisar('Las clases que faltan están en las fichas de la izquierda: arrástrelas a la cuadrícula. '
                    'Rojo = no se puede, amarillo = reemplazar, verde = libre.')

    def _refrescar_condiciones(self):
        """Vuelve a dibujar las pestañas 1 a 5 con las condiciones nuevas (la 6 queda igual)."""
        tabs = list(self.nb.tabs() or [])
        if len(tabs) < 6:
            return
        horario = tabs[5]
        for t in tabs[:5]:
            w = self.nb.nametowidget(t) if isinstance(t, str) else t
            self.nb.forget(t)
            w.destroy()
        self.tab_datos()
        self.tab_reglas()
        self.tab_docentes()
        self.tab_grupos()
        self.tab_tareas()
        self.nb.insert('end', horario)
        self.nb.select(horario)

    def nombres_alternativas(self):
        out = []
        for a in self.p.alternativas:
            t = a.get('nombre') or 'Horario'
            extra = []
            if a.get('horas_sin_ubicar'):
                extra.append(f"faltan {a['horas_sin_ubicar']}")
            if a.get('choques'):
                extra.append(f"{len(a['choques'])} choques")
            if a.get('huecos') is not None:
                extra.append(f"huecos {a['huecos']}")
            out.append(t + (' · ' + ' · '.join(extra) if extra else ''))
        return out

    def _llenar_alternativas(self, elegir=0):
        """Actualiza la lista de horarios en todas las pestañas; la pestaña actual muestra `elegir`."""
        nombres = self.nombres_alternativas()
        actual = self.vista_actual() if self.vistas else None
        for v in self.vistas:
            v.poner_alternativas(nombres, elegir if v is actual else None)
        self._ver()

    def _alt(self):
        if not getattr(self, 'vistas', None):
            return None
        return self.vista_actual().alt()

    def _renombrar_alt(self):
        if self._esperar():
            return
        alt = self._alt()
        if not alt:
            return
        n = simpledialog.askstring(TITULO, 'Nombre de este horario:', initialvalue=alt.get('nombre') or '', parent=self)
        if n and n.strip():
            alt['nombre'] = n.strip()
            self._actualizar_fila()

    # --- Vistas (pestañas y ventanas aparte) -------------------------------------
    def nueva_pestana(self, tipo=0):
        marco = ttk.Frame(self.nb_vistas)
        v = Vista(self, marco, cerrable=bool(self.vistas))
        self.nb_vistas.add(marco, text=f'Vista {len(self.vistas) + 1}')
        v.marco_pestana = marco
        actual = self.vista_actual() if self.vistas else None
        v.idx = actual.indice() if actual else 0
        self.vistas.append(v)
        v.poner_alternativas(self.nombres_alternativas(), None, redibujar=False)
        v.cb_ver.current(tipo)
        v.opciones()
        try:
            self.nb_vistas.select(marco)
        except tk.TclError:
            pass
        return v

    def nueva_ventana(self):
        w = tk.Toplevel(self)
        w.title(f'{TITULO} · otra vista')
        w.geometry('1000x700')
        v = Vista(self, w, cerrable=False)
        v.ventana = w
        v.idx = self.vista_actual().indice() if self.vistas else 0
        self.vistas.append(v)
        v.poner_alternativas(self.nombres_alternativas(), None, redibujar=False)

        def cerrar():
            if v in self.vistas:
                self.vistas.remove(v)
            w.destroy()
        w.protocol('WM_DELETE_WINDOW', cerrar)
        w.bind('<Escape>', lambda e: self.quitar_seleccion())
        v.opciones()
        return v

    def cerrar_vista(self, v):
        if v in self.vistas and len(self.vistas) > 1:
            self.vistas.remove(v)
            if getattr(v, 'marco_pestana', None) is not None:
                self.nb_vistas.forget(v.marco_pestana)
                v.marco_pestana.destroy()
            self._renombrar_pestanas()

    def _renombrar_pestanas(self):
        for v in self.vistas:
            if getattr(v, 'marco_pestana', None) is not None:
                try:
                    self.nb_vistas.tab(v.marco_pestana, text=v.titulo())
                except tk.TclError:
                    pass

    def vista_actual(self):
        try:
            actual = self.nb_vistas.select()
        except tk.TclError:
            actual = None
        for v in self.vistas:
            if actual and str(getattr(v, 'marco_pestana', '')) == str(actual):
                return v
        return self.vistas[0]

    # Compatibilidad (la prueba y el resto del código hablan de «la» vista)
    cb_ver = property(lambda self: self.vista_actual().cb_ver)
    cb_quien = property(lambda self: self.vista_actual().cb_quien)
    quien_l = property(lambda self: self.vista_actual().quien_l)
    rejilla = property(lambda self: self.vista_actual().rejilla)
    paleta = property(lambda self: self.vista_actual().paleta)

    def _opciones_ver(self):
        self.vista_actual().opciones()

    def _ver(self):
        self.sel = None
        self._avisos(self._alt())
        for v in list(self.vistas):
            v.dibujar()
        self._actualizar_fila()

    # --- Selección: verde / amarillo / rojo --------------------------------------
    def _vista_de(self, datos):
        v = datos.get('vista') if isinstance(datos, dict) else None
        return v if v in getattr(self, 'vistas', []) else self.vista_actual()

    def escoger(self, datos):
        alt = self._vista_de(datos).alt()
        if not alt or (alt.get('vivo') and self._esperar()):
            return
        self._sel_alt = alt
        self.sel = datos
        largo = datos.get('largo', 1) if datos['tipo'] == 'nueva' else 1
        if datos['tipo'] == 'nueva':
            aid, i = datos['asig'], None
        else:
            i = datos['i']
            aid = alt['sesiones'][i]['asignacion']
        self._mapa = self.p.mapa_destinos(alt, aid, i, largo)
        self._pintar_seleccion()
        D = self.p.datos
        a = D.asignaciones[aid]
        libres = sum(1 for e in self._mapa.values() if e == 'libre')
        self.avisar(f'{D.nombre_materia(a["materia"])} · {D.nombre_curso(a["curso"])}: {libres} hora(s) libres en verde. '
                    'Amarillo = ocupada, se puede reemplazar o intercambiar.')

    def _pintar_seleccion(self):
        if not self.sel or not getattr(self, '_mapa', None):
            return
        for v in self.vistas:
            if v.alt() is getattr(self, '_sel_alt', None):      # solo las pestañas que muestran ese horario
                v.pintar(self._mapa)

    def quitar_seleccion(self, redibujar=True):
        if self.sel:
            self.sel = None
            if redibujar:
                for v in self.vistas:
                    v.dibujar()

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
            comp = self.p.texto_compensacion(alt) + self.p.texto_viajan(alt)
            if comp:
                t.insert('end', '\nDías largos compensados (día largo ↔ día corto):\n')
                for x in comp[:12]:
                    t.insert('end', f'  • {x}\n')
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

    # Fichas que se arrastran (o se tocan para escogerlas)
    def _ficha(self, padre, texto, color, datos, z=1.0):
        lbl = tk.Label(padre, text=texto, bg=color, font=('Segoe UI', max(6, round(8 * z))), justify='center',
                       wraplength=int(140 * z),
                       relief='raised' if datos else 'flat', bd=1, cursor='hand2' if datos else '')
        if datos:
            lbl.bind('<ButtonPress-1>', lambda e: self._tomar(e, datos, texto, color))
            lbl.bind('<B1-Motion>', self._arrastrar)
            lbl.bind('<ButtonRelease-1>', self._soltar_evento)
            if datos['tipo'] == 'puesta':
                lbl.bind('<Button-3>', lambda e: self._menu_ficha(e, datos['i'], datos.get('vista')))
                lbl.bind('<Control-Button-1>', lambda e: self.marcar(datos))
                v = datos.get('vista')
                if v is not None and v.alt() is self._marcadas_alt and datos['i'] in self.marcadas:
                    lbl.configure(relief='solid', bd=3, highlightthickness=2, highlightbackground='#1d4ed8')
        return lbl

    def _tomar(self, e, datos, texto, color):
        self._arr = {'datos': datos, 'x': e.x_root, 'y': e.y_root, 'texto': texto, 'color': color, 'ventana': None}
        self.escoger(datos)

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
            return                       # fue un toque: la ficha queda escogida (colores)
        a['ventana'].destroy()
        w = self.winfo_containing(e.x_root, e.y_root)
        while w is not None and not hasattr(w, 'destino'):
            w = w.master
        if w is not None:
            self.soltar(a['datos'], w.destino)
        else:
            self.quitar_seleccion()

    def tocar_celda(self, destino):
        """Con una ficha escogida, tocar una casilla la pone ahí."""
        if self.sel:
            self.soltar(self.sel, destino)

    def soltar(self, datos, destino):
        """Aplica una ficha soltada en una celda o en la paleta."""
        alt = self._vista_de(datos).alt()
        if not alt or (alt.get('vivo') and self._esperar()):
            return
        self._paso(alt)
        if len(destino) > 3 and destino[3] is not None and destino[3].alt() is not alt:
            self.avisar('✖ Esa pestaña muestra otro horario: suelte la ficha en una que muestre el mismo.', error=True)
            self.bell()
            return self._ver()
        motivo = None
        fijar = bool(self.var_fijar.get())
        hecho = 'Ficha ubicada' + (' y fijada (🔒).' if fijar else '.')
        if destino[0] == 'paleta':
            if datos['tipo'] == 'puesta':
                self.p.quitar_ficha(alt, datos['i'])
                self.avisar('Ficha sacada del horario.')
        else:
            i = datos.get('i')
            aid = datos['asig'] if datos['tipo'] == 'nueva' else alt['sesiones'][i]['asignacion']
            largo = datos.get('largo', 1) if i is None else 1
            if largo > 1:
                estado, texto, est = self.p.destino_bloque(alt, aid, destino[1], destino[2], largo)
            else:
                estado, texto, est = self.p.destino(alt, aid, destino[1], destino[2], i)
            if estado == 'libre':
                if largo > 1:
                    motivo = self.p.poner_bloque(alt, aid, destino[1], destino[2], largo, fijar)
                    hecho = f'Bloque de {largo} horas ubicado' + (' y fijado (🔒).' if fijar else '.')
                else:
                    motivo = (self.p.poner_ficha(alt, aid, destino[1], destino[2], fijar) if i is None
                              else self.p.mover_ficha(alt, i, destino[1], destino[2], fijar))
            elif estado == 'imposible':
                motivo = texto
            else:
                motivo = self._ocupada(alt, aid, i, destino, texto, est, fijar, largo)
                if motivo is False:          # canceló
                    self.avisar('No se cambió nada.')
                    return self._ver()
                if motivo is True:
                    motivo, hecho = None, 'Fichas intercambiadas.'
                elif motivo is None:
                    hecho = 'Hora reemplazada: la ficha que estaba vuelve a «Fichas por ubicar».'
        if motivo:
            self.avisar('✖ ' + motivo, error=True)
            self.bell()
        elif destino[0] == 'celda':
            self.avisar('✔ ' + hecho)
        self._actualizar_fila()
        self._ver()

    def _ocupada(self, alt, aid, i, destino, texto, est, fijar, largo=1):
        """Casilla amarilla: intercambiar (si se puede), reemplazar o cancelar.
        Devuelve True si intercambió, None si reemplazó, False si canceló, o el motivo si falló."""
        puede_intercambiar = i is not None and len(est) == 1
        if puede_intercambiar:
            r = messagebox.askyesnocancel(TITULO, texto + '\n\n«Sí»: intercambiar las dos fichas de lugar.\n'
                                          '«No»: reemplazar (la que estaba vuelve a «Fichas por ubicar»).\n'
                                          '«Cancelar»: dejar todo como está.')
            if r is None:
                return False
            if r:
                m = self.p.intercambiar(alt, i, destino[1], destino[2])
                if not m:
                    return True
                if not messagebox.askyesno(TITULO, m + '\n\nNo se pueden intercambiar. ¿Reemplazar la hora de todas formas?'):
                    return False
        elif not messagebox.askyesno(TITULO, texto + '\n\n¿Reemplazar esa hora? Lo que estaba vuelve a «Fichas por ubicar».'):
            return False
        return self.p.reemplazar(alt, aid, destino[1], destino[2], i, fijar, largo)

    def _actualizar_fila(self):
        nombres = self.nombres_alternativas()
        for v in self.vistas:
            v.poner_alternativas(nombres, None, redibujar=False)
        self._renombrar_pestanas()
        alt = self._alt()
        if alt is not None and hasattr(self, 'btn_avisos'):
            n = alt.get('horas_sin_ubicar', 0) + len(alt.get('choques') or [])
            self.btn_avisos.configure(text=f'⚠ Avisos ({n})' if n else '✔ Avisos')

    def _menu_paleta(self, e, aid):
        m = tk.Menu(self, tearoff=0)
        if aid in self.sueltas:
            m.add_command(label='Volver a ubicar en bloques', command=lambda: (self.sueltas.discard(aid), self._ver()))
        else:
            m.add_command(label='Ubicar de a una hora (partir el bloque)', command=lambda: (self.sueltas.add(aid), self._ver()))
        m.tk_popup(e.x_root, e.y_root)

    def _menu_ficha(self, e, i, vista=None):
        alt = (vista or self.vista_actual()).alt()
        if not alt or (alt.get('vivo') and self._esperar()):
            return
        m = tk.Menu(self, tearoff=0)
        fijada = alt['sesiones'][i].get('fijada')
        m.add_command(label='Soltar (el generador la puede mover)' if fijada else 'Fijar 🔒 (el generador no la mueve)',
                      command=lambda: (self._paso(alt), self.p.alternar_fijada(alt, i), self._ver()))
        m.add_command(label='Quitar del horario', command=lambda: self.soltar({'tipo': 'puesta', 'i': i, 'vista': vista},
                                                                             ('paleta',)))
        m.tk_popup(e.x_root, e.y_root)

    def _exportar(self):
        if self._esperar():
            return
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
        if self._esperar():
            return
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
        if self._esperar():
            return
        v = self.vista_actual()
        k = v.indice()
        if k is None or not messagebox.askyesno(TITULO, '¿Quitar este horario de la lista?'):
            return
        del self.p.alternativas[k]
        for otra in self.vistas:
            j = otra.indice()
            if j is not None and j > k:
                otra.idx = j - 1
            elif j == k:
                otra.idx = 0
        self._llenar_alternativas(elegir=0 if v.idx is None else v.idx)


class Vista:
    """Una cuadrícula del horario (por curso o por docente). Puede haber varias: en pestañas o en
    ventanas aparte. Cada una escoge qué horario (alternativa) muestra."""

    def __init__(self, app, padre, cerrable=False, compacta=False):
        self.app = app
        self.quien_l = []
        self.celdas = []
        self.idx = 0
        self.filtros = []
        self.zoom = 1.0
        self._necesario = 0
        anchos = (22, 10, 14, 22) if compacta else (34, 12, 20, 34)
        sel = ttk.Frame(padre)
        sel.pack(fill='x', pady=(4, 0))
        if not compacta:
            ttk.Label(sel, text='Horario:').pack(side='left')
        self.cb_alt = ttk.Combobox(sel, state='readonly', width=anchos[0])
        self.cb_alt.pack(side='left', padx=(3, 8))
        self.cb_alt.bind('<<ComboboxSelected>>', lambda e: self._cambio_alt())
        self.cb_ver = ttk.Combobox(sel, state='readonly', values=['Por curso', 'Por docente'], width=anchos[1])
        self.cb_ver.current(0)
        self.cb_ver.pack(side='left')
        self.cb_filtro = ttk.Combobox(sel, state='readonly', width=anchos[2])
        self.cb_filtro.pack(side='left', padx=4)
        self.cb_quien = ttk.Combobox(sel, state='readonly', width=anchos[3])
        self.cb_quien.pack(side='left', padx=2)
        self.cb_ver.bind('<<ComboboxSelected>>', lambda e: self.opciones())
        self.cb_filtro.bind('<<ComboboxSelected>>', lambda e: self.opciones(conservar_filtro=True))
        self.cb_quien.bind('<<ComboboxSelected>>', lambda e: (self.dibujar(), app._renombrar_pestanas()))
        if cerrable:
            ttk.Button(sel, text='✖ Cerrar pestaña', command=lambda: app.cerrar_vista(self)).pack(side='right')
        self.cb_color = ttk.Combobox(sel, state='readonly', width=16 if not compacta else 12,
                                     values=['Color normal', 'Color por área', 'Color por docente'])
        self.cb_color.current(0)
        self.cb_color.pack(side='right', padx=4)
        self.cb_color.bind('<<ComboboxSelected>>', lambda e: self.dibujar())
        self.var_paleta = tk.BooleanVar(value=not compacta)
        ttk.Checkbutton(sel, text='Fichas', variable=self.var_paleta, command=self._mostrar_paleta).pack(side='right', padx=6)
        ttk.Button(sel, text='+', width=2, command=lambda: self.cambiar_zoom(0.1)).pack(side='right')
        ttk.Button(sel, text='−', width=2, command=lambda: self.cambiar_zoom(-0.1)).pack(side='right')
        self.leyenda = tk.Frame(padre)
        self.leyenda.pack(fill='x')
        abajo = ttk.Frame(padre)
        abajo.pack(fill='both', expand=True, pady=4)
        self.paleta = tk.Frame(abajo, background=GRIS, width=190)
        self.paleta.pack(side='left', fill='y')
        self.paleta.pack_propagate(False)
        self.paleta.destino = ('paleta',)
        marco = ttk.Frame(abajo)
        marco.pack(side='left', fill='both', expand=True, padx=(6, 0))
        self.marco = marco
        self.lienzo = tk.Canvas(marco, background=BLANCO, highlightthickness=0)
        sy = ttk.Scrollbar(marco, orient='vertical', command=self.lienzo.yview)
        sx = ttk.Scrollbar(marco, orient='horizontal', command=self.lienzo.xview)
        self.lienzo.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side='right', fill='y')
        sx.pack(side='bottom', fill='x')
        self.lienzo.pack(side='left', fill='both', expand=True)
        self.rejilla = tk.Frame(self.lienzo, background=BLANCO)
        self.ventana_rejilla = self.lienzo.create_window((0, 0), window=self.rejilla, anchor='nw')
        self.rejilla.bind('<Configure>', lambda e: self.lienzo.configure(scrollregion=self.lienzo.bbox('all')))
        # La cuadrícula ocupa todo el ancho (y si con el zoom no cabe, aparece la barra de abajo)
        self.lienzo.bind('<Configure>', lambda e: self._ajustar_ancho(e.width))
        self.lienzo.vista_duena = self
        self.rejilla.vista_duena = self
        self.paleta.vista_duena = self

    def _ajustar_ancho(self, ancho=None):
        try:
            ancho = ancho or self.lienzo.winfo_width() or 0
            self.lienzo.itemconfigure(self.ventana_rejilla, width=max(int(ancho), self._necesario))
        except (tk.TclError, TypeError, ValueError):
            pass

    def cambiar_zoom(self, delta):
        """Agranda o achica esta cuadrícula (None = tamaño normal)."""
        z = 1.0 if delta is None else round(min(2.0, max(0.5, self.zoom + delta)), 2)
        if z != self.zoom:
            self.zoom = z
            self.dibujar()
        self.app.avisar(f'Tamaño de la cuadrícula: {int(round(self.zoom * 100))} %  (Ctrl + rueda del mouse también sirve)')

    def _mostrar_paleta(self):
        if self.var_paleta.get():
            self.paleta.pack(side='left', fill='y', before=self.marco)
        else:
            self.paleta.pack_forget()

    # Qué horario muestra esta pestaña
    def indice(self):
        n = len(self.app.p.alternativas)
        return self.idx if self.idx is not None and 0 <= self.idx < n else (0 if n else None)

    def alt(self):
        if self.app.generando and self.app.alt_vivo is not None:
            return self.app.alt_vivo
        k = self.indice()
        return self.app.p.alternativas[k] if k is not None else None

    def poner_alternativas(self, nombres, elegir=None, redibujar=True):
        self.cb_alt.configure(values=nombres)
        if elegir is not None:
            self.idx = elegir
        k = self.indice()
        if k is not None:
            self.cb_alt.current(k)
            self.idx = k
        else:
            self.cb_alt.set('')
        if redibujar:
            self.dibujar()

    def _cambio_alt(self):
        self.idx = self.cb_alt.current()
        self.app.quitar_seleccion(redibujar=False)
        self.app._avisos(self.alt())
        self.app._actualizar_fila()
        self.dibujar()

    def titulo(self):
        k = self.cb_quien.current()
        if k is None or k < 0 or k >= len(self.quien_l):
            return 'Vista'
        tipo, ident = self.quien_l[k]
        D = self.app.p.datos
        if tipo == 'c':
            t = D.nombre_curso(ident)
        else:
            partes = D.nombre_docente(ident).split(' ')
            t = ' '.join(partes[:2])
        if len(self.app.p.alternativas) > 1 and self.indice():
            t += f' · alt. {self.indice() + 1}'
        return t

    def opciones(self, conservar_filtro=False):
        """Llena la lista de cursos (filtrada por grado) o de docentes (filtrada por área)."""
        D = self.app.p.datos
        docente = self.cb_ver.current() == 1
        if not conservar_filtro:
            if docente:
                self.filtros = [('', 'Todas las áreas')] + [(ar, ar) for ar in sorted(D.areas)]
            else:
                grados = sorted({c.get('grado') for c in D.crudo['cursos'] if c['id'] in D.jornada_de_curso},
                                key=lambda g: (g is None, g if g is not None else 0))
                self.filtros = [('', 'Todos los grados')] + [(g, nombre_grado(g)) for g in grados]
            self.cb_filtro.configure(values=[n for _, n in self.filtros])
            self.cb_filtro.current(0)
        k = self.cb_filtro.current()
        filtro = self.filtros[k][0] if k is not None and 0 <= k < len(self.filtros) else ''
        if docente:
            con_clase = {a.get('docente') for a in D.asignaciones.values()}
            del_area = set(D.docentes_de_area(filtro)) if filtro != '' else None
            self.quien_l = [('d', d['id']) for d in sorted(D.docentes.values(), key=lambda d: d['nombre'])
                            if d['id'] in con_clase and (del_area is None or d['id'] in del_area)]
            nombres = [D.nombre_docente(x) for _, x in self.quien_l]
        else:
            self.quien_l = [('c', c['id']) for c in D.crudo['cursos'] if c['id'] in D.jornada_de_curso
                            and (filtro == '' or c.get('grado') == filtro)]
            nombres = [D.nombre_curso(x) for _, x in self.quien_l]
        self.cb_quien.configure(values=nombres)
        if nombres:
            self.cb_quien.current(0)
        else:
            self.cb_quien.set('')
        self.dibujar()
        self.app._renombrar_pestanas()

    def pintar(self, mapa):
        for celda, destino in self.celdas:
            color = COLOR_SEL.get(mapa.get((destino[1], destino[2])))
            if color:
                try:
                    celda.configure(highlightthickness=3, highlightbackground=color, highlightcolor=color)
                    if not celda.winfo_children():
                        celda.configure(bg=color)
                except tk.TclError:
                    pass

    def color_de(self, aid):
        """Color de la ficha según «Color por área / por docente» (None = el normal)."""
        modo = self.cb_color.current()
        D = self.app.p.datos
        a = D.asignaciones.get(aid)
        if not modo or not a:
            return None
        if modo == 1:
            claves = sorted(D.areas)
            k = D.materias.get(a['materia'], {}).get('area')
        else:
            claves = sorted(D.docentes, key=D.nombre_docente)
            k = a.get('docente')
        if k not in claves:
            return '#f1f5f9'
        return PALETA[claves.index(k) % len(PALETA)]

    def _poner_leyenda(self, alt):
        for w in self.leyenda.winfo_children():
            w.destroy()
        modo = self.cb_color.current()
        if not modo or not alt:
            return
        D = self.app.p.datos
        vistos = {}
        for s in alt['sesiones']:
            a = D.asignaciones.get(s['asignacion'])
            if not a:
                continue
            if modo == 1:
                nombre = D.materias.get(a['materia'], {}).get('area') or 'Sin área'
            else:
                nombre = D.nombre_docente(a.get('docente'))
            vistos.setdefault(nombre, self.color_de(s['asignacion']))
        for nombre, color in sorted(vistos.items())[:24]:
            tk.Label(self.leyenda, text=f' {nombre[:28]} ', bg=color, font=('Segoe UI', 8)).pack(side='left', padx=1, pady=1)

    def dibujar(self):
        app = self.app
        for w in list(self.rejilla.winfo_children()) + list(self.paleta.winfo_children()):
            w.destroy()
        self.celdas = []
        alt = self.alt()
        if not alt or self.cb_quien.current() < 0 or not self.quien_l:
            tk.Label(self.rejilla, text='Genere un horario o cree uno en blanco para verlo aquí.', bg=BLANCO,
                     fg='#666').grid(padx=20, pady=20)
            return
        tipo, ident = self.quien_l[self.cb_quien.current()]
        D = app.p.datos
        z = self.zoom
        chica, negrita = ('Segoe UI', max(6, round(8 * z))), ('Segoe UI', max(6, round(9 * z)), 'bold')
        if alt.get('vivo'):
            tk.Label(self.rejilla, text=f"{alt['nombre']}  ·  faltan {alt['horas_sin_ubicar']} h", bg=AMARILLO,
                     font=negrita).grid(row=0, column=0, columnspan=7, sticky='ew', pady=(0, 3))
        tk.Label(self.paleta, text='Fichas por ubicar', bg=GRIS, font=('Segoe UI', 9, 'bold')).pack(anchor='w', padx=6, pady=4)
        pend = app.p.pendientes(alt, ident) if tipo == 'c' else app.p.pendientes_docente(alt, ident)
        for a, n in pend:
            # Una ficha por cada tamaño de bloque que falta (2 h, 1 h…), en el orden que usted quiera.
            if a['id'] in app.sueltas:
                piezas = [1] * n
            else:
                piezas = app.p.piezas_pendientes(alt, a['id'])
                if sum(piezas) != n:
                    piezas = [1] * n
            cuantas = {}
            for x in piezas:
                cuantas[x] = cuantas.get(x, 0) + 1
            for largo in sorted(cuantas, reverse=True):
                k = cuantas[largo]
                que = f'bloque {largo} h' if largo > 1 else '1 h'
                if tipo == 'c':
                    texto = f"{D.nombre_materia(a['materia'])} · {que}{f' ×{k}' if k > 1 else ''}\n{D.nombre_docente(a.get('docente'))}"
                else:
                    texto = f"{D.nombre_curso(a['curso'])} · {D.nombre_materia(a['materia'])} · {que}{f' ×{k}' if k > 1 else ''}"
                color = BLOQUE if largo > 1 else SUELTA
                ficha = app._ficha(self.paleta, texto, color, {'tipo': 'nueva', 'asig': a['id'], 'largo': largo,
                                                               'vista': self}, z)
                ficha.pack(fill='x', padx=6, pady=2)
                ficha.bind('<Button-3>', lambda e, aid=a['id']: app._menu_paleta(e, aid))
        if not pend:
            tk.Label(self.paleta, text='✔ Todas ubicadas', bg=GRIS, fg='#14532d').pack(anchor='w', padx=6)
        tk.Label(self.paleta, text='Suelte aquí una ficha\npara sacarla del horario.', bg=GRIS, fg='#888',
                 font=('Segoe UI', 8)).pack(side='bottom', pady=6)
        self._poner_leyenda(alt)
        tablas = [app.p.tabla_curso(alt, ident)] if tipo == 'c' else app.p.tablas_docente(alt, ident)
        n_dias = max((len(t['dias']) for t in tablas if t), default=5)
        for c in range(1, 7):
            self.rejilla.columnconfigure(c, weight=1 if c <= n_dias else 0, uniform='dia' if c <= n_dias else '')
        self._necesario = int((60 + n_dias * 114) * z)
        self._ajustar_ancho()
        fila = 1 if alt.get('vivo') else 0
        for t in tablas:
            if not t:
                continue
            if len(tablas) > 1:
                tk.Label(self.rejilla, text=t['jornada']['nombre'], font=negrita, bg=BLANCO).grid(
                    row=fila, column=0, sticky='w', pady=(8, 2))
                fila += 1
            for c, (_, nombre) in enumerate(t['dias'], start=1):
                tk.Label(self.rejilla, text=nombre, font=negrita, bg=AZUL, fg='white').grid(
                    row=fila, column=c, padx=1, pady=1, sticky='nsew')
            fila += 1
            for fr, celdas in t['filas']:
                tk.Label(self.rejilla, text=f"{fr['inicio']}\n{fr['fin']}", bg=BLANCO, fg='#555', font=chica).grid(
                    row=fila, column=0, padx=(0, 2))
                if fr['descanso'] and not any(celdas):
                    tk.Label(self.rejilla, text=fr.get('etiqueta') or 'Descanso', bg=GRIS, fg='#888', font=chica).grid(
                        row=fila, column=1, columnspan=len(t['dias']), sticky='nsew', padx=1, pady=1)
                elif fr['descanso']:
                    for c, xs in enumerate(celdas, start=1):
                        texto = '\n'.join(f"{x['titulo']}" for x in xs) or (fr.get('etiqueta') or 'Descanso')
                        tk.Label(self.rejilla, text=texto, bg=TURNO if xs else GRIS, fg='#0f172a' if xs else '#888',
                                 font=chica).grid(row=fila, column=c, sticky='nsew', padx=1, pady=1)
                else:
                    for c, ((dia, _), xs) in enumerate(zip(t['dias'], celdas), start=1):
                        celda = tk.Frame(self.rejilla, bg=GRIS if not xs else BLANCO, width=int(110 * z), height=int(50 * z),
                                         highlightthickness=1, highlightbackground='#e2e8f0')
                        celda.grid(row=fila, column=c, padx=1, pady=1, sticky='nsew')
                        celda.grid_propagate(False)
                        celda.pack_propagate(False)
                        celda.destino = ('celda', dia, fr['id'], self)
                        celda.bind('<Button-1>', lambda e, d=celda.destino: app.tocar_celda(d))
                        self.celdas.append((celda, celda.destino))
                        for x in xs:
                            color = (REUNION if x.get('reunion') else ACTIVIDAD if x.get('actividad')
                                     else FIJA if x['fijada'] else SUELTA)
                            if x.get('i') is not None and not x.get('reunion') and not x.get('actividad'):
                                color = self.color_de(alt['sesiones'][x['i']]['asignacion']) or color
                            texto = ('🔒 ' if x.get('i') is not None and x['fijada'] else '') + f"{x['titulo']}\n{x['sub']}"
                            datos = {'tipo': 'puesta', 'i': x['i'], 'vista': self} if x.get('i') is not None else None
                            if alt.get('vivo'):
                                datos = None                      # mientras genera, solo se mira
                            app._ficha(celda, texto, color, datos, z).pack(fill='both', expand=True, padx=1, pady=1)
                fila += 1


def nombre_grado(g):
    if g is None:
        return 'Sin grado'
    return {-2: 'Prejardín', -1: 'Jardín', 0: 'Transición'}.get(g, f'Grado {g}')


def main():
    App().mainloop()


if __name__ == '__main__':
    main()
