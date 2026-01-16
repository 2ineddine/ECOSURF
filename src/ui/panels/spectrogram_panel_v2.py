"""
Spectrogram Panel V2 - Professional blue styling
Clean and minimal spectrogram configuration
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, 
    QGroupBox, QProgressBar, QHBoxLayout, QButtonGroup, QRadioButton, QSpinBox
)
from PyQt6.QtCore import pyqtSignal, Qt

from ui.workers.audio_processor_w import AudioProcessor
import os

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
    QRadioButton {
        font-size: 12px;
        color: #2C3E50;
        spacing: 6px;
    }
    QRadioButton::indicator {
        width: 14px;
        height: 14px;
    }
    QRadioButton::indicator:checked {
        background-color: #3498DB;
        border: 3px solid white;
        border-radius: 7px;
        outline: 2px solid #3498DB;
    }
    QRadioButton::indicator:unchecked {
        background-color: white;
        border: 2px solid #BDC3C7;
        border-radius: 7px;
    }
    QComboBox {
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        padding: 6px 10px;
        background-color: white;
        font-size: 12px;
        color: #2C3E50;
    }
    QComboBox:hover {
        border-color: #3498DB;
    }
    QComboBox::drop-down {
        border: none;
        width: 20px;
    }
    QProgressBar {
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        background-color: #ECEFF1;
        height: 8px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #3498DB;
        border-radius: 3px;
    }
    QSpinBox {
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        padding: 4px 8px;
        background-color: white;
        font-size: 12px;
    }
    QSpinBox:hover {
        border-color: #3498DB;
    }
"""


class SpectrogramPanel(QWidget):
    """Panel de configuration du spectrogramme - Style professionnel bleu"""
    spectrogram_computed = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.current_time_range = None
        self.processor = None
        self.recording_type = "canopé"
        self.source_type = "local"
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(PANEL_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("Spectrogram")
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
        
        # Recording Type
        type_group = QGroupBox("Recording Type")
        type_layout = QHBoxLayout()
        type_layout.setSpacing(20)
        
        self.canope_radio = QRadioButton("Canopy")
        self.ground_radio = QRadioButton("Ground")
        self.canope_radio.setChecked(True)
        
        self.type_group_btn = QButtonGroup(self)
        self.type_group_btn.addButton(self.canope_radio, 1)
        self.type_group_btn.addButton(self.ground_radio, 0)
        self.type_group_btn.buttonClicked.connect(self.on_recording_type_changed)
        
        type_layout.addWidget(self.canope_radio)
        type_layout.addWidget(self.ground_radio)
        type_layout.addStretch()
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # FFT Settings
        fft_group = QGroupBox("FFT Settings")
        fft_layout = QVBoxLayout()
        fft_layout.setSpacing(10)
        
        # Window Size
        win_row = QHBoxLayout()
        win_label = QLabel("Window:")
        win_label.setStyleSheet("font-size: 12px; color: #2C3E50;")
        self.window_combo = QComboBox()
        self.window_combo.addItems(["256", "512", "1024", "2048", "4096"])
        self.window_combo.setCurrentText("1024")
        self.window_combo.setFixedWidth(100)
        win_row.addWidget(win_label)
        win_row.addWidget(self.window_combo)
        win_row.addStretch()
        fft_layout.addLayout(win_row)
        
        # Hop Size
        hop_row = QHBoxLayout()
        hop_label = QLabel("Hop:")
        hop_label.setStyleSheet("font-size: 12px; color: #2C3E50;")
        self.hop_combo = QComboBox()
        self.hop_combo.addItems(["128", "256", "512", "1024"])
        self.hop_combo.setCurrentText("256")
        self.hop_combo.setFixedWidth(100)
        hop_row.addWidget(hop_label)
        hop_row.addWidget(self.hop_combo)
        hop_row.addStretch()
        fft_layout.addLayout(hop_row)
        
        # Colormap
        cmap_row = QHBoxLayout()
        cmap_label = QLabel("Colormap:")
        cmap_label.setStyleSheet("font-size: 12px; color: #2C3E50;")
        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems(["viridis", "plasma", "magma", "inferno", "jet", "gray"])
        self.colormap_combo.setCurrentText("viridis")
        self.colormap_combo.setFixedWidth(100)
        cmap_row.addWidget(cmap_label)
        cmap_row.addWidget(self.colormap_combo)
        cmap_row.addStretch()
        fft_layout.addLayout(cmap_row)
        
        fft_group.setLayout(fft_layout)
        layout.addWidget(fft_group)
        
        # Compute Button
        self.compute_btn = QPushButton("Compute Spectrogram")
        self.compute_btn.setEnabled(False)
        self.compute_btn.setMinimumHeight(38)
        self.compute_btn.clicked.connect(self.compute_spectrogram)
        layout.addWidget(self.compute_btn)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setTextVisible(False)
        self.progress.setMaximumHeight(6)
        layout.addWidget(self.progress)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 11px; color: #7F8C8D;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
    def on_recording_type_changed(self, button):
        """Handle recording type selection"""
        if button == self.canope_radio:
            self.recording_type = "canopé"
        else:
            self.recording_type = "ground"
            
    def set_source_type(self, source_type):
        """Set source type (local or s3)"""
        self.source_type = source_type
        
    def set_current_file(self, file_path, time_range=None):
        """Set current file to process"""
        self.current_file = file_path
        self.current_time_range = time_range
        self.compute_btn.setEnabled(file_path is not None)
        
        if file_path:
            name = os.path.basename(file_path) if isinstance(file_path, str) else "Audio loaded"
            self.status_label.setText(f"{name[:30]}...")
        else:
            self.status_label.setText("")
            
    def compute_spectrogram(self):
        """Launch spectrogram computation"""
        if not self.current_file:
            return
            
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.compute_btn.setEnabled(False)
        self.status_label.setText("Computing...")
        
        # Get settings
        n_fft = int(self.window_combo.currentText())
        hop_length = int(self.hop_combo.currentText())
        
        # Create processor
        self.processor = AudioProcessor(
            file_path=self.current_file,
            source_type=self.source_type,
            recording_type=self.recording_type,
            time_range=self.current_time_range
        )
        self.processor.n_fft = n_fft
        self.processor.hop_length = hop_length
        self.processor.colormap = self.colormap_combo.currentText()
        
        self.processor.progress.connect(self.on_progress)
        self.processor.finished.connect(self.on_finished)
        self.processor.error.connect(self.on_error)
        self.processor.start()
        
    def on_progress(self, value):
        self.progress.setValue(value)
        
    def on_finished(self, result):
        self.progress.setVisible(False)
        self.compute_btn.setEnabled(True)
        self.status_label.setText("Ready")
        self.spectrogram_computed.emit(result)
        
    def on_error(self, error_msg):
        self.progress.setVisible(False)
        self.compute_btn.setEnabled(True)
        self.status_label.setText("Error")
        self.status_label.setStyleSheet("font-size: 11px; color: #E74C3C;")
