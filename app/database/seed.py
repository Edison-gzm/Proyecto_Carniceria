import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import bcrypt
from database.session import init_db, get_session
from database.models import User, UserRole, Category, Customer


CATEGORIAS_DEFAULT = [
    {"name": "Carne de Vaca",  "description": "Cortes y piezas de res"},
    {"name": "Carne de Pollo", "description": "Pollo entero y sus partes"},
    {"name": "Carne de Cerdo", "description": "Cortes y piezas de cerdo"},
    {"name": "Embutidos",      "description": "Chorizos, salchichas, mortadela"},
    {"name": "Otros",          "description": "Productos adicionales"},
]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def seed():
    from config import DEFAULT_ADMIN_USER, DEFAULT_ADMIN_PASSWORD

    print("Inicializando base de datos...")
    init_db()
    print("Tablas creadas.")

    session = get_session()
    try:
        # Categorías
        if session.query(Category).count() == 0:
            for cat in CATEGORIAS_DEFAULT:
                session.add(Category(**cat))
            session.commit()
            print(f"{len(CATEGORIAS_DEFAULT)} categorías creadas.")
        else:
            print("Categorías ya existen, se omiten.")

        # Usuario admin
        if not session.query(User).filter_by(username=DEFAULT_ADMIN_USER).first():
            session.add(User(
                username=DEFAULT_ADMIN_USER,
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
                full_name="Administrador",
                role=UserRole.ADMIN,
            ))
            session.commit()
            print(f"Usuario '{DEFAULT_ADMIN_USER}' creado.")
        else:
            print(f"Usuario '{DEFAULT_ADMIN_USER}' ya existe, se omite.")

        # Cliente por defecto
        if not session.query(Customer).filter_by(id_number="0000").first():
            session.add(Customer(
                full_name="Consumidor Final",
                id_number="0000",
            ))
            session.commit()
            print("Cliente 'Consumidor Final' creado.")
        else:
            print("Cliente 'Consumidor Final' ya existe, se omite.")

        print("\nBase de datos lista.")

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()