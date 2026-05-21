# session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import DB_PATH

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)

def get_session():
    return SessionLocal()