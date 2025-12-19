import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QCursor, QFont
from PyQt6.QtCore import Qt, QRect


class SpectrogramWidget(QWidget):
    """Custom widget for displaying and interacting with spectrograms"""

    def __init__(self):
        super().__init__()
        self.spectrogram = None
        self.frequencies = None
        self.times = None
        self.time_offset = 0
        self.display_pixmap = None
        self.brush_size = 20
        self.drawing = False
        self.mask = None
        self.last_point = None
        self.brush_enabled = False

        self.viewport_duration = 60.0
        self.viewport_start = 0.0

        self.zoom_enabled = False
        self.zoom_start = None
        self.zoom_rect = None
        self.zoomed = False
        self.zoom_time_range = None
        self.zoom_freq_range = None

        self.playback_position = None
        
        # Margins for axes
        self.left_margin = 80
        self.bottom_margin = 50
        self.top_margin = 20

        self.setMinimumSize(800, 400)
        self.setMouseTracking(True)

    def set_spectrogram(self, spec_data, frequencies, times, time_offset=0):
        self.spectrogram = spec_data
        self.frequencies = frequencies
        self.times = times
        self.time_offset = time_offset

        self.viewport_start = 0.0
        self.zoomed = False
        self.zoom_time_range = None
        self.zoom_freq_range = None
        self.playback_position = None

        if spec_data is not None:
            height, width = spec_data.shape
            self.mask = np.zeros((height, width), dtype=np.uint8)

        self.update_display()

    def get_viewport_indices(self):
        if self.spectrogram is None or self.times is None:
            return None, None

        total_duration = self.times[-1]

        if self.zoomed and self.zoom_time_range:
            start_time = self.zoom_time_range[0]
            end_time = self.zoom_time_range[1]
        else:
            start_time = self.viewport_start
            end_time = min(self.viewport_start + self.viewport_duration, total_duration)

        start_idx = np.searchsorted(self.times, start_time)
        end_idx = np.searchsorted(self.times, end_time)

        return start_idx, end_idx

    def update_display(self):
        if self.spectrogram is None:
            return

        start_idx, end_idx = self.get_viewport_indices()
        if start_idx is None:
            return

        if self.zoomed and self.zoom_freq_range:
            freq_start, freq_end = self.zoom_freq_range
            viewport_spec = self.spectrogram[freq_start:freq_end, start_idx:end_idx]
        else:
            viewport_spec = self.spectrogram[:, start_idx:end_idx]

        viewport_spec = np.flipud(viewport_spec)
        height, width = viewport_spec.shape
        colored = self.apply_colormap(viewport_spec)

        image = QImage(colored.data, width, height, width * 3, QImage.Format.Format_RGB888)
        self.full_pixmap = QPixmap.fromImage(image)

        available_width = self.width() - self.left_margin - 10
        available_height = self.height() - self.top_margin - self.bottom_margin

        self.display_pixmap = self.full_pixmap.scaled(
            available_width, available_height,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.update()

    def apply_colormap(self, data):
        colored = np.zeros((*data.shape, 3), dtype=np.uint8)
        colored[:, :, 0] = (data * 255).astype(np.uint8)
        colored[:, :, 1] = (data * 200).astype(np.uint8)
        colored[:, :, 2] = (data * 100).astype(np.uint8)
        return colored

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 255, 255))

        if self.display_pixmap:
            painter.drawPixmap(self.left_margin, self.top_margin, self.display_pixmap)

            painter.setPen(QPen(QColor(0, 0, 0), 1))
            font = QFont("Arial", 9)
            painter.setFont(font)

            start_idx, end_idx = self.get_viewport_indices()
            if start_idx is not None:
                if self.zoomed and self.zoom_time_range:
                    time_start = self.zoom_time_range[0]
                    time_end = self.zoom_time_range[1]
                else:
                    time_start = self.viewport_start
                    time_end = min(self.viewport_start + self.viewport_duration, self.times[-1])

                num_time_ticks = 5
                for i in range(num_time_ticks + 1):
                    fraction = i / num_time_ticks
                    time_val = time_start + (time_end - time_start) * fraction
                    x_pos = self.left_margin + int(self.display_pixmap.width() * fraction)
                    painter.drawText(x_pos - 20, self.height() - 5, f"{time_val + self.time_offset:.1f}s")

                painter.drawText(self.width() // 2 - 20, self.height() - 25, "Time")

                if self.zoomed and self.zoom_freq_range:
                    freq_start = self.frequencies[self.zoom_freq_range[0]]
                    freq_end = self.frequencies[self.zoom_freq_range[1]]
                else:
                    freq_start = self.frequencies[0]
                    freq_end = self.frequencies[-1]

                num_freq_ticks = 6
                for i in range(num_freq_ticks + 1):
                    fraction = i / num_freq_ticks
                    freq_val = freq_start + (freq_end - freq_start) * (1 - fraction)
                    y_pos = self.top_margin + int(self.display_pixmap.height() * fraction)
                    painter.drawText(5, y_pos + 5, f"{freq_val:.0f}")

                painter.save()
                painter.translate(10, self.height() // 2)
                painter.rotate(-90)
                painter.drawText(-40, 0, "Frequency (Hz)")
                painter.restore()

            if self.playback_position is not None and not self.zoomed:
                if self.viewport_start <= self.playback_position <= self.viewport_start + self.viewport_duration:
                    relative_pos = (self.playback_position - self.viewport_start) / self.viewport_duration
                    x_pos = self.left_margin + int(relative_pos * self.display_pixmap.width())

                    painter.setPen(QPen(QColor(255, 0, 0), 2))
                    painter.drawLine(x_pos, self.top_margin, x_pos, self.top_margin + self.display_pixmap.height())

            if self.zoom_rect and self.zoom_enabled:
                painter.setPen(QPen(QColor(255, 255, 0), 2))
                painter.drawRect(self.zoom_rect)

            if self.mask is not None and np.any(self.mask):
                start_idx, end_idx = self.get_viewport_indices()
                if start_idx is not None:
                    if self.zoomed and self.zoom_freq_range:
                        freq_start, freq_end = self.zoom_freq_range
                        viewport_mask = self.mask[freq_start:freq_end, start_idx:end_idx]
                    else:
                        viewport_mask = self.mask[:, start_idx:end_idx]

                    viewport_mask = np.flipud(viewport_mask)

                    mask_colored = np.zeros((*viewport_mask.shape, 4), dtype=np.uint8)
                    mask_colored[viewport_mask > 0] = [255, 255, 0, 100]

                    mask_image = QImage(mask_colored.data, viewport_mask.shape[1], viewport_mask.shape[0],
                                    viewport_mask.shape[1] * 4, QImage.Format.Format_RGBA8888)
                    mask_pixmap = QPixmap.fromImage(mask_image).scaled(
                        self.display_pixmap.width(), self.display_pixmap.height(),
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    painter.drawPixmap(self.left_margin, self.top_margin, mask_pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.zoom_enabled:
                self.zoom_start = event.pos()
                self.zoom_rect = QRect(self.zoom_start, self.zoom_start)
            elif self.brush_enabled:
                self.drawing = True
                self.draw_at(event.pos())

    def mouseMoveEvent(self, event):
        if self.zoom_enabled and self.zoom_start:
            self.zoom_rect = QRect(self.zoom_start, event.pos()).normalized()
            self.update()
        elif self.brush_enabled and self.drawing:
            self.draw_at(event.pos())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.zoom_enabled and self.zoom_rect:
                self.apply_zoom()
                self.zoom_start = None
                self.zoom_rect = None
            elif self.brush_enabled:
                self.drawing = False
                self.last_point = None

    def apply_zoom(self):
        if not self.zoom_rect or self.display_pixmap is None:
            return

        start_idx, end_idx = self.get_viewport_indices()
        if start_idx is None:
            return

        display_height = self.display_pixmap.height()

        x_start_raw = self.zoom_rect.left() - self.left_margin
        x_end_raw = self.zoom_rect.right() - self.left_margin
        y_start_raw = self.zoom_rect.top() - self.top_margin
        y_end_raw = self.zoom_rect.bottom() - self.top_margin

        x_start = max(0, x_start_raw)
        x_end = min(self.display_pixmap.width(), x_end_raw)
        y_start = max(0, y_start_raw)
        y_end = min(self.display_pixmap.height(), y_end_raw)

        if (x_end - x_start) < 5 or (y_end - y_start) < 5:
            return

        if start_idx < len(self.times) and end_idx < len(self.times):
            current_time_span = self.times[end_idx] - self.times[start_idx]
            time_start = self.times[start_idx] + (x_start / self.display_pixmap.width()) * current_time_span
            time_end = self.times[start_idx] + (x_end / self.display_pixmap.width()) * current_time_span
        else:
            return

        if self.zoomed and self.zoom_freq_range:
            current_freq_start_idx = self.zoom_freq_range[0]
            current_freq_end_idx = self.zoom_freq_range[1]
        else:
            current_freq_start_idx = 0
            current_freq_end_idx = len(self.frequencies) - 1

        current_freq_span = current_freq_end_idx - current_freq_start_idx

        fraction_y_start = y_start / display_height
        fraction_y_end = y_end / display_height

        data_fraction_start = 1 - fraction_y_end
        data_fraction_end = 1 - fraction_y_start

        freq_start_idx = current_freq_start_idx + int(data_fraction_start * current_freq_span)
        freq_end_idx = current_freq_start_idx + int(data_fraction_end * current_freq_span)

        freq_start_idx = max(0, min(freq_start_idx, len(self.frequencies) - 1))
        freq_end_idx = max(freq_start_idx + 1, min(freq_end_idx, len(self.frequencies)))

        self.zoom_time_range = (time_start, time_end)
        self.zoom_freq_range = (freq_start_idx, freq_end_idx)
        self.zoomed = True

        self.update_display()

    def reset_zoom(self):
        self.zoomed = False
        self.zoom_time_range = None
        self.zoom_freq_range = None
        self.update_display()

    def draw_at(self, pos):
        if self.mask is None or self.display_pixmap is None:
            return

        adjusted_x = pos.x() - self.left_margin
        adjusted_y = pos.y() - self.top_margin

        if adjusted_x < 0 or adjusted_x >= self.display_pixmap.width():
            return
        if adjusted_y < 0 or adjusted_y >= self.display_pixmap.height():
            return

        start_idx, end_idx = self.get_viewport_indices()
        if start_idx is None:
            return

        spec_x = int((adjusted_x / self.display_pixmap.width()) * (end_idx - start_idx)) + start_idx

        if self.zoomed and self.zoom_freq_range:
            zoom_freq_start, zoom_freq_end = self.zoom_freq_range
            zoom_freq_height = zoom_freq_end - zoom_freq_start
            display_height = self.display_pixmap.height()
            data_fraction = 1 - (adjusted_y / display_height)
            spec_y = zoom_freq_start + int(data_fraction * zoom_freq_height)
        else:
            spec_y = int((1 - adjusted_y / self.display_pixmap.height()) * self.mask.shape[0])

        spec_x = max(0, min(spec_x, self.mask.shape[1] - 1))
        spec_y = max(0, min(spec_y, self.mask.shape[0] - 1))

        radius = self.brush_size // 2
        y_indices, x_indices = np.ogrid[-radius:radius+1, -radius:radius+1]
        circle = x_indices**2 + y_indices**2 <= radius**2

        y_start = max(0, spec_y - radius)
        y_end = min(self.mask.shape[0], spec_y + radius + 1)
        x_start = max(0, spec_x - radius)
        x_end = min(self.mask.shape[1], spec_x + radius + 1)

        circle_slice = circle[
            max(0, radius - spec_y):radius + min(self.mask.shape[0] - spec_y, radius + 1),
            max(0, radius - spec_x):radius + min(self.mask.shape[1] - spec_x, radius + 1)
        ]

        self.mask[y_start:y_end, x_start:x_end][circle_slice] = 255
        self.update()

    def clear_mask(self):
        if self.mask is not None:
            self.mask.fill(0)
            self.update()

    def get_selected_pattern(self):
        if self.mask is None or self.spectrogram is None:
            return None

        rows, cols = np.where(self.mask > 0)
        if len(rows) == 0:
            return None

        min_row, max_row = rows.min(), rows.max()
        min_col, max_col = cols.min(), cols.max()

        pattern = self.spectrogram[min_row:max_row+1, min_col:max_col+1]

        return pattern

    def scroll_viewport(self, value):
        if self.times is None:
            return

        total_duration = self.times[-1]
        max_start = max(0, total_duration - self.viewport_duration)

        self.viewport_start = (value / 100.0) * max_start
        self.update_display()

    def set_playback_position(self, position):
        self.playback_position = position
        self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_display()
