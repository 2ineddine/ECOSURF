"""
File Panel V2 - Professional compact design
Clean buttons and professional date picker
"""
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QComboBox, QDateTimeEdit, QSpinBox, QCalendarWidget,
    QGridLayout, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt, QDateTime, QDate
from PyQt6.QtGui import QFont, QIcon
import soundfile as sf
import numpy as np


PANEL_STYLE = """
QWidget {
    font-family: 'Segoe UI', sans-serif;
    font-size: 12px;
    color: #2C3E50;
    background: white;
}

/* Section Headers */
QLabel#header {
    font-size: 13px;
    font-weight: 600;
    color: #2C3E50;
    padding: 8px 0;
    border-bottom: 2px solid #3498DB;
    margin-bottom: 8px;
}

/* Compact Toggle Buttons */
QPushButton#toggle_btn {
    background: #F8F9FA;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 10px 16px;
    font-size: 11px;
    font-weight: 500;
    color: #5D6D7E;
    min-height: 36px;
}
QPushButton#toggle_btn:hover {
    background: #EBF5FB;
    border-color: #3498DB;
    color: #3498DB;
}
QPushButton#toggle_btn:checked, QPushButton#toggle_btn[selected="true"] {
    background: #3498DB;
    color: white;
    border-color: #2980B9;
}

/* Primary Action Buttons */
QPushButton#primary_btn {
    background: #3498DB;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 12px;
    font-weight: 600;
    min-height: 38px;
}
QPushButton#primary_btn:hover {
    background: #2980B9;
}
QPushButton#primary_btn:pressed {
    background: #1F6DA8;
}
QPushButton#primary_btn:disabled {
    background: #BDC3C7;
}

/* Secondary Buttons */
QPushButton#secondary_btn {
    background: #F8F9FA;
    color: #2C3E50;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 11px;
    font-weight: 500;
}
QPushButton#secondary_btn:hover {
    background: #EBF5FB;
    border-color: #3498DB;
}

/* Cards */
QFrame#card {
    background: #FAFBFC;
    border: 1px solid #E8E8E8;
    border-radius: 8px;
    padding: 12px;
}

/* Inputs */
QComboBox {
    background: white;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 34px;
    font-size: 12px;
}
QComboBox:hover, QComboBox:focus {
    border-color: #3498DB;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #7F8C8D;
    margin-right: 8px;
}

QDateTimeEdit {
    background: white;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 34px;
    font-size: 12px;
}
QDateTimeEdit:hover, QDateTimeEdit:focus {
    border-color: #3498DB;
}
QDateTimeEdit::drop-down {
    border: none;
    width: 24px;
}

QSpinBox {
    background: white;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    padding: 6px 10px;
    min-height: 34px;
    font-size: 12px;
}
QSpinBox:hover, QSpinBox:focus {
    border-color: #3498DB;
}

/* Status Labels */
QLabel#status {
    font-size: 11px;
    color: #7F8C8D;
    padding: 4px 0;
}
QLabel#status_success {
    font-size: 11px;
    color: #27AE60;
    padding: 4px 0;
}
QLabel#status_error {
    font-size: 11px;
    color: #E74C3C;
    padding: 4px 0;
}

/* Info Card */
QFrame#info_card {
    background: #EBF5FB;
    border: 1px solid #AED6F1;
    border-radius: 6px;
    padding: 10px;
}

QLabel#info_text {
    font-size: 11px;
    color: #2471A3;
    line-height: 1.4;
}

/* Calendar Popup Styling */
QCalendarWidget {
    background: white;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
}
QCalendarWidget QToolButton {
    color: #2C3E50;
    background: transparent;
    border: none;
    border-radius: 4px;
    padding: 6px;
    font-weight: 500;
}
QCalendarWidget QToolButton:hover {
    background: #EBF5FB;
}
QCalendarWidget QTableView {
    selection-background-color: #3498DB;
    selection-color: white;
}
"""


