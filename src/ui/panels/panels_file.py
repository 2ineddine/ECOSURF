"""
File Management Panel - With Scrollbar
Handles file loading, folder selection, and file information display
"""
import os
import re
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, 
    QGroupBox, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt
import soundfile as sf

from ui.dialogs.period_selection import PeriodSelectionDialog


class FilePanel(QWidget):
    file_loaded = pyqtSignal(str, tuple)  # file_path, time_range
    folder_loaded = pyqtSignal(list)  # list of file paths
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.file_list = []
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
        title = QLabel("File Management")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # File operations group
        file_group = QGroupBox("File Operations")
        file_layout = QVBoxLayout()
        
        load_btn = QPushButton("📂 Load Audio File")
        load_btn.clicked.connect(self.load_file)
        load_btn.setMinimumHeight(35)
        file_layout.addWidget(load_btn)
        
        load_folder_btn = QPushButton("📁 Load Folder")
        load_folder_btn.clicked.connect(self.load_folder)
        load_folder_btn.setMinimumHeight(35)
        file_layout.addWidget(load_folder_btn)
        
        reset_btn = QPushButton("🔄 Reset")
        reset_btn.clicked.connect(self.reset_application)
        reset_btn.setMinimumHeight(35)
        file_layout.addWidget(reset_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # File info group
        info_group = QGroupBox("Current File")
        info_layout = QVBoxLayout()
        
        self.file_label = QLabel("No file loaded")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet(
            "padding: 8px; background-color: #f9f9f9; "
            "border-radius: 5px; font-size: 11px;"
        )
        info_layout.addWidget(self.file_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Folder info group
        folder_group = QGroupBox("Folder")
        folder_layout = QVBoxLayout()
        
        self.folder_label = QLabel("No folder loaded")
        self.folder_label.setWordWrap(True)
        self.folder_label.setStyleSheet(
            "padding: 8px; background-color: #f9f9f9; "
            "border-radius: 5px; font-size: 11px;"
        )
        folder_layout.addWidget(self.folder_label)
        
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
    def parse_filename(self, filename):
        """Parse device ID and timestamp from filename"""
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
        """Load a single audio file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open Audio File", 
            "", 
            "Audio Files (*.flac *.wav *.mp3)"
        )
        
        if file_path:
            self.current_file = file_path
            metadata = self.parse_filename(os.path.basename(file_path))
            
            try:
                info = sf.info(file_path)
                duration = info.duration
                
                dialog = PeriodSelectionDialog(metadata, duration, self)
                if dialog.exec():
                    time_range = dialog.get_time_range()
                    
                    range_text = f"{time_range[0]:.1f}s - {time_range[1]:.1f}s"
                    self.file_label.setText(
                        f"<b>File:</b> {os.path.basename(file_path)}<br>"
                        f"<b>Date:</b> {metadata['date']}<br>"
                        f"<b>Time:</b> {metadata['time']}<br>"
                        f"<b>Duration:</b> {duration:.2f}s<br>"
                        f"<b>Range:</b> {range_text}<br>"
                        f"<b>SR:</b> {info.samplerate} Hz<br>"
                        f"<b>Channels:</b> {info.channels}"
                    )
                    
                    # Emit signal
                    self.file_loaded.emit(file_path, time_range)
            except Exception as e:
                self.file_label.setText(f"<span style='color: red;'>Error: {e}</span>")
                
    def load_folder(self):
        """Load all audio files from a folder"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        
        if folder_path:
            self.file_list = [
                os.path.join(folder_path, f) 
                for f in os.listdir(folder_path) 
                if f.endswith(('.flac', '.wav', '.mp3'))
            ]
            
            self.folder_label.setText(
                f"<b>Folder:</b> {os.path.basename(folder_path)}<br>"
                f"<b>Files:</b> {len(self.file_list)}<br>"
                f"<b>Path:</b> ...{folder_path[-40:]}"
            )
            
            # Emit signal
            self.folder_loaded.emit(self.file_list)
            
    def reset_application(self):
        """Reset all file information"""
        self.current_file = None
        self.file_list = []
        self.file_label.setText("No file loaded")
        self.folder_label.setText("No folder loaded")
        
    def update_file_info(self, additional_info):
        """Update file label with additional information"""
        current_text = self.file_label.text()
        self.file_label.setText(f"{current_text}<br>{additional_info}")