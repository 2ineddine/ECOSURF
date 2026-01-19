# ECOSURF - Bioacoustic Analysis

ECOSURF is a PyQt6 desktop application for exploring long audio recordings,
visualizing spectrograms, and running similarity search with embeddings.

## Features

- Load audio files and browse timelines
- Spectrogram visualization with zoom, brush, and region selection
- Pattern search over selections
- Embedding search with ranked results and quick playback
- 2D embedding view and clustering tools
- Annotation workflow and viewer

## Project Structure

Top-level files:
- `main.py`: application entry point
- `requirements.txt`: Python dependencies
- `config.yaml`: optional configuration file
- `credentials.json`: optional S3 credentials for data download

Core code:
- `src/core/`: audio processing, embeddings, and core logic
- `src/models/`: model package placeholder
- `src/ui/`: PyQt UI code
  - `src/ui/main_window.py`: main application window (current UI)
  - `src/ui/panels/*_v2.py`: current panel implementations
  - `src/ui/components/`: reusable UI widgets
  - `src/ui/dialogs/`: dialogs (clustering, annotations, period selection)
  - `src/ui/workers/`: background processing workers
  - `src/ui/styles.py`: shared UI styles

Data and experiments:
- `pre_processing_data/`: preprocessing scripts and datasets
- `notebooks/` and `*.ipynb`: research and prototyping notebooks
- `others/` and `tests/`: auxiliary scripts and tests

## Embeddings Paths

The app expects embedding files under `perch2/` (directory name only; details
omitted here). The important paths used by the app are:

- `perch2/perch_embeddings_FINAL.npy`
- `perch2/perch_info_FINAL.pkl`
- `perch2/labels_v2.npy`
- `perch2/embeddings_2d_ALL.npy`
- `perch2/perch_embeddings_sample10.npy`
- `perch2/perch_embeddings_sample10.faiss`
- `perch2/perch_info_sample10.pkl`

If these files are missing, the UI still launches but embedding features will
be disabled until the data is available.

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Configuration

If you need to download data from S3, place `credentials.json` at the project
root with:

```json
{
  "endpoint": "https://...",
  "ACCESS_KEY": "...",
  "SECRET_KEY": "...",
  "bucket": "ecosurf-dataset"
}
```

Then run:

```bash
python setup_data.py
```

## Tests

Test helpers live under `tests/` and `others/`. They are not required to run
the application.
