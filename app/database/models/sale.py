from sqlalchemy import Column, Integer, Numeric, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base
 
 
class Sale(Base):
    __tablename__ = "sales"
 
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    total = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default="completed")  # completed | cancelled
    created_at = Column(DateTime, default=datetime.now)
 
    user = relationship("User", back_populates="sales")
    customer = relationship("Customer", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale")
 