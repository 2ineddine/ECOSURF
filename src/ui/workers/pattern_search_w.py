import os
import re
import numpy as np
import soundfile as sf
import librosa
from scipy.spatial.distance import cosine
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal


def compute_spectrogram(y, sr, n_fft=2048, hop_length=None):
    if hop_length is None:
        hop_length = n_fft // 4
    D = librosa.stft(y, n_fft=n_fft, hop_length=hop_length, window='hann')
    S = np.abs(D) ** 2
    S_db = librosa.power_to_db(S, ref=np.max)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    times = librosa.frames_to_time(np.arange(S_db.shape[1]), sr=sr, hop_length=hop_length, n_fft=n_fft)
    return freqs, times, S_db


class PatternSearchThread(QThread):
    """Background thread for pattern searching across files"""
    progress = pyqtSignal(int, str)
    match_found = pyqtSignal(dict)
    finished = pyqtSignal()

    def __init__(self, pattern_spec, pattern_audio, file_list, threshold=0.7):
        super().__init__()
        self.pattern_spec = pattern_spec
        self.pattern_audio = pattern_audio
        self.file_list = file_list
        self.threshold = threshold
        self.running = True

    def stop(self):
        self.running = False

    def run(self):
        total_files = len(self.file_list)

        for idx, file_path in enumerate(self.file_list):
            if not self.running:
                break

            filename = os.path.basename(file_path)
            self.progress.emit(int((idx / total_files) * 100), f"Searching {filename}...")

            try:
                audio, sr = sf.read(file_path)
                if len(audio.shape) > 1:
                    audio = np.mean(audio, axis=1)

                freqs, times, S_db = compute_spectrogram(audio, sr, n_fft=2048, hop_length=1536)

                matches = self.find_pattern_matches(S_db, self.pattern_spec, sr, times)

                metadata = self.parse_filename(filename)

                for match in matches:
                    match_info = {
                        'file': file_path,
                        'filename': filename,
                        'similarity': match['similarity'],
                        'time_start': match['time_start'],
                        'time_end': match['time_end'],
                        'metadata': metadata
                    }
                    self.match_found.emit(match_info)

            except Exception as e:
                print(f"Error processing {filename}: {e}")

        self.finished.emit()

    def find_pattern_matches(self, spectrogram, pattern, sr, times):
        matches = []
        pattern_height, pattern_width = pattern.shape
        spec_height, spec_width = spectrogram.shape

        if pattern_height > spec_height or pattern_width > spec_width:
            return matches

        step = max(1, pattern_width // 4)

        for i in range(0, spec_width - pattern_width, step):
            window = spectrogram[:pattern_height, i:i+pattern_width]

            pattern_flat = pattern.flatten()
            window_flat = window.flatten()

            try:
                similarity = 1 - cosine(pattern_flat, window_flat)
            except Exception:
                similarity = 0

            if similarity > self.threshold:
                time_start = times[i] if i < len(times) else 0
                time_end = times[min(i + pattern_width, len(times)-1)]

                matches.append({
                    'similarity': similarity,
                    'time_start': time_start,
                    'time_end': time_end
                })

        return matches

    def parse_filename(self, filename):
        match = re.match(r'(\w+)_(\d{8})_(\d{6})\.flac', filename)
        if match:
            device_id, date_str, time_str = match.groups()
            datetime_obj = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
            return {
                'device_id': device_id,
                'date': datetime_obj.strftime("%Y-%m-%d"),
                'time': datetime_obj.strftime("%H:%M:%S"),
                'datetime': datetime_obj
            }
        return {'device_id': 'unknown', 'date': 'unknown', 'time': 'unknown'}
