from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, 
    QGroupBox, QProgressBar, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QFrame

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
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        
        # Ubuntu-style title
        title = QLabel("Spectrogram Configuration")
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
        
        # FFT Parameters group
        settings_group = QGroupBox("FFT Parameters")
        settings_group.setStyleSheet("""
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
        settings_layout = QVBoxLayout()
        settings_layout.setContentsMargins(12, 15, 12, 12)
        settings_layout.setSpacing(8)
        
        fft_label = QLabel("FFT Size:")
        fft_label.setStyleSheet("font-size: 12px; color: #333333; font-weight: bold;")
        settings_layout.addWidget(fft_label)
        
        self.fft_combo = QComboBox()
        self.fft_combo.addItems(["512", "1024", "2048", "4096", "8192"])
        self.fft_combo.setCurrentText("2048")
        self.fft_combo.setStyleSheet("""
            QComboBox {
                font-size: 12px;
                padding: 6px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                background-color: white;
                min-height: 28px;
            }
            QComboBox:hover {
                border: 1px solid #888888;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #CCCCCC;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #333333;
            }
        """)
        settings_layout.addWidget(self.fft_combo)
        
        hop_label = QLabel("Hop Length:")
        hop_label.setStyleSheet("font-size: 12px; color: #333333; font-weight: bold; margin-top: 8px;")
        settings_layout.addWidget(hop_label)
        
        self.hop_combo = QComboBox()
        self.hop_combo.addItems(["128", "256", "512", "1024", "2048"])
        self.hop_combo.setCurrentText("512")
        self.hop_combo.setStyleSheet("""
            QComboBox {
                font-size: 12px;
                padding: 6px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                background-color: white;
                min-height: 28px;
            }
            QComboBox:hover {
                border: 1px solid #888888;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #CCCCCC;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #333333;
            }
        """)
        settings_layout.addWidget(self.hop_combo)
        
        info_label = QLabel("Higher FFT = better frequency resolution")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                margin-top: 12px;
                padding: 8px;
                background-color: white;
                border: 1px solid #DEDEDE;
                border-radius: 3px;
                font-size: 11px;
                color: #5E5E5E;
                line-height: 1.4;
            }
        """)
        settings_layout.addWidget(info_label)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Computation group
        compute_group = QGroupBox("Computation")
        compute_group.setStyleSheet("""
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
        compute_layout = QVBoxLayout()
        compute_layout.setContentsMargins(12, 15, 12, 12)
        compute_layout.setSpacing(8)
        
        self.compute_btn = QPushButton("Compute Spectrogram")
        self.compute_btn.setEnabled(False)
        self.compute_btn.setMinimumHeight(36)
        self.compute_btn.clicked.connect(self.compute_spectrogram)
        self.compute_btn.setStyleSheet("""
            QPushButton {
                background-color: #E95420;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:enabled:hover {
                background-color: #D34615;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #888888;
            }
        """)
        compute_layout.addWidget(self.compute_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(20)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #DEDEDE;
                border-radius: 3px;
                background-color: white;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #E95420;
                border-radius: 2px;
            }
        """)
        compute_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Load file first")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: white;
                border: 1px solid #DEDEDE;
                border-radius: 3px;
                font-size: 11px;
                color: #333333;
                line-height: 1.4;
            }
        """)
        self.status_label.setWordWrap(True)
        compute_layout.addWidget(self.status_label)
        
        compute_group.setLayout(compute_layout)
        layout.addWidget(compute_group)
        
        # Info group
        results_group = QGroupBox("Information")
        results_group.setStyleSheet("""
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
        results_layout = QVBoxLayout()
        results_layout.setContentsMargins(12, 15, 12, 12)
        
        self.results_label = QLabel("No data")
        self.results_label.setWordWrap(True)
        self.results_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: white;
                border: 1px solid #DEDEDE;
                border-radius: 3px;
                font-size: 11px;
                color: #333333;
                line-height: 1.4;
            }
        """)
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
            self.status_label.setText("No file selected")
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
                    f"Success ({file_count} files)<br>"
                    f"<b>Total Duration:</b> {time_duration:.2f}s<br>"
                    f"<b>Max Freq:</b> {max_freq:.0f} Hz<br>"
                    f"<b>Time Frames:</b> {len(result['times'])}<br>"
                    f"<b>Freq Bins:</b> {len(result['frequencies'])}<br>"
                    f"<b>Avg per file:</b> {time_duration/file_count:.1f}s"
                )
                self.status_label.setText(f"{file_count} files concatenated!")
            else:
                self.results_label.setText(
                    f"Success<br>"
                    f"<b>Duration:</b> {time_duration:.2f}s<br>"
                    f"<b>Max Freq:</b> {max_freq:.0f} Hz<br>"
                    f"<b>Time Frames:</b> {len(result['times'])}<br>"
                    f"<b>Freq Bins:</b> {len(result['frequencies'])}"
                )
                self.status_label.setText("Done!")
            
            self.spectrogram_computed.emit(result)
        else:
            self.results_label.setText("Error")
            self.status_label.setText("Failed")
            
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
            self.status_label.setText(f"Using cached file")
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
            self.status_label.setText("No credentials found")
            return None
        
        # Download from S3
        try:
            self.status_label.setText(f"Downloading from S3...")
            
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
            
            self.status_label.setText(f"Downloaded successfully")
            return local_path
            
        except (BotoCoreError, ClientError) as e:
            self.status_label.setText(f"S3 error: {str(e)[:50]}")
            return None
        except Exception as e:
            self.status_label.setText(f"Download error: {str(e)[:50]}")
            return None