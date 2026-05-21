from sqlalchemy import Column, Integer, DateTime, Numeric, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database.base import Base


class CashRegisterStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class CashRegister(Base):
    __tablename__ = "cash_registers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    status = Column(Enum(CashRegisterStatus), nullable=False, default=CashRegisterStatus.OPEN)

    opening_amount = Column(Numeric(14, 2), nullable=False, default=0)
    closing_amount = Column(Numeric(14, 2), nullable=True)
    total_sales = Column(Numeric(14, 2), nullable=False, default=0)
    difference = Column(Numeric(14, 2), nullable=True)

    notes = Column(Text, nullable=True)

    opened_at = Column(DateTime, server_default=func.now(), nullable=False)
    closed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="cash_registers")
    sales = relationship("Sale", back_populates="cash_register")

    def __repr__(self):
        return f"<CashRegister(id={self.id}, status='{self.status}', total_sales={self.total_sales})>"