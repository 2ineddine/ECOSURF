"""
View Panel V2 - Professional blue styling
Clean view and zoom controls
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QCheckBox, QGroupBox, QHBoxLayout, QSlider
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor

# Style cohérent bleu professionnel
PANEL_STYLE = """
    QWidget {
        background-color: white;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QGroupBox {
        font-weight: 600;
        font-size: 11px;
        color: #2C3E50;
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        margin-top: 12px;
        padding: 12px 8px 8px 8px;
        background-color: #FAFBFC;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 6px;
        background-color: white;
    }
    QPushButton {
        background-color: #3498DB;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #2980B9;
    }
    QPushButton:pressed {
        background-color: #1F6DA8;
    }
    QPushButton:disabled {
        background-color: #BDC3C7;
        color: #7F8C8D;
    }
    QCheckBox {
        font-size: 12px;
        color: #2C3E50;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid #BDC3C7;
        border-radius: 4px;
        background-color: white;
    }
    QCheckBox::indicator:checked {
        background-color: #3498DB;
        border-color: #3498DB;
    }
    QCheckBox::indicator:hover {
        border-color: #3498DB;
    }
    QSlider::groove:horizontal {
        border: 1px solid #E0E0E0;
        height: 6px;
        background: #ECEFF1;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: #3498DB;
        border: none;
        width: 14px;
        height: 14px;
        margin: -4px 0;
        border-radius: 7px;
    }
    QSlider::sub-page:horizontal {
        background: #3498DB;
        border-radius: 3px;
    }
"""


class ViewPanel(QWidget):
    """View controls panel - Professional blue styling"""
    zoom_toggled = pyqtSignal(bool)
    zoom_reset_requested = pyqtSignal()
    viewport_scrolled = pyqtSignal(int)
    cursor_changed = pyqtSignal(object)
    zoom_level_changed = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(PANEL_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("View")
        header.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #2C3E50;
                padding-bottom: 4px;
                border-bottom: 2px solid #3498DB;
            }
        """)
        layout.addWidget(header)
        
        # Zoom Controls
        zoom_group = QGroupBox("Zoom")
        zoom_layout = QVBoxLayout()
        zoom_layout.setSpacing(10)
        
        # Enable zoom checkbox
        self.zoom_checkbox = QCheckBox("Enable zoom mode")
        self.zoom_checkbox.stateChanged.connect(self.on_zoom_toggled)
        zoom_layout.addWidget(self.zoom_checkbox)
        
        # Zoom buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(36, 36)
        self.zoom_in_btn.setToolTip("Zoom In")
        self.zoom_in_btn.clicked.connect(lambda: self.on_zoom_level(1.5))
        
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedSize(36, 36)
        self.zoom_out_btn.setToolTip("Zoom Out")
        self.zoom_out_btn.clicked.connect(lambda: self.on_zoom_level(0.67))
        
        self.zoom_reset_btn = QPushButton("R")
        self.zoom_reset_btn.setFixedSize(36, 36)
        self.zoom_reset_btn.setToolTip("Reset Zoom")
        self.zoom_reset_btn.clicked.connect(self.on_zoom_reset)
        
        self.zoom_fit_btn = QPushButton("Fit")
        self.zoom_fit_btn.setFixedSize(36, 36)
        self.zoom_fit_btn.setToolTip("Fit to Window")
        
        btn_row.addWidget(self.zoom_in_btn)
        btn_row.addWidget(self.zoom_out_btn)
        btn_row.addWidget(self.zoom_reset_btn)
        btn_row.addWidget(self.zoom_fit_btn)
        btn_row.addStretch()
        zoom_layout.addLayout(btn_row)
        
        # Zoom level display
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("""
            font-size: 12px;
            font-weight: 500;
            color: #3498DB;
        """)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        zoom_layout.addWidget(self.zoom_label)
        
        zoom_group.setLayout(zoom_layout)
        layout.addWidget(zoom_group)
        
        # Navigation
        nav_group = QGroupBox("Navigation")
        nav_layout = QVBoxLayout()
        nav_layout.setSpacing(8)
        
        # Scroll position
        scroll_row = QHBoxLayout()
        scroll_label = QLabel("Position:")
        scroll_label.setStyleSheet("font-size: 12px; color: #2C3E50;")
        self.scroll_slider = QSlider(Qt.Orientation.Horizontal)
        self.scroll_slider.setRange(0, 100)
        self.scroll_slider.setValue(0)
        self.scroll_slider.valueChanged.connect(self.on_scroll_changed)
        scroll_row.addWidget(scroll_label)
        scroll_row.addWidget(self.scroll_slider)
        nav_layout.addLayout(scroll_row)
        
        nav_group.setLayout(nav_layout)
        layout.addWidget(nav_group)
        
        # Cursor Mode
        cursor_group = QGroupBox("Cursor")
        cursor_layout = QHBoxLayout()
        cursor_layout.setSpacing(8)
        
        self.pointer_btn = QPushButton("Ptr")
        self.pointer_btn.setFixedSize(36, 36)
        self.pointer_btn.setToolTip("Pointer")
        self.pointer_btn.setCheckable(True)
        self.pointer_btn.setChecked(True)
        self.pointer_btn.clicked.connect(lambda: self.set_cursor_mode("pointer"))
        
        self.crosshair_btn = QPushButton("+")
        self.crosshair_btn.setFixedSize(36, 36)
        self.crosshair_btn.setToolTip("Crosshair")
        self.crosshair_btn.setCheckable(True)
        self.crosshair_btn.clicked.connect(lambda: self.set_cursor_mode("crosshair"))
        
        self.hand_btn = QPushButton("Pan")
        self.hand_btn.setFixedSize(36, 36)
        self.hand_btn.setToolTip("Pan")
        self.hand_btn.setCheckable(True)
        self.hand_btn.clicked.connect(lambda: self.set_cursor_mode("hand"))
        
        cursor_layout.addWidget(self.pointer_btn)
        cursor_layout.addWidget(self.crosshair_btn)
        cursor_layout.addWidget(self.hand_btn)
        cursor_layout.addStretch()
        
        cursor_group.setLayout(cursor_layout)
        layout.addWidget(cursor_group)
        
        layout.addStretch()
        
    def on_zoom_toggled(self, state):
        enabled = state == Qt.CheckState.Checked.value
        self.zoom_toggled.emit(enabled)
        
    def on_zoom_reset(self):
        self.zoom_label.setText("100%")
        self.zoom_reset_requested.emit()
        
    def on_zoom_level(self, factor):
        # Update display
        current = int(self.zoom_label.text().replace("%", ""))
        new_level = max(10, min(500, int(current * factor)))
        self.zoom_label.setText(f"{new_level}%")
        self.zoom_level_changed.emit(factor)
        
    def on_scroll_changed(self, value):
        self.viewport_scrolled.emit(value)
        
    def set_cursor_mode(self, mode):
        # Update button states
        self.pointer_btn.setChecked(mode == "pointer")
        self.crosshair_btn.setChecked(mode == "crosshair")
        self.hand_btn.setChecked(mode == "hand")
        
        # Emit cursor
        cursors = {
            "pointer": Qt.CursorShape.ArrowCursor,
            "crosshair": Qt.CursorShape.CrossCursor,
            "hand": Qt.CursorShape.OpenHandCursor
        }
        self.cursor_changed.emit(QCursor(cursors.get(mode, Qt.CursorShape.ArrowCursor)))
        
    def set_zoom_level(self, level):
        """External update of zoom level"""
        self.zoom_label.setText(f"{int(level)}%")

    def disable_zoom(self):
        """Disable zoom mode"""
        self.zoom_checkbox.setChecked(False)
