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
from PyQt6.QtWidgets import QFrame


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
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        # Content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        
        # Ubuntu-style title
        title = QLabel("Pattern Selection")
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
        
        # Brush controls group
        brush_group = QGroupBox("Selection Tools")
        brush_group.setStyleSheet("""
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
        brush_layout = QVBoxLayout()
        brush_layout.setContentsMargins(12, 15, 12, 12)
        brush_layout.setSpacing(10)
        
        # Ubuntu-style checkboxes
        self.brush_checkbox = QCheckBox("Freehand Brush")
        self.brush_checkbox.setStyleSheet("""
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
        self.brush_checkbox.stateChanged.connect(self.on_brush_toggled)
        brush_layout.addWidget(self.brush_checkbox)
        
        self.rect_checkbox = QCheckBox("Rectangle Select")
        self.rect_checkbox.setStyleSheet("""
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
        self.rect_checkbox.stateChanged.connect(self.on_rect_toggled)
        brush_layout.addWidget(self.rect_checkbox)
        
        # Brush size control
        size_label = QLabel("Brush Size:")
        size_label.setStyleSheet("font-size: 12px; color: #333333; font-weight: bold; margin-top: 8px;")
        brush_layout.addWidget(size_label)
        
        self.brush_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_slider.setMinimum(5)
        self.brush_slider.setMaximum(100)
        self.brush_slider.setValue(20)
        self.brush_slider.setMaximumHeight(20)
        self.brush_slider.valueChanged.connect(self.on_brush_size_changed)
        self.brush_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #CCCCCC;
                height: 6px;
                background: white;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #77216F;
                border: 2px solid #77216F;
                width: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #5E2750;
                border: 2px solid #5E2750;
            }
            QSlider::add-page:horizontal {
                background: #E0E0E0;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #77216F;
                border-radius: 3px;
            }
        """)
        brush_layout.addWidget(self.brush_slider)
        
        self.brush_size_label = QLabel("20 px")
        self.brush_size_label.setStyleSheet("""
            QLabel {
                color: #5E5E5E;
                font-size: 11px;
                padding-left: 5px;
            }
        """)
        brush_layout.addWidget(self.brush_size_label)
        
        # Clear button
        clear_btn = QPushButton("Clear Selection")
        clear_btn.setMinimumHeight(32)
        clear_btn.clicked.connect(self.on_clear_selection)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F2;
                color: #333333;
                font-size: 12px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px;
                margin-top: 8px;
            }
            QPushButton:hover {
                background-color: #E5E5E5;
                border: 1px solid #888888;
            }
        """)
        brush_layout.addWidget(clear_btn)
        
        brush_group.setLayout(brush_layout)
        layout.addWidget(brush_group)
        
        # Selection operations group
        operations_group = QGroupBox("Selection Operations")
        operations_group.setStyleSheet("""
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
        operations_layout = QVBoxLayout()
        operations_layout.setContentsMargins(12, 15, 12, 12)
        operations_layout.setSpacing(10)
        
        # Extract button
        self.extract_btn = QPushButton("Extract Selection")
        self.extract_btn.setMinimumHeight(36)
        self.extract_btn.clicked.connect(self.on_extract_selection)
        self.extract_btn.setStyleSheet("""
            QPushButton {
                background-color: #E95420;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #D34615;
            }
        """)
        operations_layout.addWidget(self.extract_btn)
        
        # Progress bar for extraction
        from PyQt6.QtWidgets import QProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #E95420;
                border-radius: 3px;
            }
        """)
        operations_layout.addWidget(self.progress_bar)
        
        # Play selection button
        self.play_selection_btn = QPushButton("Play Selection")
        self.play_selection_btn.setEnabled(False)
        self.play_selection_btn.setMinimumHeight(32)
        self.play_selection_btn.clicked.connect(self.on_play_selection)
        self.play_selection_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F2;
                color: #333333;
                font-size: 12px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover:enabled {
                background-color: #E5E5E5;
                border: 1px solid #888888;
            }
            QPushButton:disabled {
                background-color: #FAFAFA;
                color: #BBBBBB;
                border: 1px solid #E0E0E0;
            }
        """)
        operations_layout.addWidget(self.play_selection_btn)
        
        # Save selection button
        self.save_btn = QPushButton("Save Selection as WAV")
        self.save_btn.setEnabled(False)
        self.save_btn.setMinimumHeight(32)
        self.save_btn.clicked.connect(self.on_save_selection)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #77216F;
                color: white;
                font-size: 12px;
                border: none;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover:enabled {
                background-color: #5E2750;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #888888;
            }
        """)
        operations_layout.addWidget(self.save_btn)
        
        # Status display
        self.selection_status = QLabel("No selection extracted")
        self.selection_status.setWordWrap(True)
        self.selection_status.setStyleSheet("""
            QLabel {
                padding: 12px;
                background-color: white;
                border: 1px solid #DEDEDE;
                border-radius: 3px;
                font-size: 11px;
                color: #5E5E5E;
                line-height: 1.4;
                min-height: 60px;
            }
        """)
        operations_layout.addWidget(self.selection_status)
        
        operations_group.setLayout(operations_layout)
        layout.addWidget(operations_group)
        
        # Tips section
        tips_group = QGroupBox("Keyboard Shortcuts")
        tips_group.setStyleSheet("""
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
        tips_layout = QVBoxLayout()
        tips_layout.setContentsMargins(12, 15, 12, 12)
        
        tips_label = QLabel(
            "• <b>- / =</b> - Adjust brush size<br>"
            "• <b>Shift+Space</b> - Play/Pause selection<br>"
            "• <b>Space</b> - Play/Pause main audio<br>"
            "• <b>R</b> - Reset zoom"
        )
        tips_label.setWordWrap(True)
        tips_label.setStyleSheet("""
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
        tips_layout.addWidget(tips_label)
        
        tips_group.setLayout(tips_layout)
        layout.addWidget(tips_group)
        
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
        self.show_progress(True)
        self.extract_requested.emit()
    
    def show_progress(self, show, value=0):
        """Show or hide progress bar"""
        self.progress_bar.setVisible(show)
        self.progress_bar.setValue(value)
        self.extract_btn.setEnabled(not show)
    
    def update_progress(self, value, text=None):
        """Update progress bar value"""
        self.progress_bar.setValue(value)
        if text:
            self.progress_bar.setFormat(text)
    
    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.setVisible(False)
        self.extract_btn.setEnabled(True)
        
    def on_play_selection(self):
        """Handle play selection button"""
        self.play_selection_requested.emit()
        
    def on_save_selection(self):
        """Handle save selection button"""
        if self.selection_audio is None:
            self.selection_status.setText("No selection to save")
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
                f"Saved successfully\nFile: {os.path.basename(filename)}"
            )
        except Exception as e:
            self.selection_status.setText(f"Error: {str(e)[:40]}")
            
    def set_selection_audio(self, audio, meta):
        """Set the extracted selection audio"""
        self.selection_audio = audio
        self.selection_meta = meta
        self.play_selection_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        
        duration = len(audio) / meta.get('sample_rate', 22050)
        self.selection_status.setText(
            f"Selection extracted successfully!\n"
            f"Duration: {duration:.2f} seconds\n"
            f"Samples: {len(audio):,}\n"
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