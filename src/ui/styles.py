"""
ECOSURF Global Styles - Professional Blue Theme
All colors unified to blue palette
"""

COLORS = {
    'bg': '#F5F6F7',
    'surface': '#FFFFFF',
    'sidebar': '#2C3E50',
    'header': '#34495E',
    'primary': '#3498DB',
    'primary_hover': '#2980B9',
    'primary_dark': '#1F6DA8',
    'secondary': '#5DADE2',
    'success': '#27AE60',
    'danger': '#E74C3C',
    'text': '#2C3E50',
    'text_secondary': '#7F8C8D',
    'text_light': '#ECF0F1',
    'border': '#E0E0E0',
    'border_dark': '#BDC3C7',
    'card_bg': '#FAFBFC',
    'info_bg': '#EBF5FB',
    'info_border': '#AED6F1',
}

GLOBAL_STYLE = """
QMainWindow {
    background-color: #F5F6F7;
}

QWidget {
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 12px;
}

QLabel {
    color: #2C3E50;
}

/* Buttons - Primary Blue */
QPushButton {
    background-color: #ECF0F1;
    color: #2C3E50;
    border: 1px solid #BDC3C7;
    border-radius: 4px;
    padding: 6px 14px;
    font-size: 12px;
    min-height: 28px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #EBF5FB;
    border-color: #3498DB;
    color: #3498DB;
}

QPushButton:pressed {
    background-color: #D4E6F1;
}

QPushButton:disabled {
    background-color: #ECF0F1;
    color: #BDC3C7;
}

QPushButton[primary="true"] {
    background-color: #3498DB;
    color: white;
    border: none;
    font-weight: 600;
}

QPushButton[primary="true"]:hover {
    background-color: #2980B9;
}

QPushButton[primary="true"]:pressed {
    background-color: #1F6DA8;
}

QPushButton[success="true"] {
    background-color: #27AE60;
    color: white;
    border: none;
}

QPushButton[success="true"]:hover {
    background-color: #229954;
}

QPushButton[danger="true"] {
    background-color: #E74C3C;
    color: white;
    border: none;
}

QPushButton[danger="true"]:hover {
    background-color: #C0392B;
}

/* Input Fields */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: white;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 28px;
    color: #2C3E50;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #3498DB;
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

/* Sliders - Blue */
QSlider::groove:horizontal {
    border: none;
    height: 4px;
    background: #E0E0E0;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #3498DB;
    border: none;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #2980B9;
}

QSlider::sub-page:horizontal {
    background: #3498DB;
    border-radius: 2px;
}

/* Checkboxes - Blue */
QCheckBox {
    color: #2C3E50;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #BDC3C7;
    border-radius: 4px;
    background: white;
}

QCheckBox::indicator:hover {
    border-color: #3498DB;
}

QCheckBox::indicator:checked {
    background: #3498DB;
    border-color: #3498DB;
}

/* Radio Buttons - Blue */
QRadioButton {
    color: #2C3E50;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #BDC3C7;
    border-radius: 9px;
    background: white;
}

QRadioButton::indicator:hover {
    border-color: #3498DB;
}

QRadioButton::indicator:checked {
    background: #3498DB;
    border: 4px solid white;
    outline: 2px solid #3498DB;
}

/* Group Boxes */
QGroupBox {
    font-weight: 600;
    font-size: 11px;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    margin-top: 12px;
    padding: 12px 8px 8px 8px;
    background-color: #FAFBFC;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #2C3E50;
    background-color: white;
}

/* Scroll Bars - Subtle Blue */
QScrollBar:vertical {
    border: none;
    background: #F5F6F7;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #BDC3C7;
    min-height: 30px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #3498DB;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    border: none;
    background: #F5F6F7;
    height: 10px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #BDC3C7;
    min-width: 30px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal:hover {
    background: #3498DB;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* List Widget - Blue Selection */
QListWidget {
    background-color: white;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    outline: none;
}

QListWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #F5F6F7;
}

QListWidget::item:selected {
    background-color: #3498DB;
    color: white;
}

QListWidget::item:hover:!selected {
    background-color: #EBF5FB;
}

/* Progress Bar - Blue */
QProgressBar {
    border: none;
    background: #E0E0E0;
    height: 6px;
    border-radius: 3px;
}

QProgressBar::chunk {
    background: #3498DB;
    border-radius: 3px;
}

/* Tab Widget - Clean Blue Accent */
QTabWidget::pane {
    border: 1px solid #E0E0E0;
    background: white;
    border-radius: 4px;
}

QTabBar::tab {
    background: #ECF0F1;
    border: 1px solid #E0E0E0;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-weight: 500;
}

QTabBar::tab:selected {
    background: white;
    border-bottom: 2px solid #3498DB;
    font-weight: 600;
    color: #3498DB;
}

QTabBar::tab:hover:!selected {
    background: #EBF5FB;
}

/* Splitter */
QSplitter::handle {
    background: #E0E0E0;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

/* Tooltips - Dark Blue */
QToolTip {
    background: #2C3E50;
    color: white;
    border: none;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 11px;
}

/* Date Time Edit */
QDateTimeEdit {
    background: white;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 28px;
}

QDateTimeEdit:focus {
    border-color: #3498DB;
}

QDateTimeEdit::drop-down {
    border: none;
    width: 24px;
}

/* Calendar Widget */
QCalendarWidget {
    background: white;
}

QCalendarWidget QToolButton {
    color: #2C3E50;
    background: transparent;
    border: none;
    border-radius: 4px;
    padding: 6px;
}

QCalendarWidget QToolButton:hover {
    background: #EBF5FB;
}

QCalendarWidget QTableView {
    selection-background-color: #3498DB;
    selection-color: white;
}
"""

