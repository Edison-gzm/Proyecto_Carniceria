import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout,
    QMessageBox, QFrame, QSizePolicy, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from services.customer_service import CustomerService
from services.product_service import ProductService
from services.sale_service import SaleService
from services.invoice_service import InvoiceService
from ui.theme import COLORS


def format_price(value) -> str:
    try:
        return f"${int(float(str(value))):,}".replace(",", ".")
    except:
        return "$0"


# ──────────────────────────────────────────────
# Diálogo: seleccionar o crear cliente
# ──────────────────────────────────────────────
class SelectCustomerDialog(QDialog):
    def __init__(self, parent, session):
        super().__init__(parent)
        self.session = session
        self.selected_customer = None
        self.setWindowTitle("Seleccionar Cliente")
        self.setFixedSize(500, 460)
        self.setStyleSheet(f"background-color: {COLORS['secondary']}; color: {COLORS['text_primary']};")
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Seleccionar Cliente")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        layout.addWidget(title)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre o cédula...")
        self.search_input.setFixedHeight(38)
        self.search_input.textChanged.connect(self._search)
        layout.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Nombre", "Cédula/NIT", "Teléfono"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setColumnWidth(1, 130)
        self.table.setColumnWidth(2, 120)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._confirm_selection)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                gridline-color: {COLORS['border']};
            }}
            QTableWidget::item {{ padding: 8px; color: {COLORS['text_primary']}; }}
            QTableWidget::item:selected {{ background-color: {COLORS['primary']}; }}
            QHeaderView::section {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_secondary']};
                padding: 8px; border: none; font-weight: bold;
            }}
            QTableWidget::item:alternate {{ background-color: {COLORS['surface_light']}; }}
        """)
        layout.addWidget(self.table)

        # Botón crear nuevo cliente rápido
        new_btn = QPushButton("+ Crear nuevo cliente")
        new_btn.setFixedHeight(38)
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {COLORS['border']}; }}
        """)
        new_btn.clicked.connect(self._create_customer)
        layout.addWidget(new_btn)

        # Botón cliente genérico (Consumidor Final) — no se guarda nada nuevo en la BD
        generic_btn = QPushButton("👤  Cliente genérico (no se guardará)")
        generic_btn.setFixedHeight(38)
        generic_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: {COLORS['border']}; color: {COLORS['text_primary']}; }}
        """)
        generic_btn.clicked.connect(self._select_generic)
        layout.addWidget(generic_btn)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_primary']};
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: {COLORS['border']}; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        select_btn = QPushButton("Seleccionar")
        select_btn.setFixedHeight(40)
        select_btn.clicked.connect(self._confirm_selection)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(select_btn)
        layout.addLayout(btn_layout)

    def _load(self, query=""):
        service = CustomerService(self.session)
        customers = service.search(query) if query else service.get_all()
        self.table.setRowCount(len(customers))
        for row, c in enumerate(customers):
            self.table.setItem(row, 0, QTableWidgetItem(c.full_name))
            self.table.setItem(row, 1, QTableWidgetItem(c.id_number or ""))
            self.table.setItem(row, 2, QTableWidgetItem(c.phone or ""))
            self.table.item(row, 0).setData(Qt.UserRole, c.id)

    def _search(self, text):
        self._load(text)

    def _confirm_selection(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecciona un cliente de la lista.")
            return
        customer_id = self.table.item(row, 0).data(Qt.UserRole)
        service = CustomerService(self.session)
        self.selected_customer = service.get_by_id(customer_id)
        self.accept()

    def _create_customer(self):
        from ui.views.customers_view import CustomerDialog
        dialog = CustomerDialog(self, self.session)
        if dialog.exec():
            self._load()

    def _select_generic(self):
        """Usa el cliente 'Consumidor Final' existente en la BD, sin crear nada nuevo."""
        service = CustomerService(self.session)
        results = service.search("Consumidor Final")
        if results:
            self.selected_customer = results[0]
            self.accept()
        else:
            QMessageBox.warning(
                self, "No encontrado",
                "No existe el cliente 'Consumidor Final' en la base de datos.\n"
                "Crea uno manualmente desde el módulo de Clientes."
            )


# ──────────────────────────────────────────────
# Diálogo: ingresar cantidad para un producto
# ──────────────────────────────────────────────
class QuantityDialog(QDialog):
    def __init__(self, parent, product):
        super().__init__(parent)
        self.product = product
        self.quantity = None
        self.setWindowTitle("Cantidad")
        self.setFixedSize(300, 200)
        self.setStyleSheet(f"background-color: {COLORS['secondary']}; color: {COLORS['text_primary']};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        label = QLabel(f"{self.product.name}")
        label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        layout.addWidget(label)

        unit_label = QLabel(f"Precio: {format_price(self.product.price)} / {self.product.unit.value}")
        unit_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(unit_label)

        self.qty_input = QLineEdit()
        self.qty_input.setPlaceholderText(f"Cantidad en {self.product.unit.value}")
        self.qty_input.setFixedHeight(44)
        self.qty_input.setFont(QFont("Segoe UI", 14))
        self.qty_input.returnPressed.connect(self._confirm)
        layout.addWidget(self.qty_input)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_primary']};
                border-radius: 6px;
            }}
        """)
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("Agregar")
        ok_btn.setFixedHeight(40)
        ok_btn.clicked.connect(self._confirm)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

        self.qty_input.setFocus()

    def _confirm(self):
        text = self.qty_input.text().strip().replace(",", ".")
        try:
            qty = float(text)
            if qty <= 0:
                raise ValueError
            self.quantity = qty
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingresa una cantidad válida mayor a 0.")


