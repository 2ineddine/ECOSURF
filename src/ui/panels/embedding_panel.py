from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QListWidget, QSlider, QFileDialog, QListWidgetItem, QDialog,
    QProgressBar
)
from PyQt6.QtCore import pyqtSignal, Qt, QThread
import numpy as np
import os
import tempfile

# Audio playback
try:
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("[WARNING] sounddevice not installed. Run: pip install sounddevice")


class AudioDownloadThread(QThread):
    """Thread pour télécharger l'audio depuis S3."""
    finished = pyqtSignal(np.ndarray, int)  # audio, sample_rate
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
            
            self.progress.emit("Chargement credentials...")
            
            # Charger credentials.json (comme le reste de l'app)
            creds = None
            cred_paths = [
                'credentials.json',
                os.path.join(os.getcwd(), 'credentials.json'),
            ]
            for cp in cred_paths:
                if os.path.exists(cp):
                    with open(cp, 'r') as f:
                        creds = json.load(f)
                    break
            
            if not creds:
                self.error.emit("credentials.json non trouvé")
                return
            
            self.progress.emit("Connexion S3...")
            
            s3 = boto3.client(
                's3',
                region_name=creds.get('region', 'eu-west-2'),
                aws_access_key_id=creds.get('ACCESS_KEY'),
                aws_secret_access_key=creds.get('SECRET_KEY'),
                endpoint_url=creds.get('endpoint', 'https://s3.eu-west-2.wasabisys.com')
            )
            
            # Construire le chemin S3 complet
            # Format fichier: S4A09154_20190218_163000.flac
            # Chemin S3: 2019/S4A09154/Data/S4A09154_20190218_163000.flac
            parts = self.file_name.split('_')
            if len(parts) >= 2:
                site = parts[0]  # S4A09154
                s3_key = f"2019/{site}/Data/{self.file_name}"
            else:
                s3_key = f"2019/{self.file_name}"
            
            self.progress.emit(f"Telechargement {self.file_name}...")
            
            # Télécharger le fichier
            response = s3.get_object(Bucket='ecosurf-dataset', Key=s3_key)
            audio_data = response['Body'].read()
            
            self.progress.emit("Décodage audio...")
            
            # Décoder l'audio
            audio, sr = librosa.load(
                io.BytesIO(audio_data),
                sr=None,
                offset=self.start_time,
                duration=self.duration
            )
            
            self.finished.emit(audio, sr)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))


