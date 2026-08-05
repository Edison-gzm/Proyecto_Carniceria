import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from database.session import get_session
from services.customer_service import CustomerService
from ui.theme import COLORS


class CustomerDialog(QDialog):
    """Diálogo para crear y editar clientes."""

    def __init__(self, parent, session, customer=None):
        super().__init__(parent)
        self.session = session
        self.customer = customer
        self.is_edit = customer is not None
        self.setWindowTitle("Editar Cliente" if self.is_edit else "Nuevo Cliente")
        self.setFixedSize(420, 360)
        self.setStyleSheet(f"background-color: {COLORS['secondary']}; color: {COLORS['text_primary']};")
        self._build_ui()
        if self.is_edit:
            self._fill_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Editar Cliente" if self.is_edit else "Nuevo Cliente")
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Juan Pérez")
        self.name_input.setFixedHeight(40)
        self.name_input.returnPressed.connect(self._save)
        form.addRow("Nombre completo *:", self.name_input)

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Ej: 1234567890")
        self.id_input.setFixedHeight(40)
        self.id_input.returnPressed.connect(self._save)
        form.addRow("Cédula / NIT:", self.id_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Ej: 3001234567")
        self.phone_input.setFixedHeight(40)
        self.phone_input.returnPressed.connect(self._save)
        form.addRow("Teléfono:", self.phone_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Ej: correo@ejemplo.com")
        self.email_input.setFixedHeight(40)
        self.email_input.returnPressed.connect(self._save)
        form.addRow("Email:", self.email_input)

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
            QPushButton:hover {{ background-color: {COLORS['border']}; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Guardar")
        self.save_btn.setFixedHeight(40)
        self.save_btn.clicked.connect(self._save)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def _fill_data(self):
        self.name_input.setText(self.customer.full_name)
        self.id_input.setText(self.customer.id_number or "")
        self.phone_input.setText(self.customer.phone or "")
        self.email_input.setText(self.customer.email or "")

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
            return

        service = CustomerService(self.session)
        try:
            if self.is_edit:
                service.update(
                    self.customer.id,
                    full_name=name,
                    id_number=self.id_input.text().strip(),
                    phone=self.phone_input.text().strip(),
                    email=self.email_input.text().strip(),
                )
            else:
                service.create(
                    full_name=name,
                    id_number=self.id_input.text().strip(),
                    phone=self.phone_input.text().strip(),
                    email=self.email_input.text().strip(),
                )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar: {e}")


class CustomersView(QWidget):
    """Vista principal del módulo de clientes."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.session = app.session
        self._build_ui()
        self._load_customers()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Encabezado
        header = QHBoxLayout()
        title = QLabel("Clientes")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        header.addWidget(title)
        header.addStretch()

        self.new_btn = QPushButton("+ Nuevo Cliente")
        self.new_btn.setFixedHeight(40)
        self.new_btn.clicked.connect(self._open_create)
        header.addWidget(self.new_btn)
        layout.addLayout(header)

        # Búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre o cédula...")
        self.search_input.setFixedHeight(38)
        self.search_input.textChanged.connect(self._search)
        layout.addWidget(self.search_input)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Cédula/NIT", "Teléfono", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 130)
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
        self.toggle_btn.setFixedWidth(140)
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['warning']};
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #d68910; }}
        """)
        self.toggle_btn.clicked.connect(self._toggle_customer)

        self.delete_btn = QPushButton("🗑 Eliminar")
        self.delete_btn.setFixedHeight(38)
        self.delete_btn.setFixedWidth(120)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['danger']};
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #c0392b; }}
        """)
        self.delete_btn.clicked.connect(self._delete_customer)

        action_layout.addWidget(self.edit_btn)
        action_layout.addWidget(self.toggle_btn)
        action_layout.addWidget(self.delete_btn)
        layout.addLayout(action_layout)

    def _load_customers(self):
        self.session.expire_all() #evitar problemas con la caché
        service = CustomerService(self.session)
        customers = service.get_all(only_active=False)
        self._populate_table(customers)

    def _search(self, text):
        if not text.strip():
            self._load_customers()
            return
        service = CustomerService(self.session)
        customers = service.search(text)
        self._populate_table(customers)

    def _populate_table(self, customers):
        self.table.setRowCount(len(customers))
        for row, c in enumerate(customers):
            self.table.setItem(row, 0, QTableWidgetItem(str(c.id)))
            self.table.setItem(row, 1, QTableWidgetItem(c.full_name))
            self.table.setItem(row, 2, QTableWidgetItem(c.id_number or ""))
            self.table.setItem(row, 3, QTableWidgetItem(c.phone or ""))
            estado = QTableWidgetItem("Activo" if c.is_active else "Inactivo")
            estado.setForeground(Qt.green if c.is_active else Qt.red)
            self.table.setItem(row, 4, estado)
            self.table.item(row, 0).setData(Qt.UserRole, c.id)

    def _get_selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Selecciona un cliente primero.")
            return None
        return self.table.item(row, 0).data(Qt.UserRole)

    def _open_create(self):
        dialog = CustomerDialog(self, self.session)
        if dialog.exec():
            self._load_customers()

    def _open_edit(self):
        customer_id = self._get_selected_id()
        if not customer_id:
            return
        service = CustomerService(self.session)
        customer = service.get_by_id(customer_id)
        dialog = CustomerDialog(self, self.session, customer)
        if dialog.exec():
            self._load_customers()

    def _toggle_customer(self):
        customer_id = self._get_selected_id()
        if not customer_id:
            return
        service = CustomerService(self.session)
        customer = service.get_by_id(customer_id)
        action = "desactivar" if customer.is_active else "activar"
        reply = QMessageBox.question(
            self, "Confirmar",
            f"¿Seguro que quieres {action} a '{customer.full_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            service.toggle_active(customer_id)
            self._load_customers()

    def _delete_customer(self):
        customer_id = self._get_selected_id()
        if not customer_id:
            return
        service = CustomerService(self.session)
        customer = service.get_by_id(customer_id)
        reply = QMessageBox.warning(
            self, "Eliminar cliente",
            f"¿Eliminar permanentemente a '{customer.full_name}'?\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.session.delete(customer)
                self.session.commit()
                self._load_customers()
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Error", f"No se pudo eliminar: {e}\n\nSi el cliente tiene ventas asociadas, desactívalo en lugar de eliminarlo.")