COLORS = {
    "primary":        "#C8102E",   # Rojo carnicería
    "primary_dark":   "#A00D24",
    "secondary":      "#1A1A2E",   # Fondo oscuro
    "surface":        "#2A2A3E",   # Tarjetas
    "surface_light":  "#3A3A4E",   # Hover
    "text_primary":   "#FFFFFF",
    "text_secondary": "#B0B0C0",
    "success":        "#2ECC71",
    "warning":        "#F39C12",
    "danger":         "#E74C3C",
    "border":         "#4A4A5E",
}

STYLESHEET = f"""
    QMainWindow, QDialog {{
        background-color: {COLORS['secondary']};
        color: {COLORS['text_primary']};
        font-family: 'Segoe UI';
        font-size: 14px;
    }}
    QWidget {{
        background-color: {COLORS['secondary']};
        color: {COLORS['text_primary']};
        font-family: 'Segoe UI';
    }}
    QPushButton {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {COLORS['primary_dark']};
    }}
    QPushButton:disabled {{
        background-color: {COLORS['border']};
        color: {COLORS['text_secondary']};
    }}
    QLineEdit {{
        background-color: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 10px;
        font-size: 14px;
    }}
    QLineEdit:focus {{
        border: 1px solid {COLORS['primary']};
    }}
    QLabel {{
        color: {COLORS['text_primary']};
        background-color: transparent;
    }}
    QMessageBox {{
        background-color: {COLORS['secondary']};
        color: {COLORS['text_primary']};
    }}
"""