class EmbeddingPanel(QWidget):
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
        # Layout vertical propre et pro
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(10)
        
        # Header: Titre + Controles
        header = QHBoxLayout()
        header.setSpacing(20)
        
        title = QLabel("Embedding Search (2019)")
        title.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #E95420;
            padding: 5px 0;
        """)
        header.addWidget(title)
        
        self.load_btn = QPushButton("Charger Embeddings")
        self.load_btn.setFixedSize(160, 32)
        self.load_btn.clicked.connect(self.on_load_clicked)
        self.load_btn.setStyleSheet("""
            QPushButton { 
                background-color: #f5f5f5; 
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 12px;
                padding: 5px 15px;
            }
            QPushButton:hover { background-color: #e8e8e8; }
        """)
        header.addWidget(self.load_btn)
        
        self.status_label = QLabel("Non charge")
        self.status_label.setStyleSheet("font-size: 12px; color: #666;")
        header.addWidget(self.status_label)
        
        header.addStretch()
        
        self.search_btn = QPushButton("Rechercher Similaires")
        self.search_btn.setFixedSize(180, 36)
        self.search_btn.setEnabled(False)
        self.search_btn.clicked.connect(lambda: self.search_requested.emit())
        self.search_btn.setStyleSheet("""
            QPushButton { 
                background-color: #E95420; 
                color: white; 
                font-weight: bold; 
                font-size: 13px; 
                border: none;
                border-radius: 4px; 
            }
            QPushButton:hover { background-color: #d44810; }
            QPushButton:disabled { background-color: #CCCCCC; }
        """)
        header.addWidget(self.search_btn)
        
        main_layout.addLayout(header)
        
        # Contenu principal: Liste + Audio
        content = QHBoxLayout()
        content.setSpacing(15)
        
        # Liste des resultats (prend tout l'espace)
        results_container = QVBoxLayout()
        results_container.setSpacing(5)
        
        results_header = QLabel("Resultats de recherche:")
        results_header.setStyleSheet("font-size: 11px; color: #888; font-weight: bold;")
        results_container.addWidget(results_header)
        
        self.results_list = QListWidget()
        self.results_list.setMinimumHeight(100)
        self.results_list.itemClicked.connect(self.on_result_selected)
        self.results_list.itemDoubleClicked.connect(self.on_result_play)
        self.results_list.setStyleSheet("""
            QListWidget { 
                font-size: 12px; 
                border: 1px solid #ddd; 
                border-radius: 4px;
                background: white;
            }
            QListWidget::item { 
                padding: 8px 12px; 
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected { 
                background-color: #E95420; 
                color: white; 
            }
            QListWidget::item:hover:!selected {
                background-color: #f5f5f5;
            }
        """)
        results_container.addWidget(self.results_list)
        
        content.addLayout(results_container, stretch=1)
        
        # Panneau audio (droite)
        audio_panel = QVBoxLayout()
        audio_panel.setSpacing(8)
        
        audio_title = QLabel("Lecture Audio")
        audio_title.setStyleSheet("font-size: 11px; color: #888; font-weight: bold;")
        audio_panel.addWidget(audio_title)
        
        self.play_btn = QPushButton("Ecouter")
        self.play_btn.setFixedSize(100, 36)
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.play_selected)
        self.play_btn.setStyleSheet("""
            QPushButton { 
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                font-size: 12px;
                border: none;
                border-radius: 4px; 
            }
            QPushButton:hover { background-color: #43a047; }
            QPushButton:disabled { background-color: #CCCCCC; }
        """)
        audio_panel.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFixedSize(100, 36)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_audio)
        self.stop_btn.setStyleSheet("""
            QPushButton { 
                background-color: #f44336; 
                color: white; 
                font-size: 12px;
                border: none;
                border-radius: 4px; 
            }
            QPushButton:hover { background-color: #e53935; }
            QPushButton:disabled { background-color: #CCCCCC; }
        """)
        audio_panel.addWidget(self.stop_btn)
        
        self.audio_status = QLabel("")
        self.audio_status.setStyleSheet("color: #666; font-size: 11px;")
        self.audio_status.setFixedWidth(100)
        self.audio_status.setWordWrap(True)
        self.audio_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        audio_panel.addWidget(self.audio_status)
        
        audio_panel.addStretch()
        content.addLayout(audio_panel)
        
        main_layout.addLayout(content, stretch=1)
    
    def on_load_clicked(self):
        self.load_btn.setText("Chargement...")
        self.load_btn.setEnabled(False)
    
    def on_embeddings_loaded(self, count):
        self.status_label.setText(f"{count:,} segments charges")
        self.load_btn.setText("Embeddings charges")
        self.search_btn.setEnabled(True)
    
    def enable_search(self, enabled):
        self.search_btn.setEnabled(enabled)
    
    def show_results(self, results):
        self.results_list.clear()
        self.results_data = results
        for i, r in enumerate(results):
            meta = r['metadata']
            score_pct = r['similarity'] * 100
            text = f"#{i+1} | {meta['file'][:20]}... | {meta['start']:.0f}-{meta['end']:.0f}s | {score_pct:.1f}%"
            self.results_list.addItem(text)
        self.play_btn.setEnabled(len(results) > 0)
        self.status_label.setText(f"{len(results)} resultats trouves")
    
    def on_result_selected(self, item):
        idx = self.results_list.row(item)
        if idx < len(self.results_data):
            self.play_btn.setEnabled(True)
    
    def on_result_play(self, item):
        """Double-clic = jouer directement."""
        self.play_selected()
    
    def play_selected(self):
        """Télécharge et joue l'audio du résultat sélectionné."""
        idx = self.results_list.currentRow()
        if idx < 0 or idx >= len(self.results_data):
            return
        
        if not AUDIO_AVAILABLE:
            self.audio_status.setText("sounddevice non installe")
            return
        
        result = self.results_data[idx]
        meta = result['metadata']
        file_name = meta['file']
        start_time = meta['start']
        duration = meta['end'] - meta['start']
        
        self.audio_status.setText(f"Telechargement {file_name}...")
        self.play_btn.setEnabled(False)
        
        # Lancer le téléchargement en thread
        self.download_thread = AudioDownloadThread(file_name, start_time, duration)
        self.download_thread.finished.connect(self.on_audio_downloaded)
        self.download_thread.error.connect(self.on_audio_error)
        self.download_thread.progress.connect(lambda msg: self.audio_status.setText(msg))
        self.download_thread.start()
    
    def on_audio_downloaded(self, audio, sr):
        """Joue l'audio téléchargé."""
        self.current_audio = audio
        self.current_sr = sr
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        
        self.audio_status.setText(f"Lecture... ({len(audio)/sr:.1f}s)")
        
        try:
            sd.stop()
            sd.play(audio, sr)
        except Exception as e:
            self.audio_status.setText(f"Erreur lecture: {e}")
    
    def on_audio_error(self, error):
        self.audio_status.setText(f"Erreur: {error}")
        self.play_btn.setEnabled(True)
    
    def stop_audio(self):
        """Arrête la lecture."""
        if AUDIO_AVAILABLE:
            sd.stop()
        self.stop_btn.setEnabled(False)
        self.audio_status.setText("Arrete")
    
    def on_result_clicked(self, item):
        idx = self.results_list.row(item)
        self.result_selected.emit({'index': idx})