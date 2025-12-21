"""
Pattern Search Panel - With Scrollbar
Handles pattern matching across multiple files
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QSlider, 
    QGroupBox, QProgressBar, QListWidget, QFileDialog, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt

from ui.workers.pattern_search_w import PatternSearchThread


class SearchPanel(QWidget):
    result_opened = pyqtSignal(str)  # file_path
    
    def __init__(self):
        super().__init__()
        self.search_thread = None
        self.file_list = []
        self.audio_data = None
        self.period_dict = {}  # <-- ADD THIS LINE
        self.init_ui()
        
    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Title
        title = QLabel("Pattern Search")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Settings group
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()
        
        threshold_label = QLabel("Similarity:")
        threshold_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        settings_layout.addWidget(threshold_label)
        
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(50)
        self.threshold_slider.setMaximum(99)
        self.threshold_slider.setValue(70)
        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)
        settings_layout.addWidget(self.threshold_slider)
        
        self.threshold_label = QLabel("0.70")
        self.threshold_label.setStyleSheet("color: #666; font-size: 10px;")
        settings_layout.addWidget(self.threshold_label)
        
        threshold_info = QLabel("💡 Higher = stricter match")
        threshold_info.setWordWrap(True)
        threshold_info.setStyleSheet(
            "margin-top: 3px; padding: 4px; background-color: #e3f2fd; "
            "border-radius: 4px; font-size: 10px;"
        )
        settings_layout.addWidget(threshold_info)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Search controls group
        controls_group = QGroupBox("Controls")
        controls_layout = QVBoxLayout()
        
        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.setEnabled(False)
        self.search_btn.setMinimumHeight(40)
        self.search_btn.clicked.connect(self.on_start_search)
        self.search_btn.setStyleSheet("""
            QPushButton:enabled {
                background-color: #FF9800;
                color: white;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        controls_layout.addWidget(self.search_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(32)
        self.stop_btn.clicked.connect(self.on_stop_search)
        controls_layout.addWidget(self.stop_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(20)
        controls_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Load folder & extract pattern")
        self.status_label.setStyleSheet(
            "padding: 6px; background-color: #f9f9f9; "
            "border-radius: 4px; font-size: 10px;"
        )
        self.status_label.setWordWrap(True)
        controls_layout.addWidget(self.status_label)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Results group
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("font-size: 10px;")
        self.results_list.itemDoubleClicked.connect(self.on_result_double_clicked)
        results_layout.addWidget(self.results_list)
        
        export_btn = QPushButton("📊 Export CSV")
        export_btn.setMinimumHeight(30)
        export_btn.clicked.connect(self.on_export_results)
        results_layout.addWidget(export_btn)
        
        self.results_count_label = QLabel("No results")
        self.results_count_label.setStyleSheet(
            "padding: 4px; background-color: #f9f9f9; "
            "border-radius: 4px; font-size: 10px;"
        )
        results_layout.addWidget(self.results_count_label)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
    def on_threshold_changed(self, value):
        """Handle threshold slider change"""
        self.threshold_label.setText(f"{value/100:.2f}")
        
    def set_file_list(self, file_list):
        """Set the list of files to search in"""
        self.file_list = file_list
        self.update_search_button_state()
        self.status_label.setText(f"Ready: {len(file_list)} files")
        
    def set_audio_data(self, audio_data):
        """Set the audio data (needed for pattern extraction)"""
        self.audio_data = audio_data
        self.update_search_button_state()

    def set_period_dict(self, period_dict):
        """Set period dictionary used for accelerated searching."""
        try:
            self.period_dict = period_dict or {}
            self.status_label.setText(f"Loaded period dict: {len(self.period_dict)} entries")
            self.update_search_button_state()
        except Exception:
            # Keep minimal behavior on failure
            self.period_dict = {}
        
    def update_search_button_state(self):
        """Enable search button if we have files and pattern"""
        has_files = len(self.file_list) > 0
        has_audio = self.audio_data is not None
        self.search_btn.setEnabled(has_files and has_audio)
        
    def on_start_search(self):
        """Start the pattern search"""
        pass
        
    def start_search_with_pattern(self, pattern, audio):
        """Actually start the search with pattern"""
        if not pattern or len(self.file_list) == 0:
            self.status_label.setText("⚠️ Missing data")
            return
            
        threshold = self.threshold_slider.value() / 100
        
        self.results_list.clear()
        self.search_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("🔍 Searching...")
        
        self.search_thread = PatternSearchThread(
            pattern, audio, self.file_list, threshold
        )
        self.search_thread.progress.connect(self.on_progress)
        self.search_thread.match_found.connect(self.on_match_found)
        self.search_thread.finished.connect(self.on_search_finished)
        self.search_thread.start()
        
    def on_stop_search(self):
        """Stop the current search"""
        if self.search_thread:
            self.search_thread.stop()
            self.search_thread.wait()
            self.on_search_finished()
            
    def on_progress(self, value, status):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        short_status = status[:50] + "..." if len(status) > 50 else status
        self.status_label.setText(short_status)
        
    def on_match_found(self, match_info):
        """Add a search result"""
        metadata = match_info['metadata']
        result_text = (
            f"{match_info['filename']} | "
            f"{metadata['date']} {metadata['time']} | "
            f"T: {match_info['time_start']:.1f}s | "
            f"S: {match_info['similarity']:.3f}"
        )
        self.results_list.addItem(result_text)
        self.results_count_label.setText(f"Found: {self.results_list.count()}")
        
    def on_search_finished(self):
        """Handle search completion"""
        self.search_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        count = self.results_list.count()
        self.status_label.setText(f"✅ Complete! {count} matches")
        self.results_count_label.setText(f"Total: {count}")
        
    def on_result_double_clicked(self, item):
        """Handle double-click on result"""
        filename = item.text().split(' | ')[0]
        file_path = next(
            (f for f in self.file_list if os.path.basename(f) == filename), 
            None
        )
        if file_path:
            self.result_opened.emit(file_path)
            
    def on_export_results(self):
        """Export results to CSV"""
        if self.results_list.count() == 0:
            self.status_label.setText("⚠️ No results")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write("Filename,Date,Time,TimeStart,Similarity\n")
                    for i in range(self.results_list.count()):
                        text = self.results_list.item(i).text()
                        f.write(text.replace(' | ', ',') + '\n')
                        
                self.status_label.setText(f"✅ Exported")
            except Exception as e:
                self.status_label.setText(f"❌ Error")