import os
import threading
from datetime import datetime

import numpy as np
import librosa
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QListWidget, QStackedWidget, QSplitter, QScrollBar, QPushButton,
    QLabel, QListWidgetItem, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from ui.styles import GLOBAL_STYLE, SIDEBAR_STYLE, HEADER_STYLE, INSPECTOR_STYLE
from ui.panels.panels_file import FilePanel
from ui.panels.spectrogram_panel import SpectrogramPanel
from ui.panels.view_panel import ViewPanel
from ui.panels.audio_panel import AudioPanel
from ui.panels.pattern_panel import PatternPanel
from ui.panels.search_panel import SearchPanel
from ui.panels.embedding_panel import EmbeddingPanel
from ui.panels.clustering_panel import ClusteringPanel
from ui.components.spectrogram_widget import SpectrogramWidget
from ui.dialogs.clustering_dialog import ClusteringDialog
from core.embedding_manager import EmbeddingManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ECOSURF - Bioacoustic Analysis")
        self.setGeometry(50, 50, 1600, 900)
        self.setStyleSheet(GLOBAL_STYLE)
        
        self.current_file = None
        self.current_time_range = None
        self.audio_data = None
        self.file_list = []
        self.audio_thread = None
        self.playing = False
        self.playing_selection = False
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback_position)
        self.playback_start_time = 0
        self.search_results = []
        self.embedding_manager = EmbeddingManager()
        self.perch_model = None
        self.perch_model_loading = False
        self.clustering_dialog = None
        
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.header = self.create_header()
        main_layout.addWidget(self.header)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = self.create_sidebar()
        body_layout.addWidget(self.sidebar)

        self.workspace = self.create_workspace()
        body_layout.addWidget(self.workspace, stretch=1)

        self.inspector = self.create_inspector()
        body_layout.addWidget(self.inspector)

        main_layout.addWidget(body, stretch=1)

    def create_header(self):
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(40)
        header.setStyleSheet(HEADER_STYLE)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        logo = QLabel("ECOSURF")
        logo.setObjectName("header_text")
        logo.setStyleSheet("font-weight: bold; font-size: 14px; color: #ECF0F1;")
        layout.addWidget(logo)

        sep1 = QLabel("|")
        sep1.setStyleSheet("color: rgba(255,255,255,0.3);")
        layout.addWidget(sep1)

        self.header_file = QLabel("No file loaded")
        self.header_file.setObjectName("header_file")
        self.header_file.setStyleSheet("color: #BDC3C7; font-size: 11px;")
        layout.addWidget(self.header_file)

        layout.addStretch()

        self.header_status = QLabel("")
        self.header_status.setStyleSheet("color: #27AE60; font-size: 11px;")
        layout.addWidget(self.header_status)

        return header

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet(SIDEBAR_STYLE)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        logo_label = QLabel("ECOSURF")
        logo_label.setObjectName("logo")
        layout.addWidget(logo_label)

        version = QLabel("v1.0 - Bioacoustic")
        version.setObjectName("version")
        layout.addWidget(version)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("nav")

        nav_items = [
            ("Files", 0),
            ("Spectrogram", 1),
            ("View", 2),
            ("Audio", 3),
            ("Selection", 4),
            ("Pattern Search", 5),
            ("Embedding", 6),
            ("2D Clustering", 7),
        ]

        for name, idx in nav_items:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.nav_list.addItem(item)

        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        layout.addWidget(self.nav_list, stretch=1)

        layout.addStretch()

        return sidebar

    def create_workspace(self):
        workspace = QWidget()
        workspace.setStyleSheet("background: #F5F6F7;")
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E0E0E0; background: white; border-radius: 4px; }
            QTabBar::tab { background: #ECF0F1; border: 1px solid #E0E0E0; padding: 8px 20px; margin-right: 2px; }
            QTabBar::tab:selected { background: white; border-bottom: 1px solid white; font-weight: bold; }
            QTabBar::tab:hover:!selected { background: #D5DBDB; }
        """)

        spectro_tab = QWidget()
        spectro_layout = QVBoxLayout(spectro_tab)
        spectro_layout.setContentsMargins(8, 8, 8, 8)
        self.spectrogram_widget = SpectrogramWidget()
        spectro_layout.addWidget(self.spectrogram_widget)

        self.viewport_scroll = QScrollBar(Qt.Orientation.Horizontal)
        self.viewport_scroll.setMinimum(0)
        self.viewport_scroll.setMaximum(100)
        self.viewport_scroll.setValue(0)
        self.viewport_scroll.setEnabled(False)
        self.viewport_scroll.valueChanged.connect(self.on_viewport_scroll)
        self.viewport_scroll.setFixedHeight(14)
        spectro_layout.addWidget(self.viewport_scroll)

        self.tabs.addTab(spectro_tab, "Spectrogram")

        cluster_tab = QWidget()
        cluster_layout = QVBoxLayout(cluster_tab)
        cluster_layout.setContentsMargins(20, 20, 20, 20)

        info_label = QLabel("2D Clustering Visualization")
        info_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2C3E50;")
        cluster_layout.addWidget(info_label)

        desc = QLabel("Explore 650,760 audio segments projected in 2D space using UMAP.\nClick below to open the interactive visualization.")
        desc.setStyleSheet("color: #7F8C8D; font-size: 12px;")
        cluster_layout.addWidget(desc)

        cluster_layout.addSpacing(20)

        open_btn = QPushButton("Open 2D Clustering")
        open_btn.setFixedSize(200, 40)
        open_btn.setProperty("primary", True)
        open_btn.clicked.connect(self.open_clustering_dialog)
        cluster_layout.addWidget(open_btn)

        cluster_layout.addStretch()

        stats_frame = QFrame()
        stats_frame.setStyleSheet("background: white; border: 1px solid #E0E0E0; border-radius: 4px; padding: 12px;")
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.addWidget(QLabel("Dataset Statistics:"))
        stats_layout.addWidget(QLabel("Total segments: 650,760"))
        stats_layout.addWidget(QLabel("Clusters: 488"))
        stats_layout.addWidget(QLabel("Embedding dim: 1536"))
        stats_layout.addWidget(QLabel("Segment duration: 5s"))
        cluster_layout.addWidget(stats_frame)

        cluster_layout.addStretch()

        self.tabs.addTab(cluster_tab, "2D Clustering")

        layout.addWidget(self.tabs, stretch=1)

        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)

        return workspace

    def create_toolbar(self):
        toolbar = QFrame()
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet("background: white; border: 1px solid #E0E0E0; border-radius: 4px;")
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        self.play_btn = QPushButton("Play")
        self.play_btn.setFixedSize(60, 28)
        self.play_btn.setProperty("success", True)
        self.play_btn.clicked.connect(self.play_audio)
        layout.addWidget(self.play_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFixedSize(50, 28)
        self.stop_btn.clicked.connect(self.stop_audio)
        layout.addWidget(self.stop_btn)

        layout.addSpacing(16)

        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet("background: #E0E0E0;")
        layout.addWidget(sep)

        layout.addSpacing(16)

        zoom_in = QPushButton("+")
        zoom_in.setFixedSize(28, 28)
        zoom_in.setToolTip("Zoom In")
        layout.addWidget(zoom_in)

        zoom_out = QPushButton("-")
        zoom_out.setFixedSize(28, 28)
        zoom_out.setToolTip("Zoom Out")
        layout.addWidget(zoom_out)

        zoom_reset = QPushButton("Reset")
        zoom_reset.setFixedSize(50, 28)
        zoom_reset.clicked.connect(self.on_zoom_reset)
        layout.addWidget(zoom_reset)

        layout.addStretch()

        self.toolbar_status = QLabel("")
        self.toolbar_status.setStyleSheet("color: #7F8C8D; font-size: 11px;")
        layout.addWidget(self.toolbar_status)

        return toolbar

    def create_inspector(self):
        inspector = QFrame()
        inspector.setObjectName("inspector")
        inspector.setFixedWidth(280)
        inspector.setStyleSheet(INSPECTOR_STYLE)

        scroll_content = QWidget()
        self.inspector_layout = QVBoxLayout(scroll_content)
        self.inspector_layout.setContentsMargins(12, 12, 12, 12)
        self.inspector_layout.setSpacing(8)

        self.panel_stack = QStackedWidget()

        self.file_panel = FilePanel()
        self.spectrogram_panel = SpectrogramPanel()
        self.view_panel = ViewPanel()
        self.audio_panel = AudioPanel()
        self.pattern_panel = PatternPanel()
        self.search_panel = SearchPanel()
        self.embedding_panel = EmbeddingPanel()
        self.clustering_panel = ClusteringPanel()

        self.panel_stack.addWidget(self.file_panel)
        self.panel_stack.addWidget(self.spectrogram_panel)
        self.panel_stack.addWidget(self.view_panel)
        self.panel_stack.addWidget(self.audio_panel)
        self.panel_stack.addWidget(self.pattern_panel)
        self.panel_stack.addWidget(self.search_panel)
        self.panel_stack.addWidget(self.embedding_panel)
        self.panel_stack.addWidget(self.clustering_panel)

        self.inspector_layout.addWidget(self.panel_stack)
        self.inspector_layout.addStretch()

        main_layout = QVBoxLayout(inspector)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_content)

        return inspector

    def on_nav_changed(self, index):
        if index >= 0:
            self.panel_stack.setCurrentIndex(index)
            if index == 7:
                self.tabs.setCurrentIndex(1)
            else:
                self.tabs.setCurrentIndex(0)

    def open_clustering_dialog(self):
        if self.clustering_dialog is None or not self.clustering_dialog.isVisible():
            self.clustering_dialog = ClusteringDialog(self)
        self.clustering_dialog.show()
        self.clustering_dialog.raise_()

    def connect_signals(self):
        self.file_panel.file_loaded.connect(self.on_file_loaded_with_source)
        self.file_panel.search_scope_changed.connect(self.on_search_scope_changed)
        self.file_panel.period_dict_loaded.connect(self.on_period_dict_loaded)
        self.file_panel.folder_loaded.connect(self.on_folder_loaded)
        
        self.spectrogram_panel.spectrogram_computed.connect(self.on_spectrogram_computed)
        
        self.view_panel.zoom_toggled.connect(self.on_zoom_toggled)
        self.view_panel.zoom_reset_requested.connect(self.on_zoom_reset)
        self.view_panel.cursor_changed.connect(self.spectrogram_widget.setCursor)
        
        self.audio_panel.play_requested.connect(self.play_audio)
        self.audio_panel.pause_requested.connect(self.pause_audio)
        self.audio_panel.stop_requested.connect(self.stop_audio)
        
        self.pattern_panel.brush_toggled.connect(self.on_brush_toggled)
        self.pattern_panel.brush_size_changed.connect(self.on_brush_size_changed)
        self.pattern_panel.rect_mode_toggled.connect(self.on_rect_mode_toggled)
        self.pattern_panel.selection_cleared.connect(self.spectrogram_widget.clear_mask)
        self.pattern_panel.extract_requested.connect(self.extract_selection)
        self.pattern_panel.play_selection_requested.connect(self.play_selection)
        self.pattern_panel.cursor_changed.connect(self.spectrogram_widget.setCursor)
        
        self.search_panel.result_opened.connect(self.open_search_result)
        
        self.embedding_panel.load_btn.clicked.connect(self.load_embeddings)
        self.embedding_panel.search_requested.connect(self.search_embeddings)
        self.embedding_panel.result_selected.connect(self.on_embedding_result_selected)
        
        try:
            self.spectrogram_widget.scrollableChanged.connect(self.viewport_scroll.setEnabled)
        except:
            pass

    def on_period_dict_loaded(self, period_dict):
        if hasattr(self, 'search_panel'):
            self.search_panel.set_period_dict(period_dict)

    def on_file_loaded_with_source(self, file_path, time_range, source_type):
        self.current_file = file_path
        self.current_time_range = time_range
        self.spectrogram_panel.set_file(file_path, time_range, source_type)
        if isinstance(file_path, list):
            self.header_file.setText(f"{len(file_path)} files selected")
        else:
            name = os.path.basename(file_path) if file_path else "No file"
            self.header_file.setText(name[:50])

    def on_folder_loaded(self, file_list):
        self.file_list = file_list
        self.search_panel.set_file_list(file_list)

    def on_spectrogram_computed(self, audio_data):
        self.audio_data = audio_data
        max_freq = audio_data['frequencies'][-1]
        self.header_status.setText(f"Max: {max_freq:.0f} Hz")
        self.spectrogram_widget.set_spectrogram(
            audio_data['spectrogram'], 
            audio_data['frequencies'], 
            audio_data['times'], 
            audio_data['time_offset']
        )
        total_duration = float(audio_data['times'][-1])
        viewport_duration = self.spectrogram_widget.viewport_duration
        self.viewport_scroll.setEnabled(total_duration > viewport_duration)
        self.viewport_scroll.setValue(0)
        self.audio_panel.enable_controls(True)
        self.search_panel.set_audio_data(audio_data)
        self.toolbar_status.setText(f"Duration: {total_duration:.1f}s")

    def on_viewport_scroll(self, value):
        if self.playing:
            return
        self.spectrogram_widget.scroll_viewport(value)

    def on_zoom_toggled(self, enabled):
        self.spectrogram_widget.zoom_enabled = enabled
        if enabled:
            self.pattern_panel.disable_brush()

    def on_zoom_reset(self):
        self.spectrogram_widget.reset_zoom()

    def on_brush_toggled(self, enabled):
        self.spectrogram_widget.brush_enabled = enabled
        if enabled:
            self.view_panel.disable_zoom()

    def on_search_scope_changed(self, scope_type, file_list):
        if hasattr(self, 'search_panel') and hasattr(self.search_panel, 'set_search_scope'):
            self.search_panel.set_search_scope(scope_type, file_list)

    def on_rect_mode_toggled(self, enabled):
        if enabled:
            self.spectrogram_widget.rect_selection_mode = True
            self.spectrogram_widget.brush_enabled = False
            self.view_panel.disable_zoom()
        else:
            self.spectrogram_widget.rect_selection_mode = False

    def on_brush_size_changed(self, size):
        self.spectrogram_widget.brush_size = size

    def extract_selection(self):
        try:
            from core.spectrogram_audio import extract_patch_audio
        except:
            self.pattern_panel.hide_progress()
            return
        if self.audio_data is None:
            self.pattern_panel.hide_progress()
            return
        mask = self.spectrogram_widget.mask
        if mask is None or not mask.any():
            self.pattern_panel.hide_progress()
            self.pattern_panel.selection_status.setText("No selection")
            return
        self.pattern_panel.update_progress(10, "Preparing...")
        QTimer.singleShot(50, self._do_extract_selection)
    
    def _do_extract_selection(self):
        try:
            from core.spectrogram_audio import extract_patch_audio
        except:
            self.pattern_panel.hide_progress()
            return
        self.pattern_panel.update_progress(20, "Computing STFT...")
        n_fft = int(self.spectrogram_panel.fft_combo.currentText())
        hop_length = int(self.spectrogram_panel.hop_combo.currentText())
        audio = self.audio_data.get('audio')
        sr = self.audio_data.get('sample_rate')
        mask = self.spectrogram_widget.mask
        try:
            stft = librosa.stft(audio, n_fft=n_fft, hop_length=hop_length)
        except:
            self.pattern_panel.hide_progress()
            return
        self.pattern_panel.update_progress(60, "Extracting audio...")
        sel_audio, meta = extract_patch_audio(
            stft, mask, sr, 
            hop_length=hop_length, 
            n_fft=n_fft, 
            time_offset=self.audio_data.get('time_offset', 0.0)
        )
        self.pattern_panel.update_progress(90, "Finalizing...")
        if sel_audio is None or len(sel_audio) == 0:
            self.pattern_panel.hide_progress()
            self.pattern_panel.selection_status.setText("Extraction failed")
            return
        self.pattern_panel.set_selection_audio(sel_audio, meta)
        try:
            self.spectrogram_widget.show_selection_audio(sel_audio, sr)
        except:
            pass
        self.pattern_panel.hide_progress()

    def play_audio(self):
        if self.audio_data is None:
            return
        self.stop_audio()
        start_idx, end_idx = self.spectrogram_widget.get_viewport_indices()
        if start_idx is None:
            return
        times = self.audio_data['times']
        sr = self.audio_data['sample_rate']
        audio = self.audio_data['audio']
        start_sample = int(times[start_idx] * sr)
        end_sample = int(times[end_idx] * sr)
        audio_segment = audio[start_sample:end_sample]
        self.playing = True
        self.playing_selection = False
        self.playback_start_time = datetime.now().timestamp()
        self.audio_thread = threading.Thread(target=self._play_audio_thread, args=(audio_segment, sr), daemon=True)
        self.audio_thread.start()
        self.playback_timer.start(50)
        self.audio_panel.set_playing_state()
        self.viewport_scroll.setEnabled(False)
        self.play_btn.setText("Playing...")
        self.play_btn.setEnabled(False)

    def play_selection(self):
        selection_audio = self.pattern_panel.selection_audio
        if selection_audio is None:
            return
        self.stop_audio()
        sr = int(self.pattern_panel.selection_meta.get('sample_rate', self.audio_data.get('sample_rate')))
        self.playing = True
        self.playing_selection = True
        self.playback_start_time = datetime.now().timestamp()
        self.audio_thread = threading.Thread(target=self._play_audio_thread, args=(selection_audio, sr), daemon=True)
        self.audio_thread.start()
        self.playback_timer.start(50)
        self.audio_panel.set_playing_state()
        self.viewport_scroll.setEnabled(False)

    def _play_audio_thread(self, audio, sr):
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paFloat32, channels=1, rate=sr, output=True)
            chunk_size = 1024
            audio_float = audio.astype('float32')
            for i in range(0, len(audio_float), chunk_size):
                if not self.playing:
                    break
                chunk = audio_float[i:i+chunk_size]
                stream.write(chunk.tobytes())
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            print(f"Audio error: {e}")
        self.playing = False

    def pause_audio(self):
        self.playing = False
        self.playback_timer.stop()
        if self.audio_thread:
            self.audio_thread.join()
        self.audio_panel.set_paused_state()
        try:
            self.viewport_scroll.setEnabled(self.spectrogram_widget._scrollable)
        except:
            pass
        self.play_btn.setText("Play")
        self.play_btn.setEnabled(True)

    def stop_audio(self):
        self.playing = False
        self.playback_timer.stop()
        if self.audio_thread:
            self.audio_thread.join()
        self.spectrogram_widget.set_playback_position(None)
        self.audio_panel.set_stopped_state()
        try:
            self.viewport_scroll.setEnabled(self.spectrogram_widget._scrollable)
        except:
            pass
        try:
            self.playing_selection = False
            self.spectrogram_widget.set_selection_playback_pos(None)
        except:
            pass
        self.play_btn.setText("Play")
        self.play_btn.setEnabled(True)

    def update_playback_position(self):
        if not self.playing:
            return
        elapsed = datetime.now().timestamp() - self.playback_start_time
        if self.playing_selection:
            self.spectrogram_widget.set_selection_playback_pos(elapsed)
            duration = self.spectrogram_widget.selection_duration
            if duration and elapsed >= duration:
                self.stop_audio()
            return
        current_pos = self.spectrogram_widget.viewport_start + elapsed
        self.spectrogram_widget.set_playback_position(current_pos)
        viewport_end = self.spectrogram_widget.viewport_start + self.spectrogram_widget.viewport_duration
        if current_pos >= viewport_end:
            self.stop_audio()

    def open_search_result(self, file_path):
        self.current_file = file_path
        self.header_file.setText(os.path.basename(file_path))

    def load_embeddings(self):
        self.embedding_panel.status_label.setText("Searching files...")
        self.embedding_panel.load_btn.setEnabled(False)
        success = self.embedding_manager.load_best_available(
            on_done=self.embedding_panel.on_embeddings_loaded,
            on_error=lambda e: (
                self.embedding_panel.status_label.setText(f"Error: {e}"),
                self.embedding_panel.load_btn.setEnabled(True)
            ),
            on_progress=lambda msg: self.embedding_panel.status_label.setText(msg)
        )
        if not success:
            self.embedding_panel.status_label.setText("Embeddings not found in perch2/")
            self.embedding_panel.load_btn.setEnabled(True)

    def search_embeddings(self):
        if self.audio_data is None:
            self.embedding_panel.status_label.setText("No audio loaded")
            return
        if not self.embedding_manager.loaded:
            self.embedding_panel.status_label.setText("Embeddings not loaded")
            return
        mask = self.spectrogram_widget.mask
        if mask is None or not mask.any():
            self.embedding_panel.status_label.setText("Select a region first (5s max)")
            return
        time_cols = np.any(mask > 0, axis=0)
        if not np.any(time_cols):
            return
        first = int(np.where(time_cols)[0][0])
        last = int(np.where(time_cols)[0][-1])
        times = self.audio_data['times']
        start_time = times[first] + self.audio_data.get('time_offset', 0.0)
        end_time = times[last] + self.audio_data.get('time_offset', 0.0)
        selection_duration = end_time - start_time
        if selection_duration > 5.5:
            self.embedding_panel.status_label.setText(f"Selection too long: {selection_duration:.1f}s (max 5s)")
            return
        self.embedding_panel.status_label.setText("Computing Perch embedding...")
        sr = self.audio_data['sample_rate']
        audio = self.audio_data['audio']
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)
        selection_audio = audio[start_sample:end_sample]
        query_emb = self.compute_embedding(selection_audio, sr)
        if query_emb is not None:
            self.embedding_panel.status_label.setText("Searching database...")
            results = self.embedding_manager.search(query_emb, top_k=20)
            self.embedding_panel.show_results(results)
            self.search_results = results
            self.embedding_panel.status_label.setText(f"{len(results)} results found")
        else:
            self.embedding_panel.status_label.setText("Embedding computation failed")

    def load_perch_model(self):
        if self.perch_model is not None:
            return True
        if self.perch_model_loading:
            return False
        try:
            self.perch_model_loading = True
            self.embedding_panel.status_label.setText("Loading Perch model...")
            from perch_hoplite.zoo import model_configs
            self.perch_model = model_configs.load_model_by_name("perch_v2")
            self.perch_model_loading = False
            self.embedding_panel.status_label.setText("Perch model loaded")
            return True
        except Exception as e:
            self.perch_model_loading = False
            self.embedding_panel.status_label.setText(f"Perch error: {str(e)[:50]}")
            return False

    def compute_embedding(self, audio, sr):
        try:
            if not self.load_perch_model():
                return None
            if sr != 32000:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=32000)
                sr = 32000
            target_length = 160000
            if len(audio) < target_length:
                audio = np.pad(audio, (0, target_length - len(audio)), mode='constant')
            elif len(audio) > target_length:
                audio = audio[:target_length]
            audio = audio.astype(np.float32)
            outputs = self.perch_model.embed(audio)
            embedding = outputs.embeddings.flatten()
            return embedding.astype(np.float32)
        except Exception as e:
            print(f"Embedding error: {e}")
            return None

    def on_embedding_result_selected(self, data):
        idx = data['index']
        if idx < len(self.search_results):
            result = self.search_results[idx]
            print(f"Selected: {result['metadata']}")

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()
        if key == Qt.Key.Key_Space:
            if mods & Qt.KeyboardModifier.ShiftModifier:
                if self.pattern_panel.selection_audio is not None:
                    if self.playing:
                        self.pause_audio()
                    else:
                        self.play_selection()
            else:
                if self.playing and not self.playing_selection:
                    self.pause_audio()
                else:
                    self.play_audio()
            return
        if key == Qt.Key.Key_R:
            self.spectrogram_widget.reset_zoom()
            return
        if key == Qt.Key.Key_Minus:
            self.pattern_panel.change_brush_size(-2)
            return
        if key == Qt.Key.Key_Equal:
            self.pattern_panel.change_brush_size(+2)
            return
        super().keyPressEvent(event)
