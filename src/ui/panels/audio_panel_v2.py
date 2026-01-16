"""
Audio Panel V2 - Professional blue styling
Clean audio playback controls
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox, QHBoxLayout, QSlider
)
from PyQt6.QtCore import pyqtSignal, Qt

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
    QSlider::handle:horizontal:hover {
        background: #2980B9;
    }
    QSlider::sub-page:horizontal {
        background: #3498DB;
        border-radius: 3px;
    }
"""


class AudioPanel(QWidget):
    """Audio playback panel - Professional blue styling"""
    play_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    volume_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.is_playing = False
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(PANEL_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("Audio")
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
        
        # Playback Controls
        controls_group = QGroupBox("Playback")
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(10)
        
        # Transport buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        
        self.play_btn = QPushButton("Play")
        self.play_btn.setFixedSize(60, 32)
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.on_play)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #229954; }
            QPushButton:disabled { background-color: #BDC3C7; }
        """)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setFixedSize(60, 32)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.on_pause)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #F39C12;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #D68910; }
            QPushButton:disabled { background-color: #BDC3C7; }
        """)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFixedSize(60, 32)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.on_stop)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #C0392B; }
            QPushButton:disabled { background-color: #BDC3C7; }
        """)
        
        btn_row.addStretch()
        btn_row.addWidget(self.play_btn)
        btn_row.addWidget(self.pause_btn)
        btn_row.addWidget(self.stop_btn)
        btn_row.addStretch()
        controls_layout.addLayout(btn_row)
        
        # Volume slider
        vol_row = QHBoxLayout()
        vol_label = QLabel("Vol")
        vol_label.setStyleSheet("font-size: 11px; color: #7F8C8D;")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        vol_max = QLabel("Max")
        vol_max.setStyleSheet("font-size: 11px; color: #7F8C8D;")
        
        vol_row.addWidget(vol_label)
        vol_row.addWidget(self.volume_slider)
        vol_row.addWidget(vol_max)
        controls_layout.addLayout(vol_row)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Status
        self.status_label = QLabel("No audio loaded")
        self.status_label.setStyleSheet("font-size: 11px; color: #7F8C8D;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Time display
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("""
            font-size: 13px; 
            font-weight: 500;
            color: #2C3E50;
            font-family: 'Consolas', monospace;
        """)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)
        
        layout.addStretch()
        
    def on_play(self):
        self.is_playing = True
        self.update_button_states()
        self.play_requested.emit()
        
    def on_pause(self):
        self.is_playing = False
        self.update_button_states()
        self.pause_requested.emit()
        
    def on_stop(self):
        self.is_playing = False
        self.update_button_states()
        self.stop_requested.emit()
        
    def on_volume_changed(self, value):
        self.volume_changed.emit(value)
        
    def update_button_states(self):
        self.play_btn.setEnabled(not self.is_playing)
        self.pause_btn.setEnabled(self.is_playing)
        self.stop_btn.setEnabled(self.is_playing)
        
    def set_audio_loaded(self, loaded, filename=None):
        """Called when audio is loaded"""
        self.play_btn.setEnabled(loaded)
        if loaded and filename:
            self.status_label.setText(f"{filename[:25]}...")
            self.status_label.setStyleSheet("font-size: 11px; color: #27AE60;")
        else:
            self.status_label.setText("No audio loaded")
            self.status_label.setStyleSheet("font-size: 11px; color: #7F8C8D;")
            
    def update_time(self, current_sec, total_sec):
        """Update time display"""
        curr_min = int(current_sec // 60)
        curr_sec = int(current_sec % 60)
        tot_min = int(total_sec // 60)
        tot_sec = int(total_sec % 60)
        self.time_label.setText(f"{curr_min:02d}:{curr_sec:02d} / {tot_min:02d}:{tot_sec:02d}")

    def enable_controls(self, enabled):
        """Enable/disable playback controls"""
        self.play_btn.setEnabled(enabled)
        if enabled:
            self.status_label.setText("Audio ready")
            self.status_label.setStyleSheet("font-size: 11px; color: #27AE60;")
        else:
            self.status_label.setText("No audio loaded")
            self.status_label.setStyleSheet("font-size: 11px; color: #7F8C8D;")

    def set_playing_state(self):
        """Set UI to playing state"""
        self.is_playing = True
        self.update_button_states()
        self.status_label.setText("Playing...")
        self.status_label.setStyleSheet("font-size: 11px; color: #3498DB;")

    def set_paused_state(self):
        """Set UI to paused state"""
        self.is_playing = False
        self.update_button_states()
        self.status_label.setText("Paused")
        self.status_label.setStyleSheet("font-size: 11px; color: #F39C12;")

    def set_stopped_state(self):
        """Set UI to stopped state"""
        self.is_playing = False
        self.update_button_states()
        self.status_label.setText("Stopped")
        self.status_label.setStyleSheet("font-size: 11px; color: #7F8C8D;")
