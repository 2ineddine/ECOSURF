"""
Clustering Visualization Dialog - Professional 2D cluster exploration
"""
import os
import pickle
import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel, 
    QSlider, QSpinBox, QComboBox, QPushButton, QGroupBox,
    QSplitter, QCheckBox, QFrame, QLineEdit, QRadioButton,
    QButtonGroup, QToolButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtGui import QFont, QFontMetrics

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import mplcursors


class ElidedLabel(QLabel):
    """Label that automatically elides text with ellipsis"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._full_text = text
        self.setMinimumWidth(30)
        
    def setText(self, text):
        self._full_text = text
        self._update_elided()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided()
        
    def _update_elided(self):
        fm = QFontMetrics(self.font())
        elided = fm.elidedText(self._full_text, Qt.TextElideMode.ElideRight, self.width() - 5)
        super().setText(elided)
        if elided != self._full_text:
            self.setToolTip(self._full_text)
        else:
            self.setToolTip("")


class AudioLoaderThread(QThread):
    """Thread pour charger l'audio depuis S3"""
    finished = pyqtSignal(object, int)
    error = pyqtSignal(str)
    
    def __init__(self, file_path, start_time, end_time):
        super().__init__()
        self.file_path = file_path
        self.start_time = start_time
        self.end_time = end_time
        
    def run(self):
        try:
            import boto3
            import librosa
            import json
            import io
            
            creds_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'credentials.json')
            with open(creds_path, 'r') as f:
                creds = json.load(f)
            
            s3 = boto3.client(
                's3',
                endpoint_url=creds['endpoint'],
                aws_access_key_id=creds['ACCESS_KEY'],
                aws_secret_access_key=creds['SECRET_KEY']
            )
            
            file_name = self.file_path
            site = file_name.split('_')[0]
            s3_key = f"2019/{site}/Data/{file_name}"
            
            buffer = io.BytesIO()
            s3.download_fileobj(creds['bucket'], s3_key, buffer)
            buffer.seek(0)
            
            audio, sr = librosa.load(buffer, sr=None, offset=self.start_time, 
                                     duration=self.end_time - self.start_time)
            self.finished.emit(audio, sr)
            
        except Exception as e:
            self.error.emit(str(e))


