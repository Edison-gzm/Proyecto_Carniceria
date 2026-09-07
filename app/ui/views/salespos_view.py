import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QPushButton, QScrollArea, QFrame, QTableWidget, 
    QTableWidgetItem, QHeaderView, QGridLayout, QLineEdit,
    QDialog, QDoubleSpinBox, QToolButton, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon
from services.product_service import ProductService, CategoryService
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
    pixmap = QPixmap(img_path)
    if pixmap.isNull():
        return QPixmap()
    w, h = pixmap.width(), pixmap.height()
    min_dim = min(w, h)
    x = (w - min_dim) // 2
    y = (h - min_dim) // 2
    cropped = pixmap.copy(x, y, min_dim, min_dim)
    return cropped.scaled(size, size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

def format_price(value) -> str:
    try:
        return f"${int(float(str(value))):,}".replace(",", ".")
    except Exception:
        return "$0"


class QuantityDialog(QDialog):
    """Ventana emergente para seleccionar los Kilos/Cantidad a vender."""
    def __init__(self, product_name, current_qty=1.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cantidad de Producto")
        self.setFixedSize(360, 230)
        self.setStyleSheet("background-color: #FFFFFF;")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        lbl = QLabel(f"Selecciona peso para:<br><span style='color:#2563EB; font-size:15px; font-weight:bold;'>{product_name}</span>")
        lbl.setTextFormat(Qt.RichText)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setFont(QFont("Segoe UI", 10))
        layout.addWidget(lbl)

        self.spin_qty = QDoubleSpinBox()
        self.spin_qty.setRange(0.05, 999.0)
        self.spin_qty.setSingleStep(0.5)
        self.spin_qty.setDecimals(2)
        self.spin_qty.setSuffix(" Kg")
        self.spin_qty.setValue(current_qty)
        self.spin_qty.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.spin_qty.setAlignment(Qt.AlignCenter)
        self.spin_qty.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #2563EB;
                border-radius: 8px;
                padding: 6px;
                color: #111111;
            }
        """)
        layout.addWidget(self.spin_qty)

        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(6)
        for weight in [0.5, 1.0, 2.0, 3.0]:
            btn = QPushButton(f"{weight} kg")
            btn.setFixedHeight(32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #F1F5F9; color: #1E293B; font-weight: bold; border-radius: 6px; border: 1px solid #CBD5E1; padding: 0 4px;
                }
                QPushButton:hover { background-color: #E2E8F0; }
            """)
            btn.clicked.connect(lambda _, w=weight: self.spin_qty.setValue(w))
            quick_layout.addWidget(btn)
        layout.addLayout(quick_layout)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setFixedHeight(36)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setStyleSheet("background-color: #94A3B8; color: white; font-weight: bold; border-radius: 6px; border: none;")
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("✔ Confirmar")
        btn_ok.setFixedHeight(36)
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setStyleSheet("background-color: #16A34A; color: white; font-weight: bold; border-radius: 6px; border: none;")
        btn_ok.clicked.connect(self.accept)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_ok)
        layout.addLayout(btn_box)

    def get_quantity(self):
        return self.spin_qty.value()


