from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox, QScrollArea
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QFrame


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
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        
        # Ubuntu-style title
        title = QLabel("Audio Playback")
        title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #E95420;
                padding: 8px 0px;
                border-bottom: 2px solid #DEDEDE;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(title)
        
        # Controls group
        playback_group = QGroupBox("Controls")
        playback_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #DEDEDE;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #FAFAFA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0px 5px 0px 5px;
            }
        """)
        playback_layout = QVBoxLayout()
        playback_layout.setContentsMargins(12, 15, 12, 12)
        playback_layout.setSpacing(8)
        
        # Ubuntu-style play button
        self.play_btn = QPushButton("Play")
        self.play_btn.setEnabled(False)
        self.play_btn.setMinimumHeight(36)
        self.play_btn.clicked.connect(self.on_play)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #E95420;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:enabled:hover {
                background-color: #D34615;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #888888;
            }
        """)
        playback_layout.addWidget(self.play_btn)
        
        # Ubuntu-style pause button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.setMinimumHeight(32)
        self.pause_btn.clicked.connect(self.on_pause)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F2;
                color: #333333;
                font-size: 12px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover:enabled {
                background-color: #E5E5E5;
                border: 1px solid #888888;
            }
            QPushButton:disabled {
                background-color: #FAFAFA;
                color: #BBBBBB;
                border: 1px solid #E0E0E0;
            }
        """)
        playback_layout.addWidget(self.pause_btn)
        
        # Ubuntu-style stop button
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMinimumHeight(32)
        self.stop_btn.clicked.connect(self.on_stop)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F2;
                color: #333333;
                font-size: 12px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover:enabled {
                background-color: #E5E5E5;
                border: 1px solid #888888;
            }
            QPushButton:disabled {
                background-color: #FAFAFA;
                color: #BBBBBB;
                border: 1px solid #E0E0E0;
            }
        """)
        playback_layout.addWidget(self.stop_btn)
        
        # Status label
        self.status_label = QLabel("Stopped")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: white;
                border: 1px solid #DEDEDE;
                border-radius: 3px;
                font-size: 11px;
                color: #333333;
                font-weight: bold;
                text-align: center;
            }
        """)
        playback_layout.addWidget(self.status_label)
        
        playback_group.setLayout(playback_layout)
        layout.addWidget(playback_group)
        
        # Tips group
        info_group = QGroupBox("Tips & Shortcuts")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #DEDEDE;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #FAFAFA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0px 5px 0px 5px;
            }
        """)
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(12, 15, 12, 12)
        
        info_text = QLabel(
            "• <b>Space</b> - Play/Pause main audio<br>"
            "• <b>Shift+Space</b> - Play/Pause selection<br>"
            "• Playback follows current viewport<br>"
            "• Scrollbar disabled during playback<br>"
            "• Stop resets to start position"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: white;
                border: 1px solid #DEDEDE;
                border-radius: 3px;
                font-size: 11px;
                color: #5E5E5E;
                line-height: 1.4;
            }
        """)
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
        self.status_label.setText("Playing...")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #EDF7ED;
                border: 1px solid #4CAF50;
                border-radius: 3px;
                font-size: 11px;
                color: #2E7D32;
                font-weight: bold;
                text-align: center;
            }
        """)
        
    def set_paused_state(self):
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Paused")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #FFF8E1;
                border: 1px solid #FFB300;
                border-radius: 3px;
                font-size: 11px;
                color: #F57C00;
                font-weight: bold;
                text-align: center;
            }
        """)
        
    def set_stopped_state(self):
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Stopped")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: white;
                border: 1px solid #DEDEDE;
                border-radius: 3px;
                font-size: 11px;
                color: #333333;
                font-weight: bold;
                text-align: center;
            }
        """)