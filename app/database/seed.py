import sys
from pathlib import Path

# Permitir importaciones desde la raíz del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.session import get_session
from services.product_service import ProductService, CategoryService
from database.models.product import UnitType

PRODUCTS_DATA = {
    "Carne de Vaca": [
        ("Lomo Fino de Res", "Corte magro y suave ideal para asar o sartén", 42000),
        ("Punta de Anca", "Corte con capa de grasa jugosa para parrilla", 38000),
        ("Chatas / Lomo Ancho", "Corte tradicional muy sabroso para asar", 36000),
        ("Bife Ancho / Ojo de Bife", "Corte marmoleado de alta calidad", 35000),
        ("Colita de Cuadril", "Corte magro y versátil para hornear o asar", 32000),
        ("Cadera", "Carne blanda para frite, asado o platanito", 30000),
        ("Bola de Pierna", "Ideal para milanesas y sudados", 28000),
        ("Muchacho", "Corte magro ideal para rellenar o sudar", 28000),
        ("Tabla de Res", "Carne magra para bistec y fritos", 28000),
        ("Sobrebarriga", "Excelente para sudar, hornear o dorar", 26000),
        ("Carne Molida Especial", "100% magra sin gordura agregada", 26000),
        ("Murillo", "Corte con colágeno perfecto para caldos y sudados", 24000),
        ("Costilla de Res", "Ideal para sancochos y sopas", 22000),
        ("Pecho de Res", "Excelente sabor para caldos y sudados", 22000),
        ("Carne Molida Corriente", "Mezcla tradicional para guisos y rellenos", 20000),
    ],
    "Carne de Cerdo": [
        ("Solomito de Cerdo", "Corte muy tierno y magro", 26000),
        ("Bondiola de Cerdo", "Jugosa y marmoleada para asar", 25000),
        ("Costilla de Cerdo", "Perfecta para BBQ, horno o sartén", 24000),
        ("Cañón de Cerdo", "Lomo limpio bajo en grasa", 23000),
        ("Lomo de Cerdo", "Corte clásico para chuletas o asar", 22000),
        ("Tocino Barriguero", "Ideal para chicharrón crocante", 22000),
        ("Chuleta de Cerdo", "Corte con hueso lleno de sabor", 21000),
        ("Cabeza de Lomo", "Carne suave para guisos y asados", 21000),
        ("Chicharrón Cojín", "Tocino carnudo seleccionado", 20000),
        ("Pierna de Cerdo", "Ideal para hornear o desmechar", 19000),
        ("Brazo de Cerdo", "Excelente para sudados y tamales", 18000),
        ("Lagarto de Cerdo", "Corte magro para trocear", 18000),
        ("Carne Molida de Cerdo", "Ideal para albóndigas y hamburguesas", 18000),
        ("Ossobuco de Cerdo", "Corte con hueso para estofados", 17000),
        ("Hueso de Sancocho", "Para dar gran sabor a sopas y frijoles", 10000),
    ],
    "Pollo": [
        ("Pollo Desmechado", "Pechuga cocida y desmechada", 20000),
        ("Pechuga Deshuesada", "Filete limpio sin piel ni hueso", 18000),
        ("Filete de Muslo", "Deshuesado jugoso para plancha", 16000),
        ("Pechuga con Hueso", "Pechuga entera con hueso", 15000),
        ("Alas de Pollo", "Perfectas para freír o BBQ", 14000),
        ("Colombinas de Pollo", "Muslitos de ala seleccionados", 13000),
        ("Pollo Entero Racionado", "Pollo fresco picado en presas", 12500),
        ("Contramuslos", "Presas jugosas con hueso", 12000),
        ("Muslos de Pollo", "Presas tradicionales para sudar", 11000),
        ("Pernil de Pollo Completo", "Muslo y contramuslo unido", 11500),
        ("Mollejas de Pollo", "Límpias y listas para guisar", 8000),
        ("Hígados de Pollo", "Frescos para saltear o paté", 7000),
        ("Patas de Pollo", "Ideal para enriquecer caldos", 6000),
        ("Menudencias de Pollo", "Surtido para sopa de menudencias", 6000),
        ("Huacal / Rabadilla", "Para bases de sopas y consomé", 5000),
    ],
    "Embutidos": [
        ("Tocineta Ahumada", "Laminada con proceso ahumado natural", 38000),
        ("Salame / Genoa", "Madurado de alta calidad", 35000),
        ("Jamón de Pavo", "Bajo en grasa y bajo en sodio", 30000),
        ("Salchicha Ranchera", "Sabor ahumado tradicional", 28000),
        ("Chorizo de Ternera", "Artesanal bajo en grasa", 28000),
        ("Chorizo Santarrosano", "Chorizo tradicional picado a cuchillo", 26000),
        ("Jamón Especial de Cerdo", "Tajado tipo premium", 25000),
        ("Chorizo Antioqueño", "Sabor casero para asador", 24000),
        ("Salchicha Suiza", "Tamaño grande ideal para asar", 24000),
        ("Longaniza", "Embutido aliñado para asar", 22000),
        ("Butifarra", "Especialidad costeña aliñada", 20000),
        ("Salchichón Cervecero", "Tajado tradicional", 18000),
        ("Queso de Cabeza", "Preparación artesanal de cerdo", 18000),
        ("Morcilla / Rellena", "Con arroz y poleo lista para freír", 16000),
        ("Salchicha Manguera", "Para perros calientes y guisos", 15000),
    ]
}


def run_seed():
    session = get_session()
    cat_service = CategoryService(session)
    prod_service = ProductService(session)

    print("🚀 Iniciando carga de datos...")

    try:
        # 1. Obtener o crear categorías
        existing_categories = {c.name: c.id for c in cat_service.get_all()}
        category_map = {}

        for cat_name in PRODUCTS_DATA.keys():
            if cat_name in existing_categories:
                category_map[cat_name] = existing_categories[cat_name]
            else:
                new_cat = cat_service.create(name=cat_name)
                category_map[cat_name] = new_cat.id
                print(f"  [+] Categoría creada: {cat_name}")

        # 2. Insertar productos
        existing_products = {p.name.lower() for p in prod_service.get_all(only_active=False)}
        created_count = 0

        for cat_name, products in PRODUCTS_DATA.items():
            cat_id = category_map[cat_name]

            for name, description, price in products:
                if name.lower() not in existing_products:
                    prod_service.create(
                        name=name,
                        description=description,
                        price=float(price),
                        category_id=cat_id,
                        unit=UnitType.KILO
                    )
                    created_count += 1

        session.commit()
        print(f"✅ ¡ÉXITO! Se guardaron {created_count} productos en la base de datos.")

    except Exception as e:
        session.rollback()
        print(f"❌ Error al guardar datos: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    run_seed()