from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QMessageBox, QFrame, QTextEdit, QDoubleSpinBox, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from decimal import Decimal

from database.models.cash_register import CashRegisterStatus


class CashRegisterView(QWidget):
    def __init__(self, session, current_user_id: int):
        super().__init__()
        self.session = session
        self.current_user_id = current_user_id
        
        # Importamos diferido para evitar ciclos de importación si fuera necesario
        from services.cash_register_service import CashRegisterService
        self.service = CashRegisterService(self.session)

        self.current_register = None
        self.init_ui()
        self.refresh_view()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # 1. Título
        title = QLabel("Gestión y Arqueo de Caja")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_layout.addWidget(title)

        # 2. Panel Superior Dinámico (Apertura o Cierre)
        self.status_container = QWidget()
        self.status_layout = QVBoxLayout(self.status_container)
        self.status_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.status_container)

        # 3. Sección de Historial
        history_group = QGroupBox("Historial de Cajas")
        history_layout = QVBoxLayout(history_group)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "ID", "Usuario", "Apertura", "Cierre", 
            "M. Inicial", "Ventas", "Cierre Real", "Diferencia"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.history_table)

        main_layout.addWidget(history_group)

    def refresh_view(self):
        """Refresca el estado actual de la caja y la tabla de historial."""
        self.current_register = self.service.get_open()
        
        # Limpiar el panel superior dinámico
        for i in reversed(range(self.status_layout.count())):
            widget = self.status_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if self.current_register:
            self._build_open_register_ui()
        else:
            self._build_closed_register_ui()

        self.load_history()

    def _build_closed_register_ui(self):
        """Interfaz cuando la caja está CERRADA (Formulario de Apertura)."""
        box = QGroupBox("Apertura de Caja")
        layout = QGridLayout(box)

        status_lbl = QLabel("ESTADO: CAJA CERRADA")
        status_lbl.setStyleSheet("color: #d9534f; font-weight: bold; font-size: 14px;")
        layout.addWidget(status_lbl, 0, 0, 1, 2)

        layout.addWidget(QLabel("Monto Inicial en Efectivo ($):"), 1, 0)
        self.opening_amount_spin = QDoubleSpinBox()
        self.opening_amount_spin.setRange(0, 10000000)
        self.opening_amount_spin.setDecimals(2)
        self.opening_amount_spin.setPrefix("$ ")
        layout.addWidget(self.opening_amount_spin, 1, 1)

        btn_open = QPushButton("Abrir Caja")
        btn_open.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 8px;")
        btn_open.clicked.connect(self.handle_open_register)
        layout.addWidget(btn_open, 2, 0, 1, 2)

        self.status_layout.addWidget(box)

    def _build_open_register_ui(self):
        """Interfaz cuando la caja está ABIERTA (Resumen + Arqueo)."""
        box = QGroupBox("Caja Activa (Turno en curso)")
        layout = QGridLayout(box)

        # Calcular totales actuales
        current_sales = self.service.get_current_sales_total(self.current_register.id)
        opening = self.current_register.opening_amount
        expected_total = opening + current_sales

        # Info general
        lbl_info = QLabel(
            f"<b>Abierta por:</b> ID Usuario {self.current_register.user_id} | "
            f"<b>Fecha:</b> {self.current_register.opened_at.strftime('%Y-%m-%d %H:%M')}"
        )
        layout.addWidget(lbl_info, 0, 0, 1, 2)

        # Resumen dinámico
        summary_text = (
            f"<b>Monto Inicial:</b> ${opening:,.2f} | "
            f"<b>Ventas Turno:</b> ${current_sales:,.2f} | "
            f"<b>Total Esperado en Caja:</b> <span style='color: #0275d8;'>${expected_total:,.2f}</span>"
        )
        lbl_summary = QLabel(summary_text)
        lbl_summary.setStyleSheet("font-size: 13px; margin: 10px 0;")
        layout.addWidget(lbl_summary, 1, 0, 1, 2)

        # Cierre y Arqueo
        layout.addWidget(QLabel("Monto Físico Contado en Caja ($):"), 2, 0)
        self.closing_amount_spin = QDoubleSpinBox()
        self.closing_amount_spin.setRange(0, 10000000)
        self.closing_amount_spin.setDecimals(2)
        self.closing_amount_spin.setPrefix("$ ")
        self.closing_amount_spin.setValue(float(expected_total))
        layout.addWidget(self.closing_amount_spin, 2, 1)

        layout.addWidget(QLabel("Notas / Observaciones:"), 3, 0)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("Ej. Se realizó retiro de $50.000 para pago de flete...")
        layout.addWidget(self.notes_edit, 3, 1)

        btn_close = QPushButton("Realizar Arqueo y Cerrar Caja")
        btn_close.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold; padding: 8px;")
        btn_close.clicked.connect(self.handle_close_register)
        layout.addWidget(btn_close, 4, 0, 1, 2)

        self.status_layout.addWidget(box)

    def handle_open_register(self):
        monto = self.opening_amount_spin.value()
        try:
            self.service.open_register(user_id=self.current_user_id, opening_amount=monto)
            QMessageBox.information(self, "Éxito", "Caja abierta correctamente.")
            self.refresh_view()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la caja: {str(e)}")

    def handle_close_register(self):
        monto_real = self.closing_amount_spin.value()
        notas = self.notes_edit.toPlainText()

        confirm = QMessageBox.question(
            self, "Confirmar Cierre", 
            "¿Estás seguro de que deseas cerrar la caja actual?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                closed = self.service.close_register(
                    register_id=self.current_register.id,
                    closing_amount=monto_real,
                    notes=notas
                )
                
                diff_msg = ""
                if closed.difference != 0:
                    diff_msg = f"\n\nDiferencia detectada: ${closed.difference:,.2f}"

                QMessageBox.information(
                    self, "Caja Cerrada", 
                    f"Caja cerrada exitosamente.{diff_msg}"
                )
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al cerrar la caja: {str(e)}")

    def load_history(self):
        """Carga el historial de cajas en la tabla."""
        history = self.service.get_history(limit=20)
        self.history_table.setRowCount(len(history))

        for row, reg in enumerate(history):
            self.history_table.setItem(row, 0, QTableWidgetItem(str(reg.id)))
            self.history_table.setItem(row, 1, QTableWidgetItem(str(reg.user_id)))
            self.history_table.setItem(
                row, 2, QTableWidgetItem(reg.opened_at.strftime("%d/%m/%Y %H:%M") if reg.opened_at else "")
            )
            self.history_table.setItem(
                row, 3, QTableWidgetItem(reg.closed_at.strftime("%d/%m/%Y %H:%M") if reg.closed_at else "ABIERTA")
            )
            self.history_table.setItem(row, 4, QTableWidgetItem(f"${reg.opening_amount:,.2f}"))
            self.history_table.setItem(row, 5, QTableWidgetItem(f"${reg.total_sales:,.2f}"))
            
            cierre = f"${reg.closing_amount:,.2f}" if reg.closing_amount is not None else "-"
            self.history_table.setItem(row, 6, QTableWidgetItem(cierre))

            diff = f"${reg.difference:,.2f}" if reg.difference is not None else "-"
            diff_item = QTableWidgetItem(diff)
            
            # Pintar diferencia en rojo si faltó o sobró dinero
            if reg.difference and reg.difference != 0:
                diff_item.setForeground(Qt.GlobalColor.red)
            
            self.history_table.setItem(row, 7, diff_item)