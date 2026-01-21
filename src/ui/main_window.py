"""
ECOSURF Main Window - Professional UI
Clean 3-column layout with embedding results panel
"""
import os
import threading
from datetime import datetime

import numpy as np
import librosa
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QListWidget, QStackedWidget, QScrollBar, QPushButton,
    QLabel, QListWidgetItem, QTabWidget, QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from ui.styles import GLOBAL_STYLE, SIDEBAR_STYLE, HEADER_STYLE, INSPECTOR_STYLE
from ui.panels.file_panel_v2 import FilePanel
from ui.panels.spectrogram_panel_v2 import SpectrogramPanel
from ui.panels.view_panel_v2 import ViewPanel
from ui.panels.audio_panel_v2 import AudioPanel
from ui.panels.pattern_panel_v2 import PatternPanel
from ui.panels.search_panel_v2 import SearchPanel
from ui.panels.embedding_panel_v2 import EmbeddingPanel
from ui.components.spectrogram_widget import SpectrogramWidget
from core.embedding_manager import EmbeddingManager


class EmbeddingResultsWidget(QWidget):
    """Embedding search results panel with audio playback"""
    result_clicked = pyqtSignal(int)
    result_play = pyqtSignal(int)
    stop_requested = pyqtSignal()
    show_spectrogram_requested = pyqtSignal(int)
    close_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.results = []
        self.selected_index = -1
        self.init_ui()

    def init_ui(self):
        self.setFixedHeight(140)
        self.setStyleSheet("""
            QWidget {
                background: #FAFBFC;
                border-top: 2px solid #3498DB;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        # Header row with close button
        header_row = QHBoxLayout()

        self.title_label = QLabel("Search Results")
        self.title_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #2C3E50;")
        header_row.addWidget(self.title_label)

        self.count_label = QLabel("0 results")
        self.count_label.setStyleSheet("font-size: 11px; color: #7F8C8D; margin-left: 10px;")
        header_row.addWidget(self.count_label)

        header_row.addStretch()

        # Info label for selected result
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("font-size: 11px; color: #2980B9;")
        header_row.addWidget(self.info_label)

        header_row.addSpacing(20)

        # Play button
        self.play_btn = QPushButton("Play")
        self.play_btn.setFixedSize(60, 26)
        self.play_btn.setEnabled(False)
        self.play_btn.setStyleSheet("""
            QPushButton { background: #27AE60; color: white; border: none; border-radius: 4px; font-weight: 500; }
            QPushButton:hover { background: #229954; }
            QPushButton:disabled { background: #BDC3C7; }
        """)
        self.play_btn.clicked.connect(self.on_play_clicked)
        header_row.addWidget(self.play_btn)

        # Stop button
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFixedSize(60, 26)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton { background: #F39C12; color: white; border: none; border-radius: 4px; font-weight: 500; }
            QPushButton:hover { background: #D68910; }
            QPushButton:disabled { background: #BDC3C7; }
        """)
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        header_row.addWidget(self.stop_btn)

        # Show spectrogram button
        self.show_spec_btn = QPushButton("Spec")
        self.show_spec_btn.setFixedSize(60, 26)
        self.show_spec_btn.setEnabled(False)
        self.show_spec_btn.setStyleSheet("""
            QPushButton { background: #2980B9; color: white; border: none; border-radius: 4px; font-weight: 500; }
            QPushButton:hover { background: #2471A3; }
            QPushButton:disabled { background: #BDC3C7; }
        """)
        self.show_spec_btn.clicked.connect(self.on_show_spec_clicked)
        header_row.addWidget(self.show_spec_btn)

        # Close button
        self.close_btn = QPushButton("X")
        self.close_btn.setFixedSize(32, 26)
        self.close_btn.setStyleSheet("""
            QPushButton { background: #E74C3C; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: #C0392B; }
        """)
        self.close_btn.clicked.connect(self.on_close)
        header_row.addWidget(self.close_btn)

        layout.addLayout(header_row)

        # Scrollable results area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.results_container = QWidget()
        self.results_layout = QHBoxLayout(self.results_container)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(8)
        self.results_layout.addStretch()

        scroll.setWidget(self.results_container)
        layout.addWidget(scroll)

    def show_results(self, results):
        """Display embedding search results"""
        self.clear_results()
        self.results = results

        for i, r in enumerate(results[:20]):
            card = self.create_result_card(i, r)
            self.results_layout.insertWidget(i, card)

        self.count_label.setText(f"{len(results)} results")
        self.title_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #27AE60;")

    def create_result_card(self, index, result):
        """Create a result card with date/time info"""
        card = QFrame()
        card.setFixedSize(150, 70)
        card.setStyleSheet("""
            QFrame { background: white; border: 1px solid #E0E0E0; border-radius: 6px; }
            QFrame:hover { border-color: #3498DB; background: #EBF5FB; }
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(3)

        meta = result['metadata']
        score = result['similarity'] * 100

        # Row 1: Index and score
        top_row = QHBoxLayout()
        idx_label = QLabel(f"#{index+1}")
        idx_label.setStyleSheet("font-size: 11px; font-weight: 600; color: #3498DB;")
        top_row.addWidget(idx_label)
        score_label = QLabel(f"{score:.0f}%")
        score_label.setStyleSheet("font-size: 11px; font-weight: 500; color: #27AE60;")
        top_row.addWidget(score_label)
        top_row.addStretch()
        layout.addLayout(top_row)

        # Row 2: File name (extract date from filename)
        filename = meta.get('file', 'Unknown')
        # Parse date from filename like S4A09154_20190218_163000.flac
        date_str = ""
        if '_' in filename:
            parts = filename.split('_')
            if len(parts) >= 3:
                date_part = parts[1]  # 20190218
                time_part = parts[2].replace('.flac', '')  # 163000
                if len(date_part) == 8 and len(time_part) >= 4:
                    date_str = f"{date_part[6:8]}/{date_part[4:6]}/{date_part[0:4]} {time_part[0:2]}:{time_part[2:4]}"

        if date_str:
            date_label = QLabel(date_str)
            date_label.setStyleSheet("font-size: 10px; color: #2C3E50;")
            layout.addWidget(date_label)
        else:
            file_label = QLabel(filename[:18])
            file_label.setStyleSheet("font-size: 9px; color: #7F8C8D;")
            layout.addWidget(file_label)

        # Row 3: Time range
        start = meta.get('start', 0)
        end = meta.get('end', 0)
        time_label = QLabel(f"Segment: {start:.0f}s - {end:.0f}s")
        time_label.setStyleSheet("font-size: 9px; color: #95A5A6;")
        layout.addWidget(time_label)

        # Click handling
        card.mousePressEvent = lambda e, i=index: self.on_card_clicked(i)
        card.mouseDoubleClickEvent = lambda e, i=index: self.on_card_double_clicked(i)

        return card

    def on_card_clicked(self, index):
        self.selected_index = index
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.show_spec_btn.setEnabled(True)
        if index < len(self.results):
            meta = self.results[index]['metadata']
            self.info_label.setText(f"Selected: {meta.get('file', '')[:25]}")
        self.result_clicked.emit(index)

    def on_card_double_clicked(self, index):
        self.result_play.emit(index)

    def on_play_clicked(self):
        if self.selected_index >= 0:
            self.result_play.emit(self.selected_index)

    def on_stop_clicked(self):
        self.stop_requested.emit()

    def on_show_spec_clicked(self):
        if self.selected_index >= 0:
            self.show_spectrogram_requested.emit(self.selected_index)

    def on_close(self):
        self.setVisible(False)
        self.close_requested.emit()

    def clear_results(self):
        """Clear all results"""
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.results = []
        self.selected_index = -1
        self.count_label.setText("0 results")
        self.info_label.setText("")
        self.play_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.show_spec_btn.setEnabled(False)
        self.title_label.setStyleSheet("font-size: 12px; font-weight: 600; color: #2C3E50;")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "final_icon.png")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("ECOSURF - Bioacoustic Analysis")
        self.setGeometry(50, 50, 1600, 900)
        self.setStyleSheet(GLOBAL_STYLE)

        self.current_file = None
        self.current_time_range = None
        self.audio_data = None
        self.file_list = []
        self.audio_thread = None
        self.playing = False
        self.playing_selection = False
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback_position)
        self.playback_start_time = 0
        self.playback_offset_time = 0
        self.search_results = []
        self.embedding_manager = EmbeddingManager()
        self.perch_model = None
        self.perch_model_loading = False
        self._auto_embedding_search_pending = False
        self._last_nav_index = 0
        self._cluster_dialog = None

        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.header = self.create_header()
        main_layout.addWidget(self.header)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = self.create_sidebar()
        body_layout.addWidget(self.sidebar)

        self.workspace = self.create_workspace()
        body_layout.addWidget(self.workspace, stretch=1)

        self.inspector = self.create_inspector()
        body_layout.addWidget(self.inspector)

        main_layout.addWidget(body, stretch=1)

    def create_header(self):
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(44)
        header.setStyleSheet(HEADER_STYLE)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        logo = QLabel("ECOSURF")
        logo.setObjectName("header_text")
        logo.setStyleSheet("font-weight: bold; font-size: 14px; color: #ECF0F1;")
        layout.addWidget(logo)

        sep1 = QLabel("|")
        sep1.setStyleSheet("color: rgba(255,255,255,0.3);")
        layout.addWidget(sep1)

        self.header_file = QLabel("No file loaded")
        self.header_file.setObjectName("header_file")
        self.header_file.setStyleSheet("color: #BDC3C7; font-size: 11px;")
        layout.addWidget(self.header_file)

        layout.addStretch()

        self.header_status = QLabel("")
        self.header_status.setStyleSheet("color: #27AE60; font-size: 11px;")
        layout.addWidget(self.header_status)

        layout.addSpacing(10)

        # Toggle buttons for panels avec fleches
        self.toggle_sidebar_btn = QPushButton("<< Menu")
        self.toggle_sidebar_btn.setFixedSize(75, 28)
        self.toggle_sidebar_btn.setCheckable(True)
        self.toggle_sidebar_btn.setChecked(True)
        self.toggle_sidebar_btn.setStyleSheet("""
            QPushButton {
                background: #34495E;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover { background: #4A6785; }
            QPushButton:checked { background: #27AE60; }
        """)
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)
        layout.addWidget(self.toggle_sidebar_btn)

        self.toggle_inspector_btn = QPushButton("Panel >>")
        self.toggle_inspector_btn.setFixedSize(75, 28)
        self.toggle_inspector_btn.setCheckable(True)
        self.toggle_inspector_btn.setChecked(True)
        self.toggle_inspector_btn.setStyleSheet("""
            QPushButton {
                background: #34495E;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover { background: #4A6785; }
            QPushButton:checked { background: #27AE60; }
        """)
        self.toggle_inspector_btn.clicked.connect(self.toggle_inspector)
        layout.addWidget(self.toggle_inspector_btn)

        return header

    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(170)
        sidebar.setStyleSheet(SIDEBAR_STYLE)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        logo_label = QLabel("ECOSURF")
        logo_label.setObjectName("logo")
        layout.addWidget(logo_label)

        version = QLabel("v2.0 - Pro")
        version.setObjectName("version")
        layout.addWidget(version)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("nav")

        nav_items = [
            ("Files", 0),
            ("Spectrogram", 1),
            ("View", 2),
            ("Selection", 3),
            ("Pattern Search", 4),
            ("Embedding", 5),
            ("Carte 2D", 6),
            ("Annotations", 7),
        ]

        for name, idx in nav_items:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.nav_list.addItem(item)

        self.nav_list.setCurrentRow(0)
        self.nav_list.currentRowChanged.connect(self.on_nav_changed)
        layout.addWidget(self.nav_list, stretch=1)

        layout.addStretch()

        return sidebar

    def create_workspace(self):
        workspace = QWidget()
        workspace.setStyleSheet("background: #F5F6F7;")
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #E0E0E0;
                background: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #ECF0F1;
                border: 1px solid #E0E0E0;
                padding: 10px 24px;
                margin-right: 2px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #3498DB;
                color: #3498DB;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background: #EBF5FB;
            }
        """)

        # Spectrogram Tab
        spectro_tab = QWidget()
        spectro_layout = QVBoxLayout(spectro_tab)
        spectro_layout.setContentsMargins(8, 8, 8, 8)
        spectro_layout.setSpacing(4)

        self.spectrogram_widget = SpectrogramWidget()
        spectro_layout.addWidget(self.spectrogram_widget, stretch=1)

        self.viewport_scroll = QScrollBar(Qt.Orientation.Horizontal)
        self.viewport_scroll.setMinimum(0)
        self.viewport_scroll.setMaximum(100)
        self.viewport_scroll.setValue(0)
        self.viewport_scroll.setEnabled(False)
        self.viewport_scroll.valueChanged.connect(self.on_viewport_scroll)
        self.viewport_scroll.setFixedHeight(14)
        spectro_layout.addWidget(self.viewport_scroll)

        # Embedding results panel (under spectrogram)
        self.embedding_results = EmbeddingResultsWidget()
        self.embedding_results.result_clicked.connect(self.on_embedding_result_selected_from_panel)
        self.embedding_results.result_play.connect(self.play_embedding_result)
        self.embedding_results.setVisible(False)
        spectro_layout.addWidget(self.embedding_results)

        self.tabs.addTab(spectro_tab, "Spectrogram")

        layout.addWidget(self.tabs, stretch=1)

        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)

        return workspace

    def create_toolbar(self):
        toolbar = QFrame()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
            }
        """)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        # Play button
        self.play_btn = QPushButton("Play")
        self.play_btn.setFixedSize(70, 34)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: #27AE60;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover { background: #229954; }
            QPushButton:disabled { background: #BDC3C7; }
        """)
        self.play_btn.clicked.connect(self.play_audio)
        layout.addWidget(self.play_btn)

        # Pause button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setFixedSize(70, 34)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background: #F39C12;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover { background: #D68910; }
            QPushButton:disabled { background: #BDC3C7; }
        """)
        self.pause_btn.clicked.connect(self.pause_audio)
        self.pause_btn.setEnabled(False)
        layout.addWidget(self.pause_btn)

        # Stop button
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFixedSize(60, 34)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: #E74C3C;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 500;
                font-size: 12px;
            }
            QPushButton:hover { background: #C0392B; }
        """)
        self.stop_btn.clicked.connect(self.stop_audio)
        layout.addWidget(self.stop_btn)

        layout.addSpacing(6)

        # Annotation button
        self.annotate_btn = QPushButton("Annotate")
        self.annotate_btn.setFixedSize(80, 34)
        self.annotate_btn.setStyleSheet("""
            QPushButton {
                background: #9B59B6;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover { background: #8E44AD; }
            QPushButton:disabled { background: #BDC3C7; }
        """)
        self.annotate_btn.clicked.connect(self.open_annotation_dialog)
        self.annotate_btn.setToolTip("Create annotation for current audio position")
        layout.addWidget(self.annotate_btn)

        layout.addSpacing(10)

        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet("background: #E0E0E0;")
        layout.addWidget(sep)

        layout.addSpacing(10)

        # Info label for click-to-play
        click_info = QLabel("Click on spectrogram to start from position")
        click_info.setStyleSheet("color: #7F8C8D; font-size: 10px; font-style: italic;")
        layout.addWidget(click_info)

        layout.addStretch()

        # Reset view button
        reset_btn = QPushButton("Reset View")
        reset_btn.setFixedSize(80, 30)
        reset_btn.clicked.connect(self.on_zoom_reset)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #ECF0F1;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                color: #2C3E50;
                font-size: 11px;
            }
            QPushButton:hover { background: #EBF5FB; border-color: #3498DB; }
        """)
        layout.addWidget(reset_btn)

        layout.addSpacing(10)

        self.toolbar_status = QLabel("")
        self.toolbar_status.setStyleSheet("color: #7F8C8D; font-size: 11px;")
        layout.addWidget(self.toolbar_status)

        return toolbar

    def create_inspector(self):
        inspector = QFrame()
        inspector.setObjectName("inspector")
        inspector.setFixedWidth(320)
        inspector.setStyleSheet(INSPECTOR_STYLE)

        scroll_content = QWidget()
        self.inspector_layout = QVBoxLayout(scroll_content)
        self.inspector_layout.setContentsMargins(0, 0, 0, 0)
        self.inspector_layout.setSpacing(0)

        self.panel_stack = QStackedWidget()

        self.file_panel = FilePanel()
        self.spectrogram_panel = SpectrogramPanel()
        self.view_panel = ViewPanel()
        self.audio_panel = AudioPanel()
        self.pattern_panel = PatternPanel()
        self.search_panel = SearchPanel()
        self.embedding_panel = EmbeddingPanel()

        self.panel_stack.addWidget(self.file_panel)       # 0: Files
        self.panel_stack.addWidget(self.spectrogram_panel) # 1: Spectrogram
        self.panel_stack.addWidget(self.view_panel)        # 2: View
        self.panel_stack.addWidget(self.pattern_panel)     # 3: Selection
        self.panel_stack.addWidget(self.search_panel)      # 4: Pattern Search
        self.panel_stack.addWidget(self.embedding_panel)   # 5: Embedding

        self.inspector_layout.addWidget(self.panel_stack)

        main_layout = QVBoxLayout(inspector)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_content)

        return inspector

    def on_nav_changed(self, index):
        if index >= 0:
            if index == 6:
                self.open_clustering_dialog()
                self.nav_list.blockSignals(True)
                self.nav_list.setCurrentRow(self._last_nav_index)
                self.nav_list.blockSignals(False)
                return
            if index == 7:
                self.open_annotations_viewer()
                self.nav_list.blockSignals(True)
                self.nav_list.setCurrentRow(self._last_nav_index)
                self.nav_list.blockSignals(False)
                return
            self._last_nav_index = index
            self.panel_stack.setCurrentIndex(index)
            self.tabs.setCurrentIndex(0)

    def toggle_sidebar(self):
        """Toggle sidebar visibility"""
        visible = self.toggle_sidebar_btn.isChecked()
        self.sidebar.setVisible(visible)
        if visible:
            self.toggle_sidebar_btn.setText("<< Menu")
        else:
            self.toggle_sidebar_btn.setText(">> Menu")

    def toggle_inspector(self):
        """Toggle inspector panel visibility"""
        visible = self.toggle_inspector_btn.isChecked()
        self.inspector.setVisible(visible)
        if visible:
            self.toggle_inspector_btn.setText("Panel >>")
        else:
            self.toggle_inspector_btn.setText("Panel <<")

    def connect_signals(self):
        self.file_panel.file_loaded.connect(self.on_file_loaded_with_source)
        self.file_panel.search_scope_changed.connect(self.on_search_scope_changed)
        self.file_panel.period_dict_loaded.connect(self.on_period_dict_loaded)
        self.file_panel.folder_loaded.connect(self.on_folder_loaded)

        self.spectrogram_panel.spectrogram_computed.connect(self.on_spectrogram_computed)
        self.spectrogram_panel.colormap_changed.connect(self.spectrogram_widget.set_colormap)

        self.view_panel.zoom_toggled.connect(self.on_zoom_toggled)
        self.view_panel.zoom_reset_requested.connect(self.on_zoom_reset)

        self.pattern_panel.brush_toggled.connect(self.on_brush_toggled)
        self.pattern_panel.brush_size_changed.connect(self.on_brush_size_changed)
        self.pattern_panel.rect_mode_toggled.connect(self.on_rect_mode_toggled)
        self.pattern_panel.selection_cleared.connect(self.spectrogram_widget.clear_mask)
        self.pattern_panel.extract_requested.connect(self.extract_selection)
        self.pattern_panel.play_selection_requested.connect(self.play_selection)
        self.pattern_panel.cursor_changed.connect(self.spectrogram_widget.setCursor)

        self.search_panel.result_opened.connect(self.open_search_result)

        self.embedding_panel.load_btn.clicked.connect(self.load_embeddings)
        self.embedding_panel.search_requested.connect(self.search_embeddings)
        self.embedding_panel.result_selected.connect(self.on_embedding_result_selected)
        self.embedding_results.stop_requested.connect(self.embedding_panel.stop_audio)
        self.embedding_results.show_spectrogram_requested.connect(self.show_embedding_result_spectrogram)

        try:
            self.spectrogram_widget.scrollableChanged.connect(self.viewport_scroll.setEnabled)
        except:
            pass

        # Connect click on spectrogram to play from position
        self.spectrogram_widget.playback_position_clicked.connect(self.play_from_position)

        # Connect selection changed to enable buttons
        self.spectrogram_widget.selectionChanged.connect(self.on_selection_changed)

    def open_clustering_dialog(self):
        try:
            from ui.dialogs.clustering_dialog_fast import ClusteringDialogFast
            if self._cluster_dialog is None or not self._cluster_dialog.isVisible():
                self._cluster_dialog = ClusteringDialogFast(self)
                self._cluster_dialog.show_spectrogram_signal.connect(self.show_clustering_spectrogram)
                self._cluster_dialog.show()
            else:
                self._cluster_dialog.raise_()
                self._cluster_dialog.activateWindow()
        except ImportError as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Erreur", f"PyQtGraph requis:\npip install pyqtgraph\n\n{e}")

    def open_annotations_viewer(self):
        """Open the annotations viewer window"""
        try:
            from ui.dialogs.annotations_viewer import AnnotationsViewer
            if not hasattr(self, '_annotations_viewer') or self._annotations_viewer is None or not self._annotations_viewer.isVisible():
                self._annotations_viewer = AnnotationsViewer(self)
                self._annotations_viewer.load_annotation_requested.connect(self.load_annotation_audio)
                self._annotations_viewer.show()
            else:
                self._annotations_viewer.raise_()
                self._annotations_viewer.activateWindow()
                self._annotations_viewer.load_annotations()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Could not open annotations viewer:\n{e}")

    def open_annotation_dialog(self):
        """Open dialog to create a new annotation"""
        from PyQt6.QtWidgets import QMessageBox

        if self.audio_data is None:
            QMessageBox.warning(self, "No Audio", "Please load an audio file first.")
            return

        # Gather current audio context
        audio_info = self._get_current_audio_info()

        try:
            from ui.dialogs.annotation_dialog import AnnotationDialog
            dialog = AnnotationDialog(self, audio_info)
            dialog.annotation_saved.connect(self._on_annotation_saved)
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open annotation dialog:\n{e}")

    def _get_current_audio_info(self):
        """Get current audio context for annotation"""
        info = {
            'file_path': self.current_file or '',
            'file_name': os.path.basename(self.current_file) if self.current_file else '',
            'sample_rate': self.audio_data.get('sample_rate', 0) if self.audio_data else 0,
            'channel': 'Mono',
            'source_type': getattr(self.spectrogram_panel, '_source_type', 'local')
        }

        # Get viewport time range
        if self.audio_data and 'times' in self.audio_data:
            times = self.audio_data['times']
            start_idx, end_idx = self.spectrogram_widget.get_viewport_indices()
            if start_idx is not None and end_idx is not None:
                info['start_time'] = times[start_idx]
                info['end_time'] = times[min(end_idx, len(times) - 1)]
            else:
                info['start_time'] = times[0] if len(times) > 0 else 0
                info['end_time'] = times[-1] if len(times) > 0 else 0

            info['duration'] = info['end_time'] - info['start_time']

        # Get frequency range if available from selection
        if hasattr(self.spectrogram_widget, 'get_selection_freq_range'):
            try:
                freq_range = self.spectrogram_widget.get_selection_freq_range()
                if freq_range:
                    info['freq_min'] = freq_range[0]
                    info['freq_max'] = freq_range[1]
            except:
                pass

        # If there's a selection in pattern panel, use that info
        if hasattr(self.pattern_panel, 'selection_meta') and self.pattern_panel.selection_meta:
            meta = self.pattern_panel.selection_meta
            if 'start_time' in meta:
                info['start_time'] = meta['start_time']
            if 'end_time' in meta:
                info['end_time'] = meta['end_time']
            if 'freq_min' in meta:
                info['freq_min'] = meta['freq_min']
            if 'freq_max' in meta:
                info['freq_max'] = meta['freq_max']
            info['duration'] = info.get('end_time', 0) - info.get('start_time', 0)

        return info

    def _on_annotation_saved(self, annotation_data):
        """Called when an annotation is saved"""
        self.header_status.setText(f"Annotation #{annotation_data.get('id')} saved")
        self.header_status.setStyleSheet("color: #27AE60; font-size: 11px;")
        # Clear status after 3 seconds
        QTimer.singleShot(3000, lambda: self.header_status.setText(""))

    def load_annotation_audio(self, annotation):
        """Load audio file from an annotation"""
        from PyQt6.QtWidgets import QMessageBox

        file_path = annotation.get('file_path', '')
        source_type = annotation.get('source_type', 'local')

        if not file_path:
            QMessageBox.warning(self, "Error", "No file path in annotation.")
            return

        try:
            start_time = float(annotation.get('start_time', 0))
            end_time = float(annotation.get('end_time', 0))

            # Add some padding around the annotation
            padding = 2.0  # seconds
            padded_start = max(0, start_time - padding)
            padded_end = end_time + padding

            time_range = (padded_start, padded_end)

            # Load the file through file panel
            if source_type == 'database':
                # For database files
                self.file_panel.load_file_directly(file_path, time_range, 'database')
            else:
                # For local files
                if os.path.exists(file_path):
                    self.file_panel.load_file_directly(file_path, time_range, 'local')
                else:
                    QMessageBox.warning(
                        self, "File Not Found",
                        f"The audio file was not found:\n{file_path}\n\nIt may have been moved or deleted."
                    )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load annotation audio:\n{e}")

    def on_selection_changed(self):
        """Called when a selection is made on the spectrogram"""
        # Enable Extract and Play Selection buttons in pattern panel
        self.pattern_panel.extract_btn.setEnabled(True)
        self.pattern_panel.status_label.setText("Selection ready - Click Extract")
        self.pattern_panel.status_label.setStyleSheet("font-size: 11px; color: #27AE60; font-weight: 500;")
        self.pattern_panel.disable_brush()

    def on_period_dict_loaded(self, period_dict):
        if hasattr(self, 'search_panel'):
            self.search_panel.set_period_dict(period_dict)

    def on_file_loaded_with_source(self, file_path, time_range, source_type):
        self.current_file = file_path
        self.current_time_range = time_range
        self.spectrogram_panel.set_current_file(file_path, time_range)
        self.spectrogram_panel.set_source_type(source_type)
        if isinstance(file_path, list):
            self.header_file.setText(f"{len(file_path)} files selected")
        else:
            name = os.path.basename(file_path) if file_path else "No file"
            self.header_file.setText(name[:50])

    def on_folder_loaded(self, file_list):
        self.file_list = file_list
        self.search_panel.set_file_list(file_list)

    def on_spectrogram_computed(self, audio_data):
        if audio_data is None:
            self.header_status.setText("Error loading audio")
            self.toolbar_status.setText("Load failed")
            return
        self.audio_data = audio_data
        max_freq = audio_data['frequencies'][-1]
        self.header_status.setText(f"Max: {max_freq:.0f} Hz")
        self.spectrogram_widget.set_spectrogram(
            audio_data['spectrogram'],
            audio_data['frequencies'],
            audio_data['times'],
            audio_data['time_offset']
        )
        total_duration = float(audio_data['times'][-1])
        viewport_duration = self.spectrogram_widget.viewport_duration
        self.viewport_scroll.setEnabled(total_duration > viewport_duration)
        self.viewport_scroll.setValue(0)
        self.search_panel.set_audio_data(audio_data)
        self.toolbar_status.setText(f"Duration: {total_duration:.1f}s")
        self.play_btn.setEnabled(True)

    def on_viewport_scroll(self, value):
        if self.playing:
            return
        self.spectrogram_widget.scroll_viewport(value)

    def on_zoom_toggled(self, enabled):
        self.spectrogram_widget.zoom_enabled = enabled
        if enabled:
            self.pattern_panel.disable_brush()

    def on_zoom_reset(self):
        self.spectrogram_widget.reset_zoom()

    def on_brush_toggled(self, enabled):
        self.spectrogram_widget.brush_enabled = enabled
        if enabled:
            self.view_panel.disable_zoom()

    def on_search_scope_changed(self, scope_type, file_list):
        if hasattr(self, 'search_panel') and hasattr(self.search_panel, 'set_search_scope'):
            self.search_panel.set_search_scope(scope_type, file_list)

    def on_rect_mode_toggled(self, enabled):
        if enabled:
            self.spectrogram_widget.rect_selection_mode = True
            self.spectrogram_widget.brush_enabled = False
            self.view_panel.disable_zoom()
        else:
            self.spectrogram_widget.rect_selection_mode = False

    def on_brush_size_changed(self, size):
        self.spectrogram_widget.brush_size = size

    def extract_selection(self):
        try:
            from core.spectrogram_audio import extract_patch_audio
        except:
            self.pattern_panel.hide_progress()
            return
        if self.audio_data is None:
            self.pattern_panel.hide_progress()
            return
        mask = self.spectrogram_widget.mask
        if mask is None or not mask.any():
            self.pattern_panel.hide_progress()
            self.pattern_panel.status_label.setText("No selection")
            return
        self.pattern_panel.update_progress(10, "Preparing...")
        QTimer.singleShot(50, self._do_extract_selection)

    def _do_extract_selection(self):
        try:
            from core.spectrogram_audio import extract_patch_audio
        except:
            self.pattern_panel.hide_progress()
            return
        self.pattern_panel.update_progress(20, "Computing STFT...")
        n_fft = int(self.spectrogram_panel.window_combo.currentText())
        hop_length = int(self.spectrogram_panel.hop_combo.currentText())
        audio = self.audio_data.get('audio')
        sr = self.audio_data.get('sample_rate')
        mask = self.spectrogram_widget.mask
        try:
            stft = librosa.stft(audio, n_fft=n_fft, hop_length=hop_length)
        except:
            self.pattern_panel.hide_progress()
            return
        self.pattern_panel.update_progress(60, "Extracting audio...")
        sel_audio, meta = extract_patch_audio(
            stft, mask, sr,
            hop_length=hop_length,
            n_fft=n_fft,
            time_offset=self.audio_data.get('time_offset', 0.0)
        )
        self.pattern_panel.update_progress(90, "Finalizing...")
        if sel_audio is None or len(sel_audio) == 0:
            self.pattern_panel.hide_progress()
            self.pattern_panel.status_label.setText("Extraction failed")
            return
        self.pattern_panel.set_selection_data(sel_audio, meta)
        try:
            self.spectrogram_widget.show_selection_audio(sel_audio, sr)
        except:
            pass
        self.pattern_panel.hide_progress()

    def play_audio(self):
        if self.audio_data is None:
            return
        self.stop_audio()
        start_idx, end_idx = self.spectrogram_widget.get_viewport_indices()
        if start_idx is None:
            return
        times = self.audio_data['times']
        sr = self.audio_data['sample_rate']
        audio = self.audio_data['audio']
        start_sample = int(times[start_idx] * sr)
        end_sample = int(times[end_idx] * sr)
        audio_segment = audio[start_sample:end_sample]
        self.playing = True
        self.playing_selection = False
        self.playback_offset_time = times[start_idx]  # Store start time
        self.playback_start_time = datetime.now().timestamp()
        self.audio_thread = threading.Thread(target=self._play_audio_thread, args=(audio_segment, sr), daemon=True)
        self.audio_thread.start()
        self.playback_timer.start(50)
        self.viewport_scroll.setEnabled(False)
        self.play_btn.setText("Playing...")
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)

    def play_from_position(self, start_time):
        """Play audio starting from a specific time position"""
        if self.audio_data is None:
            return
        self.stop_audio()

        sr = self.audio_data['sample_rate']
        audio = self.audio_data['audio']
        times = self.audio_data['times']

        # Find end time (end of viewport or end of audio)
        start_idx, end_idx = self.spectrogram_widget.get_viewport_indices()
        if end_idx is not None:
            end_time = times[min(end_idx, len(times) - 1)]
        else:
            end_time = times[-1]

        # Calculate sample indices
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)

        # Clamp to valid range
        start_sample = max(0, min(start_sample, len(audio) - 1))
        end_sample = max(start_sample + 1, min(end_sample, len(audio)))

        audio_segment = audio[start_sample:end_sample]

        # Store offset for playback position display
        self.playback_offset_time = start_time

        self.playing = True
        self.playing_selection = False
        self.playback_start_time = datetime.now().timestamp()
        self.audio_thread = threading.Thread(target=self._play_audio_thread, args=(audio_segment, sr), daemon=True)
        self.audio_thread.start()
        self.playback_timer.start(50)
        self.viewport_scroll.setEnabled(False)
        self.play_btn.setText("Playing...")
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)

    def play_selection(self):
        selection_audio = self.pattern_panel.selection_audio
        if selection_audio is None:
            return
        self.stop_audio()
        sr = int(self.pattern_panel.selection_meta.get('sample_rate', self.audio_data.get('sample_rate')))
        self.playing = True
        self.playing_selection = True
        self.playback_start_time = datetime.now().timestamp()
        self.audio_thread = threading.Thread(target=self._play_audio_thread, args=(selection_audio, sr), daemon=True)
        self.audio_thread.start()
        self.playback_timer.start(50)
        self.viewport_scroll.setEnabled(False)
        self.play_btn.setText("Playing...")
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)

    def _play_audio_thread(self, audio, sr):
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paFloat32, channels=1, rate=sr, output=True)
            chunk_size = 1024
            audio_float = audio.astype('float32')
            for i in range(0, len(audio_float), chunk_size):
                if not self.playing:
                    break
                chunk = audio_float[i:i+chunk_size]
                stream.write(chunk.tobytes())
            stream.stop_stream()
            stream.close()
            p.terminate()
        except Exception as e:
            print(f"Audio error: {e}")
        self.playing = False

    def pause_audio(self):
        self.playing = False
        self.playback_timer.stop()
        if self.audio_thread:
            self.audio_thread.join()
        try:
            self.viewport_scroll.setEnabled(self.spectrogram_widget._scrollable)
        except:
            pass
        self.play_btn.setText("Play")
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)

    def stop_audio(self):
        self.playing = False
        self.playback_timer.stop()
        if self.audio_thread:
            self.audio_thread.join()
        self.spectrogram_widget.set_playback_position(None)
        try:
            self.viewport_scroll.setEnabled(self.spectrogram_widget._scrollable)
        except:
            pass
        try:
            self.playing_selection = False
            self.spectrogram_widget.set_selection_playback_pos(None)
        except:
            pass
        self.play_btn.setText("Play")
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)

    def update_playback_position(self):
        if not self.playing:
            return
        elapsed = datetime.now().timestamp() - self.playback_start_time
        if self.playing_selection:
            self.spectrogram_widget.set_selection_playback_pos(elapsed)
            duration = self.spectrogram_widget.selection_duration
            if duration and elapsed >= duration:
                self.stop_audio()
            return
        current_pos = self.playback_offset_time + elapsed
        self.spectrogram_widget.set_playback_position(current_pos)
        # Check if we've reached end of viewport
        start_idx, end_idx = self.spectrogram_widget.get_viewport_indices()
        if start_idx is not None and end_idx is not None and self.audio_data:
            times = self.audio_data['times']
            viewport_end = times[min(end_idx, len(times) - 1)]
            if current_pos >= viewport_end:
                self.stop_audio()

    def open_search_result(self, file_path):
        self.current_file = file_path
        self.header_file.setText(os.path.basename(file_path))

    def load_embeddings(self):
        if self.embedding_manager.loader_thread is not None and self.embedding_manager.loader_thread.isRunning():
            self.embedding_panel.status_label.setText("Loading embeddings...")
            return
        self.embedding_panel.status_label.setText("Searching files...")
        self.embedding_panel.load_btn.setEnabled(False)
        def _on_loaded(count):
            self.embedding_panel.on_embeddings_loaded(count)
            if self._auto_embedding_search_pending:
                self._auto_embedding_search_pending = False
                self.search_embeddings()

        def _on_error(e):
            self.embedding_panel.status_label.setText(f"Error: {e}")
            self.embedding_panel.load_btn.setEnabled(True)
            self._auto_embedding_search_pending = False

        success = self.embedding_manager.load_best_available(
            on_done=_on_loaded,
            on_error=_on_error,
            on_progress=lambda msg: self.embedding_panel.status_label.setText(msg)
        )
        if not success:
            self.embedding_panel.status_label.setText("Embeddings not found in perch2/")
            self.embedding_panel.load_btn.setEnabled(True)
            self._auto_embedding_search_pending = False

    def search_embeddings(self, auto_load=False, auto_navigate=False):
        if self.audio_data is None:
            self.embedding_panel.status_label.setText("No audio loaded")
            return
        mask = self.spectrogram_widget.mask
        if mask is None or not mask.any():
            self.embedding_panel.status_label.setText("Select a region first (10s max)")
            return
        time_cols = np.any(mask > 0, axis=0)
        if not np.any(time_cols):
            return
        first = int(np.where(time_cols)[0][0])
        last = int(np.where(time_cols)[0][-1])
        times = self.audio_data['times']
        start_time = times[first] + self.audio_data.get('time_offset', 0.0)
        end_time = times[last] + self.audio_data.get('time_offset', 0.0)
        selection_duration = end_time - start_time
        max_selection_s = 10.0
        if selection_duration > max_selection_s:
            self.embedding_panel.status_label.setText(
                f"Selection too long: {selection_duration:.1f}s (max {max_selection_s:.0f}s)"
            )
            return
        if auto_navigate:
            self.nav_list.setCurrentRow(5)
        if not self.embedding_manager.loaded:
            if auto_load:
                self._auto_embedding_search_pending = True
                self.load_embeddings()
            else:
                self.embedding_panel.status_label.setText("Embeddings not loaded")
            return

        # Start progress bar
        self.embedding_panel.start_search_progress()
        self.embedding_panel.update_search_progress(10, "Preparing audio...")

        sr = self.audio_data['sample_rate']
        audio = self.audio_data['audio']
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)
        selection_audio = audio[start_sample:end_sample]

        self.embedding_panel.update_search_progress(30, "Computing Perch embedding...")
        query_emb = self.compute_embedding(selection_audio, sr)

        if query_emb is not None:
            self.embedding_panel.update_search_progress(70, "Searching database...")
            results = self.embedding_manager.search(query_emb, top_k=20)

            self.embedding_panel.update_search_progress(90, "Loading results...")
            self.embedding_panel.show_results(results)
            self.search_results = results

            self.embedding_panel.update_search_progress(100, f"{len(results)} results found")

            # Show results in the main panel
            self.embedding_results.show_results(results)
            self.embedding_results.setVisible(True)

            self.embedding_panel.finish_search_progress()
            self.embedding_panel.status_label.setText(f"{len(results)} results found")
        else:
            self.embedding_panel.finish_search_progress()
            self.embedding_panel.status_label.setText("Embedding computation failed")

    def load_perch_model(self):
        if self.perch_model is not None:
            return True
        if self.perch_model_loading:
            return False
        try:
            self.perch_model_loading = True
            self.embedding_panel.status_label.setText("Loading Perch model...")
            from perch_hoplite.zoo import model_configs
            self.perch_model = model_configs.load_model_by_name("perch_v2")
            self.perch_model_loading = False
            self.embedding_panel.status_label.setText("Perch model loaded")
            return True
        except Exception as e:
            self.perch_model_loading = False
            self.embedding_panel.status_label.setText(f"Perch error: {str(e)[:50]}")
            return False

    def compute_embedding(self, audio, sr):
        try:
            if not self.load_perch_model():
                return None
            if sr != 32000:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=32000)
                sr = 32000
            target_length = 160000
            if len(audio) < target_length:
                audio = np.pad(audio, (0, target_length - len(audio)), mode='constant')
            elif len(audio) > target_length:
                audio = audio[:target_length]
            audio = audio.astype(np.float32)
            outputs = self.perch_model.embed(audio)
            embedding = outputs.embeddings.flatten()
            return embedding.astype(np.float32)
        except Exception as e:
            print(f"Embedding error: {e}")
            return None

    def on_embedding_result_selected(self, data):
        idx = data['index']
        if idx < len(self.search_results):
            result = self.search_results[idx]
            print(f"Selected: {result['metadata']}")

    def on_embedding_result_selected_from_panel(self, idx):
        """Handle result selection from the main results panel"""
        if idx < len(self.search_results):
            result = self.search_results[idx]
            print(f"Selected result {idx}: {result['metadata']}")

    def show_embedding_result_spectrogram(self, idx):
        if idx < 0 or idx >= len(self.search_results):
            return
        meta = self.search_results[idx]['metadata']
        file_name = meta.get('file')
        start_time = meta.get('start', 0.0)
        end_time = meta.get('end', start_time)
        if not file_name:
            return
        self.nav_list.setCurrentRow(1)
        self.tabs.setCurrentIndex(0)
        self.on_file_loaded_with_source(file_name, (start_time, end_time), 'database')
        self.spectrogram_panel.compute_spectrogram()

    def show_clustering_spectrogram(self, file_name, start_time, end_time):
        if not file_name:
            return
        self.nav_list.setCurrentRow(1)
        self.tabs.setCurrentIndex(0)
        self.on_file_loaded_with_source(file_name, (start_time, end_time), 'database')
        self.spectrogram_panel.compute_spectrogram()

    def play_embedding_result(self, idx):
        """Play audio from embedding result"""
        if idx < len(self.search_results):
            result = self.search_results[idx]
            self.embedding_panel.play_selected_result(idx, result)

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()
        if key == Qt.Key.Key_Space:
            if mods & Qt.KeyboardModifier.ShiftModifier:
                if self.pattern_panel.selection_audio is not None:
                    if self.playing:
                        self.pause_audio()
                    else:
                        self.play_selection()
            else:
                if self.playing and not self.playing_selection:
                    self.pause_audio()
                else:
                    self.play_audio()
            return
        if key == Qt.Key.Key_R:
            self.spectrogram_widget.reset_zoom()
            return
        if key == Qt.Key.Key_Minus:
            self.pattern_panel.change_brush_size(-2)
            return
        if key == Qt.Key.Key_Equal:
            self.pattern_panel.change_brush_size(+2)
            return
        super().keyPressEvent(event)
