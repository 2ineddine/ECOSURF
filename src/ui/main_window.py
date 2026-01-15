"""
Main Window - Professional Modular Architecture
Features are selected from left sidebar, panels displayed on right
Viewport scrollbar placed under spectrogram
WITH TOGGLE BUTTONS FOR BOTH PANELS
"""
import os
import threading
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QStackedWidget, QSplitter, QScrollBar, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont
import librosa
from PyQt6.QtCore import pyqtSignal  # <-- Add this if not already imported
from ui.panels.panels_file import FilePanel
from ui.panels.spectrogram_panel import SpectrogramPanel
from ui.panels.view_panel import ViewPanel
from ui.panels.audio_panel import AudioPanel
from ui.panels.pattern_panel import PatternPanel
from ui.panels.search_panel import SearchPanel
from ui.components.spectrogram_widget import SpectrogramWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jungle Audio Pattern Search Tool")
        self.setGeometry(0, 0, 1600, 900)
        
        # Shared state
        self.current_file = None
        self.current_time_range = None
        self.audio_data = None
        self.file_list = []
        self.bottom_mini_toggle = None  # Add this line
        # Audio playback state
        self.audio_thread = None
        self.playing = False
        self.playing_selection = False
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback_position)
        self.playback_start_time = 0
        
        # Panel visibility state
        self.left_panel_visible = True
        self.bottom_panel_visible = True
        self.previous_right_size = 0
        self.previous_left_size = 220   
        self.bottom_container = None
        self.right_panel_height = 1380  # Add this line to track right panel height
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left sidebar container with toggle button
        left_container = QWidget()
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # Feature selector
        self.feature_list = QListWidget()
        self.feature_list.setMaximumWidth(220)
        self.feature_list.setMinimumWidth(220)
        self.feature_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.feature_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.feature_list.setSelectionBehavior(QListWidget.SelectionBehavior.SelectRows)
        self.feature_list.setSpacing(2)
        
        # Add features
        features = [
            "File Management",
            "Spectrogram",
            "View Controls",
            "Audio Playback",
            "Pattern Selection",
            "Pattern Search"
        ]
        
        for feature in features:
            self.feature_list.addItem(feature)
        
        # Clean Ubuntu styling
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
        
        # Left toggle button
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
        
        # Right side - Stacked panels and spectrogram
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Create a container for spectrogram
        spectrogram_container = QWidget()
        spectrogram_layout = QVBoxLayout(spectrogram_container)
        spectrogram_layout.setContentsMargins(10, 10, 10, 10)
        spectrogram_layout.setSpacing(0)
        
        # Spectrogram display
        self.spectrogram_widget = SpectrogramWidget()
        spectrogram_layout.addWidget(self.spectrogram_widget)
        
        right_layout.addWidget(spectrogram_container, stretch=3)
        
        # Bottom toggle button - ABOVE scrollbar (separate from bottom_container)
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
        right_layout.addWidget(self.bottom_toggle_btn)  # ADD TOGGLE BUTTON FIRST
        
        # Viewport scrollbar - BELOW toggle button (always visible)
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
        right_layout.addWidget(self.viewport_scroll)  # ADD SCROLLBAR AFTER TOGGLE BUTTON
        
        # Bottom: Feature panels (without toggle button now)
        self.bottom_container = QWidget()
        self.bottom_container.setMinimumHeight(400)  # SET MINIMUM HEIGHT HERE (adjust this value)
        self.bottom_container.setStyleSheet("background-color: #FAFAFA; border-top: 1px solid #DEDEDE;")
        bottom_layout = QVBoxLayout(self.bottom_container)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)
        
        self.panel_stack = QStackedWidget()
        
        # Create all panels
        self.file_panel = FilePanel()
        self.spectrogram_panel = SpectrogramPanel()
        self.view_panel = ViewPanel()
        self.audio_panel = AudioPanel()
        self.pattern_panel = PatternPanel()
        self.search_panel = SearchPanel()
        
        # Add panels to stack
        self.panel_stack.addWidget(self.file_panel)
        self.panel_stack.addWidget(self.spectrogram_panel)
        self.panel_stack.addWidget(self.view_panel)
        self.panel_stack.addWidget(self.audio_panel)
        self.panel_stack.addWidget(self.pattern_panel)
        self.panel_stack.addWidget(self.search_panel)
        
        bottom_layout.addWidget(self.panel_stack)
        
        right_layout.addWidget(self.bottom_container, stretch=1)
        
        # Main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.addWidget(left_container)
        self.main_splitter.addWidget(right_widget)
        self.main_splitter.setSizes([220, 1200])
        self.main_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(self.main_splitter)
        
        # Select first feature by default
        self.feature_list.setCurrentRow(0)
    def toggle_left_panel(self):
        """Toggle left sidebar visibility - completely close like Ubuntu"""
        if self.left_panel_visible:
            # Completely hide left panel
            self.feature_list.hide()
            self.feature_list.setMaximumWidth(0)
            self.feature_list.setMinimumWidth(0)
            self.left_toggle_btn.setText("▶")
            self.left_toggle_btn.setToolTip("Show sidebar (F1)")
            self.left_panel_visible = False
            
            # Store current splitter state
            current_sizes = self.main_splitter.sizes()
            
            # Give the space from left panel to the spectrogram
            if self.bottom_panel_visible:
                # Bottom visible, left hidden: give left panel space to spectrogram
                self.main_splitter.setSizes([20, current_sizes[1] + 200])
            else:
                # Both panels hidden: give maximum space to spectrogram
                self.main_splitter.setSizes([20, current_sizes[1] + 220])
            
            # Update window title
        else:
            # Show left panel
            self.feature_list.show()
            self.feature_list.setMaximumWidth(220)
            self.feature_list.setMinimumWidth(220)
            self.left_toggle_btn.setText("◀")
            self.left_toggle_btn.setToolTip("Hide sidebar (F1)")
            self.left_panel_visible = True
            
            # Restore standard splitter sizes
            if self.bottom_panel_visible:
                self.main_splitter.setSizes([220, 1180])  # Both panels visible
            else:
                self.main_splitter.setSizes([220, 1360])  # Bottom hidden, left visible
            
            # Restore window title

    def toggle_bottom_panel(self):
        """Toggle bottom panel visibility - exactly like left panel behavior"""
        if self.bottom_panel_visible:
            # Completely hide panel content
            self.panel_stack.hide()
            
            # Store the current panel height before hiding
            self.previous_right_size = self.main_splitter.sizes()[1]
            
            # Hide the entire bottom container
            self.bottom_container.hide()
            
            # Change the main toggle button text to "Show"
            self.bottom_toggle_btn.setText("▲")
            
            self.bottom_panel_visible = False
            
            # Give the space to spectrogram (like left panel does)
            if self.left_panel_visible:
                # Left visible, bottom hidden: give more space to spectrogram
                self.main_splitter.setSizes([220, self.previous_right_size + 600])
            else:
                # Both panels hidden: give maximum space to spectrogram
                self.main_splitter.setSizes([20, self.previous_right_size + 800])
                
            # Update window title
            self.setWindowTitle("Jungle Audio Pattern Search (Controls hidden)")
        else:
            # Show panel content
            self.bottom_container.show()
            self.panel_stack.show()
            
            # Change the main toggle button text back to "Hide"
            self.bottom_toggle_btn.setText("▼")
            self.bottom_toggle_btn.setToolTip("Hide controls (F2)")
            
            self.bottom_panel_visible = True
            
            # Restore original splitter sizes
            # ADJUST THESE VALUES TO CHANGE BOTTOM PANEL HEIGHT:
            if self.left_panel_visible:
                self.main_splitter.setSizes([220, 500])  # Change 1180 - smaller = taller bottom panel
            else:
                self.main_splitter.setSizes([20, 1360])   # Change 1360 - smaller = taller bottom panel
            
            # Restore window title
            self.setWindowTitle("Jungle Audio Pattern Search")
            
            # Restore window title
            
    def on_period_dict_loaded(self, period_dict):
        """Handle period dictionary loaded from file panel"""
        # Pass to search panel for accelerated searching
        if hasattr(self, 'search_panel'):
            self.search_panel.set_period_dict(period_dict)
        
    
    def resizeEvent(self, event):
        """Handle window resize to keep mini toggle button positioned correctly"""
        super().resizeEvent(event)
        
        # Reposition the mini toggle button if it exists and is visible
        if self.bottom_mini_toggle is not None and self.bottom_mini_toggle.isVisible():
            # Calculate the actual right panel width (accounting for left panel visibility)
            left_panel_width = 220 if self.left_panel_visible else 20
            right_panel_width = self.width() - left_panel_width
            
            # Center the button within the right panel area
            button_x = left_panel_width + (right_panel_width - 120) // 2
            
            # Position at the VERY BOTTOM of the window
            self.bottom_mini_toggle.move(
                button_x,                # Center horizontally in right panel
                self.height() - 20       # Position at very bottom of window
            )
    def connect_signals(self):
        """Connect all inter-panel signals"""
        self.file_panel.file_loaded.connect(self.on_file_loaded_with_source)        # File panel signals
        self.file_panel.search_scope_changed.connect(self.on_search_scope_changed)
        self.file_panel.period_dict_loaded.connect(self.on_period_dict_loaded)
        self.file_panel.folder_loaded.connect(self.on_folder_loaded)
        
        # Spectrogram panel signals
        self.spectrogram_panel.spectrogram_computed.connect(self.on_spectrogram_computed)
        
        # View panel signals
        self.view_panel.zoom_toggled.connect(self.on_zoom_toggled)
        self.view_panel.zoom_reset_requested.connect(self.on_zoom_reset)
        self.view_panel.cursor_changed.connect(self.spectrogram_widget.setCursor)
        
        # Audio panel signals
        self.audio_panel.play_requested.connect(self.play_audio)
        self.audio_panel.pause_requested.connect(self.pause_audio)
        self.audio_panel.stop_requested.connect(self.stop_audio)
        
        # Pattern panel signals
        self.pattern_panel.brush_toggled.connect(self.on_brush_toggled)
        self.pattern_panel.brush_size_changed.connect(self.on_brush_size_changed)
        self.pattern_panel.rect_mode_toggled.connect(self.on_rect_mode_toggled)
        self.pattern_panel.selection_cleared.connect(self.spectrogram_widget.clear_mask)
        self.pattern_panel.selection_cleared.connect(self.spectrogram_widget.clear_mask)
        self.pattern_panel.extract_requested.connect(self.extract_selection)
        self.pattern_panel.play_selection_requested.connect(self.play_selection)
        self.pattern_panel.cursor_changed.connect(self.spectrogram_widget.setCursor)
        
        # Search panel signals
        self.search_panel.result_opened.connect(self.open_search_result)
        
        # Spectrogram widget signals
        try:
            self.spectrogram_widget.scrollableChanged.connect(self.viewport_scroll.setEnabled)
        except Exception:
            pass
        try:
            self.spectrogram_widget.selectionChanged.connect(self.extract_selection)
        except Exception:
            pass
            
    def on_feature_changed(self, index):
        """Switch displayed panel when feature is selected"""
        self.panel_stack.setCurrentIndex(index)
        
    # File: main_window.py
