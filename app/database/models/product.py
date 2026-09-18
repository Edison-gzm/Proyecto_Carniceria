from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database.base import Base


class UnitType(str, enum.Enum):
    KILO = "kg"
    LIBRA = "libra"
    UNIDAD = "unidad"
    GRAMO = "gramo"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    unit = Column(Enum(UnitType), nullable=False, default=UnitType.KILO)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Campo para auditoría de creación por usuario
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="products")
    sale_items = relationship("SaleItem", back_populates="product", passive_deletes=True)
    created_by = relationship("User", foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<Product(name='{self.name}', price={self.price})>"