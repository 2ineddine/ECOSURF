#!/usr/bin/env python3
import sys
import os
from PyQt6.QtWidgets import QApplication

# Ensure 'src' package is importable when running from repository root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.main_window import MainWindow


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
