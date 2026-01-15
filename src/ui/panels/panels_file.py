"""
File Management Panel - Step-by-Step Wizard
Intuitive workflow: Choose source → Choose scope → Load & display
"""
import os
import re
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, 
    QGroupBox, QScrollArea, QComboBox, QHBoxLayout, QMessageBox,
    QRadioButton, QButtonGroup, QFrame
)

from PyQt6.QtWidgets import QDialog, QCalendarWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtWidgets import QDialog, QCalendarWidget, QVBoxLayout, QPushButton
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtCore import QRegularExpression
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QSlider

import soundfile as sf
import numpy as np

from ui.dialogs.period_selection import PeriodSelectionDialog


class FilePanel(QWidget):
    # file_loaded = pyqtSignal(str, tuple, str)  # Single file
    # files_loaded = pyqtSignal(list, tuple, str)  # Multiple files (NEW)
    folder_loaded = pyqtSignal(list)
    # #file_loaded = pyqtSignal(str, tuple, str)  # file_path, time_range, source_type
    # folder_loaded = pyqtSignal(list)
    file_loaded = pyqtSignal(object, tuple, str)  # file_path(s), time_range, source_type
    period_dict_loaded = pyqtSignal(dict)  # Emit period dictionary for other panels
    search_scope_changed = pyqtSignal(str, list)
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.file_list = []
        self.period_dict = {}
        self.unique_dates = []
        self.date_to_times = {}
        self.current_source = None  # 'database' or 'local'
        self.init_ui()



    def create_ubuntu_step_widget(self, step_num, title, description):
        """Create an Ubuntu-style step header"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: #F7F7F7;
                border-left: 4px solid #E95420;
                border-radius: 3px;
                padding: 8px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        
        step_label = QLabel(f"<b>Step {step_num}</b>")
        step_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #E95420;
                font-weight: bold;
            }
        """)
        layout.addWidget(step_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333333;
            }
        """)
        layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #5E5E5E;
                line-height: 1.3;
            }
        """)
        layout.addWidget(desc_label)
        
        return widget  
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Ubuntu-themed Title
        title = QLabel("File Selection")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #E95420;  /* Ubuntu orange */
                padding: 8px 0px;
                border-bottom: 2px solid #DEDEDE;
                margin-bottom: 5px;
            }
        """)
        layout.addWidget(title)
        
        # ========= STEP 1: CHOOSE SOURCE =========
        step1 = self.create_ubuntu_step_widget(
            "1", 
            "Choose Data Source",
            "Where is your audio data located?"
        )
        layout.addWidget(step1)
        
        source_group = QGroupBox()
        source_group.setStyleSheet("""
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
        source_layout = QVBoxLayout()
        source_layout.setSpacing(8)
        source_layout.setContentsMargins(12, 15, 12, 12)
        
        self.source_button_group = QButtonGroup()
        
        # Ubuntu-style radio buttons
        self.source_database = QRadioButton("Database (S3 Cloud Storage)")
        self.source_database.setStyleSheet("""
            QRadioButton {
                font-size: 13px;
                padding: 8px 0px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #888888;
            }
            QRadioButton::indicator:checked {
                background-color: #E95420;  /* Ubuntu orange */
                border: 2px solid #E95420;
            }
        """)
        self.source_button_group.addButton(self.source_database, 1)
        source_layout.addWidget(self.source_database)
        
        db_hint = QLabel("• Access thousands of pre-processed files\n• Requires period_locations.json")
        db_hint.setStyleSheet("""
            QLabel {
                color: #5E5E5E;
                font-size: 11px;
                margin-left: 26px;
                line-height: 1.3;
            }
        """)
        source_layout.addWidget(db_hint)
        
        self.source_local = QRadioButton("Local Files (My Computer)")
        self.source_local.setStyleSheet("""
            QRadioButton {
                font-size: 13px;
                padding: 8px 0px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #888888;
            }
            QRadioButton::indicator:checked {
                background-color: #E95420;
                border: 2px solid #E95420;
            }
        """)
        self.source_button_group.addButton(self.source_local, 2)
        source_layout.addWidget(self.source_local)
        
        local_hint = QLabel("• Use your own audio files\n• Traditional file browser")
        local_hint.setStyleSheet("""
            QLabel {
                color: #5E5E5E;
                font-size: 11px;
                margin-left: 26px;
                line-height: 1.3;
            }
        """)
        source_layout.addWidget(local_hint)
        
        # Ubuntu-style button
        self.confirm_source_btn = QPushButton("Confirm Source")
        self.confirm_source_btn.setEnabled(False)
        self.confirm_source_btn.setMinimumHeight(36)
        self.confirm_source_btn.setStyleSheet("""
            QPushButton {
                background-color: #E95420;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 8px;
                margin-top: 10px;
            }
            QPushButton:enabled:hover {
                background-color: #D34615;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #888888;
            }
        """)
        self.confirm_source_btn.clicked.connect(self.on_source_confirmed)
        source_layout.addWidget(self.confirm_source_btn)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        self.source_database.toggled.connect(lambda: self.confirm_source_btn.setEnabled(True))
        self.source_local.toggled.connect(lambda: self.confirm_source_btn.setEnabled(True))
        
        # ========= STEP 2: CHOOSE SCOPE (Hidden initially) =========
        self.step2_widget = self.create_ubuntu_step_widget(
            "2",
            "Choose Time Scope",
            "For Database files only"
        )
        self.step2_widget.setVisible(False)
        layout.addWidget(self.step2_widget)
        
        self.scope_group = QGroupBox()
        self.scope_group.setStyleSheet("""
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
        scope_layout = QVBoxLayout()
        scope_layout.setSpacing(8)
        scope_layout.setContentsMargins(12, 15, 12, 12)
        
        self.scope_button_group = QButtonGroup()
        
        self.scope_single = QRadioButton("Single Minute File")
        self.scope_single.setStyleSheet("""
            QRadioButton {
                font-size: 13px;
                padding: 8px 0px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #888888;
            }
            QRadioButton::indicator:checked {
                background-color: #E95420;
                border: 2px solid #E95420;
            }
        """)
        self.scope_button_group.addButton(self.scope_single, 1)
        scope_layout.addWidget(self.scope_single)
        
        single_hint = QLabel("• Display one specific minute\n• Fast loading")
        single_hint.setStyleSheet("""
            QLabel {
                color: #5E5E5E;
                font-size: 11px;
                margin-left: 26px;
                line-height: 1.3;
            }
        """)
        scope_layout.addWidget(single_hint)
        
        self.scope_range = QRadioButton("Date/Time Range")
        self.scope_range.setStyleSheet("""
            QRadioButton {
                font-size: 13px;
                padding: 8px 0px;
                spacing: 8px;
            }
            QRadioButton::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #888888;
            }
            QRadioButton::indicator:checked {
                background-color: #E95420;
                border: 2px solid #E95420;
            }
        """)
        self.scope_button_group.addButton(self.scope_range, 2)
        scope_layout.addWidget(self.scope_range)
        self.scope_range.setToolTip("Available only for Database source")
        
        range_hint = QLabel("• Multiple files combined\n• Longer audio segments")
        range_hint.setStyleSheet("""
            QLabel {
                color: #5E5E5E;
                font-size: 11px;
                margin-left: 26px;
                line-height: 1.3;
            }
        """)
        scope_layout.addWidget(range_hint)
        
        self.confirm_scope_btn = QPushButton("Confirm")
        self.confirm_scope_btn.setEnabled(False)
        self.confirm_scope_btn.setMinimumHeight(36)
        self.confirm_scope_btn.setStyleSheet("""
            QPushButton {
                background-color: #77216F;  /* Ubuntu purple */
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 8px;
                margin-top: 10px;
            }
            QPushButton:enabled:hover {
                background-color: #5E2750;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #888888;
            }
        """)
        self.confirm_scope_btn.clicked.connect(self.on_scope_confirmed)
        scope_layout.addWidget(self.confirm_scope_btn)
        
        self.scope_group.setLayout(scope_layout)
        self.scope_group.setVisible(False)
        layout.addWidget(self.scope_group)
        
        self.scope_single.toggled.connect(lambda: self.confirm_scope_btn.setEnabled(True))
        self.scope_range.toggled.connect(lambda: self.confirm_scope_btn.setEnabled(True))
        
        # ========= STEP 3: SELECTION UI (Hidden initially) =========
        self.step3_widget = self.create_ubuntu_step_widget(
            "3",
            "Select & Load",
            "Choose your audio file(s)"
        )
        self.step3_widget.setVisible(False)
        layout.addWidget(self.step3_widget)
        
        # ========= DATABASE - SINGLE FILE SELECTION =========
        self.db_single_group = QGroupBox("Select Specific File")
        self.db_single_group.setStyleSheet("""
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
        db_single_layout = QVBoxLayout()
        db_single_layout.setSpacing(10)
        db_single_layout.setContentsMargins(12, 15, 12, 12)

        # Date selection
        date_layout = QHBoxLayout()
        date_label = QLabel("Date:")
        date_label.setStyleSheet("font-weight: bold; font-size: 12px; min-width: 40px;")
        date_layout.addWidget(date_label)
        
        self.date_combo = QComboBox()
        self.date_combo.setVisible(False)
        self.date_combo.setStyleSheet("""
            QComboBox {
                font-size: 12px;
                padding: 6px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                background-color: white;
                min-height: 28px;
            }
            QComboBox:hover {
                border: 1px solid #888888;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #CCCCCC;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #333333;
            }
        """)
        self.date_combo.setMinimumWidth(120)
        self.date_combo.currentTextChanged.connect(self.on_date_selected)
        date_layout.addWidget(self.date_combo, stretch=1)

        # Ubuntu-style calendar button
        self.calendar_btn = QPushButton("Calendar")
        self.calendar_btn.setMinimumHeight(28)
        self.calendar_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F2;
                color: #333333;
                font-size: 12px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #E5E5E5;
                border: 1px solid #888888;
            }
            QPushButton:pressed {
                background-color: #D8D8D8;
            }
        """)
        self.calendar_btn.clicked.connect(self.open_calendar_picker)
        date_layout.addWidget(self.calendar_btn)
        db_single_layout.addLayout(date_layout)

        # Time selection
        time_layout = QHBoxLayout()
        time_label = QLabel("Time:")
        time_label.setStyleSheet("font-weight: bold; font-size: 12px; min-width: 40px;")
        time_layout.addWidget(time_label)
        
        self.time_combo = QComboBox()
        self.time_combo.setStyleSheet("""
            QComboBox {
                font-size: 12px;
                padding: 6px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                background-color: white;
                min-height: 28px;
            }
            QComboBox:hover {
                border: 1px solid #888888;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #CCCCCC;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #333333;
            }
        """)
        self.time_combo.setMinimumWidth(100)
        time_layout.addWidget(self.time_combo, stretch=1)
        db_single_layout.addLayout(time_layout)

        # Ubuntu-style load button
        self.load_db_single_btn = QPushButton("Load & Display")
        self.load_db_single_btn.setMinimumHeight(36)
        self.load_db_single_btn.setStyleSheet("""
            QPushButton {
                background-color: #E95420;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 8px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #D34615;
            }
        """)
        self.load_db_single_btn.clicked.connect(self.load_database_single)
        db_single_layout.addWidget(self.load_db_single_btn)

        self.db_single_group.setLayout(db_single_layout)
        self.db_single_group.setVisible(False)
        layout.addWidget(self.db_single_group)
        
        # ========= DATABASE - RANGE SELECTION =========
        self.db_range_group = QGroupBox("Select Date Range")
        self.db_range_group.setStyleSheet("""
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
        db_range_layout = QVBoxLayout()
        db_range_layout.setSpacing(12)
        db_range_layout.setContentsMargins(12, 15, 12, 12)

        # Date range selection
        range_selector = QGroupBox("Date Range")
        range_selector.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: none;
                margin-top: 0px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                color: #333333;
            }
        """)
        range_selector_layout = QHBoxLayout()
        range_selector_layout.setSpacing(15)

        # Start date
        start_layout = QVBoxLayout()
        start_label = QLabel("From:")
        start_label.setStyleSheet("font-size: 11px; color: #5E5E5E; margin-bottom: 4px;")
        start_layout.addWidget(start_label)
        
        start_widget = QWidget()
        start_hbox = QHBoxLayout(start_widget)
        start_hbox.setSpacing(5)
        start_hbox.setContentsMargins(0, 0, 0, 0)
        
        self.start_date_combo = QComboBox()
        self.start_date_combo.setStyleSheet("""
            QComboBox {
                font-size: 12px;
                padding: 6px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                background-color: white;
                min-height: 28px;
                min-width: 120px;
            }
            QComboBox:hover {
                border: 1px solid #888888;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #CCCCCC;
            }
        """)
        start_hbox.addWidget(self.start_date_combo)
        
        self.start_cal_btn = QPushButton("...")
        self.start_cal_btn.setFixedSize(28, 28)
        self.start_cal_btn.setToolTip("Pick start date")
        self.start_cal_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F2;
                color: #333333;
                font-size: 12px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #E5E5E5;
                border: 1px solid #888888;
            }
        """)
        self.start_cal_btn.clicked.connect(lambda: self.open_range_calendar('start'))
        start_hbox.addWidget(self.start_cal_btn)
        start_layout.addWidget(start_widget)

        # Arrow separator
        arrow_label = QLabel("→")
        arrow_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #888888;
                padding: 0 5px;
                margin-top: 15px;
            }
        """)
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # End date
        end_layout = QVBoxLayout()
        end_label = QLabel("To:")
        end_label.setStyleSheet("font-size: 11px; color: #5E5E5E; margin-bottom: 4px;")
        end_layout.addWidget(end_label)
        
        end_widget = QWidget()
        end_hbox = QHBoxLayout(end_widget)
        end_hbox.setSpacing(5)
        end_hbox.setContentsMargins(0, 0, 0, 0)
        
        self.end_date_combo = QComboBox()
        self.end_date_combo.setStyleSheet("""
            QComboBox {
                font-size: 12px;
                padding: 6px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                background-color: white;
                min-height: 28px;
                min-width: 120px;
            }
            QComboBox:hover {
                border: 1px solid #888888;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left: 1px solid #CCCCCC;
            }
        """)
        end_hbox.addWidget(self.end_date_combo)
        
        self.end_cal_btn = QPushButton("...")
        self.end_cal_btn.setFixedSize(28, 28)
        self.end_cal_btn.setToolTip("Pick end date")
        self.end_cal_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F2;
                color: #333333;
                font-size: 12px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #E5E5E5;
                border: 1px solid #888888;
            }
        """)
        self.end_cal_btn.clicked.connect(lambda: self.open_range_calendar('end'))
        end_hbox.addWidget(self.end_cal_btn)
        end_layout.addWidget(end_widget)

        range_selector_layout.addLayout(start_layout)
        range_selector_layout.addWidget(arrow_label)
        range_selector_layout.addLayout(end_layout)
        range_selector.setLayout(range_selector_layout)
        db_range_layout.addWidget(range_selector)

        # Time range filter
        time_range_group = QGroupBox("Time Filter (15-minute intervals)")
        time_range_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: none;
                margin-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 0px;
                color: #333333;
            }
        """)
        time_range_layout = QVBoxLayout()

        time_filter_layout = QHBoxLayout()
        time_filter_layout.setSpacing(10)
        
        from_label = QLabel("From:")
        from_label.setStyleSheet("font-size: 11px; color: #5E5E5E; min-width: 35px;")
        time_filter_layout.addWidget(from_label)
        
        self.time_filter_start = QComboBox()
        
        # Generate 15-minute intervals
        times_15min = []
        for hour in range(24):
            for minute in [0, 15, 30, 45]:
                times_15min.append(f"{hour:02d}:{minute:02d}")
        
        self.time_filter_start.addItems(times_15min)
        self.time_filter_start.setStyleSheet("""
            QComboBox {
                font-size: 12px;
                padding: 6px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                background-color: white;
                min-height: 28px;
                min-width: 80px;
            }
            QComboBox:hover {
                border: 1px solid #888888;
            }
        """)
        time_filter_layout.addWidget(self.time_filter_start)
        
        to_label = QLabel("to")
        to_label.setStyleSheet("font-size: 11px; color: #5E5E5E; margin: 0 5px;")
        time_filter_layout.addWidget(to_label)
        
        self.time_filter_end = QComboBox()
        self.time_filter_end.addItems(times_15min)
        self.time_filter_end.setCurrentText("23:45")
        self.time_filter_end.setStyleSheet("""
            QComboBox {
                font-size: 12px;
                padding: 6px;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                background-color: white;
                min-height: 28px;
                min-width: 80px;
            }
            QComboBox:hover {
                border: 1px solid #888888;
            }
        """)
        time_filter_layout.addWidget(self.time_filter_end)
        
        time_range_layout.addLayout(time_filter_layout)
        time_range_group.setLayout(time_range_layout)
        db_range_layout.addWidget(time_range_group)

        # Load range button
        self.load_db_range_btn = QPushButton("Load Range")
        self.load_db_range_btn.setMinimumHeight(36)
        self.load_db_range_btn.setStyleSheet("""
            QPushButton {
                background-color: #77216F;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 8px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #5E2750;
            }
        """)
        self.load_db_range_btn.clicked.connect(self.load_database_range)
        db_range_layout.addWidget(self.load_db_range_btn)
        
        self.db_range_group.setLayout(db_range_layout)
        self.db_range_group.setVisible(False)
        layout.addWidget(self.db_range_group)
        
        # ========= LOCAL - SINGLE FILE =========
        self.local_single_group = QGroupBox("Browse for File")
        self.local_single_group.setStyleSheet("""
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
        local_single_layout = QVBoxLayout()
        local_single_layout.setContentsMargins(12, 15, 12, 12)
        
        self.load_local_single_btn = QPushButton("Browse & Select Audio File")
        self.load_local_single_btn.setMinimumHeight(36)
        self.load_local_single_btn.setStyleSheet("""
            QPushButton {
                background-color: #2C001E;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #1A0014;
            }
        """)
        self.load_local_single_btn.clicked.connect(self.load_local_file)
        local_single_layout.addWidget(self.load_local_single_btn)
        
        self.local_single_group.setLayout(local_single_layout)
        self.local_single_group.setVisible(False)
        layout.addWidget(self.local_single_group)
        
        # ========= LOCAL - FOLDER =========
        self.local_folder_group = QGroupBox("Browse for Folder")
        self.local_folder_group.setStyleSheet("""
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
        local_folder_layout = QVBoxLayout()
        local_folder_layout.setContentsMargins(12, 15, 12, 12)
        
        self.load_local_folder_btn = QPushButton("Browse & Select Folder")
        self.load_local_folder_btn.setMinimumHeight(36)
        self.load_local_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #2C001E;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #1A0014;
            }
        """)
        self.load_local_folder_btn.clicked.connect(self.load_local_folder)
        local_folder_layout.addWidget(self.load_local_folder_btn)
        
        self.local_folder_group.setLayout(local_folder_layout)
        self.local_folder_group.setVisible(False)
        layout.addWidget(self.local_folder_group)
        
        # ========= STATUS INFO =========
        info_group = QGroupBox("Current Status")
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
        
        self.status_label = QLabel("Please complete Step 1 to begin")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: white;
                border: 1px solid #DEDEDE;
                border-radius: 3px;
                font-size: 11px;
                color: #333333;
                line-height: 1.4;
            }
        """)
        info_layout.addWidget(self.status_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Ubuntu-style reset button
        reset_btn = QPushButton("Start Over")
        reset_btn.setMinimumHeight(32)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #F2F2F2;
                color: #333333;
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 6px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #E5E5E5;
                border: 1px solid #888888;
            }
        """)
        reset_btn.clicked.connect(self.reset_wizard)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
    def create_step_widget(self, step_num, title, description):
        """Create a styled step header"""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-left: 4px solid #4CAF50;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        layout = QVBoxLayout(widget)
        layout.setSpacing(2)
        
        step_label = QLabel(f"<b>{step_num}</b>")
        step_label.setStyleSheet("font-size: 11px; color: #4CAF50;")
        layout.addWidget(step_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 10px; color: #666;")
        layout.addWidget(desc_label)
        
        return widget
        
    def on_source_confirmed(self):
        """Handle source confirmation"""
        if self.source_database.isChecked():
            self.current_source = 'database'
            # Try to load period_locations.json
            self.load_period_dict()
            
        elif self.source_local.isChecked():
            self.current_source = 'local'
            # COMPLETELY SKIP STEP 2 - Go directly to file upload
            self.status_label.setText("Source: Local Files\n\nSelect your audio file")
            
            # Hide Step 2 completely
            self.step2_widget.setVisible(False)
            self.scope_group.setVisible(False)
            
            # Show Step 3 directly (file upload)
            self.step3_widget.setVisible(True)
            
            # Show only local file upload option
            self.db_single_group.setVisible(False)
            self.db_range_group.setVisible(False)
            self.local_single_group.setVisible(True)
            self.local_folder_group.setVisible(False)
            
            # Emit a dummy scope confirmation to trigger any connected signals
            self.scope_single.setChecked(True)  # Auto-set to single file
            
    # File: ui/panels/panels_file.py
# In load_period_dict method, UPDATE the first search path:

    def load_period_dict(self):
        """Load period_locations.json from pre_processing_data"""
        # FIXED: Your file is at M2_PFE_ECOSURF/pre_processing_data/period_locations.json
        possible_paths = [
            # OPTION 1: From project root (where main.py runs)
            os.path.join('pre_processing_data', 'period_locations.json'),  # ← THIS ONE!
            
            # OPTION 2: Relative from this file
            os.path.join(os.path.dirname(__file__), '..', '..', '..', 'pre_processing_data', 'period_locations.json'),
            
            # OPTION 3: Absolute from current directory
            os.path.join(os.getcwd(), 'pre_processing_data', 'period_locations.json'),
            
            # Backup options
            'period_locations.json',
            os.path.join('data', 'pre_processing_data', 'period_locations.json'),
            os.path.join('..', 'pre_processing_data', 'period_locations.json'),
        ]
        
        print("DEBUG: Looking for period_locations.json...")
        found_path = None
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            exists = os.path.exists(path)
            print(f"   {'[OK]' if exists else '[NOT FOUND]'} {abs_path}")
            
            if exists and found_path is None:
                found_path = abs_path
                break
        
        if not found_path:
            # Create helpful error message
            error_msg = (
                "Could not find period_locations.json!\n\n"
                f"Current directory: {os.getcwd()}\n"
                f"Expected at: {os.path.abspath('pre_processing_data/period_locations.json')}\n\n"
                "Please ensure the file exists in:\n"
                "M2_PFE_ECOSURF/pre_processing_data/period_locations.json"
            )
            QMessageBox.critical(self, "File Not Found", error_msg)
            return
        
        print(f"DEBUG: Found at: {found_path}")
        
        try:
            with open(found_path, 'r') as f:
                self.period_dict = json.load(f)
                
            self.process_period_dict()
            self.status_label.setText(
                f"Source: Database\n"
                f"Loaded: {len(self.period_dict):,} files\n"
                f"Date range: {self.unique_dates[0]} to {self.unique_dates[-1]}\n\n"
                f"Proceed to Step 2"
            )
            
            self.step2_widget.setVisible(True)
            self.scope_group.setVisible(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load database:\n{str(e)}")  
    def process_period_dict(self):
        """Process period dictionary"""
        self.unique_dates = sorted(list(set(
            k.split('_')[0] for k in self.period_dict.keys()
        )))
        
        self.date_to_times = {}
        for period_key in self.period_dict.keys():
            date_str, time_str = period_key.split('_')
            if date_str not in self.date_to_times:
                self.date_to_times[date_str] = []
            time_short = time_str[:5]
            if time_short not in self.date_to_times[date_str]:
                self.date_to_times[date_str].append(time_short)
                
        for date in self.date_to_times:
            self.date_to_times[date].sort()
            
    def on_scope_confirmed(self):
        """Handle scope confirmation - ONLY for database files"""
        self.step3_widget.setVisible(True)
        
        # This method is only called for database files now
        if self.scope_single.isChecked():
            # Show database single selection
            self.db_single_group.setVisible(True)
            self.db_range_group.setVisible(False)
            self.local_single_group.setVisible(False)
            self.local_folder_group.setVisible(False)
            self.populate_date_combos()
            self.status_label.setText(
                "Source: Database\n"
                "Scope: Single File\n\n"
                "Select date and time, then click 'Load & Display'"
            )
        elif self.scope_range.isChecked():
            # Show database range selection
            self.db_single_group.setVisible(False)
            self.db_range_group.setVisible(True)
            self.local_single_group.setVisible(False)
            self.local_folder_group.setVisible(False)
            self.populate_range_combos()
            self.status_label.setText(
                "Source: Database\n"
                "Scope: Date Range\n\n"
                "Select date range, then click 'Load & Combine Range'"
            )
    def populate_date_combos(self):
        """Populate date/time combos for single file selection"""
        self.date_combo.clear()
        self.date_combo.addItems(self.unique_dates)
        
    def populate_range_combos(self):
        """Populate range combos"""
        self.start_date_combo.clear()
        self.start_date_combo.addItems(self.unique_dates)
        
        self.end_date_combo.clear()
        self.end_date_combo.addItems(self.unique_dates)
        if self.unique_dates:
            self.end_date_combo.setCurrentIndex(len(self.unique_dates)-1)
            
    def on_date_selected(self, date_str):
        """Update time combo when date selected"""
        if date_str in self.date_to_times:
            self.time_combo.clear()
            self.time_combo.addItems(self.date_to_times[date_str])
            
    # File: ui/panels/panels_file.py
# In load_database_single method, UPDATE the S3 URI construction:

    def load_database_single(self):
        """Load single file from database"""
        date = self.date_combo.currentText()
        time = self.time_combo.currentText()
        
        if not date or not time:
            QMessageBox.warning(self, "Selection Error", "Please select date and time")
            return
            
        period_key = f"{date}_{time}:00"
        
        if period_key not in self.period_dict:
            period_key = f"{date}_{time}"
            
        if period_key in self.period_dict:
            file_info = self.period_dict[period_key]
            
            # FIX: Use 's3_uri' (not 's3_path')
            s3_uri = file_info.get('s3_uri', '')
            
            # Validate
            if not s3_uri or not s3_uri.startswith('s3://'):
                QMessageBox.warning(self, "Invalid URI", f"S3 URI is invalid: {s3_uri}")
                return
            
            print(f"DEBUG: S3 URI: {s3_uri}")
            
            time_range = (0.0, 60.0)
            self.current_file = s3_uri
            
            self.status_label.setText(
                f"<b>Loaded from Database</b><br>"
                f"{date} {time}<br>"
                f"Device: {file_info.get('device', 'N/A')}<br>"
                f"Size: {file_info.get('size_mb', 0):.1f} MB"
            )
            
            self.file_loaded.emit(s3_uri, time_range, 'database')
        else:
            QMessageBox.warning(self, "Not Found", f"File not found: {period_key}")
            
   # File: ui/panels/panels_file.py
# REPLACE the entire load_database_range method (from line ~369 onward):

    def load_database_range(self):
        """Load range from database for concatenation"""
        start_date = self.start_date_combo.currentText()
        end_date = self.end_date_combo.currentText()
        time_start = self.time_filter_start.currentText()
        time_end = self.time_filter_end.currentText()
        
        if not start_date or not end_date:
            QMessageBox.warning(self, "Selection Error", "Please select date range")
            return
            
        # Collect files in range
        range_files = []
        range_info = []
        
        for period_key, file_info in self.period_dict.items():
            file_date, file_time = period_key.split('_')
            file_hour_min = file_time[:5]  # Get HH:MM
            
            # Convert times to minutes for comparison
            file_time_min = self.time_to_minutes(file_hour_min)
            time_start_min = self.time_to_minutes(time_start)
            time_end_min = self.time_to_minutes(time_end)
            
            if start_date <= file_date <= end_date:
                if time_start_min <= file_time_min <= time_end_min:
                    # FIX: Use 's3_uri' (not 's3_path')
                    s3_uri = file_info.get('s3_uri', '')
                    
                    # Validate URI before adding
                    if s3_uri and s3_uri.startswith('s3://'):
                        range_files.append(s3_uri)
                        range_info.append((period_key, file_info))
                        print(f"DEBUG: Added S3 URI: {s3_uri}")
                    else:
                        print(f"WARNING: Skipping {period_key} - invalid S3 URI")
                            
        if not range_files:
            QMessageBox.warning(self, "No Files", "No files found in range")
            return
        
        self.file_list = range_files
        self.current_file = range_files
        
        total_duration = len(range_files) * 60
        
        self.status_label.setText(
            f"<b>Ready to Concatenate</b><br>"
            f"Range: {start_date} to {end_date}<br>"
            f"Time: {time_start} to {time_end}<br>"
            f"Files: {len(range_files):,}<br>"
            f"Total duration: {total_duration/60:.1f} minutes"
        )
        
        self.file_loaded.emit(range_files, (0.0, 60.0), 'database')
        self.folder_loaded.emit(range_files)
        
        QMessageBox.information(
            self,
            "Range Selected",
            f"Selected {len(range_files):,} files ({total_duration/60:.1f} minutes)\n\n"
            f"Click 'Compute' in Spectrogram Panel to concatenate and display."
        )
    def load_local_file(self):
        """Load single local file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Audio File", "", "Audio Files (*.flac *.wav *.mp3)"
        )
        
        if file_path:
            try:
                info = sf.info(file_path)
                duration = info.duration
                
                metadata = self.parse_filename(os.path.basename(file_path))
                dialog = PeriodSelectionDialog(metadata, duration, self)
                if dialog.exec():
                    time_range = dialog.get_time_range()
                    self.current_file = file_path
                    
                    self.status_label.setText(
                        f"<b>Loaded from Local</b><br>"
                        f"{os.path.basename(file_path)}<br>"
                        f"Duration: {duration:.1f}s<br>"
                        f"Range: {time_range[0]:.1f}s - {time_range[1]:.1f}s"
                    )
                    
                    self.file_loaded.emit(file_path, time_range, 'local')
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load file:\n{str(e)}")
                
    def load_local_folder(self):
        """Load local folder"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        
        if folder_path:
            self.file_list = [
                os.path.join(folder_path, f) 
                for f in os.listdir(folder_path) 
                if f.endswith(('.flac', '.wav', '.mp3'))
            ]
            
            if self.file_list:
                self.status_label.setText(
                    f"<b>Loaded from Local</b><br>"
                    f"{os.path.basename(folder_path)}<br>"
                    f"Files: {len(self.file_list):,}"
                )
                
                self.folder_loaded.emit(self.file_list)
            else:
                QMessageBox.warning(self, "No Files", "No audio files found in folder")
                
    def parse_filename(self, filename):
        """Parse filename for metadata"""
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
        
    def time_to_minutes(self, time_str):
        """Convert HH:MM to minutes"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes
        except:
            return 0
            
    def reset_wizard(self):
        """Reset the wizard to step 1"""
        self.current_source = None
        self.current_file = None
        self.file_list = []
        
        # Hide all steps except step 1
        self.step2_widget.setVisible(False)
        self.step3_widget.setVisible(False)
        self.scope_group.setVisible(False)
        self.db_single_group.setVisible(False)
        self.db_range_group.setVisible(False)
        self.local_single_group.setVisible(False)
        self.local_folder_group.setVisible(False)
        
        # Reset button groups
        self.source_button_group.setExclusive(False)
        self.source_database.setChecked(False)
        self.source_local.setChecked(False)
        self.source_button_group.setExclusive(True)
        
        # Auto-reset scope to single for next time
        self.scope_button_group.setExclusive(False)
        self.scope_single.setChecked(True)  # Reset to single
        self.scope_range.setChecked(False)
        self.scope_button_group.setExclusive(True)
        
        # Reset confirm buttons
        self.confirm_source_btn.setEnabled(False)
        self.confirm_scope_btn.setEnabled(False)
        
        self.status_label.setText("Please complete Step 1 to begin")
        
    def update_file_info(self, additional_info):
        """Update status label with additional info"""
        current = self.status_label.text()
        self.status_label.setText(f"{current}<br>{additional_info}")
    
    def open_range_calendar(self, which):
        """Open calendar for range selection (start or end) - no colors"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Select {which.capitalize()} Date")
        dialog.setFixedSize(300, 250)

        layout = QVBoxLayout(dialog)
        
        calendar = QCalendarWidget()
        calendar.setGridVisible(False)
        # NO COLORS - minimal styling
        calendar.setStyleSheet("""
            QCalendarWidget {
                border: 1px solid #ccc;
                background-color: white;
            }
            QCalendarWidget QAbstractItemView {
                background-color: white;
                selection-background-color: #e0e0e0;
                selection-color: black;
            }
            QCalendarWidget QToolButton {
                background-color: white;
                border: 1px solid #ddd;
                color: black;
            }
        """)
        
        # Set current selection
        combo = self.start_date_combo if which == 'start' else self.end_date_combo
        current_date = combo.currentText()
        if current_date:
            try:
                year, month, day = map(int, current_date.split('-'))
                calendar.setSelectedDate(QDate(year, month, day))
            except:
                pass
        
        layout.addWidget(calendar)
        
        btn_layout = QHBoxLayout()
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(lambda: self.on_range_calendar_selected(which, calendar.selectedDate(), dialog))
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(select_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec()

    def on_range_calendar_selected(self, which, qdate, dialog):
        """Handle range date selection"""
        date_str = qdate.toString("yyyy-MM-dd")
        combo = self.start_date_combo if which == 'start' else self.end_date_combo
        if date_str in [combo.itemText(i) for i in range(combo.count())]:
            combo.setCurrentText(date_str)
        dialog.accept()

    def update_time_range_display(self):
        """Update the time range display label"""
        start = self.time_filter_start.currentText()
        end = self.time_filter_end.currentText()
        self.time_range_display.setText(f"{start} to {end}")
    
    def create_time_validator(self):
        """Create validator for time input (HH:MM format)"""
       
        
        # Accept HH:MM where HH=00-23, MM=00-59
        pattern = QRegularExpression(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$")
        return QRegularExpressionValidator(pattern)

    def open_range_calendar(self, which):
        """Open calendar for range selection (start or end) - black and white"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Select {which.capitalize()} Date")
        dialog.setFixedSize(300, 250)
            
        layout = QVBoxLayout(dialog)
        
        calendar = QCalendarWidget()
        calendar.setGridVisible(False)
        # BLACK AND WHITE - minimal styling
        calendar.setStyleSheet("""
            QCalendarWidget {
                border: 1px solid #ccc;
                background-color: white;
            }
            /* Main table view - ALL BLACK TEXT */
            QCalendarWidget QTableView {
                background-color: white;
                alternate-background-color: white;
            }
            /* ALL DAYS - black text, white background */
            QCalendarWidget QTableView::item {
                color: black;
                background-color: white;
                border: none;
            }
            /* WEEKEND DAYS - also black */
            QCalendarWidget QTableView::item:!selected {
                color: black;
                background-color: white;
            }
            /* SELECTED DAY - light gray border */
            QCalendarWidget QTableView::item:selected {
                background-color: white;
                color: black;
                border: 2px solid #888888;  /* Light gray border */
                border-radius: 3px;
            }
            /* CURRENT DAY - same as others, no blue circle */
            QCalendarWidget QTableView::item:enabled:focus {
                background-color: white;
                color: black;
            }
            /* Header (month/year) */
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: white;
                border-bottom: 1px solid #ccc;
            }
            /* Tool buttons */
            QCalendarWidget QToolButton {
                background-color: white;
                border: 1px solid #ccc;
                color: black;
                border-radius: 2px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #f5f5f5;
            }
            /* Spin boxes */
            QCalendarWidget QSpinBox {
                background-color: white;
                border: 1px solid #ccc;
                color: black;
            }
            /* Dropdown menu */
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #ccc;
                color: black;
            }
        """)
        
        # Set current selection
        combo = self.start_date_combo if which == 'start' else self.end_date_combo
        current_date = combo.currentText()
        if current_date:
            try:
                year, month, day = map(int, current_date.split('-'))
                calendar.setSelectedDate(QDate(year, month, day))
            except:
                pass
        
        layout.addWidget(calendar)
        
        btn_layout = QHBoxLayout()
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(lambda: self.on_range_calendar_selected(which, calendar.selectedDate(), dialog))
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(select_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec()
    def on_calendar_date_selected(self, qdate, dialog):
        """Handle date selection from calendar"""
        date_str = qdate.toString("yyyy-MM-dd")
        if date_str in [self.date_combo.itemText(i) for i in range(self.date_combo.count())]:
            self.date_combo.setCurrentText(date_str)
        dialog.accept()

    def set_time(self, time_str):
        """Set time from quick buttons"""
        self.time_combo.setCurrentText(time_str)
        if self.time_combo.lineEdit():
            self.time_combo.lineEdit().setText(time_str)
    
    def open_calendar_picker(self):
        """Open a calendar dialog for date selection - black and white"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Date")
        dialog.setFixedSize(300, 250)
        
        layout = QVBoxLayout(dialog)
        
        calendar = QCalendarWidget()
        calendar.setGridVisible(False)
        # BLACK AND WHITE - minimal styling
        calendar.setStyleSheet("""
            QCalendarWidget {
                border: 1px solid #ccc;
                background-color: white;
            }
            /* Main table view - ALL BLACK TEXT */
            QCalendarWidget QTableView {
                background-color: white;
                alternate-background-color: white;
            }
            /* ALL DAYS - black text, white background */
            QCalendarWidget QTableView::item {
                color: black;
                background-color: white;
                border: none;
            }
            /* WEEKEND DAYS - also black */
            QCalendarWidget QTableView::item:!selected {
                color: black;
                background-color: white;
            }
            /* SELECTED DAY - light gray border */
            QCalendarWidget QTableView::item:selected {
                background-color: white;
                color: black;
                border: 2px solid #888888;  /* Light gray border */
                border-radius: 3px;
            }
            /* CURRENT DAY - same as others, no blue circle */
            QCalendarWidget QTableView::item:enabled:focus {
                background-color: white;
                color: black;
            }
            /* Header (month/year) */
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: white;
                border-bottom: 1px solid #ccc;
            }
            /* Tool buttons */
            QCalendarWidget QToolButton {
                background-color: white;
                border: 1px solid #ccc;
                color: black;
                border-radius: 2px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #f5f5f5;
            }
            /* Spin boxes */
            QCalendarWidget QSpinBox {
                background-color: white;
                border: 1px solid #ccc;
                color: black;
            }
            /* Dropdown menu */
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #ccc;
                color: black;
            }
        """)
        
        # Try to set to current selection
        current_date = self.date_combo.currentText()
        if current_date:
            try:
                year, month, day = map(int, current_date.split('-'))
                calendar.setSelectedDate(QDate(year, month, day))
            except:
                pass
        
        layout.addWidget(calendar)
        
        btn_layout = QHBoxLayout()
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(lambda: self.on_calendar_date_selected(calendar.selectedDate(), dialog))
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(select_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec()