from sqlalchemy import Column, Integer, DateTime, Numeric, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.base import Base


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # Copia del producto al momento de la venta — no cambia aunque edites el producto
    product_name = Column(String(150), nullable=False)
    unit = Column(String(20), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)

    quantity = Column(Numeric(10, 3), nullable=False)
    subtotal = Column(Numeric(14, 2), nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")

    def __repr__(self):
        return f"<SaleItem(product='{self.product_name}', qty={self.quantity}, subtotal={self.subtotal})>"