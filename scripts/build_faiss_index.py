"""
Script pour créer l'index FAISS à l'avance.
Exécuter UNE FOIS avant d'utiliser l'application.

Usage:
    python scripts/build_faiss_index.py --sample 0.1   # 10% des données
    python scripts/build_faiss_index.py --sample 1.0   # 100% des données
"""

import numpy as np
import pickle
import os
import argparse
import time

try:
    import faiss
except ImportError:
    print("ERREUR: FAISS non installé. Exécutez: pip install faiss-cpu")
    exit(1)


def build_index(emb_path, meta_path, sample_ratio=0.1, output_dir=None):
    """
    Construit un index FAISS à partir des embeddings.
    
    Args:
        emb_path: Chemin vers le fichier .npy des embeddings
        meta_path: Chemin vers le fichier .pkl des métadonnées
        sample_ratio: Ratio d'échantillonnage (0.1 = 10%)
        output_dir: Dossier de sortie (par défaut: même que emb_path)
    """
    
    if output_dir is None:
        output_dir = os.path.dirname(emb_path)
    
    print("=" * 60)
    print("CONSTRUCTION INDEX FAISS")
    print("=" * 60)
    
    # 1. Charger les embeddings avec memory-mapping (RAPIDE)
    print(f"\n[1/5] Chargement embeddings (memory-map): {emb_path}")
    start = time.time()
    embeddings_mmap = np.load(emb_path, mmap_mode='r')
    total_count = len(embeddings_mmap)
    dim = embeddings_mmap.shape[1]
    print(f"      Shape: {embeddings_mmap.shape}")
    print(f"      Temps: {time.time() - start:.1f}s")
    
    # 2. Charger les métadonnées
    print(f"\n[2/5] Chargement métadonnées: {meta_path}")
    start = time.time()
    with open(meta_path, 'rb') as f:
        metadata = pickle.load(f)
    print(f"      Nombre: {len(metadata)}")
    print(f"      Temps: {time.time() - start:.1f}s")
    
    # 3. Échantillonner si demandé
    sample_count = int(total_count * sample_ratio)
    
    if sample_ratio < 1.0:
        print(f"\n[3/5] Échantillonnage: {sample_ratio*100:.0f}% ({sample_count:,} / {total_count:,})")
        
        # Échantillonnage aléatoire mais reproductible
        np.random.seed(42)
        indices = np.random.choice(total_count, sample_count, replace=False)
        indices = np.sort(indices)
        
        # Extraire seulement les données sélectionnées (efficace avec mmap)
        print(f"      Extraction des embeddings sélectionnés...")
        embeddings = embeddings_mmap[indices].astype(np.float32)
        metadata = [metadata[i] for i in indices]
        
        print(f"      Nouvelle taille: {len(embeddings):,}")
    else:
        print(f"\n[3/5] Pas d'échantillonnage (100%)")
        embeddings = embeddings_mmap[:].astype(np.float32)
        indices = None
    
    # 4. Normaliser les embeddings
    print(f"\n[4/5] Normalisation des embeddings...")
    start = time.time()
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = (embeddings / (norms + 1e-8)).astype(np.float32)
    print(f"      Temps: {time.time() - start:.1f}s")
    
    # 5. Construire l'index FAISS
    print(f"\n[5/5] Construction index FAISS...")
    start = time.time()
    dim = normalized.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner Product = Cosine similarity sur vecteurs normalisés
    index.add(normalized)
    print(f"      Dimension: {dim}")
    print(f"      Vecteurs indexés: {index.ntotal:,}")
    print(f"      Temps: {time.time() - start:.1f}s")
    
    # 6. Sauvegarder
    sample_suffix = f"_sample{int(sample_ratio*100)}" if sample_ratio < 1.0 else ""
    
    index_path = os.path.join(output_dir, f"perch_embeddings{sample_suffix}.faiss")
    meta_out_path = os.path.join(output_dir, f"perch_info{sample_suffix}.pkl")
    emb_out_path = os.path.join(output_dir, f"perch_embeddings{sample_suffix}.npy")
    
    print(f"\n[SAVE] Sauvegarde des fichiers...")
    
    # Sauvegarder index FAISS
    faiss.write_index(index, index_path)
    print(f"       Index: {index_path}")
    
    # Sauvegarder métadonnées échantillonnées
    with open(meta_out_path, 'wb') as f:
        pickle.dump(metadata, f)
    print(f"       Métadonnées: {meta_out_path}")
    
    # Sauvegarder embeddings échantillonnés (pour référence)
    np.save(emb_out_path, embeddings)
    print(f"       Embeddings: {emb_out_path}")
    
    print("\n" + "=" * 60)
    print("✓ INDEX FAISS CRÉÉ AVEC SUCCÈS!")
    print("=" * 60)
    print(f"\nPour utiliser dans l'application, modifiez les chemins vers:")
    print(f"  - Embeddings: {emb_out_path}")
    print(f"  - Métadonnées: {meta_out_path}")
    print(f"  - Index FAISS: {index_path}")
    
    return index_path, meta_out_path, emb_out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Construire index FAISS pour la recherche d'embeddings")
    parser.add_argument("--sample", type=float, default=0.1, 
                        help="Ratio d'échantillonnage (0.1 = 10%%, 1.0 = 100%%)")
    parser.add_argument("--emb", type=str, default="perch2/perch_embeddings_FINAL.npy",
                        help="Chemin vers les embeddings")
    parser.add_argument("--meta", type=str, default="perch2/perch_info_FINAL.pkl",
                        help="Chemin vers les métadonnées")
    
    args = parser.parse_args()
    
    build_index(args.emb, args.meta, sample_ratio=args.sample)