class SalesPosView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.app = getattr(main_window, 'app', main_window)
        self.session = self.app.session
        self.cart = {}
        self.selected_category_name = "Todas"
        self._build_ui()
        self._load_products()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(16)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(12)

        top_bar = QHBoxLayout()
        title = QLabel("Inicio — Punto de Venta")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS.get('text_primary', '#111111')};")
        top_bar.addWidget(title)
        top_bar.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar producto...")
        self.search_input.setFixedWidth(240)
        self.search_input.setFixedHeight(38)
        self.search_input.setFont(QFont("Segoe UI", 10))
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: #FFFFFF;
                color: #111111;
                border: 1px solid {COLORS.get('border', '#CBD5E1')};
                border-radius: 8px;
                padding: 0 10px;
            }}
            QLineEdit:focus {{ border: 2px solid #2563EB; }}
        """)
        self.search_input.textChanged.connect(self._load_products)
        top_bar.addWidget(self.search_input)
        left_layout.addLayout(top_bar)

        # Filtro de Categorías
        cat_scroll = QScrollArea()
        cat_scroll.setFixedHeight(80)
        cat_scroll.setWidgetResizable(True)
        cat_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        cat_container = QWidget()
        cat_bar = QHBoxLayout(cat_container)
        cat_bar.setContentsMargins(0, 0, 0, 0)
        cat_bar.setSpacing(10)

        self.cat_buttons = {}
        categories = [
            ("Todas", None),
            ("Carne de Vaca", CATEGORY_IMAGES.get("Carne de Vaca")),
            ("Carne de Cerdo", CATEGORY_IMAGES.get("Carne de Cerdo")),
            ("Pollo", CATEGORY_IMAGES.get("Pollo")),
            ("Embutidos", CATEGORY_IMAGES.get("Embutidos"))
        ]

        for name, img_path in categories:
            btn = QToolButton()
            btn.setFixedSize(68, 68)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setToolTip(name)

            if img_path and Path(img_path).exists():
                pixmap = get_square_pixmap(img_path, 52)
                btn.setIcon(QIcon(pixmap))
                btn.setIconSize(QSize(52, 52))
                btn.setToolButtonStyle(Qt.ToolButtonIconOnly)
            else:
                btn.setText(name)
                btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
                btn.setToolButtonStyle(Qt.ToolButtonTextOnly)

            btn.clicked.connect(lambda _, c=name: self._filter_category(c))
            self.cat_buttons[name] = btn
            cat_bar.addWidget(btn)

        cat_bar.addStretch()
        cat_scroll.setWidget(cat_container)
        left_layout.addWidget(cat_scroll)
        self._update_cat_buttons_style()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.products_container = QWidget()
        self.products_grid = QGridLayout(self.products_container)
        self.products_grid.setSpacing(12)
        self.products_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        scroll.setWidget(self.products_container)
        left_layout.addWidget(scroll)

        right_panel = QFrame()
        right_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.get('surface', '#FFFFFF')};
                border: 1px solid {COLORS.get('border', '#E2E8F0')};
                border-radius: 10px;
            }}
        """)
        cart_layout = QVBoxLayout(right_panel)
        cart_layout.setContentsMargins(12, 14, 12, 14)
        cart_layout.setSpacing(10)

        cart_title = QLabel("🛒 Lista de Compra")
        cart_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        cart_title.setStyleSheet("border: none; color: #111111;")
        cart_layout.addWidget(cart_title)

        self.cart_table = QTableWidget(0, 4)
        self.cart_table.setHorizontalHeaderLabels(["Producto", "Cant", "Subtotal", "Acciones"])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_table.setColumnWidth(1, 50)
        self.cart_table.setColumnWidth(2, 75)
        self.cart_table.setColumnWidth(3, 110)
        self.cart_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E2E8F0;
                gridline-color: #F1F5F9;
                font-size: 11px;
                color: #111111;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                font-weight: bold;
                color: #334155;
                border: none;
                padding: 4px;
            }
        """)
        cart_layout.addWidget(self.cart_table)

        self.total_label = QLabel("Total: $0")
        self.total_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.total_label.setStyleSheet("color: #16A34A; border: none;")
        self.total_label.setAlignment(Qt.AlignRight)
        cart_layout.addWidget(self.total_label)

        action_btn_box = QHBoxLayout()
        clear_btn = QPushButton("Vaciar Lista")
        clear_btn.setFixedHeight(38)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444; color: white; font-weight: bold; border-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #DC2626; }
        """)
        clear_btn.clicked.connect(self._clear_cart)

        process_btn = QPushButton("Procesar Venta")
        process_btn.setFixedHeight(38)
        process_btn.setCursor(Qt.PointingHandCursor)
        process_btn.setStyleSheet("""
            QPushButton {
                background-color: #16A34A; color: white; font-weight: bold; border-radius: 6px; border: none;
            }
            QPushButton:hover { background-color: #15803D; }
        """)
        # <-- CONEXIÓN AGREGADA -->
        process_btn.clicked.connect(self._process_sale)

        action_btn_box.addWidget(clear_btn)
        action_btn_box.addWidget(process_btn)
        cart_layout.addLayout(action_btn_box)

        main_layout.addLayout(left_layout, stretch=4)
        main_layout.addWidget(right_panel, stretch=6)

    def _filter_category(self, category_name):
        self.selected_category_name = category_name
        self._update_cat_buttons_style()
        self._load_products()

    def _update_cat_buttons_style(self):
        for name, btn in self.cat_buttons.items():
            if name == self.selected_category_name:
                btn.setStyleSheet("""
                    QToolButton {
                        background-color: #2563EB; color: white; border-radius: 10px; border: 2px solid #1D4ED8;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QToolButton {
                        background-color: #FFFFFF; color: #334155; border-radius: 10px; border: 1px solid #CBD5E1;
                    }
                    QToolButton:hover { background-color: #F8FAFC; border-color: #2563EB; }
                """)

    def _load_products(self):
        while self.products_grid.count():
            item = self.products_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.session.expire_all()
        service = ProductService(self.session)
        products = service.get_all(only_active=True)
        search_text = self.search_input.text().lower().strip()

        filtered = []
        for p in products:
            cat_name = p.category.name if p.category else "Sin Categoría"
            if (self.selected_category_name == "Todas" or cat_name.lower() == self.selected_category_name.lower()) and (search_text in p.name.lower()):
                filtered.append((p, cat_name))

        cols = 3
        for i, (product, cat_name) in enumerate(filtered):
            card = self._create_card(product, cat_name)
            self.products_grid.addWidget(card, i // cols, i % cols)

    def _create_card(self, product, category_name):
        card = QFrame()
        card.setFixedSize(190, 220)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.get('surface', '#FFFFFF')};
                border: 1px solid {COLORS.get('border', '#E2E8F0')};
                border-radius: 10px;
            }}
            QFrame:hover {{ border: 2px solid #2563EB; }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignCenter)

        img_path = CATEGORY_IMAGES.get(category_name, str(IMAGES_DIR / "vaca.jpg"))
        img_label = QLabel()
        pixmap = get_square_pixmap(img_path, 65)
        if not pixmap.isNull():
            img_label.setPixmap(pixmap)
        img_label.setStyleSheet("border: none;")
        layout.addWidget(img_label)

        name_lbl = QLabel(product.name)
        name_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        name_lbl.setStyleSheet("border: none; color: #111111;")
        name_lbl.setWordWrap(True)
        name_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_lbl)

        price_lbl = QLabel(format_price(product.price))
        price_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        price_lbl.setStyleSheet("color: #16A34A; border: none;")
        price_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(price_lbl)

        add_btn = QPushButton("+ Agregar")
        add_btn.setFixedHeight(32)
        add_btn.setFont(QFont("Segoe UI", 9, QFont.Bold))
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2563EB, stop:1 #1D4ED8);
                color: #FFFFFF;
                border-radius: 16px;
                border: none;
                padding: 0 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3B82F6, stop:1 #2563EB);
            }
        """)
        add_btn.clicked.connect(lambda _, p=product: self._prompt_and_add_to_cart(p))
        layout.addWidget(add_btn)

        return card

    def _prompt_and_add_to_cart(self, product):
        initial_qty = self.cart[product.id]['qty'] if product.id in self.cart else 1.0
        dialog = QuantityDialog(product.name, current_qty=initial_qty, parent=self)
        if dialog.exec():
            qty = dialog.get_quantity()
            self.cart[product.id] = {
                'product': product,
                'qty': qty,
                'subtotal': qty * float(product.price)
            }
            self._refresh_cart_ui()

    def _edit_item_qty(self, product_id):
        if product_id in self.cart:
            item = self.cart[product_id]
            dialog = QuantityDialog(item['product'].name, current_qty=item['qty'], parent=self)
            if dialog.exec():
                qty = dialog.get_quantity()
                if qty <= 0:
                    del self.cart[product_id]
                else:
                    item['qty'] = qty
                    item['subtotal'] = qty * float(item['product'].price)
                self._refresh_cart_ui()

    def _remove_from_cart(self, product_id):
        if product_id in self.cart:
            del self.cart[product_id]
            self._refresh_cart_ui()

    def _clear_cart(self):
        self.cart.clear()
        self._refresh_cart_ui()

    def _refresh_cart_ui(self):
        self.cart_table.setRowCount(0)
        total = 0.0

        for pid, item in self.cart.items():
            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)

            p_name = item['product'].name
            qty = item['qty']
            subtotal = item['subtotal']
            total += subtotal

            qty_str = f"{qty:g}k" if qty < 100 else f"{int(qty)}k"

            self.cart_table.setItem(row, 0, QTableWidgetItem(p_name))
            self.cart_table.setItem(row, 1, QTableWidgetItem(qty_str))
            self.cart_table.setItem(row, 2, QTableWidgetItem(format_price(subtotal)))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(4)

            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Editar Cantidad")
            edit_btn.setFixedSize(28, 24)
            edit_btn.setCursor(Qt.PointingHandCursor)
            edit_btn.setStyleSheet("""
                QPushButton { background-color: #3B82F6; color: white; border-radius: 4px; border: none; font-size: 11px; }
                QPushButton:hover { background-color: #2563EB; }
            """)
            edit_btn.clicked.connect(lambda _, p_id=pid: self._edit_item_qty(p_id))

            del_btn = QPushButton("Eliminar")
            del_btn.setToolTip("Quitar del Carrito")
            del_btn.setFixedHeight(24)
            del_btn.setFont(QFont("Segoe UI", 8, QFont.Bold))
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet("""
                QPushButton { background-color: #EF4444; color: white; border-radius: 4px; border: none; padding: 0 4px; }
                QPushButton:hover { background-color: #DC2626; }
            """)
            del_btn.clicked.connect(lambda _, p_id=pid: self._remove_from_cart(p_id))

            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(del_btn)
            self.cart_table.setCellWidget(row, 3, actions_widget)

        self.total_label.setText(f"Total: {format_price(total)}")

    def _process_sale(self):
        """Procesa la venta actual y la guarda en la base de datos."""
        if not self.cart:
            QMessageBox.warning(self, "Carrito Vacío", "No hay productos en la lista para procesar la venta.")
            return

        total_amount = sum(item['subtotal'] for item in self.cart.values())

        reply = QMessageBox.question(
            self,
            "Confirmar Venta",
            f"¿Desea completar la venta por un total de {format_price(total_amount)}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            # 1. Intentar usar SaleService si está disponible
            try:
                from services.sale_service import SaleService
                sale_service = SaleService(self.session)
                
                items = [
                    {
                        'product_id': pid,
                        'quantity': item['qty'],
                        'unit_price': float(item['product'].price),
                        'subtotal': item['subtotal']
                    }
                    for pid, item in self.cart.items()
                ]
                
                current_user_id = getattr(self.app.current_user, 'id', None)
                sale_service.create_sale(
                    user_id=current_user_id,
                    items=items,
                    total=total_amount
                )
            except (ImportError, AttributeError):
                # 2. Si no existe SaleService, registrar directamente con el modelo Sale/SaleDetail
                from database.models.sale import Sale, SaleDetail
                
                current_user_id = getattr(self.app.current_user, 'id', None)
                new_sale = Sale(
                    user_id=current_user_id,
                    total=total_amount
                )
                self.session.add(new_sale)
                self.session.flush()

                for pid, item in self.cart.items():
                    detail = SaleDetail(
                        sale_id=new_sale.id,
                        product_id=pid,
                        quantity=item['qty'],
                        unit_price=float(item['product'].price),
                        subtotal=item['subtotal']
                    )
                    self.session.add(detail)
                    
                    # Descontar stock si el modelo Product tiene el atributo stock
                    product = item['product']
                    if hasattr(product, 'stock') and product.stock is not None:
                        product.stock -= item['qty']

                self.session.commit()

            QMessageBox.information(self, "Venta Exitosa", "¡La venta se ha registrado correctamente!")
            self._clear_cart()

        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Error al procesar venta", f"No se pudo registrar la venta:\n{str(e)}")