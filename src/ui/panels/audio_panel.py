"""
Audio Playback Panel
Handles audio playback controls
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox
)
from PyQt6.QtCore import pyqtSignal


class AudioPanel(QWidget):
    play_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Audio Playback")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Main playback group
        playback_group = QGroupBox("Main Audio Controls")
        playback_layout = QVBoxLayout()
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setEnabled(False)
        self.play_btn.setMinimumHeight(45)
        self.play_btn.clicked.connect(self.on_play)
        self.play_btn.setStyleSheet("""
            QPushButton:enabled {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        playback_layout.addWidget(self.play_btn)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.setMinimumHeight(40)
        self.pause_btn.clicked.connect(self.on_pause)
        playback_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.clicked.connect(self.on_stop)
        playback_layout.addWidget(self.stop_btn)
        
        self.status_label = QLabel("⏹ Stopped")
        self.status_label.setStyleSheet(
            "padding: 10px; background-color: #f9f9f9; "
            "border-radius: 5px; font-size: 13px; font-weight: bold;"
        )
        playback_layout.addWidget(self.status_label)
        
        playback_group.setLayout(playback_layout)
        layout.addWidget(playback_group)
        
        # Info group
        info_group = QGroupBox("Playback Information")
        info_layout = QVBoxLayout()
        
        info_text = QLabel(
            "💡 <b>Playback Tips:</b><br>"
            "• Press <b>Space</b> to play/pause<br>"
            "• Playback follows viewport<br>"
            "• Viewport scrollbar disabled during playback<br>"
            "• Use Stop to reset position"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("padding: 8px; background-color: #e3f2fd; border-radius: 4px;")
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        
    def on_play(self):
        """Handle play button click"""
        self.play_requested.emit()
        
    def on_pause(self):
        """Handle pause button click"""
        self.pause_requested.emit()
        
    def on_stop(self):
        """Handle stop button click"""
        self.stop_requested.emit()
        
    def enable_controls(self, enable=True):
        """Enable or disable playback controls"""
        self.play_btn.setEnabled(enable)
        
    def set_playing_state(self):
        """Set UI to playing state"""
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("▶ Playing...")
        self.status_label.setStyleSheet(
            "padding: 10px; background-color: #c8e6c9; "
            "border-radius: 5px; font-size: 13px; font-weight: bold;"
        )
        
    def set_paused_state(self):
        """Set UI to paused state"""
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("⏸ Paused")
        self.status_label.setStyleSheet(
            "padding: 10px; background-color: #fff9c4; "
            "border-radius: 5px; font-size: 13px; font-weight: bold;"
        )
        
    def set_stopped_state(self):
        """Set UI to stopped state"""
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("⏹ Stopped")
        self.status_label.setStyleSheet(
            "padding: 10px; background-color: #f9f9f9; "
            "border-radius: 5px; font-size: 13px; font-weight: bold;"
        )