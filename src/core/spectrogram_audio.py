from typing import Tuple, Optional, Dict
import numpy as np
import librosa

try:
    from scipy.ndimage import zoom, gaussian_filter
except Exception:
    zoom = None
    gaussian_filter = None


def _resize_mask(mask: np.ndarray, target_shape: Tuple[int, int]) -> np.ndarray:
    if mask.shape == target_shape:
        return mask
    if zoom is not None:
        factors = (target_shape[0] / mask.shape[0], target_shape[1] / mask.shape[1])
        return zoom(mask, factors, order=0)
    # fallback: nearest-neighbour using repeat
    ry = int(np.ceil(target_shape[0] / mask.shape[0]))
    rx = int(np.ceil(target_shape[1] / mask.shape[1]))
    m = np.repeat(np.repeat(mask, ry, axis=0), rx, axis=1)
    return m[: target_shape[0], : target_shape[1]]


def apply_mask_and_reconstruct(
    stft_complex: np.ndarray,
    mask: np.ndarray,
    *,
    mask_type: str = "hard",
    hop_length: int = 512,
    n_fft: int = 2048,
    length: Optional[int] = None,
    normalize_peak: float = 0.8,
) -> np.ndarray:
    if stft_complex is None:
        raise ValueError("stft_complex is required")

    n_bins, n_frames = stft_complex.shape
    mask_resized = _resize_mask(mask, (n_bins, n_frames))

    if mask_type == "soft" and gaussian_filter is not None:
        m = gaussian_filter(mask_resized.astype(float), sigma=2)
        if m.max() > 0:
            m = m / m.max()
    elif mask_type == "preserve":
        m = np.where(mask_resized > 0, 1.0, 0.2).astype(float)
    else:
        m = (mask_resized > 0).astype(float)

    magnitude = np.abs(stft_complex)
    phase = np.angle(stft_complex)

    masked_magnitude = magnitude * m
    masked_stft = masked_magnitude * np.exp(1j * phase)

    reconstructed = librosa.istft(masked_stft, hop_length=hop_length, win_length=n_fft, length=length)

    if reconstructed.size and np.max(np.abs(reconstructed)) > 0:
        reconstructed = reconstructed / np.max(np.abs(reconstructed)) * float(normalize_peak)

    return reconstructed.astype(np.float32)


def extract_patch_audio(
    stft_complex: np.ndarray,
    mask: np.ndarray,
    sample_rate: int,
    *,
    hop_length: int = 512,
    n_fft: int = 2048,
    time_offset: float = 0.0,
    mask_type: str = "hard",
    length: Optional[int] = None,
) -> Tuple[np.ndarray, Dict]:
    if stft_complex is None:
        raise ValueError("stft_complex is required")
    n_bins, n_frames = stft_complex.shape
    mask_resized = _resize_mask(mask, (n_bins, n_frames))
    time_cols = np.any(mask_resized > 0, axis=0)
    if not np.any(time_cols):
        return np.array([], dtype=np.float32), {}

    first_frame = int(np.where(time_cols)[0][0])
    last_frame = int(np.where(time_cols)[0][-1])

    times = librosa.frames_to_time(np.arange(n_frames), sr=sample_rate, hop_length=hop_length)
    time_start_s = times[first_frame] + float(time_offset)
    time_end_s = times[last_frame] + float(time_offset)

    reconstructed_full = apply_mask_and_reconstruct(
        stft_complex,
        mask_resized,
        mask_type=mask_type,
        hop_length=hop_length,
        n_fft=n_fft,
        length=length,
    )

    sample_start = int(first_frame * hop_length)
    sample_end = int(min((last_frame + 1) * hop_length, len(reconstructed_full)))

    audio = reconstructed_full[sample_start:sample_end].astype(np.float32)

    metadata = {
        "time_start_s": float(time_start_s),
        "time_end_s": float(time_end_s),
        "frame_start": int(first_frame),
        "frame_end": int(last_frame),
        "sample_start": int(sample_start),
        "sample_end": int(sample_end),
        "n_fft": int(n_fft),
        "hop_length": int(hop_length),
        "sample_rate": int(sample_rate),
        "mask_type": mask_type,
    }

    return audio, metadata
