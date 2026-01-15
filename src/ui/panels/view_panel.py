from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QCheckBox, 
    QGroupBox, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QFrame


class ViewPanel(QWidget):
    zoom_toggled = pyqtSignal(bool)
    zoom_reset_requested = pyqtSignal()
    viewport_scrolled = pyqtSignal(int)
    cursor_changed = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        
        # Ubuntu-style title
        title = QLabel("View Controls")
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #E95420;
                padding: 8px 0px;
                border-bottom: 2px solid #DEDEDE;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(title)
        
        # Zoom group
        zoom_group = QGroupBox("Zoom")
        zoom_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #DEDEDE;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #FAFAFA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0px 5px 0px 5px;
            }
        """)
        zoom_layout = QVBoxLayout()
        zoom_layout.setContentsMargins(12, 15, 12, 12)
        zoom_layout.setSpacing(10)
        
        # Ubuntu-style checkbox
        self.zoom_checkbox = QCheckBox("Enable Zoom")
        self.zoom_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #888888;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #E95420;
                border: 2px solid #E95420;
                image: url(none);
            }
            QCheckBox::indicator:hover {
                border: 2px solid #555555;
            }
        """)
        self.zoom_checkbox.stateChanged.connect(self.on_zoom_toggled)
        zoom_layout.addWidget(self.zoom_checkbox)
        
        zoom_info = QLabel("Click & drag rectangle to zoom in")
        zoom_info.setWordWrap(True)
        zoom_info.setStyleSheet("""
            QLabel {
                color: #5E5E5E;
                font-size: 11px;
                margin-left: 26px;
                line-height: 1.3;
                padding-top: 2px;
            }
        """)
        zoom_layout.addWidget(zoom_info)
        
        # Ubuntu-style reset button
        reset_btn = QPushButton("Reset Zoom")
        reset_btn.setMinimumHeight(32)
        reset_btn.clicked.connect(self.on_reset_zoom)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F2;
                color: #333333;
                font-size: 12px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #E5E5E5;
                border: 1px solid #888888;
            }
        """)
        zoom_layout.addWidget(reset_btn)
        
        zoom_group.setLayout(zoom_layout)
        layout.addWidget(zoom_group)
        
        # Shortcuts group
        shortcuts_group = QGroupBox("Keyboard Shortcuts")
        shortcuts_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #DEDEDE;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #FAFAFA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0px 5px 0px 5px;
            }
        """)
        shortcuts_layout = QVBoxLayout()
        shortcuts_layout.setContentsMargins(12, 15, 12, 12)
        
        shortcuts_text = QLabel(
            "<b>R</b> - Reset zoom<br>"
            "<b>Space</b> - Play/Pause main audio<br>"
            "<b>Shift+Space</b> - Play/Pause selection<br>"
            "<b>- / =</b> - Adjust brush size<br>"
            "<b>F1</b> - Toggle left sidebar<br>"
            "<b>F2</b> - Toggle controls panel<br>"
            "<b>Mouse Wheel</b> - Zoom in/out"
        )
        shortcuts_text.setWordWrap(True)
        shortcuts_text.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: white;
                border: 1px solid #DEDEDE;
                border-radius: 3px;
                font-size: 11px;
                color: #5E5E5E;
                line-height: 1.4;
            }
        """)
        shortcuts_layout.addWidget(shortcuts_text)
        
        shortcuts_group.setLayout(shortcuts_layout)
        layout.addWidget(shortcuts_group)
        
        # Display group
        display_group = QGroupBox("Display Tips")
        display_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #DEDEDE;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #FAFAFA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0px 5px 0px 5px;
            }
        """)
        display_layout = QVBoxLayout()
        display_layout.setContentsMargins(12, 15, 12, 12)
        
        display_info = QLabel(
            "<b>Navigation Tips:</b><br>"
            "• Mouse wheel to zoom vertically<br>"
            "• Click & drag to pan viewport<br>"
            "• Use scrollbar under spectrogram<br>"
            "• Middle click to reset view"
        )
        display_info.setWordWrap(True)
        display_info.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: white;
                border: 1px solid #DEDEDE;
                border-radius: 3px;
                font-size: 11px;
                color: #5E5E5E;
                line-height: 1.4;
            }
        """)
        display_layout.addWidget(display_info)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
    def on_zoom_toggled(self, state):
        enabled = (state == Qt.CheckState.Checked.value)
        self.zoom_toggled.emit(enabled)
        
        if enabled:
            self.cursor_changed.emit(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.cursor_changed.emit(QCursor(Qt.CursorShape.ArrowCursor))
            
    def on_reset_zoom(self):
        self.zoom_reset_requested.emit()
        
    def disable_zoom(self):
        self.zoom_checkbox.setChecked(False)