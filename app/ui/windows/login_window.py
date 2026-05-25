import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from database.session import get_session
from services.auth_service import AuthService
from ui.theme import COLORS


class LoginWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("Carnicería — Iniciar Sesión")
        self.setFixedSize(420, 500)
        self._center_window()
        self._build_ui()

    def _center_window(self):
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(0)

        # Título
        title = QLabel("🥩")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 48))
        main_layout.addWidget(title)

        subtitle = QLabel("Sistema de Facturación")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 18, QFont.Bold))
        subtitle.setStyleSheet(f"color: {COLORS['primary']}; margin-bottom: 4px;")
        main_layout.addWidget(subtitle)

        carniceria = QLabel("Carnicería")
        carniceria.setAlignment(Qt.AlignCenter)
        carniceria.setFont(QFont("Segoe UI", 13))
        carniceria.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-bottom: 32px;")
        main_layout.addWidget(carniceria)

        # Card del formulario
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-radius: 12px;
                padding: 8px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(24, 24, 24, 24)

        # Usuario
        user_label = QLabel("Usuario")
        user_label.setFont(QFont("Segoe UI", 11))
        card_layout.addWidget(user_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ingresa tu usuario")
        self.username_input.setFixedHeight(44)
        card_layout.addWidget(self.username_input)

        # Contraseña
        pass_label = QLabel("Contraseña")
        pass_label.setFont(QFont("Segoe UI", 11))
        card_layout.addWidget(pass_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Ingresa tu contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(44)
        self.password_input.returnPressed.connect(self._handle_login)
        card_layout.addWidget(self.password_input)

        # Botón
        self.login_btn = QPushButton("Iniciar Sesión")
        self.login_btn.setFixedHeight(46)
        self.login_btn.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.login_btn.clicked.connect(self._handle_login)
        card_layout.addWidget(self.login_btn)

        main_layout.addWidget(card)

        # Versión
        version = QLabel("v1.0.0")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet(f"color: {COLORS['text_secondary']}; margin-top: 16px; font-size: 11px;")
        main_layout.addWidget(version)

    def _handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Por favor ingresa usuario y contraseña.")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Verificando...")

        try:
            session = get_session()
            auth = AuthService(session)
            user = auth.login(username, password)

            if user:
                self.app.session = session
                self.app.current_user = user
                self._open_main_window()
            else:
                QMessageBox.warning(self, "Error", "Usuario o contraseña incorrectos.")
                self.password_input.clear()
                self.password_input.setFocus()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error de conexión: {e}")
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("Iniciar Sesión")

    def _open_main_window(self):
        from ui.windows.main_window import MainWindow
        self.main_window = MainWindow(self.app)
        self.main_window.show()
        self.close()