# ECOSURF - Bioacoustic Analysis

ECOSURF is a PyQt6 desktop application for exploring long audio recordings,
visualizing spectrograms, and running similarity search with embeddings.

## How to Run

```bash
pip install -r requirements.txt
python main.py
```

If you use S3 download for data, add `credentials.json` at the project root
and run `python others/setup_data.py`.

## Architecture Overview

- The app starts in `main.py` and instantiates the main UI window.
- UI panels handle file loading, spectrograms, search, embeddings, clustering,
  and annotations.
- Core modules handle audio processing and embeddings I/O.
- Optional data and experiments live under `others/` and `pre_processing_data/`.

## Repository Structure (Detailed)

Top-level files:
- `main.py`: entry point that configures `src` on `sys.path` and launches the UI.
- `requirements.txt`: Python dependency list for the application.
- `README.md`: project documentation.
- `credentials.json`: optional S3 credentials (required only for data download).

Core Python packages:
- `src/`: application code package
  - `src/core/`: core logic and data handling
    - `src/core/__init__.py`: package marker.
    - `src/core/spectrogram_audio.py`: spectrogram computation and audio patch
      extraction utilities used by the UI.
    - `src/core/embedding_manager.py`: loading/searching embedding files and
      managing FAISS index usage.
    - `src/core/annotation_manager.py`: annotation read/write and persistence
      helpers for annotation dialogs.
  - `src/models/`: model package placeholder
    - `src/models/__init__.py`: package marker.
  - `src/ui/`: PyQt6 user interface
    - `src/ui/__init__.py`: package marker.
    - `src/ui/main_window.py`: current main UI window used by `main.py`.
    - `src/ui/main_window_v2.py`: older window implementation (legacy).
    - `src/ui/main_window_backup.py`: backup copy of an older UI version.
    - `src/ui/styles.py`: shared application styles.
    - `src/ui/components/`: reusable widgets
      - `src/ui/components/__init__.py`: package marker.
      - `src/ui/components/spectrogram_widget.py`: spectrogram display widget
        with zoom, selection, and playback cursor.
      - `src/ui/components/clustering_widget.py`: clustering visualization UI.
    - `src/ui/dialogs/`: modal dialogs
      - `src/ui/dialogs/__init__.py`: package marker.
      - `src/ui/dialogs/period_selection.py`: period/time selection dialog.
      - `src/ui/dialogs/clustering_dialog.py`: clustering dialog (legacy).
      - `src/ui/dialogs/clustering_dialog_fast.py`: optimized clustering dialog
        used by the current UI.
      - `src/ui/dialogs/annotation_dialog.py`: annotation creation/edit dialog.
      - `src/ui/dialogs/annotations_viewer.py`: annotation list/view dialog.
    - `src/ui/panels/`: main UI panels (current versions end with `_v2`)
      - `src/ui/panels/file_panel_v2.py`: file browsing and loading panel.
      - `src/ui/panels/spectrogram_panel_v2.py`: spectrogram controls and
        parameters (FFT, hop, display).
      - `src/ui/panels/view_panel_v2.py`: view controls and navigation.
      - `src/ui/panels/audio_panel_v2.py`: playback and audio controls.
      - `src/ui/panels/pattern_panel_v2.py`: selection and pattern search tools.
      - `src/ui/panels/search_panel_v2.py`: metadata and scope search panel.
      - `src/ui/panels/embedding_panel_v2.py`: embedding search and results.
      - `src/ui/panels/clustering_panel_v2.py`: clustering controls and actions.
    - `src/ui/workers/`: background workers
      - `src/ui/workers/audio_processor_w.py`: audio loading and spectrogram job.
      - `src/ui/workers/multifile_processor.py`: batch processing worker.
      - `src/ui/workers/pattern_search_w.py`: asynchronous pattern search worker.

Data and experiment folders:
- `pre_processing_data/`: preprocessing utilities and assets
  - `pre_processing_data/extract_data.py`: helper to extract/prepare datasets.
  - `pre_processing_data/period_locations.json`: period metadata.
  - `pre_processing_data/period_locations.pkl`: binary cache of period metadata.
- `others/`: non-core utilities and experiments
  - `others/config.yaml`: alternative configuration template.
  - `others/setup_data.py`: S3 download helper (used to populate data files).
  - `others/notebooks/cluster_labeling_birdnet.ipynb`: notebook for labeling.
  - `others/tests/__init__.py`: placeholder for external tests.
  - `others/scripts/setup_perch.py`: download Perch embeddings and optionally
    run the app.
  - `others/scripts/build_faiss_index.py`: build FAISS index from embeddings.
  - `others/tropical/SAM-audio.ipynb`: notebook for SAM audio experiments.

Embedding and data directory:
- `perch2/`: local data and embedding artifacts used by embedding search
  - `perch2/perch_embeddings_FINAL.npy`: full embedding vectors.
  - `perch2/perch_info_FINAL.pkl`: metadata for embeddings.
  - `perch2/labels_v2.npy`: clustering labels.
  - `perch2/embeddings_2d_ALL.npy`: 2D embeddings for visualization.
  - `perch2/perch_embeddings_sample10.npy`: sampled embeddings.
  - `perch2/perch_embeddings_sample10.faiss`: FAISS index for sample set.
  - `perch2/perch_info_sample10.pkl`: sample metadata.
  - `perch2/cluster_labels_birdnet.csv`: class labels.
  - `perch2/cluster_labels_birdnet.pkl`: labels in pickle format.
  - `perch2/cluster_species_mapping.pkl`: cluster-to-species mapping.
  - `perch2/clustering_v2.py`: clustering utilities (legacy).
  - `perch2/clustering_v3.py`: updated clustering utilities.
  - `perch2/extract_perch.py`: helper for extracting Perch embeddings.
  - `perch2/clusters_v2.png`: clustering visualization image.
  - `perch2/Clustering.ipynb`: clustering exploration notebook.

## Functional Overview

- File loading: handled by `file_panel_v2.py` and `audio_processor_w.py`.
- Spectrogram view: `spectrogram_panel_v2.py` and `spectrogram_widget.py`.
- Playback controls: `audio_panel_v2.py` and audio methods in `main_window.py`.
- Pattern search: `pattern_panel_v2.py` and `pattern_search_w.py`.
- Search scope/filters: `search_panel_v2.py`.
- Embedding search: `embedding_panel_v2.py` + `embedding_manager.py`.
- Clustering: `clustering_panel_v2.py` + `clustering_dialog_fast.py`.
- Annotations: `annotation_dialog.py`, `annotations_viewer.py`,
  `annotation_manager.py`.

## Notes

- The current UI uses the `_v2` panel set and `src/ui/main_window.py`.
- Legacy UI files remain for reference (`main_window_v2.py`,
  `main_window_backup.py`).
