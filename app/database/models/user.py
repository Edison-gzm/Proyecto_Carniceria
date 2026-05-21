from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database.base import Base
 
 
class User(Base):
    __tablename__ = "users"
 
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="cajero")  # admin | cajero
    is_active = Column(Boolean, default=True)
 
    sales = relationship("Sale", back_populates="user")
    cash_registers = relationship("CashRegister", back_populates="user")