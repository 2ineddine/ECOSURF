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
    QGridLayout, QSizePolicy, QDialog, QTimeEdit, QFileDialog, QToolButton, QMenu  # ADD THIS
)
from PyQt6.QtCore import pyqtSignal, Qt, QDateTime, QDate, QTime
from PyQt6.QtGui import QFont, QIcon
import soundfile as sf
import numpy as np


PANEL_STYLE = """
QWidget {
    font-family: 'Segoe UI', sans-serif;
    font-size: 10px;  /* reduced from 12px */
    color: #2C3E50;
    background: white;
}

/* Section Headers */
QLabel#header {
    font-size: 11px;  /* smaller */
    font-weight: 500;
    color: #2C3E50;
    padding: 6px 0;
    border-bottom: 1px solid #3498DB;
    margin-bottom: 6px;
}

/* Compact Toggle Buttons */
QPushButton#toggle_btn {
    background: #F8F9FA;
    border: 1px solid #E0E0E0;
    border-radius: 5px;
    padding: 6px 10px;  /* reduced padding */
    font-size: 10px;
    font-weight: 500;
    color: #5D6D7E;
    min-height: 28px;  /* reduced from 36px */
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
    background: #F0F0F0;  /* removed strong color */
    color: #2C3E50;
    border: 1px solid #D0D0D0;
    border-radius: 5px;
    padding: 6px 14px;
    font-size: 10px;
    font-weight: 500;
    min-height: 28px;
}
QPushButton#primary_btn:hover {
    background: #E8E8E8;
}
QPushButton#primary_btn:pressed {
    background: #D8D8D8;
}
QPushButton#primary_btn:disabled {
    background: #BDC3C7;
}

/* Secondary Buttons */
QPushButton#secondary_btn {
    background: #F8F9FA;
    color: #2C3E50;
    border: 1px solid #E0E0E0;
    border-radius: 5px;
    padding: 5px 12px;
    font-size: 10px;
    font-weight: 500;
    min-height: 28px;
}

/* Inputs */
QComboBox, QDateTimeEdit, QSpinBox {
    background: white;
    border: 1px solid #E0E0E0;
    border-radius: 5px;
    padding: 4px 8px;
    min-height: 28px;  /* shrink height */
    font-size: 10px;   /* shrink text */
}

/* Status Labels */
QLabel#status, QLabel#status_success, QLabel#status_error, QLabel#info_text {
    font-size: 10px;
}
"""

