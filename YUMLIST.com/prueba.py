import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
import sqlite3
import os
import logging
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import platform

# Configuración de logging para depuración
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='yumlist.log',
    filemode='w'
)
logger = logging.getLogger(__name__)

# Constantes y configuración
APP_NAME = "Yumlist - Gestor de Recetas Inteligente"
APP_VERSION = "2.0"
DB_NAME = "recetas.db"
DEFAULT_IMAGE_SIZE = (980, 700)
LOGO_SIZE = (100, 100)
BUTTON_SIZE = (140, 44)
FONT_TITLE = ("Arial", 24, "bold")
FONT_SUBTITLE = ("Arial", 12, "bold")
FONT_NORMAL = ("Arial", 11)
FONT_SMALL = ("Arial", 10)
COLORS = {
    "primary": "#4CAF50",
    "primary_dark": "#388E3C",
    "primary_light": "#C8E6C9",
    "accent": "#FFC107",
    "text": "#212121",
    "secondary_text": "#757575",
    "background": "#F5F5F5",
    "error": "#F44336",
    "warning": "#FF9800",
    "success": "#8BC34A",
    "info": "#2196F3"
}

@dataclass
class Recipe:
    id: int
    name: str
    ingredients: str
    quantities: str
    preparation: str
    cooking_time: str
    diets: str

