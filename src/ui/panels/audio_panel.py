from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt


class AudioPanel(QWidget):
    play_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        
        title = QLabel("Audio Playback")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(title)
        
        playback_group = QGroupBox("Controls")
        playback_layout = QVBoxLayout()
        
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setEnabled(False)
        self.play_btn.setMinimumHeight(42)
        self.play_btn.clicked.connect(self.on_play)
        self.play_btn.setStyleSheet("""
            QPushButton:enabled {
                background-color: #4CAF50;
                color: white;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        playback_layout.addWidget(self.play_btn)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.setMinimumHeight(35)
        self.pause_btn.clicked.connect(self.on_pause)
        playback_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(35)
        self.stop_btn.clicked.connect(self.on_stop)
        playback_layout.addWidget(self.stop_btn)
        
        self.status_label = QLabel("⏹ Stopped")
        self.status_label.setStyleSheet(
            "padding: 8px; background-color: #f9f9f9; "
            "border-radius: 5px; font-size: 12px; font-weight: bold;"
        )
        playback_layout.addWidget(self.status_label)
        
        playback_group.setLayout(playback_layout)
        layout.addWidget(playback_group)
        
        info_group = QGroupBox("💡 Tips")
        info_layout = QVBoxLayout()
        
        info_text = QLabel(
            "• <b>Space</b> to play/pause<br>"
            "• Playback follows viewport<br>"
            "• Scrollbar disabled during play<br>"
            "• Stop resets position"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(
            "padding: 6px; background-color: #e3f2fd; "
            "border-radius: 4px; font-size: 10px;"
        )
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
    def on_play(self):
        self.play_requested.emit()
        
    def on_pause(self):
        self.pause_requested.emit()
        
    def on_stop(self):
        self.stop_requested.emit()
        
    def enable_controls(self, enable=True):
        self.play_btn.setEnabled(enable)
        
    def set_playing_state(self):
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("▶ Playing...")
        self.status_label.setStyleSheet(
            "padding: 8px; background-color: #c8e6c9; "
            "border-radius: 5px; font-size: 12px; font-weight: bold;"
        )
        
    def set_paused_state(self):
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("⏸ Paused")
        self.status_label.setStyleSheet(
            "padding: 8px; background-color: #fff9c4; "
            "border-radius: 5px; font-size: 12px; font-weight: bold;"
        )
        
    def set_stopped_state(self):
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("⏹ Stopped")
        self.status_label.setStyleSheet(
            "padding: 8px; background-color: #f9f9f9; "
            "border-radius: 5px; font-size: 12px; font-weight: bold;"
        )