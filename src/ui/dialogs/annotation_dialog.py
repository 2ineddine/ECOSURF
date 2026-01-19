"""
ECOSURF Annotation Dialog
Dialog for creating new audio annotations
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTextEdit, QFrame, QSlider, QGridLayout,
    QGroupBox, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.annotation_manager import AnnotationManager


class AnnotationDialog(QDialog):
    """Dialog for creating a new annotation"""

    annotation_saved = pyqtSignal(dict)

    def __init__(self, parent=None, audio_info=None):
        """
        Initialize annotation dialog

        Args:
            parent: Parent widget
            audio_info: Dictionary with current audio context:
                - file_path: Full path to audio file
                - file_name: Just the filename
                - start_time: Start time in seconds
                - end_time: End time in seconds
                - duration: Duration in seconds
                - channel: Audio channel (L/R/Mono)
                - sample_rate: Sample rate in Hz
                - freq_min: Min frequency of selection (optional)
                - freq_max: Max frequency of selection (optional)
                - source_type: 'local' or 'database'
        """
        super().__init__(parent)
        self.audio_info = audio_info or {}
        self.annotation_manager = AnnotationManager()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("New Annotation")
        self.setFixedSize(480, 520)
        self.setStyleSheet("""
            QDialog {
                background: #FAFBFC;
            }
            QLabel {
                color: #2C3E50;
                font-size: 12px;
            }
            QLabel#title {
                font-size: 16px;
                font-weight: bold;
                color: #2C3E50;
                padding: 8px 0;
            }
            QLabel#section {
                font-size: 11px;
                font-weight: 600;
                color: #7F8C8D;
                text-transform: uppercase;
            }
            QGroupBox {
                font-weight: 600;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                margin-top: 12px;
                padding: 12px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #2C3E50;
            }
            QComboBox {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px 12px;
                min-height: 32px;
                font-size: 12px;
            }
            QComboBox:focus {
                border-color: #3498DB;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QTextEdit {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QTextEdit:focus {
                border-color: #3498DB;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #E0E0E0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #3498DB;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::sub-page:horizontal {
                background: #3498DB;
                border-radius: 3px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel("New Annotation")
        title.setObjectName("title")
        layout.addWidget(title)

        # Audio Info Section
        info_group = QGroupBox("Audio Information")
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(8)

        # File name
        info_layout.addWidget(QLabel("File:"), 0, 0)
        file_label = QLabel(self.audio_info.get('file_name', 'No file loaded'))
        file_label.setStyleSheet("color: #3498DB; font-weight: 500;")
        file_label.setWordWrap(True)
        info_layout.addWidget(file_label, 0, 1)

        # Time range
        start_time = self.audio_info.get('start_time', 0)
        end_time = self.audio_info.get('end_time', 0)
        duration = end_time - start_time if end_time > start_time else self.audio_info.get('duration', 0)

        info_layout.addWidget(QLabel("Time:"), 1, 0)
        time_label = QLabel(f"{self._format_time(start_time)} - {self._format_time(end_time)} ({duration:.2f}s)")
        time_label.setStyleSheet("font-family: monospace;")
        info_layout.addWidget(time_label, 1, 1)

        # Channel & Sample rate
        info_layout.addWidget(QLabel("Channel:"), 2, 0)
        channel_label = QLabel(self.audio_info.get('channel', 'Unknown'))
        info_layout.addWidget(channel_label, 2, 1)

        info_layout.addWidget(QLabel("Sample Rate:"), 3, 0)
        sr_label = QLabel(f"{self.audio_info.get('sample_rate', 0)} Hz")
        info_layout.addWidget(sr_label, 3, 1)

        # Frequency range (if available)
        freq_min = self.audio_info.get('freq_min')
        freq_max = self.audio_info.get('freq_max')
        if freq_min is not None and freq_max is not None:
            info_layout.addWidget(QLabel("Frequency:"), 4, 0)
            freq_label = QLabel(f"{freq_min:.0f} - {freq_max:.0f} Hz")
            freq_label.setStyleSheet("font-family: monospace;")
            info_layout.addWidget(freq_label, 4, 1)

        layout.addWidget(info_group)

        # Event Type Section
        event_group = QGroupBox("Event Classification")
        event_layout = QVBoxLayout(event_group)
        event_layout.setSpacing(10)

        # Event type dropdown
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Event Type:"))
        self.event_combo = QComboBox()
        self.event_combo.setMinimumWidth(280)
        for label, code in AnnotationManager.get_event_types():
            self.event_combo.addItem(label, code)
        type_row.addWidget(self.event_combo)
        type_row.addStretch()
        event_layout.addLayout(type_row)

        # Quality slider
        quality_row = QHBoxLayout()
        quality_row.addWidget(QLabel("Quality:"))
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setMinimum(1)
        self.quality_slider.setMaximum(10)
        self.quality_slider.setValue(5)
        self.quality_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.quality_slider.setTickInterval(1)
        self.quality_slider.valueChanged.connect(self._update_quality_label)
        quality_row.addWidget(self.quality_slider)
        self.quality_label = QLabel("5/10")
        self.quality_label.setFixedWidth(40)
        self.quality_label.setStyleSheet("font-weight: bold; color: #3498DB;")
        quality_row.addWidget(self.quality_label)
        event_layout.addLayout(quality_row)

        layout.addWidget(event_group)

        # Notes Section
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Add optional notes about this annotation...")
        self.notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_edit)
        layout.addWidget(notes_group)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #ECF0F1;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                color: #2C3E50;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #E0E0E0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        btn_layout.addStretch()

        save_btn = QPushButton("Save Annotation")
        save_btn.setFixedSize(140, 36)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #3498DB;
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #2980B9;
            }
        """)
        save_btn.clicked.connect(self._save_annotation)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _format_time(self, seconds):
        """Format seconds as HH:MM:SS.ms"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"
        return f"{minutes:02d}:{secs:05.2f}"

    def _update_quality_label(self, value):
        """Update quality label when slider changes"""
        self.quality_label.setText(f"{value}/10")
        # Color coding
        if value <= 3:
            color = "#E74C3C"  # Red
        elif value <= 6:
            color = "#F39C12"  # Orange
        else:
            color = "#27AE60"  # Green
        self.quality_label.setStyleSheet(f"font-weight: bold; color: {color};")

    def _save_annotation(self):
        """Save the annotation to CSV"""
        event_code = self.event_combo.currentData()
        event_label = self.event_combo.currentText()

        annotation_data = {
            'file_path': self.audio_info.get('file_path', ''),
            'file_name': self.audio_info.get('file_name', ''),
            'start_time': self.audio_info.get('start_time', 0),
            'end_time': self.audio_info.get('end_time', 0),
            'duration': self.audio_info.get('end_time', 0) - self.audio_info.get('start_time', 0),
            'channel': self.audio_info.get('channel', ''),
            'sample_rate': self.audio_info.get('sample_rate', 0),
            'freq_min': self.audio_info.get('freq_min', ''),
            'freq_max': self.audio_info.get('freq_max', ''),
            'event_type': event_label,
            'event_code': event_code,
            'quality': self.quality_slider.value(),
            'notes': self.notes_edit.toPlainText().strip(),
            'source_type': self.audio_info.get('source_type', 'local')
        }

        # Save to CSV
        annotation_id = self.annotation_manager.add_annotation(annotation_data)
        annotation_data['id'] = annotation_id

        self.annotation_saved.emit(annotation_data)
        self.accept()

    def get_annotation_data(self):
        """Return the annotation data (after save)"""
        return {
            'event_type': self.event_combo.currentText(),
            'event_code': self.event_combo.currentData(),
            'quality': self.quality_slider.value(),
            'notes': self.notes_edit.toPlainText().strip()
        }
