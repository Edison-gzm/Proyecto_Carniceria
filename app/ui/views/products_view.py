import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QScrollArea, QFrame, 
    QGridLayout, QDialog, QFormLayout, QComboBox, 
    QMessageBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap, QColor
from database.session import get_session
from services.product_service import ProductService, CategoryService
from database.models.product import UnitType
from ui.theme import COLORS

BASE_DIR = Path(__file__).parent.parent.parent
IMAGES_DIR = BASE_DIR / "assets" / "images"

CATEGORY_IMAGES = {
    "Carne de Vaca": str(IMAGES_DIR / "vaca.jpg"),
    "Carne de Cerdo": str(IMAGES_DIR / "cerdo.jpg"),
    "Pollo": str(IMAGES_DIR / "pollo.jpg"),
    "Embutidos": str(IMAGES_DIR / "embutidos.jpg")
}


def get_square_pixmap(img_path: str, size: int) -> QPixmap:
    """Recorta la imagen desde el centro a formato 1:1 (cuadrado) y la escala uniformemente."""
    pixmap = QPixmap(img_path)
    if pixmap.isNull():
        return QPixmap()
    
    w, h = pixmap.width(), pixmap.height()
    min_dim = min(w, h)
    x = (w - min_dim) // 2
    y = (h - min_dim) // 2
    
    # Recorte centrado en un cuadrado perfecto
    cropped = pixmap.copy(x, y, min_dim, min_dim)
    return cropped.scaled(size, size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)


def format_price(value) -> str:
    try:
        return f"${int(float(str(value))):,}".replace(",", ".")
    except Exception:
        return "$0"


