"""
View Controls Panel
Handles zoom, viewport scrolling, and display settings
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QCheckBox, 
    QGroupBox, QSlider
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor


class ViewPanel(QWidget):
    zoom_toggled = pyqtSignal(bool)
    zoom_reset_requested = pyqtSignal()
    viewport_scrolled = pyqtSignal(int)
    cursor_changed = pyqtSignal(object)  # QCursor
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("View Controls")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Zoom group
        zoom_group = QGroupBox("Zoom Controls")
        zoom_layout = QVBoxLayout()
        
        self.zoom_checkbox = QCheckBox("🔍 Enable Zoom Mode")
        self.zoom_checkbox.stateChanged.connect(self.on_zoom_toggled)
        zoom_layout.addWidget(self.zoom_checkbox)
        
        zoom_info = QLabel("Click and drag on spectrogram to zoom into a region")
        zoom_info.setWordWrap(True)
        zoom_info.setStyleSheet("color: #666; font-size: 11px; margin-left: 20px;")
        zoom_layout.addWidget(zoom_info)
        
        reset_btn = QPushButton("↺ Reset Zoom")
        reset_btn.setMinimumHeight(35)
        reset_btn.clicked.connect(self.on_reset_zoom)
        zoom_layout.addWidget(reset_btn)
        
        zoom_group.setLayout(zoom_layout)
        layout.addWidget(zoom_group)
        
        # Keyboard shortcuts group
        shortcuts_group = QGroupBox("⌨️ Keyboard Shortcuts")
        shortcuts_layout = QVBoxLayout()
        
        shortcuts_text = QLabel(
            "<b>R</b> - Reset zoom<br>"
            "<b>Space</b> - Play/Pause main audio<br>"
            "<b>Shift+Space</b> - Play/Pause selection<br>"
            "<b>- / =</b> - Decrease/Increase brush size"
        )
        shortcuts_text.setStyleSheet("padding: 10px; background-color: #f9f9f9; border-radius: 5px;")
        shortcuts_layout.addWidget(shortcuts_text)
        
        shortcuts_group.setLayout(shortcuts_layout)
        layout.addWidget(shortcuts_group)
        
        # Display settings group
        display_group = QGroupBox("Display Settings")
        display_layout = QVBoxLayout()
        
        display_info = QLabel(
            "💡 <b>Tips:</b><br>"
            "• Use mouse wheel to zoom in/out<br>"
            "• Click and drag to pan<br>"
            "• Viewport scrollbar appears below spectrogram"
        )
        display_info.setWordWrap(True)
        display_info.setStyleSheet("padding: 8px; background-color: #e3f2fd; border-radius: 4px;")
        display_layout.addWidget(display_info)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        layout.addStretch()
        
    def on_zoom_toggled(self, state):
        """Handle zoom checkbox toggle"""
        enabled = (state == Qt.CheckState.Checked.value)
        self.zoom_toggled.emit(enabled)
        
        if enabled:
            self.cursor_changed.emit(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.cursor_changed.emit(QCursor(Qt.CursorShape.ArrowCursor))
            
    def on_reset_zoom(self):
        """Request zoom reset"""
        self.zoom_reset_requested.emit()
        
    def disable_zoom(self):
        """Disable zoom mode (called from other panels)"""
        self.zoom_checkbox.setChecked(False)