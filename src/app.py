"""
Application entry point for E-book Image Optimiser.
"""

import sys

from PySide6.QtWidgets import QApplication

from ui_main import MainWindow


def main():
    """Initialize and run the application."""
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
