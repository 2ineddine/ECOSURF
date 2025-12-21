from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QCheckBox, 
    QGroupBox, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor


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
        
        content = QWidget()
        layout = QVBoxLayout(content)
        
        title = QLabel("View Controls")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(title)
        
        zoom_group = QGroupBox("Zoom")
        zoom_layout = QVBoxLayout()
        
        self.zoom_checkbox = QCheckBox("🔍 Enable Zoom")
        self.zoom_checkbox.stateChanged.connect(self.on_zoom_toggled)
        zoom_layout.addWidget(self.zoom_checkbox)
        
        zoom_info = QLabel("Click & drag to zoom")
        zoom_info.setWordWrap(True)
        zoom_info.setStyleSheet("color: #666; font-size: 10px; margin-left: 20px;")
        zoom_layout.addWidget(zoom_info)
        
        reset_btn = QPushButton("↺ Reset Zoom")
        reset_btn.setMinimumHeight(32)
        reset_btn.clicked.connect(self.on_reset_zoom)
        zoom_layout.addWidget(reset_btn)
        
        zoom_group.setLayout(zoom_layout)
        layout.addWidget(zoom_group)
        
        shortcuts_group = QGroupBox("⌨️ Shortcuts")
        shortcuts_layout = QVBoxLayout()
        
        shortcuts_text = QLabel(
            "<b>R</b> - Reset zoom<br>"
            "<b>Space</b> - Play/Pause<br>"
            "<b>Shift+Space</b> - Play selection<br>"
            "<b>-/=</b> - Brush size<br>"
            "<b>F1</b> - Toggle left panel<br>"
            "<b>F2</b> - Toggle bottom panel"
        )
        shortcuts_text.setStyleSheet(
            "padding: 8px; background-color: #f9f9f9; "
            "border-radius: 5px; font-size: 10px;"
        )
        shortcuts_layout.addWidget(shortcuts_text)
        
        shortcuts_group.setLayout(shortcuts_layout)
        layout.addWidget(shortcuts_group)
        
        display_group = QGroupBox("Display")
        display_layout = QVBoxLayout()
        
        display_info = QLabel(
            "💡 <b>Tips:</b><br>"
            "• Mouse wheel to zoom<br>"
            "• Click & drag to pan<br>"
            "• Scrollbar under spectrogram"
        )
        display_info.setWordWrap(True)
        display_info.setStyleSheet(
            "padding: 6px; background-color: #e3f2fd; "
            "border-radius: 4px; font-size: 10px;"
        )
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