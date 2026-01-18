"""
Embedding Panel V2 - Compact professional design
Search controls only - results displayed in main panel
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QListWidget, QListWidgetItem, QProgressBar
)
from PyQt6.QtCore import pyqtSignal, Qt, QThread
import numpy as np
import os

try:
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


PANEL_STYLE = """
QWidget {
    font-family: 'Segoe UI', sans-serif;
    font-size: 12px;
    color: #2C3E50;
    background: white;
}

QLabel#header {
    font-size: 13px;
    font-weight: 600;
    color: #2C3E50;
    padding: 8px 0;
    border-bottom: 2px solid #3498DB;
    margin-bottom: 8px;
}

QFrame#card {
    background: #FAFBFC;
    border: 1px solid #E8E8E8;
    border-radius: 8px;
    padding: 12px;
}

QPushButton#primary_btn {
    background: #3498DB;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 12px;
    font-weight: 600;
    min-height: 38px;
}

QPushButton#primary_btn:hover {
    background: #2980B9;
}

QPushButton#primary_btn:disabled {
    background: #BDC3C7;
}

QPushButton#secondary_btn {
    background: #F8F9FA;
    color: #2C3E50;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 11px;
    font-weight: 500;
}

QPushButton#secondary_btn:hover {
    background: #EBF5FB;
    border-color: #3498DB;
}

QLabel#status {
    font-size: 11px;
    color: #7F8C8D;
    padding: 4px 0;
}

QLabel#status_success {
    font-size: 11px;
    color: #27AE60;
    padding: 4px 0;
}

QFrame#info_card {
    background: #EBF5FB;
    border: 1px solid #AED6F1;
    border-radius: 6px;
    padding: 10px;
}

QListWidget {
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    background: white;
    font-size: 11px;
}

QListWidget::item {
    padding: 8px;
    border-bottom: 1px solid #F0F0F0;
}

QListWidget::item:selected {
    background: #3498DB;
    color: white;
}

