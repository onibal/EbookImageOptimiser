"""
Application entry point for E-book Image Optimiser.
"""

import sys

from PySide6.QtWidgets import QApplication

import src.ui_main


def main():
    """Initialize and run the application."""
    app = QApplication(sys.argv)
    w = src.ui_main.MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
