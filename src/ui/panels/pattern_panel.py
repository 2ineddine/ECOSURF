"""
Pattern Selection Panel
Handles brush selection, extraction, and pattern audio operations
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QCheckBox, 
    QSlider, QGroupBox, QFileDialog
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
    
    def __init__(self):
        super().__init__()
        self.selection_audio = None
        self.selection_meta = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Pattern Selection")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Brush controls group
        brush_group = QGroupBox("Brush Tool")
        brush_layout = QVBoxLayout()
        
        self.brush_checkbox = QCheckBox("🖌 Enable Brush Mode")
        self.brush_checkbox.stateChanged.connect(self.on_brush_toggled)
        brush_layout.addWidget(self.brush_checkbox)
        
        brush_info = QLabel("Click and drag on spectrogram to paint selection")
        brush_info.setWordWrap(True)
        brush_info.setStyleSheet("color: #666; font-size: 11px; margin-left: 20px;")
        brush_layout.addWidget(brush_info)
        
        size_label = QLabel("Brush Size:")
        size_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        brush_layout.addWidget(size_label)
        
        self.brush_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_slider.setMinimum(5)
        self.brush_slider.setMaximum(100)
        self.brush_slider.setValue(20)
        self.brush_slider.valueChanged.connect(self.on_brush_size_changed)
        brush_layout.addWidget(self.brush_slider)
        
        self.brush_size_label = QLabel("20 px")
        self.brush_size_label.setStyleSheet("color: #666;")
        brush_layout.addWidget(self.brush_size_label)
        
        clear_btn = QPushButton("🗑 Clear Selection")
        clear_btn.setMinimumHeight(35)
        clear_btn.clicked.connect(self.on_clear_selection)
        brush_layout.addWidget(clear_btn)
        
        brush_group.setLayout(brush_layout)
        layout.addWidget(brush_group)
        
        # Selection operations group
        operations_group = QGroupBox("Selection Operations")
        operations_layout = QVBoxLayout()
        
        extract_btn = QPushButton("✂ Extract Selection")
        extract_btn.setMinimumHeight(40)
        extract_btn.clicked.connect(self.on_extract_selection)
        extract_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
            }
        """)
        operations_layout.addWidget(extract_btn)
        
        self.play_selection_btn = QPushButton("▶ Play Selection")
        self.play_selection_btn.setEnabled(False)
        self.play_selection_btn.setMinimumHeight(40)
        self.play_selection_btn.clicked.connect(self.on_play_selection)
        operations_layout.addWidget(self.play_selection_btn)
        
        self.save_btn = QPushButton("💾 Save Selection")
        self.save_btn.setEnabled(False)
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self.on_save_selection)
        operations_layout.addWidget(self.save_btn)
        
        self.selection_status = QLabel("No selection extracted")
        self.selection_status.setStyleSheet(
            "padding: 8px; background-color: #f9f9f9; border-radius: 4px;"
        )
        self.selection_status.setWordWrap(True)
        operations_layout.addWidget(self.selection_status)
        
        operations_group.setLayout(operations_layout)
        layout.addWidget(operations_group)
        
        # Info group
        info_group = QGroupBox("💡 Usage Tips")
        info_layout = QVBoxLayout()
        
        info_text = QLabel(
            "1. Enable brush mode<br>"
            "2. Paint over the pattern on spectrogram<br>"
            "3. Click 'Extract Selection' to create audio<br>"
            "4. Play or save the extracted pattern<br>"
            "5. Use <b>Shift+Space</b> to play selection<br>"
            "6. Use <b>- / =</b> keys to adjust brush size"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("padding: 8px; background-color: #e3f2fd; border-radius: 4px;")
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        
    def on_brush_toggled(self, state):
        """Handle brush checkbox toggle"""
        enabled = (state == Qt.CheckState.Checked.value)
        self.brush_toggled.emit(enabled)
        
        if enabled:
            self.cursor_changed.emit(QCursor(Qt.CursorShape.CrossCursor))
        else:
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
            "Save Extracted Selection", 
            default_name, 
            "WAV files (*.wav);;All files (*.*)"
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
                
            self.selection_status.setText(f"✅ Saved: {os.path.basename(filename)}")
        except Exception as e:
            self.selection_status.setText(f"❌ Error: {e}")
            
    def set_selection_audio(self, audio, meta):
        """Set the extracted selection audio"""
        self.selection_audio = audio
        self.selection_meta = meta
        self.play_selection_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        
        duration = len(audio) / meta.get('sample_rate', 22050)
        self.selection_status.setText(
            f"✅ Selection extracted<br>"
            f"<b>Duration:</b> {duration:.2f}s<br>"
            f"<b>Samples:</b> {len(audio)}"
        )
        
    def disable_brush(self):
        """Disable brush mode (called from other panels)"""
        self.brush_checkbox.setChecked(False)
        
    def change_brush_size(self, delta):
        """Change brush size by delta (for keyboard shortcuts)"""
        new_val = max(5, min(100, self.brush_slider.value() + delta))
        self.brush_slider.setValue(new_val)