class FilePanel(QWidget):
    """File panel with compact professional buttons"""
    folder_loaded = pyqtSignal(list)
    file_loaded = pyqtSignal(object, tuple, str)
    period_dict_loaded = pyqtSignal(dict)
    search_scope_changed = pyqtSignal(str, list)

    def __init__(self):
        super().__init__()
        self.current_source = None
        self.period_dict = {}
        self.file_list = []
        self.current_file = None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(PANEL_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("Data Source")
        header.setObjectName("header")
        layout.addWidget(header)

        # Source Selection - Compact Buttons
        source_frame = QFrame()
        source_frame.setObjectName("card")
        source_layout = QVBoxLayout(source_frame)
        source_layout.setSpacing(10)
        source_layout.setContentsMargins(10, 10, 10, 10)

        # Button Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.s3_btn = QPushButton("S3 Cloud")
        self.s3_btn.setObjectName("toggle_btn")
        self.s3_btn.setCheckable(True)
        self.s3_btn.clicked.connect(lambda: self.select_source('s3'))
        btn_row.addWidget(self.s3_btn)

        self.local_btn = QPushButton("Local")
        self.local_btn.setObjectName("toggle_btn")
        self.local_btn.setCheckable(True)
        self.local_btn.clicked.connect(lambda: self.select_source('local'))
        btn_row.addWidget(self.local_btn)

        source_layout.addLayout(btn_row)

        # Status
        self.source_status = QLabel("Select a data source")
        self.source_status.setObjectName("status")
        source_layout.addWidget(self.source_status)

        layout.addWidget(source_frame)

        # ===== S3 Configuration Card =====
        self.s3_card = QFrame()
        self.s3_card.setObjectName("card")
        self.s3_card.setVisible(False)
        s3_layout = QVBoxLayout(self.s3_card)
        s3_layout.setSpacing(12)
        s3_layout.setContentsMargins(10, 10, 10, 10)

        # Site Selection
        site_row = QHBoxLayout()
        site_label = QLabel("Site:")
        site_label.setStyleSheet("font-weight: 500; color: #5D6D7E;")
        self.site_combo = QComboBox()
        self.site_combo.addItems(["S4A09154", "S4A09155", "S4A09156", "S4A09157"])
        self.site_combo.setMinimumWidth(130)
        site_row.addWidget(site_label)
        site_row.addWidget(self.site_combo)
        site_row.addStretch()
        s3_layout.addLayout(site_row)

        # Date & Time Selection
        dt_label = QLabel("Date & Time")
        dt_label.setStyleSheet("font-weight: 600; color: #2C3E50; margin-top: 4px;")
        s3_layout.addWidget(dt_label)

        # DateTime picker with calendar
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDisplayFormat("dd MMM yyyy  HH:mm")
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDateTime(QDateTime(2019, 2, 18, 16, 30))
        self.datetime_edit.setMinimumWidth(180)

        # Style the calendar popup
        calendar = self.datetime_edit.calendarWidget()
        if calendar:
            calendar.setGridVisible(True)
            calendar.setStyleSheet("""
                QCalendarWidget QToolButton {
                    color: #2C3E50;
                    font-weight: 500;
                }
                QCalendarWidget QTableView {
                    selection-background-color: #3498DB;
                }
            """)

        s3_layout.addWidget(self.datetime_edit)

        # Duration
        dur_row = QHBoxLayout()
        dur_label = QLabel("Duration:")
        dur_label.setStyleSheet("font-weight: 500; color: #5D6D7E;")
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 60)
        self.duration_spin.setValue(5)
        self.duration_spin.setSuffix(" min")
        self.duration_spin.setFixedWidth(90)
        dur_row.addWidget(dur_label)
        dur_row.addWidget(self.duration_spin)
        dur_row.addStretch()
        s3_layout.addLayout(dur_row)

        # Load Button
        self.load_s3_btn = QPushButton("Load Audio")
        self.load_s3_btn.setObjectName("primary_btn")
        self.load_s3_btn.clicked.connect(self.load_from_s3)
        s3_layout.addWidget(self.load_s3_btn)

        layout.addWidget(self.s3_card)

        # ===== Local File Card =====
        self.local_card = QFrame()
        self.local_card.setObjectName("card")
        self.local_card.setVisible(False)
        local_layout = QVBoxLayout(self.local_card)
        local_layout.setSpacing(10)
        local_layout.setContentsMargins(10, 10, 10, 10)

        # Browse Button
        self.browse_btn = QPushButton("Browse File...")
        self.browse_btn.setObjectName("primary_btn")
        self.browse_btn.clicked.connect(self.browse_local)
        local_layout.addWidget(self.browse_btn)

        # File name label
        self.file_label = QLabel("No file selected")
        self.file_label.setObjectName("status")
        self.file_label.setWordWrap(True)
        local_layout.addWidget(self.file_label)

        layout.addWidget(self.local_card)

        # ===== File Info Card =====
        self.info_card = QFrame()
        self.info_card.setObjectName("info_card")
        self.info_card.setVisible(False)
        info_layout = QVBoxLayout(self.info_card)
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(10, 10, 10, 10)

        self.info_label = QLabel("")
        self.info_label.setObjectName("info_text")
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)

        layout.addWidget(self.info_card)

        layout.addStretch()

    def select_source(self, source):
        """Handle source selection"""
        self.current_source = source
        self.s3_btn.setChecked(source == 's3')
        self.local_btn.setChecked(source == 'local')

        self.s3_card.setVisible(source == 's3')
        self.local_card.setVisible(source == 'local')

        if source == 's3':
            self.source_status.setText("Connected to Wasabi S3")
            self.source_status.setObjectName("status_success")
            self.source_status.setStyleSheet("font-size: 11px; color: #27AE60;")
            self.load_period_dict()
        else:
            self.source_status.setText("Local file mode")
            self.source_status.setObjectName("status")
            self.source_status.setStyleSheet("font-size: 11px; color: #7F8C8D;")

    def load_period_dict(self):
        """Load available periods from JSON"""
        paths = [
            'pre_processing_data/period_locations.json',
            'period_locations.json'
        ]
        for p in paths:
            if os.path.exists(p):
                try:
                    with open(p, 'r') as f:
                        self.period_dict = json.load(f)
                    self.period_dict_loaded.emit(self.period_dict)
                    # Keep default site values - don't extract from period_dict
                    # as keys are date_time format, not site_date_time
                    return
                except:
                    pass

    def load_from_s3(self):
        """Load audio from S3 based on selections"""
        dt = self.datetime_edit.dateTime()
        site = self.site_combo.currentText()
        duration = self.duration_spin.value()

        date_str = dt.toString("yyyyMMdd")

        files = []
        for i in range(duration):
            minute_dt = dt.addSecs(i * 60)
            t_str = minute_dt.toString("HHmmss")
            filename = f"{site}_{date_str}_{t_str}.flac"
            files.append(filename)

        time_range = (0, duration * 60)

        if len(files) == 1:
            self.file_loaded.emit(files[0], time_range, 'database')
        else:
            self.file_loaded.emit(files, time_range, 'database')

        # Show info
        self.info_card.setVisible(True)
        self.info_label.setText(
            f"Site: {site}\n"
            f"Date: {dt.toString('dd MMM yyyy HH:mm')}\n"
            f"Duration: {duration} min"
        )

    def browse_local(self):
        """Open file browser for local files"""
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "",
            "Audio Files (*.flac *.wav *.mp3);;All Files (*)"
        )
        if path:
            self.current_file = path
            self.file_label.setText(os.path.basename(path))

            try:
                info = sf.info(path)
                duration = info.duration
                sr = info.samplerate

                self.info_card.setVisible(True)
                self.info_label.setText(
                    f"File: {os.path.basename(path)[:30]}\n"
                    f"Duration: {duration:.1f}s\n"
                    f"Sample rate: {sr:,} Hz"
                )
                self.file_loaded.emit(path, (0, duration), 'local')
            except Exception as e:
                self.info_label.setText(f"Error: {str(e)[:50]}")

    def update_file_info(self, text):
        """Update file info display"""
        self.info_card.setVisible(True)
        self.info_label.setText(text)
