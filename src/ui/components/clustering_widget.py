"""
Clustering Widget - Embeddable 2D cluster visualization
"""
import os
import pickle
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QSpinBox, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

try:
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except:
    AUDIO_AVAILABLE = False


class AudioLoaderThread(QThread):
    finished = pyqtSignal(object, int)
    error = pyqtSignal(str)
    
    def __init__(self, file_path, start_time, end_time):
        super().__init__()
        self.file_path = file_path
        self.start_time = start_time
        self.end_time = end_time
        
    def run(self):
        try:
            import boto3
            import librosa
            import json
            import io
            
            creds_path = 'credentials.json'
            if not os.path.exists(creds_path):
                creds_path = os.path.join(os.path.dirname(__file__), '..', '..', 'credentials.json')
            
            with open(creds_path, 'r') as f:
                creds = json.load(f)
            
            s3 = boto3.client(
                's3',
                endpoint_url=creds['endpoint'],
                aws_access_key_id=creds['ACCESS_KEY'],
                aws_secret_access_key=creds['SECRET_KEY']
            )
            
            file_name = self.file_path
            site = file_name.split('_')[0]
            s3_key = f"2019/{site}/Data/{file_name}"
            
            buffer = io.BytesIO()
            s3.download_fileobj(creds['bucket'], s3_key, buffer)
            buffer.seek(0)
            
            audio, sr = librosa.load(buffer, sr=None, offset=self.start_time, 
                                     duration=self.end_time - self.start_time)
            self.finished.emit(audio, sr)
            
        except Exception as e:
            self.error.emit(str(e))


