"""
Pattern Panel V2 - Professional blue styling
Clean pattern selection tools
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QCheckBox,
    QSlider, QGroupBox, QFileDialog, QHBoxLayout, QProgressBar
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor
import soundfile as sf

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


class PatternPanel(QWidget):
    """Pattern selection panel - Professional blue styling"""
    brush_toggled = pyqtSignal(bool)
    brush_size_changed = pyqtSignal(int)
    selection_cleared = pyqtSignal()
    extract_requested = pyqtSignal()
    play_selection_requested = pyqtSignal()
    cursor_changed = pyqtSignal(object)
    rect_mode_toggled = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.selection_audio = None
        self.selection_meta = None
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(PANEL_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("Pattern")
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
        
        # Selection Tools
        tools_group = QGroupBox("Selection Mode")
        tools_layout = QVBoxLayout()
        tools_layout.setSpacing(8)
        
        # Mode checkboxes
        self.brush_checkbox = QCheckBox("Freehand Brush")
        self.brush_checkbox.stateChanged.connect(self.on_brush_toggled)
        tools_layout.addWidget(self.brush_checkbox)
        
        self.rect_checkbox = QCheckBox("Rectangle")
        self.rect_checkbox.stateChanged.connect(self.on_rect_toggled)
        tools_layout.addWidget(self.rect_checkbox)
        
        # Brush size
        size_row = QHBoxLayout()
        size_label = QLabel("Size:")
        size_label.setStyleSheet("font-size: 12px; color: #2C3E50;")
        self.brush_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_slider.setMinimum(5)
        self.brush_slider.setMaximum(100)
        self.brush_slider.setValue(20)
        self.brush_slider.valueChanged.connect(self.on_brush_size_changed)
        self.size_value = QLabel("20")
        self.size_value.setStyleSheet("font-size: 11px; color: #3498DB; font-weight: 500;")
        self.size_value.setFixedWidth(30)
        
        size_row.addWidget(size_label)
        size_row.addWidget(self.brush_slider)
        size_row.addWidget(self.size_value)
        tools_layout.addLayout(size_row)
        
        tools_group.setLayout(tools_layout)
        layout.addWidget(tools_group)
        
        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)
        
        # Play selection
        self.play_btn = QPushButton("Play Selection")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.on_play_selection)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #229954; }
            QPushButton:disabled { background-color: #BDC3C7; color: #7F8C8D; }
        """)
        actions_layout.addWidget(self.play_btn)
        
        # Extract button
        self.extract_btn = QPushButton("Extract Pattern")
        self.extract_btn.setEnabled(False)
        self.extract_btn.clicked.connect(self.on_extract)
        actions_layout.addWidget(self.extract_btn)
        
        # Save button
        self.save_btn = QPushButton("Save Audio")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.on_save)
        actions_layout.addWidget(self.save_btn)
        
        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.on_clear)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #C0392B; }
        """)
        actions_layout.addWidget(self.clear_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #E0E0E0;
                border-radius: 3px;
                background-color: #ECEFF1;
            }
            QProgressBar::chunk {
                background-color: #3498DB;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Status
        self.status_label = QLabel("No selection")
        self.status_label.setStyleSheet("font-size: 11px; color: #7F8C8D;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        layout.addStretch()
        
    def on_brush_toggled(self, state):
        enabled = state == Qt.CheckState.Checked.value
        if enabled:
            self.rect_checkbox.setChecked(False)
        self.brush_toggled.emit(enabled)
        if enabled:
            self.cursor_changed.emit(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.cursor_changed.emit(QCursor(Qt.CursorShape.ArrowCursor))
            
    def on_rect_toggled(self, state):
        enabled = state == Qt.CheckState.Checked.value
        if enabled:
            self.brush_checkbox.setChecked(False)
        self.rect_mode_toggled.emit(enabled)
        if enabled:
            self.cursor_changed.emit(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.cursor_changed.emit(QCursor(Qt.CursorShape.ArrowCursor))
            
    def on_brush_size_changed(self, value):
        self.size_value.setText(str(value))
        self.brush_size_changed.emit(value)
        
    def on_play_selection(self):
        self.play_selection_requested.emit()
        
    def on_extract(self):
        self.extract_requested.emit()
        
    def on_clear(self):
        self.selection_audio = None
        self.selection_meta = None
        self.update_buttons_state()
        self.status_label.setText("No selection")
        self.selection_cleared.emit()
        
    def on_save(self):
        if self.selection_audio is None:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Audio", "", "WAV (*.wav)"
        )
        if file_path:
            try:
                sr = self.selection_meta.get('sr', 32000) if self.selection_meta else 32000
                sf.write(file_path, self.selection_audio, sr)
                self.status_label.setText("Saved!")
                self.status_label.setStyleSheet("font-size: 11px; color: #27AE60;")
            except Exception as e:
                self.status_label.setText("Error")
                self.status_label.setStyleSheet("font-size: 11px; color: #E74C3C;")
                
    def set_selection_data(self, audio_data, meta):
        """Set extracted selection data"""
        self.selection_audio = audio_data
        self.selection_meta = meta
        self.update_buttons_state()
        if audio_data is not None:
            duration = len(audio_data) / meta.get('sr', 32000) if meta else 0
            self.status_label.setText(f"{duration:.2f}s selected")
            self.status_label.setStyleSheet("font-size: 11px; color: #27AE60;")
            
    def update_buttons_state(self):
        has_selection = self.selection_audio is not None
        self.play_btn.setEnabled(has_selection)
        self.save_btn.setEnabled(has_selection)
        self.extract_btn.setEnabled(True)  # Can always try to extract

    def disable_brush(self):
        """Disable brush mode"""
        self.brush_checkbox.setChecked(False)
        self.rect_checkbox.setChecked(False)

    def update_progress(self, value, text=""):
        """Update progress bar and status"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(value)
        if text:
            self.status_label.setText(text)
            self.status_label.setStyleSheet("font-size: 11px; color: #3498DB;")

    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.setVisible(False)
        self.status_label.setStyleSheet("font-size: 11px; color: #7F8C8D;")

    def change_brush_size(self, delta):
        """Change brush size by delta"""
        current = self.brush_slider.value()
        new_val = max(self.brush_slider.minimum(), min(self.brush_slider.maximum(), current + delta))
        self.brush_slider.setValue(new_val)
