"""
ECOSURF Annotations Viewer
Window for viewing, managing and navigating annotations
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QFileDialog, QMessageBox, QAbstractItemView, QWidget,
    QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from core.annotation_manager import AnnotationManager


class AnnotationsViewer(QDialog):
    """Window for viewing and managing all annotations"""

    # Signal emitted when user wants to load an annotation's audio
    load_annotation_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.annotation_manager = AnnotationManager()
        self.annotations = []
        self.init_ui()
        self.load_annotations()

    def init_ui(self):
        self.setWindowTitle("Annotations Viewer")
        self.setMinimumSize(1000, 600)
        self.setStyleSheet("""
            QDialog {
                background: #F5F6F7;
            }
            QLabel {
                color: #2C3E50;
            }
            QLabel#title {
                font-size: 18px;
                font-weight: bold;
                color: #2C3E50;
            }
            QLabel#subtitle {
                font-size: 12px;
                color: #7F8C8D;
            }
            QTableWidget {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                gridline-color: #F0F0F0;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background: #3498DB;
                color: white;
            }
            QHeaderView::section {
                background: #34495E;
                color: white;
                padding: 10px 8px;
                border: none;
                font-weight: 600;
                font-size: 11px;
            }
            QLineEdit {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #3498DB;
            }
            QComboBox {
                background: white;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 8px 12px;
                min-width: 150px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()

        title_section = QVBoxLayout()
        title = QLabel("Annotations")
        title.setObjectName("title")
        title_section.addWidget(title)

        self.subtitle = QLabel("0 annotations")
        self.subtitle.setObjectName("subtitle")
        title_section.addWidget(self.subtitle)
        header.addLayout(title_section)

        header.addStretch()

        # CSV path info
        path_label = QLabel(f"CSV: {self.annotation_manager.get_csv_path()}")
        path_label.setStyleSheet("font-size: 10px; color: #95A5A6;")
        header.addWidget(path_label)

        layout.addLayout(header)

        # Filter/Search bar
        filter_bar = QHBoxLayout()

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search annotations...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self._filter_table)
        filter_bar.addWidget(self.search_input)

        # Event type filter
        filter_bar.addWidget(QLabel("Filter by type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types", "")
        for label, code in AnnotationManager.get_event_types():
            self.type_filter.addItem(label, code)
        self.type_filter.currentIndexChanged.connect(self._filter_table)
        filter_bar.addWidget(self.type_filter)

        filter_bar.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFixedSize(80, 32)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #ECF0F1;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                color: #2C3E50;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #EBF5FB;
                border-color: #3498DB;
            }
        """)
        refresh_btn.clicked.connect(self.load_annotations)
        filter_bar.addWidget(refresh_btn)

        layout.addLayout(filter_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Date", "File", "Time Range", "Duration",
            "Event Type", "Quality", "Notes", "Load", "Delete"
        ])

        # Configure table
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)

        # Column widths
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Date
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # File
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Time
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Duration
        header_view.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Event Type
        header_view.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # Quality
        header_view.setSectionResizeMode(7, QHeaderView.ResizeMode.Stretch)  # Notes
        header_view.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)  # Load
        header_view.setSectionResizeMode(9, QHeaderView.ResizeMode.Fixed)  # Delete

        self.table.setColumnWidth(0, 50)   # ID
        self.table.setColumnWidth(1, 100)  # Date
        self.table.setColumnWidth(3, 140)  # Time
        self.table.setColumnWidth(4, 70)   # Duration
        self.table.setColumnWidth(5, 150)  # Event Type
        self.table.setColumnWidth(6, 60)   # Quality
        self.table.setColumnWidth(8, 70)   # Load
        self.table.setColumnWidth(9, 70)   # Delete

        layout.addWidget(self.table)

        # Bottom buttons
        btn_layout = QHBoxLayout()

        # Export button
        export_btn = QPushButton("Export CSV")
        export_btn.setFixedSize(100, 36)
        export_btn.setStyleSheet("""
            QPushButton {
                background: #27AE60;
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #229954;
            }
        """)
        export_btn.clicked.connect(self._export_csv)
        btn_layout.addWidget(export_btn)

        # Import button
        import_btn = QPushButton("Import CSV")
        import_btn.setFixedSize(100, 36)
        import_btn.setStyleSheet("""
            QPushButton {
                background: #3498DB;
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #2980B9;
            }
        """)
        import_btn.clicked.connect(self._import_csv)
        btn_layout.addWidget(import_btn)

        btn_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(80, 36)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #ECF0F1;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                color: #2C3E50;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #E0E0E0;
            }
        """)
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def load_annotations(self):
        """Load all annotations from CSV and display in table"""
        self.annotations = self.annotation_manager.get_all_annotations()
        self._populate_table(self.annotations)
        self.subtitle.setText(f"{len(self.annotations)} annotations")

    def _populate_table(self, annotations):
        """Populate table with annotations"""
        self.table.setRowCount(0)
        self.table.setRowCount(len(annotations))

        for row, ann in enumerate(annotations):
            # ID
            id_item = QTableWidgetItem(str(ann.get('id', '')))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, id_item)

            # Date (formatted from timestamp)
            timestamp = ann.get('timestamp', '')
            if timestamp:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(timestamp)
                    date_str = dt.strftime("%Y-%m-%d")
                except:
                    date_str = timestamp[:10] if len(timestamp) >= 10 else timestamp
            else:
                date_str = ""
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, date_item)

            # File name
            file_item = QTableWidgetItem(ann.get('file_name', ''))
            file_item.setToolTip(ann.get('file_path', ''))
            self.table.setItem(row, 2, file_item)

            # Time range
            try:
                start = float(ann.get('start_time', 0))
                end = float(ann.get('end_time', 0))
                time_str = f"{self._format_time(start)} - {self._format_time(end)}"
            except:
                time_str = ""
            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            time_item.setFont(QFont("Consolas", 9))
            self.table.setItem(row, 3, time_item)

            # Duration
            try:
                duration = float(ann.get('duration', 0))
                dur_str = f"{duration:.2f}s"
            except:
                dur_str = ""
            dur_item = QTableWidgetItem(dur_str)
            dur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, dur_item)

            # Event type
            event_item = QTableWidgetItem(ann.get('event_type', ''))
            self.table.setItem(row, 5, event_item)

            # Quality (with color)
            try:
                quality = int(ann.get('quality', 0))
                quality_item = QTableWidgetItem(f"{quality}/10")
                quality_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if quality <= 3:
                    quality_item.setForeground(QColor("#E74C3C"))
                elif quality <= 6:
                    quality_item.setForeground(QColor("#F39C12"))
                else:
                    quality_item.setForeground(QColor("#27AE60"))
                quality_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            except:
                quality_item = QTableWidgetItem("")
            self.table.setItem(row, 6, quality_item)

            # Notes (truncated)
            notes = ann.get('notes', '')
            notes_truncated = notes[:50] + "..." if len(notes) > 50 else notes
            notes_item = QTableWidgetItem(notes_truncated)
            notes_item.setToolTip(notes)
            self.table.setItem(row, 7, notes_item)

            # Load button
            load_btn = QPushButton("Load")
            load_btn.setStyleSheet("""
                QPushButton {
                    background: #3498DB;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-size: 10px;
                    font-weight: 500;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background: #2980B9;
                }
            """)
            load_btn.clicked.connect(lambda checked, a=ann: self._load_annotation(a))
            self.table.setCellWidget(row, 8, self._center_widget(load_btn))

            # Delete button
            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet("""
                QPushButton {
                    background: #E74C3C;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    font-size: 10px;
                    font-weight: 500;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background: #C0392B;
                }
            """)
            del_btn.clicked.connect(lambda checked, a=ann: self._delete_annotation(a))
            self.table.setCellWidget(row, 9, self._center_widget(del_btn))

    def _center_widget(self, widget):
        """Create a container to center a widget in table cell"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.addWidget(widget)
        return container

    def _format_time(self, seconds):
        """Format seconds as MM:SS.ms"""
        try:
            seconds = float(seconds)
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes:02d}:{secs:05.2f}"
        except:
            return "00:00.00"

    def _filter_table(self):
        """Filter table based on search and type filter"""
        search_text = self.search_input.text().lower()
        type_filter = self.type_filter.currentData()

        filtered = []
        for ann in self.annotations:
            # Check type filter
            if type_filter and ann.get('event_code', '') != type_filter:
                continue

            # Check search text
            if search_text:
                searchable = f"{ann.get('file_name', '')} {ann.get('event_type', '')} {ann.get('notes', '')}".lower()
                if search_text not in searchable:
                    continue

            filtered.append(ann)

        self._populate_table(filtered)
        self.subtitle.setText(f"{len(filtered)} of {len(self.annotations)} annotations")

    def _load_annotation(self, annotation):
        """Emit signal to load annotation's audio file"""
        self.load_annotation_requested.emit(annotation)

    def _delete_annotation(self, annotation):
        """Delete an annotation after confirmation"""
        reply = QMessageBox.question(
            self,
            "Delete Annotation",
            f"Delete annotation #{annotation.get('id')}?\n\nFile: {annotation.get('file_name')}\nEvent: {annotation.get('event_type')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            ann_id = int(annotation.get('id', 0))
            if self.annotation_manager.delete_annotation(ann_id):
                self.load_annotations()
                QMessageBox.information(self, "Deleted", "Annotation deleted successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete annotation.")

    def _export_csv(self):
        """Export annotations to a CSV file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Annotations",
            "annotations_export.csv",
            "CSV Files (*.csv)"
        )

        if file_path:
            self.annotation_manager.export_to_csv(file_path)
            QMessageBox.information(
                self,
                "Export Complete",
                f"Exported {len(self.annotations)} annotations to:\n{file_path}"
            )

    def _import_csv(self):
        """Import annotations from a CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Annotations",
            "",
            "CSV Files (*.csv)"
        )

        if file_path:
            reply = QMessageBox.question(
                self,
                "Import Mode",
                "How do you want to import?\n\n"
                "Yes = Merge with existing annotations\n"
                "No = Replace all existing annotations",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Cancel:
                return

            merge = reply == QMessageBox.StandardButton.Yes
            self.annotation_manager.import_from_csv(file_path, merge=merge)
            self.load_annotations()
            QMessageBox.information(self, "Import Complete", "Annotations imported successfully.")
