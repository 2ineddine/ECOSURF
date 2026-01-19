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
    QGridLayout, QSizePolicy, QDialog, QTimeEdit
)
from PyQt6.QtCore import pyqtSignal, Qt, QDateTime, QDate, QTime
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


class CalendarDialog(QDialog):
    """Calendrier propre et bien visible"""
    date_selected = pyqtSignal(QDateTime)

    def __init__(self, parent=None, current_datetime=None):
        super().__init__(parent)
        self.setWindowTitle("Select Date & Time")
        self.setModal(True)
        self.setMinimumSize(350, 420)
        self.setMaximumSize(400, 480)

        # Style global
        self.setStyleSheet("""
            QDialog {
                background: white;
            }
            QLabel {
                color: #2C3E50;
            }
            QPushButton {
                font-size: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Header avec bouton fermer
        header_row = QHBoxLayout()
        header_label = QLabel("Select Date & Time")
        header_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2C3E50;
        """)
        header_row.addWidget(header_label)
        header_row.addStretch()

        close_btn = QPushButton("X")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #E74C3C;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #C0392B;
            }
        """)
        close_btn.clicked.connect(self.reject)
        header_row.addWidget(close_btn)
        layout.addLayout(header_row)

        # Ligne de separation
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background: #3498DB; min-height: 2px; max-height: 2px;")
        layout.addWidget(line)

        # Calendar widget
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
            }
            QCalendarWidget QToolButton {
                color: #2C3E50;
                background: #F8F9FA;
                border: none;
                border-radius: 4px;
                padding: 6px 10px;
                font-weight: 600;
                font-size: 12px;
            }
            QCalendarWidget QToolButton:hover {
                background: #3498DB;
                color: white;
            }
            QCalendarWidget QMenu {
                background: white;
                border: 1px solid #E0E0E0;
            }
            QCalendarWidget QSpinBox {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 4px;
            }
            QCalendarWidget QTableView {
                background: white;
                selection-background-color: #3498DB;
                selection-color: white;
                font-size: 12px;
            }
            QCalendarWidget QTableView::item:hover {
                background: #EBF5FB;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: #F8F9FA;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        if current_datetime:
            self.calendar.setSelectedDate(current_datetime.date())
        # Double-clic pour selection rapide
        self.calendar.activated.connect(self.on_date_activated)
        layout.addWidget(self.calendar)

        # Time selection
        time_frame = QFrame()
        time_frame.setStyleSheet("""
            QFrame {
                background: #F8F9FA;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        time_layout = QHBoxLayout(time_frame)
        time_layout.setContentsMargins(12, 8, 12, 8)

        time_label = QLabel("Time:")
        time_label.setStyleSheet("font-weight: 600; font-size: 13px; color: #2C3E50;")
        time_layout.addWidget(time_label)

        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setFixedWidth(60)
        self.hour_spin.setStyleSheet("""
            QSpinBox {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
                font-weight: 600;
            }
            QSpinBox:focus {
                border-color: #3498DB;
            }
        """)
        time_layout.addWidget(self.hour_spin)

        time_layout.addWidget(QLabel(":"))

        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setFixedWidth(60)
        self.minute_spin.setStyleSheet("""
            QSpinBox {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 6px;
                font-size: 14px;
                font-weight: 600;
            }
            QSpinBox:focus {
                border-color: #3498DB;
            }
        """)
        time_layout.addWidget(self.minute_spin)

        if current_datetime:
            self.hour_spin.setValue(current_datetime.time().hour())
            self.minute_spin.setValue(current_datetime.time().minute())
        else:
            self.hour_spin.setValue(12)
            self.minute_spin.setValue(0)

        time_layout.addStretch()
        layout.addWidget(time_frame)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(40)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: #95A5A6;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
                padding: 0 25px;
            }
            QPushButton:hover {
                background: #7F8C8D;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.select_btn = QPushButton("Select Date")
        self.select_btn.setFixedHeight(40)
        self.select_btn.setStyleSheet("""
            QPushButton {
                background: #27AE60;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
                padding: 0 25px;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        self.select_btn.clicked.connect(self.on_select)
        btn_layout.addWidget(self.select_btn)

        layout.addLayout(btn_layout)

    def on_date_activated(self, date):
        """Double-clic sur une date = selection directe"""
        self.on_select()

    def on_select(self):
        date = self.calendar.selectedDate()
        time = QTime(self.hour_spin.value(), self.minute_spin.value())
        dt = QDateTime(date, time)
        self.date_selected.emit(dt)
        self.accept()

    def get_datetime(self):
        date = self.calendar.selectedDate()
        time = QTime(self.hour_spin.value(), self.minute_spin.value())
        return QDateTime(date, time)


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

        # DateTime picker with calendar button
        dt_row = QHBoxLayout()
        dt_row.setSpacing(6)

        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDisplayFormat("dd MMM yyyy  HH:mm")
        self.datetime_edit.setCalendarPopup(False)  # Disable built-in popup
        self.datetime_edit.setDateTime(QDateTime(2019, 2, 18, 16, 30))
        self.datetime_edit.setMinimumWidth(160)
        dt_row.addWidget(self.datetime_edit)

        # Calendar button - plus visible avec icone
        self.calendar_btn = QPushButton("Select...")
        self.calendar_btn.setFixedSize(70, 34)
        self.calendar_btn.setToolTip("Open calendar to select date")
        self.calendar_btn.setStyleSheet("""
            QPushButton {
                background: #9B59B6;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #8E44AD;
            }
            QPushButton:pressed {
                background: #7D3C98;
            }
        """)
        self.calendar_btn.clicked.connect(self.show_calendar_popup)
        dt_row.addWidget(self.calendar_btn)
        dt_row.addStretch()

        s3_layout.addLayout(dt_row)

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

    def load_file_directly(self, file_path, time_range, source_type='local'):
        """Load a file directly (used by annotations viewer)"""
        self.current_file = file_path

        if source_type == 'local':
            if os.path.exists(file_path):
                try:
                    info = sf.info(file_path)
                    self.info_card.setVisible(True)
                    self.info_label.setText(
                        f"File: {os.path.basename(file_path)[:30]}\n"
                        f"Duration: {info.duration:.1f}s\n"
                        f"Sample rate: {info.samplerate:,} Hz"
                    )
                    self.file_loaded.emit(file_path, time_range, 'local')
                except Exception as e:
                    self.info_label.setText(f"Error: {str(e)[:50]}")
        else:
            # Database source
            self.file_loaded.emit(file_path, time_range, 'database')

    def show_calendar_popup(self):
        """Show calendar dialog - centered and visible"""
        current_dt = self.datetime_edit.dateTime()
        dialog = CalendarDialog(self, current_dt)
        dialog.date_selected.connect(self.on_calendar_date_selected)
        dialog.exec()

    def on_calendar_date_selected(self, dt):
        """Handle date selection from calendar popup"""
        self.datetime_edit.setDateTime(dt)
