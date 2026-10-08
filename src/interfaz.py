import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import tkinter.font as tkfont

COLORES = {
    "fondo": "#1e1f29",
    "panel": "#262837",
    "editor": "#1a1b26",
    "texto": "#e6e6f0",
    "texto_tenue": "#7a7f9a",
    "acento": "#7aa2f7",
    "acento_hover": "#9ab8ff",
    "exito": "#9ece6a",
    "exito_hover": "#b5e08a",
    "borde": "#33364a",
    "linea_actual": "#24263a",
    "seleccion": "#33467c",
}


class EditorConLineas(tk.Frame):

    def __init__(self, master, fuente):
        super().__init__(master, bg=COLORES["editor"])
        self.fuente = fuente

        self.numeros = tk.Canvas(
            self, width=52, bg=COLORES["panel"], highlightthickness=0, bd=0
        )
        self.numeros.pack(side="left", fill="y")

        self.texto = tk.Text(
            self,
            font=fuente,
            bg=COLORES["editor"],
            fg=COLORES["texto"],
            insertbackground=COLORES["acento"],
            selectbackground=COLORES["seleccion"],
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            wrap="none",
            undo=True,
            tabs=(fuente.measure("    "),),
        )
        scroll_y = ttk.Scrollbar(self, orient="vertical", command=self._scroll_y)
        scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self.texto.xview)
        self.texto.configure(
            yscrollcommand=lambda *a: (scroll_y.set(*a), self._redibujar()),
            xscrollcommand=scroll_x.set,
        )
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        self.texto.pack(side="left", fill="both", expand=True)

        self.texto.tag_configure("linea_actual", background=COLORES["linea_actual"])
        self.texto.tag_lower("linea_actual")

        for evento in ("<KeyRelease>", "<ButtonRelease-1>", "<Configure>", "<<Modified>>"):
            self.texto.bind(evento, self._al_cambiar, add="+")

    def _scroll_y(self, *args):
        self.texto.yview(*args)
        self._redibujar()

    def _al_cambiar(self, _evento=None):
        self.texto.edit_modified(False)
        self.texto.tag_remove("linea_actual", "1.0", "end")
        self.texto.tag_add("linea_actual", "insert linestart", "insert lineend+1c")
        self._redibujar()
        self.event_generate("<<CursorMovido>>")

    def _redibujar(self):
        self.numeros.delete("all")
        actual = self.texto.index("insert").split(".")[0]
        indice = self.texto.index("@0,0")
        while True:
            info = self.texto.dlineinfo(indice)
            if info is None:
                break
            linea = indice.split(".")[0]
            color = COLORES["acento"] if linea == actual else COLORES["texto_tenue"]
            self.numeros.create_text(
                42, info[1] + 8, anchor="ne", text=linea, fill=color, font=self.fuente
            )
            indice = self.texto.index(f"{indice}+1line")
            if indice.split(".")[0] == linea:
                break

    def obtener(self):
        return self.texto.get("1.0", "end-1c")

    def establecer(self, contenido):
        self.texto.delete("1.0", "end")
        self.texto.insert("1.0", contenido)
        self.texto.edit_reset()
        self.texto.mark_set("insert", "1.0")
        self.texto.see("1.0")
        self._al_cambiar()

    def limpiar(self):
        self.establecer("")


class BotonPlano(tk.Label):

    def __init__(self, master, texto, comando, color, color_hover):
        super().__init__(
            master,
            text=texto,
            bg=color,
            fg=COLORES["fondo"],
            font=("Segoe UI", 10, "bold"),
            padx=18,
            pady=8,
            cursor="hand2",
        )
        self.bind("<Button-1>", lambda _e: comando())
        self.bind("<Enter>", lambda _e: self.configure(bg=color_hover))
        self.bind("<Leave>", lambda _e: self.configure(bg=color))


