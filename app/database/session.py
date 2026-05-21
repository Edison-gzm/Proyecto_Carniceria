from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from config import DATABASE_URL
from database.base import Base

### Ala idea es administrar todo lo relacionado de sql alchemy y sqlite en este archivo

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_session() -> Session:
    return SessionLocal()


def init_db():
    from database.models import user, category, product, customer, sale, sale_item, cash_register  # noqa
    Base.metadata.create_all(bind=engine)