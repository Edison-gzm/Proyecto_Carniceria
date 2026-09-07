import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from database.models import Sale
from services.invoice_service import InvoiceService
from ui.theme import COLORS


def format_price(value) -> str:
    try:
        return f"${int(float(str(value))):,}".replace(",", ".")
    except Exception:
        return "$0"


class SaleDetailDialog(QDialog):
    """Diálogo modal para visualizar los detalles e ítems de una venta."""
    def __init__(self, parent, session, sale):
        super().__init__(parent)
        self.session = session
        self.sale = sale
        self.setWindowTitle(f"Detalle de Venta #{sale.id}")
        self.setFixedSize(550, 480)
        self.setStyleSheet(f"background-color: {COLORS['secondary']}; color: {COLORS['text_primary']};")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        invoice_num = getattr(self.sale, 'invoice_number', f"VTA-{self.sale.id}")
        title = QLabel(f"Factura: {invoice_num}")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        layout.addWidget(title)

        # Información general
        customer_name = "Consumidor Final"
        if hasattr(self.sale, 'customer') and self.sale.customer:
            customer_name = getattr(self.sale.customer, 'full_name', getattr(self.sale.customer, 'name', 'Cliente'))

        created = getattr(self.sale, 'created_at', None)
        date_str = created.strftime("%d/%m/%Y %H:%M:%S") if created else "N/A"

        info_lbl = QLabel(
            f"Fecha: {date_str}\n"
            f"Cliente: {customer_name}\n"
            f"Método Pago: {getattr(self.sale, 'payment_method', 'Efectivo')}\n"
            f"Estado: {getattr(self.sale, 'status', 'CLOSED')}"
        )
        info_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(info_lbl)

        # Tabla de items
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Producto", "Cant.", "P. Unitario", "Subtotal"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                gridline-color: {COLORS['border']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_secondary']};
                padding: 6px; font-weight: bold;
            }}
        """)

        items = getattr(self.sale, 'items', [])
        table.setRowCount(len(items))

        for row, item in enumerate(items):
            p_name = "Producto"
            if hasattr(item, 'product') and item.product:
                p_name = item.product.name
            
            qty = getattr(item, 'quantity', 0)
            unit_price = getattr(item, 'unit_price', 0.0)
            subtotal = getattr(item, 'subtotal', qty * unit_price)

            table.setItem(row, 0, QTableWidgetItem(str(p_name)))
            
            item_qty = QTableWidgetItem(str(qty))
            item_qty.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 1, item_qty)

            item_price = QTableWidgetItem(format_price(unit_price))
            item_price.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row, 2, item_price)

            item_sub = QTableWidgetItem(format_price(subtotal))
            item_sub.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(row, 3, item_sub)

        layout.addWidget(table)

        # Total
        total_lbl = QLabel(f"Total: {format_price(getattr(self.sale, 'total', 0.0))}")
        total_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        total_lbl.setAlignment(Qt.AlignRight)
        layout.addWidget(total_lbl)

        # Acciones
        btn_layout = QHBoxLayout()
        print_btn = QPushButton("🖨 Imprimir Factura")
        print_btn.setFixedHeight(38)
        print_btn.clicked.connect(self._print_invoice)

        close_btn = QPushButton("Cerrar")
        close_btn.setFixedHeight(38)
        close_btn.clicked.connect(self.accept)

        btn_layout.addWidget(print_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _print_invoice(self):
        try:
            service = InvoiceService(self.session)
            service.print_invoice(self.sale.id)
            QMessageBox.information(self, "Éxito", "Factura enviada a la impresora.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo imprimir:\n{e}")


class SalesView(QWidget):
    """Vista de Historial de Ventas."""
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.session = app.session
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Encabezado
        title = QLabel("Historial de Ventas")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        # Barra de Búsqueda y Acciones
        top_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por Factura ID o Nombre de Cliente...")
        self.search_input.setFixedHeight(40)
        self.search_input.textChanged.connect(self._apply_filter)
        top_bar.addWidget(self.search_input)

        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.setFixedHeight(40)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 0 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {COLORS['border']}; }}
        """)
        refresh_btn.clicked.connect(self.refresh_data)
        top_bar.addWidget(refresh_btn)
        layout.addLayout(top_bar)

        # Tabla Principal de Ventas
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(7)
        self.sales_table.setHorizontalHeaderLabels([
            "ID Venta", "N° Factura", "Fecha / Hora", "Cliente", "Método Pago", "Total", "Estado"
        ])
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sales_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sales_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.sales_table.setAlternatingRowColors(True)
        self.sales_table.doubleClicked.connect(self._show_sale_details)
        self.sales_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                gridline-color: {COLORS['border']};
                font-size: 13px;
            }}
            QTableWidget::item {{ padding: 8px; color: {COLORS['text_primary']}; }}
            QTableWidget::item:selected {{ background-color: {COLORS['primary']}; }}
            QHeaderView::section {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_secondary']};
                padding: 10px; border: none; font-weight: bold;
            }}
        """)
        layout.addWidget(self.sales_table)

        hint = QLabel("Doble clic en cualquier registro para ver el detalle de la venta e imprimir la factura.")
        hint.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

    def refresh_data(self):
        """Consulta la base de datos y carga todas las ventas."""
        sales = self.session.query(Sale).order_by(Sale.id.desc()).all()
        self.all_sales = sales
        self._populate_table(sales)

    def _populate_table(self, sales_list):
        self.sales_table.setRowCount(0)

        for row, sale in enumerate(sales_list):
            self.sales_table.insertRow(row)

            # ID
            item_id = QTableWidgetItem(str(sale.id))
            item_id.setTextAlignment(Qt.AlignCenter)
            item_id.setData(Qt.UserRole, sale.id)
            self.sales_table.setItem(row, 0, item_id)

            # Factura
            invoice = getattr(sale, 'invoice_number', f"VTA-{sale.id}")
            item_inv = QTableWidgetItem(str(invoice))
            item_inv.setTextAlignment(Qt.AlignCenter)
            self.sales_table.setItem(row, 1, item_inv)

            # Fecha / Hora
            created = getattr(sale, 'created_at', None)
            date_str = created.strftime("%d/%m/%Y %H:%M") if created else "N/A"
            item_date = QTableWidgetItem(date_str)
            item_date.setTextAlignment(Qt.AlignCenter)
            self.sales_table.setItem(row, 2, item_date)

            # Cliente
            customer_name = "Consumidor Final"
            if hasattr(sale, 'customer') and sale.customer:
                customer_name = getattr(sale.customer, 'full_name', getattr(sale.customer, 'name', 'Cliente'))
            self.sales_table.setItem(row, 3, QTableWidgetItem(customer_name))

            # Método de Pago
            metodo = getattr(sale, 'payment_method', 'Efectivo')
            item_pago = QTableWidgetItem(str(metodo))
            item_pago.setTextAlignment(Qt.AlignCenter)
            self.sales_table.setItem(row, 4, item_pago)

            # Total
            total = getattr(sale, 'total', 0.0)
            item_total = QTableWidgetItem(format_price(total))
            item_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.sales_table.setItem(row, 5, item_total)

            # Estado
            status = getattr(sale, 'status', 'CLOSED')
            item_status = QTableWidgetItem(str(status))
            item_status.setTextAlignment(Qt.AlignCenter)
            self.sales_table.setItem(row, 6, item_status)

    def _apply_filter(self, query):
        """Filtra la lista de ventas según el texto ingresado."""
        query = query.strip().lower()
        if not query:
            self._populate_table(self.all_sales)
            return

        filtered = []
        for sale in self.all_sales:
            invoice = str(getattr(sale, 'invoice_number', '')).lower()
            sale_id = str(sale.id)
            customer_name = ""
            if hasattr(sale, 'customer') and sale.customer:
                customer_name = getattr(sale.customer, 'full_name', getattr(sale.customer, 'name', '')).lower()

            if query in invoice or query in sale_id or query in customer_name:
                filtered.append(sale)

        self._populate_table(filtered)

    def _show_sale_details(self):
        row = self.sales_table.currentRow()
        if row < 0:
            return

        sale_id = self.sales_table.item(row, 0).data(Qt.UserRole)
        sale = self.session.query(Sale).get(sale_id)
        if sale:
            dialog = SaleDetailDialog(self, self.session, sale)
            dialog.exec()