class ClusteringDialog(QDialog):
    """Dialog for professional interactive 2D cluster visualization"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Analyse des Clusters - Exploration Interactive")
        self.setMinimumSize(1200, 800)
        self.setModal(False)
        
        # Data
        self.embeddings_2d = None
        self.labels = None
        self.metadata = None
        self.n_clusters = 0
        self.selected_point_idx = None
        self.displayed_indices = None
        self.cluster_sizes = {}
        self.sorted_clusters = []
        
        # Selection mode: 'range' or 'specific'
        self.selection_mode = 'range'
        self.specific_clusters = []
        
        # Plot objects
        self.scatter = None
        self.ax = None
        
        # Audio
        self.audio_thread = None
        self.is_playing = False
        self.selected_meta = None
        
        # Matplotlib cursor for hover
        self.cursor = None
        
        # Debounce timer
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._do_update_plot)
        
        self.init_ui()
        QTimer.singleShot(100, self.load_data)
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === LEFT PANEL ===
        left_panel = QFrame()
        left_panel.setFixedWidth(240)
        left_panel.setStyleSheet("""
            QFrame { background: #fafafa; border-right: 1px solid #ddd; }
            QGroupBox { font-weight: bold; font-size: 10px; margin-top: 8px; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 3px; }
            QLabel { font-size: 9px; }
            QSpinBox, QComboBox, QLineEdit { font-size: 9px; height: 22px; }
            QRadioButton { font-size: 9px; }
            QPushButton { font-size: 9px; }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(4)
        
        # Title
        title = QLabel("Controles")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setStyleSheet("font-size: 13px;")
        left_layout.addWidget(title)
        
        # --- Selection Mode ---
        grp1 = QGroupBox("Selection Clusters")
        g1_layout = QVBoxLayout(grp1)
        g1_layout.setSpacing(4)
        g1_layout.setContentsMargins(6, 12, 6, 6)
        
        # Radio buttons for mode
        self.mode_group = QButtonGroup(self)
        
        self.range_radio = QRadioButton("Par plage (rang)")
        self.range_radio.setChecked(True)
        self.range_radio.toggled.connect(self.on_mode_changed)
        self.mode_group.addButton(self.range_radio)
        g1_layout.addWidget(self.range_radio)
        
        # Range selection
        self.range_widget = QWidget()
        range_layout = QVBoxLayout(self.range_widget)
        range_layout.setContentsMargins(15, 0, 0, 0)
        range_layout.setSpacing(3)
        
        row_min = QHBoxLayout()
        row_min.addWidget(QLabel("Min:"))
        self.min_spinbox = QSpinBox()
        self.min_spinbox.setRange(1, 488)
        self.min_spinbox.setValue(1)
        self.min_spinbox.valueChanged.connect(self.on_range_changed)
        row_min.addWidget(self.min_spinbox)
        row_min.addStretch()
        range_layout.addLayout(row_min)
        
        row_max = QHBoxLayout()
        row_max.addWidget(QLabel("Max:"))
        self.max_spinbox = QSpinBox()
        self.max_spinbox.setRange(1, 488)
        self.max_spinbox.setValue(20)
        self.max_spinbox.valueChanged.connect(self.on_range_changed)
        row_max.addWidget(self.max_spinbox)
        row_max.addStretch()
        range_layout.addLayout(row_max)
        
        g1_layout.addWidget(self.range_widget)
        
        self.specific_radio = QRadioButton("Clusters specifiques")
        self.specific_radio.toggled.connect(self.on_mode_changed)
        self.mode_group.addButton(self.specific_radio)
        g1_layout.addWidget(self.specific_radio)
        
        # Specific clusters input
        self.specific_widget = QWidget()
        spec_layout = QVBoxLayout(self.specific_widget)
        spec_layout.setContentsMargins(15, 0, 0, 0)
        spec_layout.setSpacing(3)
        
        self.clusters_input = QLineEdit()
        self.clusters_input.setPlaceholderText("ex: 5, 12, 45, 78")
        self.clusters_input.setMaximumWidth(180)
        spec_layout.addWidget(self.clusters_input)
        
        self.apply_btn = QPushButton("Appliquer")
        self.apply_btn.setMaximumWidth(80)
        self.apply_btn.clicked.connect(self.apply_specific_clusters)
        self.apply_btn.setStyleSheet("background: #2196F3; color: white; padding: 3px 8px;")
        spec_layout.addWidget(self.apply_btn)
        
        self.specific_widget.setEnabled(False)
        g1_layout.addWidget(self.specific_widget)
        
        self.info_label = ElidedLabel("Chargement...")
        self.info_label.setStyleSheet("color: #666; font-size: 9px; padding: 2px;")
        g1_layout.addWidget(self.info_label)
        
        left_layout.addWidget(grp1)
        
        # --- Display Options ---
        grp2 = QGroupBox("Affichage")
        g2_layout = QVBoxLayout(grp2)
        g2_layout.setSpacing(3)
        g2_layout.setContentsMargins(6, 12, 6, 6)
        
        row_size = QHBoxLayout()
        row_size.addWidget(QLabel("Taille:"))
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(1, 30)
        self.size_slider.setValue(10)
        self.size_slider.valueChanged.connect(self.schedule_update)
        row_size.addWidget(self.size_slider)
        g2_layout.addLayout(row_size)
        
        row_alpha = QHBoxLayout()
        row_alpha.addWidget(QLabel("Alpha:"))
        self.alpha_slider = QSlider(Qt.Orientation.Horizontal)
        self.alpha_slider.setRange(10, 100)
        self.alpha_slider.setValue(70)
        self.alpha_slider.valueChanged.connect(self.schedule_update)
        row_alpha.addWidget(self.alpha_slider)
        g2_layout.addLayout(row_alpha)
        
        row_sample = QHBoxLayout()
        row_sample.addWidget(QLabel("Echant.:"))
        self.sample_combo = QComboBox()
        self.sample_combo.addItems(["1%", "5%", "10%", "25%", "50%", "100%"])
        self.sample_combo.setCurrentIndex(1)
        self.sample_combo.currentIndexChanged.connect(self.schedule_update)
        row_sample.addWidget(self.sample_combo)
        g2_layout.addLayout(row_sample)
        
        self.centroids_cb = QCheckBox("Afficher centroides")
        self.centroids_cb.setChecked(True)
        self.centroids_cb.stateChanged.connect(self.schedule_update)
        g2_layout.addWidget(self.centroids_cb)
        
        self.hover_cb = QCheckBox("Info au survol")
        self.hover_cb.setChecked(True)
        self.hover_cb.stateChanged.connect(self.toggle_hover)
        g2_layout.addWidget(self.hover_cb)
        
        left_layout.addWidget(grp2)
        
        # --- Zoom Controls ---
        grp_zoom = QGroupBox("Zoom")
        zoom_layout = QHBoxLayout(grp_zoom)
        zoom_layout.setContentsMargins(6, 12, 6, 6)
        zoom_layout.setSpacing(4)
        
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(28, 24)
        self.zoom_in_btn.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_layout.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedSize(28, 24)
        self.zoom_out_btn.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(self.zoom_out_btn)
        
        self.zoom_reset_btn = QPushButton("Reset")
        self.zoom_reset_btn.setFixedSize(45, 24)
        self.zoom_reset_btn.clicked.connect(self.zoom_reset)
        zoom_layout.addWidget(self.zoom_reset_btn)
        
        self.zoom_fit_btn = QPushButton("Fit")
        self.zoom_fit_btn.setFixedSize(35, 24)
        self.zoom_fit_btn.clicked.connect(self.zoom_fit)
        zoom_layout.addWidget(self.zoom_fit_btn)
        
        zoom_layout.addStretch()
        left_layout.addWidget(grp_zoom)
        
        # --- Point Info ---
        grp3 = QGroupBox("Selection")
        g3_layout = QVBoxLayout(grp3)
        g3_layout.setSpacing(4)
        g3_layout.setContentsMargins(6, 12, 6, 6)
        
        self.point_info = QWidget()
        self.point_info.setStyleSheet("""
            background: white; padding: 4px; border-radius: 3px; border: 1px solid #ddd;
        """)
        point_layout = QVBoxLayout(self.point_info)
        point_layout.setContentsMargins(4, 4, 4, 4)
        point_layout.setSpacing(1)
        
        self.lbl_point = ElidedLabel("Point: -")
        self.lbl_cluster = ElidedLabel("Cluster: -")
        self.lbl_file = ElidedLabel("Fichier: -")
        self.lbl_channel = ElidedLabel("Canal: -")
        self.lbl_time = ElidedLabel("Temps: -")
        
        for lbl in [self.lbl_point, self.lbl_cluster, self.lbl_file, self.lbl_channel, self.lbl_time]:
            lbl.setStyleSheet("font-family: Consolas; font-size: 9px; background: transparent;")
            point_layout.addWidget(lbl)
        
        g3_layout.addWidget(self.point_info)
        
        btn_layout = QHBoxLayout()
        self.play_btn = QPushButton("Ecouter")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.play_audio)
        self.play_btn.setStyleSheet("""
            QPushButton { background: #4CAF50; color: white; padding: 5px 10px; 
                         border-radius: 3px; font-weight: bold; }
            QPushButton:hover { background: #45a049; }
            QPushButton:disabled { background: #ccc; color: #888; }
        """)
        btn_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_audio)
        self.stop_btn.setStyleSheet("""
            QPushButton { background: #777; color: white; padding: 5px 8px; border-radius: 3px; }
            QPushButton:hover { background: #555; }
            QPushButton:disabled { background: #ccc; color: #888; }
        """)
        btn_layout.addWidget(self.stop_btn)
        g3_layout.addLayout(btn_layout)
        
        left_layout.addWidget(grp3)
        
        # --- Stats ---
        grp4 = QGroupBox("Statistiques")
        g4_layout = QVBoxLayout(grp4)
        g4_layout.setContentsMargins(6, 12, 6, 6)
        
        self.stats_widget = QWidget()
        stats_inner = QVBoxLayout(self.stats_widget)
        stats_inner.setContentsMargins(0, 0, 0, 0)
        stats_inner.setSpacing(1)
        
        self.stat_total = ElidedLabel("Total: -")
        self.stat_clusters = ElidedLabel("Clusters: -")
        self.stat_avg = ElidedLabel("Moyenne: -")
        self.stat_minmax = ElidedLabel("Min/Max: -")
        
        for lbl in [self.stat_total, self.stat_clusters, self.stat_avg, self.stat_minmax]:
            lbl.setStyleSheet("font-size: 9px;")
            stats_inner.addWidget(lbl)
        
        g4_layout.addWidget(self.stats_widget)
        left_layout.addWidget(grp4)
        
        left_layout.addStretch()
        
        splitter.addWidget(left_panel)
        
        # === RIGHT PANEL: Plot ===
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Figure - optimized for performance
        self.figure = Figure(figsize=(8, 6), dpi=80, facecolor='white')
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        
        # Pan state
        self._pan_start = None
        
        # Store original limits for reset
        self.original_xlim = None
        self.original_ylim = None
        
        self.toolbar = NavigationToolbar(self.canvas, self)
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)
        
        self.status_label = QLabel("Pret")
        self.status_label.setStyleSheet("background: #f0f0f0; padding: 4px; font-size: 9px;")
        right_layout.addWidget(self.status_label)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([240, 960])
        
        layout.addWidget(splitter)
    
    def on_mode_changed(self):
        """Switch between range and specific mode"""
        if self.range_radio.isChecked():
            self.selection_mode = 'range'
            self.range_widget.setEnabled(True)
            self.specific_widget.setEnabled(False)
            self.schedule_update()
        else:
            self.selection_mode = 'specific'
            self.range_widget.setEnabled(False)
            self.specific_widget.setEnabled(True)
    
    def on_range_changed(self):
        """Handle min/max range change"""
        min_val = self.min_spinbox.value()
        max_val = self.max_spinbox.value()
        if min_val > max_val:
            self.max_spinbox.setValue(min_val)
        self.schedule_update()
    
    def apply_specific_clusters(self):
        """Parse and apply specific cluster selection"""
        text = self.clusters_input.text().strip()
        if not text:
            self.specific_clusters = []
            return
        
        try:
            clusters = []
            for part in text.replace(' ', '').split(','):
                if '-' in part:
                    start, end = part.split('-')
                    clusters.extend(range(int(start), int(end) + 1))
                else:
                    clusters.append(int(part))
            
            # Validate clusters exist
            valid = [c for c in clusters if c in self.cluster_sizes]
            self.specific_clusters = valid
            self.info_label.setText(f"Selection: {len(valid)} clusters")
            self.schedule_update()
        except ValueError:
            self.info_label.setText("Format invalide!")
    
    def toggle_hover(self, state):
        """Enable/disable hover cursor"""
        if self.cursor:
            self.cursor.remove()
            self.cursor = None
        if state and hasattr(self, 'scatter') and self.scatter:
            self._setup_hover_cursor()
    
    def _setup_hover_cursor(self):
        """Setup mplcursors for hover"""
        try:
            if self.scatter is None:
                return
            self.cursor = mplcursors.cursor(self.scatter, hover=True)
            
            @self.cursor.connect("add")
            def on_add(sel):
                idx = self.displayed_indices[sel.index]
                cid = self.labels[idx]
                size = self.cluster_sizes.get(cid, 0)
                sel.annotation.set_text(f"Cluster {cid}\n{size:,} segments")
                sel.annotation.get_bbox_patch().set_alpha(0.9)
        except Exception as e:
            print(f"Hover setup error: {e}")
    
    def zoom_in(self):
        """Zoom in on the plot"""
        if self.ax:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2
            x_range = (xlim[1] - xlim[0]) * 0.4
            y_range = (ylim[1] - ylim[0]) * 0.4
            self.ax.set_xlim(x_center - x_range, x_center + x_range)
            self.ax.set_ylim(y_center - y_range, y_center + y_range)
            self.canvas.draw_idle()
    
    def zoom_out(self):
        """Zoom out on the plot"""
        if self.ax:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2
            x_range = (xlim[1] - xlim[0]) * 0.7
            y_range = (ylim[1] - ylim[0]) * 0.7
            self.ax.set_xlim(x_center - x_range, x_center + x_range)
            self.ax.set_ylim(y_center - y_range, y_center + y_range)
            self.canvas.draw_idle()
    
    def zoom_reset(self):
        """Reset to original view"""
        if self.ax and self.original_xlim and self.original_ylim:
            self.ax.set_xlim(self.original_xlim)
            self.ax.set_ylim(self.original_ylim)
            self.canvas.draw_idle()
    
    def zoom_fit(self):
        """Fit to displayed data"""
        if self.ax and self.displayed_indices is not None:
            x = np.array(self.embeddings_2d[self.displayed_indices, 0])
            y = np.array(self.embeddings_2d[self.displayed_indices, 1])
            margin = 0.05
            x_range = x.max() - x.min()
            y_range = y.max() - y.min()
            self.ax.set_xlim(x.min() - margin * x_range, x.max() + margin * x_range)
            self.ax.set_ylim(y.min() - margin * y_range, y.max() + margin * y_range)
            self.canvas.draw_idle()
    
    def on_scroll(self, event):
        """Handle mouse scroll for zoom"""
        if event.inaxes != self.ax:
            return
        
        # Zoom factor
        base_scale = 1.2
        if event.button == 'up':
            scale = 1 / base_scale
        elif event.button == 'down':
            scale = base_scale
        else:
            return
        
        # Get current limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        # Get mouse position
        xdata, ydata = event.xdata, event.ydata
        
        # Calculate new limits (zoom centered on mouse position)
        new_xlim = [xdata - (xdata - xlim[0]) * scale,
                    xdata + (xlim[1] - xdata) * scale]
        new_ylim = [ydata - (ydata - ylim[0]) * scale,
                    ydata + (ylim[1] - ydata) * scale]
        
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        self.canvas.draw_idle()
    
    def on_mouse_press(self, event):
        """Handle mouse press for pan (right click or middle click)"""
        if event.inaxes != self.ax:
            return
        if event.button in [2, 3]:  # Middle or right click
            self._pan_start = (event.xdata, event.ydata)
            self.canvas.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def on_mouse_release(self, event):
        """Handle mouse release"""
        if event.button in [2, 3]:
            self._pan_start = None
            self.canvas.setCursor(Qt.CursorShape.ArrowCursor)
    
    def on_mouse_move(self, event):
        """Handle mouse move for panning"""
        if self._pan_start is None or event.inaxes != self.ax:
            return
        if event.xdata is None or event.ydata is None:
            return
        
        # Calculate delta
        dx = self._pan_start[0] - event.xdata
        dy = self._pan_start[1] - event.ydata
        
        # Get current limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        # Apply pan
        self.ax.set_xlim(xlim[0] + dx, xlim[1] + dx)
        self.ax.set_ylim(ylim[0] + dy, ylim[1] + dy)
        
        self.canvas.draw_idle()
        
    def load_data(self):
        """Load clustering data"""
        try:
            self.status_label.setText("Chargement des donnees...")
            base_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'perch2')
            
            self.embeddings_2d = np.load(os.path.join(base_path, 'embeddings_2d_ALL.npy'), mmap_mode='r')
            self.labels = np.load(os.path.join(base_path, 'labels.npy'))
            
            with open(os.path.join(base_path, 'perch_info_FINAL.pkl'), 'rb') as f:
                self.metadata = pickle.load(f)
            
            # Compute cluster stats
            unique, counts = np.unique(self.labels, return_counts=True)
            self.cluster_sizes = dict(zip(unique, counts))
            self.n_clusters = len(unique)
            
            # Sort by size (descending)
            self.sorted_clusters = sorted(self.cluster_sizes.keys(), 
                                         key=lambda x: self.cluster_sizes[x], 
                                         reverse=True)
            
            # Update UI limits
            self.min_spinbox.setMaximum(self.n_clusters)
            self.max_spinbox.setMaximum(self.n_clusters)
            self.info_label.setText(f"{self.n_clusters} clusters | {len(self.labels):,} pts")
            
            # Stats
            sizes = list(self.cluster_sizes.values())
            self.stat_total.setText(f"Total: {len(self.labels):,} segments")
            self.stat_clusters.setText(f"Clusters: {self.n_clusters}")
            self.stat_avg.setText(f"Moyenne: {np.mean(sizes):.0f} | Med: {np.median(sizes):.0f}")
            self.stat_minmax.setText(f"Min: {np.min(sizes)} | Max: {np.max(sizes):,}")
            
            self.status_label.setText("Donnees chargees")
            self._do_update_plot()
            
        except Exception as e:
            self.status_label.setText(f"Erreur: {e}")
            print(f"Load error: {e}")
            
    def schedule_update(self):
        """Debounced update - wait 200ms before updating"""
        self.update_timer.start(200)
        
    def _do_update_plot(self):
        """Actually update the plot"""
        if self.embeddings_2d is None:
            return
            
        self.status_label.setText("Mise a jour...")
        
        # Get display params
        sample_rates = [0.01, 0.05, 0.10, 0.25, 0.50, 1.0]
        sample_rate = sample_rates[self.sample_combo.currentIndex()]
        point_size = self.size_slider.value()
        alpha = self.alpha_slider.value() / 100.0
        
        # Determine which clusters to show based on mode
        if self.selection_mode == 'range':
            min_rank = self.min_spinbox.value()
            max_rank = self.max_spinbox.value()
            clusters_to_show = self.sorted_clusters[min_rank - 1:max_rank]
        else:
            clusters_to_show = self.specific_clusters if self.specific_clusters else self.sorted_clusters[:20]
        
        n_clusters = len(clusters_to_show)
        
        # Build mask
        mask = np.isin(self.labels, clusters_to_show)
        indices = np.where(mask)[0]
        
        # Sample
        if sample_rate < 1.0:
            n_samples = max(100, int(len(indices) * sample_rate))
            if n_samples < len(indices):
                indices = np.random.choice(indices, n_samples, replace=False)
        
        self.displayed_indices = indices
        
        # Get data
        x = np.array(self.embeddings_2d[indices, 0])
        y = np.array(self.embeddings_2d[indices, 1])
        c = self.labels[indices]
        
        # Store current view if zoomed
        current_xlim = self.ax.get_xlim() if self.ax.has_data() else None
        current_ylim = self.ax.get_ylim() if self.ax.has_data() else None
        
        # Clear and plot
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        
        self.scatter = self.ax.scatter(x, y, c=c, cmap='tab20', s=point_size, 
                                       alpha=alpha, edgecolors='none', picker=True)
        
        # Centroids
        if self.centroids_cb.isChecked():
            for cid in clusters_to_show[:min(20, n_clusters)]:
                cmask = self.labels == cid
                if np.sum(cmask) > 0:
                    cx = np.mean(self.embeddings_2d[cmask, 0])
                    cy = np.mean(self.embeddings_2d[cmask, 1])
                    self.ax.plot(cx, cy, 'ko', markersize=6, markerfacecolor='white', 
                                markeredgewidth=1.5, zorder=10)
                    self.ax.annotate(str(cid), (cx, cy), fontsize=7, ha='center', 
                                    va='bottom', fontweight='bold', 
                                    xytext=(0, 3), textcoords='offset points')
        
        # Selected point
        if self.selected_point_idx is not None:
            sx = self.embeddings_2d[self.selected_point_idx, 0]
            sy = self.embeddings_2d[self.selected_point_idx, 1]
            self.ax.plot(sx, sy, 'r*', markersize=18, markeredgecolor='black', 
                        markeredgewidth=1.5, zorder=20)
        
        self.ax.set_xlabel('UMAP Dim 1', fontsize=9)
        self.ax.set_ylabel('UMAP Dim 2', fontsize=9)
        self.ax.set_title(f'{len(indices):,} points | {n_clusters} clusters', fontsize=10)
        self.ax.grid(True, alpha=0.2, linestyle='--')
        self.ax.tick_params(labelsize=8)
        
        # Store original limits for reset
        if self.original_xlim is None:
            self.original_xlim = self.ax.get_xlim()
            self.original_ylim = self.ax.get_ylim()
        
        # Restore zoom if we had one
        if current_xlim and current_ylim:
            self.ax.set_xlim(current_xlim)
            self.ax.set_ylim(current_ylim)
        
        # Colorbar
        cbar = self.figure.colorbar(self.scatter, ax=self.ax, shrink=0.5, pad=0.02)
        cbar.ax.tick_params(labelsize=7)
        cbar.set_label('Cluster ID', fontsize=8)
        
        self.figure.tight_layout()
        self.canvas.draw_idle()
        
        # Setup hover if enabled
        if self.hover_cb.isChecked():
            self._setup_hover_cursor()
        
        self.status_label.setText(f"Affiche: {len(indices):,} pts | {n_clusters} clusters")
        
    def on_click(self, event):
        """Handle click"""
        if event.inaxes is None or self.displayed_indices is None:
            return
        if event.button != 1:
            return
            
        # Find closest point
        x_click, y_click = event.xdata, event.ydata
        x = np.array(self.embeddings_2d[self.displayed_indices, 0])
        y = np.array(self.embeddings_2d[self.displayed_indices, 1])
        
        dist = (x - x_click)**2 + (y - y_click)**2
        closest = np.argmin(dist)
        self.selected_point_idx = self.displayed_indices[closest]
        
        # Update info labels (using elided labels)
        meta = self.metadata[self.selected_point_idx]
        cid = self.labels[self.selected_point_idx]
        csize = self.cluster_sizes.get(cid, 0)
        
        self.lbl_point.setText(f"Point: {self.selected_point_idx:,}")
        self.lbl_cluster.setText(f"Cluster: {cid} ({csize:,} pts)")
        self.lbl_file.setText(f"Fichier: {meta['file']}")
        self.lbl_channel.setText(f"Canal: {meta['channel']}")
        self.lbl_time.setText(f"Temps: {meta['start']:.1f}s - {meta['end']:.1f}s")
        
        self.selected_meta = meta
        self.play_btn.setEnabled(True)
        
        self._do_update_plot()
        
    def play_audio(self):
        """Play selected audio"""
        if self.selected_meta is None:
            return
            
        self.play_btn.setEnabled(False)
        self.play_btn.setText("Chargement...")
        
        meta = self.selected_meta
        self.audio_thread = AudioLoaderThread(meta['file'], meta['start'], meta['end'])
        self.audio_thread.finished.connect(self.on_audio_loaded)
        self.audio_thread.error.connect(self.on_audio_error)
        self.audio_thread.start()
        
    def on_audio_loaded(self, audio, sr):
        """Audio ready"""
        self.play_btn.setText("Ecouter")
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        
        try:
            import sounddevice as sd
            sd.stop()
            sd.play(audio, sr)
            self.is_playing = True
        except Exception as e:
            self.point_label.setText(self.point_label.text() + f"\nErreur audio: {e}")
            
    def on_audio_error(self, msg):
        """Audio error"""
        self.play_btn.setText("Erreur")
        self.play_btn.setEnabled(True)
        self.point_label.setText(self.point_label.text() + f"\nErreur: {msg}")
        
    def stop_audio(self):
        """Stop"""
        try:
            import sounddevice as sd
            sd.stop()
            self.stop_btn.setEnabled(False)
        except:
            pass
            
    def closeEvent(self, event):
        self.stop_audio()
        if self.audio_thread and self.audio_thread.isRunning():
            self.audio_thread.terminate()
        super().closeEvent(event)
