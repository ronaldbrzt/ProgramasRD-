import pygame
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from PIL import Image, ImageTk
import os

# --- CONFIGURACIÓN PYGAME SELECTOR ---
def selector_dieta_pygame():
    pygame.init()
    WHITE = (255, 255, 255)
    GRAY = (200, 200, 200)
    PURPLE = (136, 0, 123)
    BLACK = (0, 0, 0)
    ANCHO, ALTO = 460, 140
    screen = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Selector de dieta")

    font = pygame.font.SysFont("Arial", 26)
    font_btn = pygame.font.SysFont("Arial", 22)
    opciones = ["Omnívoro", "Vegetariano", "Vegano"]
    selected = 0

    running = True
    while running:
        screen.fill((243, 249, 241))
        titulo = font.render("Selecciona tu tipo de dieta:", True, BLACK)
        screen.blit(titulo, (30, 15))

        botones = []
        x = 30
        y = 60
        w = 130
        h = 45
        sep = 10
        for i, texto in enumerate(opciones):
            rect = pygame.Rect(x + i*(w+sep), y, w, h)
            if i == selected:
                pygame.draw.rect(screen, PURPLE, rect, border_radius=22)
                color_texto = WHITE
            else:
                pygame.draw.rect(screen, WHITE, rect, border_radius=22)
                pygame.draw.rect(screen, GRAY, rect, 2, border_radius=22)
                color_texto = BLACK
            texto_render = font_btn.render(texto, True, color_texto)
            screen.blit(
                texto_render, (
                    rect.x + (w-texto_render.get_width())//2,
                    rect.y + (h-texto_render.get_height())//2
                )
            )
            botones.append(rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(botones):
                    if rect.collidepoint(event.pos):
                        selected = i
                        running = False  # Selección hecha

        pygame.display.flip()
    pygame.quit()
    return opciones[selected]

# -------- BASE DE DATOS --------
def crear_base_datos():
    conn = sqlite3.connect("recetas.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            ingredientes TEXT NOT NULL,
            cantidades TEXT NOT NULL,
            preparacion TEXT NOT NULL,
            tiempo_coccion TEXT NOT NULL
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM recetas")
    if cursor.fetchone()[0] == 0:
        recetas_ejemplo = [
            ("Tortilla de papa", "papa, huevo, cebolla, sal, aceite", "3 papas, 3 huevos, 1 cebolla, sal, aceite", "Freír papas y cebolla. Mezclar con huevo batido. Cocinar en sartén.", "25 minutos"),
            ("Omelet de queso", "huevos, queso, sal, aceite", "2 huevos, 50g queso, 1 pizca sal, 1 cda aceite", "Batir huevos, calentar en sartén con aceite, añadir queso, doblar y cocinar.", "5 minutos"),
            ("Arroz con pollo", "arroz, pollo, cebolla, ajo, aceite, sal", "200g arroz, 150g pollo, 1 cebolla, 1 diente de ajo, 1 cda aceite, 1 cdita sal", "Dorar el pollo. Agregar ajo y cebolla. Añadir arroz y agua. Cocinar 20 minutos.", "30 minutos"),
            ("Ensalada fresca", "lechuga, tomate, zanahoria, sal, aceite", "4 hojas lechuga, 1 tomate, 1 zanahoria, 1 cdita sal, 1 cda aceite", "Lavar y cortar los vegetales. Mezclar con aceite y sal.", "10 minutos"),
            ("Spaghetti bolognesa", "spaghetti, carne, tomate, cebolla, ajo, sal", "200g spaghetti, 150g carne, 2 tomates, 1 cebolla, 1 ajo, sal", "Hervir pasta. Cocinar carne con vegetales. Mezclar y servir.", "30 minutos")
        ]
        cursor.executemany("INSERT INTO recetas (nombre, ingredientes, cantidades, preparacion, tiempo_coccion) VALUES (?, ?, ?, ?, ?)", recetas_ejemplo)
    conn.commit()
    conn.close()

# Ingredientes prohibidos según tipo de dieta
INGR_PROHIBIDOS = {
    "Vegano": {"huevo", "huevos", "queso", "pollo", "carne", "leche", "miel", "mantequilla", "yogur"},
    "Vegetariano": {"pollo", "carne"},
    "Omnívoro": set()
}

# -------- FUNCIONES --------
def filtrar_por_dieta(ingredientes_text, dieta):
    ingredientes_set = set(i.strip().lower() for i in ingredientes_text.split(","))
    prohibidos = INGR_PROHIBIDOS.get(dieta, set())
    return len(prohibidos.intersection(ingredientes_set)) == 0

def buscar_recetas():
    entrada = entrada_ingredientes.get().lower()
    resultados.delete(*resultados.get_children())
    limpiar_detalle()
    error_label.config(text="", fg="red")

    if not entrada.strip():
        error_label.config(text="Ingresa al menos un ingrediente.")
        return

    ingredientes_usuario = [i.strip() for i in entrada.split(",") if i.strip()]
    if not ingredientes_usuario:
        error_label.config(text="Debes ingresar ingredientes separados por comas.")
        return

    dieta = dieta_seleccionada.get()

    conn = sqlite3.connect("recetas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recetas")
    recetas = cursor.fetchall()
    conn.close()

    encontrados = 0
    for receta in recetas:
        ingredientes_receta = receta[2].lower()
        if not filtrar_por_dieta(ingredientes_receta, dieta):
            continue
        if all(i in ingredientes_receta for i in ingredientes_usuario):
            resultados.insert("", "end", iid=receta[0], values=(receta[1], receta[5], receta[3]))
            encontrados += 1

    if encontrados == 0:
        error_label.config(text="No se encontraron recetas con esos ingredientes para la dieta seleccionada.")

def mostrar_todas():
    resultados.delete(*resultados.get_children())
    limpiar_detalle()
    error_label.config(text="", fg="red")

    dieta = dieta_seleccionada.get()

    conn = sqlite3.connect("recetas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recetas")
    recetas = cursor.fetchall()
    conn.close()

    for receta in recetas:
        ingredientes_receta = receta[2].lower()
        if filtrar_por_dieta(ingredientes_receta, dieta):
            resultados.insert("", "end", iid=receta[0], values=(receta[1], receta[5], receta[3]))

def mostrar_detalle(event):
    item = resultados.focus()
    if not item:
        return
    conn = sqlite3.connect("recetas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT ingredientes, cantidades FROM recetas WHERE id=?", (item,))
    data = cursor.fetchone()
    conn.close()
    if data:
        ingredientes, cantidades = data
        texto = f"Ingredientes:\n{ingredientes}\n\nCantidades:\n{cantidades}"
        detalle_text.config(state="normal")
        detalle_text.delete("1.0", tk.END)
        detalle_text.insert(tk.END, texto)
        detalle_text.config(state="disabled")

def limpiar_detalle():
    detalle_text.config(state="normal")
    detalle_text.delete("1.0", tk.END)
    detalle_text.config(state="disabled")

def limpiar_busqueda():
    entrada_ingredientes.delete(0, tk.END)
    limpiar_detalle()
    resultados.delete(*resultados.get_children())
    error_label.config(text="")

# -------- INICIO: SELECCIÓN DE DIETA (PYGAME) --------
dieta_inicial = selector_dieta_pygame()

# -------- INTERFAZ TKINTER --------
app = tk.Tk()
app.title("Yumlist - Gestor de Recetas")
app.geometry("980x700")
app.configure(bg="#f3f9f1")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", font=("Arial", 10))
style.configure("Treeview.Heading", font=("Arial", 11, "bold"))
style.configure("TButton", font=("Arial", 11, "bold"), background="#66bb6a", foreground="white")

# Logo
frame_logo = tk.Frame(app, bg="#f3f9f1")
frame_logo.pack(pady=10)

try:
    if os.path.exists("logo.jpg"):
        img = Image.open("logo.jpg").resize((100, 100))
        logo_img = ImageTk.PhotoImage(img)
        label_logo = tk.Label(frame_logo, image=logo_img, bg="#f3f9f1")
        label_logo.image = logo_img
    else:
        label_logo = tk.Label(frame_logo, text="Yumlist", font=("Arial", 24, "bold"), bg="#f3f9f1")
    label_logo.pack()
except:
    tk.Label(frame_logo, text="Yumlist", font=("Arial", 24, "bold"), bg="#f3f9f1").pack()

# ------ Selector dieta con botones tipo toggle ------
frame_dieta = tk.Frame(app, bg="#e6ffe6")
frame_dieta.pack(fill="x", padx=10, pady=(0,10))

tk.Label(frame_dieta, text="Selecciona tu tipo de dieta:", font=("Arial", 13, "bold"), bg="#e6ffe6").pack(side="left", padx=(10,5), pady=5)

DIETAS = ["Omnívoro", "Vegetariano", "Vegano"]
dieta_seleccionada = tk.StringVar(value=dieta_inicial)
botones_dieta = {}

def actualizar_dieta(dieta):
    dieta_seleccionada.set(dieta)
    for d, btn in botones_dieta.items():
        if d == dieta:
            btn.config(bg="#88007b", fg="white", bd=0, highlightthickness=0)
        else:
            btn.config(bg="white", fg="black", bd=1, highlightbackground="#d0d0d0", highlightcolor="#d0d0d0")
    mostrar_todas()
    entrada_ingredientes.delete(0, tk.END)
    error_label.config(text="")

for dieta in DIETAS:
    btn = tk.Button(
        frame_dieta,
        text=dieta,
        font=("Arial", 11),
        relief="solid",
        padx=18,
        pady=5,
        bd=1,
        highlightthickness=0,
        bg="#88007b" if dieta == dieta_inicial else "white",
        fg="white" if dieta == dieta_inicial else "black",
        cursor="hand2",
        command=lambda d=dieta: actualizar_dieta(d)
    )
    btn.pack(side="left", padx=5)
    botones_dieta[dieta] = btn

# Entrada y botones
frame_busqueda = tk.Frame(app, bg="#d0f0c0")
frame_busqueda.pack(fill="x", padx=10, pady=12)

label = tk.Label(frame_busqueda, text="Ingredientes disponibles (separados por coma):", font=("Arial", 12), bg="#d0f0c0")
label.grid(row=0, column=0, columnspan=4, pady=5, sticky="w")

entrada_ingredientes = tk.Entry(frame_busqueda, width=60, font=("Arial", 12))
entrada_ingredientes.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="w")

# Botón buscar
boton_buscar = tk.Button(frame_busqueda, text="🔍 Buscar Recetas", command=buscar_recetas, bg="#388e3c", fg="white", font=("Arial", 13, "bold"), relief="raised", borderwidth=2, cursor="hand2", activebackground="#66bb6a")
boton_buscar.grid(row=1, column=2, padx=8, pady=5, sticky="w")

# Botón limpiar
boton_limpiar = tk.Button(frame_busqueda, text="🧹 Limpiar", command=limpiar_busqueda, bg="#1e88e5", fg="white", font=("Arial", 12, "bold"), relief="raised", borderwidth=2, cursor="hand2", activebackground="#6ab7ff")
boton_limpiar.grid(row=1, column=3, padx=8, pady=5, sticky="w")

# Botón mostrar todas
boton_todas = tk.Button(frame_busqueda, text="📖 Mostrar todas las recetas", command=mostrar_todas, bg="#ffa726", fg="white", font=("Arial", 12, "bold"), relief="raised", borderwidth=2, cursor="hand2", activebackground="#ffd95b")
boton_todas.grid(row=2, column=0, columnspan=4, padx=5, pady=(10,2), sticky="we")

error_label = tk.Label(app, text="", bg="#f3f9f1", fg="red", font=("Arial", 11))
error_label.pack()

# Resultados
frame_resultados = tk.Frame(app, bg="#f3f9f1")
frame_resultados.pack(fill="both", expand=True, padx=10, pady=(10,0))

columnas = ("Nombre", "Tiempo", "Preparación")
resultados = ttk.Treeview(frame_resultados, columns=columnas, show="headings", height=12, selectmode="browse")
for col in columnas:
    resultados.heading(col, text=col)
    resultados.column(col, width=250 if col != "Preparación" else 400)
resultados.pack(fill="both", expand=True)
resultados.bind("<<TreeviewSelect>>", mostrar_detalle)

# Detalle de ingredientes y cantidades
frame_detalle = tk.Frame(app, bg="#e2f0d9")
frame_detalle.pack(fill="x", padx=10, pady=10)

label_detalle = tk.Label(frame_detalle, text="Ingredientes y Cantidades", font=("Arial", 12, "bold"), bg="#e2f0d9")
label_detalle.pack(anchor="w", padx=5, pady=5)

detalle_text = tk.Text(frame_detalle, height=7, font=("Arial", 11), bg="white", state="disabled", wrap="word")
detalle_text.pack(fill="x", padx=5, pady=5)

# Tooltips (opcional)
def create_tooltip(widget, text):
    tooltip = tk.Toplevel(widget)
    tooltip.withdraw()
    tooltip.overrideredirect(True)
    tooltip.config(bg="lightyellow")
    label = tk.Label(tooltip, text=text, bg="lightyellow", font=("Arial", 10), justify="left")
    label.pack()
    def enter(event):
        x, y, _, _ = widget.bbox("insert")
        tooltip.geometry(f"+{widget.winfo_rootx()+50}+{widget.winfo_rooty()+20}")
        tooltip.deiconify()
    def leave(event):
        tooltip.withdraw()
    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)

create_tooltip(boton_buscar, "Busca recetas según los ingredientes y dieta elegida.")
create_tooltip(boton_limpiar, "Limpia la búsqueda y resultados.")
create_tooltip(boton_todas, "Muestra todas las recetas disponibles para tu dieta.")

# Inicializar base y mostrar recetas según la dieta elegida en Pygame
crear_base_datos()
mostrar_todas()

app.mainloop()