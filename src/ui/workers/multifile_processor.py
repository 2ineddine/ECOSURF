import numpy as np
import librosa
from PyQt6.QtCore import QThread, pyqtSignal

class MultiFileAudioProcessor(QThread):
    """Computes spectrograms for multiple files and concatenates them"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    
    def __init__(self, file_list, n_fft, hop_length, time_range, recording_type="canopé"):
        super().__init__()
        self.file_list = file_list  # List of file paths
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.time_range = time_range  # For each file
        self.recording_type = recording_type  # "canopé" or "ground"

    def run(self):
        """Main computation thread - STREAMS FROM S3 with stereo channel handling"""
        print(f"=== DEBUG: Starting multi-file processor ===")
        print(f"Files to process: {len(self.file_list)}")
        print(f"Recording type: {self.recording_type}")
        
        for i, fp in enumerate(self.file_list):
            print(f"  [{i}] {fp}")

        try:
            # --- PREPARE S3 CLIENT (ONCE) ---
            import json, os, boto3, io
            creds = None
            cred_paths = [
                'credentials.json',
                os.path.join(os.getcwd(), 'credentials.json'),
                os.path.join(os.path.expanduser('~'), '.config', 'ecosurf', 'credentials.json')
            ]
            
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
            
            # Create S3 client
            session = boto3.session.Session()
            s3 = session.client(
                's3',
                region_name=creds.get('region', 'eu-west-2'),
                aws_access_key_id=creds.get('ACCESS_KEY'),
                aws_secret_access_key=creds.get('SECRET_KEY'),
                endpoint_url=creds.get('endpoint', 'https://s3.eu-west-2.wasabisys.com')
            )
            
            all_spectrograms = []
            all_frequencies = None
            all_times = []
            all_audio = []
            current_time_offset = 0.0
            
            # --- PROCESS EACH FILE ---
            for i, file_path in enumerate(self.file_list):
                # Check if S3 URI
                if isinstance(file_path, str) and file_path.startswith('s3://'):
                    # 1. PARSE S3 URI
                    without_protocol = file_path[5:]  # Remove 's3://'
                    parts = without_protocol.split('/', 1)
                    if len(parts) == 2:
                        bucket_name, s3_path = parts
                    else:
                        bucket_name = parts[0]
                        s3_path = ""
                    
                    # 2. DOWNLOAD TO MEMORY
                    try:
                        response = s3.get_object(Bucket=bucket_name, Key=s3_path)
                        audio_bytes = response['Body'].read()
                        
                        # 3. LOAD FROM BYTES (STEREO)
                        if self.time_range:
                            audio, sr = librosa.load(
                                io.BytesIO(audio_bytes),
                                offset=self.time_range[0],
                                duration=self.time_range[1]-self.time_range[0],
                                sr=None,
                                mono=False  # Load as stereo
                            )
                        else:
                            audio, sr = librosa.load(
                                io.BytesIO(audio_bytes),
                                sr=None,
                                mono=False  # Load as stereo
                            )
                    except Exception as e:
                        print(f"Failed to load {file_path}: {e}")
                        continue
                        
                else:
                    # LOCAL FILE - load stereo
                    if self.time_range:
                        audio, sr = librosa.load(
                            file_path,
                            offset=self.time_range[0],
                            duration=self.time_range[1]-self.time_range[0],
                            mono=False  # Load as stereo
                        )
                    else:
                        audio, sr = librosa.load(
                            file_path,
                            mono=False  # Load as stereo
                        )
                
                if audio is None or len(audio) == 0:
                    continue
                
                # --- SELECT CHANNEL BASED ON RECORDING TYPE ---
                if audio.ndim == 2:  # Stereo audio
                    if self.recording_type == "ground":
                        audio = audio[0, :]  # Channel 0 = Ground
                    else:  # "canopé" or default
                        audio = audio[1, :]  # Channel 1 = Canopé
                # If mono, use as-is
                
                # --- COMPUTE SPECTROGRAM ---
                stft = librosa.stft(audio, n_fft=self.n_fft, hop_length=self.hop_length)
                spectrogram = librosa.amplitude_to_db(np.abs(stft), ref=np.max)
                
                # Get frequency bins (same for all files)
                if all_frequencies is None:
                    all_frequencies = librosa.fft_frequencies(sr=sr, n_fft=self.n_fft)
                
                # Get time points
                times = librosa.times_like(spectrogram, sr=sr, hop_length=self.hop_length)
                times_with_offset = times + current_time_offset
                
                # Store results
                all_spectrograms.append(spectrogram)
                all_times.append(times_with_offset)
                all_audio.append(audio)
                
                # Update offsets
                file_duration = len(audio) / sr
                current_time_offset += file_duration
                
                # Progress
                progress = int((i + 1) / len(self.file_list) * 100)
                self.progress.emit(progress)
            
            # --- CONCATENATE RESULTS ---
            if not all_spectrograms:
                self.finished.emit(None)
                return
                
            combined_spectrogram = np.hstack(all_spectrograms)
            combined_times = np.concatenate(all_times)
            combined_audio = np.concatenate(all_audio)
            total_duration = current_time_offset
            
            result = {
                'spectrogram': combined_spectrogram,
                'frequencies': all_frequencies,
                'times': combined_times,
                'sample_rate': sr,
                'audio': combined_audio,
                'time_offset': 0.0,
                'file_count': len(all_spectrograms),
                'total_duration': total_duration,
                'recording_type': self.recording_type
            }
            
            self.finished.emit(result)
            
        except Exception as e:
            print(f"Error in MultiFileAudioProcessor: {e}")
            self.finished.emit(None)