class CalendarDialog(QDialog):
    """Simple web-style calendar dialog"""
    date_selected = pyqtSignal(QDateTime)

    def __init__(self, parent=None, current_datetime=None):
        super().__init__(parent)
        self.setWindowTitle("Select Date & Time")
        self.setModal(True)
        self.setFixedSize(320, 400)

        # Clean web style
        self.setStyleSheet("""
            QDialog {
                background: white;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Calendar widget - compact with 3-letter days
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(False)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        
        # Set year range (2019-2023)
        self.calendar.setMinimumDate(QDate(2019, 1, 1))
        self.calendar.setMaximumDate(QDate(2023, 12, 31))
        
        # Set initial date
        if current_datetime:
            self.calendar.setSelectedDate(current_datetime.date())
        else:
            self.calendar.setSelectedDate(QDate(2019, 2, 18))
        
        # Access navigation bar to customize year button behavior
        nav_bar = self.calendar.findChild(QWidget, "qt_calendar_navigationbar")
        if nav_bar:
            # Find all tool buttons and enable popup mode
            for button in nav_bar.findChildren(QPushButton):
                if hasattr(button, 'setPopupMode'):
                    button.setPopupMode(QPushButton.ToolButtonPopupMode.InstantPopup)
        
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background: white;
                border: none;
            }
            
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: white;
                padding: 4px;
            }
            
            QCalendarWidget QToolButton {
                background: transparent;
                border: none;
                color: #333;
                padding: 8px;
                font-size: 13px;
                font-weight: normal;
                margin: 2px;
            }
            
            QCalendarWidget QToolButton:hover {
                background: #F0F0F0;
                border-radius: 4px;
            }
            
            QCalendarWidget QToolButton::menu-indicator {
                image: none;
            }
            
            QCalendarWidget QMenu {
                background: white;
                border: 1px solid #DDD;
                border-radius: 4px;
            }
            
            QCalendarWidget QMenu::item {
                padding: 8px 16px;
                font-size: 13px;
                font-weight: normal;
                color: #333;
            }
            
            QCalendarWidget QMenu::item:selected {
                background: #F0F0F0;
                color: #333;
            }
            
            QCalendarWidget QTableView {
                background: white;
                selection-background-color: transparent;
                outline: none;
                border: none;
            }
            
            QCalendarWidget QTableView::item {
                padding: 6px 2px;
                color: #333;
                border: none;
                border-radius: 4px;
            }
            
            QCalendarWidget QTableView::item:hover {
                background: #F0F0F0;
            }
            
            QCalendarWidget QTableView::item:selected {
                background: #4A90E2;
                color: white;
                font-weight: 600;
            }
            
            QCalendarWidget QHeaderView::section {
                background: white;
                border: none;
                padding: 6px 2px;
                font-size: 11px;
                font-weight: 600;
                color: #666;
            }
            
            QCalendarWidget QSpinBox {
                background: transparent;
                border: none;
                font-size: 13px;
                color: #333;
                font-weight: normal;
                padding: 4px 8px;
            }
            
            QCalendarWidget QSpinBox::up-button,
            QCalendarWidget QSpinBox::down-button {
                width: 0px;
            }
        """)
            
        self.calendar.activated.connect(self.on_date_activated)
        layout.addWidget(self.calendar)

        # Professional time panel - aligned inputs
        # --- Time panel (minimal & professional) ---
        # --- Time panel (minimal & professional) ---
        time_frame = QFrame()
        time_frame.setStyleSheet("""
            QFrame {
                background: #FAFAFA;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
            }
        """)
        time_layout = QHBoxLayout(time_frame)
        time_layout.setContentsMargins(16, 10, 16, 10)
        time_layout.setSpacing(12)

        # Label
        time_label = QLabel("Time:")
        time_label.setStyleSheet("""
            QLabel {
                color: #555;
                font-size: 13px;
                font-weight: 500;
            }
        """)
        time_label.setFixedWidth(40)
        time_layout.addWidget(time_label)

        # Inner container for hour : minute
        time_values = QHBoxLayout()
        time_values.setSpacing(6)

        # Hour
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(16)
        self.hour_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.hour_spin.setFixedSize(42, 32)
        self.hour_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hour_spin.setStyleSheet("""
            QSpinBox {
                background: white;
                border: 1px solid #D0D0D0;
                border-radius: 4px;
                color: #333;
                font-size: 14px;
                font-weight: 500;
                padding: 0px;
            }
            QSpinBox:hover {
                border-color: #4A90E2;
            }
            QSpinBox:focus {
                border: 2px solid #4A90E2;
                padding: 0px;
            }
        """)
        time_values.addWidget(self.hour_spin)

        # Separator
        colon = QLabel(":")
        colon.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        colon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        colon.setFixedWidth(10)
        time_values.addWidget(colon)

        # Minute
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(30)
        self.minute_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.minute_spin.setFixedSize(42, 32)
        self.minute_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.minute_spin.setStyleSheet("""
            QSpinBox {
                background: white;
                border: 1px solid #D0D0D0;
                border-radius: 4px;
                color: #333;
                font-size: 14px;
                font-weight: 500;
                padding: 0px;
            }
            QSpinBox:hover {
                border-color: #4A90E2;
            }
            QSpinBox:focus {
                border: 2px solid #4A90E2;
                padding: 0px;
            }
        """)
        time_values.addWidget(self.minute_spin)

        time_layout.addLayout(time_values)
        time_layout.addStretch()
        # Center the time frame
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(time_frame)
        center_layout.addStretch()
        layout.addLayout(center_layout)

        # Set initial values from current_datetime if provided
        if current_datetime:
            self.hour_spin.setValue(current_datetime.time().hour())
            self.minute_spin.setValue(current_datetime.time().minute())

        if current_datetime:
            self.hour_spin.setValue(current_datetime.time().hour())
            self.minute_spin.setValue(current_datetime.time().minute())
        else:
            self.hour_spin.setValue(16)
            self.minute_spin.setValue(30)

        # Professional buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setContentsMargins(0, 8, 0, 0)
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFixedHeight(36)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: white;
                color: #666;
                border: 1px solid #D0D0D0;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 500;
                padding: 0 24px;
            }
            QPushButton:hover {
                background: #F8F8F8;
                border-color: #B0B0B0;
                color: #333;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.select_btn = QPushButton("OK")
        self.select_btn.setFixedHeight(36)
        self.select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.select_btn.setStyleSheet("""
            QPushButton {
                background: #4A90E2;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 28px;
            }
            QPushButton:hover {
                background: #357ABD;
            }
            QPushButton:pressed {
                background: #2E6DA4;
            }
        """)
        self.select_btn.clicked.connect(self.on_select)
        btn_layout.addWidget(self.select_btn)

        layout.addLayout(btn_layout)

    def on_date_activated(self, date):
        """Double-click = direct selection"""
        self.on_select()

    def on_select(self):
        date = self.calendar.selectedDate()
        hour = self.hour_spin.value()
        minute = self.minute_spin.value()
        
        # Round minute to nearest 15
        rounded_minute = (minute // 15) * 15
        if rounded_minute != minute:
            minute = rounded_minute
            self.minute_spin.setValue(minute)
        
        time = QTime(hour, minute)
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


        # Date & Time Selection
        # ===== Date & Time Selection =====
        dt_label = QLabel("Start Date & Time")
        dt_label.setStyleSheet("font-weight: 600; color: #2C3E50; margin-top: 4px;")
        s3_layout.addWidget(dt_label)

        # Start DateTime picker
        dt_row = QHBoxLayout()
        dt_row.setSpacing(6)

        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDisplayFormat("dd MMM yyyy  HH:mm")
        self.datetime_edit.setCalendarPopup(False)
        self.datetime_edit.setDateTime(QDateTime(2019, 2, 18, 16, 30))
        self.datetime_edit.setMinimumWidth(160)
        dt_row.addWidget(self.datetime_edit)

        # Calendar button for start
        self.calendar_btn = QPushButton("Select...")
        self.calendar_btn.setFixedSize(70, 34)
        self.calendar_btn.setToolTip("Open calendar to select start date")
        dt_row.addWidget(self.calendar_btn)
        dt_row.addStretch()

        s3_layout.addLayout(dt_row)

        # End DateTime picker
        dt_label2 = QLabel("End Date & Time")
        dt_label2.setStyleSheet("font-weight: 600; color: #2C3E50; margin-top: 4px;")
        s3_layout.addWidget(dt_label2)

        end_dt_row = QHBoxLayout()
        end_dt_row.setSpacing(6)

        self.end_datetime_edit = QDateTimeEdit()
        self.end_datetime_edit.setDisplayFormat("dd MMM yyyy  HH:mm")
        self.end_datetime_edit.setCalendarPopup(False)
        # Set default end = start + 15 minutes
        default_end = self.datetime_edit.dateTime().addSecs(15 * 60)
        self.end_datetime_edit.setDateTime(default_end)
        self.end_datetime_edit.setMinimumWidth(160)
        end_dt_row.addWidget(self.end_datetime_edit)

        # Calendar button for end
        self.end_calendar_btn = QPushButton("Select...")
        self.end_calendar_btn.setFixedSize(70, 34)
        self.end_calendar_btn.setToolTip("Open calendar to select end date")
        end_dt_row.addWidget(self.end_calendar_btn)
        end_dt_row.addStretch()

        s3_layout.addLayout(end_dt_row)

        # --- Button Styling ---
        btn_style = """
        QPushButton {
            background: #F0F0F0;
            color: #2C3E50;
            border: 1px solid #D0D0D0;
            border-radius: 5px;
            font-weight: 500;
            font-size: 10px;
        }
        QPushButton:hover {
            background: #E8E8E8;
        }
        """
        self.calendar_btn.setStyleSheet(btn_style)
        self.end_calendar_btn.setStyleSheet(btn_style)

        # --- Connections ---
        self.calendar_btn.clicked.connect(self.show_start_calendar_popup)
        self.end_calendar_btn.clicked.connect(self.show_end_calendar_popup)

       


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

    def get_site_from_date(self, year):
        """Determine site based on year"""
        site_mapping = {
            2019: ["S4A09154"],
            2020: ["S4A09154"],
            2021: ["S4A06374", "S4A09128", "S4A09154"],
            2022: ["S4A06374"],
            2023: ["S4A06374", "S4A90112"]
        }
        sites = site_mapping.get(year, ["S4A09154"])
        return sites[0]

    
    
    def show_start_calendar_popup(self):
        dialog = CalendarDialog(self, self.datetime_edit.dateTime())
        dialog.date_selected.connect(lambda dt: self.on_calendar_date_selected(dt, self.datetime_edit))
        dialog.exec()

    def show_end_calendar_popup(self):
        dialog = CalendarDialog(self, self.end_datetime_edit.dateTime())
        dialog.date_selected.connect(lambda dt: self.on_calendar_date_selected(dt, self.end_datetime_edit))
        dialog.exec()

    def browse_local(self):
        """Open file browser for local files"""
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

    def show_calendar_popup(self, target_widget=None):
        """Show calendar dialog - centered and visible"""
        if target_widget is None:
            target_widget = self.datetime_edit
        
        current_dt = target_widget.dateTime()
        dialog = CalendarDialog(self, current_dt)
        dialog.date_selected.connect(lambda dt: self.on_calendar_date_selected(dt, target_widget))
        dialog.exec()

    def on_calendar_date_selected(self, dt, target_widget):
        """Handle date selection from calendar popup"""
        # Round to nearest 15 minutes
        minute = dt.time().minute()
        rounded_minute = (minute // 15) * 15
        if rounded_minute != minute:
            dt = QDateTime(dt.date(), QTime(dt.time().hour(), rounded_minute))
        
        target_widget.setDateTime(dt)
    

    def load_from_s3(self):
        """Load audio from S3 based on start and end time selections (15-min flexible blocks)"""
        start_dt = self.datetime_edit.dateTime()
        end_dt = self.end_datetime_edit.dateTime()

        if end_dt < start_dt:
            self.update_file_info("Error: End time must be after start time")
            return

        year = start_dt.date().year()
        site = self.get_site_from_date(year)

        # --- Snap start & end to 15-minute grid ---
        def snap_to_15(dt):
            m = (dt.time().minute() // 15) * 15
            return QDateTime(dt.date(), QTime(dt.time().hour(), m))

        start_dt = snap_to_15(start_dt)
        end_dt = snap_to_15(end_dt)

        # --- Generate one file per 15-minute slot ---
        files = []
        current_dt = start_dt

        while current_dt < end_dt:
            date_str = current_dt.toString("yyyyMMdd")
            time_str = current_dt.toString("HHmmss")
            files.append(f"{site}_{date_str}_{time_str}.flac")
            current_dt = current_dt.addSecs(15 * 60)

        # --- Full playback range ---
        total_seconds = start_dt.secsTo(end_dt)
        time_range = (0, total_seconds)

        # Emit
        if len(files) == 1:
            self.file_loaded.emit(files[0], time_range, 'database')
        else:
            self.file_loaded.emit(files, time_range, 'database')

        # UI info
        self.info_card.setVisible(True)
        self.info_label.setText(
            f"Site: {site}\n"
            f"Start: {start_dt.toString('dd MMM yyyy HH:mm')}\n"
            f"End: {end_dt.toString('dd MMM yyyy HH:mm')}\n"
            f"Files loaded: {len(files)}"
        )

