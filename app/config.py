from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()
#This file is to configute

# Rutas base
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "carniceria.db"
INVOICES_DIR = DATA_DIR / "facturas"
REPORTS_DIR = DATA_DIR / "reportes"
LOGS_DIR = DATA_DIR / "logs"

# Crear directorios automáticamente si no existen
DATA_DIR.mkdir(exist_ok=True)
INVOICES_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# App
APP_NAME = "Sistema de Facturación — Carnicería"
APP_VERSION = "1.0.0"

# Base de datos
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Seguridad
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-cambiar-en-produccion")
DEFAULT_ADMIN_USER = os.getenv("DEFAULT_ADMIN_USER", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

# UI y Tema de Colores
COLORS = {
    'surface': '#FFFFFF',
    'surface_light': '#F8FAFC',
    'border': '#E2E8F0',
    'primary': '#2563EB',
    'success': '#16A34A',
    'danger': '#DC2626',
    'text_primary': '#0F172A'
}

# Imágenes y Categorías
IMAGES_DIR = BASE_DIR / "assets" / "images"
CATEGORY_IMAGES = {
    "Carne de Vaca": str(IMAGES_DIR / "vaca.jpg"),
    "Carne de Cerdo": str(IMAGES_DIR / "cerdo.jpg"),
    "Pollo": str(IMAGES_DIR / "pollo.jpg"),
    "Embutidos": str(IMAGES_DIR / "embutidos.jpg"),
}
