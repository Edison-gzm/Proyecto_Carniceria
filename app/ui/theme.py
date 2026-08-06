# ui/theme.py

COLORS = {
    'primary': '#2C3E50',        # Azul oscuro para encabezados/botones principales
    'secondary': '#F8F9FA',      # Fondo general claro
    'surface': '#FFFFFF',        # Fondo blanco para tarjetas y campos
    'surface_light': '#E9ECEF',  # Fondo suave para elementos secundarios
    'text_primary': '#111111',   # Texto negro de alto contraste
    'text_secondary': '#495057', # Texto secundario oscuro
    'border': '#CED4DA',         # Bordes definidos
    'warning': '#D35400',        # Naranja
    'danger': '#C0392B',         # Rojo
    'success': '#27AE60'         # Verde
}

STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {COLORS['secondary']};
}}

QWidget {{
    font-family: 'Segoe UI', sans-serif;
    color: {COLORS['text_primary']};
}}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['surface']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
}}

QLineEdit:focus, QComboBox:focus {{
    border: 2px solid {COLORS['primary']};
}}

QPushButton {{
    background-color: {COLORS['primary']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 18px;
    font-size: 14px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: #1A252F;
}}

QTableWidget {{
    background-color: {COLORS['surface']};
    color: {COLORS['text_primary']};
    gridline-color: {COLORS['border']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
}}

QHeaderView::section {{
    background-color: {COLORS['surface_light']};
    color: {COLORS['text_primary']};
    font-weight: bold;
    padding: 8px;
    border: none;
    border-bottom: 2px solid {COLORS['border']};
}}
"""