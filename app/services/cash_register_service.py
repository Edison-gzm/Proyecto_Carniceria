from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from database.models.cash_register import CashRegister, CashRegisterStatus
from database.models.sale import Sale, SaleStatus
 
 
class CashRegisterService:
    def __init__(self, session: Session):
        self.session = session
 
    def get_open(self) -> CashRegister | None:
        return self.session.query(CashRegister).filter_by(status=CashRegisterStatus.OPEN).first()
 
    def open_register(self, user_id: int, opening_amount: float = 0) -> CashRegister:
        if self.get_open():
            raise ValueError("Ya hay una caja abierta")
        register = CashRegister(
            user_id=user_id,
            opening_amount=Decimal(str(opening_amount)),
            status=CashRegisterStatus.OPEN,
        )
        self.session.add(register)
        self.session.commit()
        return register
 
    def close_register(self, register_id: int, closing_amount: float, notes: str = "") -> CashRegister:
        register = self.session.get(CashRegister, register_id)
        if not register or register.status != CashRegisterStatus.OPEN:
            raise ValueError("Caja no encontrada o ya cerrada")
 
        # Calcular total de ventas de esta caja
        sales_total = self.session.query(Sale).filter(
            Sale.cash_register_id == register_id,
            Sale.status == SaleStatus.CLOSED
        ).all()
        total_sales = sum(s.total for s in sales_total)
 
        closing = Decimal(str(closing_amount))
        register.closing_amount = closing
        register.total_sales = Decimal(str(total_sales))
        register.difference = closing - (register.opening_amount + Decimal(str(total_sales)))
        register.status = CashRegisterStatus.CLOSED
        register.closed_at = datetime.now()
        register.notes = notes
 
        self.session.commit()
        return register
 
    def get_history(self, limit: int = 30) -> list[CashRegister]:
        return (
            self.session.query(CashRegister)
            .order_by(CashRegister.opened_at.desc())
            .limit(limit)
            .all()
        )