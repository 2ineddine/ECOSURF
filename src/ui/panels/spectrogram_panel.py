from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, 
    QGroupBox, QProgressBar, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt

from ui.workers.audio_processor_w import AudioProcessor
import os
from ui.workers.multifile_processor import MultiFileAudioProcessor

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
        
    def set_file(self, file_path, time_range, source_type='local'):
        """Set file with source type (database or local)"""
        self.current_file = file_path
        self.current_time_range = time_range
        self.source_type = source_type  # Store source type
        self.compute_btn.setEnabled(True)
        
        if source_type == 'database':
            self.status_label.setText("Ready to compute (Database file)")
        else:
            self.status_label.setText("Ready to compute (Local file)")
        
    def compute_spectrogram(self):
        if not self.current_file:
            self.status_label.setText("⚠️ No file")
            return
            
        n_fft = int(self.fft_combo.currentText())
        hop_length = int(self.hop_combo.currentText())
        
        # Check if it's a list (multiple files)
        if isinstance(self.current_file, list):
            self.compute_multiple_files(n_fft, hop_length)
        else:
            self.compute_single_file(n_fft, hop_length)

    def compute_multiple_files(self, n_fft, hop_length):
        """Multiple file computation - NO DOWNLOAD"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.compute_btn.setEnabled(False)
        self.status_label.setText(f"Computing {len(self.current_file)} files...")
        
        self.processor = MultiFileAudioProcessor(
            self.current_file, n_fft, hop_length, self.current_time_range
        )
        self.processor.progress.connect(self.on_progress)
        self.processor.finished.connect(self.on_finished)
        self.processor.start()

    def compute_single_file(self, n_fft, hop_length):
        """Single file computation - NO DOWNLOAD"""
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
            
            # Check if this is multi-file result
            file_count = result.get('file_count', 1)
            
            if file_count > 1:
                self.results_label.setText(
                    f"✅ Success ({file_count} files)<br>"
                    f"<b>Total Duration:</b> {time_duration:.2f}s<br>"
                    f"<b>Max Freq:</b> {max_freq:.0f} Hz<br>"
                    f"<b>Time Frames:</b> {len(result['times'])}<br>"
                    f"<b>Freq Bins:</b> {len(result['frequencies'])}<br>"
                    f"<b>Avg per file:</b> {time_duration/file_count:.1f}s"
                )
                self.status_label.setText(f"✅ {file_count} files concatenated!")
            else:
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
    def download_s3_file(self, s3_uri):
        """Download file from S3 to local cache"""
        import boto3
        import json
        from botocore.exceptions import BotoCoreError, ClientError
        
        # Extract S3 path
        s3_path = s3_uri.replace('s3://ecosurf-dataset/', '')
        filename = os.path.basename(s3_path)
        
        # Check if already downloaded
        cache_dir = os.path.join('downloads', 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        local_path = os.path.join(cache_dir, filename)
        
        if os.path.exists(local_path):
            self.status_label.setText(f"✅ Using cached file")
            return local_path
        
        # Load credentials
        cred_paths = [
            os.path.join(os.getcwd(), 'credentials.json'),
            os.path.join(os.path.expanduser('~'), '.config', 'ecosurf', 'credentials.json')
        ]
        
        creds = None
        for cp in cred_paths:
            if os.path.exists(cp):
                try:
                    with open(cp, 'r') as f:
                        creds = json.load(f)
                    break
                except:
                    pass
        
        if not creds:
            self.status_label.setText("❌ No credentials found")
            return None
        
        # Download from S3
        try:
            self.status_label.setText(f"⬇️ Downloading from S3...")
            
            session = boto3.session.Session()
            s3 = session.client(
                's3',
                region_name=creds.get('region'),
                aws_access_key_id=creds.get('ACCESS_KEY'),
                aws_secret_access_key=creds.get('SECRET_KEY'),
                endpoint_url=creds.get('endpoint')
            )
            
            bucket = creds.get('bucket', 'ecosurf-dataset')
            s3.download_file(bucket, s3_path, local_path)
            
            self.status_label.setText(f"✅ Downloaded successfully")
            return local_path
            
        except (BotoCoreError, ClientError) as e:
            self.status_label.setText(f"❌ S3 error: {str(e)[:50]}")
            return None
        except Exception as e:
            self.status_label.setText(f"❌ Download error: {str(e)[:50]}")
            return None