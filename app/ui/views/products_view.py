import sys
from database.models.user import UserRole
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QComboBox, QMessageBox, QFrame, QFormLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from services.product_service import ProductService, CategoryService
from database.models.product import UnitType
from ui.theme import COLORS

def format_price(value) -> str:
    try:
        return f"${int(float(str(value))):,}".replace(",", ".")
    except Exception:
        return "$0"


class ProductsView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.session = app.session
        self.selected_product = None
        self._build_ui()
        self._apply_role_permissions()
        self._load_data()

    def _is_admin(self) -> bool:
        """Verifica si el usuario actual tiene rol de Administrador."""
        if not hasattr(self.app, 'current_user') or not self.app.current_user:
            return False
        role = getattr(self.app.current_user, 'role', None)
        return role == UserRole.ADMIN or str(role).upper() == "ADMIN"

    def _apply_role_permissions(self):
        """Oculta o deshabilita acciones no permitidas para usuarios no administradores."""
        if not self._is_admin():
            self.btn_delete.setVisible(False)

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # TABLA DE PRODUCTOS
        left_layout = QVBoxLayout()
        
        top_bar = QHBoxLayout()
        title = QLabel("Listado de Productos")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #111111;")
        top_bar.addWidget(title)
        top_bar.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar en el listado...")
        self.search_input.setFixedWidth(250)
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: white; color: #111111;
                border: 1px solid #CBD5E1; border-radius: 6px; padding: 0 10px;
            }
        """)
        self.search_input.textChanged.connect(self._load_table)
        top_bar.addWidget(self.search_input)
        left_layout.addLayout(top_bar)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Categoría", "Precio"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white; border: 1px solid #E2E8F0; gridline-color: #F1F5F9; color: #111111;
            }
            QHeaderView::section {
                background-color: #F8FAFC; font-weight: bold; border: none; padding: 8px; color: #334155;
            }
        """)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        left_layout.addWidget(self.table)

        # PANEL DE CREACIÓN / EDICIÓN
        panel = QFrame()
        panel.setFixedWidth(340)
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.get('surface', '#FFFFFF')};
                border: 1px solid {COLORS.get('border', '#E2E8F0')};
                border-radius: 10px;
            }}
        """)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_layout.setSpacing(14)

        self.panel_title = QLabel("Crear Nuevo Producto")
        self.panel_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.panel_title.setStyleSheet("border: none; color: #111111;")
        panel_layout.addWidget(self.panel_title)

        form = QFormLayout()
        form.setSpacing(12)

        INPUT_STYLE = """
            QLineEdit, QComboBox {
                background-color: #FFFFFF; color: #111111; font-weight: bold;
                border: 1.5px solid #64748B; border-radius: 6px; padding: 6px;
            }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #2563EB; }
        """

        self.txt_name = QLineEdit()
        self.txt_name.setStyleSheet(INPUT_STYLE)
        
        self.cmb_category = QComboBox()
        self.cmb_category.setStyleSheet(INPUT_STYLE)

        self.txt_price = QLineEdit()
        self.txt_price.setStyleSheet(INPUT_STYLE)

        form.addRow("Nombre:", self.txt_name)
        form.addRow("Categoría:", self.cmb_category)
        form.addRow("Precio ($):", self.txt_price)
        panel_layout.addLayout(form)

        # Botones de Acción CRUD
        self.btn_new = QPushButton("✨ Limpiar Formulario")
        self.btn_save = QPushButton("➕ Crear Producto")
        self.btn_delete = QPushButton("🗑️ Eliminar Seleccionado")

        self.btn_new.setFixedHeight(36)
        self.btn_save.setFixedHeight(40)
        self.btn_delete.setFixedHeight(36)

        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setCursor(Qt.PointingHandCursor)

        self.btn_new.setStyleSheet("background-color: #64748B; color: white; font-weight: bold; border-radius: 6px; border: none;")
        self.btn_save.setStyleSheet("background-color: #16A34A; color: white; font-weight: bold; border-radius: 6px; border: none; font-size: 13px;")
        self.btn_delete.setStyleSheet("background-color: #DC2626; color: white; font-weight: bold; border-radius: 6px; border: none;")

        self.btn_new.clicked.connect(self._clear_form)
        self.btn_save.clicked.connect(self._save_product)
        self.btn_delete.clicked.connect(self._delete_product)

        panel_layout.addWidget(self.btn_save)
        panel_layout.addWidget(self.btn_new)
        panel_layout.addWidget(self.btn_delete)
        panel_layout.addStretch()

        main_layout.addLayout(left_layout, stretch=2)
        main_layout.addWidget(panel, stretch=1)

    def _load_data(self):
        cat_service = CategoryService(self.session)
        self.cmb_category.clear()
        for cat in cat_service.get_all():
            self.cmb_category.addItem(cat.name, cat.id)

        self._load_table()

    def _load_table(self):
        self.table.setRowCount(0)
        self.session.expire_all()
        prod_service = ProductService(self.session)
        products = prod_service.get_all(only_active=True)

        query = self.search_input.text().lower().strip()

        for prod in products:
            if query and query not in prod.name.lower():
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(prod.id)))
            self.table.setItem(row, 1, QTableWidgetItem(prod.name))
            
            cat_name = prod.category.name if prod.category else "Sin Categoría"
            self.table.setItem(row, 2, QTableWidgetItem(cat_name))
            self.table.setItem(row, 3, QTableWidgetItem(format_price(prod.price)))

    def _on_row_selected(self):
        # Si NO es admin, no se permite cargar el producto para edición o eliminación
        if not self._is_admin():
            self.selected_product = None
            self.panel_title.setText("Crear Nuevo Producto")
            self.btn_save.setText("➕ Crear Producto")
            self.btn_save.setEnabled(True)
            return

        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        prod_id = int(self.table.item(row, 0).text())

        prod_service = ProductService(self.session)
        self.selected_product = prod_service.get_by_id(prod_id)

        if self.selected_product:
            self.txt_name.setText(self.selected_product.name)
            self.txt_price.setText(str(int(float(str(self.selected_product.price)))))

            for i in range(self.cmb_category.count()):
                if self.cmb_category.itemData(i) == self.selected_product.category_id:
                    self.cmb_category.setCurrentIndex(i)
                    break

            self.panel_title.setText("Editar Producto")
            self.btn_save.setText("💾 Actualizar Producto")
            self.btn_save.setEnabled(True)
            self.btn_delete.setEnabled(True)

    def _clear_form(self):
        self.selected_product = None
        self.panel_title.setText("Crear Nuevo Producto")
        self.btn_save.setText("➕ Crear Producto")
        self.btn_save.setEnabled(True)
        
        if self._is_admin():
            self.btn_delete.setVisible(True)
            self.btn_delete.setEnabled(True)
        else:
            self.btn_delete.setVisible(False)

        self.txt_name.clear()
        self.txt_price.clear()
        self.table.clearSelection()

    def _save_product(self):
        name = self.txt_name.text().strip()
        price_text = self.txt_price.text().strip().replace(".", "").replace(",", "")
        category_id = self.cmb_category.currentData()

        if not name or not price_text:
            QMessageBox.warning(self, "Atención", "Por favor completa todos los campos.")
            return

        try:
            price = float(price_text)
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingresa un precio numérico válido.")
            return

        prod_service = ProductService(self.session)

        # Si hay producto seleccionado Y es admin, se actualiza; de lo contrario, SIEMPRE se crea
        if self.selected_product and self._is_admin():
            prod_service.update(self.selected_product.id, name=name, price=price, category_id=category_id)
            QMessageBox.information(self, "Éxito", "Producto actualizado correctamente.")
        else:
            prod_service.create(
                name=name, price=price, category_id=category_id, 
                unit=UnitType.KILO
            )
            QMessageBox.information(self, "Éxito", "Producto creado exitosamente.")

        self._clear_form()
        self._load_table()  

    def _delete_product(self):
        if not self._is_admin():
            QMessageBox.warning(self, "Acceso Denegado", "Solo los administradores pueden eliminar productos.")
            return

        if not self.selected_product:
            QMessageBox.warning(self, "Atención", "Selecciona primero un producto de la tabla para eliminar.")
            return

        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Estás seguro de que deseas eliminar el producto '{self.selected_product.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            prod_service = ProductService(self.session)
            success, message = prod_service.delete(self.selected_product.id)

            if success:
                self._clear_form()
                self._load_table()
            else:
                QMessageBox.warning(self, "No se puede eliminar", message)