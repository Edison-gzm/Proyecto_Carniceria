from pathlib import Path

APP_NAME = "Facturacion Carniceria Edison"
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "carniceria.db"
FACTURAS_DIR = DATA_DIR / "facturas"
REPORTES_DIR = DATA_DIR / "reportes"