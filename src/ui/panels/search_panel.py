"""
Pattern Search Panel
Handles pattern matching across multiple files
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QSlider, 
    QGroupBox, QProgressBar, QListWidget, QFileDialog
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
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Pattern Search")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Settings group
        settings_group = QGroupBox("Search Settings")
        settings_layout = QVBoxLayout()
        
        threshold_label = QLabel("Similarity Threshold:")
        threshold_label.setStyleSheet("font-weight: bold;")
        settings_layout.addWidget(threshold_label)
        
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(50)
        self.threshold_slider.setMaximum(99)
        self.threshold_slider.setValue(70)
        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)
        settings_layout.addWidget(self.threshold_slider)
        
        self.threshold_label = QLabel("0.70")
        self.threshold_label.setStyleSheet("color: #666; font-size: 12px;")
        settings_layout.addWidget(self.threshold_label)
        
        threshold_info = QLabel(
            "💡 Higher threshold = more strict matching<br>"
            "Lower threshold = more results, less precise"
        )
        threshold_info.setWordWrap(True)
        threshold_info.setStyleSheet("margin-top: 5px; padding: 6px; background-color: #e3f2fd; border-radius: 4px; font-size: 11px;")
        settings_layout.addWidget(threshold_info)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Search controls group
        controls_group = QGroupBox("Search Controls")
        controls_layout = QVBoxLayout()
        
        self.search_btn = QPushButton("🔍 Search in Files")
        self.search_btn.setEnabled(False)
        self.search_btn.setMinimumHeight(45)
        self.search_btn.clicked.connect(self.on_start_search)
        self.search_btn.setStyleSheet("""
            QPushButton:enabled {
                background-color: #FF9800;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        controls_layout.addWidget(self.search_btn)
        
        self.stop_btn = QPushButton("⏹ Stop Search")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.clicked.connect(self.on_stop_search)
        controls_layout.addWidget(self.stop_btn)
        
        self.progress_bar = QProgressBar()
        controls_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Load a folder and extract a pattern first")
        self.status_label.setStyleSheet(
            "padding: 8px; background-color: #f9f9f9; border-radius: 4px;"
        )
        self.status_label.setWordWrap(True)
        controls_layout.addWidget(self.status_label)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Results group
        results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout()
        
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.on_result_double_clicked)
        results_layout.addWidget(self.results_list)
        
        export_btn = QPushButton("📊 Export Results to CSV")
        export_btn.setMinimumHeight(35)
        export_btn.clicked.connect(self.on_export_results)
        results_layout.addWidget(export_btn)
        
        self.results_count_label = QLabel("No results yet")
        self.results_count_label.setStyleSheet("padding: 6px; background-color: #f9f9f9; border-radius: 4px;")
        results_layout.addWidget(self.results_count_label)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
        
    def on_threshold_changed(self, value):
        """Handle threshold slider change"""
        self.threshold_label.setText(f"{value/100:.2f}")
        
    def set_file_list(self, file_list):
        """Set the list of files to search in"""
        self.file_list = file_list
        self.update_search_button_state()
        self.status_label.setText(f"Ready to search in {len(file_list)} files")
        
    def set_audio_data(self, audio_data):
        """Set the audio data (needed for pattern extraction)"""
        self.audio_data = audio_data
        self.update_search_button_state()
        
    def update_search_button_state(self):
        """Enable search button if we have files and pattern"""
        has_files = len(self.file_list) > 0
        has_audio = self.audio_data is not None
        self.search_btn.setEnabled(has_files and has_audio)
        
    def on_start_search(self):
        """Start the pattern search"""
        # This will be connected to main window to get pattern
        # For now, just emit a signal
        pass
        
    def start_search_with_pattern(self, pattern, audio):
        """Actually start the search with pattern"""
        if not pattern or len(self.file_list) == 0:
            self.status_label.setText("⚠️ Missing pattern or file list")
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
        self.status_label.setText(status)
        
    def on_match_found(self, match_info):
        """Add a search result"""
        metadata = match_info['metadata']
        result_text = (
            f"{match_info['filename']} | "
            f"{metadata['date']} {metadata['time']} | "
            f"Time: {match_info['time_start']:.2f}s | "
            f"Similarity: {match_info['similarity']:.3f}"
        )
        self.results_list.addItem(result_text)
        self.results_count_label.setText(f"Found {self.results_list.count()} matches")
        
    def on_search_finished(self):
        """Handle search completion"""
        self.search_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        count = self.results_list.count()
        self.status_label.setText(f"✅ Search complete! Found {count} matches")
        self.results_count_label.setText(f"Total: {count} matches")
        
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
            self.status_label.setText("⚠️ No results to export")
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
                        
                self.status_label.setText(f"✅ Exported to {os.path.basename(file_path)}")
            except Exception as e:
                self.status_label.setText(f"❌ Export error: {e}")