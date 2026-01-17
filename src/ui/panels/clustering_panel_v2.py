"""
Clustering Panel V2 - Professional blue styling
Options and controls for 2D clustering visualization
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QGroupBox, 
    QHBoxLayout, QSpinBox, QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt

# Style cohérent bleu professionnel
PANEL_STYLE = """
    QWidget {
        background-color: white;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QGroupBox {
        font-weight: 600;
        font-size: 11px;
        color: #2C3E50;
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        margin-top: 12px;
        padding: 12px 8px 8px 8px;
        background-color: #FAFBFC;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 6px;
        background-color: white;
    }
    QPushButton {
        background-color: #3498DB;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #2980B9;
    }
    QPushButton:pressed {
        background-color: #1F6DA8;
    }
    QPushButton:disabled {
        background-color: #BDC3C7;
        color: #7F8C8D;
    }
    QSpinBox {
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        padding: 4px 8px;
        background-color: white;
        font-size: 12px;
    }
    QSpinBox:hover {
        border-color: #3498DB;
    }
    QComboBox {
        border: 1px solid #E0E0E0;
        border-radius: 4px;
        padding: 6px 10px;
        background-color: white;
        font-size: 12px;
    }
    QComboBox:hover {
        border-color: #3498DB;
    }
"""


class ClusteringPanel(QWidget):
    """Clustering options panel - Professional blue styling"""
    cluster_range_changed = pyqtSignal(int, int)
    colormap_changed = pyqtSignal(str)
    refresh_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setStyleSheet(PANEL_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Header
        header = QLabel("Clustering")
        header.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 600;
                color: #2C3E50;
                padding-bottom: 4px;
                border-bottom: 2px solid #3498DB;
            }
        """)
        layout.addWidget(header)
        
        # Quick Presets
        presets_group = QGroupBox("Quick View")
        presets_layout = QVBoxLayout()
        presets_layout.setSpacing(8)

        presets_row = QHBoxLayout()
        presets_row.setSpacing(6)

        preset_btns = [("15", 15), ("30", 30), ("45", 45), ("All", 100)]
        for label, val in preset_btns:
            btn = QPushButton(label)
            btn.setFixedSize(45, 30)
            btn.clicked.connect(lambda checked, v=val: self.apply_preset(v))
            presets_row.addWidget(btn)
        presets_row.addStretch()
        presets_layout.addLayout(presets_row)

        presets_group.setLayout(presets_layout)
        layout.addWidget(presets_group)

        # Cluster Range
        range_group = QGroupBox("Cluster Range")
        range_layout = QVBoxLayout()
        range_layout.setSpacing(8)

        # Min cluster
        min_row = QHBoxLayout()
        min_label = QLabel("From:")
        min_label.setStyleSheet("font-size: 12px; color: #2C3E50;")
        self.min_spin = QSpinBox()
        self.min_spin.setRange(1, 500)
        self.min_spin.setValue(1)
        self.min_spin.valueChanged.connect(self.on_range_changed)
        min_row.addWidget(min_label)
        min_row.addWidget(self.min_spin)
        min_row.addStretch()
        range_layout.addLayout(min_row)

        # Max cluster
        max_row = QHBoxLayout()
        max_label = QLabel("To:")
        max_label.setStyleSheet("font-size: 12px; color: #2C3E50;")
        self.max_spin = QSpinBox()
        self.max_spin.setRange(1, 500)
        self.max_spin.setValue(50)
        self.max_spin.valueChanged.connect(self.on_range_changed)
        max_row.addWidget(max_label)
        max_row.addWidget(self.max_spin)
        max_row.addStretch()
        range_layout.addLayout(max_row)

        range_group.setLayout(range_layout)
        layout.addWidget(range_group)

        # Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)

        self.refresh_btn = QPushButton("Refresh View")
        self.refresh_btn.clicked.connect(self.on_refresh)
        actions_layout.addWidget(self.refresh_btn)

        self.reset_btn = QPushButton("Reset Zoom")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
        """)
        self.reset_btn.clicked.connect(self.on_reset_zoom)
        actions_layout.addWidget(self.reset_btn)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        # Help
        help_label = QLabel("Scroll: Zoom | Right-click: Pan | Click: Details")
        help_label.setStyleSheet("font-size: 10px; color: #7F8C8D; font-style: italic;")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        # Stats
        self.stats_label = QLabel("No data loaded")
        self.stats_label.setStyleSheet("""
            font-size: 11px; 
            color: #7F8C8D;
            padding: 8px;
            background-color: #FAFBFC;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
        """)
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)
        
        layout.addStretch()
        
    def on_range_changed(self):
        min_val = self.min_spin.value()
        max_val = self.max_spin.value()
        self.cluster_range_changed.emit(min_val, max_val)

    def apply_preset(self, max_val):
        """Apply preset cluster range"""
        self.min_spin.setValue(1)
        self.max_spin.setValue(max_val)
        self.on_range_changed()

    def on_colormap_changed(self, cmap):
        self.colormap_changed.emit(cmap)

    def on_refresh(self):
        self.refresh_requested.emit()

    def on_reset_zoom(self):
        # This will be connected to the clustering widget
        pass
        
    def set_stats(self, num_points, num_clusters):
        """Update stats display"""
        self.stats_label.setText(f"{num_points:,} points\n{num_clusters} clusters")
        self.stats_label.setStyleSheet("""
            font-size: 11px; 
            color: #27AE60;
            padding: 8px;
            background-color: #FAFBFC;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
        """)
        self.max_spin.setMaximum(num_clusters)
        self.max_spin.setValue(min(50, num_clusters))
