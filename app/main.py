import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from database.session import init_db
from ui.app import App


def main():
    init_db()
    app = App()
    
    # Desbloquea los estilos personalizados en ventanas de alerta (QMessageBox)
    QApplication.setStyle("Fusion")
    
    app.run()


if __name__ == "__main__":
    main()