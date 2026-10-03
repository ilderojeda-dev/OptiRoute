import math
import tkinter as tk
from tkinter import ttk, messagebox

import logica


COLOR_NODO = "#dbe9ff"
COLOR_BORDE_NODO = "#2b5fb8"
COLOR_ARISTA = "#9aa0a6"
COLOR_RUTA_RESALTADA = "#2e8b57"   
COLOR_RUTA_INVALIDA = "#b0392f"    
COLOR_RUTA_OPTIMA = "#d40ab2"     

CENTRO_X, CENTRO_Y, RADIO_GRAFO = 280, 260, 210


class OptiRouteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OptiRoute - Problema del Agente Viajero")

        self.n = tk.IntVar(value=5) 
        self.matriz = None
        self.resultado = None
        self.indice_paso = -1
        self.posiciones = {}
        self.solo_ruta = tk.BooleanVar(value=True)

        self._construir_panel_izquierdo()
        self._construir_panel_central()

        self._mostrar_texto("Genere un grafo aleatorio o manual para comenzar.")

# PANEL IZQUIERDO: crear grafo, aristas manuales y algoritmo
    def _construir_panel_izquierdo(self):
        contenedor = ttk.Frame(self.root)
        contenedor.grid(row=0, column=0, sticky="ns", padx=8, pady=8)

        # --- 1. Crear grafo ---
        panel1 = ttk.LabelFrame(contenedor, text="1. Crear grafo")
        panel1.pack(fill="x", pady=4)

        fila_n = ttk.Frame(panel1)
        fila_n.pack(anchor="w", padx=6, pady=4)
        ttk.Label(fila_n, text="Nodos (5-10):").pack(side="left")
        ttk.Spinbox(fila_n, from_=5, to=10, textvariable=self.n, width=5).pack(side="left", padx=4)

        ttk.Button(panel1, text="Grafo aleatorio", command=self._generar_aleatorio).pack(fill="x", padx=6, pady=2)
        ttk.Button(panel1, text="Grafo manual", command=self._iniciar_manual).pack(fill="x", padx=6, pady=(2, 6))

        # --- 2. Aristas (manual) ---
        panel2 = ttk.LabelFrame(contenedor, text="2. Aristas (manual)")
        panel2.pack(fill="x", pady=4)

        self.entrada_origen = self._fila_entrada(panel2, "Origen:")
        self.entrada_destino = self._fila_entrada(panel2, "Destino:")
        self.entrada_peso = self._fila_entrada(panel2, "Peso:")

        ttk.Button(panel2, text="Agregar arista", command=self._agregar_arista).pack(fill="x", padx=6, pady=2)
        ttk.Button(panel2, text="Borrar todas las aristas", command=self._borrar_aristas).pack(
            fill="x", padx=6, pady=(2, 6))

        # --- 3. Algoritmo ---
        panel3 = ttk.LabelFrame(contenedor, text="3. Algoritmo")
        panel3.pack(fill="x", pady=4)

        ttk.Button(panel3, text="Iniciar", command=self._iniciar_algoritmo).pack(fill="x", padx=6, pady=2)
        ttk.Button(panel3, text="Siguiente paso >>", command=self._siguiente_paso).pack(fill="x", padx=6, pady=2)
        ttk.Button(panel3, text="<< Paso anterior", command=self._paso_anterior).pack(fill="x", padx=6, pady=2)
        ttk.Button(panel3, text="Ver resultado final", command=self._ver_resultado_final).pack(
            fill="x", padx=6, pady=(2, 6))

        ttk.Checkbutton(contenedor, text="Mostrar solo la ruta resaltada",
                         variable=self.solo_ruta, command=self._redibujar_actual).pack(anchor="w", pady=(8, 4))

        ttk.Button(contenedor, text="Salir", command=self.root.destroy).pack(fill="x", pady=(16, 4))

    def _fila_entrada(self, parent, texto):
        fila = ttk.Frame(parent)
        fila.pack(anchor="w", padx=6, pady=2, fill="x")
        ttk.Label(fila, text=texto, width=8).pack(side="left")
        entrada = ttk.Entry(fila, width=8)
        entrada.pack(side="left")
        return entrada

