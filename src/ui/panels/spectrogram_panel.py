from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, 
    QGroupBox, QProgressBar, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt

from ui.workers.audio_processor_w import AudioProcessor


class SpectrogramPanel(QWidget):
    spectrogram_computed = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.current_time_range = None
        self.processor = None
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        
        title = QLabel("Spectrogram Config")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(title)
        
        settings_group = QGroupBox("FFT Parameters")
        settings_layout = QVBoxLayout()
        
        fft_label = QLabel("FFT Size:")
        fft_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        settings_layout.addWidget(fft_label)
        
        self.fft_combo = QComboBox()
        self.fft_combo.addItems(["512", "1024", "2048", "4096", "8192"])
        self.fft_combo.setCurrentText("2048")
        settings_layout.addWidget(self.fft_combo)
        
        hop_label = QLabel("Hop Length:")
        hop_label.setStyleSheet("font-weight: bold; margin-top: 8px; font-size: 11px;")
        settings_layout.addWidget(hop_label)
        
        self.hop_combo = QComboBox()
        self.hop_combo.addItems(["128", "256", "512", "1024", "2048"])
        self.hop_combo.setCurrentText("512")
        settings_layout.addWidget(self.hop_combo)
        
        info_label = QLabel("💡 Higher FFT = better freq resolution")
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "margin-top: 8px; padding: 6px; background-color: #e3f2fd; "
            "border-radius: 4px; font-size: 10px;"
        )
        settings_layout.addWidget(info_label)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        compute_group = QGroupBox("Computation")
        compute_layout = QVBoxLayout()
        
        self.compute_btn = QPushButton("⚡ Compute")
        self.compute_btn.setEnabled(False)
        self.compute_btn.setMinimumHeight(40)
        self.compute_btn.clicked.connect(self.compute_spectrogram)
        self.compute_btn.setStyleSheet("""
            QPushButton:enabled {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 13px;
            }
        """)
        compute_layout.addWidget(self.compute_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(20)
        compute_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Load file first")
        self.status_label.setStyleSheet(
            "padding: 6px; background-color: #f9f9f9; "
            "border-radius: 4px; font-size: 10px;"
        )
        self.status_label.setWordWrap(True)
        compute_layout.addWidget(self.status_label)
        
        compute_group.setLayout(compute_layout)
        layout.addWidget(compute_group)
        
        results_group = QGroupBox("Info")
        results_layout = QVBoxLayout()
        
        self.results_label = QLabel("No data")
        self.results_label.setWordWrap(True)
        self.results_label.setStyleSheet(
            "padding: 8px; background-color: #f9f9f9; "
            "border-radius: 5px; font-size: 10px;"
        )
        results_layout.addWidget(self.results_label)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
    def set_file(self, file_path, time_range):
        self.current_file = file_path
        self.current_time_range = time_range
        self.compute_btn.setEnabled(True)
        self.status_label.setText("Ready to compute")
        
    def compute_spectrogram(self):
        if not self.current_file:
            self.status_label.setText("⚠️ No file")
            return
            
        n_fft = int(self.fft_combo.currentText())
        hop_length = int(self.hop_combo.currentText())
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.compute_btn.setEnabled(False)
        self.status_label.setText("Computing...")
        
        self.processor = AudioProcessor(
            self.current_file, n_fft, hop_length, self.current_time_range
        )
        self.processor.progress.connect(self.on_progress)
        self.processor.finished.connect(self.on_finished)
        self.processor.start()
        
    def on_progress(self, value):
        self.progress_bar.setValue(value)
        
    def on_finished(self, result):
        self.progress_bar.setVisible(False)
        self.compute_btn.setEnabled(True)
        
        if result:
            max_freq = result['frequencies'][-1]
            time_duration = result['times'][-1]
            
            self.results_label.setText(
                f"✅ Success<br>"
                f"<b>Duration:</b> {time_duration:.2f}s<br>"
                f"<b>Max Freq:</b> {max_freq:.0f} Hz<br>"
                f"<b>Time Frames:</b> {len(result['times'])}<br>"
                f"<b>Freq Bins:</b> {len(result['frequencies'])}"
            )
            
            self.status_label.setText("✅ Done!")
            self.spectrogram_computed.emit(result)
        else:
            self.results_label.setText("❌ Error")
            self.status_label.setText("❌ Failed")