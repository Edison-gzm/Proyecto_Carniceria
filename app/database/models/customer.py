from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.base import Base
 
 
class Customer(Base):
    __tablename__ = "customers"
 
    id = Column(Integer, primary_key=True, autoincrement=True)
    cedula_nit = Column(String(20), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
 
    sales = relationship("Sale", back_populates="customer")
 