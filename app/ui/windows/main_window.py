import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from ui.theme import COLORS


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("Sistema de Facturación — Carnicería")
        self.setMinimumSize(1100, 650)
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
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barra lateral
        sidebar = self._build_sidebar()
        layout.addWidget(sidebar)

        # Área de contenido
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {COLORS['secondary']};")
        layout.addWidget(self.stack)

        # Páginas vacías por ahora (se llenan en siguiente fase)
        self.pages = {}
        modules = [
            "Dashboard", "Ventas", "Productos",
            "Clientes", "Caja", "Reportes"
        ]
        from ui.views.products_view import ProductsView

        for name in modules:
            if name == "Productos":
                page = ProductsView(self.app)
            else:
                page = self._placeholder_page(name)

            self.pages[name] = page
            self.stack.addWidget(page)

        # Mostrar dashboard por defecto
        self.stack.setCurrentWidget(self.pages["Dashboard"])

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header del sidebar
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet(f"background-color: {COLORS['primary']}; border: none;")
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignCenter)

        app_name = QLabel("🥩 Carnicería")
        app_name.setAlignment(Qt.AlignCenter)
        app_name.setFont(QFont("Segoe UI", 13, QFont.Bold))
        app_name.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(app_name)

        layout.addWidget(header)

        # Info del usuario
        user = self.app.current_user
        user_frame = QFrame()
        user_frame.setFixedHeight(60)
        user_frame.setStyleSheet(f"""
            QFrame {{ background-color: {COLORS['surface_light']}; border: none; }}
        """)
        user_layout = QVBoxLayout(user_frame)
        user_layout.setAlignment(Qt.AlignCenter)

        user_label = QLabel(f"👤 {user.full_name}")
        user_label.setAlignment(Qt.AlignCenter)
        user_label.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent; font-size: 12px;")
        role_label = QLabel(user.role.value)
        role_label.setAlignment(Qt.AlignCenter)
        role_label.setStyleSheet(f"color: {COLORS['primary']}; background: transparent; font-size: 11px;")

        user_layout.addWidget(user_label)
        user_layout.addWidget(role_label)
        layout.addWidget(user_frame)

        # Separador
        layout.addSpacing(8)

        # Botones de navegación
        nav_items = [
            ("📊", "Dashboard"),
            ("🛒", "Ventas"),
            ("🥩", "Productos"),
            ("👥", "Clientes"),
            ("💰", "Caja"),
            ("📈", "Reportes"),
        ]

        self.nav_buttons = {}
        for icon, name in nav_items:
            btn = self._nav_button(icon, name)
            self.nav_buttons[name] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Botón cerrar sesión
        logout_btn = QPushButton("⬅  Cerrar Sesión")
        logout_btn.setFixedHeight(44)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                border-top: 1px solid {COLORS['border']};
                border-radius: 0px;
                font-size: 13px;
                text-align: left;
                padding-left: 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger']};
                color: white;
            }}
        """)
        logout_btn.clicked.connect(self._logout)
        layout.addWidget(logout_btn)

        return sidebar

    def _nav_button(self, icon, name):
        btn = QPushButton(f"  {icon}  {name}")
        btn.setFixedHeight(48)
        btn.setCheckable(True)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                border-radius: 0px;
                font-size: 14px;
                text-align: left;
                padding-left: 20px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_primary']};
            }}
            QPushButton:checked {{
                background-color: {COLORS['primary']};
                color: white;
                border-left: 3px solid white;
            }}
        """)
        btn.clicked.connect(lambda checked, n=name: self._navigate(n))
        return btn

    def _navigate(self, name):
        for btn_name, btn in self.nav_buttons.items():
            btn.setChecked(btn_name == name)
        self.stack.setCurrentWidget(self.pages[name])

    def _placeholder_page(self, name):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel(f"{name}")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        label.setStyleSheet(f"color: {COLORS['text_secondary']};")

        sublabel = QLabel("Módulo en construcción")
        sublabel.setAlignment(Qt.AlignCenter)
        sublabel.setStyleSheet(f"color: {COLORS['border']}; font-size: 14px;")

        layout.addWidget(label)
        layout.addWidget(sublabel)
        return page

    def _logout(self):
        if self.app.session:
            self.app.session.close()
        from ui.windows.login_window import LoginWindow
        self.login_window = LoginWindow(self.app)
        self.login_window.show()
        self.close()