QListWidget::item:hover:!selected {
    background: #EBF5FB;
}
"""


class AudioDownloadThread(QThread):
    """Thread for downloading and playing audio from S3"""
    finished = pyqtSignal(np.ndarray, int)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, file_name, start_time, duration=5.0):
        super().__init__()
        self.file_name = file_name
        self.start_time = start_time
        self.duration = duration

    def run(self):
        try:
            import boto3
            import json
            import io
            import librosa

            self.progress.emit("Loading...")

            creds = None
            for cp in ['credentials.json', os.path.join(os.getcwd(), 'credentials.json')]:
                if os.path.exists(cp):
                    with open(cp, 'r') as f:
                        creds = json.load(f)
                    break

            if not creds:
                self.error.emit("credentials.json not found")
                return

            s3 = boto3.client(
                's3',
                region_name=creds.get('region', 'eu-west-2'),
                aws_access_key_id=creds.get('ACCESS_KEY'),
                aws_secret_access_key=creds.get('SECRET_KEY'),
                endpoint_url=creds.get('endpoint', 'https://s3.eu-west-2.wasabisys.com')
            )

            parts = self.file_name.split('_')
            site = parts[0] if len(parts) >= 2 else ""
            s3_key = f"2019/{site}/Data/{self.file_name}"

            self.progress.emit("Downloading...")
            response = s3.get_object(Bucket='ecosurf-dataset', Key=s3_key)
            audio_data = response['Body'].read()

            audio, sr = librosa.load(io.BytesIO(audio_data), sr=None, offset=self.start_time, duration=self.duration)
            self.finished.emit(audio, sr)

        except Exception as e:
            self.error.emit(str(e))


class EmbeddingPanel(QWidget):
    """Compact embedding search panel"""
    search_requested = pyqtSignal()
    result_selected = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.results_data = []
        self.current_audio = None
        self.current_sr = None
        self.download_thread = None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(PANEL_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("Embedding Search")
        header.setObjectName("header")
        layout.addWidget(header)

        # Load embeddings card
        load_card = QFrame()
        load_card.setObjectName("card")
        load_layout = QVBoxLayout(load_card)
        load_layout.setSpacing(10)
        load_layout.setContentsMargins(10, 10, 10, 10)

        self.load_btn = QPushButton("Load Embeddings")
        self.load_btn.setObjectName("primary_btn")
        load_layout.addWidget(self.load_btn)

        self.status_label = QLabel("Not loaded")
        self.status_label.setObjectName("status")
        load_layout.addWidget(self.status_label)

        layout.addWidget(load_card)

        # Search card
        search_card = QFrame()
        search_card.setObjectName("card")
        search_layout = QVBoxLayout(search_card)
        search_layout.setSpacing(10)
        search_layout.setContentsMargins(10, 10, 10, 10)

        search_hint = QLabel("Select region on spectrogram (max 10s)")
        search_hint.setStyleSheet("font-size: 10px; color: #7F8C8D;")
        search_hint.setWordWrap(True)
        search_layout.addWidget(search_hint)

        self.search_btn = QPushButton("Search Similar")
        self.search_btn.setObjectName("primary_btn")
        self.search_btn.setEnabled(False)
        self.search_btn.clicked.connect(lambda: self.search_requested.emit())
        search_layout.addWidget(self.search_btn)

        # Progress bar for search
        self.search_progress = QProgressBar()
        self.search_progress.setVisible(False)
        self.search_progress.setFixedHeight(8)
        self.search_progress.setTextVisible(False)
        self.search_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background: #E8E8E8;
            }
            QProgressBar::chunk {
                background: #3498DB;
                border-radius: 4px;
            }
        """)
        search_layout.addWidget(self.search_progress)

        self.search_status = QLabel("")
        self.search_status.setStyleSheet("font-size: 10px; color: #7F8C8D;")
        self.search_status.setVisible(False)
        search_layout.addWidget(self.search_status)

        layout.addWidget(search_card)

        # Results summary card
        self.results_card = QFrame()
        self.results_card.setObjectName("info_card")
        self.results_card.setVisible(False)
        results_layout = QVBoxLayout(self.results_card)
        results_layout.setSpacing(6)
        results_layout.setContentsMargins(10, 10, 10, 10)

        self.results_label = QLabel("Results")
        self.results_label.setStyleSheet("font-weight: 600; color: #2471A3;")
        results_layout.addWidget(self.results_label)

        self.results_count = QLabel("0 similar sounds found")
        self.results_count.setStyleSheet("font-size: 11px; color: #2471A3;")
        results_layout.addWidget(self.results_count)

        results_hint = QLabel("Results shown below spectrogram")
        results_hint.setStyleSheet("font-size: 10px; color: #5DADE2;")
        results_layout.addWidget(results_hint)

        layout.addWidget(self.results_card)

        layout.addStretch()

        # Hidden elements for compatibility
        self.play_btn = QPushButton()
        self.play_btn.setVisible(False)
        self.stop_btn = QPushButton()
        self.stop_btn.setVisible(False)
        self.results_list = QListWidget()
        self.results_list.setVisible(False)
        self.audio_status = QLabel("")
        self.audio_status.setVisible(False)

    def on_embeddings_loaded(self, count):
        """Called when embeddings are loaded"""
        self.status_label.setText(f"{count:,} segments loaded")
        self.status_label.setStyleSheet("font-size: 11px; color: #27AE60;")
        self.load_btn.setText("Loaded")
        self.load_btn.setEnabled(False)
        self.search_btn.setEnabled(True)

    def start_search_progress(self):
        """Show and start the search progress bar"""
        self.search_progress.setVisible(True)
        self.search_progress.setValue(0)
        self.search_status.setVisible(True)
        self.search_btn.setEnabled(False)

    def update_search_progress(self, value, text=""):
        """Update the search progress bar"""
        self.search_progress.setValue(value)
        if text:
            self.search_status.setText(text)

    def finish_search_progress(self):
        """Hide the search progress bar"""
        self.search_progress.setVisible(False)
        self.search_status.setVisible(False)
        self.search_btn.setEnabled(True)

    def show_results(self, results):
        """Display search results with date and info"""
        self.results_list.clear()
        self.results_data = results

        for i, r in enumerate(results[:10]):  # Show top 10 in compact list
            meta = r['metadata']
            score = r['similarity'] * 100
            # Extract date from filename (format: SITE_YYYYMMDD_HHMMSS.WAV)
            file_parts = meta.get('file', '').split('_')
            date_str = ""
            if len(file_parts) >= 3:
                try:
                    date_part = file_parts[1]
                    time_part = file_parts[2].split('.')[0] if '.' in file_parts[2] else file_parts[2]
                    date_str = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]} {time_part[:2]}:{time_part[2:4]}"
                except:
                    date_str = ""
            start = meta.get('start', 0)
            end = meta.get('end', 0)
            duration = end - start
            text = f"#{i+1} | {score:.0f}% | {date_str} | {duration:.1f}s"
            item = QListWidgetItem(text)
            item.setToolTip(f"File: {meta.get('file', 'N/A')}\nStart: {start:.1f}s - End: {end:.1f}s")
            self.results_list.addItem(item)

        self.results_card.setVisible(True)
        self.results_count.setText(f"{len(results)} similar sounds found")
        self.play_btn.setEnabled(len(results) > 0)

    def on_result_clicked(self, item):
        """Handle result selection"""
        idx = self.results_list.row(item)
        if idx < len(self.results_data):
            self.result_selected.emit({'index': idx})
            self.play_btn.setEnabled(True)

    def play_selected(self):
        """Play selected result"""
        idx = self.results_list.currentRow()
        if idx < 0 or idx >= len(self.results_data):
            return

        if not AUDIO_AVAILABLE:
            self.audio_status.setText("sounddevice not installed")
            return

        result = self.results_data[idx]
        meta = result['metadata']

        self.audio_status.setText("Downloading...")
        self.play_btn.setEnabled(False)

        self.download_thread = AudioDownloadThread(
            meta['file'], meta['start'], meta['end'] - meta['start']
        )
        self.download_thread.finished.connect(self.on_audio_ready)
        self.download_thread.error.connect(lambda e: self.audio_status.setText(f"Error: {e[:30]}"))
        self.download_thread.start()

    def play_selected_result(self, idx, result):
        """Play a specific result (called from main window)"""
        if not AUDIO_AVAILABLE:
            self.audio_status.setText("sounddevice not installed")
            return

        meta = result['metadata']
        self.audio_status.setText("Downloading...")

        self.download_thread = AudioDownloadThread(
            meta['file'], meta['start'], meta['end'] - meta['start']
        )
        self.download_thread.finished.connect(self.on_audio_ready)
        self.download_thread.error.connect(lambda e: self.audio_status.setText(f"Error: {e[:30]}"))
        self.download_thread.start()

    def on_audio_ready(self, audio, sr):
        """Play downloaded audio"""
        self.current_audio = audio
        self.current_sr = sr
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.audio_status.setText(f"Playing {len(audio)/sr:.1f}s")

        try:
            sd.stop()
            sd.play(audio, sr)
        except Exception as e:
            self.audio_status.setText(f"Error: {str(e)[:30]}")

    def stop_audio(self):
        """Stop audio playback"""
        if AUDIO_AVAILABLE:
            sd.stop()
        self.stop_btn.setEnabled(False)
        self.audio_status.setText("Stopped")


# Alias for compatibility
EmbeddingPanelV2 = EmbeddingPanel
