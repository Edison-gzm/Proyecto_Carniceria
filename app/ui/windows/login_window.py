import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QLabel, QLineEdit, QPushButton, QFrame,
    QMessageBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QFont, QColor

from database.session import get_session
from services.auth_service import AuthService
from ui.theme import COLORS


class LoginWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.settings = QSettings("CarniceriaApp", "LoginSession")
        
        self.setWindowTitle("Carnicería — Iniciar Sesión")
        self.setFixedSize(400, 540)
        self._center_window()
        self._build_ui()
        self._setup_enter_navigation()
        self._load_last_username()

    def _center_window(self):
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setAlignment(Qt.AlignCenter)

        # Encabezado
        header_icon = QLabel("🥩")
        header_icon.setFont(QFont("Segoe UI", 36))
        header_icon.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_icon)

        title = QLabel("Sistema de Facturación")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        subtitle = QLabel("Carnicería")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        subtitle.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle)

        main_layout.addSpacing(15)

        # Tarjeta del Formulario
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-radius: 12px;
                border: 1px solid {COLORS['border']};
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 35))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(12)

        # Usuario
        user_label = QLabel("Usuario")
        user_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        user_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        card_layout.addWidget(user_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Ingresa tu usuario")
        self.username_input.setFixedHeight(40)
        card_layout.addWidget(self.username_input)

        # Contraseña
        pass_label = QLabel("Contraseña")
        pass_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        pass_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        card_layout.addWidget(pass_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Ingresa tu contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(40)
        card_layout.addWidget(self.password_input)

        card_layout.addSpacing(18)

        # Botón de Iniciar Sesión
        self.login_btn = QPushButton("Iniciar Sesión")
        self.login_btn.setFixedHeight(42)
        self.login_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self._handle_login)
        card_layout.addWidget(self.login_btn)

        main_layout.addWidget(card)

        # Versión
        version = QLabel("v1.0.0")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        main_layout.addSpacing(10)
        main_layout.addWidget(version)

    def _setup_enter_navigation(self):
        """Conecta la tecla Enter de cada casilla."""
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self._handle_login)

    def _load_last_username(self):
        """Carga el último usuario recordado."""
        last_user = self.settings.value("last_username", "", type=str)
        if last_user:
            self.username_input.setText(last_user)
            self.password_input.setFocus()
        else:
            self.username_input.setFocus()

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
                self.settings.setValue("last_username", username)
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