class RecipeManager:
    """Clase para gestionar las operaciones con recetas en la base de datos"""
    
    INGREDIENT_RESTRICTIONS = {
        "Vegano": {"huevo", "huevos", "queso", "pollo", "carne", "leche", "miel", "mantequilla", "yogur"},
        "Vegetariano": {"pollo", "carne"},
        "Omnívoro": set()
    }
    
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self._initialize_db()
    
    def _initialize_db(self) -> None:
        """Inicializa la base de datos con la estructura necesaria"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Verificar si existe la columna 'dieta'
                cursor.execute("PRAGMA table_info(recetas)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'dieta' not in columns:
                    cursor.execute("ALTER TABLE recetas ADD COLUMN dieta TEXT DEFAULT 'Omnívoro'")
                
                # Crear tabla si no existe
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
                
                # Insertar datos de ejemplo si la tabla está vacía
                cursor.execute("SELECT COUNT(*) FROM recetas")
                if cursor.fetchone()[0] == 0:
                    self._insert_sample_data(cursor)
                
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Error al inicializar la base de datos: {e}")
            raise
    
    def _insert_sample_data(self, cursor: sqlite3.Cursor) -> None:
        """Inserta datos de ejemplo en la base de datos"""
        sample_recipes = [
            ("Tortilla de papa", "papa, huevo, cebolla, sal, aceite", 
             "3 papas, 3 huevos, 1 cebolla, sal, aceite", 
             "Freír papas y cebolla. Mezclar con huevo batido. Cocinar en sartén.", 
             "25 minutos", "Omnívoro"),
            ("Ensalada fresca", "lechuga, tomate, zanahoria, sal, aceite", 
             "4 hojas lechuga, 1 tomate, 1 zanahoria, 1 cdita sal, 1 cda aceite", 
             "Lavar y cortar los vegetales. Mezclar con aceite y sal.", 
             "10 minutos", "Vegano,Vegetariano,Omnívoro")
        ]
        cursor.executemany(
            "INSERT INTO recetas (nombre, ingredientes, cantidades, preparacion, tiempo_coccion, dieta) VALUES (?, ?, ?, ?, ?, ?)",
            sample_recipes
        )
    
    def get_all_recipes(self) -> List[Recipe]:
        """Obtiene todas las recetas de la base de datos"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM recetas")
                return [Recipe(*row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error al obtener todas las recetas: {e}")
            return []
    
    def search_recipes(self, ingredients: List[str], diet: str) -> List[Recipe]:
        """Busca recetas que contengan los ingredientes especificados y cumplan con la dieta"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM recetas")
                recipes = [Recipe(*row) for row in cursor.fetchall()]
                
                matching_recipes = []
                for recipe in recipes:
                    if not self._is_recipe_compatible(recipe, diet):
                        continue
                    
                    recipe_ingredients = {i.strip().lower() for i in recipe.ingredients.split(",")}
                    if all(ing.lower() in recipe_ingredients for ing in ingredients):
                        matching_recipes.append(recipe)
                
                return matching_recipes
        except sqlite3.Error as e:
            logger.error(f"Error al buscar recetas: {e}")
            return []
    
    def _is_recipe_compatible(self, recipe: Recipe, diet: str) -> bool:
        """Verifica si una receta es compatible con la dieta especificada"""
        if diet not in [d.strip() for d in recipe.diets.split(",")]:
            return False
            
        recipe_ingredients = {i.strip().lower() for i in recipe.ingredients.split(",")}
        prohibited = self.INGREDIENT_RESTRICTIONS.get(diet, set())
        return len(prohibited.intersection(recipe_ingredients)) == 0
    
    def add_recipe(self, recipe_data: Dict) -> bool:
        """Agrega una nueva receta a la base de datos"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO recetas (nombre, ingredientes, cantidades, preparacion, tiempo_coccion, dieta) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        recipe_data["name"],
                        recipe_data["ingredients"],
                        recipe_data["quantities"],
                        recipe_data["preparation"],
                        recipe_data["cooking_time"],
                        recipe_data["diets"]
                    )
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error al agregar receta: {e}")
            return False
    
    def update_recipe(self, recipe_id: int, recipe_data: Dict) -> bool:
        """Actualiza una receta existente"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE recetas SET nombre=?, ingredientes=?, cantidades=?, preparacion=?, tiempo_coccion=?, dieta=? WHERE id=?",
                    (
                        recipe_data["name"],
                        recipe_data["ingredients"],
                        recipe_data["quantities"],
                        recipe_data["preparation"],
                        recipe_data["cooking_time"],
                        recipe_data["diets"],
                        recipe_id
                    )
                )
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error al actualizar receta: {e}")
            return False
    
    def delete_recipe(self, recipe_id: int) -> bool:
        """Elimina una receta de la base de datos"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM recetas WHERE id=?", (recipe_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logger.error(f"Error al eliminar receta: {e}")
            return False

class ModernButton(tk.Button):
    """Clase para crear botones modernos con estilo consistente"""
    
    def __init__(self, master=None, **kwargs):
        # Configuración por defecto
        defaults = {
            "bg": COLORS["primary"],
            "fg": "white",
            "font": FONT_NORMAL,
            "bd": 0,
            "activebackground": COLORS["primary_dark"],
            "activeforeground": "white",
            "cursor": "hand2",
            "padx": 10,
            "pady": 5,
            "relief": "flat",
            "highlightthickness": 0
        }
        
        # Actualizar con los valores proporcionados
        defaults.update(kwargs)
        
        super().__init__(master, **defaults)
        
        # Efecto hover
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
    
    def _on_enter(self, event):
        self.config(bg=COLORS["primary_dark"])
    
    def _on_leave(self, event):
        self.config(bg=COLORS["primary"])

class RecipeApp:
    """Clase principal de la aplicación de gestión de recetas"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.recipe_manager = RecipeManager()
        self.current_diet = tk.StringVar(value="Omnívoro")
        self.selected_recipe_id = None
        
        self._setup_ui()
        self._load_images()
        self._show_all_recipes()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario principal"""
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("980x700")
        self.root.configure(bg=COLORS["background"])
        
        # Configurar el estilo de los widgets
        self._configure_styles()
        
        # Crear el diseño principal
        self._create_header()
        self._create_diet_selector()
        self._create_search_section()
        self._create_results_section()
        self._create_details_section()
        self._create_footer()
    
    def _configure_styles(self) -> None:
        """Configura los estilos para los widgets ttk"""
        style = ttk.Style()
        
        # Configurar tema
        if platform.system() == "Windows":
            style.theme_use("vista")
        else:
            style.theme_use("clam")
        
        # Configurar Treeview
        style.configure("Treeview", 
                       font=FONT_SMALL, 
                       rowheight=25, 
                       background="white", 
                       fieldbackground="white")
        style.configure("Treeview.Heading", 
                        font=FONT_SUBTITLE, 
                        background=COLORS["primary"], 
                        foreground="white",
                        relief="flat")
        style.map("Treeview.Heading", 
                  background=[("active", COLORS["primary_dark"])])
        
        # Configurar Notebook
        style.configure("TNotebook", background=COLORS["background"])
        style.configure("TNotebook.Tab", 
                       font=FONT_NORMAL, 
                       padding=[10, 5], 
                       background=COLORS["primary_light"],
                       foreground=COLORS["text"])
        style.map("TNotebook.Tab", 
                 background=[("selected", COLORS["primary"])],
                 foreground=[("selected", "white")])
    
    def _load_images(self) -> None:
        """Carga las imágenes utilizadas en la interfaz"""
        try:
            # Fondo principal
            bg_image_path = os.path.join("assets", "background.jpg")
            if os.path.exists(bg_image_path):
                img = Image.open(bg_image_path).resize(DEFAULT_IMAGE_SIZE)
                self.bg_img = ImageTk.PhotoImage(img)
                bg_label = tk.Label(self.root, image=self.bg_img)
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Logo
            logo_path = os.path.join("assets", "logo.png")
            if os.path.exists(logo_path):
                img_logo = Image.open(logo_path).resize(LOGO_SIZE)
                self.logo_img = ImageTk.PhotoImage(img_logo)
                self.logo_label.config(image=self.logo_img)
        except Exception as e:
            logger.error(f"Error al cargar imágenes: {e}")
    
    def _create_header(self) -> None:
        """Crea la sección del encabezado con el logo y título"""
        self.header_frame = tk.Frame(self.root, bg=COLORS["background"])
        self.header_frame.pack(pady=10)
        
        # Logo
        self.logo_label = tk.Label(self.header_frame, text=APP_NAME, font=FONT_TITLE, bg=COLORS["background"])
        self.logo_label.pack()
        
        # Versión
        version_label = tk.Label(self.header_frame, text=f"v{APP_VERSION}", font=("Arial", 10), 
                               bg=COLORS["background"], fg=COLORS["secondary_text"])
        version_label.pack()
    
    def _create_diet_selector(self) -> None:
        """Crea el selector de tipo de dieta"""
        self.diet_frame = tk.Frame(self.root, bg=COLORS["primary_light"])
        self.diet_frame.pack(fill="x", padx=8, pady=(0, 8))
        
        tk.Label(self.diet_frame, text="Selecciona tu tipo de dieta:", 
                font=FONT_SUBTITLE, bg=COLORS["primary_light"]).pack(side="left", padx=(10, 5), pady=5)
        
        # Botones de selección de dieta
        diets = ["Omnívoro", "Vegetariano", "Vegano"]
        for diet in diets:
            btn = tk.Radiobutton(
                self.diet_frame, 
                text=diet, 
                variable=self.current_diet, 
                value=diet,
                command=self._show_all_recipes,
                font=FONT_NORMAL,
                bg="white",
                activebackground=COLORS["primary_light"],
                selectcolor=COLORS["primary_light"],
                indicatoron=0,
                relief="solid",
                bd=1,
                padx=10,
                pady=3
            )
            btn.pack(side="left", padx=4)
    
    def _create_search_section(self) -> None:
        """Crea la sección de búsqueda de recetas"""
        self.search_frame = tk.Frame(self.root, bg=COLORS["primary_light"], bd=0)
        self.search_frame.pack(fill="x", padx=8, pady=2)
        
        # Etiqueta y entrada de ingredientes
        tk.Label(self.search_frame, text="Ingredientes disponibles (separados por coma):", 
                font=FONT_NORMAL, bg=COLORS["primary_light"]).grid(row=0, column=0, columnspan=5, pady=3, sticky="w")
        
        self.ingredients_entry = tk.Entry(self.search_frame, width=52, font=FONT_NORMAL)
        self.ingredients_entry.grid(row=1, column=0, columnspan=5, padx=3, pady=5, sticky="w")
        
        # Frame para botones de acción
        self.button_frame = tk.Frame(self.search_frame, bg=COLORS["primary_light"])
        self.button_frame.grid(row=2, column=0, columnspan=5, pady=10)
        
        # Botones de acción
        self.search_btn = ModernButton(
            self.button_frame, 
            text="🔍 Buscar Recetas", 
            command=self._search_recipes
        )
        self.search_btn.grid(row=0, column=0, padx=12, pady=5)
        
        self.clear_btn = ModernButton(
            self.button_frame, 
            text="Limpiar", 
            command=self._clear_search,
            bg=COLORS["info"]
        )
        self.clear_btn.grid(row=0, column=1, padx=12, pady=5)
        
        self.show_all_btn = ModernButton(
            self.button_frame, 
            text="Mostrar Todas", 
            command=self._show_all_recipes,
            bg=COLORS["accent"],
            fg=COLORS["text"]
        )
        self.show_all_btn.grid(row=0, column=2, padx=12, pady=5)
        
        self.add_btn = ModernButton(
            self.button_frame, 
            text="➕ Agregar", 
            command=self._open_add_recipe_dialog,
            bg=COLORS["success"]
        )
        self.add_btn.grid(row=0, column=3, padx=12, pady=5)
        
        # Etiqueta para mensajes de error
        self.error_label = tk.Label(
            self.root, 
            text="", 
            bg=COLORS["background"], 
            fg=COLORS["error"], 
            font=FONT_NORMAL
        )
        self.error_label.pack()
    
    def _create_results_section(self) -> None:
        """Crea la sección de resultados de recetas"""
        self.results_frame = tk.Frame(self.root, bg=COLORS["background"])
        self.results_frame.pack(fill="both", expand=True, padx=8, pady=(5, 0))
        
        # Treeview para mostrar las recetas
        columns = ("Nombre", "Tiempo", "Ingredientes")
        self.results_tree = ttk.Treeview(
            self.results_frame, 
            columns=columns, 
            show="headings", 
            height=8, 
            selectmode="browse"
        )
        
        # Configurar columnas
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=260 if col != "Ingredientes" else 360)
        
        self.results_tree.pack(fill="both", expand=True)
        self.results_tree.bind("<<TreeviewSelect>>", self._show_recipe_details)
        
        # Barra de desplazamiento
        scrollbar = ttk.Scrollbar(self.results_tree, orient="vertical", command=self.results_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.results_tree.configure(yscrollcommand=scrollbar.set)
    
    def _create_details_section(self) -> None:
        """Crea la sección de detalles de la receta seleccionada"""
        # Notebook para pestañas de detalles
        self.details_notebook = ttk.Notebook(self.root)
        self.details_notebook.pack(fill="x", padx=8, pady=6)
        
        # Pestaña de ingredientes
        self.ingredients_tab = tk.Frame(self.details_notebook, bg=COLORS["background"])
        self.details_notebook.add(self.ingredients_tab, text="Ingredientes")
        
        tk.Label(self.ingredients_tab, text="Ingredientes y Cantidades", 
                font=FONT_SUBTITLE, bg=COLORS["background"]).pack(anchor="w", padx=5, pady=5)
        
        self.ingredients_text = scrolledtext.ScrolledText(
            self.ingredients_tab, 
            height=5, 
            font=FONT_NORMAL, 
            bg="white", 
            wrap="word",
            state="disabled"
        )
        self.ingredients_text.pack(fill="x", padx=5, pady=5)
        
        # Pestaña de preparación
        self.preparation_tab = tk.Frame(self.details_notebook, bg=COLORS["background"])
        self.details_notebook.add(self.preparation_tab, text="Preparación")
        
        tk.Label(self.preparation_tab, text="Instrucciones de Preparación", 
                font=FONT_SUBTITLE, bg=COLORS["background"]).pack(anchor="w", padx=5, pady=5)
        
        self.preparation_text = scrolledtext.ScrolledText(
            self.preparation_tab, 
            height=5, 
            font=FONT_NORMAL, 
            bg="white", 
            wrap="word",
            state="disabled"
        )
        self.preparation_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Frame para botones de edición/eliminación
        self.edit_frame = tk.Frame(self.root, bg=COLORS["background"])
        self.edit_frame.pack(fill="x", padx=8, pady=5)
        
        self.edit_btn = ModernButton(
            self.edit_frame, 
            text="✏️ Editar", 
            command=self._open_edit_recipe_dialog,
            bg=COLORS["info"]
        )
        self.edit_btn.pack(side="left", padx=5)
        
        self.delete_btn = ModernButton(
            self.edit_frame, 
            text="🗑️ Eliminar", 
            command=self._delete_recipe,
            bg=COLORS["error"]
        )
        self.delete_btn.pack(side="left", padx=5)
    
    def _create_footer(self) -> None:
        """Crea el pie de página"""
        self.footer_frame = tk.Frame(self.root, bg=COLORS["primary"], height=30)
        self.footer_frame.pack(fill="x", side="bottom")
        
        tk.Label(
            self.footer_frame, 
            text=f"© 2023 {APP_NAME} | v{APP_VERSION}", 
            bg=COLORS["primary"], 
            fg="white",
            font=("Arial", 9)
        ).pack(pady=5)
    
    def _search_recipes(self) -> None:
        """Busca recetas basadas en los ingredientes ingresados"""
        ingredients_input = self.ingredients_entry.get().lower()
        self.results_tree.delete(*self.results_tree.get_children())
        self._clear_recipe_details()
        self.error_label.config(text="", fg=COLORS["error"])
        
        if not ingredients_input.strip():
            self.error_label.config(text="Ingresa al menos un ingrediente.")
            return
        
        ingredients_list = [i.strip() for i in ingredients_input.split(",") if i.strip()]
        if not ingredients_list:
            self.error_label.config(text="Debes ingresar ingredientes separados por comas.")
            return
        
        diet = self.current_diet.get()
        matching_recipes = self.recipe_manager.search_recipes(ingredients_list, diet)
        
        if not matching_recipes:
            self.error_label.config(text="No se encontraron recetas con esos ingredientes para la dieta seleccionada.")
            return
        
        for recipe in matching_recipes:
            self.results_tree.insert(
                "", 
                "end", 
                iid=recipe.id, 
                values=(recipe.name, recipe.cooking_time, recipe.quantities)
            )
    
    def _show_all_recipes(self) -> None:
        """Muestra todas las recetas compatibles con la dieta seleccionada"""
        self.results_tree.delete(*self.results_tree.get_children())
        self._clear_recipe_details()
        self.error_label.config(text="", fg=COLORS["error"])
        
        diet = self.current_diet.get()
        all_recipes = self.recipe_manager.get_all_recipes()
        
        for recipe in all_recipes:
            if self.recipe_manager._is_recipe_compatible(recipe, diet):
                self.results_tree.insert(
                    "", 
                    "end", 
                    iid=recipe.id, 
                    values=(recipe.name, recipe.cooking_time, recipe.quantities)
                )
    
    def _show_recipe_details(self, event) -> None:
        """Muestra los detalles de la receta seleccionada"""
        selected_item = self.results_tree.focus()
        if not selected_item:
            return
        
        self.selected_recipe_id = int(selected_item)
        recipe = self._get_recipe_by_id(self.selected_recipe_id)
        
        if not recipe:
            return
        
        # Mostrar ingredientes y cantidades
        self.ingredients_text.config(state="normal")
        self.ingredients_text.delete("1.0", tk.END)
        self.ingredients_text.insert(tk.END, f"Ingredientes:\n{recipe.ingredients}\n\nCantidades:\n{recipe.quantities}")
        self.ingredients_text.config(state="disabled")
        
        # Mostrar preparación
        self.preparation_text.config(state="normal")
        self.preparation_text.delete("1.0", tk.END)
        self.preparation_text.insert(tk.END, recipe.preparation)
        self.preparation_text.config(state="disabled")
    
    def _clear_recipe_details(self) -> None:
        """Limpia los detalles de la receta mostrados"""
        self.ingredients_text.config(state="normal")
        self.ingredients_text.delete("1.0", tk.END)
        self.ingredients_text.config(state="disabled")
        
        self.preparation_text.config(state="normal")
        self.preparation_text.delete("1.0", tk.END)
        self.preparation_text.config(state="disabled")
        
        self.selected_recipe_id = None
    
    def _clear_search(self) -> None:
        """Limpia la búsqueda actual"""
        self.ingredients_entry.delete(0, tk.END)
        self._clear_recipe_details()
        self.results_tree.delete(*self.results_tree.get_children())
        self.error_label.config(text="")
    
    def _get_recipe_by_id(self, recipe_id: int) -> Optional[Recipe]:
        """Obtiene una receta por su ID"""
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM recetas WHERE id=?", (recipe_id,))
                row = cursor.fetchone()
                return Recipe(*row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Error al obtener receta por ID: {e}")
            return None
    
    def _open_add_recipe_dialog(self) -> None:
        """Abre el diálogo para agregar una nueva receta"""
        self._recipe_dialog("Agregar Receta")
    
    def _open_edit_recipe_dialog(self) -> None:
        """Abre el diálogo para editar una receta existente"""
        if not self.selected_recipe_id:
            messagebox.showerror("Error", "Selecciona una receta para editar.")
            return
        
        recipe = self._get_recipe_by_id(self.selected_recipe_id)
        if not recipe:
            messagebox.showerror("Error", "No se pudo obtener la receta seleccionada.")
            return
        
        self._recipe_dialog("Editar Receta", recipe)
    
    def _recipe_dialog(self, title: str, recipe: Optional[Recipe] = None) -> None:
        """Crea un diálogo para agregar/editar recetas"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.grab_set()
        dialog.geometry("500x600")
        dialog.resizable(False, False)
        dialog.configure(bg=COLORS["background"])
        
        # Variables para los checkboxes de dieta
        var_omni = tk.IntVar(value=1 if not recipe or "Omnívoro" in recipe.diets else 0)
        var_vege = tk.IntVar(value=1 if recipe and "Vegetariano" in recipe.diets else 0)
        var_vegan = tk.IntVar(value=1 if recipe and "Vegano" in recipe.diets else 0)
        
        # Función para guardar la receta
        def save_recipe():
            name = entry_name.get().strip()
            ingredients = entry_ingredients.get("1.0", tk.END).strip()
            quantities = entry_quantities.get("1.0", tk.END).strip()
            preparation = entry_preparation.get("1.0", tk.END).strip()
            cooking_time = entry_time.get().strip()
            
            diets = []
            if var_omni.get(): diets.append("Omnívoro")
            if var_vege.get(): diets.append("Vegetariano")
            if var_vegan.get(): diets.append("Vegano")
            
            if not name or not ingredients or not quantities or not preparation or not cooking_time or not diets:
                messagebox.showerror("Error", "Todos los campos y al menos una dieta son requeridos.")
                return
            
            recipe_data = {
                "name": name,
                "ingredients": ingredients,
                "quantities": quantities,
                "preparation": preparation,
                "cooking_time": cooking_time,
                "diets": ",".join(diets)
            }
            
            success = False
            if recipe:
                success = self.recipe_manager.update_recipe(recipe.id, recipe_data)
            else:
                success = self.recipe_manager.add_recipe(recipe_data)
            
            if success:
                messagebox.showinfo("Éxito", "Receta guardada correctamente.")
                dialog.destroy()
                self._show_all_recipes()
            else:
                messagebox.showerror("Error", "No se pudo guardar la receta.")
        
        # Campos del formulario
        tk.Label(dialog, text="Nombre:", bg=COLORS["background"], font=FONT_NORMAL).pack(anchor="w", padx=10, pady=(10, 0))
        entry_name = tk.Entry(dialog, width=60, font=FONT_NORMAL)
        entry_name.pack(padx=10)
        if recipe:
            entry_name.insert(0, recipe.name)
        
        tk.Label(dialog, text="Ingredientes (uno por línea):", bg=COLORS["background"], font=FONT_NORMAL).pack(anchor="w", padx=10, pady=(10, 0))
        entry_ingredients = scrolledtext.ScrolledText(dialog, width=60, height=4, font=FONT_NORMAL)
        entry_ingredients.pack(padx=10)
        if recipe:
            entry_ingredients.insert("1.0", recipe.ingredients)
        
        tk.Label(dialog, text="Cantidades (una por línea):", bg=COLORS["background"], font=FONT_NORMAL).pack(anchor="w", padx=10, pady=(10, 0))
        entry_quantities = scrolledtext.ScrolledText(dialog, width=60, height=4, font=FONT_NORMAL)
        entry_quantities.pack(padx=10)
        if recipe:
            entry_quantities.insert("1.0", recipe.quantities)
        
        tk.Label(dialog, text="Preparación:", bg=COLORS["background"], font=FONT_NORMAL).pack(anchor="w", padx=10, pady=(10, 0))
        entry_preparation = scrolledtext.ScrolledText(dialog, width=60, height=6, font=FONT_NORMAL)
        entry_preparation.pack(padx=10)
        if recipe:
            entry_preparation.insert("1.0", recipe.preparation)
        
        tk.Label(dialog, text="Tiempo de cocción:", bg=COLORS["background"], font=FONT_NORMAL).pack(anchor="w", padx=10, pady=(10, 0))
        entry_time = tk.Entry(dialog, width=60, font=FONT_NORMAL)
        entry_time.pack(padx=10)
        if recipe:
            entry_time.insert(0, recipe.cooking_time)
        
        # Checkboxes para dietas
        tk.Label(dialog, text="Dietas compatibles:", bg=COLORS["background"], font=FONT_NORMAL).pack(anchor="w", padx=10, pady=(10, 0))
        
        frame_diets = tk.Frame(dialog, bg=COLORS["background"])
        frame_diets.pack(anchor="w", padx=20, pady=5)
        
        chk_omni = tk.Checkbutton(
            frame_diets, 
            text="Omnívoro", 
            variable=var_omni, 
            bg=COLORS["background"],
            font=FONT_NORMAL
        )
        chk_omni.pack(anchor="w")
        
        chk_vege = tk.Checkbutton(
            frame_diets, 
            text="Vegetariano", 
            variable=var_vege, 
            bg=COLORS["background"],
            font=FONT_NORMAL
        )
        chk_vege.pack(anchor="w")
        
        chk_vegan = tk.Checkbutton(
            frame_diets, 
            text="Vegano", 
            variable=var_vegan, 
            bg=COLORS["background"],
            font=FONT_NORMAL
        )
        chk_vegan.pack(anchor="w")
        
        # Botón de guardar
        btn_save = ModernButton(
            dialog, 
            text="💾 Guardar", 
            command=save_recipe,
            bg=COLORS["success"]
        )
        btn_save.pack(pady=10)
    
    def _delete_recipe(self) -> None:
        """Elimina la receta seleccionada"""
        if not self.selected_recipe_id:
            messagebox.showerror("Error", "Selecciona una receta para eliminar.")
            return
        
        recipe_name = self.results_tree.item(self.selected_recipe_id, "values")[0]
        if not messagebox.askyesno("Confirmar", f"¿Seguro que deseas eliminar '{recipe_name}'?"):
            return
        
        if self.recipe_manager.delete_recipe(self.selected_recipe_id):
            messagebox.showinfo("Éxito", "Receta eliminada correctamente.")
            self._show_all_recipes()
        else:
            messagebox.showerror("Error", "No se pudo eliminar la receta.")

def main():
    """Función principal para iniciar la aplicación"""
    root = tk.Tk()
    app = RecipeApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()