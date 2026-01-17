from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class ClusteringWidget(QWidget):
    show_spectrogram_signal = pyqtSignal(str, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.addStretch()

        title = QLabel("Carte 2D Interactive")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2C3E50;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("Cliquez pour ouvrir la visualisation des clusters")
        desc.setStyleSheet("color: #7F8C8D; font-size: 14px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        layout.addSpacing(20)

        self.open_btn = QPushButton("Ouvrir la Carte 2D")
        self.open_btn.setFixedSize(250, 55)
        self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_btn.setStyleSheet("""
            QPushButton {
                background: #3498DB;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton:hover { background: #2980B9; }
            QPushButton:pressed { background: #1F618D; }
        """)
        self.open_btn.clicked.connect(self.open_dialog)

        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(self.open_btn)
        layout.addWidget(btn_container)

        layout.addStretch()

    def open_dialog(self):
        try:
            from ui.dialogs.clustering_dialog_fast import ClusteringDialogFast
            if self.dialog is None or not self.dialog.isVisible():
                self.dialog = ClusteringDialogFast(self.window())
                self.dialog.show_spectrogram_signal.connect(self.show_spectrogram_signal.emit)
                self.dialog.show()
            else:
                self.dialog.raise_()
                self.dialog.activateWindow()
        except ImportError as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", f"PyQtGraph requis:\npip install pyqtgraph\n\n{e}")
