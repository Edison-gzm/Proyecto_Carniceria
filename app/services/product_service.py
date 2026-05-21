from sqlalchemy.orm import Session
from database.models.product import Product, UnitType
from database.models.category import Category
 
 
class ProductService:
    def __init__(self, session: Session):
        self.session = session
 
    def get_all(self, only_active: bool = True) -> list[Product]:
        q = self.session.query(Product)
        if only_active:
            q = q.filter_by(is_active=True)
        return q.order_by(Product.name).all()
 
    def search(self, query: str) -> list[Product]:
        return (
            self.session.query(Product)
            .filter(Product.name.ilike(f"%{query}%"), Product.is_active == True)
            .order_by(Product.name)
            .all()
        )
 
    def get_by_id(self, product_id: int) -> Product | None:
        return self.session.get(Product, product_id)
 
    def create(self, name: str, price: float, category_id: int,
                unit: UnitType = UnitType.KILO, description: str = "") -> Product:
        product = Product(name=name, price=price, category_id=category_id,
                          unit=unit, description=description)
        self.session.add(product)
        self.session.commit()
        return product
 
    def update(self, product_id: int, **kwargs) -> Product | None:
        product = self.session.get(Product, product_id)
        if not product:
            return None
        for key, value in kwargs.items():
            setattr(product, key, value)
        self.session.commit()
        return product
 
    def toggle_active(self, product_id: int) -> bool:
        product = self.session.get(Product, product_id)
        if not product:
            return False
        product.is_active = not product.is_active
        self.session.commit()
        return product.is_active
 
    def get_by_category(self, category_id: int) -> list[Product]:
        return (
            self.session.query(Product)
            .filter_by(category_id=category_id, is_active=True)
            .order_by(Product.name)
            .all()
        )
 
 
class CategoryService:
    def __init__(self, session: Session):
        self.session = session
 
    def get_all(self, only_active: bool = True) -> list[Category]:
        q = self.session.query(Category)
        if only_active:
            q = q.filter_by(is_active=True)
        return q.order_by(Category.name).all()
 
    def create(self, name: str, description: str = "") -> Category:
        category = Category(name=name, description=description)
        self.session.add(category)
        self.session.commit()
        return category
 
    def update(self, category_id: int, **kwargs) -> Category | None:
        category = self.session.get(Category, category_id)
        if not category:
            return None
        for key, value in kwargs.items():
            setattr(category, key, value)
        self.session.commit()
        return category
 
    def toggle_active(self, category_id: int) -> bool:
        category = self.session.get(Category, category_id)
        if not category:
            return False
        category.is_active = not category.is_active
        self.session.commit()
        return category.is_active