from app.config import DATA_DIR, FACTURAS_DIR, REPORTES_DIR
from app.database.session import engine
from app.database.base import Base
import app.database.models  #

def init_app():
    # 
    for folder in [DATA_DIR, FACTURAS_DIR, REPORTES_DIR]:
        folder.mkdir(parents=True, exist_ok=True)
    # Crear tablas
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    init_app()
    # 