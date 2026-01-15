import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QCursor, QFont
from PyQt6.QtCore import Qt, QRect, pyqtSignal


class SpectrogramWidget(QWidget):
    """Custom widget for displaying and interacting with spectrograms"""
    scrollableChanged = pyqtSignal(bool)
    selectionChanged = pyqtSignal()

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
        self.rect_selection_mode = False  # ADD THIS LINE

        # Rectangle selection for brush (right-button drag)
        self.rect_select_start = None
        self.rect_select_rect = None

        # Selection waveform display
        self.selection_waveform_pixmap = None
        self.selection_waveform_height = 80
        self.selection_duration = None
        self.selection_sr = None
        self.selection_playback_pos = None
        self.waveform_visible = False

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
        self._scrollable = False
        
        # Cache for colormap optimization
        self._cached_colormap = None
        self._cached_colormap_shape = None

    def set_spectrogram(self, spec_data, frequencies, times, time_offset=0):
        self.spectrogram = spec_data
        self.frequencies = frequencies
        self.times = times
        self.time_offset = time_offset

        # FIX FOR MULTI-FILE: Show only 60s even for long concatenated spectrograms
        if times is not None and len(times) > 1:
            total_dur = float(times[-1])
            # Always show max 60s viewport, but allow scrolling for longer files
            self.viewport_duration = min(60.0, total_dur)
            # Reset to start
            self.viewport_start = 0.0
        else:
            # For empty or single files, keep original logic
            self.viewport_duration = 60.0
            self.viewport_start = 0.0

        self.zoomed = False
        self.zoom_time_range = None
        self.zoom_freq_range = None
        self.playback_position = None

        if spec_data is not None and len(times) > 1:
            height, width = spec_data.shape
            self.mask = np.zeros((height, width), dtype=np.uint8)
        else:
            self.mask = None

        # cached pixmaps for performance
        self.display_pixmap = None
        self.mask_pixmap = None

        self.update_display()

    def get_viewport_indices(self):
        if self.spectrogram is None or self.times is None:
            return None, None
        total_duration = self.times[-1]

        # When zoomed we allow a viewport window inside the zoom range
        if self.zoomed and self.zoom_time_range:
            zoom_start, zoom_end = self.zoom_time_range
            zoom_span = max(0.0, zoom_end - zoom_start)

            if zoom_span <= self.viewport_duration:
                # show entire zoomed region
                start_time = zoom_start
                end_time = zoom_end
            else:
                # ensure viewport_start lies inside zoom range
                max_start = zoom_end - self.viewport_duration
                # clamp viewport_start between zoom_start and max_start
                vs = min(max(self.viewport_start, zoom_start), max_start)
                start_time = vs
                end_time = vs + self.viewport_duration
        else:
            start_time = self.viewport_start
            end_time = min(self.viewport_start + self.viewport_duration, total_duration)

        # clamp to available times
        start_time = max(self.times[0], start_time)
        end_time = min(self.times[-1], end_time)

        start_idx = np.searchsorted(self.times, start_time)
        end_idx = np.searchsorted(self.times, end_time)

        # ensure at least one frame
        if end_idx <= start_idx:
            end_idx = min(start_idx + 1, len(self.times))

        return start_idx, end_idx

    def update_display(self):
        if self.spectrogram is None or self.frequencies is None or self.times is None:
            return

        # ---- Get current viewport indices ----
        start_idx, end_idx = self.get_viewport_indices()
        if start_idx is None or end_idx is None:
            return

        # ---- Extract spectrogram slice for viewport ----
        if self.zoomed and self.zoom_freq_range:
            freq_start, freq_end = self.zoom_freq_range
            viewport_spec = self.spectrogram[freq_start:freq_end, start_idx:end_idx]
        else:
            viewport_spec = self.spectrogram[:, start_idx:end_idx]

        if viewport_spec.size == 0:
            return

        # Flip vertically for display (low freq at bottom)
        viewport_spec = np.flipud(viewport_spec)
        viewport_height, viewport_width = viewport_spec.shape

        # ---- Convert spectrogram to RGB image and cache it ----
        colored = self.apply_colormap(viewport_spec)
        colored = np.ascontiguousarray(colored)
        image = QImage(colored.data, viewport_width, viewport_height, viewport_width * 3, QImage.Format.Format_RGB888)
        full_pixmap = QPixmap.fromImage(image)

        # ---- Compute display size ----
        available_width = self.width() - self.left_margin - 10
        # Reserve room for optional selection waveform at the bottom
        waveform_h = self.selection_waveform_height if self.waveform_visible else 0
        available_height = self.height() - self.top_margin - self.bottom_margin - waveform_h

        # Always fill the available width with the current viewport image
        # (the image shows only the frames between start_idx and end_idx)
        scaled_width = max(1, int(available_width))
        self.display_pixmap = full_pixmap.scaled(
            scaled_width, available_height,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Store full_pixmap for mask overlay drawing
        self.full_pixmap = full_pixmap

        # Precompute mask pixmap for this viewport for faster paint
        if self.mask is not None and np.any(self.mask):
            if self.zoomed and self.zoom_freq_range:
                freq_start, freq_end = self.zoom_freq_range
                viewport_mask = self.mask[freq_start:freq_end, start_idx:end_idx]
            else:
                viewport_mask = self.mask[:, start_idx:end_idx]

            viewport_mask = np.flipud(viewport_mask)
            mask_colored = np.zeros((*viewport_mask.shape, 4), dtype=np.uint8)
            mask_colored[viewport_mask > 0] = [255, 255, 0, 120]
            mask_colored = np.ascontiguousarray(mask_colored)
            mask_image = QImage(mask_colored.data, viewport_mask.shape[1], viewport_mask.shape[0], viewport_mask.shape[1] * 4, QImage.Format.Format_RGBA8888)
            self.mask_pixmap = QPixmap.fromImage(mask_image).scaled(
                self.display_pixmap.width(), self.display_pixmap.height(),
                Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
        else:
            self.mask_pixmap = None

        # compute whether scrollbar should be enabled: only if total duration exceeds viewport
        total_duration = float(self.times[-1])
        zoom_span = 0.0
        if self.zoomed and self.zoom_time_range:
            zoom_span = float(self.zoom_time_range[1] - self.zoom_time_range[0])

        scrollable = False
        if total_duration > self.viewport_duration:
            # if zoomed and zoomed region is smaller or equal to viewport, no scrolling needed
            if self.zoomed and zoom_span <= self.viewport_duration:
                scrollable = False
            else:
                scrollable = True

        if scrollable != self._scrollable:
            self._scrollable = scrollable
            try:
                self.scrollableChanged.emit(scrollable)
            except Exception:
                pass

        self.update()

    def show_selection_audio(self, audio, sr):
        """Render a small waveform of the selection and show it below the spectrogram."""
        try:
            if audio is None or len(audio) == 0:
                self.selection_waveform_pixmap = None
                self.waveform_visible = False
                self.selection_duration = None
                self.update()
                return

            # compute envelope and downsample to display width
            env = np.abs(audio)
            # downsample envelope to widget width for fast rendering
            w = max(200, self.width() - self.left_margin - 10)
            factor = max(1, int(len(env) / w))
            env_ds = env.reshape(-1, factor).max(axis=1) if factor > 1 and len(env) >= factor else env

            # normalize to [0,1]
            env_ds = env_ds / (env_ds.max() + 1e-12)

            hw = int(w)
            hh = int(self.selection_waveform_height)

            img = np.zeros((hh, hw, 3), dtype=np.uint8) + 255
            center = hh // 2
            for x in range(min(hw, len(env_ds))):
                v = float(env_ds[x])
                h = int(v * (hh // 2 - 2))
                img[center - h:center + h, x, :] = 0

            from PyQt6.QtGui import QImage, QPixmap
            img = np.ascontiguousarray(img)
            qimg = QImage(img.data, hw, hh, hw * 3, QImage.Format.Format_RGB888)
            self.selection_waveform_pixmap = QPixmap.fromImage(qimg)
            self.selection_duration = float(len(audio) / float(sr))
            self.selection_sr = int(sr)
            self.selection_playback_pos = None
            self.waveform_visible = True
            self.update()
        except Exception:
            pass

    def set_selection_playback_pos(self, t):
        """Set playback position (seconds) for selection waveform."""
        self.selection_playback_pos = None if t is None else float(t)
        self.update()


    def apply_colormap(self, data):
        """Hot colormap (like MATLAB's hot) - good for spectrograms - WITH CACHE"""
        if data.size == 0:
            return np.zeros((*data.shape, 3), dtype=np.uint8)
        
        # Check cache - reuse if same shape (viewport scroll optimization)
        if (self._cached_colormap is not None and 
            self._cached_colormap_shape == data.shape and
            not self.zoomed):
            # For scroll, we can reuse parts of the colormap
            pass  # Will compute new one for now, but shape check helps
        
        # Normalize to 0-1
        dmin = np.min(data)
        dmax = np.max(data)
        if dmax - dmin > 1e-10:
            norm_data = (data - dmin) / (dmax - dmin)
        else:
            norm_data = data * 0
        
        # Hot colormap implementation - vectorized for speed
        colored = np.empty((*data.shape, 3), dtype=np.uint8)
        
        # Red: ramp up quickly
        np.clip(norm_data * 1.7 * 255, 0, 255, out=colored[:, :, 0].astype(np.float32)).astype(np.uint8, copy=False)
        colored[:, :, 0] = np.clip(norm_data * 1.7 * 255, 0, 255).astype(np.uint8)
        # Green: ramp up in middle
        colored[:, :, 1] = np.clip((norm_data * 1.5 - 0.3) * 255, 0, 255).astype(np.uint8)
        # Blue: only at high values
        colored[:, :, 2] = np.clip((norm_data * 3 - 2) * 255, 0, 255).astype(np.uint8)
        
        # Update cache
        self._cached_colormap = colored
        self._cached_colormap_shape = data.shape
        
        return colored

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 255, 255))

        if not self.display_pixmap:
            return

        # Draw the spectrogram image
        painter.drawPixmap(self.left_margin, self.top_margin, self.display_pixmap)

        # Prepare font
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        font = painter.font()
        if font.pointSize() <= 0:
            font.setPointSize(10)
        painter.setFont(font)

        # ---- Retrieve viewport indices ----
        start_idx, end_idx = self.get_viewport_indices()
        if start_idx is None:
            return

        # FIX 3: Recompute viewport_spec for frequency axis calculations
        if self.zoomed and self.zoom_freq_range:
            freq_start, freq_end = self.zoom_freq_range
            viewport_spec = self.spectrogram[freq_start:freq_end, start_idx:end_idx]
        else:
            viewport_spec = self.spectrogram[:, start_idx:end_idx]

        viewport_spec = np.flipud(viewport_spec)
        viewport_height, viewport_width = viewport_spec.shape

        # ---- TIME AXIS ----
        # FIX 4: Use zoom_time_range when zoomed
        if self.zoomed and self.zoom_time_range:
            time_start, time_end = self.zoom_time_range
        else:
            time_start = self.viewport_start
            total_duration = self.times[-1] if self.times is not None else 0
            time_end = min(self.viewport_start + self.viewport_duration, total_duration)

        num_time_ticks = 5
        for i in range(num_time_ticks + 1):
            fraction = i / num_time_ticks
            # Calculate time value within the current viewport
            time_val = time_start + fraction * (time_end - time_start)
            
            # FIX 2: Apply offset only when displaying text
            x_pos = self.left_margin + int(self.display_pixmap.width() * fraction)
            text = f"{time_val + self.time_offset:.1f}s"
            painter.drawText(x_pos - 20, self.height() - 5, text)

        painter.drawText(self.width() // 2 - 20, self.height() - 25, "Time")

        # ---- FREQUENCY AXIS ----
        # FIX 3: Correct frequency axis with proper mapping
        num_freq_ticks = 6
        for i in range(num_freq_ticks + 1):
            fraction = i / num_freq_ticks
            pixel_row = int(fraction * viewport_spec.shape[0])
            
            # Invert because flipped
            spec_index = viewport_spec.shape[0] - 1 - pixel_row
            
            # Map viewport pixel → frequency index
            if self.zoomed and self.zoom_freq_range:
                freq_index = self.zoom_freq_range[0] + spec_index
            else:
                freq_index = spec_index
            
            # Ensure index is within bounds
            freq_index = max(0, min(freq_index, len(self.frequencies) - 1))
            freq_val = self.frequencies[freq_index]
            
            y_pos = self.top_margin + pixel_row
            painter.drawText(5, y_pos + 5, f"{freq_val:.0f} Hz")

        # Label
        painter.save()
        painter.translate(20, self.height() // 2)
        painter.rotate(-90)
        painter.drawText(0, 0, "Frequency (Hz)")
        painter.restore()

        # ---- Playback cursor ----
        if self.playback_position is not None and not self.zoomed:
            if self.viewport_start <= self.playback_position <= self.viewport_start + self.viewport_duration:
                relative_pos = (self.playback_position - self.viewport_start) / self.viewport_duration
                x_pos = self.left_margin + int(relative_pos * self.display_pixmap.width())

                painter.setPen(QPen(QColor(255, 0, 0), 2))
                painter.drawLine(x_pos, self.top_margin, x_pos, self.top_margin + self.display_pixmap.height())
                # also draw marker on time axis
                painter.setPen(QPen(QColor(255, 0, 0), 1))
                painter.drawText(x_pos - 20, self.top_margin - 5, f"{self.playback_position:.2f}s")

        # ---- Zoom Rectangle ----
        if self.zoom_rect and self.zoom_enabled:
            painter.setPen(QPen(QColor(255, 255, 0), 2))
            painter.drawRect(self.zoom_rect)
        
        # ---- Rectangle selection mode (pattern selection) ----
        if self.zoom_rect and self.rect_selection_mode:
            painter.setPen(QPen(QColor(0, 150, 255), 2, Qt.PenStyle.DashLine))
            painter.setBrush(QColor(0, 150, 255, 40))
            painter.drawRect(self.zoom_rect)
            # Afficher dimensions
            if self.zoom_rect.width() > 30 and self.zoom_rect.height() > 20:
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(self.zoom_rect.center().x() - 30, self.zoom_rect.center().y(), 
                                f"{self.zoom_rect.width()}x{self.zoom_rect.height()}")

        # ---- Mask Overlay ----
        if self.mask_pixmap is not None:
            painter.drawPixmap(self.left_margin, self.top_margin, self.mask_pixmap)

        # ---- Rectangle selection (right-button) ----
        if self.rect_select_rect is not None and self.brush_enabled:
            painter.setPen(QPen(QColor(0, 200, 0), 2, Qt.PenStyle.DashLine))
            painter.drawRect(self.rect_select_rect)

        # ---- Selection waveform ----
        if self.waveform_visible and self.selection_waveform_pixmap is not None:
            wf_x = self.left_margin
            wf_y = self.top_margin + self.display_pixmap.height() + 4
            painter.drawPixmap(wf_x, wf_y, self.selection_waveform_pixmap)

            # draw time axis for waveform
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawText(wf_x, wf_y + self.selection_waveform_height + 12, "Selection waveform")

            # playback position on waveform
            if self.selection_playback_pos is not None and self.selection_duration and self.selection_duration > 0:
                frac = max(0.0, min(1.0, self.selection_playback_pos / self.selection_duration))
                x_pos = wf_x + int(frac * self.selection_waveform_pixmap.width())
                painter.setPen(QPen(QColor(255, 0, 0), 2))
                painter.drawLine(x_pos, wf_y, x_pos, wf_y + self.selection_waveform_height)


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.rect_selection_mode:
                # Rectangle selection mode - start rectangle
                self.zoom_start = event.pos()
                self.zoom_rect = QRect(self.zoom_start, self.zoom_start)
            elif self.zoom_enabled:
                # Zoom mode - start rectangle
                self.zoom_start = event.pos()
                self.zoom_rect = QRect(self.zoom_start, self.zoom_start)
            elif self.brush_enabled:
                # Brush mode - left-button draws with brush
                self.drawing = True
                self.last_point = event.pos()
                self.draw_at(event.pos())
        elif event.button() == Qt.MouseButton.RightButton and self.brush_enabled:
            # Right-button rectangle selection while brush enabled
            self.rect_select_start = event.pos()
            self.rect_select_rect = QRect(self.rect_select_start, self.rect_select_start)
            self.update()

    def mouseMoveEvent(self, event):
        if self.rect_selection_mode and self.zoom_start:
            # Rectangle selection mode - update rectangle avec limite de 5 secondes
            raw_rect = QRect(self.zoom_start, event.pos()).normalized()
            
            # Limiter à 5 secondes max
            if self.times is not None and self.display_pixmap is not None and len(self.times) > 1:
                # Calculer la durée totale affichée
                start_idx, end_idx = self.get_viewport_indices()
                if start_idx is not None and end_idx is not None:
                    displayed_duration = self.times[min(end_idx, len(self.times)-1)] - self.times[start_idx]
                    if displayed_duration > 0:
                        # Calculer la largeur max en pixels pour 5 secondes
                        max_duration = 5.0
                        pixels_per_second = self.display_pixmap.width() / displayed_duration
                        max_width_pixels = int(pixels_per_second * max_duration)
                        
                        # Limiter la largeur du rectangle
                        if raw_rect.width() > max_width_pixels:
                            if event.pos().x() > self.zoom_start.x():
                                # Sélection vers la droite
                                raw_rect.setRight(raw_rect.left() + max_width_pixels)
                            else:
                                # Sélection vers la gauche
                                raw_rect.setLeft(raw_rect.right() - max_width_pixels)
            
            self.zoom_rect = raw_rect
            self.update()
        elif self.zoom_enabled and self.zoom_start:
            # Zoom mode - update rectangle
            self.zoom_rect = QRect(self.zoom_start, event.pos()).normalized()
            self.update()
        elif self.brush_enabled and self.drawing:
            # Brush mode - draw while moving
            self.draw_at(event.pos())
            self.last_point = event.pos()
        elif self.rect_select_start is not None:
            # Right-button rectangle while brush enabled
            self.rect_select_rect = QRect(self.rect_select_start, event.pos()).normalized()
            self.update()

    # File: ui/components/spectrogram_widget.py
# Replace your mouseReleaseEvent method with this:

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Rectangle selection mode (left-click) - fill the selected area
            if self.rect_selection_mode and self.zoom_start and self.zoom_rect:
                try:
                    start_idx, end_idx = self.get_viewport_indices()
                    if start_idx is None:
                        self.zoom_start = None
                        self.zoom_rect = None
                        return
                    
                    display_h = self.display_pixmap.height()
                    x_start_raw = self.zoom_rect.left() - self.left_margin
                    x_end_raw = self.zoom_rect.right() - self.left_margin
                    y_start_raw = self.zoom_rect.top() - self.top_margin
                    y_end_raw = self.zoom_rect.bottom() - self.top_margin
                    
                    x_start = max(0, min(self.display_pixmap.width(), x_start_raw))
                    x_end = max(0, min(self.display_pixmap.width(), x_end_raw))
                    y_start = max(0, min(display_h, y_start_raw))
                    y_end = max(0, min(display_h, y_end_raw))
                    
                    if (x_end - x_start) >= 2 and (y_end - y_start) >= 2:
                        displayed_time_bins = max(1, end_idx - start_idx)
                        sel_bin_start = int((x_start / float(self.display_pixmap.width())) * displayed_time_bins)
                        sel_bin_end = int((x_end / float(self.display_pixmap.width())) * displayed_time_bins)
                        sel_bin_start = max(0, min(displayed_time_bins - 1, sel_bin_start))
                        sel_bin_end = max(sel_bin_start + 1, min(displayed_time_bins, sel_bin_end))
                        
                        time_start_idx = start_idx + sel_bin_start
                        time_end_idx = start_idx + sel_bin_end
                        
                        # Freq mapping
                        if self.zoomed and self.zoom_freq_range:
                            freq_start_idx = self.zoom_freq_range[0]
                            freq_end_idx = self.zoom_freq_range[1]
                        else:
                            freq_start_idx = 0
                            freq_end_idx = self.mask.shape[0]
                        
                        displayed_freq_bins = max(1, freq_end_idx - freq_start_idx)
                        frac_top = float(y_start) / float(display_h)
                        frac_bottom = float(y_end) / float(display_h)
                        data_frac_start = 1.0 - frac_bottom
                        data_frac_end = 1.0 - frac_top
                        
                        sel_freq_start = int(freq_start_idx + data_frac_start * displayed_freq_bins)
                        sel_freq_end = int(freq_start_idx + data_frac_end * displayed_freq_bins)
                        sel_freq_start = max(0, min(self.mask.shape[0] - 1, sel_freq_start))
                        sel_freq_end = max(sel_freq_start + 1, min(self.mask.shape[0], sel_freq_end))
                        
                        # Fill mask region
                        self.mask[sel_freq_start:sel_freq_end, time_start_idx:time_end_idx] = 255
                        self.update_display()
                        
                        try:
                            self.selectionChanged.emit()
                        except Exception:
                            pass
                finally:
                    self.zoom_start = None
                    self.zoom_rect = None
                    self.update()
                    
            # Zoom mode - apply zoom
            elif self.zoom_enabled and self.zoom_rect:
                self.apply_zoom()
                self.zoom_start = None
                self.zoom_rect = None
                
            # Brush mode - stop drawing
            elif self.brush_enabled:
                self.drawing = False
                self.last_point = None
                
        elif event.button() == Qt.MouseButton.RightButton and self.rect_select_rect is not None:
            # Right-button rectangle selection (when brush enabled) - fill the selected area
            try:
                start_idx, end_idx = self.get_viewport_indices()
                if start_idx is None:
                    self.rect_select_start = None
                    self.rect_select_rect = None
                    return
                    
                display_h = self.display_pixmap.height()
                x_start_raw = self.rect_select_rect.left() - self.left_margin
                x_end_raw = self.rect_select_rect.right() - self.left_margin
                y_start_raw = self.rect_select_rect.top() - self.top_margin
                y_end_raw = self.rect_select_rect.bottom() - self.top_margin
                
                x_start = max(0, min(self.display_pixmap.width(), x_start_raw))
                x_end = max(0, min(self.display_pixmap.width(), x_end_raw))
                y_start = max(0, min(display_h, y_start_raw))
                y_end = max(0, min(display_h, y_end_raw))
                
                if (x_end - x_start) >= 2 and (y_end - y_start) >= 2:
                    displayed_time_bins = max(1, end_idx - start_idx)
                    sel_bin_start = int((x_start / float(self.display_pixmap.width())) * displayed_time_bins)
                    sel_bin_end = int((x_end / float(self.display_pixmap.width())) * displayed_time_bins)
                    sel_bin_start = max(0, min(displayed_time_bins - 1, sel_bin_start))
                    sel_bin_end = max(sel_bin_start + 1, min(displayed_time_bins, sel_bin_end))
                    
                    time_start_idx = start_idx + sel_bin_start
                    time_end_idx = start_idx + sel_bin_end
                    
                    # Freq mapping
                    if self.zoomed and self.zoom_freq_range:
                        freq_start_idx = self.zoom_freq_range[0]
                        freq_end_idx = self.zoom_freq_range[1]
                    else:
                        freq_start_idx = 0
                        freq_end_idx = self.mask.shape[0]
                    
                    displayed_freq_bins = max(1, freq_end_idx - freq_start_idx)
                    frac_top = float(y_start) / float(display_h)
                    frac_bottom = float(y_end) / float(display_h)
                    data_frac_start = 1.0 - frac_bottom
                    data_frac_end = 1.0 - frac_top
                    
                    sel_freq_start = int(freq_start_idx + data_frac_start * displayed_freq_bins)
                    sel_freq_end = int(freq_start_idx + data_frac_end * displayed_freq_bins)
                    sel_freq_start = max(0, min(self.mask.shape[0] - 1, sel_freq_start))
                    sel_freq_end = max(sel_freq_start + 1, min(self.mask.shape[0], sel_freq_end))
                    
                    # Fill mask region
                    self.mask[sel_freq_start:sel_freq_end, time_start_idx:time_end_idx] = 255
                    self.update_display()
                    
                    try:
                        self.selectionChanged.emit()
                    except Exception:
                        pass
            finally:
                self.rect_select_start = None
                self.rect_select_rect = None
                self.update()

    def apply_zoom(self):
        if not self.zoom_rect or self.display_pixmap is None:
            return

        start_idx, end_idx = self.get_viewport_indices()
        if start_idx is None:
            return
        # Map zoom rectangle to spectrogram data bins instead of relying on pixel ratios
        display_height = self.display_pixmap.height()

        # rectangle coordinates relative to spectrogram image
        x_start_raw = self.zoom_rect.left() - self.left_margin
        x_end_raw = self.zoom_rect.right() - self.left_margin
        y_start_raw = self.zoom_rect.top() - self.top_margin
        y_end_raw = self.zoom_rect.bottom() - self.top_margin

        x_start = max(0, min(self.display_pixmap.width(), x_start_raw))
        x_end = max(0, min(self.display_pixmap.width(), x_end_raw))
        y_start = max(0, min(display_height, y_start_raw))
        y_end = max(0, min(display_height, y_end_raw))

        if (x_end - x_start) < 4 or (y_end - y_start) < 4:
            return

        # number of time bins displayed
        displayed_time_bins = end_idx - start_idx
        if displayed_time_bins <= 0:
            return

        # compute selected time bins within displayed region
        sel_bin_start = int((x_start / float(self.display_pixmap.width())) * displayed_time_bins)
        sel_bin_end = int((x_end / float(self.display_pixmap.width())) * displayed_time_bins)
        sel_bin_start = max(0, min(displayed_time_bins - 1, sel_bin_start))
        sel_bin_end = max(sel_bin_start + 1, min(displayed_time_bins, sel_bin_end))

        time_start_idx = start_idx + sel_bin_start
        time_end_idx = start_idx + sel_bin_end

        # Frequency mapping: determine currently visible freq index range
        if self.zoomed and self.zoom_freq_range:
            freq_start_idx = self.zoom_freq_range[0]
            freq_end_idx = self.zoom_freq_range[1]
        else:
            freq_start_idx = 0
            freq_end_idx = self.mask.shape[0]

        displayed_freq_bins = max(1, freq_end_idx - freq_start_idx)

        # convert y (pixels) -> fraction and then to data bins (note the vertical flip)
        frac_top = float(y_start) / float(display_height)
        frac_bottom = float(y_end) / float(display_height)

        data_frac_start = 1.0 - frac_bottom
        data_frac_end = 1.0 - frac_top

        sel_freq_start = int(freq_start_idx + data_frac_start * displayed_freq_bins)
        sel_freq_end = int(freq_start_idx + data_frac_end * displayed_freq_bins)

        sel_freq_start = max(0, min(self.mask.shape[0] - 1, sel_freq_start))
        sel_freq_end = max(sel_freq_start + 1, min(self.mask.shape[0], sel_freq_end))

        # set zoom ranges and make viewport match the yellow-rectangle time span
        # convert frame indices to times for zoom_time_range
        time_start = self.times[time_start_idx] if time_start_idx < len(self.times) else self.times[0]
        time_end = self.times[time_end_idx - 1] if (time_end_idx - 1) < len(self.times) else self.times[-1]

        # ensure a minimal duration
        sel_duration = max(0.05, float(time_end - time_start))

        # set viewport to exactly the selection span so the zoom scale follows the rectangle
        self.viewport_duration = sel_duration
        self.viewport_start = float(time_start)

        self.zoom_time_range = (time_start, time_end)
        self.zoom_freq_range = (sel_freq_start, sel_freq_end)
        self.zoomed = True

        self.update_display()

    def reset_zoom(self):
        # Clear zoom ranges and restore a sensible default viewport
        self.zoomed = False
        self.zoom_time_range = None
        self.zoom_freq_range = None

        # Restore default viewport duration to up to 60s (or the clip length)
        try:
            if self.times is not None and len(self.times) > 1:
                total_dur = float(self.times[-1])
                self.viewport_duration = min(60.0, total_dur)
            else:
                self.viewport_duration = 60.0
        except Exception:
            self.viewport_duration = 60.0

        # Reset viewport start to the beginning
        self.viewport_start = 0.0

        self.update_display()

    def scroll_viewport(self, value):
        """Scroll viewport using a 0-100 slider value."""
        if self.times is None or len(self.times) == 0:
            return
        total_duration = float(self.times[-1])
        frac = max(0.0, min(1.0, value / 100.0))

        # If zoomed, scroll inside zoomed time range
        if self.zoomed and self.zoom_time_range:
            zoom_start, zoom_end = self.zoom_time_range
            zoom_span = max(0.0, zoom_end - zoom_start)
            if zoom_span <= self.viewport_duration:
                self.viewport_start = float(zoom_start)
            else:
                max_start = float(zoom_end - self.viewport_duration)
                self.viewport_start = float(zoom_start + frac * (max_start - zoom_start))
        else:
            max_start = max(0.0, total_duration - self.viewport_duration)
            self.viewport_start = frac * max_start
        self.update_display()

    def set_playback_position(self, t):
        """Set playback position in seconds (absolute time)."""
        self.playback_position = t
        self.update()

    def get_mask(self):
        return None if self.mask is None else self.mask.copy()

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

        # FIX 5: Correct brush drawing mapping
        display_h = self.display_pixmap.height()
        data_fraction = 1 - (adjusted_y / display_h)
        
        if self.zoomed and self.zoom_freq_range:
            start_f, end_f = self.zoom_freq_range
            spec_y = start_f + int(data_fraction * (end_f - start_f))
        else:
            spec_y = int(data_fraction * self.mask.shape[0])

        spec_x = max(0, min(spec_x, self.mask.shape[1] - 1))
        spec_y = max(0, min(spec_y, self.mask.shape[0] - 1))

        # Soft circular brush with linear falloff for smoother, round strokes
        radius = max(1, int(self.brush_size // 2))

        y_start = max(0, spec_y - radius)
        y_end = min(self.mask.shape[0], spec_y + radius + 1)
        x_start = max(0, spec_x - radius)
        x_end = min(self.mask.shape[1], spec_x + radius + 1)

        h = y_end - y_start
        w = x_end - x_start
        if h <= 0 or w <= 0:
            return

        # If we have a last_point, interpolate between points to avoid gaps
        points = [pos]
        if self.last_point is not None and self.last_point != pos:
            lp = self.last_point
            dx = pos.x() - lp.x()
            dy = pos.y() - lp.y()
            dist = max(1.0, (dx*dx + dy*dy) ** 0.5)
            steps = int(max(1, dist / max(1.0, radius * 0.5)))
            for i in range(1, steps + 1):
                t = i / float(steps + 1)
                ix = int(lp.x() + dx * t)
                iy = int(lp.y() + dy * t)
                points.append(type(pos)(ix, iy))

        for p in points:
            # recalc mapping for each interpolated point
            adjusted_x = p.x() - self.left_margin
            adjusted_y = p.y() - self.top_margin
            if adjusted_x < 0 or adjusted_x >= self.display_pixmap.width():
                continue
            if adjusted_y < 0 or adjusted_y >= self.display_pixmap.height():
                continue

            # map to spectrogram indices
            start_idx, end_idx = self.get_viewport_indices()
            if start_idx is None:
                continue

            spec_x = int((adjusted_x / self.display_pixmap.width()) * (end_idx - start_idx)) + start_idx
            display_h = self.display_pixmap.height()
            data_fraction = 1 - (adjusted_y / display_h)
            if self.zoomed and self.zoom_freq_range:
                start_f, end_f = self.zoom_freq_range
                spec_y = start_f + int(data_fraction * (end_f - start_f))
            else:
                spec_y = int(data_fraction * self.mask.shape[0])

            spec_x = max(0, min(spec_x, self.mask.shape[1] - 1))
            spec_y = max(0, min(spec_y, self.mask.shape[0] - 1))

            y0 = max(0, spec_y - radius)
            y1 = min(self.mask.shape[0], spec_y + radius + 1)
            x0 = max(0, spec_x - radius)
            x1 = min(self.mask.shape[1], spec_x + radius + 1)

            yy = np.arange(y0, y1) - spec_y
            xx = np.arange(x0, x1) - spec_x
            dy = yy[:, None]
            dx = xx[None, :]
            dist = np.sqrt(dx*dx + dy*dy)

            kernel = np.clip(1.0 - (dist / float(radius)), 0.0, 1.0)
            region = self.mask[y0:y1, x0:x1].astype(np.float32)
            new_vals = (kernel * 255.0).astype(np.float32)
            combined = np.maximum(region, new_vals)
            self.mask[y0:y1, x0:x1] = combined.astype(self.mask.dtype)

        # update cached mask pixmap for current viewport for immediate visual response
        self.update_display()

    def clear_mask(self):
        if self.mask is not None:
            self.mask.fill(0)
            self.update_display()

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_display()






















# """
# def mouseMoveEvent(self, event):
#     # Update mouse coordinates for tooltip display
#     if self.spectrogram is not None and self.display_pixmap is not None:
#         x = event.x() - self.left_margin
#         y = event.y() - self.top_margin

#         if 0 <= x < self.display_pixmap.width() and 0 <= y < self.display_pixmap.height():
#             start_idx, end_idx = self.get_viewport_indices()
#             if start_idx is not None:
#                 # Map x -> time
#                 fraction_x = x / self.display_pixmap.width()
#                 if self.zoomed and self.zoom_time_range:
#                     time_start, time_end = self.zoom_time_range
#                 else:
#                     time_start = self.viewport_start
#                     time_end = min(self.viewport_start + self.viewport_duration, self.times[-1])
#                 time_val = time_start + fraction_x * (time_end - time_start)
#                 self.mouse_time = time_val + self.time_offset

#                 # Map y -> frequency
#                 fraction_y = 1 - (y / self.display_pixmap.height())
#                 if self.zoomed and self.zoom_freq_range:
#                     freq_start, freq_end = self.zoom_freq_range
#                     freq_index = freq_start + int(fraction_y * (freq_end - freq_start))
#                 else:
#                     freq_index = int(fraction_y * self.mask.shape[0])
#                 freq_index = max(0, min(freq_index, len(self.frequencies)-1))
#                 self.mouse_freq = self.frequencies[freq_index]
#         else:
#             self.mouse_time = None
#             self.mouse_freq = None

#     self.update()  # trigger paintEvent

    



# # updat pain event 

# # ---- Mouse coordinates display ----
# if self.mouse_time is not None and self.mouse_freq is not None:
#     painter.setPen(QPen(QColor(0, 0, 255), 1))
#     font = painter.font()
#     font.setBold(True)
#     painter.setFont(font)
#     text = f"Time: {self.mouse_time:.3f}s, Freq: {self.mouse_freq:.1f} Hz"
#     painter.drawText(self.left_margin, self.height() - 25, text)

    
# # add to __init__
#         self.mouse_time = None
#         self.mouse_freq = None




# """

# import numpy as np
# from PyQt6.QtWidgets import QWidget
# from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QCursor, QFont
# from PyQt6.QtCore import Qt, QRect, pyqtSignal


# class SpectrogramWidget(QWidget):
#     """Custom widget for displaying and interacting with spectrograms"""
#     scrollableChanged = pyqtSignal(bool)
#     selectionChanged = pyqtSignal()

#     def __init__(self):
#         super().__init__()
#         self.spectrogram = None
#         self.frequencies = None
#         self.times = None
#         self.time_offset = 0
#         self.display_pixmap = None
#         self.brush_size = 20
#         self.drawing = False
#         self.mask = None
#         self.last_point = None
#         self.brush_enabled = False
#         self.rect_selection_mode = False

#         # Rectangle selection for brush (right-button drag)
#         self.rect_select_start = None
#         self.rect_select_rect = None

#         # Selection waveform display
#         self.selection_waveform_pixmap = None
#         self.selection_waveform_height = 80
#         self.selection_duration = None
#         self.selection_sr = None
#         self.selection_playback_pos = None
#         self.waveform_visible = False

#         self.viewport_duration = 60.0
#         self.viewport_start = 0.0

#         self.zoom_enabled = False
#         self.zoom_start = None
#         self.zoom_rect = None
#         self.zoomed = False
#         self.zoom_time_range = None
#         self.zoom_freq_range = None

#         self.playback_position = None
        
#         # Margins for axes
#         self.left_margin = 80
#         self.bottom_margin = 50
#         self.top_margin = 20

#         self.setMinimumSize(800, 400)
#         self.setMouseTracking(True)
#         self._scrollable = False

#     def set_spectrogram(self, spec_data, frequencies, times, time_offset=0):
#         self.spectrogram = spec_data
#         self.frequencies = frequencies
#         self.times = times
#         self.time_offset = time_offset

#         # For multi-file: Show only 60s initially even for long concatenated spectrograms
#         if times is not None and len(times) > 1:
#             total_dur = float(times[-1])
#             # Always show max 60s viewport, but allow scrolling for longer files
#             self.viewport_duration = min(60.0, total_dur)
#             # Reset to start
#             self.viewport_start = 0.0
#         else:
#             self.viewport_duration = 60.0
#             self.viewport_start = 0.0

#         self.zoomed = False
#         self.zoom_time_range = None
#         self.zoom_freq_range = None
#         self.playback_position = None

#         if spec_data is not None and len(times) > 1:
#             height, width = spec_data.shape
#             self.mask = np.zeros((height, width), dtype=np.uint8)
#         else:
#             self.mask = None

#         # cached pixmaps for performance
#         self.display_pixmap = None
#         self.mask_pixmap = None

#         self.update_display()

#     def get_viewport_indices(self):
#         if self.spectrogram is None or self.times is None:
#             return None, None
#         total_duration = self.times[-1]

#         # When zoomed we allow a viewport window inside the zoom range
#         if self.zoomed and self.zoom_time_range:
#             zoom_start, zoom_end = self.zoom_time_range
#             zoom_span = max(0.0, zoom_end - zoom_start)

#             if zoom_span <= self.viewport_duration:
#                 # show entire zoomed region
#                 start_time = zoom_start
#                 end_time = zoom_end
#             else:
#                 # ensure viewport_start lies inside zoom range
#                 max_start = zoom_end - self.viewport_duration
#                 # clamp viewport_start between zoom_start and max_start
#                 vs = min(max(self.viewport_start, zoom_start), max_start)
#                 start_time = vs
#                 end_time = vs + self.viewport_duration
#         else:
#             start_time = self.viewport_start
#             end_time = min(self.viewport_start + self.viewport_duration, total_duration)

#         # clamp to available times
#         start_time = max(self.times[0], start_time)
#         end_time = min(self.times[-1], end_time)

#         start_idx = np.searchsorted(self.times, start_time)
#         end_idx = np.searchsorted(self.times, end_time)

#         # ensure at least one frame
#         if end_idx <= start_idx:
#             end_idx = min(start_idx + 1, len(self.times))

#         return start_idx, end_idx

#     def _get_current_time_range(self):
#         """Get current visible time range"""
#         if self.zoomed and self.zoom_time_range:
#             return self.zoom_time_range
#         else:
#             if self.times is not None and len(self.times) > 0:
#                 total_duration = float(self.times[-1])
#                 time_end = min(self.viewport_start + self.viewport_duration, total_duration)
#                 return (self.viewport_start, time_end)
#             return (0.0, 60.0)

#     def _get_current_freq_range(self):
#         """Get current visible frequency range"""
#         if self.zoomed and self.zoom_freq_range:
#             if self.frequencies is not None and len(self.frequencies) > 0:
#                 freq_start, freq_end = self.zoom_freq_range
#                 return (self.frequencies[freq_start], self.frequencies[freq_end-1])
        
#         # Default: show all frequencies
#         if self.frequencies is not None and len(self.frequencies) > 0:
#             return (self.frequencies[0], self.frequencies[-1])
#         return (0.0, 11025.0)  # Default max for 22050Hz SR

#     def update_display(self):
#         if self.spectrogram is None or self.frequencies is None or self.times is None:
#             return

#         # ---- Get current viewport indices ----
#         start_idx, end_idx = self.get_viewport_indices()
#         if start_idx is None or end_idx is None:
#             return

#         # ---- Extract spectrogram slice for viewport ----
#         if self.zoomed and self.zoom_freq_range:
#             freq_start, freq_end = self.zoom_freq_range
#             viewport_spec = self.spectrogram[freq_start:freq_end, start_idx:end_idx]
#         else:
#             viewport_spec = self.spectrogram[:, start_idx:end_idx]

#         if viewport_spec.size == 0:
#             return

#         # Flip vertically for display (low freq at bottom)
#         viewport_spec = np.flipud(viewport_spec)
#         viewport_height, viewport_width = viewport_spec.shape

#         # ---- Convert spectrogram to RGB image and cache it ----
#         colored = self.apply_colormap(viewport_spec)
#         colored = np.ascontiguousarray(colored)
#         image = QImage(colored.data, viewport_width, viewport_height, viewport_width * 3, QImage.Format.Format_RGB888)
#         full_pixmap = QPixmap.fromImage(image)

#         # ---- Compute display size with PROPER ASPECT RATIO ----
#         available_width = self.width() - self.left_margin - 10
#         # Reserve room for optional selection waveform at the bottom
#         waveform_h = self.selection_waveform_height if self.waveform_visible else 0
#         available_height = self.height() - self.top_margin - self.bottom_margin - waveform_h
        
#         # Calculate optimal dimensions to maintain aspect ratio
#         # Don't stretch too much in either direction
#         spec_aspect = viewport_width / max(1, viewport_height)
#         display_aspect = available_width / max(1, available_height)
        
#         if spec_aspect > display_aspect:
#             # Spectrogram is wider than display area - use full width
#             scaled_width = max(1, int(available_width))
#             scaled_height = max(1, int(available_width / spec_aspect))
#         else:
#             # Spectrogram is taller than display area - use full height
#             scaled_height = max(1, int(available_height))
#             scaled_width = max(1, int(available_height * spec_aspect))
        
#         # Ensure we don't exceed available space
#         scaled_width = min(scaled_width, available_width)
#         scaled_height = min(scaled_height, available_height)
        
#         self.display_pixmap = full_pixmap.scaled(
#             scaled_width, scaled_height,
#             Qt.AspectRatioMode.IgnoreAspectRatio,
#             Qt.TransformationMode.SmoothTransformation
#         )

#         # Store full_pixmap for mask overlay drawing
#         self.full_pixmap = full_pixmap

#         # Precompute mask pixmap for this viewport for faster paint
#         if self.mask is not None and np.any(self.mask):
#             if self.zoomed and self.zoom_freq_range:
#                 freq_start, freq_end = self.zoom_freq_range
#                 viewport_mask = self.mask[freq_start:freq_end, start_idx:end_idx]
#             else:
#                 viewport_mask = self.mask[:, start_idx:end_idx]

#             viewport_mask = np.flipud(viewport_mask)
#             mask_colored = np.zeros((*viewport_mask.shape, 4), dtype=np.uint8)
#             mask_colored[viewport_mask > 0] = [255, 255, 0, 120]
#             mask_colored = np.ascontiguousarray(mask_colored)
#             mask_image = QImage(mask_colored.data, viewport_mask.shape[1], viewport_mask.shape[0], 
#                                viewport_mask.shape[1] * 4, QImage.Format.Format_RGBA8888)
#             self.mask_pixmap = QPixmap.fromImage(mask_image).scaled(
#                 self.display_pixmap.width(), self.display_pixmap.height(),
#                 Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation
#             )
#         else:
#             self.mask_pixmap = None

#         # compute whether scrollbar should be enabled: only if total duration exceeds viewport
#         total_duration = float(self.times[-1])
#         zoom_span = 0.0
#         if self.zoomed and self.zoom_time_range:
#             zoom_span = float(self.zoom_time_range[1] - self.zoom_time_range[0])

#         scrollable = False
#         if total_duration > self.viewport_duration:
#             # if zoomed and zoomed region is smaller or equal to viewport, no scrolling needed
#             if self.zoomed and zoom_span <= self.viewport_duration:
#                 scrollable = False
#             else:
#                 scrollable = True

#         if scrollable != self._scrollable:
#             self._scrollable = scrollable
#             try:
#                 self.scrollableChanged.emit(scrollable)
#             except Exception:
#                 pass

#         self.update()

#     def show_selection_audio(self, audio, sr):
#         """Render a small waveform of the selection and show it below the spectrogram."""
#         try:
#             if audio is None or len(audio) == 0:
#                 self.selection_waveform_pixmap = None
#                 self.waveform_visible = False
#                 self.selection_duration = None
#                 self.update()
#                 return

#             # compute envelope and downsample to display width
#             env = np.abs(audio)
#             # downsample envelope to widget width for fast rendering
#             w = max(200, self.width() - self.left_margin - 10)
#             factor = max(1, int(len(env) / w))
#             env_ds = env.reshape(-1, factor).max(axis=1) if factor > 1 and len(env) >= factor else env

#             # normalize to [0,1]
#             env_ds = env_ds / (env_ds.max() + 1e-12)

#             hw = int(w)
#             hh = int(self.selection_waveform_height)

#             img = np.zeros((hh, hw, 3), dtype=np.uint8) + 255
#             center = hh // 2
#             for x in range(min(hw, len(env_ds))):
#                 v = float(env_ds[x])
#                 h = int(v * (hh // 2 - 2))
#                 img[center - h:center + h, x, :] = 0

#             from PyQt6.QtGui import QImage, QPixmap
#             img = np.ascontiguousarray(img)
#             qimg = QImage(img.data, hw, hh, hw * 3, QImage.Format.Format_RGB888)
#             self.selection_waveform_pixmap = QPixmap.fromImage(qimg)
#             self.selection_duration = float(len(audio) / float(sr))
#             self.selection_sr = int(sr)
#             self.selection_playback_pos = None
#             self.waveform_visible = True
#             self.update()
#         except Exception:
#             pass

#     def set_selection_playback_pos(self, t):
#         """Set playback position (seconds) for selection waveform."""
#         self.selection_playback_pos = None if t is None else float(t)
#         self.update()

#     def apply_colormap(self, data):
#         """Hot colormap (like MATLAB's hot) - good for spectrograms"""
#         if data.size == 0:
#             return np.zeros((*data.shape, 3), dtype=np.uint8)
        
#         # Normalize to 0-1
#         dmin = np.min(data)
#         dmax = np.max(data)
#         if dmax - dmin > 1e-10:
#             norm_data = (data - dmin) / (dmax - dmin)
#         else:
#             norm_data = data * 0
        
#         # Hot colormap implementation
#         colored = np.zeros((*data.shape, 3), dtype=np.uint8)
        
#         # Red: ramp up quickly
#         colored[:, :, 0] = np.clip(norm_data * 1.7 * 255, 0, 255).astype(np.uint8)
#         # Green: ramp up in middle
#         colored[:, :, 1] = np.clip((norm_data * 1.5 - 0.3) * 255, 0, 255).astype(np.uint8)
#         # Blue: only at high values
#         colored[:, :, 2] = np.clip((norm_data * 3 - 2) * 255, 0, 255).astype(np.uint8)
        
#         return colored

#     def paintEvent(self, event):
#         painter = QPainter(self)
#         painter.fillRect(self.rect(), QColor(255, 255, 255))

#         if not self.display_pixmap:
#             return

#         # Draw the spectrogram image
#         painter.drawPixmap(self.left_margin, self.top_margin, self.display_pixmap)

#         # Prepare font
#         painter.setPen(QPen(QColor(0, 0, 0), 1))
#         font = painter.font()
#         if font.pointSize() <= 0:
#             font.setPointSize(10)
#         painter.setFont(font)

#         # ---- Retrieve viewport indices ----
#         start_idx, end_idx = self.get_viewport_indices()
#         if start_idx is None:
#             return

#         # Recompute viewport_spec for frequency axis calculations
#         if self.zoomed and self.zoom_freq_range:
#             freq_start, freq_end = self.zoom_freq_range
#             viewport_spec = self.spectrogram[freq_start:freq_end, start_idx:end_idx]
#         else:
#             viewport_spec = self.spectrogram[:, start_idx:end_idx]

#         viewport_spec = np.flipud(viewport_spec)
#         viewport_height, viewport_width = viewport_spec.shape

#         # ---- TIME AXIS ----
#         # Use current time range
#         time_start, time_end = self._get_current_time_range()
        
#         num_time_ticks = 5
#         for i in range(num_time_ticks + 1):
#             fraction = i / num_time_ticks
#             # Calculate time value within the current viewport
#             time_val = time_start + fraction * (time_end - time_start)
            
#             # Apply offset only when displaying text
#             x_pos = self.left_margin + int(self.display_pixmap.width() * fraction)
#             text = f"{time_val + self.time_offset:.1f}s"
#             painter.drawText(x_pos - 20, self.height() - 5, text)

#         painter.drawText(self.width() // 2 - 20, self.height() - 25, "Time")

#         # ---- FREQUENCY AXIS ----
#         # Get current frequency range
#         freq_min, freq_max = self._get_current_freq_range()
        
#         num_freq_ticks = 6
#         for i in range(num_freq_ticks + 1):
#             fraction = i / num_freq_ticks
#             freq_val = freq_min + fraction * (freq_max - freq_min)
            
#             # Map frequency to pixel position (inverted: low freq at bottom)
#             if freq_max > freq_min:
#                 y_fraction = 1 - ((freq_val - freq_min) / (freq_max - freq_min))
#             else:
#                 y_fraction = 0.5
                
#             y_pos = self.top_margin + int(y_fraction * self.display_pixmap.height())
#             painter.drawText(5, y_pos + 5, f"{freq_val:.0f} Hz")

#         # Label
#         painter.save()
#         painter.translate(20, self.height() // 2)
#         painter.rotate(-90)
#         painter.drawText(0, 0, "Frequency (Hz)")
#         painter.restore()

#         # ---- Playback cursor ----
#         if self.playback_position is not None and not self.zoomed:
#             if self.viewport_start <= self.playback_position <= self.viewport_start + self.viewport_duration:
#                 relative_pos = (self.playback_position - self.viewport_start) / self.viewport_duration
#                 x_pos = self.left_margin + int(relative_pos * self.display_pixmap.width())

#                 painter.setPen(QPen(QColor(255, 0, 0), 2))
#                 painter.drawLine(x_pos, self.top_margin, x_pos, self.top_margin + self.display_pixmap.height())
#                 # also draw marker on time axis
#                 painter.setPen(QPen(QColor(255, 0, 0), 1))
#                 painter.drawText(x_pos - 20, self.top_margin - 5, f"{self.playback_position:.2f}s")

#         # ---- Zoom Rectangle ----
#         if self.zoom_rect and self.zoom_enabled:
#             painter.setPen(QPen(QColor(255, 255, 0), 2))
#             painter.drawRect(self.zoom_rect)

#         # ---- Mask Overlay ----
#         if self.mask_pixmap is not None:
#             painter.drawPixmap(self.left_margin, self.top_margin, self.mask_pixmap)

#         # ---- Rectangle selection (right-button) ----
#         if self.rect_select_rect is not None and self.brush_enabled:
#             painter.setPen(QPen(QColor(0, 200, 0), 2, Qt.PenStyle.DashLine))
#             painter.drawRect(self.rect_select_rect)

#         # ---- Selection waveform ----
#         if self.waveform_visible and self.selection_waveform_pixmap is not None:
#             wf_x = self.left_margin
#             wf_y = self.top_margin + self.display_pixmap.height() + 4
#             painter.drawPixmap(wf_x, wf_y, self.selection_waveform_pixmap)

#             # draw time axis for waveform
#             painter.setPen(QPen(QColor(0, 0, 0), 1))
#             painter.drawText(wf_x, wf_y + self.selection_waveform_height + 12, "Selection waveform")

#             # playback position on waveform
#             if self.selection_playback_pos is not None and self.selection_duration and self.selection_duration > 0:
#                 frac = max(0.0, min(1.0, self.selection_playback_pos / self.selection_duration))
#                 x_pos = wf_x + int(frac * self.selection_waveform_pixmap.width())
#                 painter.setPen(QPen(QColor(255, 0, 0), 2))
#                 painter.drawLine(x_pos, wf_y, x_pos, wf_y + self.selection_waveform_height)

#     def mousePressEvent(self, event):
#         if event.button() == Qt.MouseButton.LeftButton:
#             if self.rect_selection_mode:
#                 # Rectangle selection mode - start rectangle
#                 self.zoom_start = event.pos()
#                 self.zoom_rect = QRect(self.zoom_start, self.zoom_start)
#             elif self.zoom_enabled:
#                 # Zoom mode - start rectangle
#                 self.zoom_start = event.pos()
#                 self.zoom_rect = QRect(self.zoom_start, self.zoom_start)
#             elif self.brush_enabled:
#                 # Brush mode - left-button draws with brush
#                 self.drawing = True
#                 self.last_point = event.pos()
#                 self.draw_at(event.pos())
#         elif event.button() == Qt.MouseButton.RightButton and self.brush_enabled:
#             # Right-button rectangle selection while brush enabled
#             self.rect_select_start = event.pos()
#             self.rect_select_rect = QRect(self.rect_select_start, self.rect_select_start)
#             self.update()

#     def mouseMoveEvent(self, event):
#         if self.rect_selection_mode and self.zoom_start:
#             # Rectangle selection mode - update rectangle
#             self.zoom_rect = QRect(self.zoom_start, event.pos()).normalized()
#             self.update()
#         elif self.zoom_enabled and self.zoom_start:
#             # Zoom mode - update rectangle
#             self.zoom_rect = QRect(self.zoom_start, event.pos()).normalized()
#             self.update()
#         elif self.brush_enabled and self.drawing:
#             # Brush mode - draw while moving
#             self.draw_at(event.pos())
#             self.last_point = event.pos()
#         elif self.rect_select_start is not None:
#             # Right-button rectangle while brush enabled
#             self.rect_select_rect = QRect(self.rect_select_start, event.pos()).normalized()
#             self.update()

#     def mouseReleaseEvent(self, event):
#         if event.button() == Qt.MouseButton.LeftButton:
#             # Rectangle selection mode (left-click) - fill the selected area
#             if self.rect_selection_mode and self.zoom_start and self.zoom_rect:
#                 try:
#                     start_idx, end_idx = self.get_viewport_indices()
#                     if start_idx is None:
#                         self.zoom_start = None
#                         self.zoom_rect = None
#                         return
                    
#                     display_h = self.display_pixmap.height()
#                     x_start_raw = self.zoom_rect.left() - self.left_margin
#                     x_end_raw = self.zoom_rect.right() - self.left_margin
#                     y_start_raw = self.zoom_rect.top() - self.top_margin
#                     y_end_raw = self.zoom_rect.bottom() - self.top_margin
                    
#                     x_start = max(0, min(self.display_pixmap.width(), x_start_raw))
#                     x_end = max(0, min(self.display_pixmap.width(), x_end_raw))
#                     y_start = max(0, min(display_h, y_start_raw))
#                     y_end = max(0, min(display_h, y_end_raw))
                    
#                     if (x_end - x_start) >= 2 and (y_end - y_start) >= 2:
#                         displayed_time_bins = max(1, end_idx - start_idx)
#                         sel_bin_start = int((x_start / float(self.display_pixmap.width())) * displayed_time_bins)
#                         sel_bin_end = int((x_end / float(self.display_pixmap.width())) * displayed_time_bins)
#                         sel_bin_start = max(0, min(displayed_time_bins - 1, sel_bin_start))
#                         sel_bin_end = max(sel_bin_start + 1, min(displayed_time_bins, sel_bin_end))
                        
#                         time_start_idx = start_idx + sel_bin_start
#                         time_end_idx = start_idx + sel_bin_end
                        
#                         # Freq mapping
#                         if self.zoomed and self.zoom_freq_range:
#                             freq_start_idx = self.zoom_freq_range[0]
#                             freq_end_idx = self.zoom_freq_range[1]
#                         else:
#                             freq_start_idx = 0
#                             freq_end_idx = self.mask.shape[0]
                        
#                         displayed_freq_bins = max(1, freq_end_idx - freq_start_idx)
#                         frac_top = float(y_start) / float(display_h)
#                         frac_bottom = float(y_end) / float(display_h)
#                         data_frac_start = 1.0 - frac_bottom
#                         data_frac_end = 1.0 - frac_top
                        
#                         sel_freq_start = int(freq_start_idx + data_frac_start * displayed_freq_bins)
#                         sel_freq_end = int(freq_start_idx + data_frac_end * displayed_freq_bins)
#                         sel_freq_start = max(0, min(self.mask.shape[0] - 1, sel_freq_start))
#                         sel_freq_end = max(sel_freq_start + 1, min(self.mask.shape[0], sel_freq_end))
                        
#                         # Fill mask region
#                         self.mask[sel_freq_start:sel_freq_end, time_start_idx:time_end_idx] = 255
#                         self.update_display()
                        
#                         try:
#                             self.selectionChanged.emit()
#                         except Exception:
#                             pass
#                 finally:
#                     self.zoom_start = None
#                     self.zoom_rect = None
#                     self.update()
                    
#             # Zoom mode - apply zoom
#             elif self.zoom_enabled and self.zoom_rect:
#                 self.apply_zoom()
#                 self.zoom_start = None
#                 self.zoom_rect = None
                
#             # Brush mode - stop drawing
#             elif self.brush_enabled:
#                 self.drawing = False
#                 self.last_point = None
                
#         elif event.button() == Qt.MouseButton.RightButton and self.rect_select_rect is not None:
#             # Right-button rectangle selection (when brush enabled) - fill the selected area
#             try:
#                 start_idx, end_idx = self.get_viewport_indices()
#                 if start_idx is None:
#                     self.rect_select_start = None
#                     self.rect_select_rect = None
#                     return
                    
#                 display_h = self.display_pixmap.height()
#                 x_start_raw = self.rect_select_rect.left() - self.left_margin
#                 x_end_raw = self.rect_select_rect.right() - self.left_margin
#                 y_start_raw = self.rect_select_rect.top() - self.top_margin
#                 y_end_raw = self.rect_select_rect.bottom() - self.top_margin
                
#                 x_start = max(0, min(self.display_pixmap.width(), x_start_raw))
#                 x_end = max(0, min(self.display_pixmap.width(), x_end_raw))
#                 y_start = max(0, min(display_h, y_start_raw))
#                 y_end = max(0, min(display_h, y_end_raw))
                
#                 if (x_end - x_start) >= 2 and (y_end - y_start) >= 2:
#                     displayed_time_bins = max(1, end_idx - start_idx)
#                     sel_bin_start = int((x_start / float(self.display_pixmap.width())) * displayed_time_bins)
#                     sel_bin_end = int((x_end / float(self.display_pixmap.width())) * displayed_time_bins)
#                     sel_bin_start = max(0, min(displayed_time_bins - 1, sel_bin_start))
#                     sel_bin_end = max(sel_bin_start + 1, min(displayed_time_bins, sel_bin_end))
                    
#                     time_start_idx = start_idx + sel_bin_start
#                     time_end_idx = start_idx + sel_bin_end
                    
#                     # Freq mapping
#                     if self.zoomed and self.zoom_freq_range:
#                         freq_start_idx = self.zoom_freq_range[0]
#                         freq_end_idx = self.zoom_freq_range[1]
#                     else:
#                         freq_start_idx = 0
#                         freq_end_idx = self.mask.shape[0]
                    
#                     displayed_freq_bins = max(1, freq_end_idx - freq_start_idx)
#                     frac_top = float(y_start) / float(display_h)
#                     frac_bottom = float(y_end) / float(display_h)
#                     data_frac_start = 1.0 - frac_bottom
#                     data_frac_end = 1.0 - frac_top
                    
#                     sel_freq_start = int(freq_start_idx + data_frac_start * displayed_freq_bins)
#                     sel_freq_end = int(freq_start_idx + data_frac_end * displayed_freq_bins)
#                     sel_freq_start = max(0, min(self.mask.shape[0] - 1, sel_freq_start))
#                     sel_freq_end = max(sel_freq_start + 1, min(self.mask.shape[0], sel_freq_end))
                    
#                     # Fill mask region
#                     self.mask[sel_freq_start:sel_freq_end, time_start_idx:time_end_idx] = 255
#                     self.update_display()
                    
#                     try:
#                         self.selectionChanged.emit()
#                     except Exception:
#                         pass
#             finally:
#                 self.rect_select_start = None
#                 self.rect_select_rect = None
#                 self.update()

#     def apply_zoom(self):
#         if not self.zoom_rect or self.display_pixmap is None:
#             return

#         display_height = self.display_pixmap.height()
#         display_width = self.display_pixmap.width()

#         # rectangle coordinates relative to spectrogram image
#         x_start_raw = self.zoom_rect.left() - self.left_margin
#         x_end_raw = self.zoom_rect.right() - self.left_margin
#         y_start_raw = self.zoom_rect.top() - self.top_margin
#         y_end_raw = self.zoom_rect.bottom() - self.top_margin

#         # Clip to display bounds
#         x_start = max(0, min(display_width, x_start_raw))
#         x_end = max(0, min(display_width, x_end_raw))
#         y_start = max(0, min(display_height, y_start_raw))
#         y_end = max(0, min(display_height, y_end_raw))

#         if (x_end - x_start) < 4 or (y_end - y_start) < 4:
#             return

#         # ----- TIME ZOOM -----
#         # Map screen X to time
#         time_start, time_end = self._get_current_time_range()
#         time_span = time_end - time_start
        
#         zoom_time_start = time_start + (x_start / display_width) * time_span
#         zoom_time_end = time_start + (x_end / display_width) * time_span
        
#         # Ensure minimal duration
#         zoom_time_duration = max(0.05, zoom_time_end - zoom_time_start)
        
#         # Update viewport to zoomed time range
#         self.viewport_start = zoom_time_start
#         self.viewport_duration = zoom_time_duration
#         self.zoom_time_range = (zoom_time_start, zoom_time_end)

#         # ----- FREQUENCY ZOOM -----
#         # Map screen Y to frequency (inverted: top=high freq, bottom=low freq)
#         freq_min, freq_max = self._get_current_freq_range()
#         freq_span = freq_max - freq_min
        
#         # Y is inverted for frequency
#         zoom_freq_min = freq_min + (1 - y_end/display_height) * freq_span
#         zoom_freq_max = freq_min + (1 - y_start/display_height) * freq_span
        
#         # Ensure minimal frequency range
#         zoom_freq_span = max(10.0, zoom_freq_max - zoom_freq_min)  # At least 10Hz
        
#         # Map frequency range back to spectrogram indices
#         if self.frequencies is not None and len(self.frequencies) > 0:
#             # Find indices in frequency array
#             freq_idx_min = np.searchsorted(self.frequencies, zoom_freq_min) - 1
#             freq_idx_max = np.searchsorted(self.frequencies, zoom_freq_max) + 1
            
#             # Clamp to valid range
#             freq_idx_min = max(0, min(freq_idx_min, len(self.frequencies)-1))
#             freq_idx_max = max(freq_idx_min + 1, min(freq_idx_max, len(self.frequencies)))
            
#             self.zoom_freq_range = (freq_idx_min, freq_idx_max)
#         else:
#             self.zoom_freq_range = None

#         self.zoomed = True
#         self.update_display()

#     def reset_zoom(self):
#         """Reset zoom to show full frequency range and reasonable time window"""
#         self.zoomed = False
#         self.zoom_time_range = None
#         self.zoom_freq_range = None

#         # Reset to show full frequency range
#         if self.frequencies is not None and len(self.frequencies) > 0:
#             # Already showing full range when not zoomed
#             pass

#         # Reset time viewport based on total duration
#         if self.times is not None and len(self.times) > 1:
#             total_duration = float(self.times[-1])
            
#             # For VERY long files (> 5 min), show first 60s
#             if total_duration > 300:  # 5 minutes
#                 self.viewport_duration = 60.0
#                 self.viewport_start = 0.0
#             # For medium files (1-5 min), show 30% of total
#             elif total_duration > 60:
#                 self.viewport_duration = total_duration * 0.3
#                 self.viewport_start = 0.0
#             # For short files, show everything
#             else:
#                 self.viewport_duration = total_duration
#                 self.viewport_start = 0.0
#         else:
#             self.viewport_duration = 60.0
#             self.viewport_start = 0.0

#         self.update_display()

#     def scroll_viewport(self, value):
#         """Scroll viewport using a 0-100 slider value."""
#         if self.times is None or len(self.times) == 0:
#             return
#         total_duration = float(self.times[-1])
#         frac = max(0.0, min(1.0, value / 100.0))

#         # If zoomed, scroll inside zoomed time range
#         if self.zoomed and self.zoom_time_range:
#             zoom_start, zoom_end = self.zoom_time_range
#             zoom_span = max(0.0, zoom_end - zoom_start)
#             if zoom_span <= self.viewport_duration:
#                 self.viewport_start = float(zoom_start)
#             else:
#                 max_start = float(zoom_end - self.viewport_duration)
#                 self.viewport_start = float(zoom_start + frac * (max_start - zoom_start))
#         else:
#             max_start = max(0.0, total_duration - self.viewport_duration)
#             self.viewport_start = frac * max_start
#         self.update_display()

#     def set_playback_position(self, t):
#         """Set playback position in seconds (absolute time)."""
#         self.playback_position = t
#         self.update()

#     def get_mask(self):
#         return None if self.mask is None else self.mask.copy()

#     def draw_at(self, pos):
#         if self.mask is None or self.display_pixmap is None:
#             return

#         adjusted_x = pos.x() - self.left_margin
#         adjusted_y = pos.y() - self.top_margin

#         if adjusted_x < 0 or adjusted_x >= self.display_pixmap.width():
#             return
#         if adjusted_y < 0 or adjusted_y >= self.display_pixmap.height():
#             return

#         start_idx, end_idx = self.get_viewport_indices()
#         if start_idx is None:
#             return

#         spec_x = int((adjusted_x / self.display_pixmap.width()) * (end_idx - start_idx)) + start_idx

#         # Correct brush drawing mapping
#         display_h = self.display_pixmap.height()
#         data_fraction = 1 - (adjusted_y / display_h)
        
#         if self.zoomed and self.zoom_freq_range:
#             start_f, end_f = self.zoom_freq_range
#             spec_y = start_f + int(data_fraction * (end_f - start_f))
#         else:
#             spec_y = int(data_fraction * self.mask.shape[0])

#         spec_x = max(0, min(spec_x, self.mask.shape[1] - 1))
#         spec_y = max(0, min(spec_y, self.mask.shape[0] - 1))

#         # Soft circular brush with linear falloff for smoother, round strokes
#         radius = max(1, int(self.brush_size // 2))

#         y_start = max(0, spec_y - radius)
#         y_end = min(self.mask.shape[0], spec_y + radius + 1)
#         x_start = max(0, spec_x - radius)
#         x_end = min(self.mask.shape[1], spec_x + radius + 1)

#         h = y_end - y_start
#         w = x_end - x_start
#         if h <= 0 or w <= 0:
#             return

#         # If we have a last_point, interpolate between points to avoid gaps
#         points = [pos]
#         if self.last_point is not None and self.last_point != pos:
#             lp = self.last_point
#             dx = pos.x() - lp.x()
#             dy = pos.y() - lp.y()
#             dist = max(1.0, (dx*dx + dy*dy) ** 0.5)
#             steps = int(max(1, dist / max(1.0, radius * 0.5)))
#             for i in range(1, steps + 1):
#                 t = i / float(steps + 1)
#                 ix = int(lp.x() + dx * t)
#                 iy = int(lp.y() + dy * t)
#                 points.append(type(pos)(ix, iy))

#         for p in points:
#             # recalc mapping for each interpolated point
#             adjusted_x = p.x() - self.left_margin
#             adjusted_y = p.y() - self.top_margin
#             if adjusted_x < 0 or adjusted_x >= self.display_pixmap.width():
#                 continue
#             if adjusted_y < 0 or adjusted_y >= self.display_pixmap.height():
#                 continue

#             # map to spectrogram indices
#             start_idx, end_idx = self.get_viewport_indices()
#             if start_idx is None:
#                 continue

#             spec_x = int((adjusted_x / self.display_pixmap.width()) * (end_idx - start_idx)) + start_idx
#             display_h = self.display_pixmap.height()
#             data_fraction = 1 - (adjusted_y / display_h)
#             if self.zoomed and self.zoom_freq_range:
#                 start_f, end_f = self.zoom_freq_range
#                 spec_y = start_f + int(data_fraction * (end_f - start_f))
#             else:
#                 spec_y = int(data_fraction * self.mask.shape[0])

#             spec_x = max(0, min(spec_x, self.mask.shape[1] - 1))
#             spec_y = max(0, min(spec_y, self.mask.shape[0] - 1))

#             y0 = max(0, spec_y - radius)
#             y1 = min(self.mask.shape[0], spec_y + radius + 1)
#             x0 = max(0, spec_x - radius)
#             x1 = min(self.mask.shape[1], spec_x + radius + 1)

#             yy = np.arange(y0, y1) - spec_y
#             xx = np.arange(x0, x1) - spec_x
#             dy = yy[:, None]
#             dx = xx[None, :]
#             dist = np.sqrt(dx*dx + dy*dy)

#             kernel = np.clip(1.0 - (dist / float(radius)), 0.0, 1.0)
#             region = self.mask[y0:y1, x0:x1].astype(np.float32)
#             new_vals = (kernel * 255.0).astype(np.float32)
#             combined = np.maximum(region, new_vals)
#             self.mask[y0:y1, x0:x1] = combined.astype(self.mask.dtype)

#         # update cached mask pixmap for current viewport for immediate visual response
#         self.update_display()

#     def clear_mask(self):
#         if self.mask is not None:
#             self.mask.fill(0)
#             self.update_display()

#     def get_selected_pattern(self):
#         if self.mask is None or self.spectrogram is None:
#             return None

#         rows, cols = np.where(self.mask > 0)
#         if len(rows) == 0:
#             return None

#         min_row, max_row = rows.min(), rows.max()
#         min_col, max_col = cols.min(), cols.max()

#         pattern = self.spectrogram[min_row:max_row+1, min_col:max_col+1]

#         return pattern

#     def resizeEvent(self, event):
#         super().resizeEvent(event)
#         self.update_display()