from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from database.models.sale import Sale, SaleStatus
from database.models.sale_item import SaleItem
from database.models.product import Product
 
 
class SaleService:
    def __init__(self, session: Session):
        self.session = session
 
    def create_sale(self, user_id: int, customer_id: int,
                    items: list[dict], cash_register_id: int | None = None) -> Sale:
        """
        items: [{"product_id": 1, "quantity": 2.5}, ...]
        """
        sale = Sale(
            user_id=user_id,
            customer_id=customer_id,
            cash_register_id=cash_register_id,
            status=SaleStatus.OPEN,
        )
        self.session.add(sale)
        self.session.flush()  # para obtener sale.id
 
        subtotal = Decimal("0")
        for item in items:
            product = self.session.get(Product, item["product_id"])
            if not product or not product.is_active:
                raise ValueError(f"Producto {item['product_id']} no disponible")
            qty = Decimal(str(item["quantity"]))
            unit_price = Decimal(str(product.price))
            item_subtotal = qty * unit_price
            subtotal += item_subtotal
 
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                product_name=product.name,
                unit=product.unit.value,
                unit_price=unit_price,
                quantity=qty,
                subtotal=item_subtotal,
            )
            self.session.add(sale_item)
 
        sale.subtotal = subtotal
        sale.tax = Decimal("0")
        sale.total = subtotal
        sale.status = SaleStatus.CLOSED
        sale.closed_at = datetime.now()
        sale.invoice_number = self._generate_invoice_number()
 
        self.session.commit()
        return sale
 
    def _generate_invoice_number(self) -> str:
        last = (
            self.session.query(Sale)
            .filter(Sale.invoice_number.isnot(None))
            .order_by(Sale.id.desc())
            .first()
        )
        if last and last.invoice_number:
            try:
                num = int(last.invoice_number.split("-")[-1]) + 1
            except ValueError:
                num = 1
        else:
            num = 1
        return f"FAC-{num:06d}"
 
    def cancel_sale(self, sale_id: int) -> bool:
        sale = self.session.get(Sale, sale_id)
        if not sale or sale.status == SaleStatus.CANCELLED:
            return False
        sale.status = SaleStatus.CANCELLED
        self.session.commit()
        return True
 
    def get_by_date(self, date_from: datetime, date_to: datetime) -> list[Sale]:
        return (
            self.session.query(Sale)
            .filter(Sale.created_at >= date_from, Sale.created_at <= date_to)
            .filter(Sale.status != SaleStatus.CANCELLED)
            .order_by(Sale.created_at.desc())
            .all()
        )
 
    def get_today(self) -> list[Sale]:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.get_by_date(today, datetime.now())
 
    def get_by_id(self, sale_id: int) -> Sale | None:
        return self.session.get(Sale, sale_id)