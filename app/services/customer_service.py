from sqlalchemy.orm import Session
from database.models.customer import Customer
 
 
class CustomerService:
    def __init__(self, session: Session):
        self.session = session
 
    def get_all(self, only_active: bool = True) -> list[Customer]:
        q = self.session.query(Customer)
        if only_active:
            q = q.filter_by(is_active=True)
        return q.order_by(Customer.full_name).all()
 
    def get_by_id(self, customer_id: int) -> Customer | None:
        return self.session.get(Customer, customer_id)
 
    def get_by_id_number(self, id_number: str) -> Customer | None:
        return self.session.query(Customer).filter_by(id_number=id_number).first()
 
    def search(self, query: str) -> list[Customer]:
        return (
            self.session.query(Customer)
            .filter(
                Customer.is_active == True,
                (Customer.full_name.ilike(f"%{query}%")) |
                (Customer.id_number.ilike(f"%{query}%"))
            )
            .order_by(Customer.full_name)
            .all()
        )
 
    def create(self, full_name: str, id_number: str = "",
               phone: str = "", email: str = "", address: str = "", created_by_id: int | None = None) -> Customer:
        customer = Customer(
            full_name=full_name, id_number=id_number,
            phone=phone, email=email, address=address, created_by_id=created_by_id
        )
        self.session.add(customer)
        self.session.commit()
        return customer
 
    def update(self, customer_id: int, **kwargs) -> Customer | None:
        customer = self.session.get(Customer, customer_id)
        if not customer:
            return None
        for key, value in kwargs.items():
            setattr(customer, key, value)
        self.session.commit()
        return customer
 
    def toggle_active(self, customer_id: int) -> bool:
        customer = self.session.get(Customer, customer_id)
        if not customer:
            return False
        customer.is_active = not customer.is_active
        self.session.commit()
        return customer.is_active
 