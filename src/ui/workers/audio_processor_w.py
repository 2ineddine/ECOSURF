import numpy as np
import librosa
from PyQt6.QtCore import QThread, pyqtSignal
import json
import os
import boto3
import io
import tempfile
import hashlib

# Cache directory for S3 downloads
CACHE_DIR = os.path.join(tempfile.gettempdir(), "ecosurf_cache")


def compute_spectrogram(y, sr, n_fft=2048, hop_length=None):
    """Helper function to compute spectrogram"""
    if hop_length is None:
        hop_length = n_fft // 4
    D = librosa.stft(y, n_fft=n_fft, hop_length=hop_length, window='hann')
    S = np.abs(D) ** 2
    S_db = librosa.power_to_db(S, ref=np.max)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    times = librosa.frames_to_time(np.arange(S_db.shape[1]), sr=sr, hop_length=hop_length, n_fft=n_fft)
    return freqs, times, S_db


class AudioProcessor(QThread):
    """Universal audio processor with separate methods for each mode"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)

    def __init__(self, file_path, n_fft=2048, hop_length=512, time_range=None, recording_type="canopé", source_type="local"):
        """
        Args:
            file_path: Can be a string (single file) or list (multiple files)
            n_fft: FFT size
            hop_length: Hop length
            time_range: Tuple (start, end) in seconds or None for full duration
            recording_type: "canopé" or "ground"
            source_type: "database" or "local"
        """
        super().__init__()
        self.file_path = file_path
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.time_range = time_range
        self.recording_type = recording_type
        self.source_type = source_type
        self.is_multi_file = isinstance(file_path, list)
        
    def run(self):
        """Main computation thread - routes to appropriate method"""
        print(f"=== DEBUG: Starting AudioProcessor ===")
        print(f"Source type: {self.source_type}")
        print(f"Recording type: {self.recording_type}")
        print(f"Is multi-file: {self.is_multi_file}")
        
        try:
            # Route to appropriate method based on source type and file count
            if self.source_type == "database":
                if self.is_multi_file:
                    result = self._process_database_multifile()
                else:
                    result = self._process_database_single()
            else:  # local
                if self.is_multi_file:
                    result = self._process_local_multifile()
                else:
                    result = self._process_local_single()
            
            self.finished.emit(result)
            
        except Exception as e:
            print(f"Error in AudioProcessor: {e}")
            import traceback
            traceback.print_exc()
            self.finished.emit(None)
    
    # ==================== DATABASE (S3) METHODS ====================
    
    def _process_database_single(self):
        """Process single file from database (S3)"""
        print(f"Processing single database file: {self.file_path}")
        
        # Get S3 client
        s3_client = self._get_s3_client()
        if s3_client is None:
            return None
        
        # Load audio from S3
        audio, sr = self._load_database_audio(self.file_path, s3_client)
        if audio is None:
            return None
        
        self.progress.emit(50)
        
        # Select channel if stereo
        audio = self._select_channel(audio)
        
        # Compute spectrogram
        result = self._compute_spectrogram(audio, sr)
        
        self.progress.emit(100)
        return result
    
    def _process_database_multifile(self):
        """Process multiple files from database (S3)"""
        print(f"Processing {len(self.file_path)} database files")
        
        # Get S3 client
        s3_client = self._get_s3_client()
        if s3_client is None:
            return None
        
        all_spectrograms = []
        all_frequencies = None
        all_times = []
        all_audio = []
        current_time_offset = 0.0
        
        # Process each file
        for i, file_path in enumerate(self.file_path):
            print(f"  Processing database file {i+1}/{len(self.file_path)}: {file_path}")
            
            # Load audio from S3
            audio, sr = self._load_database_audio(file_path, s3_client)
            if audio is None:
                continue
            
            # Select channel if stereo
            audio = self._select_channel(audio)
            
            # Compute spectrogram for this file
            stft = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length)
            spectrogram = librosa.amplitude_to_db(np.abs(stft), ref=np.max)
            
            # Get frequency bins (same for all files)
            if all_frequencies is None:
                all_frequencies = librosa.fft_frequencies(sr=sr, n_fft=self.n_fft)
            
            # Get time points with offset
            times = librosa.times_like(spectrogram, sr=sr, hop_length=self.hop_length)
            times_with_offset = times + current_time_offset
            
            # Store results
            all_spectrograms.append(spectrogram)
            all_times.append(times_with_offset)
            all_audio.append(audio)
            
            # Update offsets
            file_duration = len(audio) / sr
            current_time_offset += file_duration
            
            # Update progress
            progress = int((i + 1) / len(self.file_path) * 100)
            self.progress.emit(progress)
        
        # Concatenate results
        if not all_spectrograms:
            return None
            
        result = self._concatenate_results(
            all_spectrograms, all_frequencies, all_times, all_audio, 
            sr, current_time_offset, len(all_spectrograms)
        )
        
        return result
    
    def _get_cache_path(self, s3_uri):
        """Get cache file path for S3 URI"""
        os.makedirs(CACHE_DIR, exist_ok=True)
        cache_key = hashlib.md5(s3_uri.encode()).hexdigest()
        return os.path.join(CACHE_DIR, f"{cache_key}.cache")
    
    def _load_from_cache(self, s3_uri):
        """Try to load audio from local cache"""
        cache_path = self._get_cache_path(s3_uri)
        if os.path.exists(cache_path):
            try:
                print(f"  [CACHE HIT] Loading from cache: {s3_uri[:50]}...")
                return open(cache_path, 'rb').read()
            except:
                pass
        return None
    
    def _save_to_cache(self, s3_uri, audio_bytes):
        """Save audio bytes to local cache"""
        try:
            cache_path = self._get_cache_path(s3_uri)
            with open(cache_path, 'wb') as f:
                f.write(audio_bytes)
            print(f"  [CACHE SAVE] Saved to cache")
        except Exception as e:
            print(f"  [CACHE ERROR] Could not save: {e}")
    
    def _load_database_audio(self, s3_uri, s3_client):
        """Load audio from S3 database with local caching"""
        try:
            # Try cache first
            audio_bytes = self._load_from_cache(s3_uri)
            
            # If not in cache, download from S3
            if audio_bytes is None:
                print(f"  [CACHE MISS] Downloading from S3...")
                audio_bytes = self._download_from_s3(s3_uri, s3_client)
                if audio_bytes is None:
                    return None, None
                # Save to cache for next time
                self._save_to_cache(s3_uri, audio_bytes)
            
            # Load from bytes
            if self.time_range:
                audio, sr = librosa.load(
                    io.BytesIO(audio_bytes),
                    offset=self.time_range[0],
                    duration=self.time_range[1]-self.time_range[0],
                    sr=None,
                    mono=False  # Keep stereo
                )
            else:
                audio, sr = librosa.load(
                    io.BytesIO(audio_bytes),
                    sr=None,
                    mono=False  # Keep stereo
                )
            
            return audio, sr
            
        except Exception as e:
            print(f"Error loading database audio from {s3_uri}: {e}")
            return None, None
    
    # ==================== LOCAL FILE METHODS ====================
    
    def _process_local_single(self):
        """Process single local file"""
        print(f"Processing single local file: {self.file_path}")
        
        # Load audio from local file
        audio, sr = self._load_local_audio(self.file_path)
        if audio is None:
            return None
        
        self.progress.emit(50)
        
        # Select channel if stereo
        audio = self._select_channel(audio)
        
        # Compute spectrogram
        result = self._compute_spectrogram(audio, sr)
        
        self.progress.emit(100)
        return result
    
    def _process_local_multifile(self):
        """Process multiple local files"""
        print(f"Processing {len(self.file_path)} local files")
        
        all_spectrograms = []
        all_frequencies = None
        all_times = []
        all_audio = []
        current_time_offset = 0.0
        
        # Process each file
        for i, file_path in enumerate(self.file_path):
            print(f"  Processing local file {i+1}/{len(self.file_path)}: {file_path}")
            
            # Load audio from local file
            audio, sr = self._load_local_audio(file_path)
            if audio is None:
                continue
            
            # Select channel if stereo
            audio = self._select_channel(audio)
            
            # Compute spectrogram for this file
            stft = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length)
            spectrogram = librosa.amplitude_to_db(np.abs(stft), ref=np.max)
            
            # Get frequency bins (same for all files)
            if all_frequencies is None:
                all_frequencies = librosa.fft_frequencies(sr=sr, n_fft=self.n_fft)
            
            # Get time points with offset
            times = librosa.times_like(spectrogram, sr=sr, hop_length=self.hop_length)
            times_with_offset = times + current_time_offset
            
            # Store results
            all_spectrograms.append(spectrogram)
            all_times.append(times_with_offset)
            all_audio.append(audio)
            
            # Update offsets
            file_duration = len(audio) / sr
            current_time_offset += file_duration
            
            # Update progress
            progress = int((i + 1) / len(self.file_path) * 100)
            self.progress.emit(progress)
        
        # Concatenate results
        if not all_spectrograms:
            return None
            
        result = self._concatenate_results(
            all_spectrograms, all_frequencies, all_times, all_audio, 
            sr, current_time_offset, len(all_spectrograms)
        )
        
        return result
    
    def _load_local_audio(self, file_path):
        """Load audio from local file"""
        try:
            if self.time_range:
                audio, sr = librosa.load(
                    file_path,
                    offset=self.time_range[0],
                    duration=self.time_range[1]-self.time_range[0],
                    mono=False  # Keep stereo
                )
            else:
                audio, sr = librosa.load(
                    file_path,
                    mono=False  # Keep stereo
                )
            
            return audio, sr
            
        except Exception as e:
            print(f"Error loading local audio from {file_path}: {e}")
            return None, None
    
    # ==================== SHARED HELPER METHODS ====================
    
    def _get_s3_client(self):
        """Create and return S3 client for database access"""
        try:
            # Load credentials
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
                print("No S3 credentials found")
                return None
            
            # Create client
            session = boto3.session.Session()
            s3 = session.client(
                's3',
                region_name=creds.get('region', 'eu-west-2'),
                aws_access_key_id=creds.get('ACCESS_KEY'),
                aws_secret_access_key=creds.get('SECRET_KEY'),
                endpoint_url=creds.get('endpoint', 'https://s3.eu-west-2.wasabisys.com')
            )
            
            return s3
            
        except Exception as e:
            print(f"Error creating S3 client: {e}")
            return None
    
    def _download_from_s3(self, s3_uri, s3_client):
        """Download file from S3 to memory"""
        try:
            # Parse S3 URI
            without_protocol = s3_uri[5:]  # Remove 's3://'
            parts = without_protocol.split('/', 1)
            if len(parts) == 2:
                bucket_name, s3_path = parts
            else:
                bucket_name = parts[0]
                s3_path = ""
            
            # Download to memory
            response = s3_client.get_object(Bucket=bucket_name, Key=s3_path)
            return response['Body'].read()
            
        except Exception as e:
            print(f"Error downloading from S3: {e}")
            return None
    
    def _select_channel(self, audio):
        """Select channel from stereo audio based on recording_type"""
        if audio.ndim == 2:  # Stereo audio
            if self.recording_type == "ground":
                return audio[0, :]  # Channel 0 = Ground
            else:  # "canopé" or default
                return audio[1, :]  # Channel 1 = Canopé
        # If mono, return as-is
        return audio
    
    def _compute_spectrogram(self, audio, sr):
        """Compute spectrogram for single audio"""
        stft = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length)
        spectrogram = librosa.amplitude_to_db(np.abs(stft), ref=np.max)
        frequencies = librosa.fft_frequencies(sr=sr, n_fft=self.n_fft)
        times = librosa.times_like(spectrogram, sr=sr, hop_length=self.hop_length)
        
        return {
            'spectrogram': spectrogram,
            'frequencies': frequencies,
            'times': times,
            'sample_rate': sr,
            'audio': audio,
            'time_offset': self.time_range[0] if self.time_range else 0.0,
            'recording_type': self.recording_type,
            'file_count': 1,
            'source_type': self.source_type
        }
    
    def _concatenate_results(self, spectrograms, frequencies, times_list, audio_list, sr, total_duration, file_count):
        """Concatenate results from multiple files"""
        combined_spectrogram = np.hstack(spectrograms)
        combined_times = np.concatenate(times_list)
        combined_audio = np.concatenate(audio_list)
        
        return {
            'spectrogram': combined_spectrogram,
            'frequencies': frequencies,
            'times': combined_times,
            'sample_rate': sr,
            'audio': combined_audio,
            'time_offset': 0.0,
            'file_count': file_count,
            'total_duration': total_duration,
            'recording_type': self.recording_type,
            'source_type': self.source_type
        }