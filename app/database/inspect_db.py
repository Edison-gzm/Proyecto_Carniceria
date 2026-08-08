import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect
from database.session import engine

inspector = inspect(engine)

print("=" * 50)
print("TABLAS DE LA BASE DE DATOS")
print("=" * 50)

for table in inspector.get_table_names():
    print(f"\n📋 Tabla: {table}")
    print("-" * 40)
    for column in inspector.get_columns(table):
        print(f"{column['name']:<20} {column['type']}")