# REPLACE the on_file_loaded_with_source method with this:

    def on_file_loaded_with_source(self, file_path, time_range, source_type):
        """Handle file loaded from file panel - accepts str OR list"""
        self.current_file = file_path  # Can be str (single) or list (multiple)
        self.current_time_range = time_range
        
        # Update spectrogram panel with the file(s)
        self.spectrogram_panel.set_file(file_path, time_range, source_type)
        
        # Update status in file panel based on single vs multiple files
        if isinstance(file_path, list):
            # Multiple files selected
            self.file_panel.update_file_info(
                f"Ready to compute {len(file_path)} files "
                f"({len(file_path)*60:.0f}s total)"
            )
        else:
            # Single file
            self.file_panel.update_file_info(
                f"Ready to compute (source: {source_type})"
            )
        
    def on_folder_loaded(self, file_list):
        """Handle folder loaded from file panel"""
        self.file_list = file_list
        
        # Update search panel
        self.search_panel.set_file_list(file_list)
        
    def on_spectrogram_computed(self, audio_data):
        """Handle spectrogram computation complete"""
        self.audio_data = audio_data
        
        # Update file panel with frequency info
        max_freq = audio_data['frequencies'][-1]
        self.file_panel.update_file_info(f"Max Frequency: {max_freq:.0f} Hz")
        
        # Update spectrogram widget
        self.spectrogram_widget.set_spectrogram(
            audio_data['spectrogram'], 
            audio_data['frequencies'], 
            audio_data['times'], 
            audio_data['time_offset']
        )
        
        # Update viewport scrollbar
        total_duration = float(audio_data['times'][-1])
        viewport_duration = self.spectrogram_widget.viewport_duration
        self.viewport_scroll.setEnabled(total_duration > viewport_duration)
        self.viewport_scroll.setValue(0)
        
        # Enable audio controls
        self.audio_panel.enable_controls(True)
        
        # Update search panel
        self.search_panel.set_audio_data(audio_data)
        
    def on_viewport_scroll(self, value):
        """Handle viewport scrollbar movement"""
        if self.playing:
            return
        self.spectrogram_widget.scroll_viewport(value)
        
    def on_zoom_toggled(self, enabled):
        """Handle zoom mode toggle"""
        self.spectrogram_widget.zoom_enabled = enabled
        if enabled:
            self.pattern_panel.disable_brush()
            
    def on_zoom_reset(self):
        """Handle zoom reset"""
        self.spectrogram_widget.reset_zoom()
        
    def on_brush_toggled(self, enabled):
        """Handle brush mode toggle"""
        self.spectrogram_widget.brush_enabled = enabled
        if enabled:
            self.view_panel.disable_zoom()
    
    def on_search_scope_changed(self, scope_type, file_list):
        """Handle search scope change from file panel"""
        # Update search panel
        if hasattr(self, 'search_panel') and hasattr(self.search_panel, 'set_search_scope'):
            self.search_panel.set_search_scope(scope_type, file_list)
        
        # Show in status bar
        scope_names = {
            "database": "Entire database",
            "current": "Current file only",
            "period": "Selected date range"
        }
        self.statusBar().showMessage(
            f"Search scope: {scope_names.get(scope_type, 'Unknown')} ({len(file_list)} files)",
            3000
        )
    def on_rect_mode_toggled(self, enabled):
        """Handle rectangle selection mode toggle"""
        if enabled:
            # Enable rectangle selection mode on spectrogram widget
            self.spectrogram_widget.rect_selection_mode = True
            self.spectrogram_widget.brush_enabled = False
            # Disable zoom when rect selection is on
            self.view_panel.disable_zoom()
        else:
            self.spectrogram_widget.rect_selection_mode = False
            
    def on_brush_size_changed(self, size):
        """Handle brush size change"""
        self.spectrogram_widget.brush_size = size
        
    def extract_selection(self):
        """Extract audio from painted selection"""
        try:
            from core.spectrogram_audio import extract_patch_audio
        except Exception:
            return
            
        if self.audio_data is None:
            return
            
        mask = self.spectrogram_widget.mask
        if mask is None or not mask.any():
            return
            
        n_fft = int(self.spectrogram_panel.fft_combo.currentText())
        hop_length = int(self.spectrogram_panel.hop_combo.currentText())
        
        audio = self.audio_data.get('audio')
        sr = self.audio_data.get('sample_rate')
        
        try:
            stft = librosa.stft(audio, n_fft=n_fft, hop_length=hop_length)
        except Exception:
            return
            
        sel_audio, meta = extract_patch_audio(
            stft, mask, sr, 
            hop_length=hop_length, 
            n_fft=n_fft, 
            time_offset=self.audio_data.get('time_offset', 0.0)
        )
        
        if sel_audio is None or len(sel_audio) == 0:
            return
            
        # Update pattern panel
        self.pattern_panel.set_selection_audio(sel_audio, meta)
        
        # Show selection waveform
        try:
            self.spectrogram_widget.show_selection_audio(sel_audio, sr)
        except Exception:
            pass
            
    def play_audio(self):
        """Play main audio from current viewport"""
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
        
        self.audio_thread = threading.Thread(
            target=self._play_audio_thread, 
            args=(audio_segment, sr),
            daemon=True
        )
        self.audio_thread.start()
        
        self.playback_timer.start(50)
        self.audio_panel.set_playing_state()
        self.viewport_scroll.setEnabled(False)
        
    def play_selection(self):
        """Play extracted selection audio"""
        selection_audio = self.pattern_panel.selection_audio
        if selection_audio is None:
            return
            
        self.stop_audio()
        
        sr = int(self.pattern_panel.selection_meta.get(
            'sample_rate', 
            self.audio_data.get('sample_rate')
        ))
        
        self.playing = True
        self.playing_selection = True
        self.playback_start_time = datetime.now().timestamp()
        
        self.audio_thread = threading.Thread(
            target=self._play_audio_thread, 
            args=(selection_audio, sr),
            daemon=True
        )
        self.audio_thread.start()
        
        self.playback_timer.start(50)
        self.audio_panel.set_playing_state()
        self.viewport_scroll.setEnabled(False)
        
    def _play_audio_thread(self, audio, sr):
        """Audio playback thread"""
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paFloat32, 
                channels=1, 
                rate=sr, 
                output=True
            )
            
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
        """Pause audio playback"""
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
        """Stop audio playback"""
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
        """Update playback cursor position"""
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
        
        viewport_end = (self.spectrogram_widget.viewport_start + 
                       self.spectrogram_widget.viewport_duration)
        if current_pos >= viewport_end:
            self.stop_audio()
            
    def open_search_result(self, file_path):
        """Open a file from search results"""
        self.current_file = file_path
        self.file_panel.file_label.setText(f"Opened: {os.path.basename(file_path)}")
        
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        key = event.key()
        mods = event.modifiers()
        
        # Space: play/pause
        if key == Qt.Key.Key_Space:
            if mods & Qt.KeyboardModifier.ShiftModifier:
                # Shift+Space: play/pause selection
                if self.pattern_panel.selection_audio is not None:
                    if self.playing:
                        self.pause_audio()
                    else:
                        self.play_selection()
            else:
                # Space: play/pause main
                if self.playing and not self.playing_selection:
                    self.pause_audio()
                else:
                    self.play_audio()
            return
            
        # R: reset zoom
        if key == Qt.Key.Key_R:
            self.spectrogram_widget.reset_zoom()
            return
            
        # - / = : brush size
        if key == Qt.Key.Key_Minus:
            self.pattern_panel.change_brush_size(-2)
            return
        if key == Qt.Key.Key_Equal:
            self.pattern_panel.change_brush_size(+2)
            return
            
        # F1: toggle left panel
        if key == Qt.Key.Key_F1:
            self.toggle_left_panel()
            return
            
        # F2: toggle bottom panel
        if key == Qt.Key.Key_F2:
            self.toggle_bottom_panel()
            return
            
        super().keyPressEvent(event)