# ──────────────────────────────────────────────
# Vista principal: POS / Ventas
# ──────────────────────────────────────────────
# ──────────────────────────────────────────────
# Diálogo: opciones después de confirmar la venta
# ──────────────────────────────────────────────
class PostSaleDialog(QDialog):
    def __init__(self, parent, session, sale):
        super().__init__(parent)
        self.session = session
        self.sale = sale
        self.setWindowTitle("Venta registrada")
        self.setFixedSize(380, 360)
        self.setStyleSheet(f"background-color: {COLORS['secondary']}; color: {COLORS['text_primary']};")
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        check = QLabel("✔  Venta registrada")
        check.setFont(QFont("Segoe UI", 15, QFont.Bold))
        check.setStyleSheet(f"color: {COLORS['success']};")
        check.setAlignment(Qt.AlignCenter)
        layout.addWidget(check)

        info = QLabel(
            f"Factura: {self.sale.invoice_number}\n"
            f"Total: {format_price(self.sale.total)}"
        )
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(info)

        layout.addSpacing(6)

        has_email = bool(self.sale.customer and self.sale.customer.email)
        email_btn = QPushButton("📧  Enviar factura electrónica" if has_email else "📧  Cliente sin correo registrado")
        email_btn.setFixedHeight(46)
        email_btn.setEnabled(has_email)
        email_btn.clicked.connect(self._send_email)
        layout.addWidget(email_btn)

        print_btn = QPushButton("🖨  Imprimir factura")
        print_btn.setFixedHeight(46)
        print_btn.clicked.connect(self._print)
        layout.addWidget(print_btn)

        dian_btn = QPushButton("🏛  Generar factura electrónica DIAN")
        dian_btn.setFixedHeight(46)
        dian_btn.setEnabled(False)
        dian_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_secondary']};
                border-radius: 6px;
            }}
        """)
        dian_btn.setToolTip("Próximamente — integración con la DIAN")
        layout.addWidget(dian_btn)

        layout.addStretch()

        finish_btn = QPushButton("✔  Finalizar")
        finish_btn.setFixedHeight(46)
        finish_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        finish_btn.clicked.connect(self.accept)
        layout.addWidget(finish_btn)

    def _print(self):
        try:
            service = InvoiceService(self.session)
            service.print_invoice(self.sale.id)
            QMessageBox.information(self, "Imprimiendo", "La factura se envió a la impresora.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo imprimir:\n{e}")

    def _send_email(self):
        try:
            service = InvoiceService(self.session)
            service.send_email(self.sale.id)
            QMessageBox.information(self, "Enviado", f"Factura enviada a {self.sale.customer.email}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo enviar el correo:\n{e}")


class SalesView(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.session = app.session
        self.cart = []          # lista de dicts: {product, quantity, subtotal}
        self.customer = None    # Cliente seleccionado
        self._build_ui()
        self._load_products()

    # ── UI ─────────────────────────────────────
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Panel izquierdo: búsqueda y productos
        left = self._build_left_panel()
        # Panel derecho: carrito y total
        right = self._build_right_panel()

        root.addLayout(left, 5)
        root.addLayout(right, 4)

    def _build_left_panel(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 24, 16, 24)
        layout.setSpacing(14)

        title = QLabel("Punto de Venta")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        layout.addWidget(title)

        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("🔍  Buscar producto...")
        self.product_search.setFixedHeight(44)
        self.product_search.setFont(QFont("Segoe UI", 13))
        self.product_search.textChanged.connect(self._search_products)
        layout.addWidget(self.product_search)

        # Tabla de productos
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(4)
        self.product_table.setHorizontalHeaderLabels(["Nombre", "Categoría", "Precio", "Unidad"])
        self.product_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.product_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.product_table.setColumnWidth(2, 110)
        self.product_table.setColumnWidth(3, 80)
        self.product_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.product_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.setAlternatingRowColors(True)
        self.product_table.doubleClicked.connect(self._add_to_cart_from_table)
        self.product_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                gridline-color: {COLORS['border']};
            }}
            QTableWidget::item {{ padding: 8px; color: {COLORS['text_primary']}; }}
            QTableWidget::item:selected {{ background-color: {COLORS['primary']}; }}
            QHeaderView::section {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_secondary']};
                padding: 10px; border: none; font-weight: bold;
            }}
            QTableWidget::item:alternate {{ background-color: {COLORS['surface_light']}; }}
        """)
        layout.addWidget(self.product_table)

        hint = QLabel("Doble clic en un producto para agregarlo al carrito")
        hint.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

        return layout

    def _build_right_panel(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 24, 32, 24)
        layout.setSpacing(14)

        # — Cliente —
        customer_label = QLabel("Cliente")
        customer_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        customer_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(customer_label)

        customer_row = QHBoxLayout()
        self.customer_display = QLabel("Sin cliente seleccionado")
        self.customer_display.setFixedHeight(38)
        self.customer_display.setStyleSheet(f"""
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 0 10px;
            color: {COLORS['text_secondary']};
        """)
        customer_row.addWidget(self.customer_display)

        select_customer_btn = QPushButton("Cambiar")
        select_customer_btn.setFixedWidth(90)
        select_customer_btn.setFixedHeight(38)
        select_customer_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {COLORS['border']}; }}
        """)
        select_customer_btn.clicked.connect(self._select_customer)
        customer_row.addWidget(select_customer_btn)
        layout.addLayout(customer_row)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(sep)

        # — Carrito —
        cart_label = QLabel("Carrito")
        cart_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        cart_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(cart_label)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(["Producto", "Cant.", "Unidad", "Precio", "Subtotal"])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_table.setColumnWidth(1, 50)
        self.cart_table.setColumnWidth(2, 55)
        self.cart_table.setColumnWidth(3, 80)
        self.cart_table.setColumnWidth(4, 85)
        self.cart_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cart_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setAlternatingRowColors(True)
        self.cart_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                gridline-color: {COLORS['border']};
            }}
            QTableWidget::item {{ padding: 6px; color: {COLORS['text_primary']}; font-size: 13px; }}
            QTableWidget::item:selected {{ background-color: {COLORS['primary']}; }}
            QHeaderView::section {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_secondary']};
                padding: 8px; border: none; font-weight: bold;
            }}
            QTableWidget::item:alternate {{ background-color: {COLORS['surface_light']}; }}
        """)
        layout.addWidget(self.cart_table)

        remove_btn = QPushButton("✕  Quitar producto seleccionado")
        remove_btn.setFixedHeight(36)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {COLORS['danger']}; color: white; }}
        """)
        remove_btn.clicked.connect(self._remove_from_cart)
        layout.addWidget(remove_btn)

        # — Total —
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"color: {COLORS['border']};")
        layout.addWidget(sep2)

        total_row = QHBoxLayout()
        total_lbl = QLabel("TOTAL:")
        total_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.total_display = QLabel("$0")
        self.total_display.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.total_display.setStyleSheet(f"color: {COLORS['success']};")
        self.total_display.setAlignment(Qt.AlignRight)
        total_row.addWidget(total_lbl)
        total_row.addStretch()
        total_row.addWidget(self.total_display)
        layout.addLayout(total_row)

        # — Botones —
        self.confirm_btn = QPushButton("🧾  Generar Factura Electrónica")
        self.confirm_btn.setFixedHeight(52)
        self.confirm_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.confirm_btn.clicked.connect(self._confirm_sale)
        layout.addWidget(self.confirm_btn)

        clear_btn = QPushButton("🗑  Limpiar carrito")
        clear_btn.setFixedHeight(38)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: {COLORS['border']}; color: white; }}
        """)
        clear_btn.clicked.connect(self._clear_cart)
        layout.addWidget(clear_btn)

        return layout

    # ── Lógica ─────────────────────────────────
    def _load_products(self, query=""):
        self.session.expire_all() #evitar problemas con la caché
        service = ProductService(self.session)
        products = service.search(query) if query else service.get_all(only_active=True)
        self.product_table.setRowCount(len(products))
        for row, p in enumerate(products):
            self.product_table.setItem(row, 0, QTableWidgetItem(p.name))
            self.product_table.setItem(row, 1, QTableWidgetItem(p.category.name if p.category else ""))
            self.product_table.setItem(row, 2, QTableWidgetItem(format_price(p.price)))
            self.product_table.setItem(row, 3, QTableWidgetItem(p.unit.value))
            self.product_table.item(row, 0).setData(Qt.UserRole, p.id)

    def _search_products(self, text):
        self._load_products(text)

    def _add_to_cart_from_table(self):
        row = self.product_table.currentRow()
        if row < 0:
            return
        product_id = self.product_table.item(row, 0).data(Qt.UserRole)
        service = ProductService(self.session)
        product = service.get_by_id(product_id)
        if not product:
            return

        dialog = QuantityDialog(self, product)
        if not dialog.exec():
            return
        qty = dialog.quantity

        # Si ya está en el carrito, actualizar cantidad
        for item in self.cart:
            if item["product"].id == product.id:
                item["quantity"] += qty
                item["subtotal"] = item["quantity"] * float(product.price)
                self._refresh_cart()
                return

        self.cart.append({
            "product": product,
            "quantity": qty,
            "subtotal": qty * float(product.price),
        })
        self._refresh_cart()

    def _refresh_cart(self):
        self.cart_table.setRowCount(len(self.cart))
        total = 0
        for row, item in enumerate(self.cart):
            p = item["product"]
            qty = item["quantity"]
            sub = item["subtotal"]
            total += sub

            qty_str = f"{qty:.3f}".rstrip("0").rstrip(".")
            self.cart_table.setItem(row, 0, QTableWidgetItem(p.name))
            self.cart_table.setItem(row, 1, QTableWidgetItem(qty_str))
            self.cart_table.setItem(row, 2, QTableWidgetItem(p.unit.value))
            self.cart_table.setItem(row, 3, QTableWidgetItem(format_price(p.price)))
            self.cart_table.setItem(row, 4, QTableWidgetItem(format_price(sub)))
            self.cart_table.item(row, 0).setData(Qt.UserRole, row)

        self.total_display.setText(format_price(total))

    def _remove_from_cart(self):
        row = self.cart_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecciona un producto del carrito.")
            return
        del self.cart[row]
        self._refresh_cart()

    def _clear_cart(self):
        if not self.cart:
            return
        reply = QMessageBox.question(
            self, "Confirmar", "¿Vaciar el carrito?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.cart.clear()
            self._refresh_cart()

    def _select_customer(self):
        dialog = SelectCustomerDialog(self, self.session)
        if dialog.exec() and dialog.selected_customer:
            self.customer = dialog.selected_customer
            self.customer_display.setText(
                f"{self.customer.full_name}  —  {self.customer.id_number or 'Sin cédula'}"
            )
            self.customer_display.setStyleSheet(f"""
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['primary']};
                border-radius: 6px;
                padding: 0 10px;
                color: {COLORS['text_primary']};
            """)

    def _confirm_sale(self):
        if not self.cart:
            QMessageBox.warning(self, "Carrito vacío", "Agrega al menos un producto.")
            return

        # Paso obligatorio: elegir cliente (existente, nuevo o genérico) antes de generar la factura
        if not self.customer:
            dialog = SelectCustomerDialog(self, self.session)
            if not dialog.exec() or not dialog.selected_customer:
                QMessageBox.information(self, "Venta cancelada", "Debes seleccionar un cliente para generar la factura.")
                return
            self.customer = dialog.selected_customer

        customer_id = self.customer.id

        items = [
            {"product_id": item["product"].id, "quantity": item["quantity"]}
            for item in self.cart
        ]

        try:
            sale_service = SaleService(self.session)
            sale = sale_service.create_sale(
                user_id=self.app.current_user.id,
                customer_id=customer_id,
                items=items,
            )

            # Generar el PDF de la factura y guardar su ruta en la BD
            try:
                inv = InvoiceService(self.session)
                inv.generate_pdf(sale.id)
            except Exception as e:
                QMessageBox.warning(self, "Aviso", f"La venta se registró, pero no se pudo generar el PDF:\n{e}")

            self.cart.clear()
            self.customer = None
            self.customer_display.setText("Sin cliente seleccionado")
            self.customer_display.setStyleSheet(f"""
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 0 10px;
                color: {COLORS['text_secondary']};
            """)
            self._refresh_cart()

            # Mostrar diálogo con opciones: imprimir, enviar por email, DIAN, finalizar
            post_dialog = PostSaleDialog(self, self.session, sale)
            post_dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar la venta:\n{e}")