SIDEBAR_STYLE = """
QFrame#sidebar {
    background-color: #2C3E50;
    border: none;
}

QListWidget#nav {
    background-color: transparent;
    border: none;
    outline: none;
    color: #ECF0F1;
    font-size: 12px;
}

QListWidget#nav::item {
    padding: 14px 16px;
    border: none;
    border-left: 3px solid transparent;
    margin: 1px 0;
}

QListWidget#nav::item:selected {
    background-color: rgba(52, 152, 219, 0.3);
    border-left: 3px solid #3498DB;
    color: white;
    font-weight: 500;
}

QListWidget#nav::item:hover:!selected {
    background-color: rgba(255, 255, 255, 0.08);
}

QLabel#logo {
    color: #ECF0F1;
    font-size: 16px;
    font-weight: bold;
    padding: 16px;
}

QLabel#version {
    color: #7F8C8D;
    font-size: 10px;
    padding: 0 16px 8px 16px;
}
"""

HEADER_STYLE = """
QFrame#header {
    background-color: #34495E;
    border: none;
    min-height: 40px;
    max-height: 40px;
}

QLabel#header_text {
    color: #ECF0F1;
    font-size: 12px;
    padding: 0 12px;
}

QLabel#header_file {
    color: #BDC3C7;
    font-size: 11px;
}

QLabel#status_dot {
    color: #27AE60;
    font-size: 14px;
}

QPushButton#header_btn {
    background: transparent;
    color: #ECF0F1;
    border: none;
    padding: 8px 12px;
}

QPushButton#header_btn:hover {
    background: rgba(52, 152, 219, 0.3);
}
"""

INSPECTOR_STYLE = """
QFrame#inspector {
    background-color: #FAFAFA;
    border-left: 1px solid #E0E0E0;
}

QLabel#section_title {
    font-weight: 600;
    font-size: 11px;
    color: #2C3E50;
    padding: 8px 0 4px 0;
}

QFrame#section {
    background: white;
    border: 1px solid #E0E0E0;
    border-radius: 6px;
    margin-bottom: 8px;
}

QFrame#section_header {
    background: #F8F9FA;
    border-bottom: 1px solid #E0E0E0;
    padding: 8px 12px;
}

QPushButton#collapse_btn {
    background: transparent;
    border: none;
    color: #7F8C8D;
    font-size: 10px;
    padding: 0;
}
"""

TOOLBAR_STYLE = """
QFrame#toolbar {
    background: rgba(255, 255, 255, 0.95);
    border: 1px solid #E0E0E0;
    border-radius: 4px;
}

QPushButton#tool_btn {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    min-width: 28px;
    max-width: 28px;
    min-height: 28px;
    max-height: 28px;
    font-size: 14px;
    color: #2C3E50;
}

QPushButton#tool_btn:hover {
    background: #EBF5FB;
    border-color: #3498DB;
}

QPushButton#tool_btn:pressed {
    background: #D4E6F1;
}
"""

# Panel style for all right-side panels
PANEL_STYLE = """
QWidget {
    font-family: 'Segoe UI', sans-serif;
    font-size: 12px;
    color: #2C3E50;
    background: white;
}

QLabel#header {
    font-size: 13px;
    font-weight: 600;
    color: #2C3E50;
    padding: 8px 0;
    border-bottom: 2px solid #3498DB;
    margin-bottom: 8px;
}

QFrame#card {
    background: #FAFBFC;
    border: 1px solid #E8E8E8;
    border-radius: 8px;
    padding: 12px;
}

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

QPushButton#toggle_btn:checked {
    background: #3498DB;
    color: white;
    border-color: #2980B9;
}

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

QPushButton#primary_btn:disabled {
    background: #BDC3C7;
}

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

QFrame#info_card {
    background: #EBF5FB;
    border: 1px solid #AED6F1;
    border-radius: 6px;
    padding: 10px;
}

QLabel#info_text {
    font-size: 11px;
    color: #2471A3;
}

QLabel#status {
    font-size: 11px;
    color: #7F8C8D;
}

QLabel#status_success {
    font-size: 11px;
    color: #27AE60;
}
"""