class ProductDialog(QDialog):
    """Diálogo para crear y editar productos."""

    def __init__(self, parent, session, product=None):
        super().__init__(parent)
        self.session = session
        self.product = product
        self.is_edit = product is not None
        self.setWindowTitle("Editar Producto" if self.is_edit else "Nuevo Producto")
        self.setFixedSize(400, 320)
        self.setStyleSheet(f"background-color: {COLORS['secondary']}; color: {COLORS['text_primary']};")
        self._build_ui()
        if self.is_edit:
            self._fill_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Editar Producto" if self.is_edit else "Nuevo Producto")
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Lomo de res")
        self.name_input.setFixedHeight(40)
        form.addRow("Nombre:", self.name_input)

        self.category_combo = QComboBox()
        self.category_combo.setFixedHeight(40)
        self.category_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_primary']};
                selection-background-color: {COLORS['primary']};
            }}
        """)
        cat_service = CategoryService(self.session)
        self.categories = cat_service.get_all()
        for cat in self.categories:
            self.category_combo.addItem(cat.name, cat.id)
        form.addRow("Categoría:", self.category_combo)

        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Ej: 15000")
        self.price_input.setFixedHeight(40)
        form.addRow("Precio (por kg):", self.price_input)

        layout.addLayout(form)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_primary']};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border']};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Guardar")
        self.save_btn.setFixedHeight(40)
        self.save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def _fill_data(self):
        self.name_input.setText(self.product.name)
        self.price_input.setText(str(int(float(str(self.product.price)))))
        for i in range(self.category_combo.count()):
            if self.category_combo.itemData(i) == self.product.category_id:
                self.category_combo.setCurrentIndex(i)
                break

    def _save(self):
        name = self.name_input.text().strip()
        price_text = self.price_input.text().strip().replace(".", "").replace(",", "")
        category_id = self.category_combo.currentData()

        if not name:
            QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
            return
        try:
            price = float(price_text)
            if price <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingresa un precio válido.")
            return

        try:
            service = ProductService(self.session)
            if self.is_edit:
                service.update(self.product.id, name=name, price=price, category_id=category_id)
            else:
                service.create(
                    name=name, price=price,
                    category_id=category_id,
                    unit=UnitType.KILO
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")


class ProductsView(QWidget):
    """Vista de productos en formato catálogo visual con buscador resaltado e imágenes cuadradas."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.session = app.session
        self.selected_category_name = "Todas"
        self._build_ui()
        self._load_products()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(18)

        # 1. Barra superior (Título + Buscador Destacado + Botón Nuevo)
        top_bar = QHBoxLayout()
        title = QLabel("Catálogo de Productos")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #111111;")
        top_bar.addWidget(title)

        top_bar.addStretch()

        # Input de búsqueda diseñado con alto contraste y sombra
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 BUSCAR PRODUCTO...")
        self.search_input.setFixedWidth(290)
        self.search_input.setFixedHeight(46)
        self.search_input.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #FFFFFF;
                color: #111111;
                border: 2px solid {COLORS.get('primary', '#1E3A8A')};
                border-radius: 10px;
                padding-left: 14px;
                padding-right: 14px;
            }}
            QLineEdit:focus {{
                border: 3px solid #2563EB;
                background-color: #F8FAFC;
            }}
        """)
        
        # Efecto de sombra real (DropShadow) para destacar el buscador
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 45))
        self.search_input.setGraphicsEffect(shadow)

        self.search_input.textChanged.connect(self._load_products)
        top_bar.addWidget(self.search_input)

        self.new_btn = QPushButton("+ Nuevo Producto")
        self.new_btn.setFixedHeight(42)
        self.new_btn.setCursor(Qt.PointingHandCursor)
        self.new_btn.clicked.connect(self._open_create)

        from database.models.user import UserRole
        if hasattr(self.app, 'current_user') and self.app.current_user.role != UserRole.ADMIN:
            self.new_btn.setVisible(False)

        top_bar.addWidget(self.new_btn)
        layout.addLayout(top_bar)

        # 2. Selector rápido de categorías (Imágenes en formato cuadrado uniforme)
        cat_bar = QHBoxLayout()
        cat_bar.setSpacing(12)

        self.cat_buttons = {}
        categories = [
            ("Todas", None),
            ("Carne de Vaca", CATEGORY_IMAGES.get("Carne de Vaca")),
            ("Carne de Cerdo", CATEGORY_IMAGES.get("Carne de Cerdo")),
            ("Pollo", CATEGORY_IMAGES.get("Pollo")),
            ("Embutidos", CATEGORY_IMAGES.get("Embutidos"))
        ]

        for name, img_path in categories:
            btn = QPushButton()
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(name)
            btn.setFixedSize(85, 85)

            btn_layout = QVBoxLayout(btn)
            btn_layout.setContentsMargins(6, 6, 6, 6)
            btn_layout.setAlignment(Qt.AlignCenter)

            if img_path:
                img_label = QLabel()
                pixmap = get_square_pixmap(img_path, 72)
                if not pixmap.isNull():
                    img_label.setPixmap(pixmap)
                img_label.setAlignment(Qt.AlignCenter)
                img_label.setStyleSheet("border: None; background: transparent; border-radius: 6px;")
                btn_layout.addWidget(img_label)
            else:
                text_label = QLabel("Todas")
                text_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
                text_label.setStyleSheet("color: #111111; background: transparent;")
                text_label.setAlignment(Qt.AlignCenter)
                btn_layout.addWidget(text_label)

            btn.clicked.connect(lambda _, c=name: self.filter_by_category(c))
            self.cat_buttons[name] = btn
            cat_bar.addWidget(btn)

        cat_bar.addStretch()
        layout.addLayout(cat_bar)

        # 3. Área desplazable con cuadrícula de productos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.products_container = QWidget()
        self.products_grid = QGridLayout(self.products_container)
        self.products_grid.setSpacing(16)
        self.products_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll.setWidget(self.products_container)
        layout.addWidget(scroll)

        self._update_cat_buttons_style()

    def filter_by_category(self, category_name):
        self.selected_category_name = category_name
        self._update_cat_buttons_style()
        self._load_products()

    def _update_cat_buttons_style(self):
        for name, btn in self.cat_buttons.items():
            if name == self.selected_category_name:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['surface_light']};
                        border: 3px solid {COLORS['primary']};
                        border-radius: 12px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['surface']};
                        border: 1px solid {COLORS['border']};
                        border-radius: 12px;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['surface_light']};
                    }}
                """)

    def _load_products(self):
        while self.products_grid.count():
            item = self.products_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.session.expire_all()
        service = ProductService(self.session)
        products = service.get_all(only_active=True)

        search_text = self.search_input.text().lower().replace("🔍", "").strip()

        filtered = []
        for p in products:
            cat_name = p.category.name if p.category else "Sin Categoría"

            matches_cat = (self.selected_category_name == "Todas" or cat_name.lower() == self.selected_category_name.lower())
            matches_search = (search_text in p.name.lower())

            if matches_cat and matches_search:
                filtered.append((p, cat_name))

        if not filtered:
            empty_lbl = QLabel("No se encontraron productos.")
            empty_lbl.setFont(QFont("Segoe UI", 13))
            empty_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-top: 30px;")
            self.products_grid.addWidget(empty_lbl, 0, 0)
            return

        cols = 4
        for i, (product, cat_name) in enumerate(filtered):
            card = self._create_product_card(product, cat_name)
            row = i // cols
            col = i % cols
            self.products_grid.addWidget(card, row, col)

    def _create_product_card(self, product, category_name):
        card = QFrame()
        card.setFixedSize(220, 260)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
            QFrame:hover {{
                border: 2px solid {COLORS['primary']};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setAlignment(Qt.AlignCenter)

        # Imagen recortada perfectamente en cuadrado
        img_path = CATEGORY_IMAGES.get(category_name, str(IMAGES_DIR / "vaca.jpg"))
        img_label = QLabel()
        pixmap = get_square_pixmap(img_path, 80)
        if not pixmap.isNull():
            img_label.setPixmap(pixmap)
        img_label.setAlignment(Qt.AlignCenter)
        img_label.setStyleSheet("border: none;")
        layout.addWidget(img_label)

        # Nombre
        name_label = QLabel(product.name)
        name_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        name_label.setStyleSheet("color: #111111; border: none;")
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

        # Precio Gigante
        price_label = QLabel(format_price(product.price))
        price_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        price_label.setStyleSheet(f"color: {COLORS['success']}; border: none;")
        price_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(price_label)

        # Botones Editar / Eliminar
        btn_box = QHBoxLayout()
        btn_box.setSpacing(6)

        edit_btn = QPushButton("✏ Editar")
        edit_btn.setFixedHeight(28)
        edit_btn.setFont(QFont("Segoe UI", 9))
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: {COLORS['border']}; }}
        """)
        edit_btn.clicked.connect(lambda _, p=product: self._open_edit(p))
        btn_box.addWidget(edit_btn)

        del_btn = QPushButton("🗑")
        del_btn.setFixedHeight(28)
        del_btn.setFixedWidth(32)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']};
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #c0392b; }}
        """)
        del_btn.clicked.connect(lambda _, p=product: self._delete_product(p))
        btn_box.addWidget(del_btn)

        from database.models.user import UserRole
        if hasattr(self.app, 'current_user') and self.app.current_user.role != UserRole.ADMIN:
            edit_btn.setVisible(False)
            del_btn.setVisible(False)

        layout.addLayout(btn_box)
        return card

    def _open_create(self):
        dialog = ProductDialog(self, self.session)
        if dialog.exec():
            self._load_products()

    def _open_edit(self, product):
        dialog = ProductDialog(self, self.session, product)
        if dialog.exec():
            self._load_products()

    def _delete_product(self, product):
        reply = QMessageBox.warning(
            self, "Eliminar producto",
            f"¿Eliminar '{product.name}' de la lista?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            service = ProductService(self.session)
            exito, mensaje = service.delete(product.id)
            if exito:
                QMessageBox.information(self, "Éxito", "Producto eliminado correctamente.")
            else:
                service.toggle_active(product.id)
                QMessageBox.information(self, "Producto retirado", f"'{product.name}' se ha retirado de la lista.")
            self._load_products()