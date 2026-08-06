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
        self.setMinimumSize(1100, 700)
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
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Barra superior de navegación (Pestañas horizontales)
        navbar = self._build_navbar()
        main_layout.addWidget(navbar)

        # 2. Área de contenido
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {COLORS['secondary']};")
        main_layout.addWidget(self.stack)

        # Configuración de vistas
        self.pages = {}
        modules = [
            "INICIO", "Ventas", "Productos",
            "Clientes", "Caja", "Reportes"
        ]
        
        from ui.views.dashboard_view import DashboardView
        from ui.views.products_view import ProductsView
        from ui.views.customers_view import CustomersView
        from ui.views.sales_view import SalesView

        for name in modules:
            if name == "INICIO":
                page = DashboardView(self)
            elif name == "Productos":
                page = ProductsView(self.app)
            elif name == "Clientes":
                page = CustomersView(self.app)
            elif name == "Ventas":
                page = SalesView(self.app)
            else:
                page = self._placeholder_page(name)

            self.pages[name] = page
            self.stack.addWidget(page)

        # Mostrar INICIO por defecto
        self.stack.setCurrentWidget(self.pages["INICIO"])

    def _build_navbar(self):
        navbar = QFrame()
        navbar.setFixedHeight(65)
        navbar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        
        layout = QHBoxLayout(navbar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(8)

        # Logo / Nombre
        app_name = QLabel("🥩 Carnicería")
        app_name.setFont(QFont("Segoe UI", 13, QFont.Bold))
        app_name.setStyleSheet(f"color: {COLORS['primary']}; border: none; margin-right: 12px;")
        layout.addWidget(app_name)

        # Botones de las Pestañas
        nav_items = [
            ("📊", "INICIO"),
            ("🛒", "Ventas"),
            ("🥩", "Productos"),
            ("👥", "Clientes"),
            ("💰", "Caja"),
            ("📈", "Reportes"),
        ]

        self.nav_buttons = {}
        for icon, name in nav_items:
            btn = QPushButton(f"{icon} {name}")
            btn.setFixedHeight(45)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {COLORS['text_secondary']};
                    border: none;
                    border-bottom: 3px solid transparent;
                    font-size: 13px;
                    font-weight: bold;
                    padding: 0 14px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['surface_light']};
                    color: {COLORS['text_primary']};
                }}
                QPushButton:checked {{
                    color: {COLORS['primary']};
                    border-bottom: 3px solid {COLORS['primary']};
                    background-color: {COLORS['surface_light']};
                }}
            """)
            btn.clicked.connect(lambda _, n=name: self._navigate(n))
            self.nav_buttons[name] = btn
            layout.addWidget(btn)

        # Marcar INICIO por defecto
        if "INICIO" in self.nav_buttons:
            self.nav_buttons["INICIO"].setChecked(True)

        layout.addStretch()

        # Info del usuario
        user = self.app.current_user
        user_label = QLabel(f"👤 {user.full_name}")
        user_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; font-weight: bold; border: none;")
        layout.addWidget(user_label)

        # Botón Cerrar Sesión
        logout_btn = QPushButton("⬅ Salir")
        logout_btn.setFixedHeight(34)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['danger']};
                border: 1px solid {COLORS['danger']};
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['danger']};
                color: white;
            }}
        """)
        logout_btn.clicked.connect(self._logout)
        layout.addWidget(logout_btn)

        return navbar

    def show_products_category(self, category_name):
        """Redirige a la vista de Productos y aplica el filtro por categoría."""
        if "Productos" in self.pages:
            self.stack.setCurrentWidget(self.pages["Productos"])
            
            for btn_name, btn in self.nav_buttons.items():
                btn.setChecked(btn_name == "Productos")

            products_view = self.pages["Productos"]
            if hasattr(products_view, 'filter_by_category'):
                products_view.filter_by_category(category_name)

    def _navigate(self, name):
        for btn_name, btn in self.nav_buttons.items():
            btn.setChecked(btn_name == name)
        self.stack.setCurrentWidget(self.pages[name])

    def _placeholder_page(self, name):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel(f"{name}")
        label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        label.setStyleSheet(f"color: {COLORS['text_secondary']};")

        sublabel = QLabel("Módulo en construcción")
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