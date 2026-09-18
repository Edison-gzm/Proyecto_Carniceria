import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QComboBox, QMessageBox, QFrame, QFormLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from database.models.user import User, UserRole
from database.models.sale import Sale
from database.models.product import Product
from database.models.customer import Customer
from services.auth_service import AuthService
from ui.theme import COLORS


class UsersView(QWidget):
    """Vista de administración de usuarios y métricas con CRUD completo."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.session = app.session
        self.selected_user_id = None
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # TABLA DE USUARIOS Y MÉTRICAS
        left_layout = QVBoxLayout()
        title = QLabel("Gestión de Usuarios y Métricas")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #111111;")
        left_layout.addWidget(title)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Usuario", "Nombre Completo", "Rol", "Ventas (#)", "Prods. Creados", "Clientes Creados"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #E2E8F0; color: #111111; }
            QHeaderView::section { background-color: #F8FAFC; font-weight: bold; border: none; padding: 8px; color: #334155; }
        """)
        self.table.itemSelectionChanged.connect(self._on_user_selected)
        left_layout.addWidget(self.table)

        # PANEL REGISTRO Y ACCIONES
        panel = QFrame()
        panel.setFixedWidth(340)
        panel.setStyleSheet(f"QFrame {{ background-color: {COLORS.get('surface', '#FFFFFF')}; border: 1px solid {COLORS.get('border', '#E2E8F0')}; border-radius: 10px; }}")
        
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(16, 16, 16, 16)
        panel_layout.setSpacing(10)

        panel_title = QLabel("Gestión de Usuario")
        panel_title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        panel_title.setStyleSheet("border: none; color: #111111;")
        panel_layout.addWidget(panel_title)

        form = QFormLayout()
        form.setSpacing(10)

        INPUT_STYLE = "QLineEdit, QComboBox { background-color: white; color: #111; font-weight: bold; border: 1.5px solid #64748B; border-radius: 6px; padding: 6px; }"

        self.txt_fullname = QLineEdit()
        self.txt_fullname.setStyleSheet(INPUT_STYLE)

        self.txt_username = QLineEdit()
        self.txt_username.setStyleSheet(INPUT_STYLE)

        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.Password)
        self.txt_password.setStyleSheet(INPUT_STYLE)
        self.txt_password.setPlaceholderText("Dejar en blanco para conservar")

        self.cmb_role = QComboBox()
        self.cmb_role.addItem("Cajero (Estándar)", UserRole.CAJERO)
        self.cmb_role.addItem("Administrador", UserRole.ADMIN)
        self.cmb_role.setStyleSheet(INPUT_STYLE)

        form.addRow("Nombre Completo:", self.txt_fullname)
        form.addRow("Usuario (Login):", self.txt_username)
        form.addRow("Contraseña:", self.txt_password)
        form.addRow("Rol:", self.cmb_role)
        panel_layout.addLayout(form)

        # BOTONES
        BTN_STYLE = "font-weight: bold; border-radius: 6px; border: none; font-size: 13px;"

        btn_create = QPushButton("👤 Crear Usuario")
        btn_create.setFixedHeight(36)
        btn_create.setCursor(Qt.PointingHandCursor)
        btn_create.setStyleSheet(f"background-color: #16A34A; color: white; {BTN_STYLE}")
        btn_create.clicked.connect(self._create_user)
        panel_layout.addWidget(btn_create)

        btn_update = QPushButton("✏️ Actualizar Usuario")
        btn_update.setFixedHeight(36)
        btn_update.setCursor(Qt.PointingHandCursor)
        btn_update.setStyleSheet(f"background-color: #2563EB; color: white; {BTN_STYLE}")
        btn_update.clicked.connect(self._update_user)
        panel_layout.addWidget(btn_update)

        btn_clear = QPushButton("✨ Limpiar Formulario")
        btn_clear.setFixedHeight(36)
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setStyleSheet(f"background-color: #475569; color: white; {BTN_STYLE}")
        btn_clear.clicked.connect(self._clear_form)
        panel_layout.addWidget(btn_clear)

        btn_delete = QPushButton("🗑️ Eliminar Seleccionado")
        btn_delete.setFixedHeight(36)
        btn_delete.setCursor(Qt.PointingHandCursor)
        btn_delete.setStyleSheet(f"background-color: #DC2626; color: white; {BTN_STYLE}")
        btn_delete.clicked.connect(self._delete_user)
        panel_layout.addWidget(btn_delete)

        panel_layout.addStretch()

        main_layout.addLayout(left_layout, stretch=2)
        main_layout.addWidget(panel, stretch=1)

    def _load_data(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.session.expire_all()
        auth_service = AuthService(self.session)
        users = auth_service.get_all()

        for u in users:
            sales_count = self.session.query(Sale).filter(Sale.user_id == u.id).count()
            prods_count = self.session.query(Product).filter(Product.created_by_id == u.id).count()
            cust_count = self.session.query(Customer).filter(Customer.created_by_id == u.id).count()

            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(u.id)))
            self.table.setItem(row, 1, QTableWidgetItem(u.username))
            self.table.setItem(row, 2, QTableWidgetItem(u.full_name))
            role_val = u.role.value if hasattr(u.role, 'value') else str(u.role)
            self.table.setItem(row, 3, QTableWidgetItem(role_val))
            self.table.setItem(row, 4, QTableWidgetItem(str(sales_count)))
            self.table.setItem(row, 5, QTableWidgetItem(str(prods_count)))
            self.table.setItem(row, 6, QTableWidgetItem(str(cust_count)))

        self.table.blockSignals(False)

    def _on_user_selected(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return

        self.selected_user_id = int(self.table.item(selected_row, 0).text())
        username = self.table.item(selected_row, 1).text()
        fullname = self.table.item(selected_row, 2).text()
        role_str = self.table.item(selected_row, 3).text()

        self.txt_username.setText(username)
        self.txt_fullname.setText(fullname)
        self.txt_password.clear()

        for i in range(self.cmb_role.count()):
            role_enum = self.cmb_role.itemData(i)
            val = role_enum.value if hasattr(role_enum, 'value') else str(role_enum)
            if val.upper() == role_str.upper():
                self.cmb_role.setCurrentIndex(i)
                break

    def _clear_form(self):
        self.selected_user_id = None
        self.table.clearSelection()
        self.txt_fullname.clear()
        self.txt_username.clear()
        self.txt_password.clear()
        self.cmb_role.setCurrentIndex(0)

    def _create_user(self):
        fullname = self.txt_fullname.text().strip()
        username = self.txt_username.text().strip()
        password = self.txt_password.text().strip()
        role = self.cmb_role.currentData()

        if not fullname or not username or not password:
            QMessageBox.warning(self, "Atención", "Por favor completa todos los campos (incluyendo contraseña).")
            return

        auth_service = AuthService(self.session)
        try:
            auth_service.create_user(username=username, password=password, full_name=fullname, role=role)
            QMessageBox.information(self, "Éxito", f"Usuario '{username}' registrado exitosamente.")
            self._clear_form()
            self._load_data()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Error", f"No se pudo crear el usuario: {e}")

    def _update_user(self):
        if not self.selected_user_id:
            QMessageBox.warning(self, "Atención", "Selecciona un usuario de la tabla para actualizar.")
            return

        fullname = self.txt_fullname.text().strip()
        username = self.txt_username.text().strip()
        password = self.txt_password.text().strip()
        role = self.cmb_role.currentData()

        if not fullname or not username:
            QMessageBox.warning(self, "Atención", "Nombre y Usuario no pueden estar vacíos.")
            return

        try:
            user = self.session.query(User).filter_by(id=self.selected_user_id).first()
            if not user:
                QMessageBox.critical(self, "Error", "El usuario seleccionado no existe.")
                return

            user.full_name = fullname
            user.username = username
            user.role = role

            if password:
                auth_service = AuthService(self.session)
                user.password_hash = auth_service.hash_password(password)

            self.session.commit()
            QMessageBox.information(self, "Éxito", f"Usuario '{username}' actualizado correctamente.")
            self._clear_form()
            self._load_data()
        except Exception as e:
            self.session.rollback()
            QMessageBox.critical(self, "Error", f"No se pudo actualizar el usuario: {e}")

    def _delete_user(self):
        if not self.selected_user_id:
            selected_row = self.table.currentRow()
            if selected_row >= 0:
                self.selected_user_id = int(self.table.item(selected_row, 0).text())

        if not self.selected_user_id:
            QMessageBox.warning(self, "Atención", "Por favor selecciona un usuario de la tabla.")
            return

        user = self.session.query(User).filter_by(id=self.selected_user_id).first()
        if not user:
            return

        current_user = getattr(self.app, 'current_user', None)
        if current_user and current_user.id == user.id:
            QMessageBox.critical(self, "Error", "No puedes eliminar tu propio usuario activo.")
            return

        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar al usuario '{user.username}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.session.delete(user)
                self.session.commit()
                QMessageBox.information(self, "Éxito", f"Usuario '{user.username}' eliminado correctamente.")
                self._clear_form()
                self._load_data()
            except Exception as e:
                self.session.rollback()
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el usuario: {e}")