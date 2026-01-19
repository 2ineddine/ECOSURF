import os
import pickle
import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton,
    QFrame, QComboBox, QSlider, QLineEdit, QSizePolicy, QGroupBox,
    QListWidget, QListWidgetItem, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QUrl
from PyQt6.QtGui import QIntValidator, QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import urllib.parse
import json

import pyqtgraph as pg
pg.setConfigOptions(antialias=False, useOpenGL=True)

try:
    import sounddevice as sd
    AUDIO_OK = True
except:
    AUDIO_OK = False


class AudioThread(QThread):
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
            creds_path = None
            for p in ['credentials.json', 'src/credentials.json', '../credentials.json']:
                if os.path.exists(p):
                    creds_path = p
                    break
            if not creds_path:
                self.error.emit("credentials.json introuvable")
                return
            with open(creds_path, 'r') as f:
                creds = json.load(f)
            s3 = boto3.client('s3', endpoint_url=creds['endpoint'],
                              aws_access_key_id=creds['ACCESS_KEY'],
                              aws_secret_access_key=creds['SECRET_KEY'])
            site = self.file_path.split('_')[0]
            s3_key = f"2019/{site}/Data/{self.file_path}"
            buf = io.BytesIO()
            s3.download_fileobj(creds['bucket'], s3_key, buf)
            buf.seek(0)
            audio, sr = librosa.load(buf, sr=None, offset=self.start_time, duration=self.end_time - self.start_time)
            self.finished.emit(audio, sr)
        except Exception as e:
            self.error.emit(str(e)[:50])


