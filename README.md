# ECOSURF

ECOSURF is a desktop workspace for exploring bioacoustic recordings. It combines audio playback, spectrogram inspection, annotations, and searches over audio patterns and precomputed embeddings.

## What the application includes

- Load and navigate long audio recordings in a PyQt6 interface.
- Inspect spectrograms, select time regions, and listen to audio.
- Search for similar patterns and review results.
- Explore embedding similarity with FAISS and inspect clustering views when prepared data is available.
- Create and review annotations.

```text
Audio files -> PyQt6 workspace -> spectrogram, playback, selections, annotations
Prepared embeddings -> FAISS search -> similar segments and clustering views
```

## Run locally

The dependency file recommends Python 3.10 or 3.11. From the repository root, create and activate a virtual environment, then run:

```bash
python -m pip install -r requirements.txt
python main.py
```

On Windows PowerShell, you can use `py -3.11 -m venv .venv` and run the commands through `.\.venv\Scripts\python.exe`. A desktop environment and working audio device are needed for the GUI.

## Optional embedding data

The repository does not include the large `perch2/` embedding artifacts. The embedding and clustering features depend on prepared files such as vectors, metadata, and a FAISS index. `others/setup_data.py` can download the expected files from an S3-compatible store if you have access.

For that optional download, create a local `credentials.json` containing `ACCESS_KEY`, `SECRET_KEY`, `endpoint`, and `bucket`, then run `python others/setup_data.py`. This file is ignored by Git. Keep credentials out of commits.

## Project layout

- `main.py` starts the desktop application.
- `src/ui/` contains the interface, panels, dialogs, and background workers.
- `src/core/` contains spectrogram, embedding, and annotation logic.
- `pre_processing_data/` and `others/` contain data preparation and research utilities.

## Status

ECOSURF is a research prototype. Some features require optional data and external services. Installation and GUI behavior have not been verified as part of this documentation update.
