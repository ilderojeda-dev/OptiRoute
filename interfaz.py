"""OptiRoute V2. Presentación Tkinter sobre la API original de logica."""
# ------------------------------------------------------------------------
# 1. IMPORTACIONES
# Bibliotecas de la interfaz, comunicación entre hilos y acceso al módulo logica.
# ------------------------------------------------------------------------
import math
import sys
import ctypes
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont

import logica

# ------------------------------------------------------------------------
# 2. CONFIGURACIÓN VISUAL Y UNIDADES
# Define colores, altura fija del bloque inferior y unidades disponibles.
# ------------------------------------------------------------------------
NAVY = '#142c4e'
BLUE = '#1769aa'
GREEN = '#16805b'
RED = '#bf3545'
VIOLET = '#952bc1'
BG = '#f1f5fa'
ALTURA_BLOQUE_INFERIOR = 280  # Independiente de N y de la longitud de los pesos.
UNIDADES = {'Distancia': ('km', 'm'), 'Tiempo': ('min', 'h', 's'),
            'Combustible': ('L', 'gal'), 'Costo monetario': ('S/', 'USD', 'EUR'),
            'Personalizado': ('unidades',)}


# ------------------------------------------------------------------------
# 3. NITIDEZ EN WINDOWS
# Configura el reconocimiento DPI antes de crear la ventana de Tkinter.
# ------------------------------------------------------------------------
def configurar_nitidez():
    """Antes de crear Tk: renderizado al DPI del sistema, sin estirar un bitmap.

    No cambia la configuración de Windows. Se usa System Aware porque esta
    interfaz Tk no implementa todavía un relayout por cambio de monitor/DPI.
    """
    if sys.platform != 'win32':
        return
    try:
        # 1 = PROCESS_SYSTEM_DPI_AWARE. Un modo ya fijado se conserva.
        result = ctypes.windll.shcore.SetProcessDpiAwareness(1)
        if result in (0, -2147024891):
            return
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass


# ------------------------------------------------------------------------
# 4. COMPONENTES REUTILIZABLES: TEXTO
# Presenta etiquetas, valores y rutas con jerarquía tipográfica y ajuste de ancho.
# ------------------------------------------------------------------------
class DetailBlock(ttk.Frame):
    """Texto con jerarquía y ajuste de ancho, sin altura fija ni recortes."""
    def __init__(self, parent, color=NAVY):
        super().__init__(parent)
        self.content = ''
        self.color = color
        self.pack(fill='x', pady=5)
        self.bind('<Configure>', self._resize)

    def _resize(self, event):
        for child in self.winfo_children():
            child.configure(wraplength=max(100, event.width-8))

    def configure(self, **kwargs):
        if 'text' not in kwargs and 'foreground' not in kwargs:
            return super().configure(**kwargs)
        self.content = kwargs.get('text', self.content)
        self.color = kwargs.get('foreground', self.color)
        for child in self.winfo_children():
            child.destroy()
        for paragraph in self.content.split('\n\n'):
            if ': ' in paragraph and ' → ' not in paragraph:
                title, value = paragraph.split(': ', 1)
                ttk.Label(self, text=title+':', font=('Segoe UI',10,'bold'),
                          foreground=NAVY).pack(anchor='w', pady=(5,2))
                ttk.Label(self, text=value, foreground=self.color,
                          wraplength=230).pack(anchor='w', fill='x', pady=(0,4))
            else:
                ttk.Label(self, text=paragraph, foreground=self.color,
                          font=('Segoe UI',11,'bold') if ' → ' in paragraph else ('Segoe UI',10),
                          wraplength=230).pack(anchor='w', fill='x', pady=4)

    def cget(self, key):
        return self.content if key == 'text' else super().cget(key)


# ------------------------------------------------------------------------
# 5. COMPONENTES REUTILIZABLES: DESPLAZAMIENTO
# Combina un canvas, un contenedor y una barra para desplazar paneles extensos.
# ------------------------------------------------------------------------
class ScrollPanel(ttk.Frame):
    def __init__(self, parent, width):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, width=width, bg=BG, highlightthickness=0)
        bar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=bar.set)
        self.canvas.pack(side='left', fill='both', expand=True)
        bar.pack(side='right', fill='y')
        self.body = ttk.Frame(self.canvas, padding=8)
        item = self.canvas.create_window(0, 0, anchor='nw', window=self.body)
        self.body.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure(item, width=e.width))
        # La rueda solo desplaza el panel bajo el puntero (también sus controles).
        self.bind_all('<MouseWheel>', self._wheel, add='+')

    def _wheel(self, event):
        widget = event.widget
        while widget:
            if widget == self:
                self.canvas.yview_scroll(-int(event.delta / 120), 'units')
                break
            widget = getattr(widget, 'master', None)


# ------------------------------------------------------------------------
# 6. COMPONENTES REUTILIZABLES: SECCIONES PLEGABLES
# Muestra u oculta controles sin destruirlos ni perder los datos ingresados.
# ------------------------------------------------------------------------
class SeccionPlegable(ttk.Frame):
    """Oculta el contenido sin destruir controles ni perder sus valores."""
    def __init__(self, parent, title, abierta=False):
        super().__init__(parent)
        self.title = title
        self.abierta = abierta
        self.pack(fill='x', pady=(0, 10))
        self.header = ttk.Button(self, command=self.alternar, style='Section.TButton')
        self.header.pack(fill='x')
        self.body = ttk.Frame(self, padding=(10, 8))
        self._actualizar()

    def alternar(self):
        self.abierta = not self.abierta
        self._actualizar()

    def _actualizar(self):
        self.header.configure(text=f'{"▾" if self.abierta else "▸"} {self.title}')
        if self.abierta:
            self.body.pack(fill='x')
        else:
            self.body.pack_forget()