class ClusteringDialogFast(QDialog):
    show_spectrogram_signal = pyqtSignal(str, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Carte 2D - Clusters")
        self.setMinimumSize(1100, 750)
        self.resize(1300, 850)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)

        self.embeddings_2d = None
        self.labels = None
        self.metadata = None
        self.cluster_sizes = {}
        self.n_clusters = 0
        self.displayed_indices = None
        self.scatter = None
        self.selected_marker = None
        self.selected_meta = None
        self.selected_gidx = None
        self.sample_pct = 10
        self.point_size = 8
        self.colors = None
        self.audio_thread = None
        self.is_playing = False
        self.cluster_species = {}  # Mapping cluster_id -> species name
        self._current_species = None
        self._image_cache = {}  # Cache pour les images
        self._network_manager = None

        self.init_ui()
        QTimer.singleShot(100, self.load_data)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        top_bar = QFrame()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background: #2C3E50; border-radius: 8px;")
        tb = QHBoxLayout(top_bar)
        tb.setContentsMargins(15, 8, 15, 8)
        tb.setSpacing(15)

        tb.addWidget(self.make_label("Clusters:", True))
        self.min_spin = QSpinBox()
        self.min_spin.setRange(1, 488)
        self.min_spin.setValue(1)
        self.min_spin.setFixedWidth(60)
        self.min_spin.setStyleSheet("background: white; border-radius: 4px; padding: 2px;")
        self.min_spin.valueChanged.connect(self.schedule_update)
        tb.addWidget(self.min_spin)

        tb.addWidget(self.make_label("a"))
        self.max_spin = QSpinBox()
        self.max_spin.setRange(1, 488)
        self.max_spin.setValue(50)
        self.max_spin.setFixedWidth(60)
        self.max_spin.setStyleSheet("background: white; border-radius: 4px; padding: 2px;")
        self.max_spin.valueChanged.connect(self.schedule_update)
        tb.addWidget(self.max_spin)

        self.add_sep(tb)

        tb.addWidget(self.make_label("Echantillon:", True))
        self.sample_combo = QComboBox()
        self.sample_combo.addItems(["5%", "10%", "20%", "50%", "100%"])
        self.sample_combo.setCurrentIndex(1)
        self.sample_combo.setFixedWidth(70)
        self.sample_combo.setStyleSheet("background: white; border-radius: 4px;")
        self.sample_combo.currentIndexChanged.connect(self.on_sample_changed)
        tb.addWidget(self.sample_combo)

        self.add_sep(tb)

        tb.addWidget(self.make_label("Taille:", True))
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(3, 30)
        self.size_slider.setValue(8)
        self.size_slider.setFixedWidth(100)
        self.size_slider.valueChanged.connect(self.on_size_changed)
        tb.addWidget(self.size_slider)

        self.add_sep(tb)

        # Bouton pour afficher la liste des clusters annotes
        self.show_annotated_btn = QPushButton("Clusters Annotes")
        self.show_annotated_btn.setFixedSize(120, 32)
        self.show_annotated_btn.setStyleSheet("background: #27AE60; color: white; border: none; border-radius: 4px; font-weight: 600;")
        self.show_annotated_btn.clicked.connect(self.toggle_annotated_panel)
        tb.addWidget(self.show_annotated_btn)

        tb.addStretch()

        self.reset_btn = QPushButton("Reset Vue")
        self.reset_btn.setFixedSize(80, 32)
        self.reset_btn.setStyleSheet("background: #E74C3C; color: white; border: none; border-radius: 4px; font-weight: 600;")
        self.reset_btn.clicked.connect(self.reset_view)
        tb.addWidget(self.reset_btn)

        self.pts_label = QLabel("Chargement...")
        self.pts_label.setStyleSheet("color: #ECF0F1; font-size: 12px;")
        self.pts_label.setFixedWidth(180)
        tb.addWidget(self.pts_label)

        layout.addWidget(top_bar)

        content = QHBoxLayout()
        content.setSpacing(10)

        left_panel = QFrame()
        left_panel.setFixedWidth(280)
        left_panel.setStyleSheet("background: #F8F9FA; border: 1px solid #E0E0E0; border-radius: 8px;")
        lp = QVBoxLayout(left_panel)
        lp.setContentsMargins(12, 12, 12, 12)
        lp.setSpacing(12)

        zoom_group = QGroupBox("Zoom sur Cluster")
        zoom_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #BDC3C7; border-radius: 6px; margin-top: 8px; padding-top: 8px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        zg = QVBoxLayout(zoom_group)
        zg.setSpacing(8)

        zrow = QHBoxLayout()
        zrow.addWidget(QLabel("Cluster ID:"))
        self.cluster_input = QLineEdit()
        self.cluster_input.setPlaceholderText("ex: 11")
        self.cluster_input.setFixedWidth(80)
        self.cluster_input.setValidator(QIntValidator(0, 999))
        self.cluster_input.returnPressed.connect(self.zoom_to_cluster)
        zrow.addWidget(self.cluster_input)
        self.goto_btn = QPushButton("Zoom")
        self.goto_btn.setFixedWidth(60)
        self.goto_btn.setStyleSheet("background: #3498DB; color: white; border: none; border-radius: 4px;")
        self.goto_btn.clicked.connect(self.zoom_to_cluster)
        zrow.addWidget(self.goto_btn)
        zg.addLayout(zrow)

        self.zoom_status = QLabel("")
        self.zoom_status.setStyleSheet("color: #7F8C8D; font-size: 11px;")
        self.zoom_status.setWordWrap(True)
        zg.addWidget(self.zoom_status)

        lp.addWidget(zoom_group)

        seg_group = QGroupBox("Segment Selectionne")
        seg_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #BDC3C7; border-radius: 6px; margin-top: 8px; padding-top: 8px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        sg = QVBoxLayout(seg_group)
        sg.setSpacing(6)

        self.seg_cluster = QLabel("Cluster: -")
        self.seg_cluster.setStyleSheet("font-size: 12px;")
        sg.addWidget(self.seg_cluster)

        self.seg_file = QLabel("Fichier: -")
        self.seg_file.setStyleSheet("font-size: 11px; color: #555;")
        self.seg_file.setWordWrap(True)
        sg.addWidget(self.seg_file)

        self.seg_time = QLabel("Temps: -")
        self.seg_time.setStyleSheet("font-size: 11px; color: #555;")
        sg.addWidget(self.seg_time)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.play_btn = QPushButton("Ecouter")
        self.play_btn.setEnabled(False)
        self.play_btn.setFixedHeight(36)
        self.play_btn.setStyleSheet("background: #27AE60; color: white; border: none; border-radius: 4px; font-weight: 600;")
        self.play_btn.clicked.connect(self.play_audio)
        btn_row.addWidget(self.play_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setFixedHeight(36)
        self.stop_btn.setStyleSheet("background: #95A5A6; color: white; border: none; border-radius: 4px;")
        self.stop_btn.clicked.connect(self.stop_audio)
        btn_row.addWidget(self.stop_btn)

        sg.addLayout(btn_row)

        self.spec_btn = QPushButton("Voir Spectrogramme")
        self.spec_btn.setEnabled(False)
        self.spec_btn.setFixedHeight(36)
        self.spec_btn.setStyleSheet("background: #9B59B6; color: white; border: none; border-radius: 4px; font-weight: 600;")
        self.spec_btn.clicked.connect(self.show_spectrogram)
        sg.addWidget(self.spec_btn)

        self.audio_status = QLabel("")
        self.audio_status.setStyleSheet("color: #7F8C8D; font-size: 10px;")
        self.audio_status.setWordWrap(True)
        sg.addWidget(self.audio_status)

        # Espece detectee (lien cliquable)
        self.species_label = QLabel("")
        self.species_label.setStyleSheet("font-size: 11px; color: #16A085; padding-top: 4px;")
        self.species_label.setWordWrap(True)
        self.species_label.setOpenExternalLinks(True)
        self.species_label.setTextFormat(Qt.TextFormat.RichText)
        sg.addWidget(self.species_label)

        # Image de l'espece
        self.species_image = QLabel()
        self.species_image.setFixedSize(120, 90)
        self.species_image.setStyleSheet("border: 1px solid #E0E0E0; border-radius: 4px; background: #FAFAFA;")
        self.species_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.species_image.setScaledContents(False)
        self.species_image.setVisible(False)
        sg.addWidget(self.species_image)

        lp.addWidget(seg_group)

        info_group = QGroupBox("Instructions")
        info_group.setStyleSheet("QGroupBox { font-weight: bold; border: 1px solid #BDC3C7; border-radius: 6px; margin-top: 8px; padding-top: 8px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; }")
        ig = QVBoxLayout(info_group)
        ig.setSpacing(4)

        for txt in ["Scroll = Zoom", "Clic droit = Pan", "Clic gauche = Selection"]:
            l = QLabel(txt)
            l.setStyleSheet("font-size: 11px; color: #555;")
            ig.addWidget(l)

        lp.addWidget(info_group)
        lp.addStretch()

        content.addWidget(left_panel)

        plot_frame = QFrame()
        plot_frame.setStyleSheet("background: white; border: 1px solid #E0E0E0; border-radius: 8px;")
        pf_layout = QVBoxLayout(plot_frame)
        pf_layout.setContentsMargins(5, 5, 5, 5)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#FFFFFF')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_widget.setLabel('bottom', 'UMAP 1', color='#555')
        self.plot_widget.setLabel('left', 'UMAP 2', color='#555')
        vb = self.plot_widget.getPlotItem().getViewBox()
        vb.setMouseMode(pg.ViewBox.PanMode)
        if hasattr(vb, "setClipToView"):
            vb.setClipToView(True)
        self.plot_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        pf_layout.addWidget(self.plot_widget)

        # Hover tooltip as QLabel overlay (not pyqtgraph TextItem)
        self.hover_label = QLabel(self.plot_widget)
        self.hover_label.setStyleSheet("""
            QLabel {
                background-color: rgba(44, 62, 80, 0.95);
                color: white;
                padding: 6px 10px;
                border-radius: 4px;
                border: 1px solid #1a252f;
                font-size: 11px;
            }
        """)
        self.hover_label.setVisible(False)
        self.hover_label.raise_()
        content.addWidget(plot_frame, stretch=1)

        # Panneau droit pour les clusters annotes (cache par defaut)
        self.annotated_panel = QFrame()
        self.annotated_panel.setFixedWidth(250)
        self.annotated_panel.setStyleSheet("background: #F8F9FA; border: 1px solid #E0E0E0; border-radius: 8px;")
        self.annotated_panel.setVisible(False)
        ap = QVBoxLayout(self.annotated_panel)
        ap.setContentsMargins(10, 10, 10, 10)
        ap.setSpacing(8)

        ap_header = QLabel("Clusters Annotes")
        ap_header.setStyleSheet("font-size: 13px; font-weight: bold; color: #2C3E50; padding-bottom: 4px;")
        ap.addWidget(ap_header)

        self.annotated_list = QListWidget()
        self.annotated_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                background: white;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #F0F0F0;
            }
            QListWidget::item:selected {
                background: #3498DB;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background: #EBF5FB;
            }
        """)
        self.annotated_list.itemDoubleClicked.connect(self.on_annotated_cluster_clicked)
        ap.addWidget(self.annotated_list)

        ap_hint = QLabel("Double-clic pour zoomer")
        ap_hint.setStyleSheet("font-size: 10px; color: #7F8C8D;")
        ap.addWidget(ap_hint)

        content.addWidget(self.annotated_panel)

        layout.addLayout(content, stretch=1)

        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_plot)

    def make_label(self, text, bold=False):
        lbl = QLabel(text)
        style = "color: white;"
        if bold:
            style += " font-weight: 600;"
        lbl.setStyleSheet(style)
        return lbl

    def add_sep(self, layout):
        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setFixedHeight(30)
        sep.setStyleSheet("background: #7F8C8D;")
        layout.addWidget(sep)

    def load_data(self):
        paths = ['perch2/', '../perch2/', '../../perch2/', 'src/perch2/']
        for base in paths:
            coords = os.path.join(base, 'embeddings_2d_ALL.npy')
            labels_f = os.path.join(base, 'labels_v2.npy')
            meta_f = os.path.join(base, 'perch_info_FINAL.pkl')
            species_f = os.path.join(base, 'cluster_species_mapping.pkl')
            if os.path.exists(coords) and os.path.exists(labels_f):
                try:
                    raw_emb = np.load(coords)
                    raw_labels = np.load(labels_f).astype(np.int32)
                    meta = None
                    if os.path.exists(meta_f):
                        with open(meta_f, 'rb') as f:
                            meta = pickle.load(f)
                    # Charger les labels BirdNET si disponibles
                    if os.path.exists(species_f):
                        with open(species_f, 'rb') as f:
                            self.cluster_species = pickle.load(f)
                        n_annotated = sum(1 for v in self.cluster_species.values() if v and v != 'Unknown')
                        print(f"Labels BirdNET charges: {n_annotated} clusters annotes")
                    else:
                        self.cluster_species = {}
                    mask = raw_labels != -1
                    valid_idx = np.where(mask)[0]
                    self.embeddings_2d = raw_emb[valid_idx].astype(np.float32)
                    self.labels = raw_labels[valid_idx]
                    if meta:
                        self.metadata = [meta[i] for i in valid_idx]
                    else:
                        self.metadata = None
                    unique, counts = np.unique(self.labels, return_counts=True)
                    self.cluster_sizes = dict(zip(unique.tolist(), counts.tolist()))
                    self.n_clusters = len(unique)
                    self.max_spin.setMaximum(min(488, self.n_clusters))
                    self.max_spin.setValue(min(50, self.n_clusters))
                    self.build_colors()
                    self.update_plot()
                    n_ann = sum(1 for v in self.cluster_species.values() if v and v != 'Unknown')
                    self.pts_label.setText(f"{len(self.embeddings_2d):,} pts | {self.n_clusters} clusters | {n_ann} annotes")
                    return
                except Exception as e:
                    self.pts_label.setText(f"Erreur: {str(e)[:30]}")
                    return
        self.pts_label.setText("Donnees non trouvees")

    def build_colors(self):
        cmap = pg.colormap.get('CET-R4')
        unique_labels = sorted(self.cluster_sizes.keys())
        n = len(unique_labels)
        label_to_color = {}
        for i, lbl in enumerate(unique_labels):
            label_to_color[lbl] = cmap.map(i / max(n-1, 1), mode='qcolor')
        self.label_colors = label_to_color

    def on_sample_changed(self, idx):
        self.sample_pct = [5, 10, 20, 50, 100][idx]
        self.schedule_update()

    def toggle_annotated_panel(self):
        """Affiche/cache le panneau des clusters annotes"""
        is_visible = self.annotated_panel.isVisible()
        self.annotated_panel.setVisible(not is_visible)
        if not is_visible:
            self.populate_annotated_list()

    def populate_annotated_list(self):
        """Remplit la liste des clusters annotes"""
        self.annotated_list.clear()
        if not self.cluster_species:
            return

        # Trier par cluster_id
        annotated = [
            (cid, species) for cid, species in self.cluster_species.items()
            if species and species != 'Unknown'
        ]
        annotated.sort(key=lambda x: x[0])

        for cid, species in annotated:
            size = self.cluster_sizes.get(cid, 0)
            item = QListWidgetItem(f"C{cid}: {species} ({size})")
            item.setData(Qt.ItemDataRole.UserRole, cid)
            self.annotated_list.addItem(item)

    def on_annotated_cluster_clicked(self, item):
        """Zoom sur le cluster selectionne dans la liste"""
        cid = item.data(Qt.ItemDataRole.UserRole)
        if cid is not None:
            self.cluster_input.setText(str(cid))
            self.zoom_to_cluster()

    def on_size_changed(self, val):
        self.point_size = val
        if self.scatter:
            self.scatter.setSize(val)

    def schedule_update(self):
        self.update_timer.start(150)

    def render_indices(self, indices, label_text=None):
        if self.embeddings_2d is None:
            return
        if self.selected_marker:
            self.plot_widget.removeItem(self.selected_marker)
            self.selected_marker = None

        indices = np.asarray(indices)
        if indices.size == 0:
            self.displayed_indices = np.array([], dtype=int)
            self.pts_label.setText("Aucun point")
            if self.scatter:
                self.scatter.setData([], [])
            return

        self.displayed_indices = indices
        x = self.embeddings_2d[self.displayed_indices, 0]
        y = self.embeddings_2d[self.displayed_indices, 1]
        brushes = [self.label_colors[self.labels[i]] for i in self.displayed_indices]

        if self.scatter is None:
            self.scatter = pg.ScatterPlotItem(
                pen=None,
                size=self.point_size,
                hoverable=True,
                hoverPen=pg.mkPen('#000000', width=2),
                hoverSize=self.point_size + 5,
                pxMode=True,
                useCache=False
            )
            self.scatter.sigClicked.connect(self.on_click)
            self.scatter.sigHovered.connect(self.on_hover)
            self.plot_widget.addItem(self.scatter)

        self.scatter.setData(
            x=x, y=y,
            brush=brushes,
            data=np.arange(len(self.displayed_indices))
        )

        if label_text:
            self.pts_label.setText(label_text)
        else:
            self.pts_label.setText(f"{len(self.displayed_indices):,} pts")

    def update_plot(self):
        if self.embeddings_2d is None:
            return

        min_r, max_r = self.min_spin.value(), self.max_spin.value()
        if min_r > max_r:
            min_r, max_r = max_r, min_r

        sorted_clusters = sorted(self.cluster_sizes.keys(), key=lambda x: self.cluster_sizes[x], reverse=True)
        selected_clusters = set(sorted_clusters[min_r-1:max_r])

        mask = np.isin(self.labels, list(selected_clusters))
        candidates = np.where(mask)[0]

        if len(candidates) == 0:
            self.pts_label.setText("Aucun point")
            return

        if self.sample_pct < 100:
            n_sample = max(1, int(len(candidates) * self.sample_pct / 100))
            rng = np.random.default_rng(42)
            self.displayed_indices = rng.choice(candidates, size=min(n_sample, len(candidates)), replace=False)
        else:
            self.displayed_indices = candidates

        label = f"{len(self.displayed_indices):,} pts | C{min_r}-{max_r} | {self.sample_pct}%"
        self.render_indices(self.displayed_indices, label_text=label)

    def on_hover(self, plot, points):
        if len(points) == 0:
            self.hover_label.setVisible(False)
            return
        local_idx = points[0].data()
        gidx = self.displayed_indices[local_idx]
        cluster = self.labels[gidx]
        cnt = self.cluster_sizes.get(cluster, 0)

        # Set tooltip text
        self.hover_label.setText(f"<b style='color:#3498DB;'>Cluster {cluster}</b><br/>{cnt:,} segments")

        # Convert data coordinates to pixel coordinates
        x, y = self.embeddings_2d[gidx]
        vb = self.plot_widget.getPlotItem().getViewBox()
        point_pixel = vb.mapViewToScene(pg.Point(x, y))
        point_widget = self.plot_widget.mapFromScene(point_pixel)

        # Position tooltip above and to the right of cursor
        self.hover_label.adjustSize()
        self.hover_label.move(int(point_widget.x()) + 15, int(point_widget.y()) - self.hover_label.height() - 10)
        self.hover_label.setVisible(True)
        self.hover_label.raise_()

    def on_click(self, plot, points):
        if len(points) == 0:
            return
        local_idx = points[0].data()
        gidx = self.displayed_indices[local_idx]
        self.selected_gidx = gidx
        x, y = self.embeddings_2d[gidx]

        if self.selected_marker:
            self.plot_widget.removeItem(self.selected_marker)

        self.selected_marker = pg.ScatterPlotItem(
            x=[x], y=[y],
            symbol='star',
            size=30,
            pen=pg.mkPen('#2C3E50', width=2),
            brush=pg.mkBrush('#F1C40F')
        )
        self.plot_widget.addItem(self.selected_marker)

        cluster = self.labels[gidx]
        cnt = self.cluster_sizes.get(cluster, 0)
        self.seg_cluster.setText(f"Cluster: {cluster} ({cnt:,} segments)")

        # Afficher l'espece du cluster avec lien Xeno-canto
        species = self.cluster_species.get(cluster, None)
        if species and species != 'Unknown':
            search_term = species.replace(' ', '+')
            xeno_url = f"https://xeno-canto.org/explore?query={search_term}"
            self.species_label.setText(
                f"<b style='color:#27AE60;'>Espece:</b> {species}<br/>"
                f"<a href='{xeno_url}' style='color:#16A085;'>Ecouter sur Xeno-canto</a>"
            )
            self._current_species = species
            # Charger l'image de l'espece
            self.load_species_image(species)
        else:
            self.species_label.setText("")
            self._current_species = None
            self.species_image.setVisible(False)

        if self.metadata and gidx < len(self.metadata):
            self.selected_meta = self.metadata[gidx]
            fname = self.selected_meta.get('file', '?')
            st = self.selected_meta.get('start', 0)
            en = self.selected_meta.get('end', 0)
            self.seg_file.setText(f"Fichier: {fname}")
            self.seg_time.setText(f"Temps: {st:.1f}s - {en:.1f}s")
            self.play_btn.setEnabled(AUDIO_OK)
            self.spec_btn.setEnabled(True)
            self.audio_status.setText("")
        else:
            self.selected_meta = None
            self.seg_file.setText("Fichier: -")
            self.seg_time.setText("Temps: -")
            self.play_btn.setEnabled(False)
            self.spec_btn.setEnabled(False)

    def zoom_to_cluster(self):
        txt = self.cluster_input.text().strip()
        if not txt or self.embeddings_2d is None:
            return
        try:
            cid = int(txt)
        except:
            return

        if cid not in self.cluster_sizes:
            self.zoom_status.setText(f"Cluster {cid} inexistant")
            return

        cluster_mask = self.labels == cid
        all_idx = np.where(cluster_mask)[0]

        if len(all_idx) == 0:
            self.zoom_status.setText(f"Cluster {cid} vide")
            return

        x_all = self.embeddings_2d[all_idx, 0]
        y_all = self.embeddings_2d[all_idx, 1]

        x_min, x_max = float(x_all.min()), float(x_all.max())
        y_min, y_max = float(y_all.min()), float(y_all.max())

        xr = max(x_max - x_min, 0.5)
        yr = max(y_max - y_min, 0.5)
        margin = 0.2

        self.plot_widget.setXRange(x_min - margin*xr, x_max + margin*xr, padding=0)
        self.plot_widget.setYRange(y_min - margin*yr, y_max + margin*yr, padding=0)

        if self.sample_pct < 100:
            n_sample = max(1, int(len(all_idx) * self.sample_pct / 100))
            rng = np.random.default_rng(42)
            show_idx = rng.choice(all_idx, size=min(n_sample, len(all_idx)), replace=False)
        else:
            show_idx = all_idx

        self.render_indices(show_idx, label_text=f"{len(show_idx):,} pts | Cluster {cid} | {self.sample_pct}%")
        self.zoom_status.setText(f"Cluster {cid}: {len(all_idx):,} total, {len(show_idx):,} affiches")

    def reset_view(self):
        self.plot_widget.autoRange()

    def play_audio(self):
        if not self.selected_meta or not AUDIO_OK:
            return
        self.play_btn.setEnabled(False)
        self.audio_status.setText("Telechargement...")

        file_path = self.selected_meta.get('file', '')
        start_t = self.selected_meta.get('start', 0)
        end_t = self.selected_meta.get('end', 5)

        self.audio_thread = AudioThread(file_path, start_t, end_t)
        self.audio_thread.finished.connect(self.on_audio_ready)
        self.audio_thread.error.connect(self.on_audio_error)
        self.audio_thread.start()

    def on_audio_ready(self, audio, sr):
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        self.is_playing = True
        duration = len(audio) / sr if sr > 0 else 0
        self.audio_status.setText(f"Lecture {duration:.1f}s")
        try:
            sd.stop()
            sd.play(audio, sr)
        except Exception as e:
            self.audio_status.setText(f"Erreur: {str(e)[:30]}")

    def on_audio_error(self, msg):
        self.play_btn.setEnabled(True)
        self.audio_status.setText(f"Erreur: {msg}")

    def stop_audio(self):
        if AUDIO_OK:
            sd.stop()
        self.is_playing = False
        self.stop_btn.setEnabled(False)
        self.audio_status.setText("Arrete")

    def show_spectrogram(self):
        if self.selected_meta:
            self.show_spectrogram_signal.emit(
                self.selected_meta.get('file', ''),
                self.selected_meta.get('start', 0),
                self.selected_meta.get('end', 5)
            )

    def load_species_image(self, species_name):
        """Charge l'image de l'espece depuis Wikipedia"""
        if not species_name or species_name == 'Unknown':
            self.species_image.setVisible(False)
            return

        # Verifier le cache
        if species_name in self._image_cache:
            self.display_species_image(self._image_cache[species_name])
            return

        # Initialiser le network manager si necessaire
        if self._network_manager is None:
            self._network_manager = QNetworkAccessManager()

        # Afficher un texte de chargement
        self.species_image.setText("Chargement...")
        self.species_image.setVisible(True)

        # Requete vers l'API Wikipedia pour trouver l'image
        search_term = urllib.parse.quote(species_name)
        wiki_api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{search_term}"

        request = QNetworkRequest(QUrl(wiki_api_url))
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, "ECOSURF/1.0")

        reply = self._network_manager.get(request)
        reply.finished.connect(lambda: self.on_wiki_response(reply, species_name))

    def on_wiki_response(self, reply, species_name):
        """Traite la reponse de l'API Wikipedia"""
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.species_image.setText("Image\nnon disponible")
            reply.deleteLater()
            return

        try:
            data = json.loads(bytes(reply.readAll()).decode('utf-8'))
            image_url = data.get('thumbnail', {}).get('source', None)

            if image_url:
                # Telecharger l'image
                img_request = QNetworkRequest(QUrl(image_url))
                img_request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, "ECOSURF/1.0")
                img_reply = self._network_manager.get(img_request)
                img_reply.finished.connect(lambda: self.on_image_downloaded(img_reply, species_name))
            else:
                self.species_image.setText("Pas d'image")
        except Exception as e:
            self.species_image.setText("Erreur")
        finally:
            reply.deleteLater()

    def on_image_downloaded(self, reply, species_name):
        """Traite l'image telechargee"""
        if reply.error() != QNetworkReply.NetworkError.NoError:
            self.species_image.setText("Erreur image")
            reply.deleteLater()
            return

        try:
            image_data = bytes(reply.readAll())
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                # Mettre en cache
                self._image_cache[species_name] = pixmap
                # Afficher si c'est toujours l'espece courante
                if self._current_species == species_name:
                    self.display_species_image(pixmap)
            else:
                self.species_image.setText("Format\ninvalide")
        except Exception as e:
            self.species_image.setText("Erreur")
        finally:
            reply.deleteLater()

    def display_species_image(self, pixmap):
        """Affiche l'image de l'espece avec les bonnes dimensions"""
        if pixmap.isNull():
            self.species_image.setText("Image vide")
            return

        # Redimensionner pour tenir dans 120x90 en gardant les proportions
        scaled = pixmap.scaled(
            120, 90,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.species_image.setPixmap(scaled)
        self.species_image.setVisible(True)

    def closeEvent(self, event):
        if AUDIO_OK:
            sd.stop()
        self.embeddings_2d = None
        self.labels = None
        self.metadata = None
        self._image_cache.clear()
        super().closeEvent(event)
