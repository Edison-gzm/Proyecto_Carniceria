from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base
 
 
class Product(Base):
    __tablename__ = "products"
 
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    is_active = Column(Boolean, default=True)
 
    category = relationship("Category", back_populates="products")
    sale_items = relationship("SaleItem", back_populates="product")
 