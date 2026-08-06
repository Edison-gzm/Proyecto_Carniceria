from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, 
    QPushButton, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from ui.theme import COLORS

BASE_DIR = Path(__file__).parent.parent.parent
IMAGES_DIR = BASE_DIR / "assets" / "images"

class DashboardView(QWidget):
    """Vista principal 'Inicio' con tarjetas limpias e imágenes destacadas."""

    def __init__(self, app):
        super().__init__()
        self.app = app
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        title = QLabel("¿Qué categoría deseas ver?")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #111111;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(20)

        categories = [
            ("Carne de Vaca", str(IMAGES_DIR / "vaca.jpg")),
            ("Carne de Cerdo", str(IMAGES_DIR / "cerdo.jpg")),
            ("Pollo", str(IMAGES_DIR / "pollo.jpg")),
            ("Embutidos", str(IMAGES_DIR / "embutidos.jpg"))
        ]

        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]

        for (name, img_path), (row, col) in zip(categories, positions):
            btn = QPushButton()
            btn.setFixedHeight(230)
            btn.setCursor(Qt.PointingHandCursor)
            
            btn_layout = QVBoxLayout(btn)
            btn_layout.setContentsMargins(16, 16, 16, 16)
            btn_layout.setSpacing(10)
            
            # Imagen más grande (140px)
            icon_label = QLabel()
            pixmap = QPixmap(img_path)
            
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    140, 140, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                icon_label.setPixmap(scaled_pixmap)
            else:
                icon_label.setText("[Sin Imagen]")
                
            icon_label.setAlignment(Qt.AlignCenter)
            
            # Texto negro y más pequeño (14px)
            text_label = QLabel(name)
            text_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
            text_label.setStyleSheet("color: #111111; background: transparent;")
            text_label.setAlignment(Qt.AlignCenter)

            btn_layout.addWidget(icon_label)
            btn_layout.addWidget(text_label)

            # Tarjeta blanca limpia con sombra/borde sutil
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: #FFFFFF;
                    border-radius: 12px;
                    border: 1px solid {COLORS['border']};
                }}
                QPushButton:hover {{
                    background-color: #F8F9FA;
                    border: 2px solid {COLORS['primary']};
                }}
            """)

            btn.clicked.connect(lambda _, cat_name=name: self._navigate_to_category(cat_name))
            grid.addWidget(btn, row, col)

        layout.addLayout(grid)
        layout.addStretch()

    def _navigate_to_category(self, category_name):
        if hasattr(self.app, 'show_products_category'):
            self.app.show_products_category(category_name)