# ------------------------------------------------------------------------
# 7. APLICACIÓN PRINCIPAL
# Coordina los controles, los datos del grafo, la ejecución y su representación.
# ------------------------------------------------------------------------
class OptiRouteApp:
    def __init__(self, root):
        self.root = root
        root.title('OptiRoute V2 · Agente viajero')
        root.geometry('1280x800')
        root.minsize(960, 620)
        root.state('zoomed')
        root.configure(bg=BG)
        # Estilos de fuentes, colores, bordes y estados de los controles.
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 10))
        style.configure('TFrame', background=BG)
        style.configure('TLabel', background=BG, foreground=NAVY)
        style.configure('TLabelframe', background=BG)
        style.configure('TLabelframe.Label', background=BG, foreground=BLUE, font=('Segoe UI', 10, 'bold'))
        style.configure('TButton', padding=(8, 6), background='#e7eef7', foreground=NAVY)
        style.map('TButton', background=[('pressed', '#cbddef'), ('active', '#dceafa'), ('!active', '#e7eef7')])
        style.map('TCombobox', fieldbackground=[('readonly', 'white')],
                  selectbackground=[('!focus', 'white')], selectforeground=[('!focus', NAVY)])
        # Limpiar la selección de texto al salir; mantener el foco visible para teclado.
        root.bind_class('TCombobox', '<FocusOut>', lambda e: e.widget.selection_clear(), add='+')
        style.configure('Accent.TButton', background=BLUE, foreground='white')
        style.map('Accent.TButton', background=[('pressed', NAVY), ('active', '#2180c5'), ('!active', BLUE)])
        # Bordes planos, contraste y estados consistentes; se conserva el foco.
        style.configure('TLabelframe', borderwidth=1, relief='solid', bordercolor='#dce5ef')
        style.configure('TButton', font=('Segoe UI', 10, 'bold'), borderwidth=1,
                        relief='flat', bordercolor='#d5e1ee', lightcolor='#e7eef7',
                        darkcolor='#e7eef7', padding=(10, 8))
        style.map('TButton', foreground=[('disabled', '#8997a9')],
                  bordercolor=[('focus', BLUE), ('!focus', '#d5e1ee')])
        # Encabezados de sección: alineación común y color distinto de las acciones.
        style.configure('Section.TButton', anchor='w', padding=(14, 11),
                        font=('Segoe UI', 10, 'bold'), background=NAVY,
                        foreground='white', bordercolor=NAVY,
                        lightcolor=NAVY, darkcolor=NAVY)
        style.map('Section.TButton',
                  background=[('pressed', '#0c203b'), ('active', '#23466d'), ('!active', NAVY)],
                  foreground=[('disabled', '#a9b8cb'), ('!disabled', 'white')],
                  bordercolor=[('focus', '#20a6c9'), ('!focus', NAVY)])
        style.configure('TEntry', padding=5, fieldbackground='white', bordercolor='#c9d7e6',
                        lightcolor='white', darkcolor='white')
        style.configure('TCombobox', padding=5, arrowsize=14, background='#e7eef7',
                        bordercolor='#c9d7e6', lightcolor='white', darkcolor='white')
        style.configure('TCheckbutton', background=BG, foreground=NAVY, padding=4)
        for orientation in ('Vertical', 'Horizontal'):
            style.configure(orientation+'.TScrollbar', background='#b5c6da',
                            troughcolor='#edf2f8', borderwidth=0, arrowsize=13,
                            lightcolor='#b5c6da', darkcolor='#b5c6da')
        style.configure('Treeview', rowheight=30, background='white', fieldbackground='white',
                        foreground=NAVY, borderwidth=0)
        style.configure('Treeview.Heading', font=('Segoe UI',10,'bold'),
                        background='#e7eef7', foreground=NAVY, relief='flat', padding=7)
        # Estado inicial: variables enlazadas a controles y datos de la ejecución.
        self.n = tk.StringVar(value='5')
        self.tipo = tk.StringVar(value='Distancia')
        self.unidad = tk.StringVar(value='km')
        self.minimo = tk.StringVar(value='1')
        self.maximo = tk.StringVar(value='20')
        self.peso = tk.StringVar(value='10')
        self.solo_ruta = tk.BooleanVar(value=False)
        self.nombres = [''] * 10
        self.matriz = None
        self.resultado = None
        self.indice_paso = -1
        self.ruta = None
        self.color = GREEN
        self.busy = False
        self.revision = 0
        self.vista = 'inicio'
        # La cola transporta resultados del hilo de cálculo al hilo principal de Tk.
        self.cola = queue.Queue()
        self.ventanas_ciclos = []
        self.controles_mutables = []
        self._construir()
        self._nuevo(False)

    # ------------------------------------------------------------------------
    # 8. CREACIÓN DE CONTROLES AUXILIARES
    # Métodos de apoyo para construir tarjetas, secciones, botones y entradas.
    # ------------------------------------------------------------------------
    def _card(self, parent, title):
        panel = ttk.LabelFrame(parent, text=title, padding=10)
        panel.pack(fill='x', pady=(0, 10))
        return panel

    def _seccion(self, parent, title, abierta=False):
        section = SeccionPlegable(parent, title, abierta)
        self.secciones.append(section)
        return section.body

    def _button(self, parent, text, command, mutable=False):
        def invoke():
            button.focus_set()
            command()
        button = ttk.Button(parent, text=text, command=invoke)
        button.pack(fill='x', pady=3)
        if mutable:
            self.controles_mutables.append(button)
        return button

    def _entry(self, parent, title, variable):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=3)
        ttk.Label(row, text=title).pack(side='left')
        field = ttk.Entry(row, textvariable=variable, width=12)
        field.pack(side='right')
        return field

    # ------------------------------------------------------------------------
    # 9. CONSTRUCCIÓN DE LA VENTANA
    # Organiza el encabezado y los paneles de configuración, grafo y resultados.
    # ------------------------------------------------------------------------
    def _construir(self):
        # Encabezado de la aplicación y distribución general de tres columnas.
        header = tk.Frame(self.root, bg=NAVY, padx=22, pady=13)
        header.pack(fill='x')
        tk.Label(header, text='OptiRoute', bg=NAVY, fg='white', font=('Segoe UI', 25, 'bold')).pack(side='left')
        tk.Label(header, text='  V2  /  Explora · Compara · Optimiza', bg=NAVY, fg='#79d9ef', font=('Segoe UI', 11)).pack(side='left', padx=16)
        body = ttk.Frame(self.root, padding=8)
        body.pack(fill='both', expand=True)
        body.rowconfigure(0, weight=1)
        for col, weight, minimum in [(0, 0, 255), (1, 1, 380), (2, 0, 300)]:
            body.columnconfigure(col, weight=weight, minsize=minimum)
        left = ScrollPanel(body, 245)
        left.grid(row=0, column=0, sticky='nsew')
        center = ttk.Frame(body, padding=(8, 0))
        center.grid(row=0, column=1, sticky='nsew')
        right = ScrollPanel(body, 290)
        right.grid(row=0, column=2, sticky='nsew')
        # Panel izquierdo: creación, unidades, aristas, algoritmo y ciudades.
        self.secciones = []
        p = self._seccion(left.body, '01 · Crear grafo', True)
        self._entry(p, 'Nodos (5–10)', self.n)
        ttk.Label(p, text='N se aplica al crear un nuevo grafo.', wraplength=185).pack(anchor='w')
        self._entry(p, 'Peso mínimo', self.minimo)
        self._entry(p, 'Peso máximo', self.maximo)
        self._button(p, 'Generar aleatorio', lambda: self._nuevo(True), True)
        self._button(p, 'Crear grafo manual', lambda: self._nuevo(False), True)
        p = self._seccion(left.body, '02 · Tipo de peso')
        cb = ttk.Combobox(p, textvariable=self.tipo, values=list(UNIDADES), state='readonly', width=20)
        cb.pack(fill='x', pady=3)
        cb.bind('<<ComboboxSelected>>', self._tipo_cambiado)
        self.combo_unidad = ttk.Combobox(p, textvariable=self.unidad, values=UNIDADES['Distancia'], width=20)
        self.combo_unidad.pack(fill='x', pady=3)
        self._button(p, 'Aplicar unidad', self._aplicar_unidad)
        self.unidad_aplicada = 'km'
        self.tipo_aplicado = 'Distancia'
        p = self._seccion(left.body, '03 · Editar aristas')
        self.origen = ttk.Combobox(p, state='readonly', width=20)
        self.destino = ttk.Combobox(p, state='readonly', width=20)
        ttk.Label(p, text='Origen / destino').pack(anchor='w')
        self.origen.pack(fill='x', pady=3)
        self.destino.pack(fill='x', pady=3)
        self._entry(p, 'Peso positivo', self.peso)
        self._button(p, 'Agregar / actualizar', self._agregar, True)
        self._button(p, 'Eliminar arista', self._eliminar, True)
        self._button(p, 'Borrar aristas', self._borrar, True)
        p = self._seccion(left.body, '04 · Algoritmo', True)
        self.iniciar = self._button(p, 'Iniciar búsqueda', self._iniciar, True)
        self.iniciar.configure(style='Accent.TButton')
        self.anterior = self._button(p, '← Paso anterior', lambda: self._paso(-1))
        self.siguiente = self._button(p, 'Paso siguiente →', lambda: self._paso(1))
        self.final = self._button(p, 'Ver resultado final', self._final)
        ttk.Checkbutton(p, text='Solo la ruta resaltada', variable=self.solo_ruta, command=self._dibujar).pack(anchor='w', pady=6)
        self.city_panel = self._seccion(left.body, '05 · Ciudades')
        self.ciudades_body = ttk.Frame(self.city_panel)
        self.ciudades_body.pack(fill='x')
        self._button(self.city_panel, 'Aplicar nombres', self._guardar_nombres)
        # Panel central: el grafo ocupa el espacio flexible de la ventana.
        center.rowconfigure(1, weight=1)
        center.columnconfigure(0, weight=1)
        self.titulo = ttk.Label(center, text='GRAFO PONDERADO', font=('Segoe UI', 12, 'bold'))
        self.titulo.grid(row=0, column=0, sticky='w', pady=8)
        self.canvas = tk.Canvas(center, bg='white', highlightthickness=0, width=400, height=300)
        self.canvas.grid(row=1, column=0, sticky='nsew')
        self.canvas.bind('<Configure>', lambda e: self._dibujar())
        self.matrix_title = ttk.Label(center, font=('Segoe UI', 11, 'bold'))
        self.matrix_title.grid(row=2, column=0, sticky='w', pady=(12, 5))
        # Bloque inferior de altura fija: matriz y solución en contenedores separados.
        self.lower_blocks = ttk.Frame(center, height=ALTURA_BLOQUE_INFERIOR)
        self.lower_blocks.grid(row=3, column=0, sticky='ew')
        self.lower_blocks.grid_propagate(False)
        self.lower_blocks.rowconfigure(0, weight=1)
        self.lower_blocks.columnconfigure(0, weight=3)
        self.lower_blocks.columnconfigure(1, weight=2)
        matrix_frame = ttk.Frame(self.lower_blocks)
        matrix_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        matrix_frame.rowconfigure(0, weight=1)
        matrix_frame.columnconfigure(0, weight=1)
        self.matrix_canvas = tk.Canvas(matrix_frame, bg='white', highlightthickness=0, height=200)
        self.matrix_canvas.grid(row=0, column=0, sticky='nsew')
        bar = ttk.Scrollbar(matrix_frame, orient='horizontal', command=self.matrix_canvas.xview)
        bar.grid(row=1, column=0, sticky='ew')
        self.matrix_canvas.configure(xscrollcommand=bar.set)
        vertical = ttk.Scrollbar(matrix_frame, orient='vertical', command=self.matrix_canvas.yview)
        vertical.grid(row=0, column=1, sticky='ns')
        self.matrix_canvas.configure(yscrollcommand=vertical.set)
        self.matrix_canvas.bind('<Configure>', lambda e: self._matriz())
        ttk.Label(center, text='0 = sin arista · Orden de filas y columnas indicado en la leyenda',
                  wraplength=370).grid(row=4, column=0, sticky='w', pady=5)
        # Panel derecho: estado, intento seleccionado y cinco mejores rutas.
        p = self._card(right.body, 'Ejecución')
        self.estado = self._label(p)
        self.estado.configure(font=('Segoe UI', 10, 'bold'))
        self.contador = tk.Text(p, height=3, width=22, wrap='word', bg=BG, fg=NAVY,
                               relief='flat', borderwidth=0, font=('Segoe UI', 10),
                               takefocus=False, cursor='arrow')
        self.contador.pack(fill='x', pady=4)
        self.contador.tag_configure('etiqueta', font=('Segoe UI', 10, 'bold'))
        self.contador.configure(state='disabled')
        p = self._card(right.body, 'Ruta evaluada / seleccionada')
        self.actual = DetailBlock(p)
        p = self._card(right.body, 'Top 5 · menor costo')
        self.top = ttk.Frame(p)
        self.top.pack(fill='x')
        self.todos = self._button(p, 'Ver todos los ciclos', self._todos)
        # La tarjeta óptima comparte el bloque inferior con la matriz y la leyenda.
        self.optimal_card = ttk.LabelFrame(self.lower_blocks, text='SOLUCIÓN ÓPTIMA', padding=8)
        self.optimal_card.grid(row=0, column=1, sticky='nsew')
        solution_scroll = ScrollPanel(self.optimal_card, 245)
        solution_scroll.pack(fill='both', expand=True)
        self.optima = DetailBlock(solution_scroll.body, VIOLET)

    # ------------------------------------------------------------------------
    # 10. FORMATO DE LA INFORMACIÓN
    # Crea etiquetas y transforma índices, rutas y costos en texto para el usuario.
    # ------------------------------------------------------------------------
    def _label(self, parent, color=NAVY):
        label = ttk.Label(parent, text='', wraplength=245, justify='left', foreground=color)
        label.pack(fill='x', pady=5)
        return label

    def _nombre(self, i):
        return f'{self.nombres[i]} ({chr(65+i)})' if self.nombres[i] else chr(65+i)

    def _ruta_texto(self, ruta):
        return ' → '.join(self._nombre(i) for i in ruta)

    def _ruta_letras(self, ruta):
        return ' → '.join(chr(65+i) for i in ruta)

    def _costo(self, valor):
        return f'{valor:g} {self.unidad_aplicada}'

    # ------------------------------------------------------------------------
    # 11. TIPO DE PESO Y UNIDADES
    # Valida y actualiza etiquetas; no convierte pesos ni cambia el objetivo del TSP.
    # ------------------------------------------------------------------------
    def _tipo_cambiado(self, event=None):
        values = UNIDADES[self.tipo.get()]
        self.combo_unidad.configure(values=values)
        self.unidad.set(values[0])
        self._aplicar_unidad()

    def _aplicar_unidad(self):
        unit = self.unidad.get().strip()
        if not unit or len(unit) > 16 or any(ord(c) < 32 for c in unit):
            messagebox.showerror('Unidad inválida', 'Use entre 1 y 16 caracteres visibles.')
            return
        self.unidad_aplicada = unit
        self.tipo_aplicado = self.tipo.get()
        self._cerrar_listas()
        self._refrescar()

    # ------------------------------------------------------------------------
    # 12. CREACIÓN DEL GRAFO Y NOMBRES DE CIUDADES
    # Valida N y el rango aleatorio, crea la matriz y actualiza los selectores.
    # ------------------------------------------------------------------------
    def _nuevo(self, aleatorio):
        if self.busy:
            return
        try:
            n = int(self.n.get())
            if not 5 <= n <= 10:
                raise ValueError('N debe ser un entero entre 5 y 10.')
            if aleatorio:
                minimo, maximo = int(self.minimo.get()), int(self.maximo.get())
                if not 0 < minimo <= maximo:
                    raise ValueError('El rango debe cumplir 0 < mínimo ≤ máximo (enteros).')
        except ValueError as exc:
            messagebox.showerror('Datos inválidos', str(exc))
            return
        self.matriz = logica.crear_matriz(n)
        if aleatorio:
            logica.llenar_matriz_aleatoria(self.matriz, minimo, maximo)
        for widget in self.ciudades_body.winfo_children():
            widget.destroy()
        self.city_vars = []
        for i in range(n):
            var = tk.StringVar(value=self.nombres[i])
            self.city_vars.append(var)
            self._entry(self.ciudades_body, chr(65+i), var)
        self._selectores()
        self._invalidar('Grafo aleatorio listo.' if aleatorio else 'Grafo manual: agregue sus aristas.')

    def _selectores(self):
        values = [f'{chr(65+i)} — {self.nombres[i] or "Sin nombre"}' for i in range(len(self.matriz))]
        for combo, default in [(self.origen, 0), (self.destino, 1)]:
            index = combo.current()
            combo.configure(values=values)
            combo.current(index if 0 <= index < len(values) else default)

    def _guardar_nombres(self):
        names = [v.get().strip() for v in self.city_vars]
        if any(len(s) > 24 or any(ord(c) < 32 for c in s) for s in names):
            messagebox.showerror('Nombre inválido', 'Máximo 24 caracteres visibles por ciudad; puede dejarlo vacío.')
            return
        present = [s.casefold() for s in names if s]
        if len(present) != len(set(present)):
            messagebox.showerror('Nombres repetidos', 'Utilice nombres distintos para evitar ambigüedad.')
            return
        self.nombres[:len(names)] = names
        self._cerrar_listas()
        self._selectores()
        self._refrescar()

    # ------------------------------------------------------------------------
    # 13. EDICIÓN MANUAL DE ARISTAS
    # Valida los vértices y pesos; delega en logica las modificaciones simétricas.
    # ------------------------------------------------------------------------
    def _extremos(self):
        a, b = self.origen.current(), self.destino.current()
        if a < 0 or b < 0 or a == b:
            raise ValueError('Seleccione dos vértices distintos.')
        return a, b

    def _agregar(self):
        if self.busy:
            return
        try:
            a, b = self._extremos()
            peso = float(self.peso.get())
            if not math.isfinite(peso) or peso <= 0:
                raise ValueError('El peso debe ser positivo y finito.')
        except ValueError as exc:
            messagebox.showerror('Arista inválida', str(exc))
            return
        logica.agregar_arista(self.matriz, a, b, peso)
        self._invalidar('Arista actualizada. Ejecute nuevamente la búsqueda.')

    def _eliminar(self):
        if self.busy:
            return
        try:
            a, b = self._extremos()
        except ValueError as exc:
            messagebox.showerror('Arista inválida', str(exc))
            return
        logica.agregar_arista(self.matriz, a, b, 0)
        self._invalidar('Arista eliminada.')

    def _borrar(self):
        if not self.busy:
            logica.borrar_aristas(self.matriz)
            self._invalidar('Se borraron todas las aristas.')

    # ------------------------------------------------------------------------
    # 14. REINICIO DEL ESTADO
    # Cierra listas anteriores e invalida resultados cuando cambia el grafo.
    # ------------------------------------------------------------------------
    def _cerrar_listas(self):
        for window in self.ventanas_ciclos:
            if window.winfo_exists():
                window.destroy()
        self.ventanas_ciclos.clear()

    def _invalidar(self, mensaje):
        self.revision += 1
        self._cerrar_listas()
        self.resultado = None
        self.indice_paso = -1
        self.ruta = None
        self.vista = 'inicio'
        self.estado.configure(text=mensaje, foreground=NAVY)
        self.actual.configure(text='Presione Iniciar para evaluar las rutas.', foreground=NAVY)
        self._refrescar()

    # ------------------------------------------------------------------------
    # 15. EJECUCIÓN Y COMUNICACIÓN CON LA LÓGICA
    # Ejecuta la búsqueda en un hilo y recibe sus resultados mediante una cola.
    # ------------------------------------------------------------------------
    def _iniciar(self):
        if self.busy:
            return
        self._invalidar('Calculando… La búsqueda recursiva puede tardar con 10 nodos.')
        self.busy = True
        self._botones()
        matriz = [row[:] for row in self.matriz]
        revision = self.revision

        # El cálculo llama a logica; este hilo no debe modificar widgets de Tkinter.
        def work():
            # El hilo usa exclusivamente datos Python. Tk se actualiza desde _recibir.
            try:
                if logica.existe_ciclo_hamiltoniano(matriz):
                    data = ('resultado', logica.resolver_tsp(matriz))
                else:
                    data = ('faltantes', logica.sugerir_aristas_faltantes(matriz))
                self.cola.put((revision, data))
            except Exception as exc:
                self.cola.put((revision, ('error', str(exc))))

        threading.Thread(target=work, daemon=True).start()
        self.root.after(60, self._recibir)

    # Consulta la cola con after para actualizar la interfaz sin bloquear eventos.
    def _recibir(self):
        try:
            revision, (kind, data) = self.cola.get_nowait()
        except queue.Empty:
            self.root.after(60, self._recibir)
            return
        self.busy = False
        if revision != self.revision:
            self._botones()
            return
        if kind == 'resultado':
            self.resultado = data
            self.estado.configure(text='Búsqueda completa. Recorra los intentos o consulte el resultado.', foreground=GREEN)
        elif kind == 'faltantes':
            _, faltantes = data
            self.estado.configure(text='No existe un ciclo hamiltoniano.', foreground=RED)
            self.actual.configure(text='Aristas sugeridas para completar al menos un ciclo:\n\n' + '\n'.join(f'{self._nombre(a)} — {self._nombre(b)}' for a, b in faltantes), foreground=RED)
        else:
            self.estado.configure(text='No se pudo completar la búsqueda.', foreground=RED)
            messagebox.showerror('Error de ejecución', data)
        self._refrescar()

    # ------------------------------------------------------------------------
    # 16. CONTROLES Y NAVEGACIÓN DE RESULTADOS
    # Habilita acciones y permite recorrer los intentos completos ya calculados.
    # ------------------------------------------------------------------------
    def _botones(self):
        for button in self.controles_mutables:
            button.configure(state='disabled' if self.busy else 'normal')
        ready = self.resultado is not None and not self.busy
        self.final.configure(state='normal' if ready else 'disabled')
        self.todos.configure(state='normal' if ready else 'disabled')
        self.anterior.configure(state='normal' if ready and self.indice_paso >= 0 else 'disabled')
        self.siguiente.configure(state='normal' if ready and self.indice_paso < len(self.resultado['pasos'])-1 else 'disabled')

    # delta indica avance o retroceso sobre la lista de intentos registrados.
    def _paso(self, delta):
        if not self.resultado:
            return
        self.indice_paso = max(-1, min(len(self.resultado['pasos'])-1, self.indice_paso+delta))
        self.vista = 'paso'
        self._mostrar_actual()
        self._botones()

    def _mostrar_actual(self):
        if not self.resultado:
            return
        if self.vista == 'paso' and self.indice_paso >= 0:
            paso = self.resultado['pasos'][self.indice_paso]
            self.ruta = paso['ruta']
            self.color = GREEN if paso['valida'] else RED
            detail = f"Estado: Ciclo válido\n\nPeso total: {self._costo(paso['costo'])}" if paso['valida'] else 'Estado: Ciclo inválido\n\nMotivo: Falta la arista de regreso (trazo discontinuo).'
            self.actual.configure(text=f"Intento: {self.indice_paso+1} de {len(self.resultado['pasos'])}\n\n{self._ruta_letras(self.ruta)}\n\n{detail}", foreground=self.color)
        elif self.vista in ('final', 'seleccion') and self.ruta:
            self.actual.configure(text=('Selección: Ruta óptima' if self.vista == 'final' else 'Selección: Ciclo válido') + '\n\n' + self._ruta_letras(self.ruta) + '\n\nPeso total: ' + self._costo(logica.calcular_costo(self.ruta, self.matriz)), foreground=self.color)
        else:
            self.ruta = None
            self.actual.configure(text='Aún no se ha mostrado ningún intento. Presione Paso siguiente.', foreground=NAVY)
        self._dibujar()

    # Selecciona la mejor ruta calculada y la resalta con el color de óptimo.
    def _final(self):
        if self.resultado and self.resultado['mejor']:
            self.vista = 'final'
            self.ruta = self.resultado['mejor']['ruta']
            self.color = VIOLET
            self._mostrar_actual()

    # Permite inspeccionar una solución del Top 5 o de la lista completa.
    def _seleccionar(self, solucion):
        self.vista = 'seleccion'
        self.ruta = solucion['ruta']
        self.color = BLUE
        self._mostrar_actual()

    # ------------------------------------------------------------------------
    # 17. ACTUALIZACIÓN DEL RESUMEN Y LOS CONTADORES
    # Presenta Top 5, solución óptima y cantidades sin repetir la búsqueda.
    # ------------------------------------------------------------------------
    def _refrescar(self):
        if self.matriz is None:
            return
        self._matriz()
        for child in self.top.winfo_children():
            child.destroy()
        if self.resultado:
            # API original: total_evaluadas = len(soluciones), NO len(pasos).
            # Los pasos incluyen ambos sentidos y cierres fallidos, pero no ramas truncadas.
            self._contadores(self.resultado['total_evaluadas'], len(self.resultado['pasos']))
            for i, sol in enumerate(self.resultado['ordenadas'][:5], 1):
                button = tk.Button(self.top, text=f'{i}. {" → ".join(chr(65+nodo) for nodo in sol["ruta"])}\n{self._costo(sol["costo"])}', command=lambda s=sol: self._seleccionar(s), wraplength=220, justify='left', anchor='w', bg='white', fg=NAVY, relief='flat', padx=7, pady=6, cursor='hand2')
                button.pack(fill='x', pady=3)
            best = self.resultado['mejor']
            self.optima.configure(text=(self._ruta_texto(best['ruta']) + '\n\nMínimo: ' + self._costo(best['costo'])) if best else 'Sin solución.')
            self._mostrar_actual()
        else:
            self._contadores()
            self.optima.configure(text='Pendiente de búsqueda.')
        self._botones()
        self._dibujar()

    def _contadores(self, ciclos=None, intentos=None):
        self.contador.configure(state='normal')
        self.contador.delete('1.0', 'end')
        for label, value in [('Ciclos válidos únicos: ', ciclos), ('Intentos completos: ', intentos)]:
            self.contador.insert('end', label, 'etiqueta')
            self.contador.insert('end', ('—' if value is None else str(value)) + '\n')
        self.contador.configure(state='disabled')

    # ------------------------------------------------------------------------
    # 18. DIBUJO DE LA MATRIZ Y LA LEYENDA
    # Dibuja celdas, encabezados y ciudades; conserva el dibujo si los datos no cambian.
    # ------------------------------------------------------------------------
    def _matriz(self):
        if self.matriz is None:
            return
        c = self.matrix_canvas
        # La búsqueda y los pasos no cambian estos datos. Conservar los objetos
        # del canvas y su desplazamiento cuando solo se actualizan resultados.
        key = (tuple(tuple(row) for row in self.matriz), tuple(self.nombres),
               self.tipo_aplicado, self.unidad_aplicada, c.winfo_width())
        if key == getattr(self, '_matrix_render_key', None):
            return
        self._matrix_render_key = key
        c.delete('all')
        n = len(self.matriz)
        numeric_font = tkfont.Font(family='Consolas', size=10)
        # Celdas cuadradas sin estirar: valores exactos, incluso con pesos largos.
        cell = max(23, max(numeric_font.measure(f'{v:g}') for row in self.matriz for v in row)+12)
        size = cell*n
        x0, y0 = 94, 44
        for i in range(n):
            c.create_text(x0+i*cell+cell/2, y0-20, text=chr(65+i), fill=BLUE, font=('Segoe UI',10,'bold'), tags=('columna',))
            c.create_text(x0-24, y0+i*cell+cell/2, text=chr(65+i), fill=BLUE, font=('Segoe UI',10,'bold'), tags=('fila',))
        c.create_text(12, y0+size/2, text='M =', anchor='w', fill=BLUE,
                      font=('Cambria', 19, 'italic'))
        for i, row in enumerate(self.matriz):
            for j, value in enumerate(row):
                x, y = x0+j*cell, y0+i*cell
                c.create_rectangle(x,y,x+cell,y+cell, fill='#edf3fa' if i == j else 'white', outline='')
                c.create_text(x+cell/2,y+cell/2,text=f'{value:g}',
                              fill='#94a3b8' if value == 0 else NAVY,
                              font=('Consolas', 10), tags=('valor',))
        for x, direction in [(x0-7,1),(x0+size+7,-1)]:
            c.create_line(x+direction*9,y0-5,x,y0-5,x,y0+size+5,
                          x+direction*9,y0+size+5,fill=BLUE,width=2.5)
        c.create_text(x0+size+18,y0+size+13,text=f'{n} × {n}',anchor='ne',
                      fill=BLUE,font=('Segoe UI',9,'bold'))
        lx = x0+size+43
        c.create_line(lx-16,18,lx-16,max(180,size+30),fill='#e2e8f0')
        c.create_text(lx,18,text='CIUDADES',anchor='nw',fill=BLUE,font=('Segoe UI',10,'bold'))
        c.create_text(lx,40,text='Orden de filas y columnas',anchor='nw',fill='#64748b',font=('Segoe UI',9))
        for i in range(n):
            y = 68+i*22
            c.create_text(lx,y,text=chr(65+i),anchor='w',fill=BLUE,font=('Segoe UI',10,'bold'))
            c.create_text(lx+25,y,text=self.nombres[i] or 'Sin nombre',anchor='w',fill=NAVY,font=('Segoe UI',10))
        bounds = c.bbox('all')
        height = max(size+78, 68+n*22)
        available = c.winfo_width()
        content_width = bounds[2]+18
        if available > content_width:
            c.move('all', (available-content_width)/2, 0)
        bounds = c.bbox('all')
        # Solo crece el contenido desplazable; el bloque visible conserva su altura.
        c.configure(scrollregion=(0,0,bounds[2]+18,height))
        self.matrix_title.configure(text=f'Matriz de costos · {self.tipo_aplicado} ({self.unidad_aplicada})')

    # ------------------------------------------------------------------------
    # 19. VENTANA DE TODOS LOS CICLOS
    # Muestra las soluciones ordenadas en páginas de diez y permite seleccionarlas.
    # ------------------------------------------------------------------------
    def _todos(self):
        if not self.resultado:
            return
        window = tk.Toplevel(self.root)
        window.title('Todos los ciclos · OptiRoute V2')
        window.geometry('900x540')
        self.ventanas_ciclos.append(window)
        soluciones = self.resultado['ordenadas']
        page = [0]
        page_size = 10
        controls = ttk.Frame(window, padding=8)
        controls.pack(fill='x')
        label = ttk.Label(controls)
        label.pack(side='left')
        frame = ttk.Frame(window, padding=8)
        frame.pack(fill='both', expand=True)
        tree = ttk.Treeview(frame, columns=('numero', 'ruta', 'costo'), show='headings')
        for col, width in [('numero', 65), ('ruta', 620), ('costo', 150)]:
            tree.heading(col, text={'numero': '#', 'ruta': 'Ciclo hamiltoniano', 'costo': 'Peso total'}[col])
            tree.column(col, width=width, minwidth=width, stretch=col == 'ruta')
        tree.grid(row=0, column=0, sticky='nsew')
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        for orient, row, col, sticky in [('vertical', 0, 1, 'ns'), ('horizontal', 1, 0, 'ew')]:
            bar = ttk.Scrollbar(frame, orient=orient, command=tree.yview if orient == 'vertical' else tree.xview)
            bar.grid(row=row, column=col, sticky=sticky)
            tree.configure(**{('yscrollcommand' if orient == 'vertical' else 'xscrollcommand'): bar.set})

        # Calcula la página visible y desactiva las flechas en los extremos.
        def show(delta=0):
            page[0] = max(0, min(max(0, (len(soluciones)-1)//page_size), page[0]+delta))
            tree.delete(*tree.get_children())
            start = page[0]*page_size
            for index in range(start, min(start+page_size, len(soluciones))):
                s = soluciones[index]
                tree.insert('', 'end', iid=str(index), values=(index+1, self._ruta_texto(s['ruta']), self._costo(s['costo'])))
            pages = max(1, (len(soluciones)+page_size-1)//page_size)
            label.configure(text=f'{len(soluciones)} ciclos · Página {page[0]+1} de {pages} · Mostrando {start+1 if soluciones else 0}–{min(start+page_size,len(soluciones))}')
            previous.configure(state='disabled' if page[0] == 0 else 'normal')
            following.configure(state='disabled' if page[0]+1 >= pages else 'normal')
            tree.yview_moveto(0)

        following = ttk.Button(controls, text='Página siguiente →', command=lambda: show(1))
        following.pack(side='right')
        previous = ttk.Button(controls, text='← Página anterior', command=lambda: show(-1))
        previous.pack(side='right')
        window.cycle_table = tree
        window.next_page = following
        window.previous_page = previous
        window.page_label = label
        ttk.Label(window, text='Seleccione un ciclo para resaltarlo en el grafo. 10 resultados por página; las flechas se habilitan cuando hay otra página.').pack(pady=8)
        tree.bind('<<TreeviewSelect>>', lambda e: self._seleccionar(soluciones[int(tree.selection()[0])]) if tree.selection() else None)
        show()

    # ------------------------------------------------------------------------
    # 20. REPRESENTACIÓN GRÁFICA DEL GRAFO
    # Ubica nodos, dibuja aristas y pesos, y resalta la ruta seleccionada.
    # ------------------------------------------------------------------------
    def _dibujar(self):
        if self.matriz is None:
            return
        canvas = self.canvas
        canvas.delete('all')
        n = len(self.matriz)
        w, h = max(canvas.winfo_width(), 200), max(canvas.winfo_height(), 180)
        # Filas escalonadas deterministas: evita las diagonales concurrentes del círculo.
        layouts = {
            5: [(0.08,.12),(.65,.06),(.96,.48),(.65,.94),(.10,.85)],
            6: [(0,.1),(.5,0),(1,.18),(.1,.86),(.6,1),(.94,.70)],
            7: [(0,.08),(.48,0),(.97,.15),(.20,.47),(.87,.58),(.05,.94),(.63,1)],
            8: [(0,.06),(.48,0),(1,.12),(.15,.43),(.70,.48),(0,.91),(.48,1),(.98,.88)],
            9: [(0,.07),(.45,0),(1,.12),(.10,.47),(.55,.40),(.97,.56),(0,.93),(.49,1),(.90,.89)],
            10: [(0,.08),(.40,0),(.92,.09),(.15,.36),(.64,.31),(1,.48),(0,.70),(.45,.65),(.25,1),(.94,.96)]}
        positions = {i: (42+x*(w-84), 38+y*(h-90)) for i, (x,y) in enumerate(layouts[n])}
        self.posiciones = positions
        # Compara aristas sin orientación para resaltar el ciclo en un grafo no dirigido.
        selected = {tuple(sorted((a,b))) for a,b in zip(self.ruta or [], (self.ruta or [])[1:])}
        edges = []
        for a in range(n):
            for b in range(a+1, n):
                highlight = (a,b) in selected
                if self.ruta and self.solo_ruta.get() and not highlight:
                    continue
                if not self.matriz[a][b] and not highlight:
                    continue
                color = self.color if highlight else '#abbacb'
                x1,y1 = positions[a]
                x2,y2 = positions[b]
                canvas.create_line(x1,y1,x2,y2, fill=color, width=3 if highlight else 1.2, dash=(5,4) if not self.matriz[a][b] else ())
                if self.matriz[a][b]:
                    edges.append((a,b,color,highlight))
        # Colocar etiquetas sobre las aristas; probar varios puntos evitando cajas ocupadas.
        occupied = [(x-25,y-25,x+25,y+40) for x,y in positions.values()]
        for a,b,color,highlight in sorted(edges, key=lambda edge: not edge[3]):
            x1,y1 = positions[a]
            x2,y2 = positions[b]
            text = f'{self.matriz[a][b]:g}'
            text_id = canvas.create_text(0,0,text=text,font=('Segoe UI',9,'bold' if highlight else 'normal'),fill=color if highlight else NAVY)
            candidates = []
            for t in (.5,.33,.67,.22,.78,.42,.58):
                x,y = x1+(x2-x1)*t,y1+(y2-y1)*t
                canvas.coords(text_id,x,y)
                box = canvas.bbox(text_id)
                box = (box[0]-3,box[1]-2,box[2]+3,box[3]+2)
                overlap = sum(max(0,min(box[2],o[2])-max(box[0],o[0]))*max(0,min(box[3],o[3])-max(box[1],o[1])) for o in occupied)
                candidates.append((overlap,x,y,box))
            _,x,y,box = min(candidates,key=lambda item:item[0])
            canvas.coords(text_id,x,y)
            rect = canvas.create_rectangle(*box,fill='white',outline='#e2e8f0')
            canvas.tag_raise(text_id,rect)
            occupied.append(box)
        # Dibuja los nodos al final para mantener sus letras visibles sobre las aristas.
        for i,(x,y) in positions.items():
            canvas.create_oval(x-18,y-18,x+18,y+18,fill='#e5f4ff',outline=BLUE,width=2)
            canvas.create_text(x,y,text=chr(65+i),font=('Segoe UI',11,'bold'),fill=NAVY)
            if self.nombres[i]:
                label = canvas.create_text(x,y+29,text=self.nombres[i],width=95,font=('Segoe UI',9),fill=NAVY)
                rect = canvas.create_rectangle(*canvas.bbox(label),fill='white',outline='')
                canvas.tag_raise(label,rect)
        self.titulo.configure(text=f'GRAFO · {n} vértices · pesos en {self.unidad_aplicada}')


# ------------------------------------------------------------------------
# 21. PUNTO DE ENTRADA
# Configura la nitidez, crea la aplicación e inicia el ciclo de eventos de Tkinter.
# ------------------------------------------------------------------------
def main():
    configurar_nitidez()
    root = tk.Tk()
    OptiRouteApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
