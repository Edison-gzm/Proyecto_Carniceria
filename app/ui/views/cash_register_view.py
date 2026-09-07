from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from sqlalchemy import func

from ui.theme import COLORS
from database.models import CashRegister, Sale


def _get_model_field(obj, *field_names, default=None):
    """Obtiene el valor del primer campo disponible en el objeto."""
    for field in field_names:
        if hasattr(obj, field) and getattr(obj, field) is not None:
            return getattr(obj, field)
    return default


def _set_model_field(obj, field_names, value):
    """Asigna un valor al primer campo de la lista que exista en el objeto."""
    for field in field_names:
        if hasattr(obj, field):
            setattr(obj, field, value)
            return True
    return False


class CashRegisterView(QWidget):
    def __init__(self, session, current_user_id):
        super().__init__()
        self.session = session
        self.current_user_id = current_user_id
        self.active_register = None

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título principal
        title = QLabel("Gestión y Arqueo de Caja")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        # Panel Estado de Caja
        self.box_status = QGroupBox("Caja Activa (Turno en curso)")
        self.box_status.setStyleSheet(f"""
            QGroupBox {{
                font-size: 13px;
                font-weight: bold;
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: {COLORS['surface']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        status_layout = QVBoxLayout(self.box_status)
        status_layout.setSpacing(12)

        # Información de Apertura
        self.lbl_info = QLabel("Estado: Cargando...")
        self.lbl_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        status_layout.addWidget(self.lbl_info)

        # Totales
        self.lbl_totals = QLabel("Monto Inicial: $0.00  |  Ventas Turno: $0.00  |  Total Esperado: $0.00")
        self.lbl_totals.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.lbl_totals.setStyleSheet(f"color: {COLORS['primary']};")
        status_layout.addWidget(self.lbl_totals)

        # Entrada Monto Físico
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Monto Físico Contado en Caja ($):"))
        self.input_physical_amount = QLineEdit()
        self.input_physical_amount.setPlaceholderText("0.00")
        self.input_physical_amount.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
                background-color: {COLORS['surface_light']};
            }}
        """)
        form_layout.addWidget(self.input_physical_amount)
        status_layout.addLayout(form_layout)

        # Observaciones
        obs_layout = QHBoxLayout()
        obs_layout.addWidget(QLabel("Notas / Observaciones:"))
        self.input_notes = QLineEdit()
        self.input_notes.setPlaceholderText("Ej. Arqueo correcto / Retiro de dinero...")
        self.input_notes.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 13px;
                background-color: {COLORS['surface_light']};
            }}
        """)
        obs_layout.addWidget(self.input_notes)
        status_layout.addLayout(obs_layout)

        # Botón Acción
        self.btn_action = QPushButton("Realizar Arqueo y Cerrar Caja")
        self.btn_action.setFixedHeight(40)
        self.btn_action.setCursor(Qt.PointingHandCursor)
        self.btn_action.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn_action.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']};
                color: white;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: #c82333;
            }}
        """)
        self.btn_action.clicked.connect(self._handle_cash_action)
        status_layout.addWidget(self.btn_action)

        layout.addWidget(self.box_status)

        # --- SECCIÓN: VENTAS DEL TURNO ACTIVO ---
        sales_group = QGroupBox("Ventas del Turno / Día")
        sales_group.setStyleSheet(self.box_status.styleSheet())
        
        sales_layout = QVBoxLayout(sales_group)

        self.table_sales = QTableWidget()
        self.table_sales.setColumnCount(5)
        self.table_sales.setHorizontalHeaderLabels(["ID Venta", "Hora", "Cliente", "Método Pago", "Total"])
        self.table_sales.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_sales.setAlternatingRowColors(True)
        self.table_sales.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['surface']};
                gridline-color: {COLORS['border']};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_primary']};
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                padding: 4px;
            }}
        """)
        sales_layout.addWidget(self.table_sales)
        layout.addWidget(sales_group)

    def refresh_data(self):
        """Refresca el estado de la caja y carga las ventas del turno."""
        # 1. Buscar si hay una caja abierta
        self.active_register = (
            self.session.query(CashRegister)
            .filter(CashRegister.status == "OPEN")
            .order_by(CashRegister.id.desc())
            .first()
        )

        if not self.active_register:
            self._ui_state_no_register()
            return

        # 2. Obtener fecha de apertura y monto inicial
        opened_at = _get_model_field(self.active_register, "opened_at", "opening_date", "created_at")
        initial_amount = _get_model_field(self.active_register, "opening_amount", "initial_amount", "initial_balance", default=0.0)

        # 3. Consultar las ventas asociadas a esta caja o por fecha de apertura
        sales_query = self.session.query(Sale)
        
        if hasattr(Sale, 'cash_register_id'):
            sales_query = sales_query.filter(Sale.cash_register_id == self.active_register.id)
        elif opened_at:
            sales_query = sales_query.filter(Sale.created_at >= opened_at)

        # Corrección: Filtrar por estado CLOSED en lugar de COMPLETED
        if hasattr(Sale, 'status'):
            sales_query = sales_query.filter(Sale.status == 'CLOSED')

        total_sales = sales_query.with_entities(func.sum(Sale.total)).scalar() or 0.0
        expected_total = float(initial_amount) + float(total_sales)

        # 4. Actualizar etiquetas
        opened_str = opened_at.strftime("%d/%m/%Y %H:%M:%S") if opened_at else "N/A"
        self.lbl_info.setText(f"Abierta por: Usuario #{self.active_register.user_id}  |  Hora Apertura (Local PC): {opened_str}")
        self.lbl_totals.setText(
            f"Monto Inicial: ${initial_amount:,.2f}  |  "
            f"Ventas Turno: ${total_sales:,.2f}  |  "
            f"Total Esperado: ${expected_total:,.2f}"
        )

        self.btn_action.setText("Realizar Arqueo y Cerrar Caja")
        self.btn_action.setStyleSheet(f"background-color: {COLORS['danger']}; color: white; border-radius: 6px;")
        self.input_physical_amount.setEnabled(True)
        self.input_notes.setEnabled(True)

        # 5. Cargar tabla de ventas del turno
        self._load_turn_sales(sales_query.all())

    def _ui_state_no_register(self):
        """Estado cuando la caja está cerrada."""
        self.lbl_info.setText("Caja Actualmente CERRADA. Inicie un nuevo turno.")
        self.lbl_totals.setText("Monto Inicial: $0.00  |  Ventas Turno: $0.00  |  Total Esperado: $0.00")
        self.btn_action.setText("🔓 Abrir Nueva Caja / Turno")
        self.btn_action.setStyleSheet(f"background-color: {COLORS['success']}; color: white; border-radius: 6px;")
        self.input_physical_amount.setEnabled(False)
        self.input_notes.setEnabled(False)
        self.table_sales.setRowCount(0)

    def _load_turn_sales(self, sales_list):
        """Carga el detalle de las ventas en la tabla."""
        self.table_sales.setRowCount(0)

        for row, sale in enumerate(sales_list):
            self.table_sales.insertRow(row)

            item_id = QTableWidgetItem(str(sale.id))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table_sales.setItem(row, 0, item_id)

            created = getattr(sale, 'created_at', None)
            hora_str = created.strftime("%H:%M:%S") if created else "N/A"
            item_hora = QTableWidgetItem(hora_str)
            item_hora.setTextAlignment(Qt.AlignCenter)
            self.table_sales.setItem(row, 1, item_hora)

            cliente_nombre = "Cliente General"
            if hasattr(sale, 'customer') and sale.customer:
                cliente_nombre = getattr(sale.customer, 'full_name', getattr(sale.customer, 'name', 'Cliente'))
            item_cliente = QTableWidgetItem(cliente_nombre)
            self.table_sales.setItem(row, 2, item_cliente)

            metodo = getattr(sale, 'payment_method', 'Efectivo')
            item_pago = QTableWidgetItem(str(metodo))
            item_pago.setTextAlignment(Qt.AlignCenter)
            self.table_sales.setItem(row, 3, item_pago)

            total_val = getattr(sale, 'total', 0.0)
            item_total = QTableWidgetItem(f"${total_val:,.2f}")
            item_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_sales.setItem(row, 4, item_total)

    def _handle_cash_action(self):
        if not self.active_register:
            self._open_register()
        else:
            self._close_register()

    def _open_register(self):
        now_local = datetime.now()
        cols = [c.key for c in CashRegister.__table__.columns]
        
        kwargs = {
            "user_id": self.current_user_id,
            "status": "OPEN"
        }

        if "opened_at" in cols:
            kwargs["opened_at"] = now_local
        elif "opening_date" in cols:
            kwargs["opening_date"] = now_local

        for col_name in ["opening_amount", "initial_amount", "initial_balance", "opening_balance"]:
            if col_name in cols:
                kwargs[col_name] = 0.0
                break

        new_reg = CashRegister(**kwargs)
        self.session.add(new_reg)
        self.session.commit()

        QMessageBox.information(self, "Caja Abierta", f"Se ha abierto la caja con éxito a las {now_local.strftime('%H:%M:%S')}.")
        self.refresh_data()

    def _close_register(self):
        physical_text = self.input_physical_amount.text().strip()
        if not physical_text:
            QMessageBox.warning(self, "Atención", "Por favor ingrese el monto físico contado en caja.")
            return

        try:
            physical_amount = float(physical_text)
        except ValueError:
            QMessageBox.warning(self, "Atención", "El monto físico debe ser un número válido.")
            return

        reply = QMessageBox.question(
            self,
            "Confirmar Cierre de Caja",
            "¿Está seguro de que desea realizar el arqueo y cerrar el turno?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            now_local = datetime.now()

            _set_model_field(self.active_register, ["closed_at", "closing_date"], now_local)
            _set_model_field(self.active_register, ["closing_amount", "final_amount", "closing_balance"], physical_amount)
            _set_model_field(self.active_register, ["notes", "observations"], self.input_notes.text().strip())
            self.active_register.status = "CLOSED"

            self.session.commit()
            QMessageBox.information(self, "Caja Cerrada", "El arqueo de caja se ha realizado exitosamente.")
            
            self.input_physical_amount.clear()
            self.input_notes.clear()
            self.refresh_data()