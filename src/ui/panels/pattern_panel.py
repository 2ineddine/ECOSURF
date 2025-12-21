"""
Pattern Selection Panel - Compact Version
Reduced brush section, more space for operations
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QCheckBox, 
    QSlider, QGroupBox, QFileDialog, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor
import soundfile as sf


class PatternPanel(QWidget):
    brush_toggled = pyqtSignal(bool)
    brush_size_changed = pyqtSignal(int)
    selection_cleared = pyqtSignal()
    extract_requested = pyqtSignal()
    play_selection_requested = pyqtSignal()
    cursor_changed = pyqtSignal(object)  # QCursor
    rect_mode_toggled = pyqtSignal(bool)
    def __init__(self):
        super().__init__()
        self.selection_audio = None
        self.selection_meta = None
        self.init_ui()
        
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Pattern Selection")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 3px;")
        layout.addWidget(title)
        
        # Brush controls group - COMPACT
        brush_group = QGroupBox("Brush")
        brush_layout = QVBoxLayout()
        brush_layout.setSpacing(4)
        
        self.brush_checkbox = QCheckBox("🖌 Enable")
        self.brush_checkbox.setStyleSheet("font-size: 11px;")
        self.brush_checkbox.stateChanged.connect(self.on_brush_toggled)
        brush_layout.addWidget(self.brush_checkbox)
        self.rect_checkbox = QCheckBox("▭ Rectangle Select")
        self.rect_checkbox.setStyleSheet("font-size: 11px;")
        self.rect_checkbox.stateChanged.connect(self.on_rect_toggled)
        brush_layout.addWidget(self.rect_checkbox)
        
        # Compact brush size control
        size_container = QWidget()
        size_layout = QVBoxLayout(size_container)
        size_layout.setSpacing(2)
        size_layout.setContentsMargins(0, 0, 0, 0)
        
        size_label = QLabel("Size:")
        size_label.setStyleSheet("font-size: 10px; font-weight: bold;")
        size_layout.addWidget(size_label)
        
        self.brush_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_slider.setMinimum(5)
        self.brush_slider.setMaximum(100)
        self.brush_slider.setValue(20)
        self.brush_slider.setMaximumHeight(20)
        self.brush_slider.valueChanged.connect(self.on_brush_size_changed)
        size_layout.addWidget(self.brush_slider)
        
        self.brush_size_label = QLabel("20 px")
        self.brush_size_label.setStyleSheet("color: #666; font-size: 9px;")
        size_layout.addWidget(self.brush_size_label)
        
        brush_layout.addWidget(size_container)
        
        clear_btn = QPushButton("🗑 Clear")
        clear_btn.setMaximumHeight(26)
        clear_btn.setStyleSheet("font-size: 10px;")
        clear_btn.clicked.connect(self.on_clear_selection)
        brush_layout.addWidget(clear_btn)
        
        brush_group.setLayout(brush_layout)
        layout.addWidget(brush_group)
        
        # Selection operations group - EXPANDED
        operations_group = QGroupBox("Selection Operations")
        operations_layout = QVBoxLayout()
        operations_layout.setSpacing(6)
        
        extract_btn = QPushButton("✂ Extract Selection")
        extract_btn.setMinimumHeight(38)
        extract_btn.clicked.connect(self.on_extract_selection)
        extract_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        operations_layout.addWidget(extract_btn)
        
        self.play_selection_btn = QPushButton("▶ Play Selection")
        self.play_selection_btn.setEnabled(False)
        self.play_selection_btn.setMinimumHeight(35)
        self.play_selection_btn.setStyleSheet("font-size: 11px;")
        self.play_selection_btn.clicked.connect(self.on_play_selection)
        operations_layout.addWidget(self.play_selection_btn)
        
        self.save_btn = QPushButton("💾 Save Selection")
        self.save_btn.setEnabled(False)
        self.save_btn.setMinimumHeight(35)
        self.save_btn.setStyleSheet("font-size: 11px;")
        self.save_btn.clicked.connect(self.on_save_selection)
        operations_layout.addWidget(self.save_btn)
        
        # Status with more height
        self.selection_status = QLabel("No selection extracted")
        self.selection_status.setStyleSheet(
            "padding: 10px; background-color: #f9f9f9; "
            "border-radius: 4px; font-size: 11px; min-height: 50px;"
        )
        self.selection_status.setWordWrap(True)
        operations_layout.addWidget(self.selection_status)
        
        operations_group.setLayout(operations_layout)
        layout.addWidget(operations_group)
        
        # Compact tips
        tips_label = QLabel("💡 <b>Keys:</b> Shift+Space (play) | -/= (brush size)")
        tips_label.setWordWrap(True)
        tips_label.setStyleSheet(
            "padding: 5px; background-color: #e3f2fd; "
            "border-radius: 3px; font-size: 9px;"
        )
        layout.addWidget(tips_label)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
    def on_brush_toggled(self, state):
        """Handle brush checkbox toggle"""
        enabled = (state == Qt.CheckState.Checked.value)
        self.brush_toggled.emit(enabled)
        
        if enabled:
            self.cursor_changed.emit(QCursor(Qt.CursorShape.CrossCursor))
            self.rect_checkbox.setChecked(False)
        else:
            self.cursor_changed.emit(QCursor(Qt.CursorShape.ArrowCursor))

    def on_rect_toggled(self, state):
        """Handle rectangle selection toggle"""
        enabled = (state == Qt.CheckState.Checked.value)
        
        if enabled:
            # Disable brush when rect is enabled
            self.brush_checkbox.setChecked(False)
            # Emit signal to enable rectangle mode
            try:
                self.rect_mode_toggled.emit(True)
            except:
                pass
            self.cursor_changed.emit(QCursor(Qt.CursorShape.CrossCursor))
        else:
            try:
                self.rect_mode_toggled.emit(False)
            except:
                pass
            self.cursor_changed.emit(QCursor(Qt.CursorShape.ArrowCursor))      
    def on_brush_size_changed(self, value):
        """Handle brush size slider change"""
        self.brush_size_label.setText(f"{value} px")
        self.brush_size_changed.emit(value)
        
    def on_clear_selection(self):
        """Handle clear selection button"""
        self.selection_cleared.emit()
        self.selection_status.setText("Selection cleared")
        
    def on_extract_selection(self):
        """Handle extract selection button"""
        self.extract_requested.emit()
        
    def on_play_selection(self):
        """Handle play selection button"""
        self.play_selection_requested.emit()
        
    def on_save_selection(self):
        """Handle save selection button"""
        if self.selection_audio is None:
            self.selection_status.setText("⚠️ No selection to save")
            return
            
        default_name = "selection.wav"
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Selection", 
            default_name, 
            "WAV files (*.wav)"
        )
        
        if not filename:
            return
            
        try:
            if not filename.lower().endswith('.wav'):
                filename += '.wav'
                
            sr = int(self.selection_meta.get('sample_rate', 22050))
            sf.write(filename, self.selection_audio, sr)
            
            # Save metadata
            meta_file = os.path.splitext(filename)[0] + '_info.txt'
            with open(meta_file, 'w') as f:
                f.write(str(self.selection_meta))
                
            self.selection_status.setText(
                f"✅ <b>Saved successfully</b><br>"
                f"File: {os.path.basename(filename)}"
            )
        except Exception as e:
            self.selection_status.setText(f"❌ Error: {str(e)[:40]}")
            
    def set_selection_audio(self, audio, meta):
        """Set the extracted selection audio"""
        self.selection_audio = audio
        self.selection_meta = meta
        self.play_selection_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        
        duration = len(audio) / meta.get('sample_rate', 22050)
        self.selection_status.setText(
            f"✅ <b>Selection extracted successfully!</b><br>"
            f"<b>Duration:</b> {duration:.2f} seconds<br>"
            f"<b>Samples:</b> {len(audio):,}<br>"
            f"Ready to play or save"
        )
        
    def disable_brush(self):
        """Disable brush mode (called from other panels)"""
        self.brush_checkbox.setChecked(False)
        self.rect_checkbox.setChecked(False)
        
    def change_brush_size(self, delta):
        """Change brush size by delta (for keyboard shortcuts)"""
        new_val = max(5, min(100, self.brush_slider.value() + delta))
        self.brush_slider.setValue(new_val)