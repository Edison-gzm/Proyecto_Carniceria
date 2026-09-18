from datetime import datetime
from decimal import Decimal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.theme import COLORS
from database.models import CashRegister, Sale
from services.cash_register_service import CashRegisterService


def _get_model_field(obj, *field_names, default=None):
    for field in field_names:
        if hasattr(obj, field) and getattr(obj, field) is not None:
            return getattr(obj, field)
    return default


class CashRegisterView(QWidget):
    def __init__(self, session, current_user_id):
        super().__init__()
        self.session = session
        self.current_user_id = current_user_id
        self.active_register = None
        self.cash_service = CashRegisterService(session)

        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

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

        self.lbl_info = QLabel("Estado: Cargando...")
        self.lbl_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        status_layout.addWidget(self.lbl_info)

        # Recuadro simplificado solo con Ventas Totales del Turno
        self.lbl_totals = QLabel("Total Ventas del Turno: $0.00")
        self.lbl_totals.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.lbl_totals.setStyleSheet(f"""
            color: {COLORS['primary']}; 
            background-color: {COLORS['surface_light']}; 
            padding: 12px; 
            border-radius: 6px;
            border: 1px solid {COLORS['border']};
        """)
        status_layout.addWidget(self.lbl_totals)

        # Botones de Acción (Traer y Cerrar Caja)
        buttons_layout = QHBoxLayout()
        
        self.btn_fetch = QPushButton("🔄 Traer / Actualizar Datos")
        self.btn_fetch.setFixedHeight(40)
        self.btn_fetch.setCursor(Qt.PointingHandCursor)
        self.btn_fetch.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn_fetch.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: #1d4ed8; }}
        """)
        self.btn_fetch.clicked.connect(self.refresh_data)
        buttons_layout.addWidget(self.btn_fetch)

        self.btn_action = QPushButton("Realizar Cierre de Caja")
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
            QPushButton:hover {{ background-color: #c82333; }}
        """)
        self.btn_action.clicked.connect(self._handle_cash_action)
        buttons_layout.addWidget(self.btn_action)

        status_layout.addLayout(buttons_layout)
        layout.addWidget(self.box_status)

        # --- SECCIÓN: VENTAS DEL TURNO ACTUAL ---
        sales_group = QGroupBox("Corte de Caja / Detalle de Ventas del Turno")
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
        """Refresca y trae los datos actuales del turno. Si está cerrada, la abre automáticamente."""
        self.active_register = self.cash_service.get_open()

        # SEGURIDAD AUTOMÁTICA: Si no hay caja abierta, la abre de inmediato de forma transparente
        if not self.active_register:
            try:
                self.cash_service.open_register(user_id=self.current_user_id, opening_amount=0.0)
                self.active_register = self.cash_service.get_open()
            except Exception:
                pass

        if not self.active_register:
            self._ui_state_no_register()
            return

        opened_at = _get_model_field(self.active_register, "opened_at", "opening_date", "created_at")

        # Consultar ventas del turno activo
        sales_query = self.session.query(Sale)
        if hasattr(Sale, 'cash_register_id'):
            sales_query = sales_query.filter(Sale.cash_register_id == self.active_register.id)
        elif opened_at:
            sales_query = sales_query.filter(Sale.created_at >= opened_at)

        if hasattr(Sale, 'status'):
            sales_query = sales_query.filter(Sale.status == 'CLOSED')

        sales_list = sales_query.all()
        total_sales = float(sum(s.total for s in sales_list))

        # Mostrar la información del turno en curso
        opened_str = opened_at.strftime("%d/%m/%Y %H:%M:%S") if opened_at else "N/A"
        self.lbl_info.setText(f"Abierta por: Usuario #{self.active_register.user_id}  |  Hora Apertura: {opened_str}")
        self.lbl_totals.setText(f"Total Ventas del Turno: ${total_sales:,.2f}")

        self.btn_action.setEnabled(True)
        self.btn_action.setText("🔒 Realizar Cierre de Caja")
        self.btn_action.setStyleSheet(f"background-color: {COLORS['danger']}; color: white; border-radius: 6px;")

        self._load_turn_sales(sales_list)

    def _ui_state_no_register(self):
        self.lbl_info.setText("Caja en proceso de inicialización automática...")
        self.lbl_totals.setText("Total Ventas del Turno: $0.00")
        self.table_sales.setRowCount(0)

    def _load_turn_sales(self, sales_list):
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
        # Al presionar el botón de cierre, ejecutamos directamente el cierre y apertura automática
        self._close_register()

    def _close_register(self):
        if not self.active_register:
            self.refresh_data()
            return

        reply = QMessageBox.question(
            self,
            "Confirmar Cierre de Caja",
            "¿Desea realizar el corte y cierre del turno actual? Se guardarán las ventas y se abrirá un nuevo turno de inmediato.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # 1. Obtenemos las ventas del turno actual para calcular el cierre
                sales_query = self.session.query(Sale).filter(Sale.cash_register_id == self.active_register.id)
                if hasattr(Sale, 'status'):
                    sales_query = sales_query.filter(Sale.status == 'CLOSED')
                total_sales = float(sum(s.total for s in sales_query.all()))

                # 2. Cerramos la caja actual con el total acumulado
                self.cash_service.close_register(
                    register_id=self.active_register.id,
                    closing_amount=total_sales,
                    notes="Corte y cierre automático por sistema"
                )

                # 3. ¡Abrimos inmediatamente el nuevo turno de forma automática!
                self.cash_service.open_register(user_id=self.current_user_id, opening_amount=0.0)

                QMessageBox.information(
                    self, 
                    "Corte Exitoso", 
                    "El turno se ha cerrado y se ha iniciado una nueva caja de manera automática."
                )
                
                # 4. Refrescamos los datos para mostrar el nuevo turno limpio en pantalla
                self.refresh_data()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo completar el proceso de cierre y apertura: {str(e)}")