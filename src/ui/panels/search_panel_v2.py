"""
Search Panel V2 - Professional blue styling
Clean pattern search interface
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QSlider, 
    QGroupBox, QProgressBar, QListWidget, QHBoxLayout, QListWidgetItem
)
from PyQt6.QtCore import pyqtSignal, Qt

from ui.workers.pattern_search_w import PatternSearchThread

# Style cohérent bleu professionnel
PANEL_STYLE = """
    QWidget {
        background-color: white;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QGroupBox {
        font-weight: 600;
        font-size: 11px;
        color: #2C3E50;
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        margin-top: 12px;
        padding: 12px 8px 8px 8px;
        background-color: #FAFBFC;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 6px;
        background-color: white;
    }
    QPushButton {
        background-color: #3498DB;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #2980B9;
    }
    QPushButton:pressed {
        background-color: #1F6DA8;
    }
    QPushButton:disabled {
        background-color: #BDC3C7;
        color: #7F8C8D;
    }
    QSlider::groove:horizontal {
        border: 1px solid #E0E0E0;
        height: 6px;
        background: #ECEFF1;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: #3498DB;
        border: none;
        width: 14px;
        height: 14px;
        margin: -4px 0;
        border-radius: 7px;
    }
    QSlider::sub-page:horizontal {
        background: #3498DB;
        border-radius: 3px;
    }
    QProgressBar {
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        background-color: #ECEFF1;
        height: 8px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #3498DB;
        border-radius: 3px;
    }
    QListWidget {
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        background-color: white;
        font-size: 11px;
    }
    QListWidget::item {
        padding: 8px;
        border-bottom: 1px solid #F0F0F0;
    }
    QListWidget::item:selected {
        background-color: #3498DB;
        color: white;
    }
    QListWidget::item:hover {
        background-color: #EBF5FB;
    }
"""


class SearchPanel(QWidget):
    """Pattern search panel - Professional blue styling"""
    result_opened = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.search_thread = None
        self.file_list = []
        self.audio_data = None
        self.period_dict = {}
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(PANEL_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("Search")
        header.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #2C3E50;
                padding-bottom: 4px;
                border-bottom: 2px solid #3498DB;
            }
        """)
        layout.addWidget(header)
        
        # Settings
        settings_group = QGroupBox("Threshold")
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(6)
        
        # Threshold slider
        thresh_row = QHBoxLayout()
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(50)
        self.threshold_slider.setMaximum(99)
        self.threshold_slider.setValue(70)
        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)
        
        self.threshold_label = QLabel("0.70")
        self.threshold_label.setStyleSheet("font-size: 12px; font-weight: 500; color: #3498DB;")
        self.threshold_label.setFixedWidth(40)
        
        thresh_row.addWidget(self.threshold_slider)
        thresh_row.addWidget(self.threshold_label)
        settings_layout.addLayout(thresh_row)
        
        thresh_info = QLabel("Higher = stricter matching")
        thresh_info.setStyleSheet("font-size: 10px; color: #7F8C8D;")
        settings_layout.addWidget(thresh_info)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Controls
        controls_row = QHBoxLayout()
        controls_row.setSpacing(8)
        
        self.search_btn = QPushButton("Search")
        self.search_btn.setEnabled(False)
        self.search_btn.clicked.connect(self.start_search)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFixedWidth(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_search)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #C0392B; }
            QPushButton:disabled { background-color: #BDC3C7; }
        """)
        
        controls_row.addWidget(self.search_btn)
        controls_row.addWidget(self.stop_btn)
        layout.addLayout(controls_row)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setTextVisible(False)
        self.progress.setMaximumHeight(6)
        layout.addWidget(self.progress)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-size: 11px; color: #7F8C8D;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Results
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout()
        
        self.results_list = QListWidget()
        self.results_list.setMinimumHeight(150)
        self.results_list.itemDoubleClicked.connect(self.on_result_clicked)
        results_layout.addWidget(self.results_list)
        
        # Result count
        self.count_label = QLabel("0 matches")
        self.count_label.setStyleSheet("font-size: 11px; color: #7F8C8D;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        results_layout.addWidget(self.count_label)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        layout.addStretch()
        
    def on_threshold_changed(self, value):
        self.threshold_label.setText(f"{value/100:.2f}")
        
    def set_audio_data(self, audio_data):
        """Set pattern audio data to search for"""
        self.audio_data = audio_data
        self.update_search_button()
        
    def set_file_list(self, file_list):
        """Set files to search in"""
        self.file_list = file_list
        self.update_search_button()
        
    def set_period_dict(self, period_dict):
        """Set period dict for S3 files"""
        self.period_dict = period_dict
        
    def update_search_button(self):
        enabled = self.audio_data is not None and len(self.file_list) > 0
        self.search_btn.setEnabled(enabled)
        if enabled:
            self.status_label.setText(f"{len(self.file_list)} files ready")
        
    def start_search(self):
        if self.audio_data is None or not self.file_list:
            return
            
        self.results_list.clear()
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.search_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Searching...")
        
        threshold = self.threshold_slider.value() / 100.0
        
        self.search_thread = PatternSearchThread(
            pattern_audio=self.audio_data,
            file_list=self.file_list,
            threshold=threshold,
            period_dict=self.period_dict
        )
        self.search_thread.progress.connect(self.on_progress)
        self.search_thread.result_found.connect(self.on_result_found)
        self.search_thread.finished.connect(self.on_search_finished)
        self.search_thread.start()
        
    def stop_search(self):
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.stop()
            self.status_label.setText("Stopped")
            
    def on_progress(self, value, message):
        self.progress.setValue(value)
        
    def on_result_found(self, result):
        """Add result to list"""
        item = QListWidgetItem()
        filename = os.path.basename(result.get('file', 'Unknown'))
        score = result.get('score', 0)
        time_pos = result.get('time', 0)
        
        item.setText(f"{filename[:20]}... | {score:.2f} | {time_pos:.1f}s")
        item.setData(Qt.ItemDataRole.UserRole, result)
        self.results_list.addItem(item)
        self.count_label.setText(f"{self.results_list.count()} matches")
        
    def on_search_finished(self):
        self.progress.setVisible(False)
        self.search_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        count = self.results_list.count()
        self.status_label.setText(f"Found {count} matches")
        self.status_label.setStyleSheet("font-size: 11px; color: #27AE60;")
        
    def on_result_clicked(self, item):
        """Open result file"""
        result = item.data(Qt.ItemDataRole.UserRole)
        if result:
            file_path = result.get('file', '')
            self.result_opened.emit(file_path)