# PANEL CENTRAL: titulo, grafo e informacion
    def _construir_panel_central(self):
        panel = ttk.Frame(self.root)
        panel.grid(row=0, column=1, sticky="nsew", padx=8, pady=8)

        self.label_titulo = ttk.Label(panel, text="Genere un grafo para comenzar",
                                       font=("Arial", 12, "bold"))
        self.label_titulo.pack(pady=(0, 6))

        self.canvas = tk.Canvas(panel, width=2 * CENTRO_X, height=2 * CENTRO_Y - 30, bg="white",
                                 highlightthickness=1, highlightbackground="#ccc")
        self.canvas.pack()

        ttk.Label(panel, text="Información:").pack(anchor="w", pady=(10, 0))
        self.texto_info = tk.Text(panel, height=10, width=68, state="disabled", wrap="word")
        self.texto_info.pack(fill="x")

    def _mostrar_texto(self, contenido):
        self.texto_info.config(state="normal")
        self.texto_info.delete("1.0", "end")
        self.texto_info.insert("1.0", contenido)
        self.texto_info.config(state="disabled")

    def _mostrar_matriz_en_texto(self):
        n = len(self.matriz)
        lineas = ["Matriz de costos (fila = origen, columna = destino):", ""]
        encabezado = "      " + "".join(f"{j + 1:>5}" for j in range(n))
        lineas.append(encabezado)
        for i, fila in enumerate(self.matriz):
            lineas.append(f"{i + 1:>5} " + "".join(f"{v:>5g}" for v in fila))
        self._mostrar_texto("\n".join(lineas))
        
