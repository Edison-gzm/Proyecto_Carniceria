from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

def format_price(value):
    """
    Convierte un número a formato de moneda (ej: 35000 -> $35.000)
    """
    try:
        return f"${float(value):,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return f"${value}"


def get_square_pixmap(image_path, size=120):
    """
    Carga y recorta una imagen para que quede perfectamente cuadrada y centrada
    """
    pixmap = QPixmap(str(image_path))
    
    if pixmap.isNull():
        # Si la imagen no existe, devuelve un recuadro transparente del tamaño solicitado
        blank = QPixmap(size, size)
        blank.fill(Qt.transparent)
        return blank

    width = pixmap.width()
    height = pixmap.height()
    min_dim = min(width, height)

    # Recorte centrado
    rect_x = (width - min_dim) // 2
    rect_y = (height - min_dim) // 2
    cropped = pixmap.copy(rect_x, rect_y, min_dim, min_dim)

    # Escalado suave
    return cropped.scaled(
        size, size, 
        Qt.KeepAspectRatio, 
        Qt.SmoothTransformation
    )