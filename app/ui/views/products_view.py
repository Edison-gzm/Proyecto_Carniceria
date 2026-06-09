import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QComboBox,
    QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from database.session import get_session
from services.product_service import ProductService, CategoryService
from database.models.product import UnitType
from ui.theme import COLORS


def format_price(value) -> str:
    try:
        return f"${int(float(str(value))):,}".replace(",", ".")
    except:
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

        # Nombre
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Lomo de res")
        self.name_input.setFixedHeight(40)
        form.addRow("Nombre:", self.name_input)

        # Categoría
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

        # Precio
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("Ej: 15000")
        self.price_input.setFixedHeight(40)
        form.addRow("Precio (por kg):", self.price_input)

        layout.addLayout(form)
        layout.addStretch()

        # Botones
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
    """Vista principal del módulo de productos."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.session = app.session
        self._build_ui()
        self._load_products()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Encabezado
        header = QHBoxLayout()
        title = QLabel("Productos")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        header.addWidget(title)
        header.addStretch()

        self.new_btn = QPushButton("+ Nuevo Producto")
        self.new_btn.setFixedHeight(40)
        self.new_btn.clicked.connect(self._open_create)

        # Solo admin puede crear
        from database.models.user import UserRole
        if self.app.current_user.role != UserRole.ADMIN:
            self.new_btn.setVisible(False)

        header.addWidget(self.new_btn)
        layout.addLayout(header)

        # Búsqueda y filtro
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar producto...")
        self.search_input.setFixedHeight(38)
        self.search_input.textChanged.connect(self._search)
        filter_layout.addWidget(self.search_input)

        self.category_filter = QComboBox()
        self.category_filter.setFixedHeight(38)
        self.category_filter.setFixedWidth(180)
        self.category_filter.setStyleSheet(f"""
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
        self.category_filter.addItem("Todas las categorías", None)
        cat_service = CategoryService(self.session)
        for cat in cat_service.get_all():
            self.category_filter.addItem(cat.name, cat.id)
        self.category_filter.currentIndexChanged.connect(self._load_products)
        filter_layout.addWidget(self.category_filter)
        layout.addLayout(filter_layout)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Categoría", "Precio/kg", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 90)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                gridline-color: {COLORS['border']};
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {COLORS['text_primary']};
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['primary']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_secondary']};
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
            QTableWidget::item:alternate {{
                background-color: {COLORS['surface_light']};
            }}
        """)
        layout.addWidget(self.table)

        # Botones de acción
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        self.edit_btn = QPushButton("✏ Editar")
        self.edit_btn.setFixedHeight(38)
        self.edit_btn.setFixedWidth(110)
        self.edit_btn.clicked.connect(self._open_edit)

        self.toggle_btn = QPushButton("⏸ Desactivar")
        self.toggle_btn.setFixedHeight(38)
        self.toggle_btn.setFixedWidth(130)
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['warning']};
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #d68910;
            }}
        """)
        self.toggle_btn.clicked.connect(self._toggle_product)

        action_layout.addWidget(self.edit_btn)
        action_layout.addWidget(self.toggle_btn)
        layout.addLayout(action_layout)

    def _load_products(self):
        service = ProductService(self.session)
        category_id = self.category_filter.currentData()

        if category_id:
            products = service.get_by_category(category_id)
        else:
            products = service.get_all(only_active=False)

        self._populate_table(products)

    def _search(self, text):
        if not text.strip():
            self._load_products()
            return
        service = ProductService(self.session)
        products = service.search(text)
        self._populate_table(products)

    def _populate_table(self, products):
        self.table.setRowCount(len(products))
        for row, p in enumerate(products):
            self.table.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.table.setItem(row, 1, QTableWidgetItem(p.name))
            self.table.setItem(row, 2, QTableWidgetItem(p.category.name if p.category else ""))
            self.table.setItem(row, 3, QTableWidgetItem(format_price(p.price)))

            estado = QTableWidgetItem("Activo" if p.is_active else "Inactivo")
            estado.setForeground(
                Qt.green if p.is_active else Qt.red
            )
            self.table.setItem(row, 4, estado)
            self.table.item(row, 0).setData(Qt.UserRole, p.id)

    def _get_selected_product_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecciona un producto primero.")
            return None
        return self.table.item(row, 0).data(Qt.UserRole)

    def _open_create(self):
        dialog = ProductDialog(self, self.session)
        if dialog.exec():
            self._load_products()

    def _open_edit(self):
        product_id = self._get_selected_product_id()
        if not product_id:
            return
        service = ProductService(self.session)
        product = service.get_by_id(product_id)
        dialog = ProductDialog(self, self.session, product)
        if dialog.exec():
            self._load_products()

    def _toggle_product(self):
        product_id = self._get_selected_product_id()
        if not product_id:
            return
        service = ProductService(self.session)
        product = service.get_by_id(product_id)
        action = "desactivar" if product.is_active else "activar"

        reply = QMessageBox.question(
            self, "Confirmar",
            f"¿Seguro que quieres {action} '{product.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            service.toggle_active(product_id)
            self._load_products()