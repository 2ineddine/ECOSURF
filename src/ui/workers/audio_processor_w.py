import numpy as np
import soundfile as sf
import librosa
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


class AudioProcessor(QThread):
    """Background thread for audio processing"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)

    def __init__(self, file_path, n_fft=2048, hop_length=512, time_range=None):
        super().__init__()
        self.file_path = file_path
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.time_range = time_range

    def run(self):
        try:
            audio, sr = sf.read(self.file_path)

            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)

            if self.time_range:
                start_sample = int(self.time_range[0] * sr)
                end_sample = int(self.time_range[1] * sr)
                audio = audio[start_sample:end_sample]

            self.progress.emit(30)

            freqs, times, S_db = compute_spectrogram(audio, sr, n_fft=self.n_fft, hop_length=self.hop_length)

            # Limit to 20kHz if present
            max_freq_idx = np.searchsorted(freqs, 20000)
            if max_freq_idx > 0 and max_freq_idx < len(freqs):
                freqs = freqs[:max_freq_idx]
                S_db = S_db[:max_freq_idx, :]

            self.progress.emit(70)

            Sxx_norm = (S_db - S_db.min()) / (S_db.max() - S_db.min()) if S_db.max() != S_db.min() else S_db * 0

            self.progress.emit(100)

            result = {
                'spectrogram': Sxx_norm,
                'frequencies': freqs,
                'times': times,
                'sample_rate': sr,
                'audio': audio,
                'time_range': self.time_range,
                'time_offset': self.time_range[0] if self.time_range else 0
            }

            self.finished.emit(result)

        except Exception as e:
            print(f"Error processing audio: {e}")
            self.finished.emit(None)
