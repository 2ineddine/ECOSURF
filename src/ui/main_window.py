import os
import re
import threading
from datetime import datetime

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QSlider, QSpinBox, QProgressBar, QListWidget,
    QSplitter, QGroupBox, QComboBox, QCheckBox, QScrollBar, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QCursor
import soundfile as sf

from ui.components.spectrogram_widget import SpectrogramWidget
from ui.dialogs.period_selection import PeriodSelectionDialog
from ui.workers.audio_processor_w import AudioProcessor
from ui.workers.pattern_search_w import PatternSearchThread


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jungle Audio Pattern Search Tool")
        self.setGeometry(100, 100, 1400, 800)

        self.current_file = None
        self.current_time_range = None
        self.audio_data = None
        self.file_list = []
        self.search_thread = None

        self.audio_thread = None
        self.playing = False
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback_position)
        self.playback_start_time = 0

        self.sidebar_visible = True

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QWidget()
        self.sidebar.setMinimumWidth(30)
        self.sidebar.setMaximumWidth(350)

        self.toggle_btn = QPushButton("◀")
        self.toggle_btn.setMaximumWidth(30)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)

        file_group = QGroupBox("File Management")
        file_layout = QVBoxLayout()

        load_btn = QPushButton("Load Audio File")
        load_btn.clicked.connect(self.load_file)
        file_layout.addWidget(load_btn)

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_application)
        file_layout.addWidget(reset_btn)

        load_folder_btn = QPushButton("Load Folder")
        load_folder_btn.clicked.connect(self.load_folder)
        file_layout.addWidget(load_folder_btn)

        self.file_label = QLabel("No file loaded")
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)

        file_group.setLayout(file_layout)
        controls_layout.addWidget(file_group)

        spec_group = QGroupBox("Spectrogram")
        spec_layout = QVBoxLayout()

        spec_layout.addWidget(QLabel("FFT Size:"))
        self.fft_combo = QComboBox()
        self.fft_combo.addItems(["512", "1024", "2048", "4096"])
        self.fft_combo.setCurrentText("2048")
        spec_layout.addWidget(self.fft_combo)

        spec_layout.addWidget(QLabel("Hop Length:"))
        self.hop_combo = QComboBox()
        self.hop_combo.addItems(["128", "256", "512", "1024"])
        self.hop_combo.setCurrentText("512")
        spec_layout.addWidget(self.hop_combo)

        compute_btn = QPushButton("Compute")
        compute_btn.clicked.connect(self.compute_spectrogram)
        spec_layout.addWidget(compute_btn)

        spec_group.setLayout(spec_layout)
        controls_layout.addWidget(spec_group)

        view_group = QGroupBox("View")
        view_layout = QVBoxLayout()

        self.zoom_checkbox = QCheckBox("Enable Zoom")
        self.zoom_checkbox.stateChanged.connect(self.toggle_zoom)
        view_layout.addWidget(self.zoom_checkbox)

        zoom_out_btn = QPushButton("Reset Zoom")
        zoom_out_btn.clicked.connect(self.reset_zoom)
        view_layout.addWidget(zoom_out_btn)

        view_layout.addWidget(QLabel("Time Viewport:"))
        self.viewport_scroll = QScrollBar(Qt.Orientation.Horizontal)
        self.viewport_scroll.setMinimum(0)
        self.viewport_scroll.setMaximum(100)
        self.viewport_scroll.setValue(0)
        self.viewport_scroll.valueChanged.connect(self.scroll_viewport)
        view_layout.addWidget(self.viewport_scroll)

        view_group.setLayout(view_layout)
        controls_layout.addWidget(view_group)

        audio_group = QGroupBox("Audio")
        audio_layout = QVBoxLayout()

        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.play_audio)
        self.play_btn.setEnabled(False)
        audio_layout.addWidget(self.play_btn)

        self.pause_btn = QPushButton("II Pause")
        self.pause_btn.clicked.connect(self.pause_audio)
        self.pause_btn.setEnabled(False)
        audio_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.clicked.connect(self.stop_audio)
        self.stop_btn.setEnabled(False)
        audio_layout.addWidget(self.stop_btn)

        self.playback_label = QLabel("Stopped")
        audio_layout.addWidget(self.playback_label)

        audio_group.setLayout(audio_layout)
        controls_layout.addWidget(audio_group)

        brush_group = QGroupBox("Pattern Selection")
        brush_layout = QVBoxLayout()

        self.brush_checkbox = QCheckBox("Enable Brush")
        self.brush_checkbox.stateChanged.connect(self.toggle_brush)
        brush_layout.addWidget(self.brush_checkbox)

        brush_size_label = QLabel("Brush Size:")
        brush_layout.addWidget(brush_size_label)

        self.brush_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_slider.setMinimum(5)
        self.brush_slider.setMaximum(100)
        self.brush_slider.setValue(20)
        self.brush_slider.valueChanged.connect(self.update_brush_size)
        brush_layout.addWidget(self.brush_slider)

        self.brush_size_label = QLabel("20 px")
        brush_layout.addWidget(self.brush_size_label)

        clear_btn = QPushButton("Clear Selection")
        clear_btn.clicked.connect(self.clear_selection)
        brush_layout.addWidget(clear_btn)

        brush_group.setLayout(brush_layout)
        controls_layout.addWidget(brush_group)

        search_group = QGroupBox("Pattern Search")
        search_layout = QVBoxLayout()

        threshold_label = QLabel("Similarity Threshold:")
        search_layout.addWidget(threshold_label)

        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(50)
        self.threshold_slider.setMaximum(99)
        self.threshold_slider.setValue(70)
        self.threshold_slider.valueChanged.connect(self.update_threshold)
        search_layout.addWidget(self.threshold_slider)

        self.threshold_label = QLabel("0.70")
        search_layout.addWidget(self.threshold_label)

        self.search_btn = QPushButton("Search in Files")
        self.search_btn.clicked.connect(self.start_search)
        self.search_btn.setEnabled(False)
        search_layout.addWidget(self.search_btn)

        self.stop_search_btn = QPushButton("Stop Search")
        self.stop_search_btn.clicked.connect(self.stop_search)
        self.stop_search_btn.setEnabled(False)
        search_layout.addWidget(self.stop_search_btn)

        self.search_progress = QProgressBar()
        search_layout.addWidget(self.search_progress)

        self.search_status = QLabel("Ready")
        search_layout.addWidget(self.search_status)

        search_group.setLayout(search_layout)
        controls_layout.addWidget(search_group)

        results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout()

        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.open_result)
        results_layout.addWidget(self.results_list)

        export_btn = QPushButton("Export Results")
        export_btn.clicked.connect(self.export_results)
        results_layout.addWidget(export_btn)

        results_group.setLayout(results_layout)
        controls_layout.addWidget(results_group)

        controls_layout.addStretch()

        scroll.setWidget(controls_widget)

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.addWidget(scroll)
        sidebar_layout.addWidget(self.toggle_btn)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        self.sidebar_scroll = scroll

        self.spectrogram_widget = SpectrogramWidget()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.addWidget(self.spectrogram_widget)
        content_layout.addWidget(self.progress_bar)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(content_widget)
        self.splitter.setSizes([350, 1050])
        self.splitter.setCollapsible(0, True)

        main_layout.addWidget(self.splitter)

        self.sidebar_animation = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.sidebar_animation.setDuration(200)
        self.sidebar_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar_animation.setStartValue(self.sidebar.width())
            self.sidebar_animation.setEndValue(30)
            self.sidebar_visible = False
            self.toggle_btn.setText("▶")
            for i in range(self.sidebar.layout().count()):
                widget = self.sidebar.layout().itemAt(i).widget()
                if widget and widget != self.toggle_btn:
                    widget.setVisible(False)
        else:
            self.sidebar_animation.setStartValue(self.sidebar.width())
            self.sidebar_animation.setEndValue(350)
            self.sidebar_visible = True
            self.toggle_btn.setText("◀")
            for i in range(self.sidebar.layout().count()):
                widget = self.sidebar.layout().itemAt(i).widget()
                if widget and widget != self.toggle_btn:
                    widget.setVisible(True)

        try:
            self.sidebar_animation.finished.disconnect()
        except Exception:
            pass

        self.sidebar_animation.start()

    def reset_application(self):
        self.stop_audio()
        self.current_file = None
        self.current_time_range = None
        self.audio_data = None
        self.spectrogram_widget.spectrogram = None
        self.spectrogram_widget.update()
        self.file_label.setText("No file loaded - Click 'Load Audio File' to start")
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.load_file()

    def parse_filename(self, filename):
        match = re.match(r'(\w+)_(\d{8})_(\d{6})\.flac', filename)
        if match:
            device_id, date_str, time_str = match.groups()
            datetime_obj = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
            return {
                'device_id': device_id,
                'date': datetime_obj.strftime("%Y-%m-%d"),
                'time': datetime_obj.strftime("%H:%M:%S"),
                'datetime': datetime_obj
            }
        return {'device_id': 'unknown', 'date': 'unknown', 'time': 'unknown'}

    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Audio File", "", "Audio Files (*.flac *.wav *.mp3)")

        if file_path:
            self.current_file = file_path
            metadata = self.parse_filename(os.path.basename(file_path))

            try:
                info = sf.info(file_path)
                duration = info.duration

                dialog = PeriodSelectionDialog(metadata, duration, self)
                if dialog.exec():
                    time_range = dialog.get_time_range()
                    self.current_time_range = time_range

                    range_text = f"{time_range[0]:.1f}s - {time_range[1]:.1f}s"
                    self.file_label.setText(
                        f"Loaded: {os.path.basename(file_path)}\n"
                        f"Date: {metadata['date']} {metadata['time']}\n"
                        f"Range: {range_text}"
                    )
                    self.compute_spectrogram()
            except Exception as e:
                self.file_label.setText(f"Error: {e}")

    def load_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder with FLAC Files")

        if folder_path:
            self.file_list = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.flac')]
            self.file_label.setText(f"Loaded {len(self.file_list)} files from folder")

            if len(self.file_list) > 0:
                self.search_btn.setEnabled(True)

    def compute_spectrogram(self):
        if not self.current_file:
            self.file_label.setText("Please load a file first!")
            return

        n_fft = int(self.fft_combo.currentText())
        hop_length = int(self.hop_combo.currentText())

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.processor = AudioProcessor(self.current_file, n_fft, hop_length, self.current_time_range)
        self.processor.progress.connect(self.progress_bar.setValue)
        self.processor.finished.connect(self.on_spectrogram_ready)
        self.processor.start()

    def on_spectrogram_ready(self, result):
        self.progress_bar.setVisible(False)

        if result:
            self.audio_data = result

            max_freq = result['frequencies'][-1]
            self.file_label.setText(f"{self.file_label.text()}\nMax Frequency: {max_freq:.0f} Hz")

            self.spectrogram_widget.set_spectrogram(result['spectrogram'], result['frequencies'], result['times'], result['time_offset'])
            self.play_btn.setEnabled(True)

            total_duration = result['times'][-1]
            self.viewport_scroll.setEnabled(total_duration > 60)
        else:
            self.file_label.setText("Error computing spectrogram")

    def toggle_zoom(self, state):
        self.spectrogram_widget.zoom_enabled = (state == Qt.CheckState.Checked.value)
        if self.spectrogram_widget.zoom_enabled:
            self.brush_checkbox.setChecked(False)
            self.spectrogram_widget.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.spectrogram_widget.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def toggle_brush(self, state):
        self.spectrogram_widget.brush_enabled = (state == Qt.CheckState.Checked.value)
        if self.spectrogram_widget.brush_enabled:
            self.zoom_checkbox.setChecked(False)
            self.spectrogram_widget.setCursor(QCursor(Qt.CursorShape.CrossCursor))
        else:
            self.spectrogram_widget.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def reset_zoom(self):
        self.spectrogram_widget.reset_zoom()

    def scroll_viewport(self, value):
        self.spectrogram_widget.scroll_viewport(value)

    def update_brush_size(self, value):
        self.spectrogram_widget.brush_size = value
        self.brush_size_label.setText(f"{value} px")

    def clear_selection(self):
        self.spectrogram_widget.clear_mask()

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
        self.playback_start_time = datetime.now().timestamp()
        self.audio_thread = threading.Thread(target=self._play_audio_thread, args=(audio_segment, sr))
        self.audio_thread.start()

        self.playback_timer.start(50)

        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.playback_label.setText("Playing...")

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

        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.playback_label.setText("Paused")

    def stop_audio(self):
        self.playing = False
        self.playback_timer.stop()
        if self.audio_thread:
            self.audio_thread.join()

        self.spectrogram_widget.set_playback_position(None)

        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.playback_label.setText("Stopped")

    def update_playback_position(self):
        if not self.playing:
            return

        elapsed = datetime.now().timestamp() - self.playback_start_time
        current_pos = self.spectrogram_widget.viewport_start + elapsed

        self.spectrogram_widget.set_playback_position(current_pos)

        if current_pos >= self.spectrogram_widget.viewport_start + self.spectrogram_widget.viewport_duration:
            self.stop_audio()

    def update_threshold(self, value):
        self.threshold_label.setText(f"{value/100:.2f}")

    def start_search(self):
        pattern = self.spectrogram_widget.get_selected_pattern()

        if pattern is None:
            self.search_status.setText("Please select a pattern first!")
            return

        if len(self.file_list) == 0:
            self.search_status.setText("Please load a folder first!")
            return

        threshold = self.threshold_slider.value() / 100

        self.results_list.clear()
        self.search_btn.setEnabled(False)
        self.stop_search_btn.setEnabled(True)
        self.search_progress.setValue(0)

        self.search_thread = PatternSearchThread(pattern, self.audio_data['audio'], self.file_list, threshold)
        self.search_thread.progress.connect(self.update_search_progress)
        self.search_thread.match_found.connect(self.add_search_result)
        self.search_thread.finished.connect(self.search_complete)
        self.search_thread.start()

    def stop_search(self):
        if self.search_thread:
            self.search_thread.stop()
            self.search_thread.wait()
            self.search_complete()

    def update_search_progress(self, value, status):
        self.search_progress.setValue(value)
        self.search_status.setText(status)

    def add_search_result(self, match_info):
        metadata = match_info['metadata']
        result_text = (f"{match_info['filename']} | "
                      f"{metadata['date']} {metadata['time']} | "
                      f"Time: {match_info['time_start']:.2f}s | "
                      f"Similarity: {match_info['similarity']:.3f}")

        self.results_list.addItem(result_text)

    def search_complete(self):
        self.search_btn.setEnabled(True)
        self.stop_search_btn.setEnabled(False)
        self.search_status.setText(f"Search complete! Found {self.results_list.count()} matches.")

    def open_result(self, item):
        filename = item.text().split(' | ')[0]
        file_path = next((f for f in self.file_list if os.path.basename(f) == filename), None)

        if file_path:
            self.current_file = file_path
            self.file_label.setText(f"Opened: {filename}")
            self.compute_spectrogram()

    def export_results(self):
        if self.results_list.count() == 0:
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export Results", "", "CSV Files (*.csv)")

        if file_path:
            with open(file_path, 'w') as f:
                f.write("Filename,Date,Time,TimeStart,Similarity\n")
                for i in range(self.results_list.count()):
                    f.write(self.results_list.item(i).text().replace(' | ', ',') + '\n')

            self.search_status.setText(f"Results exported to {file_path}")
