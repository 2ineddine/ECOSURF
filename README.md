# ECOSURF - Bioacoustic Analysis

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Placez `credentials.json` a la racine du projet:
```json
{
  "endpoint": "https://...",
  "ACCESS_KEY": "...",
  "SECRET_KEY": "...",
  "bucket": "ecosurf-dataset"
}
```

## Telechargement des donnees

```bash
python setup_data.py
```

### Si le script ne fonctionne pas

Telechargez manuellement depuis S3 (dossier `perch2/`) et placez dans `perch2/`:

```
perch2/
  embeddings_2d_ALL.npy
  labels_v2.npy
  perch_info_FINAL.pkl
  perch_embeddings_FINAL.npy
  perch_embeddings_sample10.npy
  perch_embeddings_sample10.faiss
  perch_info_sample10.pkl
```

## Lancement

```bash
python src/main.py
```
