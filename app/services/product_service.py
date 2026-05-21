from sqlalchemy.orm import Session
from app.database.models.product import Product
from app.database.models.category import Category


class ProductService:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> list[Product]:
        return self.session.query(Product).filter_by(is_active=True).all()

    def get_by_category(self, category_id: int) -> list[Product]:
        return self.session.query(Product).filter_by(category_id=category_id, is_active=True).all()

    def search(self, query: str) -> list[Product]:
        return self.session.query(Product)\
            .filter(Product.name.ilike(f"%{query}%"), Product.is_active == True)\
            .all()

    def create(self, name: str, price: float, category_id: int) -> Product:
        product = Product(name=name, price=price, category_id=category_id)
        self.session.add(product)
        self.session.commit()
        return product

    def update(self, product_id: int, name: str, price: float, category_id: int) -> Product:
        product = self.session.query(Product).get(product_id)
        product.name = name
        product.price = price
        product.category_id = category_id
        self.session.commit()
        return product

    def toggle_active(self, product_id: int) -> Product:
        product = self.session.query(Product).get(product_id)
        product.is_active = not product.is_active
        self.session.commit()
        return product

    # --- Categorías ---

    def get_all_categories(self) -> list[Category]:
        return self.session.query(Category).filter_by(is_active=True).all()

    def create_category(self, name: str) -> Category:
        category = Category(name=name)
        self.session.add(category)
        self.session.commit()
        return category

    def toggle_category(self, category_id: int) -> Category:
        category = self.session.query(Category).get(category_id)
        category.is_active = not category.is_active
        self.session.commit()
        return category