# CREACION DEL GRAFO
    def _leer_n_valido(self):
        try:
            n = int(self.n.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("Valor inválido", "Ingrese un número entero para N.")
            return None
        if not (5 <= n <= 10):
            messagebox.showerror("Valor inválido", "N debe estar entre 5 y 10.")
            return None
        return n

    def _reiniciar_estado(self):
        self.resultado = None
        self.indice_paso = -1

    def _generar_aleatorio(self):
        n = self._leer_n_valido()
        if n is None:
            return
        self.matriz = logica.crear_matriz(n)
        self.matriz = logica.llenar_matriz_aleatoria(self.matriz)
        self._reiniciar_estado()
        self.label_titulo.config(text="Grafo aleatorio generado. Presione 'Iniciar' para resolver.")
        self._mostrar_matriz_en_texto()
        self._dibujar_grafo()

    def _iniciar_manual(self):
        n = self._leer_n_valido()
        if n is None:
            return
        self.matriz = logica.crear_matriz(n)
        self._reiniciar_estado()
        self.label_titulo.config(text="Agregue las aristas en el panel izquierdo y presione 'Iniciar'.")
        self._mostrar_matriz_en_texto()
        self._dibujar_grafo()

# ARISTAS MANUALES
    def _agregar_arista(self):
        if self.matriz is None:
            messagebox.showinfo("Falta el grafo", "Primero presione 'Grafo manual' para fijar N.")
            return

        n = len(self.matriz)
        try:
            origen = int(self.entrada_origen.get()) - 1
            destino = int(self.entrada_destino.get()) - 1
            peso = float(self.entrada_peso.get())
        except ValueError:
            messagebox.showerror("Datos inválidos", "Origen, destino y peso deben ser numéricos.")
            return

        if not (0 <= origen < n) or not (0 <= destino < n) or origen == destino:
            messagebox.showerror("Datos inválidos", f"Origen y destino deben estar entre 1 y {n}, y ser distintos.")
            return
        if peso <= 0:
            messagebox.showerror("Datos inválidos", "El peso debe ser mayor que 0.")
            return

        logica.agregar_arista(self.matriz, origen, destino, peso)
        self._reiniciar_estado()
        self._mostrar_matriz_en_texto()
        self._dibujar_grafo()

    def _borrar_aristas(self):
        if self.matriz is None:
            return
        logica.borrar_aristas(self.matriz)
        self._reiniciar_estado()
        self._mostrar_matriz_en_texto()
        self._dibujar_grafo()

# ALGORITMO Y NAVEGACION PASO A PASO
    def _iniciar_algoritmo(self):
        if self.matriz is None:
            messagebox.showinfo("Falta el grafo", "Primero genere un grafo aleatorio o manual.")
            return

        if not logica.existe_ciclo_hamiltoniano(self.matriz):
            _, faltantes = logica.sugerir_aristas_faltantes(self.matriz)
            texto_faltantes = "\n".join(f"Nodo {a + 1} - Nodo {b + 1}" for a, b in faltantes)
            self._mostrar_texto(
                "El grafo actual NO permite formar ningún ciclo hamiltoniano.\n\n"
                "Aristas sugeridas para completarlo:\n" + texto_faltantes
            )
            self.label_titulo.config(text="Grafo incompleto: revise el panel de información.")
            return

        self.resultado = logica.resolver_tsp(self.matriz)
        self.indice_paso = -1

        self.label_titulo.config(
            text=f"Listo: {len(self.resultado['pasos'])} intentos por recorrer. Presione 'Siguiente paso'."
        )
        self._mostrar_texto(
            f"Se encontraron {self.resultado['total_evaluadas']} ciclos hamiltonianos válidos\n"
            f"entre {len(self.resultado['pasos'])} intentos completos evaluados.\n\n"
            "Presione 'Siguiente paso' para recorrerlos uno por uno,\n"
            "o 'Ver resultado final' para ir directo a la solución."
        )
        self._dibujar_grafo()

    def _siguiente_paso(self):
        if self.resultado is None:
            messagebox.showinfo("Sin resultados", "Primero presione 'Iniciar'.")
            return

        pasos = self.resultado["pasos"]
        if self.indice_paso >= len(pasos) - 1:
            messagebox.showinfo("Fin del recorrido", "Ya se mostraron todos los intentos.")
            return

        self.indice_paso += 1
        self._mostrar_paso_actual()

    def _paso_anterior(self):
        if self.resultado is None:
            return

        if self.indice_paso <= 0:
            self.indice_paso = -1
            self.label_titulo.config(text="Presione 'Siguiente paso' para comenzar.")
            self._mostrar_texto("Aún no se ha mostrado ningún intento.")
            self._dibujar_grafo()
            return

        self.indice_paso -= 1
        self._mostrar_paso_actual()

    def _mostrar_paso_actual(self):
        paso = self.resultado["pasos"][self.indice_paso]
        total = len(self.resultado["pasos"])
        ruta_texto = " -> ".join(str(nodo + 1) for nodo in paso["ruta"])

        if paso["valida"]:
            info = (f"Paso {self.indice_paso + 1} de {total}\n\n"
                    f"Ruta: {ruta_texto}\nCosto: {paso['costo']:g}\n\n"
                    "(Ciclo hamiltoniano VÁLIDO)")
            color = COLOR_RUTA_RESALTADA
        else:
            info = (f"Paso {self.indice_paso + 1} de {total}\n\n"
                    f"Ruta intentada: {ruta_texto}\n\n"
                    "(NO es válido: falta la conexión de regreso al nodo inicial)")
            color = COLOR_RUTA_INVALIDA

        self._mostrar_texto(info)
        self.label_titulo.config(text=f"Explorando intento {self.indice_paso + 1} de {total}")
        self._dibujar_grafo(ruta_resaltada=paso["ruta"], color_resaltado=color)

    def _ver_resultado_final(self):
        if self.resultado is None:
            messagebox.showinfo("Sin resultados", "Primero presione 'Iniciar'.")
            return

        mejor = self.resultado["mejor"]
        if mejor is None:
            self._mostrar_texto("No se encontró ningún ciclo hamiltoniano válido.")
            return

        top5 = self.resultado["ordenadas"][:5]
        lineas = ["TOP 5 RUTAS MÁS ÓPTIMAS", ""]
        for i, sol in enumerate(top5, start=1):
            ruta_texto = " -> ".join(str(nodo + 1) for nodo in sol["ruta"])
            lineas.append(f"{i}. {ruta_texto}   (costo {sol['costo']:g})")

        lineas.append("")
        lineas.append("RUTA ÓPTIMA")
        lineas.append(" -> ".join(str(nodo + 1) for nodo in mejor["ruta"]))
        lineas.append(f"Costo mínimo: {mejor['costo']:g}")

        self._mostrar_texto("\n".join(lineas))
        self.label_titulo.config(text="Resultado final")
        self._dibujar_grafo(ruta_resaltada=mejor["ruta"], color_resaltado=COLOR_RUTA_OPTIMA)

    def _redibujar_actual(self):
        if self.resultado and 0 <= self.indice_paso < len(self.resultado["pasos"]):
            self._mostrar_paso_actual()
        else:
            self._dibujar_grafo()


 # DIBUJO DEL GRAFO
    def _calcular_posiciones(self, n):
        posiciones = {}
        for i in range(n):
            angulo = 2 * math.pi * i / n - math.pi / 2
            x = CENTRO_X + RADIO_GRAFO * math.cos(angulo)
            y = CENTRO_Y + RADIO_GRAFO * math.sin(angulo)
            posiciones[i] = (x, y)
        return posiciones

    def _punto_control(self, x1, y1, x2, y2):
       
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2

        dx, dy = x2 - x1, y2 - y1
        largo = math.hypot(dx, dy)
        if largo == 0:
            return mx, my

        # Vector perpendicular a la arista, normalizado (largo 1).
        px, py = -dy / largo, dx / largo

        desplazamiento = 18
        opcion_a = (mx + px * desplazamiento, my + py * desplazamiento)
        opcion_b = (mx - px * desplazamiento, my - py * desplazamiento)

        # Se elige el lado que queda MAS LEJOS del centro, para que la
        # curva se arquee hacia afuera y no hacia el medio del grafo.
        dist_a = math.hypot(opcion_a[0] - CENTRO_X, opcion_a[1] - CENTRO_Y)
        dist_b = math.hypot(opcion_b[0] - CENTRO_X, opcion_b[1] - CENTRO_Y)

        return opcion_a if dist_a > dist_b else opcion_b

    def _dibujar_arista(self, i, j, color, grosor, dash=None, mostrar_peso=True):
        x1, y1 = self.posiciones[i]
        x2, y2 = self.posiciones[j]
        cx, cy = self._punto_control(x1, y1, x2, y2)

        self.canvas.create_line(x1, y1, cx, cy, x2, y2, fill=color, width=grosor,
                                 smooth=True, dash=dash)

        if mostrar_peso:
            self.canvas.create_text(cx, cy, text=f"{self.matriz[i][j]:g}", fill="#555", font=("Arial", 8))

    def _dibujar_grafo(self, ruta_resaltada=None, color_resaltado=COLOR_RUTA_RESALTADA):
        if self.matriz is None:
            self.canvas.delete("all")
            return

        n = len(self.matriz)
        self.posiciones = self._calcular_posiciones(n)
        self.canvas.delete("all")

        # Si hay una ruta resaltada y el casillero esta activado, se
        # oculta el resto de aristas para que no generen "caos" visual.
        ocultar_resto = ruta_resaltada is not None and self.solo_ruta.get()

        if not ocultar_resto:
            for i in range(n):
                for j in range(i + 1, n):
                    if self.matriz[i][j] != 0:
                        self._dibujar_arista(i, j, COLOR_ARISTA, 1)

        if ruta_resaltada:
            es_invalida = color_resaltado == COLOR_RUTA_INVALIDA
            for k in range(len(ruta_resaltada) - 1):
                a, b = ruta_resaltada[k], ruta_resaltada[k + 1]
                if self.matriz[a][b] != 0:
                    self._dibujar_arista(a, b, color_resaltado, 3)
                elif es_invalida:
                    # La arista de cierre no existe: se dibuja punteada
                    # para mostrar donde "fallo" el intento.
                    x1, y1 = self.posiciones[a]
                    x2, y2 = self.posiciones[b]
                    self.canvas.create_line(x1, y1, x2, y2, fill=color_resaltado, width=2, dash=(4, 3))

        radio_nodo = 20
        for i in range(n):
            x, y = self.posiciones[i]
            self.canvas.create_oval(x - radio_nodo, y - radio_nodo, x + radio_nodo, y + radio_nodo,
                                     fill=COLOR_NODO, outline=COLOR_BORDE_NODO, width=2)
            self.canvas.create_text(x, y, text=str(i + 1), font=("Arial", 11, "bold"))


def main():
    root = tk.Tk()
    OptiRouteApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
