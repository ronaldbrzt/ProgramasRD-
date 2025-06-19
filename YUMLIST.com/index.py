import pygame
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import sqlite3
import os

# --- FUNCIONES PARA CREAR BOTONES OVALADOS PNG CON PYGAME ---
def crear_boton_ovalado(texto, color, color_borde, color_texto, ancho=140, alto=44):
    """Devuelve un botón ovalado con el texto, listo para PhotoImage Tkinter."""
    pygame.init()
    surface = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    # Fondo ovalado
    pygame.draw.ellipse(surface, color, (0, 0, ancho, alto))
    pygame.draw.ellipse(surface, color_borde, (0, 0, ancho, alto), 3)
    font = pygame.font.SysFont("Arial", 21, bold=True)
    rendered_text = font.render(texto, True, color_texto)
    rect = rendered_text.get_rect(center=(ancho//2, alto//2))
    surface.blit(rendered_text, rect)
    raw = pygame.image.tostring(surface, "RGBA")
    img = Image.frombytes("RGBA", (ancho, alto), raw)
    return ImageTk.PhotoImage(img)

# --------- BASE DE DATOS ---------
def crear_base_datos():
    conn = sqlite3.connect("recetas.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(recetas)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'dieta' not in columns:
        try:
            cursor.execute("ALTER TABLE recetas ADD COLUMN dieta TEXT DEFAULT 'Omnívoro'")
        except:
            pass
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            ingredientes TEXT NOT NULL,
            cantidades TEXT NOT NULL,
            preparacion TEXT NOT NULL,
            tiempo_coccion TEXT NOT NULL,
            dieta TEXT DEFAULT 'Omnívoro'
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM recetas")
    if cursor.fetchone()[0] == 0:
        recetas_ejemplo = [
            ("Tortilla de papa", "papa, huevo, cebolla, sal, aceite", "3 papas, 3 huevos, 1 cebolla, sal, aceite", "Freír papas y cebolla. Mezclar con huevo batido. Cocinar en sartén.", "25 minutos", "Omnívoro"),
            ("Ensalada fresca", "lechuga, tomate, zanahoria, sal, aceite", "4 hojas lechuga, 1 tomate, 1 zanahoria, 1 cdita sal, 1 cda aceite", "Lavar y cortar los vegetales. Mezclar con aceite y sal.", "10 minutos", "Vegano,Vegetariano,Omnívoro")
        ]
        cursor.executemany(
            "INSERT INTO recetas (nombre, ingredientes, cantidades, preparacion, tiempo_coccion, dieta) VALUES (?, ?, ?, ?, ?, ?)",
            recetas_ejemplo
        )
    conn.commit()
    conn.close()

# --------- FUNCIONES DE LÓGICA ---------
INGR_PROHIBIDOS = {
    "Vegano": {"huevo", "huevos", "queso", "pollo", "carne", "leche", "miel", "mantequilla", "yogur"},
    "Vegetariano": {"pollo", "carne"},
    "Omnívoro": set()
}

def filtrar_por_dieta(ingredientes_text, dieta, dieta_receta):
    if dieta not in [d.strip() for d in dieta_receta.split(",")]:
        return False
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
        dieta_receta = receta[6] if len(receta) > 6 else "Omnívoro"
        if not filtrar_por_dieta(ingredientes_receta, dieta, dieta_receta):
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
        dieta_receta = receta[6] if len(receta) > 6 else "Omnívoro"
        if filtrar_por_dieta(ingredientes_receta, dieta, dieta_receta):
            resultados.insert("", "end", iid=receta[0], values=(receta[1], receta[5], receta[3]))

def mostrar_detalle(event):
    item = resultados.focus()
    if not item:
        return
    conn = sqlite3.connect("recetas.db")
    cursor = conn.cursor()
    cursor.execute("SELECT ingredientes, cantidades, preparacion FROM recetas WHERE id=?", (item,))
    data = cursor.fetchone()
    conn.close()
    if data:
        ingredientes, cantidades, preparacion = data
        texto = f"Ingredientes:\n{ingredientes}\n\nCantidades:\n{cantidades}"
        detalle_text.config(state="normal")
        detalle_text.delete("1.0", tk.END)
        detalle_text.insert(tk.END, texto)
        detalle_text.config(state="disabled")
        paso_paso_text.config(state="normal")
        paso_paso_text.delete("1.0", tk.END)
        paso_paso_text.insert(tk.END, f"• {preparacion}")
        paso_paso_text.config(state="disabled")

def limpiar_detalle():
    detalle_text.config(state="normal"); detalle_text.delete("1.0", tk.END); detalle_text.config(state="disabled")
    paso_paso_text.config(state="normal"); paso_paso_text.delete("1.0", tk.END); paso_paso_text.config(state="disabled")

def limpiar_busqueda():
    entrada_ingredientes.delete(0, tk.END)
    limpiar_detalle()
    resultados.delete(*resultados.get_children())
    error_label.config(text="")

def ventana_alimento(modo="agregar"):
    if modo == "editar":
        item = resultados.focus()
        if not item:
            messagebox.showerror("Error", "Selecciona una receta para editar.")
            return
        conn = sqlite3.connect("recetas.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, ingredientes, cantidades, preparacion, tiempo_coccion, dieta FROM recetas WHERE id=?", (item,))
        data = cursor.fetchone()
        conn.close()
        if not data:
            messagebox.showerror("Error", "No se pudo obtener la receta.")
            return
    else:
        data = ("", "", "", "", "", "")

    def guardar_alimento():
        nombre = entry_nombre.get().strip()
        ingredientes = entry_ingredientes.get().strip()
        cantidades = entry_cantidades.get().strip()
        preparacion = entry_preparacion.get("1.0", tk.END).strip()
        tiempo = entry_tiempo.get().strip()
        dietas_sel = []
        if var_omni.get(): dietas_sel.append("Omnívoro")
        if var_vege.get(): dietas_sel.append("Vegetariano")
        if var_vegan.get(): dietas_sel.append("Vegano")
        if not nombre or not ingredientes or not cantidades or not preparacion or not tiempo or not dietas_sel:
            messagebox.showerror("Error", "Todos los campos y al menos una dieta son requeridos.")
            return
        dieta_str = ",".join(dietas_sel)
        conn = sqlite3.connect("recetas.db")
        cursor = conn.cursor()
        if modo == "agregar":
            cursor.execute("INSERT INTO recetas (nombre, ingredientes, cantidades, preparacion, tiempo_coccion, dieta) VALUES (?, ?, ?, ?, ?, ?)",
                           (nombre, ingredientes, cantidades, preparacion, tiempo, dieta_str))
        else:
            rid = item
            cursor.execute("UPDATE recetas SET nombre=?, ingredientes=?, cantidades=?, preparacion=?, tiempo_coccion=?, dieta=? WHERE id=?",
                           (nombre, ingredientes, cantidades, preparacion, tiempo, dieta_str, rid))
        conn.commit()
        conn.close()
        win.destroy()
        mostrar_todas()

    win = tk.Toplevel(app)
    win.title("Agregar alimento" if modo == "agregar" else "Editar alimento")
    win.grab_set()
    win.geometry("420x470")
    win.resizable(False, False)
    tk.Label(win, text="Nombre:").pack(anchor="w", padx=10, pady=(10,0))
    entry_nombre = tk.Entry(win, width=45)
    entry_nombre.insert(0, data[0])
    entry_nombre.pack(padx=10)
    tk.Label(win, text="Ingredientes (separados por coma):").pack(anchor="w", padx=10, pady=(10,0))
    entry_ingredientes = tk.Entry(win, width=45)
    entry_ingredientes.insert(0, data[1])
    entry_ingredientes.pack(padx=10)
    tk.Label(win, text="Cantidades:").pack(anchor="w", padx=10, pady=(10,0))
    entry_cantidades = tk.Entry(win, width=45)
    entry_cantidades.insert(0, data[2])
    entry_cantidades.pack(padx=10)
    tk.Label(win, text="Preparación:").pack(anchor="w", padx=10, pady=(10,0))
    entry_preparacion = tk.Text(win, width=45, height=4)
    entry_preparacion.insert("1.0", data[3])
    entry_preparacion.pack(padx=10)
    tk.Label(win, text="Tiempo cocción:").pack(anchor="w", padx=10, pady=(10,0))
    entry_tiempo = tk.Entry(win, width=45)
    entry_tiempo.insert(0, data[4])
    entry_tiempo.pack(padx=10, pady=(0,10))
    tk.Label(win, text="Dieta(s):").pack(anchor="w", padx=10, pady=(10,0))
    var_omni     = tk.IntVar(value=1 if "Omnívoro" in data[5] else 0)
    var_vege     = tk.IntVar(value=1 if "Vegetariano" in data[5] else 0)
    var_vegan    = tk.IntVar(value=1 if "Vegano" in data[5] else 0)
    ch_omni  = tk.Checkbutton(win, text="Omnívoro", variable=var_omni)
    ch_vege  = tk.Checkbutton(win, text="Vegetariano", variable=var_vege)
    ch_vegan = tk.Checkbutton(win, text="Vegano", variable=var_vegan)
    ch_omni.pack(anchor="w", padx=30)
    ch_vege.pack(anchor="w", padx=30)
    ch_vegan.pack(anchor="w", padx=30)
    boton_guardar = tk.Button(win, text="Guardar", bg="#388e3c", fg="white", font=("Arial", 11, "bold"),
                              command=guardar_alimento)
    boton_guardar.pack(pady=10)

def eliminar_alimento():
    item = resultados.focus()
    if not item:
        messagebox.showerror("Error", "Selecciona una receta para eliminar.")
        return
    nombre = resultados.item(item, "values")[0]
    if messagebox.askyesno("Confirmar", f"¿Seguro que deseas eliminar '{nombre}'?"):
        conn = sqlite3.connect("recetas.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM recetas WHERE id=?", (item,))
        conn.commit()
        conn.close()
        mostrar_todas()

# -------- INTERFAZ TKINTER --------
app = tk.Tk()
app.title("Yumlist - Gestor de Recetas")
app.geometry("980x700")

# Fondo principal
bg_image_path = "imagen.jpg"
if os.path.exists(bg_image_path):
    img = Image.open(bg_image_path).resize((980, 700))
    bg_img = ImageTk.PhotoImage(img)
    bg_label = tk.Label(app, image=bg_img)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

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
        img_logo = Image.open("logo.jpg").resize((100, 100))
        logo_img = ImageTk.PhotoImage(img_logo)
        label_logo = tk.Label(frame_logo, image=logo_img, bg="#f3f9f1")
        label_logo.image = logo_img
    else:
        label_logo = tk.Label(frame_logo, text="Yumlist", font=("Arial", 24, "bold"), bg="#f3f9f1")
    label_logo.pack()
except:
    tk.Label(frame_logo, text="Yumlist", font=("Arial", 24, "bold"), bg="#f3f9f1").pack()

# Selector dieta con botones tipo toggle
frame_dieta = tk.Frame(app, bg="#e6ffe6")
frame_dieta.pack(fill="x", padx=8, pady=(0,8))
tk.Label(frame_dieta, text="Selecciona tu tipo de dieta:", font=("Arial", 13, "bold"), bg="#e6ffe6").pack(side="left", padx=(10,5), pady=5)
DIETAS = ["Omnívoro", "Vegetariano", "Vegano"]
dieta_inicial = "Omnívoro"
dieta_seleccionada = tk.StringVar(value=dieta_inicial)
botones_dieta = {}
for dieta in DIETAS:
    btn = tk.Radiobutton(frame_dieta, text=dieta, variable=dieta_seleccionada, value=dieta, indicatoron=0,
                         font=("Arial", 11, "bold"),
                         selectcolor="#d1c4e9" if dieta=="Vegano" else "#fff",
                         command=mostrar_todas,
                         bg="#fff", relief="groove", bd=2, padx=8, pady=3,
                         fg="#88007b" if dieta=="Vegano" else "#444")
    btn.pack(side="left", padx=4)
    botones_dieta[dieta] = btn

# Entrada de ingredientes
frame_busqueda = tk.Frame(app, bg="#d0f0c0", bd=0)
frame_busqueda.pack(fill="x", padx=8, pady=2)
label = tk.Label(frame_busqueda, text="Ingredientes disponibles (separados por coma):", font=("Arial", 12), bg="#d0f0c0")
label.grid(row=0, column=0, columnspan=7, pady=3, sticky="w")
entrada_ingredientes = tk.Entry(frame_busqueda, width=52, font=("Arial", 12))
entrada_ingredientes.grid(row=1, column=0, columnspan=6, padx=3, pady=5, sticky="w")

# Botones ovalados en su propio frame y bien separados
frame_botones = tk.Frame(frame_busqueda, bg="#d0f0c0")
frame_botones.grid(row=2, column=0, columnspan=7, pady=10)

# Colores y botones pygame ovalados
botones_img = {}
botones_img['buscar'] = crear_boton_ovalado("🔍 Buscar Recetas", (60,179,113), (24, 100, 50), (255,255,255))
botones_img['limpiar'] = crear_boton_ovalado("Limpiar", (33, 150, 243), (8,48,114), (255,255,255))
botones_img['mostrar'] = crear_boton_ovalado("Mostrar", (255,193,7), (173,109,0), (50,50,50))
botones_img['editar'] = crear_boton_ovalado("Editar", (3, 169, 244), (0,45,104), (255,255,255))
botones_img['eliminar'] = crear_boton_ovalado("Eliminar", (229,57,53), (100,0,0), (255,255,255))

boton_buscar = tk.Button(frame_botones, image=botones_img['buscar'], command=buscar_recetas, bd=0, bg="#d0f0c0", activebackground="#bcffcf", cursor="hand2")
boton_buscar.grid(row=0, column=0, padx=12, pady=5)
boton_limpiar = tk.Button(frame_botones, image=botones_img['limpiar'], command=limpiar_busqueda, bd=0, bg="#d0f0c0", activebackground="#bcffcf", cursor="hand2")
boton_limpiar.grid(row=0, column=1, padx=12, pady=5)
boton_mostrar = tk.Button(frame_botones, image=botones_img['mostrar'], command=mostrar_todas, bd=0, bg="#d0f0c0", activebackground="#fff3c5", cursor="hand2")
boton_mostrar.grid(row=0, column=2, padx=12, pady=5)
boton_editar = tk.Button(frame_botones, image=botones_img['editar'], command=lambda: ventana_alimento("editar"), bd=0, bg="#d0f0c0", activebackground="#d2f7ff", cursor="hand2")
boton_editar.grid(row=0, column=3, padx=12, pady=5)
boton_eliminar = tk.Button(frame_botones, image=botones_img['eliminar'], command=eliminar_alimento, bd=0, bg="#d0f0c0", activebackground="#ffd6d6", cursor="hand2")
boton_eliminar.grid(row=0, column=4, padx=12, pady=5)

error_label = tk.Label(app, text="", bg="#f3f9f1", fg="red", font=("Arial", 11))
error_label.pack()

# Resultados
frame_resultados = tk.Frame(app, bg="#f3f9f1")
frame_resultados.pack(fill="both", expand=True, padx=8, pady=(5,0))
columnas = ("Nombre", "Tiempo", "Preparación")
resultados = ttk.Treeview(frame_resultados, columns=columnas, show="headings", height=8, selectmode="browse")
for col in columnas:
    resultados.heading(col, text=col)
    resultados.column(col, width=260 if col != "Preparación" else 360)
resultados.pack(fill="both", expand=True)
resultados.bind("<<TreeviewSelect>>", mostrar_detalle)

# Detalle de ingredientes y cantidades
frame_detalle = tk.Frame(app, bg="#e2f0d9", bd=0)
frame_detalle.pack(fill="x", padx=8, pady=6)
label_detalle = tk.Label(frame_detalle, text="Ingredientes y Cantidades", font=("Arial", 12, "bold"), bg="#e2f0d9")
label_detalle.pack(anchor="w", padx=5, pady=5)
detalle_text = tk.Text(frame_detalle, height=5, font=("Arial", 11), bg="white", state="disabled", wrap="word")
detalle_text.pack(fill="x", padx=5, pady=5)

# Paso a paso abajo (con borde negro)
frame_paso = tk.Frame(app, bg="#fff", highlightbackground="black", highlightthickness=2)
frame_paso.pack(fill="x", padx=20, pady=10)
paso_paso_text = tk.Text(frame_paso, height=3, font=("Arial", 13), bg="#fff", state="disabled", wrap="word")
paso_paso_text.pack(fill="both", padx=5, pady=5)
paso_paso_text.config(state="normal")
paso_paso_text.delete("1.0", tk.END)
paso_paso_text.insert(tk.END, "Paso a paso")
paso_paso_text.config(state="disabled")

crear_base_datos()
mostrar_todas()
app.mainloop()