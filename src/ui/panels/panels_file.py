"""
File Management Panel - With Scrollbar
Handles file loading from period dictionary or traditional file/folder selection
WITH SEARCH SCOPE SELECTION
"""
import os
import re
import pickle
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, 
    QGroupBox, QScrollArea, QComboBox, QHBoxLayout, QMessageBox,
    QLineEdit, QRadioButton
)
from PyQt6.QtCore import pyqtSignal, Qt
import soundfile as sf

from ui.dialogs.period_selection import PeriodSelectionDialog


class FilePanel(QWidget):
    file_loaded = pyqtSignal(str, tuple)  # file_path, time_range
    folder_loaded = pyqtSignal(list)  # list of file paths
    period_dict_loaded = pyqtSignal(dict)  # Emit period dictionary for fast search
    search_scope_changed = pyqtSignal(str, list)  # NEW: scope_type, file_list
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.file_list = []
        self.period_dict = {}
        self.unique_dates = []
        self.date_to_times = {}
        self.period_file_path = ""
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
        
        # ========= PERIOD DICTIONARY SECTION =========
        period_group = QGroupBox("🗓️ Period Dictionary Selection")
        period_layout = QVBoxLayout()
        
        # Load period dictionary button
        load_dict_btn = QPushButton("📁 Load Period Dictionary (.pkl)")
        load_dict_btn.clicked.connect(self.load_period_dict_file)  # THIS METHOD MUST EXIST
        load_dict_btn.setMinimumHeight(35)
        load_dict_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        period_layout.addWidget(load_dict_btn)
        
        # Dictionary info
        self.dict_info_label = QLabel("No period dictionary loaded")
        self.dict_info_label.setWordWrap(True)
        self.dict_info_label.setStyleSheet(
            "padding: 6px; background-color: #e8f5e8; "
            "border-radius: 4px; font-size: 10px;"
        )
        period_layout.addWidget(self.dict_info_label)
        
        period_group.setLayout(period_layout)
        layout.addWidget(period_group)
        
        # ========= DISPLAY SELECTION =========
        display_group = QGroupBox("📺 What to Display")
        display_layout = QVBoxLayout()
        
        # Display source selection (File vs Database)
        source_layout = QHBoxLayout()
        self.display_source_file = QRadioButton("From Local File")
        self.display_source_db = QRadioButton("From Database")
        self.display_source_db.setChecked(True)
        source_layout.addWidget(self.display_source_db)
        source_layout.addWidget(self.display_source_file)
        display_layout.addLayout(source_layout)
        
        # ===== SINGLE FILE SELECTION =====
        single_group = QGroupBox("🎯 Specific 1-Minute File")
        single_layout = QVBoxLayout()
        
        # Date-Time selection
        dt_layout = QHBoxLayout()
        dt_layout.addWidget(QLabel("Date:"))
        
        self.date_combo = QComboBox()
        self.date_combo.addItem("Load dictionary first")
        self.date_combo.setEnabled(False)
        self.date_combo.currentTextChanged.connect(self.on_date_selected)
        dt_layout.addWidget(self.date_combo, stretch=2)
        
        dt_layout.addWidget(QLabel("Time:"))
        
        self.time_combo = QComboBox()
        self.time_combo.addItem("Select date")
        self.time_combo.setEnabled(False)
        dt_layout.addWidget(self.time_combo, stretch=2)
        
        single_layout.addLayout(dt_layout)
        
        # Load single file button
        self.load_single_btn = QPushButton("🎵 Load & Display This File")
        self.load_single_btn.clicked.connect(self.load_specific_file)
        self.load_single_btn.setMinimumHeight(35)
        self.load_single_btn.setEnabled(False)
        single_layout.addWidget(self.load_single_btn)
        
        single_group.setLayout(single_layout)
        display_layout.addWidget(single_group)
        
        # ===== DATE RANGE SELECTION =====
        range_group = QGroupBox("📅 Date Range (Display First File)")
        range_layout = QVBoxLayout()
        
        # Range selection
        range_hlayout = QHBoxLayout()
        range_hlayout.addWidget(QLabel("From:"))
        
        self.start_date_combo = QComboBox()
        self.start_date_combo.addItem("Load dictionary first")
        self.start_date_combo.setEnabled(False)
        range_hlayout.addWidget(self.start_date_combo, stretch=1)
        
        range_hlayout.addWidget(QLabel("To:"))
        
        self.end_date_combo = QComboBox()
        self.end_date_combo.addItem("Load dictionary first")
        self.end_date_combo.setEnabled(False)
        range_hlayout.addWidget(self.end_date_combo, stretch=1)
        
        range_layout.addLayout(range_hlayout)
        
        # Time of day filter (optional)
        time_filter_layout = QHBoxLayout()
        time_filter_layout.addWidget(QLabel("Time filter:"))
        
        self.time_filter_start = QComboBox()
        self.time_filter_start.addItems([f"{h:02d}:00" for h in range(24)])
        self.time_filter_start.setEnabled(False)
        time_filter_layout.addWidget(self.time_filter_start)
        
        time_filter_layout.addWidget(QLabel("to"))
        
        self.time_filter_end = QComboBox()
        self.time_filter_end.addItems([f"{h:02d}:59" for h in range(24)])
        self.time_filter_end.setCurrentIndex(23)
        self.time_filter_end.setEnabled(False)
        time_filter_layout.addWidget(self.time_filter_end)
        
        range_layout.addLayout(time_filter_layout)
        
        # Load range button
        self.load_range_btn = QPushButton("📊 Display First File in Range")
        self.load_range_btn.clicked.connect(self.load_date_range)
        self.load_range_btn.setMinimumHeight(35)
        self.load_range_btn.setEnabled(False)
        range_layout.addWidget(self.load_range_btn)
        
        range_group.setLayout(range_layout)
        display_layout.addWidget(range_group)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        # Connect display source toggles
        self.display_source_db.toggled.connect(self.on_display_source_changed)
        # Initialize display source state
        self.on_display_source_changed(self.display_source_db.isChecked())
        
        # ========= SEARCH SCOPE SELECTION =========
        search_group = QGroupBox("🔍 Where to Search")
        search_layout = QVBoxLayout()
        
        # Radio buttons for search scope
        self.search_scope_db = QRadioButton("🌐 Entire Database")
        self.search_scope_current = QRadioButton("📄 Currently Displayed File Only")
        self.search_scope_period = QRadioButton("📅 Selected Date Range")
        self.search_scope_db.setChecked(True)
        
        search_layout.addWidget(self.search_scope_db)
        search_layout.addWidget(self.search_scope_current)
        search_layout.addWidget(self.search_scope_period)
        
        # Search period selection (hidden by default)
        search_period_widget = QWidget()
        search_period_layout = QVBoxLayout(search_period_widget)
        
        # Date range for search
        search_range_layout = QHBoxLayout()
        search_range_layout.addWidget(QLabel("Search from:"))
        
        self.search_start_date_combo = QComboBox()
        self.search_start_date_combo.addItem("Load dictionary first")
        self.search_start_date_combo.setEnabled(False)
        search_range_layout.addWidget(self.search_start_date_combo)
        
        search_range_layout.addWidget(QLabel("to"))
        
        self.search_end_date_combo = QComboBox()
        self.search_end_date_combo.addItem("Load dictionary first")
        self.search_end_date_combo.setEnabled(False)
        search_range_layout.addWidget(self.search_end_date_combo)
        
        search_period_layout.addLayout(search_range_layout)
        
        # Time filter for search
        search_time_layout = QHBoxLayout()
        search_time_layout.addWidget(QLabel("Time:"))
        
        self.search_time_start_combo = QComboBox()
        self.search_time_start_combo.addItems([f"{h:02d}:00" for h in range(24)])
        self.search_time_start_combo.setEnabled(False)
        search_time_layout.addWidget(self.search_time_start_combo)
        
        search_time_layout.addWidget(QLabel("to"))
        
        self.search_time_end_combo = QComboBox()
        self.search_time_end_combo.addItems([f"{h:02d}:59" for h in range(24)])
        self.search_time_end_combo.setCurrentIndex(23)
        self.search_time_end_combo.setEnabled(False)
        search_time_layout.addWidget(self.search_time_end_combo)
        
        search_period_layout.addLayout(search_time_layout)
        
        search_period_widget.setVisible(False)  # Hidden by default
        search_layout.addWidget(search_period_widget)
        
        # Update search scope button
        update_scope_btn = QPushButton("🔄 Update Search Scope")
        update_scope_btn.clicked.connect(self.update_search_scope)
        update_scope_btn.setMinimumHeight(30)
        update_scope_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
            }
        """)
        search_layout.addWidget(update_scope_btn)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Store references
        self.search_period_widget = search_period_widget
        
        # Connect signals
        self.search_scope_db.toggled.connect(self.on_search_scope_changed)
        self.search_scope_current.toggled.connect(self.on_search_scope_changed)
        self.search_scope_period.toggled.connect(self.on_search_scope_changed)
        
        # ========= TRADITIONAL METHOD =========
        trad_group = QGroupBox("📂 Traditional Method")
        trad_layout = QVBoxLayout()
        
        load_btn = QPushButton("📂 Load Audio File (Traditional)")
        load_btn.clicked.connect(self.load_file)
        load_btn.setMinimumHeight(35)
        trad_layout.addWidget(load_btn)
        
        load_folder_btn = QPushButton("📁 Load Folder (Traditional)")
        load_folder_btn.clicked.connect(self.load_folder)
        load_folder_btn.setMinimumHeight(35)
        trad_layout.addWidget(load_folder_btn)
        
        trad_group.setLayout(trad_layout)
        layout.addWidget(trad_group)
        
        # ========= RESET =========
        reset_btn = QPushButton("🔄 Reset All")
        reset_btn.clicked.connect(self.reset_application)
        reset_btn.setMinimumHeight(35)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        layout.addWidget(reset_btn)
        
        # ========= FILE INFO =========
        info_group = QGroupBox("📄 Current File")
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
        
        # ========= SEARCH SCOPE INFO =========
        scope_info_group = QGroupBox("🔍 Search Scope Info")
        scope_info_layout = QVBoxLayout()
        
        self.scope_info_label = QLabel("Search scope: Entire database")
        self.scope_info_label.setWordWrap(True)
        self.scope_info_label.setStyleSheet(
            "padding: 8px; background-color: #e3f2fd; "
            "border-radius: 5px; font-size: 11px;"
        )
        scope_info_layout.addWidget(self.scope_info_label)
        
        scope_info_group.setLayout(scope_info_layout)
        layout.addWidget(scope_info_group)
        
        # ========= FOLDER INFO =========
        folder_group = QGroupBox("📁 Folder Info")
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
        
        # Initialize search scope
        self.update_search_scope()
    
    # ========= PERIOD DICTIONARY METHODS =========
    
    def find_period_pkl(self):
        """Find period_locations.pkl file in common locations"""
        possible_paths = [
            os.path.join('data', 'pre_processing_data', 'period_locations.pkl'),
            os.path.join('..', 'data', 'pre_processing_data', 'period_locations.pkl'),
            'period_locations.pkl',
            os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'pre_processing_data', 'period_locations.pkl')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        
        return None
    
    def load_period_dict_file(self):
        """Load period dictionary from .pkl file"""
        # First try to auto-find
        auto_path = self.find_period_pkl()
        
        if auto_path:
            self.period_file_path = auto_path
        else:
            # Let user select file
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Open Period Dictionary", 
                "", 
                "Pickle Files (*.pkl);;JSON Files (*.json);;All Files (*)"
            )
            if not file_path:
                return
            self.period_file_path = file_path
        
        try:
            if self.period_file_path.endswith('.pkl'):
                with open(self.period_file_path, 'rb') as f:
                    self.period_dict = pickle.load(f)
            elif self.period_file_path.endswith('.json'):
                with open(self.period_file_path, 'r') as f:
                    self.period_dict = json.load(f)
            else:
                QMessageBox.warning(self, "Format Error", "Unsupported file format")
                return
                
            # Process the dictionary
            self.process_period_dict()
            
            # Update UI
            self.update_dict_info()
            self.enable_period_widgets()
            
            # Emit signal for other panels (e.g., search panel)
            self.period_dict_loaded.emit(self.period_dict)
            
            QMessageBox.information(self, "Success", 
                                  f"Loaded {len(self.period_dict)} period entries")
            
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load dictionary:\n{str(e)}")
            self.period_dict = {}
    
    def process_period_dict(self):
        """Process period dictionary for UI display"""
        self.unique_dates = sorted(list(set(
            k.split('_')[0] for k in self.period_dict.keys()
        )))
        
        # Group times by date for quick lookup
        self.date_to_times = {}
        for period_key in self.period_dict.keys():
            date_str, time_str = period_key.split('_')
            if date_str not in self.date_to_times:
                self.date_to_times[date_str] = []
            # Keep only hour:minute
            time_short = time_str[:5]  # "HH:MM"
            if time_short not in self.date_to_times[date_str]:
                self.date_to_times[date_str].append(time_short)
        
        # Sort times for each date
        for date in self.date_to_times:
            self.date_to_times[date].sort()
    
    def update_dict_info(self):
        """Update dictionary info label"""
        if self.period_dict:
            date_range = f"{self.unique_dates[0]} to {self.unique_dates[-1]}"
            total_files = len(self.period_dict)
            self.dict_info_label.setText(
                f"✅ Loaded: {total_files:,} files\n"
                f"📅 Date range: {date_range}\n"
                f"📁 Source: {os.path.basename(self.period_file_path)}"
            )
        else:
            self.dict_info_label.setText("❌ No period dictionary loaded")
    
    def on_date_selected(self, date_str):
        """Update time combobox when date is selected"""
        if date_str in self.date_to_times:
            self.time_combo.setEnabled(True)
            self.time_combo.clear()
            self.time_combo.addItems(self.date_to_times[date_str])
        else:
            self.time_combo.setEnabled(False)
            self.time_combo.clear()
            self.time_combo.addItem("No files for this date")
    
    # ========= SEARCH SCOPE METHODS =========
    
    def on_search_scope_changed(self):
        """Show/hide search period widgets based on scope selection"""
        if self.search_scope_period.isChecked():
            self.search_period_widget.setVisible(True)
        else:
            self.search_period_widget.setVisible(False)

    def on_display_source_changed(self, checked):
        """Enable database selection widgets only when 'From Database' is selected."""
        use_db = bool(checked) if isinstance(checked, bool) else self.display_source_db.isChecked()
        # Enable/disable date/time combos and load buttons
        self.date_combo.setEnabled(use_db and bool(self.period_dict))
        self.time_combo.setEnabled(use_db and bool(self.period_dict))
        self.start_date_combo.setEnabled(use_db and bool(self.period_dict))
        self.end_date_combo.setEnabled(use_db and bool(self.period_dict))
        self.time_filter_start.setEnabled(use_db and bool(self.period_dict))
        self.time_filter_end.setEnabled(use_db and bool(self.period_dict))
        self.load_single_btn.setEnabled(use_db and bool(self.period_dict))
        self.load_range_btn.setEnabled(use_db and bool(self.period_dict))
        # If using local file, hint user to use traditional load
        if not use_db:
            self.file_label.setText("Using local file mode — use 'Load Audio File (Traditional)'.")
    
    def update_search_scope(self):
        """Update search scope and emit signal"""
        scope_type, file_list = self.get_search_scope()
        
        # Update scope info label
        scope_text = {
            "database": "🌐 Entire database",
            "current": "📄 Currently displayed file only",
            "period": "📅 Selected date range"
        }
        self.scope_info_label.setText(
            f"<b>Search scope:</b> {scope_text.get(scope_type, 'Unknown')}<br>"
            f"<b>Files to search:</b> {len(file_list):,}"
        )
        
        # Emit signal
        self.search_scope_changed.emit(scope_type, file_list)
    
    def get_search_scope(self):
        """
        Get the search scope and file list for searching
        Returns: (scope_type, file_list)
        """
        if self.search_scope_current.isChecked():
            # Search only in currently displayed file
            if self.current_file:
                return ("current", [self.current_file])
            else:
                return ("current", [])
        
        elif self.search_scope_period.isChecked():
            # Search in selected date range
            start_date = self.search_start_date_combo.currentText()
            end_date = self.search_end_date_combo.currentText()
            time_start = self.search_time_start_combo.currentText()
            time_end = self.search_time_end_combo.currentText()
            
            if not self.period_dict or not start_date or not end_date:
                return ("period", [])
            
            # Filter period dictionary for search
            search_files = self.filter_period_dict_for_search(
                start_date, end_date, time_start, time_end
            )
            return ("period", search_files)
        
        else:  # search_scope_db.isChecked()
            # Search entire database
            if self.period_dict:
                # Return all S3 paths from period dictionary
                all_files = []
                for info in self.period_dict.values():
                    s3_path = info.get('s3_uri', '').replace('s3://ecosurf-dataset/', '')
                    if s3_path:
                        all_files.append(s3_path)
                return ("database", all_files)
            else:
                # Fallback to traditional file list
                return ("database", self.file_list)
    
    def filter_period_dict_for_search(self, start_date, end_date, time_start, time_end):
        """Filter period dictionary for search based on date/time range"""
        search_files = []
        time_start_min = self.time_to_minutes(time_start)
        time_end_min = self.time_to_minutes(time_end)
        
        for period_key, file_info in self.period_dict.items():
            file_date, file_time = period_key.split('_')
            file_hour_min = file_time[:5]  # "HH:MM"
            file_time_min = self.time_to_minutes(file_hour_min)
            
            # Check date range
            if start_date <= file_date <= end_date:
                # Check time filter
                if time_start_min <= file_time_min <= time_end_min:
                    s3_path = file_info.get('s3_uri', '').replace('s3://ecosurf-dataset/', '')
                    if s3_path:
                        search_files.append(s3_path)
        
        return search_files
    
    # ========= EXISTING METHODS (with modifications) =========
    
    def enable_period_widgets(self):
        """Enable period selection widgets"""
        if self.period_dict:
            # Enable display date combos
            self.date_combo.setEnabled(True)
            self.date_combo.clear()
            self.date_combo.addItems(self.unique_dates)
            
            self.start_date_combo.setEnabled(True)
            self.start_date_combo.clear()
            self.start_date_combo.addItems(self.unique_dates)
            
            self.end_date_combo.setEnabled(True)
            self.end_date_combo.clear()
            self.end_date_combo.addItems(self.unique_dates)
            if self.unique_dates:
                self.end_date_combo.setCurrentIndex(len(self.unique_dates)-1)
            
            # Enable display time filter combos
            self.time_filter_start.setEnabled(True)
            self.time_filter_end.setEnabled(True)
            
            # Enable search date combos
            self.search_start_date_combo.setEnabled(True)
            self.search_start_date_combo.clear()
            self.search_start_date_combo.addItems(self.unique_dates)
            
            self.search_end_date_combo.setEnabled(True)
            self.search_end_date_combo.clear()
            self.search_end_date_combo.addItems(self.unique_dates)
            if self.unique_dates:
                self.search_end_date_combo.setCurrentIndex(len(self.unique_dates)-1)
            
            # Enable search time filter combos
            self.search_time_start_combo.setEnabled(True)
            self.search_time_end_combo.setEnabled(True)
            
            # Enable buttons
            self.load_single_btn.setEnabled(True)
            self.load_range_btn.setEnabled(True)
            
            # Update search scope
            self.update_search_scope()
    
    def load_specific_file(self):
        """Load a specific 1-minute file based on date/time selection"""
        date = self.date_combo.currentText()
        time = self.time_combo.currentText()
        
        if not date or not time or time == "No files for this date":
            QMessageBox.warning(self, "Selection Error", "Please select valid date and time")
            return
        
        # Format period key
        period_key = f"{date}_{time}:00"  # Add :00 for seconds
        
        if period_key in self.period_dict:
            file_info = self.period_dict[period_key]
            s3_path = file_info.get('s3_uri', '').replace("s3://ecosurf-dataset/", "")
            
            # TODO: Implement actual S3 download logic here
            local_path = self.download_from_s3_or_use_local(s3_path, period_key)
            
            if local_path and os.path.exists(local_path):
                # Default 1-minute time range
                time_range = (0.0, 60.0)
                
                # Update current file
                self.current_file = local_path
                
                # Update file label
                self.file_label.setText(
                    f"<b>File:</b> {period_key}<br>"
                    f"<b>Device:</b> {file_info.get('device', 'N/A')}<br>"
                    f"<b>Time:</b> {time}<br>"
                    f"<b>Path:</b> {s3_path}<br>"
                    f"<b>Size:</b> {file_info.get('size_mb', 0):.1f} MB"
                )
                
                # Emit signal
                self.file_loaded.emit(local_path, time_range)
                
                # Update search scope if "current file" is selected
                if self.search_scope_current.isChecked():
                    self.update_search_scope()
                
                QMessageBox.information(self, "File Loaded", 
                                      f"Loaded {period_key}\nDevice: {file_info.get('device', 'N/A')}")
            else:
                QMessageBox.critical(self, "Download Error", 
                                   f"Could not download file from S3:\n{s3_path}")
        else:
            # Try without seconds
            period_key_no_sec = f"{date}_{time}"
            if period_key_no_sec in self.period_dict:
                self.load_specific_file_with_key(period_key_no_sec)
            else:
                QMessageBox.warning(self, "Not Found", 
                                  f"File not found in dictionary: {period_key}")
    
    def load_specific_file_with_key(self, period_key):
        """Helper to load file with given period key"""
        file_info = self.period_dict[period_key]
        s3_path = file_info.get('s3_uri', '').replace("s3://ecosurf-dataset/", "")
        
        # TODO: Implement S3 download
        local_path = self.download_from_s3_or_use_local(s3_path, period_key)
        
        if local_path and os.path.exists(local_path):
            time_range = (0.0, 60.0)
            self.current_file = local_path
            
            self.file_label.setText(
                f"<b>File:</b> {period_key}<br>"
                f"<b>Device:</b> {file_info.get('device', 'N/A')}<br>"
                f"<b>Path:</b> {s3_path}"
            )
            
            self.file_loaded.emit(local_path, time_range)
            
            # Update search scope if "current file" is selected
            if self.search_scope_current.isChecked():
                self.update_search_scope()
    
    def load_date_range(self):
        """Load files for a date range with optional time filter"""
        start_date = self.start_date_combo.currentText()
        end_date = self.end_date_combo.currentText()
        time_start = self.time_filter_start.currentText()
        time_end = self.time_filter_end.currentText()
        
        if not start_date or not end_date:
            QMessageBox.warning(self, "Selection Error", "Please select start and end dates")
            return
        
        # Find all files in date range
        range_files = []
        for period_key, file_info in self.period_dict.items():
            file_date, file_time = period_key.split('_')
            file_hour_min = file_time[:5]  # "HH:MM"
            file_time_min = self.time_to_minutes(file_hour_min)
            
            # Check date range
            if start_date <= file_date <= end_date:
                # Check time filter if enabled
                time_start_min = self.time_to_minutes(time_start)
                time_end_min = self.time_to_minutes(time_end)
                if time_start_min <= file_time_min <= time_end_min:
                    range_files.append((period_key, file_info))
        
        if range_files:
            # For now, just load the first file in range
            first_key, first_info = range_files[0]
            
            self.file_label.setText(
                f"<b>Range Selected:</b> {start_date} to {end_date}<br>"
                f"<b>Time filter:</b> {time_start} to {time_end}<br>"
                f"<b>Files in range:</b> {len(range_files):,}<br>"
                f"<b>First file:</b> {first_key}"
            )
            
            # Prepare list of files (try local download, otherwise provide S3 path)
            files_to_emit = []
            for key, info in range_files:
                s3_path = info.get('s3_uri', '').replace('s3://ecosurf-dataset/', '')
                local = self.download_from_s3_or_use_local(s3_path, key)
                files_to_emit.append(local if (local and os.path.exists(local)) else s3_path)

            # Load the first file locally if possible, else attempt via key
            try:
                self.load_specific_file_with_key(first_key)
            except Exception:
                pass

            # Emit folder_loaded so other panels receive the list
            self.folder_loaded.emit(files_to_emit)

            QMessageBox.information(self, "Range Loaded", 
                                  f"Found {len(range_files):,} files in range\n"
                                  f"Loaded first file: {first_key}")
        else:
            QMessageBox.warning(self, "No Files", 
                              f"No files found in range {start_date} to {end_date}")
    
    # ========= UTILITY METHODS =========
    
    def time_to_minutes(self, time_str):
        """Convert HH:MM string to total minutes"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes
        except:
            return 0
    
    def download_from_s3_or_use_local(self, s3_path, period_key):
        """
        TODO: Implement S3 download logic
        For now, returns a placeholder path
        """
        # This is a placeholder - you need to implement actual S3 download
        # or check if file already exists locally
        local_filename = f"{period_key.replace(':', '')}.flac"
        local_path = os.path.join("downloads", local_filename)
        
        # Create downloads directory if it doesn't exist
        os.makedirs("downloads", exist_ok=True)
        
        # Check if file already exists
        if os.path.exists(local_path):
            return local_path
            
        # TODO: Add your S3 download code here using boto3
        # For now, return None to trigger error
        return None
    
    # ========= TRADITIONAL METHODS =========
    
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
        """Traditional: Load a single audio file"""
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
        """Traditional: Load all audio files from a folder"""
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
    
    def update_file_info(self, additional_info):
        """Update file label with additional information"""
        current_text = self.file_label.text()
        self.file_label.setText(f"{current_text}<br>{additional_info}")
    
    # ========= MAINWINDOW INTEGRATION =========
    
    def on_file_loaded(self, file_path, time_range):
        """Called when a file is loaded (for compatibility)"""
        self.current_file = file_path
        # Update search scope if "current file" is selected
        if self.search_scope_current.isChecked():
            self.update_search_scope()
    
    def reset_application(self):
        """Reset all file information"""
        self.current_file = None
        self.file_list = []
        self.period_dict = {}
        self.unique_dates = []
        self.date_to_times = {}
        
        # Reset UI
        self.file_label.setText("No file loaded")
        self.folder_label.setText("No folder loaded")
        self.dict_info_label.setText("No period dictionary loaded")
        self.scope_info_label.setText("Search scope: Entire database")
        
        # Disable period widgets
        self.date_combo.setEnabled(False)
        self.date_combo.clear()
        self.date_combo.addItem("Load dictionary first")
        
        self.time_combo.setEnabled(False)
        self.time_combo.clear()
        self.time_combo.addItem("Select date")
        
        self.start_date_combo.setEnabled(False)
        self.start_date_combo.clear()
        self.start_date_combo.addItem("Load dictionary first")
        
        self.end_date_combo.setEnabled(False)
        self.end_date_combo.clear()
        self.end_date_combo.addItem("Load dictionary first")
        
        self.time_filter_start.setEnabled(False)
        self.time_filter_end.setEnabled(False)
        
        self.search_start_date_combo.setEnabled(False)
        self.search_start_date_combo.clear()
        self.search_start_date_combo.addItem("Load dictionary first")
        
        self.search_end_date_combo.setEnabled(False)
        self.search_end_date_combo.clear()
        self.search_end_date_combo.addItem("Load dictionary first")
        
        self.search_time_start_combo.setEnabled(False)
        self.search_time_end_combo.setEnabled(False)
        
        self.load_single_btn.setEnabled(False)
        self.load_range_btn.setEnabled(False)
        
        # Reset search scope to database
        self.search_scope_db.setChecked(True)
        self.search_period_widget.setVisible(False)
        self.update_search_scope()
        
        QMessageBox.information(self, "Reset", "All file selections have been reset")