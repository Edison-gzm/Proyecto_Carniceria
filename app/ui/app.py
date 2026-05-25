import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.theme import STYLESHEET


class App:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Sistema de Facturación — Carnicería")
        self.app.setStyleSheet(STYLESHEET)
        self.session = None
        self.current_user = None

    def run(self):
        from ui.windows.login_window import LoginWindow
        self.login_window = LoginWindow(self)
        self.login_window.show()
        sys.exit(self.app.exec())