class ClusteringWidget(QWidget):
    """Embeddable widget for 2D cluster visualization"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.embeddings_2d = None
        self.labels = None
        self.metadata = None
        self.n_clusters = 0
        self.displayed_indices = None
        self.scatter = None
        self.ax = None
        self.audio_thread = None
        self.is_playing = False
        
        self.pan_start = None
        self.current_xlim = None
        self.current_ylim = None
        
        self.init_ui()
        QTimer.singleShot(100, self.load_data)
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        toolbar = QFrame()
        toolbar.setStyleSheet("background: white; border: 1px solid #E0E0E0; border-radius: 4px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(12)
        
        toolbar_layout.addWidget(QLabel("Clusters:"))
        
        self.min_spin = QSpinBox()
        self.min_spin.setRange(1, 500)
        self.min_spin.setValue(1)
        self.min_spin.setPrefix("From ")
        self.min_spin.valueChanged.connect(self.schedule_update)
        toolbar_layout.addWidget(self.min_spin)
        
        self.max_spin = QSpinBox()
        self.max_spin.setRange(1, 500)
        self.max_spin.setValue(50)
        self.max_spin.setPrefix("To ")
        self.max_spin.valueChanged.connect(self.schedule_update)
        toolbar_layout.addWidget(self.max_spin)
        
        toolbar_layout.addWidget(QLabel("|"))
        
        self.reset_btn = QPushButton("Reset View")
        self.reset_btn.clicked.connect(self.reset_view)
        toolbar_layout.addWidget(self.reset_btn)
        
        toolbar_layout.addStretch()
        
        self.status_label = QLabel("Loading...")
        self.status_label.setStyleSheet("color: #7F8C8D;")
        toolbar_layout.addWidget(self.status_label)
        
        layout.addWidget(toolbar)
        
        self.figure = Figure(figsize=(10, 8), dpi=100, facecolor='#F5F6F7')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background: #F5F6F7;")
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#FFFFFF')
        
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('pick_event', self.on_pick)
        
        layout.addWidget(self.canvas, stretch=1)
        
        info_frame = QFrame()
        info_frame.setStyleSheet("background: white; border: 1px solid #E0E0E0; border-radius: 4px;")
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 8, 12, 8)
        
        self.info_label = QLabel("Click a point to see details")
        self.info_label.setStyleSheet("color: #2C3E50;")
        info_layout.addWidget(self.info_label)
        
        info_layout.addStretch()
        
        self.play_btn = QPushButton("Play")
        self.play_btn.setEnabled(False)
        self.play_btn.setStyleSheet("background: #27AE60; color: white; border: none; padding: 6px 16px; border-radius: 4px;")
        self.play_btn.clicked.connect(self.play_audio)
        info_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("background: #E74C3C; color: white; border: none; padding: 6px 16px; border-radius: 4px;")
        self.stop_btn.clicked.connect(self.stop_audio)
        info_layout.addWidget(self.stop_btn)
        
        layout.addWidget(info_frame)
        
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_plot)
    
    def load_data(self):
        self.status_label.setText("Loading data...")

        base_paths = ['perch2/', '../perch2/', '../../perch2/']

        for base in base_paths:
            # Try .npy format first (new format)
            coords_npy = os.path.join(base, 'embeddings_2d_ALL.npy')
            labels_npy = os.path.join(base, 'labels_v2.npy')
            meta_pkl = os.path.join(base, 'perch_info_FINAL.pkl')

            if os.path.exists(coords_npy) and os.path.exists(labels_npy):
                try:
                    self.embeddings_2d = np.load(coords_npy)
                    self.labels = np.load(labels_npy).astype(int)

                    if os.path.exists(meta_pkl):
                        with open(meta_pkl, 'rb') as f:
                            self.metadata = pickle.load(f)
                    else:
                        self.metadata = None

                    self.n_clusters = len(np.unique(self.labels))
                    self.max_spin.setMaximum(self.n_clusters)
                    self.max_spin.setValue(min(50, self.n_clusters))

                    self.status_label.setText(f"{len(self.embeddings_2d):,} points | {self.n_clusters} clusters")
                    self.update_plot()
                    return
                except Exception as e:
                    self.status_label.setText(f"Error: {e}")
                    print(f"Clustering load error: {e}")
                    return

        self.status_label.setText("Data not found in perch2/")
    
    def schedule_update(self):
        self.update_timer.start(300)
    
    def update_plot(self):
        if self.embeddings_2d is None:
            return
        
        self.ax.clear()
        
        min_rank = self.min_spin.value()
        max_rank = self.max_spin.value()
        
        cluster_sizes = {}
        for lbl in self.labels:
            cluster_sizes[lbl] = cluster_sizes.get(lbl, 0) + 1
        
        sorted_clusters = sorted(cluster_sizes.keys(), key=lambda x: cluster_sizes[x], reverse=True)
        selected = sorted_clusters[min_rank-1:max_rank]
        
        mask = np.isin(self.labels, selected)
        self.displayed_indices = np.where(mask)[0]
        
        if len(self.displayed_indices) == 0:
            self.ax.text(0.5, 0.5, "No data in range", ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw_idle()
            return
        
        x = self.embeddings_2d[self.displayed_indices, 0]
        y = self.embeddings_2d[self.displayed_indices, 1]
        colors = self.labels[self.displayed_indices]
        
        self.scatter = self.ax.scatter(
            x, y, c=colors, cmap='tab20', s=8, alpha=0.6, picker=True, pickradius=5
        )
        
        self.ax.set_xlabel("UMAP 1", fontsize=10)
        self.ax.set_ylabel("UMAP 2", fontsize=10)
        self.ax.grid(True, alpha=0.3)
        
        self.current_xlim = self.ax.get_xlim()
        self.current_ylim = self.ax.get_ylim()
        
        self.figure.tight_layout()
        self.canvas.draw_idle()
        
        self.status_label.setText(f"{len(self.displayed_indices):,} points | Clusters {min_rank}-{max_rank}")
    
    def on_scroll(self, event):
        if event.inaxes != self.ax:
            return
        
        scale = 1.2 if event.button == 'down' else 1/1.2
        
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        xdata, ydata = event.xdata, event.ydata
        
        new_xlim = [xdata - (xdata - xlim[0]) * scale, xdata + (xlim[1] - xdata) * scale]
        new_ylim = [ydata - (ydata - ylim[0]) * scale, ydata + (ylim[1] - ydata) * scale]
        
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.canvas.draw_idle()
    
    def on_mouse_press(self, event):
        if event.button == 3 and event.inaxes == self.ax:
            self.pan_start = (event.xdata, event.ydata)
            self.current_xlim = self.ax.get_xlim()
            self.current_ylim = self.ax.get_ylim()
    
    def on_mouse_release(self, event):
        self.pan_start = None
    
    def on_mouse_move(self, event):
        if self.pan_start and event.inaxes == self.ax and event.xdata and event.ydata:
            dx = self.pan_start[0] - event.xdata
            dy = self.pan_start[1] - event.ydata
            
            self.ax.set_xlim(self.current_xlim[0] + dx, self.current_xlim[1] + dx)
            self.ax.set_ylim(self.current_ylim[0] + dy, self.current_ylim[1] + dy)
            self.canvas.draw_idle()
    
    def reset_view(self):
        self.update_plot()
    
    def on_pick(self, event):
        if not hasattr(event, 'ind') or len(event.ind) == 0:
            return
        
        local_idx = event.ind[0]
        global_idx = self.displayed_indices[local_idx]
        
        if self.metadata and global_idx < len(self.metadata):
            meta = self.metadata[global_idx]
            cluster = self.labels[global_idx]
            self.info_label.setText(f"Cluster {cluster} | {meta.get('file', 'N/A')} | {meta.get('start', 0):.0f}-{meta.get('end', 0):.0f}s")
            self.selected_meta = meta
            self.play_btn.setEnabled(True)
    
    def play_audio(self):
        if not self.selected_meta or not AUDIO_AVAILABLE:
            return
        
        self.play_btn.setEnabled(False)
        self.info_label.setText("Downloading audio...")
        
        self.audio_thread = AudioLoaderThread(
            self.selected_meta['file'],
            self.selected_meta['start'],
            self.selected_meta['end']
        )
        self.audio_thread.finished.connect(self.on_audio_loaded)
        self.audio_thread.error.connect(lambda e: self.info_label.setText(f"Error: {e}"))
        self.audio_thread.start()
    
    def on_audio_loaded(self, audio, sr):
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.info_label.setText(f"Playing {len(audio)/sr:.1f}s...")
        self.is_playing = True
        
        try:
            sd.stop()
            sd.play(audio, sr)
        except Exception as e:
            self.info_label.setText(f"Playback error: {e}")
    
    def stop_audio(self):
        if AUDIO_AVAILABLE:
            sd.stop()
        self.is_playing = False
        self.stop_btn.setEnabled(False)
        self.info_label.setText("Stopped")
