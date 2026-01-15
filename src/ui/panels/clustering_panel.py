"""
Clustering Panel - Clean panel to launch cluster visualization
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class ClusteringPanel(QWidget):
    """Panel for clustering visualization access"""
    
    def __init__(self):
        super().__init__()
        self.clustering_dialog = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("Analyse des Clusters")
        header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header.setStyleSheet("color: #333;")
        layout.addWidget(header)
        
        # Description
        desc = QLabel(
            "Explorez visuellement les 488 clusters extraits des 650,760 segments audio. "
            "Visualisation 2D avec UMAP, ecoute des segments, statistiques."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(desc)
        
        # Info boxes
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame { background-color: #f8f9fa; border: 1px solid #e9ecef; 
                    border-radius: 8px; padding: 10px; }
        """)
        info_layout = QHBoxLayout(info_frame)
        
        stats = [
            ("650,760", "Segments"),
            ("488", "Clusters"),
            ("5s", "Par segment"),
            ("1536", "Dimensions"),
        ]
        
        for value, label in stats:
            box = QWidget()
            box.setMinimumSize(100, 70)
            box_layout = QVBoxLayout(box)
            box_layout.setContentsMargins(10, 10, 10, 10)
            box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box_layout.setSpacing(5)
            
            value_label = QLabel(value)
            value_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value_label.setStyleSheet("color: #E95420; background: transparent;")
            box_layout.addWidget(value_label)
            
            text_label = QLabel(label)
            text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            text_label.setStyleSheet("color: #666; font-size: 11px; background: transparent;")
            box_layout.addWidget(text_label)
            
            box.setStyleSheet("background-color: white; border: 1px solid #dee2e6; border-radius: 6px;")
            info_layout.addWidget(box)
        
        layout.addWidget(info_frame)
        
        # Features
        features_group = QGroupBox("Fonctionnalites")
        features_group.setStyleSheet("""
            QGroupBox { font-weight: bold; font-size: 13px; border: 1px solid #e9ecef;
                       border-radius: 6px; margin-top: 10px; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)
        features_layout = QVBoxLayout(features_group)
        
        features = [
            "- Carte 2D interactive avec zoom",
            "- Selection du nombre de clusters",
            "- Clic pour voir les details",
            "- Ecoute des segments audio",
            "- Statistiques des clusters"
        ]
        
        for feature in features:
            feat_label = QLabel(feature)
            feat_label.setStyleSheet("padding: 3px; font-size: 12px;")
            features_layout.addWidget(feat_label)
        
        layout.addWidget(features_group)
        
        # Launch button
        self.launch_btn = QPushButton("Ouvrir la Visualisation")
        self.launch_btn.setStyleSheet("""
            QPushButton { background-color: #E95420; color: white; padding: 12px 25px;
                         font-size: 14px; font-weight: bold; border: none; border-radius: 6px; }
            QPushButton:hover { background-color: #c44117; }
            QPushButton:pressed { background-color: #a33612; }
        """)
        self.launch_btn.clicked.connect(self.open_clustering_dialog)
        layout.addWidget(self.launch_btn)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
    def open_clustering_dialog(self):
        """Open the clustering visualization dialog"""
        try:
            from ui.dialogs.clustering_dialog import ClusteringDialog
            
            if self.clustering_dialog is None or not self.clustering_dialog.isVisible():
                self.status_label.setText("Chargement...")
                self.clustering_dialog = ClusteringDialog(self)
                self.clustering_dialog.show()
                self.status_label.setText("Fenetre ouverte")
            else:
                self.clustering_dialog.raise_()
                self.clustering_dialog.activateWindow()
                
        except Exception as e:
            self.status_label.setText(f"Erreur: {str(e)[:50]}")
            print(f"Error opening clustering dialog: {e}")
