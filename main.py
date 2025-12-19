# #!/usr/bin/env python3
# """
# ecosurf - Entry Point (from your if __name__ == '__main__' section)
# """
# import sys
# from PyQt6.QtWidgets import QApplication
# from src.ui.main_window import MainWindow  # Your MainWindow class

# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = MainWindow()  # Your original MainWindow class
#     window.show()
#     sys.exit(app.exec())
import sys
import numpy as np
import librosa
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import os

class BrushWidget(QWidget):
    """Widget for brush painting selection"""
    def __init__(self):
        super().__init__()
        self.spectrogram_pixmap = None
        self.selection_pixmap = None
        self.drawing = False
        self.last_point = None
        self.brush_size = 20
        self.brush_color = QColor(255, 0, 0, 128)  # Semi-transparent red
        
        self.setMouseTracking(True)
    
    def load_spectrogram(self, S_db):
        """Load spectrogram and setup selection canvas"""
        # Convert to grayscale for display
        norm = ((S_db - S_db.min()) / (S_db.max() - S_db.min()) * 255).astype(np.uint8)
        
        # Create QImage from spectrogram
        height, width = norm.shape
        bytes_per_line = width
        
        # Convert to RGB for better visibility
        rgb_data = np.zeros((height, width, 3), dtype=np.uint8)
        rgb_data[:, :, 0] = norm  # Red channel
        rgb_data[:, :, 1] = norm  # Green channel
        rgb_data[:, :, 2] = norm  # Blue channel
        
        qimage = QImage(rgb_data.data, width, height, width * 3, QImage.Format.Format_RGB888)
        self.spectrogram_pixmap = QPixmap.fromImage(qimage)
        
        # Create transparent selection overlay
        self.selection_pixmap = QPixmap(width, height)
        self.selection_pixmap.fill(Qt.GlobalColor.transparent)
        
        self.update()
    
    def paintEvent(self, event):
        """Paint spectrogram and selection overlay"""
        painter = QPainter(self)
        
        # Draw spectrogram
        if self.spectrogram_pixmap:
            # Scale spectrogram to fit widget
            scaled_spec = self.spectrogram_pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled_spec)
        
        # Draw selection overlay
        if self.selection_pixmap:
            scaled_selection = self.selection_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled_selection)
        
        # Draw brush preview at cursor
        if self.underMouse() and not self.drawing:
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(self.mapFromGlobal(QCursor.pos()), 
                              self.brush_size // 2, self.brush_size // 2)
    
    def mousePressEvent(self, event):
        """Start painting"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.paint_at(event.pos())
    
    def mouseMoveEvent(self, event):
        """Paint while moving"""
        if self.drawing:
            self.paint_at(event.pos())
    
    def mouseReleaseEvent(self, event):
        """Stop painting"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = False
            self.last_point = None
    
    def paint_at(self, pos):
        """Paint at position"""
        if not self.selection_pixmap:
            return
        
        # Convert widget coordinates to pixmap coordinates
        scale_x = self.selection_pixmap.width() / self.width()
        scale_y = self.selection_pixmap.height() / self.height()
        
        x = int(pos.x() * scale_x)
        y = int(pos.y() * scale_y)
        
        # Create painter for selection overlay
        painter = QPainter(self.selection_pixmap)
        painter.setPen(QPen(self.brush_color, self.brush_size, 
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, 
                          Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Draw line from last point or single point
        if self.last_point:
            last_x = int(self.last_point.x() * scale_x)
            last_y = int(self.last_point.y() * scale_y)
            painter.drawLine(last_x, last_y, x, y)
        else:
            painter.drawPoint(x, y)
        
        painter.end()
        self.last_point = pos
        self.update()
    
    def clear_selection(self):
        """Clear painted selection"""
        if self.selection_pixmap:
            self.selection_pixmap.fill(Qt.GlobalColor.transparent)
        self.update()
    
    def get_selection_mask(self):
        """Convert painted selection to binary mask"""
        if not self.selection_pixmap:
            return None
        
        # Convert QPixmap to QImage
        image = self.selection_pixmap.toImage()
        width = image.width()
        height = image.height()
        
        # Create numpy array mask
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # Check each pixel for red color
        for y in range(height):
            for x in range(width):
                color = image.pixelColor(x, y)
                if color.red() > 100 and color.alpha() > 0:
                    mask[y, x] = 1
        
        return mask

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Brush Pattern Selector")
        self.setGeometry(100, 100, 900, 600)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Top controls
        top_layout = QHBoxLayout()
        
        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("File:"))
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Click Browse or drag audio file here")
        self.file_input.setMinimumWidth(200)
        
        # Enable drag and drop
        self.file_input.setAcceptDrops(True)
        self.file_input.dragEnterEvent = self.drag_enter_event
        self.file_input.dropEvent = self.drop_event
        
        file_layout.addWidget(self.file_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        
        top_layout.addLayout(file_layout)
        
        # Time range
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time:"))
        
        self.start_input = QSpinBox()
        self.start_input.setRange(0, 9999)
        self.start_input.setValue(0)
        self.start_input.setFixedWidth(60)
        time_layout.addWidget(self.start_input)
        
        time_layout.addWidget(QLabel("-"))
        
        self.end_input = QSpinBox()
        self.end_input.setRange(1, 9999)
        self.end_input.setValue(60)
        self.end_input.setFixedWidth(60)
        time_layout.addWidget(self.end_input)
        
        time_layout.addWidget(QLabel("sec"))
        
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.load_audio)
        time_layout.addWidget(load_btn)
        
        top_layout.addLayout(time_layout)
        layout.addLayout(top_layout)
        
        # Brush widget
        self.brush_widget = BrushWidget()
        layout.addWidget(self.brush_widget)
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        
        # Brush size
        bottom_layout.addWidget(QLabel("Brush:"))
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(5, 100)
        self.size_slider.setValue(20)
        self.size_slider.valueChanged.connect(self.update_brush_size)
        self.size_slider.setFixedWidth(100)
        bottom_layout.addWidget(self.size_slider)
        
        self.size_label = QLabel("20")
        self.size_label.setFixedWidth(30)
        bottom_layout.addWidget(self.size_label)
        
        # Action buttons
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_painting)
        bottom_layout.addWidget(clear_btn)
        
        self.save_btn = QPushButton("Save Pattern")
        self.save_btn.clicked.connect(self.save_pattern)
        self.save_btn.setEnabled(False)
        bottom_layout.addWidget(self.save_btn)
        
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Data
        self.spectrogram = None
        self.times = None
        self.freqs = None
    
    def drag_enter_event(self, event):
        """Handle drag enter"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def drop_event(self, event):
        """Handle file drop"""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.file_input.setText(files[0])
    
    def browse_file(self):
        """Browse for audio file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "", 
            "Audio Files (*.wav *.flac *.mp3 *.ogg);;All Files (*.*)"
        )
        if file_path:
            self.file_input.setText(file_path)
    
    def load_audio(self):
        """Load audio file"""
        filename = self.file_input.text().strip()
        if not filename:
            self.status_bar.showMessage("❌ Please select a file")
            return
        
        if not os.path.exists(filename):
            self.status_bar.showMessage(f"❌ File not found: {filename}")
            return
        
        try:
            self.status_bar.showMessage("⏳ Loading audio...")
            QApplication.processEvents()
            
            # Get time range
            start_time = self.start_input.value()
            end_time = self.end_input.value()
            
            if start_time >= end_time:
                self.status_bar.showMessage("❌ Invalid time range")
                return
            
            # Load audio
            audio, sr = librosa.load(filename, sr=None, mono=True)
            
            # Check time range
            audio_duration = len(audio) / sr
            if end_time > audio_duration:
                end_time = int(audio_duration)
                self.end_input.setValue(end_time)
            
            # Extract segment
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            audio_segment = audio[start_sample:end_sample]
            
            if len(audio_segment) == 0:
                self.status_bar.showMessage("❌ Empty audio segment")
                return
            
            # Compute spectrogram
            self.status_bar.showMessage("⏳ Computing spectrogram...")
            QApplication.processEvents()
            
            S = librosa.stft(audio_segment, n_fft=1024, hop_length=256)
            self.spectrogram = librosa.amplitude_to_db(np.abs(S), ref=np.max)
            self.times = librosa.frames_to_time(
                np.arange(self.spectrogram.shape[1]), 
                sr=sr, hop_length=256
            ) + start_time
            self.freqs = librosa.fft_frequencies(sr=sr, n_fft=1024)
            
            # Display
            self.brush_widget.load_spectrogram(self.spectrogram)
            self.save_btn.setEnabled(True)
            
            self.status_bar.showMessage(f"✅ Loaded. Duration: {audio_duration:.1f}s. Paint your pattern.")
            
        except Exception as e:
            self.status_bar.showMessage(f"❌ Error: {str(e)}")
    
    def update_brush_size(self, value):
        """Update brush size"""
        self.brush_widget.brush_size = value
        self.size_label.setText(str(value))
    
    def clear_painting(self):
        """Clear painted selection"""
        self.brush_widget.clear_selection()
        self.status_bar.showMessage("Cleared")
    
    def save_pattern(self):
        """Save painted pattern"""
        if self.spectrogram is None:
            self.status_bar.showMessage("❌ No spectrogram loaded")
            return
        
        mask = self.brush_widget.get_selection_mask()
        if mask is None or np.sum(mask) == 0:
            self.status_bar.showMessage("❌ Nothing painted")
            return
        
        # Find bounding box of painted area
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        
        if not np.any(rows) or not np.any(cols):
            self.status_bar.showMessage("❌ Empty selection")
            return
        
        ymin, ymax = np.where(rows)[0][[0, -1]]
        xmin, xmax = np.where(cols)[0][[0, -1]]
        
        # Extract region
        region = self.spectrogram[ymin:ymax+1, xmin:xmax+1]
        region_mask = mask[ymin:ymax+1, xmin:xmax+1]
        
        # Create binary pattern
        binary = np.zeros_like(region_mask, dtype=np.uint8)
        binary[region_mask > 0] = 1
        
        # Generate filename
        base = os.path.splitext(os.path.basename(self.file_input.text()))[0]
        filename = f"{base}_pattern.npy"
        
        # Save
        np.save(filename, binary)
        
        # Save visualization
        try:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.imshow(binary, aspect='auto', origin='lower', cmap='gray')
            ax.set_title(f"Pattern: {base}")
            ax.axis('off')
            plt.tight_layout()
            plt.savefig(f"{base}_pattern.png", dpi=150, bbox_inches='tight')
            plt.close()
        except:
            pass  # Skip if matplotlib not available
        
        self.status_bar.showMessage(f"✅ Saved: {filename}")
        print(f"Pattern saved as '{filename}'")
        print(f"Shape: {binary.shape}")
        print(f"Pattern pixels: {np.sum(binary)} / {binary.size}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Simple style
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())