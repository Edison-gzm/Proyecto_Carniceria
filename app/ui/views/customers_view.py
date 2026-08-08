import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QFrame, QFormLayout,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from services.customer_service import CustomerService
from ui.theme import COLORS


class CustomersView(QWidget):
    """Vista principal del módulo de clientes con diseño CRUD lateral."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.session = app.session
        self.selected_customer = None
        self._build_ui()
        self._load_table()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # -------------------------------------------------------------
        # PANEL IZQUIERDO: TABLA Y BUSCADOR RESALTADO CON SOMBRA
        # -------------------------------------------------------------
        left_layout = QVBoxLayout()
        
        top_bar = QHBoxLayout()
        title = QLabel("Listado de Clientes")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #111111;")
        top_bar.addWidget(title)
        top_bar.addStretch()

        # Buscador de alta visibilidad con borde resaltado
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por nombre o cédula...")
        self.search_input.setFixedWidth(280)
        self.search_input.setFixedHeight(40)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF; 
                color: #0F172A; 
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #2563EB; 
                border-radius: 8px; 
                padding: 0 12px;
            }
            QLineEdit:focus {
                border: 2px solid #1D4ED8;
                background-color: #EFF6FF;
            }
        """)

        # Efecto de sombra para el buscador
        search_shadow = QGraphicsDropShadowEffect(self)
        search_shadow.setBlurRadius(12)
        search_shadow.setXOffset(0)
        search_shadow.setYOffset(3)
        search_shadow.setColor(QColor(0, 0, 0, 45))
        self.search_input.setGraphicsEffect(search_shadow)

        self.search_input.textChanged.connect(self._load_table)
        top_bar.addWidget(self.search_input)
        left_layout.addLayout(top_bar)

        # Tabla de Clientes
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Cédula/NIT", "Teléfono", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 90)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white; 
                border: 1px solid #E2E8F0; 
                gridline-color: #F1F5F9; 
                color: #111111;
            }
            QHeaderView::section {
                background-color: #F8FAFC; 
                font-weight: bold; 
                border: none; 
                padding: 8px; 
                color: #334155;
            }
            QTableWidget::item:selected {
                background-color: #2563EB;
                color: white;
            }
        """)
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        left_layout.addWidget(self.table)

        # -------------------------------------------------------------
        # PANEL DERECHO: FORMULARIO CREAR / EDITAR CLIENTE
        # -------------------------------------------------------------
        panel = QFrame()
        panel.setFixedWidth(350)
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

        self.panel_title = QLabel("Crear Nuevo Cliente")
        self.panel_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.panel_title.setStyleSheet("border: none; color: #111111;")
        panel_layout.addWidget(self.panel_title)

        form = QFormLayout()
        form.setSpacing(10)

        INPUT_STYLE = """
            QLineEdit {
                background-color: #FFFFFF; 
                color: #111111; 
                font-weight: bold;
                border: 1.5px solid #64748B; 
                border-radius: 6px; 
                padding: 6px;
            }
            QLineEdit:focus { 
                border: 2px solid #2563EB; 
            }
        """

        self.txt_name = QLineEdit()
        self.txt_name.setStyleSheet(INPUT_STYLE)
        
        self.txt_id = QLineEdit()
        self.txt_id.setStyleSheet(INPUT_STYLE)

        self.txt_phone = QLineEdit()
        self.txt_phone.setStyleSheet(INPUT_STYLE)

        self.txt_email = QLineEdit()
        self.txt_email.setStyleSheet(INPUT_STYLE)

        form.addRow("Nombre *:", self.txt_name)
        form.addRow("Cédula/NIT:", self.txt_id)
        form.addRow("Teléfono:", self.txt_phone)
        form.addRow("Email:", self.txt_email)
        panel_layout.addLayout(form)

        # Botones de Acción CRUD
        self.btn_save = QPushButton("➕ Crear Cliente")
        self.btn_new = QPushButton("✨ Limpiar Formulario")
        self.btn_delete = QPushButton("🗑️ Eliminar Seleccionado")

        self.btn_save.setFixedHeight(40)
        self.btn_new.setFixedHeight(36)
        self.btn_delete.setFixedHeight(36)

        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setCursor(Qt.PointingHandCursor)

        self.btn_save.setStyleSheet("background-color: #16A34A; color: white; font-weight: bold; border-radius: 6px; border: none; font-size: 13px;")
        self.btn_new.setStyleSheet("background-color: #64748B; color: white; font-weight: bold; border-radius: 6px; border: none;")
        self.btn_delete.setStyleSheet("background-color: #DC2626; color: white; font-weight: bold; border-radius: 6px; border: none;")

        self.btn_save.clicked.connect(self._save_customer)
        self.btn_new.clicked.connect(self._clear_form)
        self.btn_delete.clicked.connect(self._delete_customer)

        panel_layout.addWidget(self.btn_save)
        panel_layout.addWidget(self.btn_new)
        panel_layout.addWidget(self.btn_delete)
        panel_layout.addStretch()

        main_layout.addLayout(left_layout, stretch=2)
        main_layout.addWidget(panel, stretch=1)

    def _load_table(self):
        self.table.setRowCount(0)
        self.session.expire_all()
        service = CustomerService(self.session)

        query = self.search_input.text().strip()
        if query:
            customers = service.search(query)
        else:
            customers = service.get_all(only_active=False)

        for c in customers:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(str(c.id)))
            self.table.setItem(row, 1, QTableWidgetItem(c.full_name))
            self.table.setItem(row, 2, QTableWidgetItem(c.id_number or ""))
            self.table.setItem(row, 3, QTableWidgetItem(c.phone or ""))
            
            status_item = QTableWidgetItem("Activo" if c.is_active else "Inactivo")
            status_item.setForeground(Qt.green if c.is_active else Qt.red)
            self.table.setItem(row, 4, status_item)

    def _on_row_selected(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        row = selected_items[0].row()
        customer_id = int(self.table.item(row, 0).text())

        service = CustomerService(self.session)
        self.selected_customer = service.get_by_id(customer_id)

        if self.selected_customer:
            self.panel_title.setText("Editar Cliente")
            self.btn_save.setText("💾 Actualizar Cliente")
            self.txt_name.setText(self.selected_customer.full_name)
            self.txt_id.setText(self.selected_customer.id_number or "")
            self.txt_phone.setText(self.selected_customer.phone or "")
            self.txt_email.setText(self.selected_customer.email or "")

    def _clear_form(self):
        self.selected_customer = None
        self.panel_title.setText("Crear Nuevo Cliente")
        self.btn_save.setText("➕ Crear Cliente")
        self.txt_name.clear()
        self.txt_id.clear()
        self.txt_phone.clear()
        self.txt_email.clear()
        self.table.clearSelection()

    def _save_customer(self):
        name = self.txt_name.text().strip()
        # Verifica si en tu UI el campo se llama txt_id o txt_id_number
        id_number = self.txt_id.text().strip() if hasattr(self, 'txt_id') else self.txt_id_number.text().strip()
        phone = self.txt_phone.text().strip()
        email = self.txt_email.text().strip()
        address = self.txt_address.text().strip() if hasattr(self, 'txt_address') else ""

        if not name:
            QMessageBox.warning(self, "Atención", "El nombre completo es obligatorio.")
            return

        service = CustomerService(self.session)

        try:
            if self.selected_customer:
                service.update(
                    self.selected_customer.id,
                    full_name=name,
                    id_number=id_number,
                    phone=phone,
                    email=email,
                    address=address
                )
                QMessageBox.information(self, "Éxito", "Cliente actualizado correctamente.")
            else:
                service.create(
                    full_name=name,
                    id_number=id_number,
                    phone=phone,
                    email=email,
                    address=address,
                    created_by_id=self.app.current_user.id
                )
                QMessageBox.information(self, "Éxito", "Cliente creado exitosamente.")

            self._clear_form()
            self._load_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el cliente: {e}")

    def _delete_customer(self):
        if not self.selected_customer:
            QMessageBox.warning(self, "Atención", "Selecciona primero un cliente de la tabla para eliminar.")
            return

        reply = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Estás seguro de que deseas eliminar permanentemente al cliente '{self.selected_customer.full_name}'?\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.session.delete(self.selected_customer)
                self.session.commit()
                self._clear_form()
                self._load_table()
                QMessageBox.information(self, "Éxito", "Cliente eliminado correctamente.")
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(
                    self, "Error al eliminar", 
                    f"No se pudo eliminar el cliente. Si ya posee facturas o ventas asociadas, se recomienda únicamente desactivarlo.\n\nDetalle: {e}"
                )