class InterfazMarkdown(tk.Tk):

    def __init__(self, analizar=None):
        super().__init__()
        self.analizar_callback = analizar

        self.title("Analizador de Markdown")
        self.geometry("1100x720")
        self.minsize(720, 480)
        self.configure(bg=COLORES["fondo"])

        self.fuente_editor = self._fuente_mono()
        self._estilos()
        self._construir_encabezado()
        self._construir_barra_estado()
        self._construir_cuerpo()

        self.bind("<Control-o>", lambda _e: self.cargar_archivo())
        self.bind("<F5>", lambda _e: self.analizar())

    def _fuente_mono(self):
        disponibles = set(tkfont.families())
        for nombre in ("JetBrains Mono", "Fira Code", "Cascadia Code", "Consolas",
                       "DejaVu Sans Mono", "Courier New"):
            if nombre in disponibles:
                return tkfont.Font(family=nombre, size=12)
        return tkfont.nametofont("TkFixedFont")

    def _estilos(self):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure(
            "TScrollbar",
            background=COLORES["panel"],
            troughcolor=COLORES["editor"],
            bordercolor=COLORES["editor"],
            arrowcolor=COLORES["texto_tenue"],
            relief="flat",
        )
        estilo.map("TScrollbar", background=[("active", COLORES["borde"])])
        estilo.configure(
            "Treeview",
            background=COLORES["editor"],
            fieldbackground=COLORES["editor"],
            foreground=COLORES["texto"],
            bordercolor=COLORES["borde"],
            rowheight=24,
            font=("Segoe UI", 10),
        )
        estilo.map("Treeview", background=[("selected", COLORES["seleccion"])])
        estilo.configure(
            "Treeview.Heading",
            background=COLORES["panel"],
            foreground=COLORES["texto_tenue"],
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        )
        estilo.map("Treeview.Heading", background=[("active", COLORES["borde"])])
        estilo.configure("TNotebook", background=COLORES["fondo"], borderwidth=0)
        estilo.configure(
            "TNotebook.Tab",
            background=COLORES["panel"],
            foreground=COLORES["texto_tenue"],
            padding=(14, 6),
            font=("Segoe UI", 10, "bold"),
        )
        estilo.map(
            "TNotebook.Tab",
            background=[("selected", COLORES["editor"])],
            foreground=[("selected", COLORES["texto"])],
        )

    def _construir_encabezado(self):
        barra = tk.Frame(self, bg=COLORES["panel"], padx=20, pady=14)
        barra.pack(fill="x")

        titulos = tk.Frame(barra, bg=COLORES["panel"])
        titulos.pack(side="left")
        tk.Label(
            titulos, text="Markdown", bg=COLORES["panel"], fg=COLORES["texto"],
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")
        tk.Label(
            titulos, text="Analizador léxico de Markdown",
            bg=COLORES["panel"], fg=COLORES["texto_tenue"], font=("Segoe UI", 10),
        ).pack(anchor="w")

        botones = tk.Frame(barra, bg=COLORES["panel"])
        botones.pack(side="right")
        BotonPlano(botones, "Analizar", self.analizar,
                   COLORES["exito"], COLORES["exito_hover"]).pack(side="right", padx=(10, 0))
        BotonPlano(botones, "Cargar archivo", self.cargar_archivo,
                   COLORES["acento"], COLORES["acento_hover"]).pack(side="right")

        tk.Frame(self, bg=COLORES["borde"], height=1).pack(fill="x")

    def _construir_cuerpo(self):
        paneles = tk.PanedWindow(
            self, orient="vertical", bg=COLORES["fondo"], sashwidth=6, bd=0,
        )
        paneles.pack(fill="both", expand=True)
        paneles.add(self._construir_editor(paneles), stretch="always", minsize=160)
        paneles.add(self._construir_resultados(paneles), stretch="always", minsize=140)

    def _construir_editor(self, padre):
        contenedor = tk.Frame(padre, bg=COLORES["fondo"], padx=16, pady=16)

        tk.Label(
            contenedor, text="DOCUMENTO MARKDOWN", bg=COLORES["fondo"],
            fg=COLORES["texto_tenue"], font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(0, 6))

        marco = tk.Frame(contenedor, bg=COLORES["borde"], padx=1, pady=1)
        marco.pack(fill="both", expand=True)
        self.editor = EditorConLineas(marco, self.fuente_editor)
        self.editor.pack(fill="both", expand=True)
        self.editor.bind("<<CursorMovido>>", lambda _e: self._actualizar_posicion())
        return contenedor

    def _construir_resultados(self, padre):
        contenedor = tk.Frame(padre, bg=COLORES["fondo"], padx=16)
        self.pestanas = ttk.Notebook(contenedor)
        self.pestanas.pack(fill="both", expand=True, pady=(0, 12))

        self.tabla_tokens = self._crear_tabla(self.pestanas, [
            ("No.", 60, "center"), ("Lexema", 260, "w"), ("Tipo", 200, "w"),
            ("Línea", 70, "center"), ("Columna", 80, "center"),
        ])
        self.tabla_errores = self._crear_tabla(self.pestanas, [
            ("No.", 50, "center"), ("Lexema", 110, "w"), ("Tipo", 220, "w"),
            ("Descripción", 420, "w"), ("Línea", 60, "center"), ("Columna", 70, "center"),
        ])
        self.tabla_errores.tabla.tag_configure("error", foreground="#f7768e")
        self.pestanas.add(self.tabla_tokens, text="Tokens")
        self.pestanas.add(self.tabla_errores, text="Errores")

        for marco in (self.tabla_tokens, self.tabla_errores):
            marco.tabla.bind("<Double-1>", lambda _e, m=marco: self._ir_a_fila(m.tabla))
        return contenedor

    def _crear_tabla(self, padre, columnas):
        marco = tk.Frame(padre, bg=COLORES["editor"])
        nombres = [nombre for nombre, _, _ in columnas]
        tabla = ttk.Treeview(marco, columns=nombres, show="headings")
        for nombre, ancho, alineacion in columnas:
            tabla.heading(nombre, text=nombre)
            tabla.column(nombre, width=ancho, anchor=alineacion,
                         stretch=nombre in ("Lexema", "Descripción"))
        scroll = ttk.Scrollbar(marco, orient="vertical", command=tabla.yview)
        tabla.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        tabla.pack(side="left", fill="both", expand=True)
        marco.tabla = tabla
        return marco

    def _ir_a_fila(self, tabla):
        seleccion = tabla.selection()
        if not seleccion:
            return
        valores = tabla.item(seleccion[0], "values")
        linea, columna = valores[-2], valores[-1]
        indice = f"{linea}.{max(int(columna) - 1, 0)}"
        self.editor.texto.mark_set("insert", indice)
        self.editor.texto.see(indice)
        self.editor.texto.focus_set()
        self.editor._al_cambiar()

    @staticmethod
    def _lexema_visible(lexema):
        if lexema == "":
            return "(virtual)"
        visible = lexema.replace("\n", "↵").replace("\t", "→")
        if not lexema.strip():
            visible = visible.replace(" ", "·")
        return visible

    def mostrar_resultados(self, tokens, errores):
        tabla = self.tabla_tokens.tabla
        tabla.delete(*tabla.get_children())
        for numero, token in enumerate(tokens, start=1):
            tabla.insert("", "end", values=(
                numero, self._lexema_visible(token.lexema), token.tipo,
                token.linea, token.columna,
            ))

        tabla = self.tabla_errores.tabla
        tabla.delete(*tabla.get_children())
        for error in errores:
            tabla.insert("", "end", tags=("error",), values=(
                error.numero, self._lexema_visible(error.lexema),
                f"{error.tipo} ({error.fase})", error.descripcion,
                error.linea, error.columna,
            ))

        self.pestanas.tab(self.tabla_tokens, text=f"Tokens ({len(tokens)})")
        self.pestanas.tab(self.tabla_errores, text=f"Errores ({len(errores)})")
        if errores:
            self.pestanas.select(self.tabla_errores)
            self._estado(f"✖ Análisis terminado con {len(errores)} error(es).", "#f7768e")
        else:
            self.pestanas.select(self.tabla_tokens)
            self._estado(f"✔ Análisis exitoso: {len(tokens)} tokens, sin errores.",
                         COLORES["exito"])

    def _construir_barra_estado(self):
        barra = tk.Frame(self, bg=COLORES["panel"], padx=16, pady=6)
        barra.pack(fill="x", side="bottom")
        self.lbl_estado = tk.Label(
            barra, text="Listo. Carga un archivo .md o escribe directamente (Ctrl+O · F5).",
            bg=COLORES["panel"], fg=COLORES["texto_tenue"], font=("Segoe UI", 9),
        )
        self.lbl_estado.pack(side="left")
        self.lbl_posicion = tk.Label(
            barra, text="Lín 1, Col 1", bg=COLORES["panel"],
            fg=COLORES["texto_tenue"], font=("Segoe UI", 9),
        )
        self.lbl_posicion.pack(side="right")

    def _actualizar_posicion(self):
        linea, columna = self.editor.texto.index("insert").split(".")
        total = int(self.editor.texto.index("end-1c").split(".")[0])
        self.lbl_posicion.configure(
            text=f"Lín {linea}, Col {int(columna) + 1}   ·   {total} líneas"
        )

    def _estado(self, mensaje, color=None):
        self.lbl_estado.configure(text=mensaje, fg=color or COLORES["texto_tenue"])

    def _seleccionar_archivo(self):
        if sys.platform.startswith("linux"):
            inicio = os.path.expanduser("~") + "/"
            comandos = []
            if shutil.which("zenity"):
                comandos.append([
                    "zenity", "--file-selection", "--title=Selecciona un archivo Markdown",
                    f"--filename={inicio}",
                    "--file-filter=Markdown | *.md *.markdown",
                    "--file-filter=Todos los archivos | *",
                ])
            if shutil.which("kdialog"):
                comandos.append([
                    "kdialog", "--getopenfilename", inicio,
                    "Markdown (*.md *.markdown)|Todos los archivos (*)",
                ])
            for comando in comandos:
                try:
                    resultado = subprocess.run(comando, capture_output=True, text=True)
                except OSError:
                    continue
                return resultado.stdout.strip() if resultado.returncode == 0 else ""

        return filedialog.askopenfilename(
            title="Selecciona un archivo Markdown",
            initialdir=os.path.expanduser("~"),
            filetypes=[("Markdown", "*.md *.markdown"), ("Todos los archivos", "*.*")],
        )

    def cargar_archivo(self):
        ruta = self._seleccionar_archivo()
        if not ruta:
            return
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                contenido = archivo.read()
        except (OSError, UnicodeDecodeError) as error:
            messagebox.showerror("Error al cargar", f"No se pudo leer el archivo:\n{error}")
            return
        self.editor.establecer(contenido)
        nombre = ruta.replace("\\", "/").split("/")[-1]
        self._estado(f"✔ Cargado: {nombre}", COLORES["exito"])

    def analizar(self):
        texto = self.editor.obtener()
        if not texto.strip():
            messagebox.showwarning("Editor vacío", "No hay texto para analizar.")
            return
        if self.analizar_callback is None:
            self._estado("El analizador léxico aún no está conectado.", COLORES["acento"])
            return
        tokens, errores = self.analizar_callback(texto)
        self.mostrar_resultados(tokens, errores)
