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
import os
import librosa
import soundfile as sf
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import cv2  # For contour operations

class ContourSelectWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.spectrogram_img = None
        self.points = []
        self.setMouseTracking(True)
    
    def load_spectrogram(self, S_db):
        """Convert spectrogram to QImage"""
        # Normalize to 0-255
        norm = ((S_db - S_db.min()) / (S_db.max() - S_db.min()) * 255).astype(np.uint8)
        # Apply colormap using OpenCV
        colored = cv2.applyColorMap(norm, cv2.COLORMAP_VIRIDIS)
        # Convert to QImage
        height, width, _ = colored.shape
        bytes_per_line = 3 * width
        qimage = QImage(colored.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        self.spectrogram_img = QPixmap.fromImage(qimage)
        self.update()
    
    def paintEvent(self, event):
        """Draw spectrogram and contour"""
        painter = QPainter(self)
        if self.spectrogram_img:
            # Draw spectrogram
            painter.drawPixmap(0, 0, self.spectrogram_img.scaled(self.size(), 
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        
        # Draw contour points
        if self.points:
            painter.setPen(QPen(QColor(255, 0, 0), 2))
            painter.setBrush(QBrush(QColor(255, 0, 0, 50)))
            
            # Draw lines between points
            for i in range(len(self.points)):
                painter.drawEllipse(self.points[i], 3, 3)
                if i > 0:
                    painter.drawLine(self.points[i-1], self.points[i])
            # Close polygon
            if len(self.points) > 1:
                painter.drawLine(self.points[-1], self.points[0])
    
    def mousePressEvent(self, event):
        """Add point on click"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.points.append(event.pos())
            self.update()
    
    def clear_contour(self):
        """Clear all points"""
        self.points.clear()
        self.update()
    
    def get_contour_mask(self, shape):
        """Create binary mask from contour"""
        if len(self.points) < 3:
            return None
        
        # Create mask image
        mask_img = QImage(shape[1], shape[0], QImage.Format.Format_ARGB32)
        mask_img.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(mask_img)
        painter.setPen(QPen(Qt.GlobalColor.white, 1))
        painter.setBrush(QBrush(Qt.GlobalColor.white))
        
        # Draw polygon
        polygon = QPolygon(self.points)
        painter.drawPolygon(polygon)
        painter.end()
        
        # Convert to numpy array
        mask_array = np.zeros((shape[0], shape[1]), dtype=np.uint8)
        for y in range(shape[0]):
            for x in range(shape[1]):
                if mask_img.pixelColor(x, y).alpha() > 0:
                    mask_array[y, x] = 1
        
        return mask_array

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spectrogram Pattern Selector")
        self.setGeometry(100, 100, 1000, 600)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # File input
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Audio File:"))
        self.file_input = QLineEdit("your_audio.wav")
        file_layout.addWidget(self.file_input)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)
        
        # Time range
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Time Range (s):"))
        self.start_input = QLineEdit("0")
        self.start_input.setFixedWidth(80)
        time_layout.addWidget(self.start_input)
        time_layout.addWidget(QLabel("to"))
        self.end_input = QLineEdit("60")
        self.end_input.setFixedWidth(80)
        time_layout.addWidget(self.end_input)
        load_btn = QPushButton("Load & Compute")
        load_btn.clicked.connect(self.load_and_compute)
        time_layout.addWidget(load_btn)
        time_layout.addStretch()
        layout.addLayout(time_layout)
        
        # Spectrogram display with contour selection
        self.contour_widget = ContourSelectWidget()
        layout.addWidget(self.contour_widget)
        
        # Controls
        control_layout = QHBoxLayout()
        clear_btn = QPushButton("Clear Contour")
        clear_btn.clicked.connect(self.clear_contour)
        control_layout.addWidget(clear_btn)
        
        save_btn = QPushButton("Save Pattern")
        save_btn.clicked.connect(self.save_pattern)
        control_layout.addWidget(save_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # Status
        self.status_label = QLabel("Load an audio file to start")
        layout.addWidget(self.status_label)
        
        # Data storage
        self.S_db = None
        self.times = None
        self.freqs = None
    
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Audio File", "", "Audio Files (*.wav *.flac *.mp3)"
        )
        if file_path:
            self.file_input.setText(file_path)
    
    def load_and_compute(self):
        """Load audio and compute spectrogram"""
        filename = self.file_input.text()
        start_time = float(self.start_input.text())
        end_time = float(self.end_input.text())
        
        try:
            self.status_label.setText("Loading audio...")
            QApplication.processEvents()
            
            # Load audio
            audio, sr = librosa.load(filename, sr=None, mono=True)
            
            # Extract time segment
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            audio_segment = audio[start_sample:end_sample]
            
            # Compute spectrogram
            self.status_label.setText("Computing spectrogram...")
            QApplication.processEvents()
            
            S = librosa.stft(audio_segment, n_fft=2048, hop_length=512)
            self.S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)
            self.times = librosa.frames_to_time(np.arange(self.S_db.shape[1]), 
                                               sr=sr, hop_length=512)
            self.freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
            
            # Display
            self.contour_widget.load_spectrogram(self.S_db)
            self.status_label.setText(f"Ready! Click to draw contour around pattern")
            
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
    
    def clear_contour(self):
        self.contour_widget.clear_contour()
    
    def save_pattern(self):
        """Save pattern as binary mask"""
        if self.S_db is None:
            self.status_label.setText("Please load audio first")
            return
        
        mask = self.contour_widget.get_contour_mask(self.S_db.shape)
        if mask is None:
            self.status_label.setText("Please draw a contour first (minimum 3 points)")
            return
        
        # Find bounding box of mask
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        if not np.any(rows) or not np.any(cols):
            self.status_label.setText("Invalid contour")
            return
        
        ymin, ymax = np.where(rows)[0][[0, -1]]
        xmin, xmax = np.where(cols)[0][[0, -1]]
        
        # Extract rectangle
        rect_spectrogram = self.S_db[ymin:ymax+1, xmin:xmax+1]
        rect_mask = mask[ymin:ymax+1, xmin:xmax+1]
        
        # Create binary image
        binary = np.zeros_like(rect_spectrogram)
        binary[rect_mask > 0] = 1
        
        # Save files
        base_name = os.path.splitext(os.path.basename(self.file_input.text()))[0]
        
        # Save binary mask
        np.save(f"{base_name}_pattern_binary.npy", binary)
        
        # Save visualization image
        import matplotlib.pyplot as plt
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        
        ax1.imshow(rect_spectrogram, aspect='auto', origin='lower', 
                   cmap='viridis', extent=[self.times[xmin], self.times[xmax], 
                                           self.freqs[ymin], self.freqs[ymax]])
        ax1.set_title('Extracted Region')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Frequency (Hz)')
        
        ax2.imshow(binary, aspect='auto', origin='lower', cmap='gray',
                   extent=[self.times[xmin], self.times[xmax], 
                           self.freqs[ymin], self.freqs[ymax]])
        ax2.set_title('Binary Pattern (1 inside contour)')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Frequency (Hz)')
        
        plt.tight_layout()
        plt.savefig(f"{base_name}_pattern.png", dpi=150)
        plt.close()
        
        self.status_label.setText(f"Pattern saved as {base_name}_pattern.npy and {base_name}_pattern.png")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())