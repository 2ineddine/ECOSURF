"""
Main Window - Professional Modular Architecture
"""
import os
import threading
from datetime import datetime

import numpy as np
import librosa
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QStackedWidget, QSplitter, QScrollBar, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from ui.panels.panels_file import FilePanel
from ui.panels.spectrogram_panel import SpectrogramPanel
from ui.panels.view_panel import ViewPanel
from ui.panels.audio_panel import AudioPanel
from ui.panels.pattern_panel import PatternPanel
from ui.panels.search_panel import SearchPanel
from ui.panels.embedding_panel import EmbeddingPanel
from ui.panels.clustering_panel import ClusteringPanel
from ui.components.spectrogram_widget import SpectrogramWidget
from core.embedding_manager import EmbeddingManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jungle Audio Pattern Search Tool")
        self.setGeometry(0, 0, 1600, 900)
        
        self.current_file = None
        self.current_time_range = None
        self.audio_data = None
        self.file_list = []
        self.bottom_mini_toggle = None
        self.audio_thread = None
        self.playing = False
        self.playing_selection = False
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback_position)
        self.playback_start_time = 0
        self.left_panel_visible = True
        self.bottom_panel_visible = True
        self.previous_right_size = 0
        self.previous_left_size = 220   
        self.bottom_container = None
        self.right_panel_height = 1380
        self.search_results = []
        self.embedding_manager = EmbeddingManager()
        
        # Perch model - lazy loading (sera charge au premier besoin)
        self.perch_model = None
        self.perch_model_loading = False
        
        self.init_ui()
        self.connect_signals()
        
        # NOTE: Embeddings NOT auto-loaded - user clicks "Charger Embeddings" when ready
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        left_container = QWidget()
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        self.feature_list = QListWidget()
        self.feature_list.setMaximumWidth(220)
        self.feature_list.setMinimumWidth(220)
        self.feature_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.feature_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.feature_list.setSelectionBehavior(QListWidget.SelectionBehavior.SelectRows)
        self.feature_list.setSpacing(2)
        
        features = [
            "File Management",
            "Spectrogram",
            "View Controls",
            "Audio Playback",
            "Pattern Selection",
            "Pattern Search",
            "Embedding Search",
            "Clustering"
        ]
        
        for feature in features:
            self.feature_list.addItem(feature)
        
        self.feature_list.setStyleSheet("""
            QListWidget {
                background-color: #FAFAFA;
                border: none;
                border-right: 1px solid #DEDEDE;
                font-size: 13px;
                padding: 5px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 12px;
                margin: 2px 5px;
                color: #333333;
                border-radius: 3px;
                border: 1px solid transparent;
            }
            QListWidget::item:selected {
                background-color: #E95420;
                color: white;
                font-weight: bold;
                border: 1px solid #E95420;
            }
            QListWidget::item:hover:!selected {
                background-color: #F2F2F2;
            }
        """)
        
        self.feature_list.currentRowChanged.connect(self.on_feature_changed)
        
        self.left_toggle_btn = QPushButton("◀")
        self.left_toggle_btn.setMaximumWidth(20)
        self.left_toggle_btn.setMinimumHeight(100)
        self.left_toggle_btn.clicked.connect(self.toggle_left_panel)
        self.left_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F2;
                color: #333333;
                font-weight: bold;
                border: none;
                font-size: 14px;
                border-left: 1px solid #DEDEDE;
            }
            QPushButton:hover {
                background-color: #E5E5E5;
            }
        """)
        
        left_layout.addWidget(self.feature_list)
        left_layout.addWidget(self.left_toggle_btn)
        
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        spectrogram_container = QWidget()
        spectrogram_layout = QVBoxLayout(spectrogram_container)
        spectrogram_layout.setContentsMargins(10, 10, 10, 10)
        spectrogram_layout.setSpacing(0)
        
        self.spectrogram_widget = SpectrogramWidget()
        spectrogram_layout.addWidget(self.spectrogram_widget)
        
        right_layout.addWidget(spectrogram_container, stretch=3)
        
        self.bottom_toggle_btn = QPushButton("▼")
        self.bottom_toggle_btn.setMaximumHeight(25)
        self.bottom_toggle_btn.clicked.connect(self.toggle_bottom_panel)
        self.bottom_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F2;
                color: #333333;
                font-weight: bold;
                border: none;
                font-size: 11px;
                border-top: 1px solid #DEDEDE;
                border-bottom: 1px solid #DEDEDE;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #E5E5E5;
            }
        """)
        right_layout.addWidget(self.bottom_toggle_btn)
        
        self.viewport_scroll = QScrollBar(Qt.Orientation.Horizontal)
        self.viewport_scroll.setMinimum(0)
        self.viewport_scroll.setMaximum(100)
        self.viewport_scroll.setValue(0)
        self.viewport_scroll.setEnabled(False)
        self.viewport_scroll.valueChanged.connect(self.on_viewport_scroll)
        self.viewport_scroll.setStyleSheet("""
            QScrollBar:horizontal {
                border: 1px solid #DEDEDE;
                background: #FAFAFA;
                height: 12px;
                margin: 0px;
                border-top: 1px solid #DEDEDE;
            }
            QScrollBar::handle:horizontal {
                background: #CCCCCC;
                min-width: 20px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #AAAAAA;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        right_layout.addWidget(self.viewport_scroll)
        
        self.bottom_container = QWidget()
        self.bottom_container.setMinimumHeight(400)
        self.bottom_container.setStyleSheet("background-color: #FAFAFA; border-top: 1px solid #DEDEDE;")
        bottom_layout = QVBoxLayout(self.bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)
        
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
        
        bottom_layout.addWidget(self.panel_stack)
        right_layout.addWidget(self.bottom_container, stretch=1)
        
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.addWidget(left_container)
        self.main_splitter.addWidget(right_widget)
        self.main_splitter.setSizes([220, 1200])
        self.main_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(self.main_splitter)
        self.feature_list.setCurrentRow(0)

    def toggle_left_panel(self):
        if self.left_panel_visible:
            self.feature_list.hide()
            self.feature_list.setMaximumWidth(0)
            self.feature_list.setMinimumWidth(0)
            self.left_toggle_btn.setText("▶")
            self.left_panel_visible = False
            current_sizes = self.main_splitter.sizes()
            if self.bottom_panel_visible:
                self.main_splitter.setSizes([20, current_sizes[1] + 200])
            else:
                self.main_splitter.setSizes([20, current_sizes[1] + 220])
        else:
            self.feature_list.show()
            self.feature_list.setMaximumWidth(220)
            self.feature_list.setMinimumWidth(220)
            self.left_toggle_btn.setText("◀")
            self.left_panel_visible = True
            if self.bottom_panel_visible:
                self.main_splitter.setSizes([220, 1180])
            else:
                self.main_splitter.setSizes([220, 1360])

    def toggle_bottom_panel(self):
        if self.bottom_panel_visible:
            self.panel_stack.hide()
            self.previous_right_size = self.main_splitter.sizes()[1]
            self.bottom_container.hide()
            self.bottom_toggle_btn.setText("▲")
            self.bottom_panel_visible = False
            if self.left_panel_visible:
                self.main_splitter.setSizes([220, self.previous_right_size + 600])
            else:
                self.main_splitter.setSizes([20, self.previous_right_size + 800])
            self.setWindowTitle("Jungle Audio Pattern Search (Controls hidden)")
        else:
            self.bottom_container.show()
            self.panel_stack.show()
            self.bottom_toggle_btn.setText("▼")
            self.bottom_panel_visible = True
            if self.left_panel_visible:
                self.main_splitter.setSizes([220, 500])
            else:
                self.main_splitter.setSizes([20, 1360])
            self.setWindowTitle("Jungle Audio Pattern Search")

    def on_period_dict_loaded(self, period_dict):
        if hasattr(self, 'search_panel'):
            self.search_panel.set_period_dict(period_dict)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.bottom_mini_toggle is not None and self.bottom_mini_toggle.isVisible():
            left_panel_width = 220 if self.left_panel_visible else 20
            right_panel_width = self.width() - left_panel_width
            button_x = left_panel_width + (right_panel_width - 120) // 2
            self.bottom_mini_toggle.move(button_x, self.height() - 20)

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
        except Exception:
            pass
        # NOTE: extract_selection maintenant seulement sur bouton "Extract", pas en temps reel
        # self.spectrogram_widget.selectionChanged.connect(self.extract_selection)

    def on_feature_changed(self, index):
        self.panel_stack.setCurrentIndex(index)

    def on_file_loaded_with_source(self, file_path, time_range, source_type):
        self.current_file = file_path
        self.current_time_range = time_range
        self.spectrogram_panel.set_file(file_path, time_range, source_type)
        if isinstance(file_path, list):
            self.file_panel.update_file_info(f"Ready to compute {len(file_path)} files ({len(file_path)*60:.0f}s total)")
        else:
            self.file_panel.update_file_info(f"Ready to compute (source: {source_type})")

    def on_folder_loaded(self, file_list):
        self.file_list = file_list
        self.search_panel.set_file_list(file_list)

    def on_spectrogram_computed(self, audio_data):
        self.audio_data = audio_data
        max_freq = audio_data['frequencies'][-1]
        self.file_panel.update_file_info(f"Max Frequency: {max_freq:.0f} Hz")
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
        scope_names = {"database": "Entire database", "current": "Current file only", "period": "Selected date range"}
        self.statusBar().showMessage(f"Search scope: {scope_names.get(scope_type, 'Unknown')} ({len(file_list)} files)", 3000)

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
        except Exception:
            self.pattern_panel.hide_progress()
            return
        if self.audio_data is None:
            self.pattern_panel.hide_progress()
            return
        mask = self.spectrogram_widget.mask
        if mask is None or not mask.any():
            self.pattern_panel.hide_progress()
            self.pattern_panel.selection_status.setText("Pas de selection")
            return
        
        # Afficher progression
        self.pattern_panel.update_progress(10, "Preparation...")
        QTimer.singleShot(50, self._do_extract_selection)
    
    def _do_extract_selection(self):
        """Execute l'extraction ISTFT avec progression"""
        try:
            from core.spectrogram_audio import extract_patch_audio
        except Exception:
            self.pattern_panel.hide_progress()
            return
            
        self.pattern_panel.update_progress(20, "Calcul STFT...")
        
        n_fft = int(self.spectrogram_panel.fft_combo.currentText())
        hop_length = int(self.spectrogram_panel.hop_combo.currentText())
        audio = self.audio_data.get('audio')
        sr = self.audio_data.get('sample_rate')
        mask = self.spectrogram_widget.mask
        
        try:
            stft = librosa.stft(audio, n_fft=n_fft, hop_length=hop_length)
        except Exception:
            self.pattern_panel.hide_progress()
            return
        
        self.pattern_panel.update_progress(60, "Extraction audio (ISTFT)...")
        
        sel_audio, meta = extract_patch_audio(
            stft, mask, sr, 
            hop_length=hop_length, 
            n_fft=n_fft, 
            time_offset=self.audio_data.get('time_offset', 0.0)
        )
        
        self.pattern_panel.update_progress(90, "Finalisation...")
        
        if sel_audio is None or len(sel_audio) == 0:
            self.pattern_panel.hide_progress()
            self.pattern_panel.selection_status.setText("Extraction echouee")
            return
            
        self.pattern_panel.set_selection_audio(sel_audio, meta)
        
        try:
            self.spectrogram_widget.show_selection_audio(sel_audio, sr)
        except Exception:
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
            print(f"Audio playback error: {e}")
        self.playing = False

    def pause_audio(self):
        self.playing = False
        self.playback_timer.stop()
        if self.audio_thread:
            self.audio_thread.join()
        self.audio_panel.set_paused_state()
        try:
            self.viewport_scroll.setEnabled(self.spectrogram_widget._scrollable)
        except Exception:
            pass
        if self.playing_selection:
            elapsed = datetime.now().timestamp() - self.playback_start_time
            try:
                self.spectrogram_widget.set_selection_playback_pos(elapsed)
            except Exception:
                pass

    def stop_audio(self):
        self.playing = False
        self.playback_timer.stop()
        if self.audio_thread:
            self.audio_thread.join()
        self.spectrogram_widget.set_playback_position(None)
        self.audio_panel.set_stopped_state()
        try:
            self.viewport_scroll.setEnabled(self.spectrogram_widget._scrollable)
        except Exception:
            pass
        try:
            self.playing_selection = False
            self.spectrogram_widget.set_selection_playback_pos(None)
        except Exception:
            pass

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
        self.file_panel.file_label.setText(f"Opened: {os.path.basename(file_path)}")

    def load_embeddings(self):
        # Utiliser automatiquement les meilleurs fichiers disponibles (sample10 avec FAISS)
        self.embedding_panel.status_label.setText("Recherche des fichiers...")
        self.embedding_panel.load_btn.setEnabled(False)
        
        success = self.embedding_manager.load_best_available(
            on_done=self.embedding_panel.on_embeddings_loaded,
            on_error=lambda e: (
                self.embedding_panel.status_label.setText(f"Erreur: {e}"),
                self.embedding_panel.load_btn.setEnabled(True)
            ),
            on_progress=lambda msg: self.embedding_panel.status_label.setText(msg)
        )
        
        if not success:
            self.embedding_panel.status_label.setText("Fichiers embeddings non trouvés dans perch2/")
            self.embedding_panel.load_btn.setEnabled(True)

    def search_embeddings(self):
        if self.audio_data is None:
            self.embedding_panel.status_label.setText("Pas d'audio charge")
            return
        if not self.embedding_manager.loaded:
            self.embedding_panel.status_label.setText("Embeddings non charges")
            return
            
        mask = self.spectrogram_widget.mask
        if mask is None or not mask.any():
            self.embedding_panel.status_label.setText("Selectionnez une zone d'abord (5s max)")
            return
            
        time_cols = np.any(mask > 0, axis=0)
        if not np.any(time_cols):
            return
            
        first = int(np.where(time_cols)[0][0])
        last = int(np.where(time_cols)[0][-1])
        times = self.audio_data['times']
        
        # Calculer le temps de selection
        start_time = times[first] + self.audio_data.get('time_offset', 0.0)
        end_time = times[last] + self.audio_data.get('time_offset', 0.0)
        selection_duration = end_time - start_time
        
        # Vérifier que la sélection ne dépasse pas 5 secondes
        if selection_duration > 5.5:  # Petite marge
            self.embedding_panel.status_label.setText(f"Sélection trop longue: {selection_duration:.1f}s (max 5s)")
            return
        
        self.embedding_panel.status_label.setText("Extraction de l'embedding Perch...")
        
        # Extraire l'audio de la sélection
        sr = self.audio_data['sample_rate']
        audio = self.audio_data['audio']
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)
        selection_audio = audio[start_sample:end_sample]
        
        # Calculer l'embedding avec Perch
        query_emb = self.compute_embedding(selection_audio, sr)
        
        if query_emb is not None:
            self.embedding_panel.status_label.setText("Recherche dans la base...")
            results = self.embedding_manager.search(query_emb, top_k=20)
            self.embedding_panel.show_results(results)
            self.search_results = results
            self.embedding_panel.status_label.setText(f"{len(results)} resultats trouves")
        else:
            self.embedding_panel.status_label.setText("Segment non trouve dans la base 2019")

    def find_matching_embedding(self, start_time, end_time):
        """
        Trouve les embeddings correspondant au segment selectionne.
        Si la selection chevauche plusieurs segments de 5s, on fait la moyenne
        ponderee par le chevauchement.
        """
        if not self.embedding_manager.loaded:
            return None
        
        # Extraire le nom du fichier courant
        current_file = self.current_file
        if current_file is None:
            return None
        
        # Extraire juste le nom de fichier (sans chemin)
        import os
        file_name = os.path.basename(current_file)
        # Nettoyer le nom pour matcher (enlever extension si besoin)
        file_base = file_name.replace('.flac', '').replace('.wav', '')
        
        # Chercher TOUS les segments qui chevauchent la selection
        metadata = self.embedding_manager.metadata
        matching_segments = []  # (index, overlap_duration, meta)
        
        for i, meta in enumerate(metadata):
            meta_file = meta.get('file', '').replace('.flac', '').replace('.wav', '')
            meta_start = meta.get('start', 0)
            meta_end = meta.get('end', 0)
            
            # Verifier si le fichier correspond
            if file_base in meta_file or meta_file in file_base:
                # Calculer le chevauchement temporel
                overlap_start = max(start_time, meta_start)
                overlap_end = min(end_time, meta_end)
                overlap = max(0, overlap_end - overlap_start)
                
                if overlap > 0.1:  # Au moins 0.1s de chevauchement
                    matching_segments.append((i, overlap, meta))
        
        if len(matching_segments) == 0:
            # Aucun match direct - mode demo
            self.embedding_panel.status_label.setText("Fichier non dans base 2019 - mode demo")
            if len(metadata) > 0:
                import random
                segment_idx = random.randint(0, len(metadata) - 1)
                return self.embedding_manager.get_embedding(segment_idx)
            return None
        
        # Si un seul segment, retourner directement
        if len(matching_segments) == 1:
            idx, overlap, meta = matching_segments[0]
            self.embedding_panel.status_label.setText(
                f"Segment trouve: {meta['start']:.0f}-{meta['end']:.0f}s"
            )
            return self.embedding_manager.get_embedding(idx)
        
        # Plusieurs segments - faire la moyenne ponderee par le chevauchement
        total_overlap = sum(seg[1] for seg in matching_segments)
        weighted_embedding = np.zeros(1536, dtype=np.float32)
        
        segment_info = []
        for idx, overlap, meta in matching_segments:
            weight = overlap / total_overlap
            emb = self.embedding_manager.get_embedding(idx)
            if emb is not None:
                weighted_embedding += weight * emb
                segment_info.append(f"{meta['start']:.0f}-{meta['end']:.0f}s")
        
        self.embedding_panel.status_label.setText(
            f"{len(matching_segments)} segments combines: {', '.join(segment_info[:3])}..."
        )
        
        return weighted_embedding

    def load_perch_model(self):
        """
        Charge le modèle Perch de façon lazy (au premier besoin).
        Retourne True si le modèle est chargé, False sinon.
        """
        if self.perch_model is not None:
            return True
        
        if self.perch_model_loading:
            return False
        
        try:
            self.perch_model_loading = True
            self.embedding_panel.status_label.setText("Chargement du modèle Perch...")
            
            from perch_hoplite.zoo import model_configs
            self.perch_model = model_configs.load_model_by_name("perch_v2")
            
            self.perch_model_loading = False
            self.embedding_panel.status_label.setText("Modèle Perch chargé!")
            return True
            
        except Exception as e:
            self.perch_model_loading = False
            print(f"Erreur chargement Perch: {e}")
            self.embedding_panel.status_label.setText(f"Erreur Perch: {str(e)[:50]}")
            return False

    def compute_embedding(self, audio, sr):
        """
        Calcul d'embedding pour la sélection avec le modèle Perch.
        Audio doit être 5 secondes à 32kHz (160000 samples).
        """
        try:
            # Charger Perch si nécessaire
            if not self.load_perch_model():
                self.embedding_panel.status_label.setText("Modèle Perch non disponible")
                return None
            
            # Resample to 32kHz if needed (Perch uses 32kHz)
            if sr != 32000:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=32000)
                sr = 32000
            
            # Perch attend 5 secondes = 160000 samples
            target_length = 160000
            
            if len(audio) < target_length:
                # Pad avec des zéros si trop court
                audio = np.pad(audio, (0, target_length - len(audio)), mode='constant')
            elif len(audio) > target_length:
                # Tronquer si trop long
                audio = audio[:target_length]
            
            # Assurer le bon type et shape
            audio = audio.astype(np.float32)
            
            # Calculer l'embedding avec Perch
            outputs = self.perch_model.embed(audio)
            embedding = outputs.embeddings.flatten()
            
            return embedding.astype(np.float32)
            
        except Exception as e:
            print(f"Error computing embedding: {e}")
            self.embedding_panel.status_label.setText(f"Erreur embedding: {str(e)[:50]}")
            return None

    def on_embedding_result_selected(self, data):
        idx = data['index']
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
        if key == Qt.Key.Key_F1:
            self.toggle_left_panel()
            return
        if key == Qt.Key.Key_F2:
            self.toggle_bottom_panel()
            return
        super().keyPressEvent(event)