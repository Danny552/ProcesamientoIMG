"""
interfaz.py 17/10/2025
-----------

Interfaz gráfica para procesamiento de imágenes usando Tkinter.

Autores:
 - Daniel Alejandro Henao
 - Juan Camilo Cano
 - Miguel Angel Arias


Esta aplicación:
 - Permite abrir y visualizar imágenes RGB.
 - Aplica transformaciones (negativo, grises, binarizar, brillo, contraste, rotación).
 - Muestra histograma RGB mediante matplotlib.
 - Realiza fusión ponderada entre dos imágenes.
 - Tiene un panel de controles con scroll para acomodar muchos widgets.
 - Implementa un zoom visual (no destructivo) y restauración de la imagen original.

Dependencias:
 - Python (con tkinter)
 - Pillow (PIL)
 - matplotlib
 - numpy
 - imgControl (librería propia con funciones de procesamiento)
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
import numpy as np
import imgControl


class App:
    """
    Clase principal de la aplicación.

    Atributos principales
    ----------------------
    root : tk.Tk
        Ventana raíz de Tkinter.
    img : np.ndarray | None
        Imagen actual en memoria (float en rango [0,1], forma (h,w,3)).
    img_original : np.ndarray | None
        Copia de la imagen original cargada (permite restaurar).
    img2 : np.ndarray | None
        Segunda imagen para operaciones de fusión.
    imgTk : ImageTk.PhotoImage | None
        Referencia al objeto PhotoImage mostrado (se guarda para evitar garbage collection).
    zoom_factor : float
        Factor de zoom visual actual (1.0 = 100%).
    panel_controles : tk.Frame
        Frame interno que contiene los controles (dentro de un Canvas para scroll).
    panel_imagen : tk.Label
        Widget donde se muestra la imagen (como PhotoImage).
    """

    def __init__(self, root: tk.Tk):
        """
        Construye la interfaz y todos los widgets.

        Parámetros
        ----------
        root : tk.Tk
            La ventana raíz de Tkinter que contiene la aplicación.
        """
        self.root = root
        self.root.title("Procesamiento de Imágenes")
        self.root.geometry("1200x700")
        self.root.configure(bg="#222")

        # Estado de la aplicación
        self.img = None          # Imagen actual (np.ndarray float [0,1])
        self.img_original = None # Copia de la imagen originalmente cargada
        self.img2 = None         # Segunda imagen para fusión
        self.imgTk = None        # Referencia al PhotoImage en uso
        self.zoom_factor = 1.0   # Factor de zoom visual actual

        # === PANEL IZQUIERDO CON SCROLL ===
        frame_scroll = tk.Frame(root, width=300, bg="#2b2b2b")
        frame_scroll.pack(side="left", fill="y")

        # Canvas desplazable (permite scroll de todos los controles)
        canvas = tk.Canvas(frame_scroll, bg="#2b2b2b", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        # Scrollbar vertical conectada al canvas
        scrollbar = ttk.Scrollbar(frame_scroll, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Frame interno donde van los widgets (colocado dentro del canvas)
        self.panel_controles = tk.Frame(canvas, bg="#2b2b2b")
        canvas.create_window((0, 0), window=self.panel_controles, anchor="nw")

        # Actualiza la región de scroll según el contenido del panel_controles
        def actualizar_scroll(event):
            """Callback para actualizar el scrollregion del canvas cuando cambia el tamaño del contenido."""
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.panel_controles.bind("<Configure>", actualizar_scroll)

        # Scroll con la rueda del ratón (mejora la usabilidad)
        def _on_mousewheel(event):
            """Callback para permitir el uso de la rueda del ratón sobre el canvas."""
            # event.delta varía según plataforma (en Windows suele ser múltiplo de 120)
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # PANEL DERECHO - IMAGEN (área de visualización)
        self.panel_imagen = tk.Label(root, bg="#111")
        self.panel_imagen.pack(side="right", expand=True)

        # === SECCIÓN: CARGA DE IMÁGENES ===
        tk.Label(
            self.panel_controles,
            text="CONTROL DE IMÁGENES",
            fg="white",
            bg="#2b2b2b",
            font=("Arial", 12, "bold")
        ).pack(pady=10)

        ttk.Button(self.panel_controles, text="Abrir Imagen", command=self.abrir_imagen).pack(pady=5)
        ttk.Button(self.panel_controles, text="Abrir Imagen 2 (Fusión)", command=self.abrir_imagen2).pack(pady=5)
        ttk.Button(self.panel_controles, text="Guardar Imagen", command=self.guardar_imagen).pack(pady=5)
        ttk.Button(self.panel_controles, text="Restaurar Imagen Original", command=self.restaurar_original).pack(pady=5)
        ttk.Separator(self.panel_controles, orient='horizontal').pack(fill='x', pady=10)

        # === SECCIÓN: TRANSFORMACIONES ===
        tk.Label(self.panel_controles, text="TRANSFORMACIONES", fg="white", bg="#2b2b2b",
                 font=("Arial", 12, "bold")).pack(pady=5)
        ttk.Button(self.panel_controles, text="Negativo", command=self.aplicar_negativo).pack(pady=3)
        ttk.Button(self.panel_controles, text="Escala de Grises", command=self.aplicar_grises).pack(pady=3)
        ttk.Button(self.panel_controles, text="Binarizar", command=self.binarizar).pack(pady=3)
        ttk.Button(self.panel_controles, text="Contraste Logarítmico", command=lambda: self.aplicar_contraste(0)).pack(pady=3)
        ttk.Button(self.panel_controles, text="Contraste Exponencial", command=lambda: self.aplicar_contraste(1)).pack(pady=3)
        ttk.Button(self.panel_controles, text="Mostrar Histograma", command=self.mostrar_histograma).pack(pady=3)
        ttk.Separator(self.panel_controles, orient='horizontal').pack(fill='x', pady=10)

        # === SECCIÓN: BRILLO Y CANALES ===
        tk.Label(self.panel_controles, text="BRILLO Y CANALES", fg="white", bg="#2b2b2b",
                 font=("Arial", 12, "bold")).pack(pady=5)
        self.slider_brillo = tk.Scale(
            self.panel_controles, from_=-0.5, to=0.5, resolution=0.05,
            orient="horizontal", length=200, label="Ajustar brillo",
            bg="#2b2b2b", fg="white"
        )
        self.slider_brillo.pack(pady=5)
        ttk.Button(self.panel_controles, text="Aplicar Brillo", command=self.aplicar_brillo).pack(pady=5)

        self.slider_canal = tk.Scale(
            self.panel_controles, from_=-0.5, to=0.5, resolution=0.05,
            orient="horizontal", length=200, label="Ajustar Canal R",
            bg="#2b2b2b", fg="white"
        )
        self.slider_canal.pack(pady=5)
        ttk.Button(self.panel_controles, text="Aplicar a Canal R", command=lambda: self.ajustar_canal(0)).pack(pady=3)
        ttk.Button(self.panel_controles, text="Aplicar a Canal G", command=lambda: self.ajustar_canal(1)).pack(pady=3)
        ttk.Button(self.panel_controles, text="Aplicar a Canal B", command=lambda: self.ajustar_canal(2)).pack(pady=3)
        ttk.Separator(self.panel_controles, orient='horizontal').pack(fill='x', pady=10)

        # === SECCIÓN: GEOMETRÍA ===
        tk.Label(self.panel_controles, text="GEOMETRÍA", fg="white", bg="#2b2b2b",
                 font=("Arial", 12, "bold")).pack(pady=5)
        self.slider_angulo = tk.Scale(
            self.panel_controles, from_=-180, to=180, orient="horizontal",
            length=200, label="Rotar (°)", bg="#2b2b2b", fg="white"
        )
        self.slider_angulo.pack(pady=5)
        ttk.Button(self.panel_controles, text="Aplicar Rotación", command=self.rotar_img).pack(pady=5)

        # Zoom visual (no cambia los datos, solo la vista)
        self.slider_zoom = tk.Scale(
            self.panel_controles, from_=0.5, to=3, resolution=0.1,
            orient="horizontal", length=200, label="Zoom Visual",
            bg="#2b2b2b", fg="white"
        )
        self.slider_zoom.set(1.0)
        self.slider_zoom.pack(pady=5)
        ttk.Button(self.panel_controles, text="Ampliar", command=self.ampliar).pack(pady=3)
        ttk.Button(self.panel_controles, text="Reducir", command=self.reducir).pack(pady=3)
        ttk.Separator(self.panel_controles, orient='horizontal').pack(fill='x', pady=10)

        # === SECCIÓN: FUSIÓN ===
        tk.Label(self.panel_controles, text="FUSIÓN DE IMÁGENES", fg="white", bg="#2b2b2b",
                 font=("Arial", 12, "bold")).pack(pady=5)
        self.slider_fusion = tk.Scale(
            self.panel_controles, from_=0.0, to=1.0, resolution=0.1,
            orient="horizontal", length=200, label="Factor de fusión",
            bg="#2b2b2b", fg="white"
        )
        self.slider_fusion.pack(pady=5)
        ttk.Button(self.panel_controles, text="Fusionar", command=self.fusionar).pack(pady=3)

    # =============== FUNCIONES PRINCIPALES ===============

    def abrir_imagen(self):
        """
        Abre un diálogo para seleccionar un archivo de imagen (JPG/PNG),
        carga la imagen, la normaliza a float [0,1], guarda una copia original
        y la muestra en la interfaz.

        Efectos secundarios
        -------------------
        - Actualiza self.img (np.ndarray float en [0,1]).
        - Actualiza self.img_original con una copia.
        - Resetea self.zoom_factor a 1.0.
        """
        ruta = filedialog.askopenfilename(filetypes=[("Imágenes", "*.jpg *.png *.jpeg")])
        if ruta:
            imgPIL = Image.open(ruta).convert("RGB")
            self.img = np.array(imgPIL) / 255.0
            self.img_original = self.img.copy()
            self.zoom_factor = 1.0
            self.mostrar_imagen(self.img)

    def abrir_imagen2(self):
        """
        Abre un diálogo para seleccionar la segunda imagen (para fusión).
        Convierte la imagen a RGB y la deja en self.img2 (normalizada [0,1]).
        Muestra un messagebox informando que la imagen 2 fue cargada.
        """
        ruta = filedialog.askopenfilename(filetypes=[("Imágenes", "*.jpg *.png *.jpeg")])
        if ruta:
            imgPIL = Image.open(ruta).convert("RGB")
            self.img2 = np.array(imgPIL) / 255.0
            messagebox.showinfo("Imagen 2", "Segunda imagen cargada correctamente")

    def mostrar_imagen(self, img: np.ndarray, zoom_factor: float | None = None):
        """
        Muestra la imagen proporcionada en el panel de visualización.

        Parámetros
        ----------
        img : np.ndarray
            Imagen en formato (h,w,3) con valores float en [0,1].
        zoom_factor : float, opcional
            Factor de zoom visual (si es None se usa self.zoom_factor).

        Comportamiento
        -------------
        - Convierte a uint8 (0..255) y crea un Image de PIL.
        - Redimensiona la imagen según el zoom visual antes de crear el PhotoImage.
        - Asigna la PhotoImage al widget self.panel_imagen y guarda una referencia.
        """
        if zoom_factor is None:
            zoom_factor = self.zoom_factor
        h, w = img.shape[:2]
        new_h = max(1, int(h * zoom_factor))
        new_w = max(1, int(w * zoom_factor))
        imgPIL = Image.fromarray((img * 255).astype(np.uint8))
        imgPIL = imgPIL.resize((new_w, new_h))
        self.imgTk = ImageTk.PhotoImage(imgPIL)
        self.panel_imagen.config(image=self.imgTk)
        self.panel_imagen.image = self.imgTk  # mantener referencia

    def guardar_imagen(self):
        """
        Guarda la imagen actual (self.img) en disco mediante un diálogo de "guardar como".

        Comportamiento
        -------------
        - Convierte la imagen de float [0,1] a uint8 [0,255].
        - Permite elegir ruta y nombre (extensión por defecto .png).
        - Muestra un messagebox de confirmación al finalizar.
        """
        if self.img is not None:
            ruta = filedialog.asksaveasfilename(defaultextension=".png")
            if ruta:
                imgPIL = Image.fromarray((self.img * 255).astype(np.uint8))
                imgPIL.save(ruta)
                messagebox.showinfo("Guardado", "Imagen guardada con éxito")

    def restaurar_original(self):
        """
        Restaura la imagen actual a la copia original guardada en self.img_original.

        Requisitos
        ----------
        - self.img_original debe existir (se crea al abrir una imagen con abrir_imagen).

        Efectos secundarios
        -------------------
        - Actualiza self.img con una copia de self.img_original.
        - Resetea el zoom visual a 1.0 y actualiza la vista.
        - Muestra un messagebox indicando que se restauró la imagen.
        """
        if self.img_original is not None:
            self.img = self.img_original.copy()
            self.zoom_factor = 1.0
            self.mostrar_imagen(self.img)
            messagebox.showinfo("Restaurada", "La imagen ha sido restaurada a su estado original")

    # =============== TRANSFORMACIONES (llaman a imgControl) ===============

    def aplicar_negativo(self):
        """
        Aplica el negativo a la imagen actual usando imgControl.Negativo.

        Requisito
        ---------
        - self.img no debe ser None.
        """
        if self.img is not None:
            self.img = imgControl.Negativo(self.img)
            self.mostrar_imagen(self.img)

    def aplicar_grises(self):
        """
        Convierte la imagen actual a escala de grises usando imgControl.Grises,
        y vuelve a convertir a formato RGB (tres canales iguales) para mantener la consistencia.
        """
        if self.img is not None:
            gris = imgControl.Grises(self.img)
            gris_rgb = np.stack((gris, gris, gris), axis=2)
            self.img = gris_rgb
            self.mostrar_imagen(self.img)

    def binarizar(self):
        """
        Binariza la imagen actual usando un umbral fijo (0.5).
        - Usa imgControl.Binaria que retorna una máscara booleana.
        - Convierte la máscara a float y la muestra en RGB.
        """
        if self.img is not None:
            umbral = 0.5
            binaria = imgControl.Binaria(self.img, umbral)
            binaria_rgb = np.stack((binaria, binaria, binaria), axis=2)
            self.img = binaria_rgb.astype(float)
            self.mostrar_imagen(self.img)

    def aplicar_brillo(self):
        """
        Ajusta el brillo de la imagen actual según el valor del slider self.slider_brillo.
        - Llama a imgControl.SumarBrillo.
        - Aplica np.clip para mantener valores en [0,1].
        """
        if self.img is not None:
            brillo = self.slider_brillo.get()
            self.img = imgControl.SumarBrillo(self.img, brillo)
            self.img = np.clip(self.img, 0, 1)
            self.mostrar_imagen(self.img)

    def ajustar_canal(self, canal: int):
        """
        Ajusta únicamente el canal indicado (0=R, 1=G, 2=B) según el valor del slider self.slider_canal.

        Parámetros
        ----------
        canal : int
            Índice del canal a ajustar (0=R, 1=G, 2=B).
        """
        if self.img is not None:
            ajuste = self.slider_canal.get()
            self.img = imgControl.AjusteCanal(self.img, canal, ajuste)
            self.img = np.clip(self.img, 0, 1)
            self.mostrar_imagen(self.img)

    def aplicar_contraste(self, tipo: int):
        """
        Aplica ajuste de contraste según el tipo:
        - tipo == 0 -> contraste logarítmico (imgControl.AjusteContraste con zonas=0)
        - tipo == 1 -> contraste exponencial (imgControl.AjusteContraste con zonas=1)

        Parámetros
        ----------
        tipo : int
            Selector del tipo de contraste (0 log, 1 exp).
        """
        if self.img is not None:
            self.img = imgControl.AjusteContraste(self.img, tipo, 1.2)
            self.img = np.clip(self.img, 0, 1)
            self.mostrar_imagen(self.img)

    def rotar_img(self):
        """
        Rota la imagen actual por el ángulo seleccionado en self.slider_angulo.
        - Usa imgControl.RotarImg que devuelve una nueva matriz rotada.
        """
        if self.img is not None:
            angulo = self.slider_angulo.get()
            self.img = imgControl.RotarImg(self.img, angulo)
            self.mostrar_imagen(self.img)

    # ==== ZOOM VISUAL (no destructivo) ====

    def ampliar(self):
        """
        Ajusta el zoom visual al valor del slider self.slider_zoom.
        - No altera self.img; solo cambia self.zoom_factor y actualiza la vista.
        """
        if self.img is not None:
            self.zoom_factor = self.slider_zoom.get()
            self.mostrar_imagen(self.img)

    def reducir(self):
        """
        Ajusta el zoom visual a la inversa del valor del slider self.slider_zoom.
        - Implementación actual: zoom_factor = 1 / slider_value (si slider_value != 0).
        - Alternativamente, se puede usar el valor directo según preferencia.
        """
        if self.img is not None:
            factor = self.slider_zoom.get()
            self.zoom_factor = 1 / factor if factor != 0 else 1
            self.mostrar_imagen(self.img)

    def mostrar_histograma(self):
        """
        Obtiene los histogramas por canal usando imgControl.Histograma y los muestra
        en una ventana de matplotlib con tres curvas (R, G, B).
        """
        if self.img is not None:
            histR, histG, histB = imgControl.Histograma(self.img)
            plt.figure()
            plt.plot(histR, 'r')
            plt.plot(histG, 'g')
            plt.plot(histB, 'b')
            plt.title("Histograma RGB")
            plt.xlabel("Intensidad (0-255)")
            plt.ylabel("Frecuencia")
            plt.show()

    def fusionar(self):
        """
        Fusiona self.img y self.img2 con un factor determinado por self.slider_fusion.
        - Recorta las imágenes al tamaño mínimo común para evitar broadcasting.
        - Usa imgControl.CombinarF(img1, img2, factor) que realiza mezcla lineal.
        - Sobrescribe self.img con el resultado y lo muestra.
        """
        if self.img is not None and self.img2 is not None:
            factor = self.slider_fusion.get()
            h1, w1 = self.img.shape[:2]
            h2, w2 = self.img2.shape[:2]
            h = min(h1, h2)
            w = min(w1, w2)
            img1r = self.img[:h, :w]
            img2r = self.img2[:h, :w]
            self.img = imgControl.CombinarF(img1r, img2r, factor)
            self.mostrar_imagen(self.img)


# Punto de entrada de la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
