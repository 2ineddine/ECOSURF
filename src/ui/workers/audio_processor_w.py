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

    # File: ui/workers/audio_processor_w.py
    # REPLACE the entire run() method with this:

    def run(self):
        """Main computation thread - STREAMS FROM S3"""
        """Main computation thread - STREAMS FROM S3"""
        print(f"=== DEBUG: Starting processor ===")
        print(f"File(s) to process: {self.file_path}")

        if isinstance(self.file_path, list):
            print(f"Total files in list: {len(self.file_path)}")
            for i, fp in enumerate(self.file_path):
                print(f"  [{i}] {fp}")
                if not fp or not fp.startswith('s3://'):
                    print(f"  WARNING: Invalid path at index {i}: '{fp}'")
        try:
            # --- CHECK IF S3 URI ---
            if isinstance(self.file_path, str) and self.file_path.startswith('s3://'):
                # 1. PARSE S3 URI
                without_protocol = self.file_path[5:]  # Remove 's3://'
                parts = without_protocol.split('/', 1)
                if len(parts) == 2:
                    bucket_name, s3_path = parts
                else:
                    bucket_name = parts[0]
                    s3_path = ""
                
                # 2. LOAD CREDENTIALS
                import json, os, boto3, io
                cred_paths = [
                    'credentials.json',
                    os.path.join(os.getcwd(), 'credentials.json'),
                    os.path.join(os.path.expanduser('~'), '.config', 'ecosurf', 'credentials.json')
                ]
                
                creds = None
                for cp in cred_paths:
                    if os.path.exists(cp):
                        try:
                            with open(cp, 'r') as f:
                                creds = json.load(f)
                            break
                        except:
                            pass
                
                if not creds:
                    self.finished.emit(None)
                    return
                
                # 3. CONNECT TO S3
                session = boto3.session.Session()
                s3 = session.client(
                    's3',
                    region_name=creds.get('region', 'eu-west-2'),
                    aws_access_key_id=creds.get('ACCESS_KEY'),
                    aws_secret_access_key=creds.get('SECRET_KEY'),
                    endpoint_url=creds.get('endpoint', 'https://s3.eu-west-2.wasabisys.com')
                )
                
                self.progress.emit(10)
                
                # 4. DOWNLOAD TO MEMORY (NOT DISK)
                response = s3.get_object(Bucket=bucket_name, Key=s3_path)
                audio_bytes = response['Body'].read()
                
                self.progress.emit(30)
                
                # 5. LOAD AUDIO FROM BYTES
                audio, sr = librosa.load(
                        io.BytesIO(audio_bytes),
                        offset=self.time_range[0],
                        duration=self.time_range[1]-self.time_range[0],
                        sr=None
                    )
                
            else:
                # LOCAL FILE - existing code
                audio, sr = librosa.load(
                    self.file_path,
                    offset=self.time_range[0],
                    duration=self.time_range[1]-self.time_range[0]
                )
            
            if audio is None or len(audio) == 0:
                self.finished.emit(None)
                return
            
            self.progress.emit(50)
            
            # --- COMPUTE SPECTROGRAM (EXISTING CODE) ---
            stft = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length)
            self.progress.emit(70)
            
            spectrogram = librosa.amplitude_to_db(np.abs(stft), ref=np.max)
            self.progress.emit(80)
            
            frequencies = librosa.fft_frequencies(sr=sr, n_fft=self.n_fft)
            times = librosa.times_like(spectrogram, sr=sr, hop_length=self.hop_length)
            
            result = {
                'spectrogram': spectrogram,
                'frequencies': frequencies,
                'times': times,
                'sample_rate': sr,
                'audio': audio,
                'time_offset': self.time_range[0]
            }
            
            self.progress.emit(100)
            self.finished.emit(result)
            
        except Exception as e:
            print(f"Error in AudioProcessor: {e}")
            self.finished.emit(None)