"""
Gestionnaire d'embeddings avec support FAISS.
Supporte les index FAISS pré-construits pour un chargement ultra-rapide.
"""

import numpy as np
import pickle
import os
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("[WARNING] FAISS not installed. Run: pip install faiss-cpu")


class EmbeddingLoaderThread(QThread):
    """Thread pour charger les embeddings sans bloquer l'UI."""
    finished = pyqtSignal(int)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, emb_path, meta_path, manager, faiss_path=None):
        super().__init__()
        self.emb_path = emb_path
        self.meta_path = meta_path
        self.faiss_path = faiss_path
        self.manager = manager
    
    def run(self):
        try:
            # 1. Charger l'index FAISS pré-construit (RAPIDE)
            if self.faiss_path and os.path.exists(self.faiss_path) and FAISS_AVAILABLE:
                self.progress.emit("Chargement index FAISS pré-construit...")
                self.manager.index = faiss.read_index(self.faiss_path)
                self.progress.emit(f"Index FAISS: {self.manager.index.ntotal:,} vecteurs")
            else:
                self.manager.index = None
            
            # 2. Charger les métadonnées (léger)
            self.progress.emit("Chargement métadonnées...")
            with open(self.meta_path, 'rb') as f:
                self.manager.metadata = pickle.load(f)
            
            # 3. Charger les embeddings si nécessaire (lourd mais optionnel)
            if os.path.exists(self.emb_path):
                self.progress.emit("Chargement embeddings (référence)...")
                self.manager.embeddings = np.load(self.emb_path).astype(np.float32)
            
            # 4. Si pas d'index FAISS, construire ou mode lent
            if self.manager.index is None and self.manager.embeddings is not None:
                if FAISS_AVAILABLE:
                    self.progress.emit("Construction index FAISS (1ère fois)...")
                    self.manager._build_faiss_index()
                    # Sauvegarder pour la prochaine fois
                    if self.faiss_path:
                        self.progress.emit("Sauvegarde index FAISS...")
                        faiss.write_index(self.manager.index, self.faiss_path)
                else:
                    self.progress.emit("Mode lent (pas de FAISS)...")
                    norms = np.linalg.norm(self.manager.embeddings, axis=1, keepdims=True)
                    self.manager._normalized = (self.manager.embeddings / (norms + 1e-8)).astype(np.float32)
            
            self.manager.loaded = True
            count = self.manager.index.ntotal if self.manager.index else len(self.manager.metadata)
            self.finished.emit(count)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))


class EmbeddingManager:
    """
    Gestionnaire d'embeddings avec recherche FAISS optimisée.
    
    Supporte:
    - Index FAISS pré-construit (chargement instantané)
    - Construction automatique de l'index si absent
    - Fallback numpy si FAISS non installé
    """
    
    # Chemins par défaut (10% sample pour tests rapides)
    DEFAULT_SAMPLE_DIR = "perch2"
    DEFAULT_SAMPLE_RATIO = 10  # % 
    
    def __init__(self):
        self.embeddings = None
        self.metadata = None
        self.loaded = False
        self.loader_thread = None
        self.index = None
        self._normalized = None
    
    @classmethod
    def get_sample_paths(cls, sample_ratio=10):
        """
        Retourne les chemins vers les fichiers échantillonnés.
        
        Args:
            sample_ratio: 10 pour 10%, 100 pour données complètes
        """
        base_dir = cls.DEFAULT_SAMPLE_DIR
        
        if sample_ratio >= 100:
            # Données complètes
            return {
                'embeddings': os.path.join(base_dir, "perch_embeddings_FINAL.npy"),
                'metadata': os.path.join(base_dir, "perch_info_FINAL.pkl"),
                'faiss': os.path.join(base_dir, "perch_embeddings_FINAL.faiss")
            }
        else:
            # Données échantillonnées
            suffix = f"_sample{sample_ratio}"
            return {
                'embeddings': os.path.join(base_dir, f"perch_embeddings{suffix}.npy"),
                'metadata': os.path.join(base_dir, f"perch_info{suffix}.pkl"),
                'faiss': os.path.join(base_dir, f"perch_embeddings{suffix}.faiss")
            }
    
    @classmethod
    def find_best_available(cls):
        """
        Trouve automatiquement les meilleurs fichiers disponibles.
        Préfère: 1) sample avec FAISS, 2) FINAL avec FAISS, 3) FINAL sans FAISS
        """
        # Essayer d'abord sample10 (rapide pour tests)
        paths_10 = cls.get_sample_paths(10)
        if os.path.exists(paths_10['faiss']) and os.path.exists(paths_10['metadata']):
            return paths_10, "10% sample"
        
        # Sinon données complètes avec FAISS
        paths_full = cls.get_sample_paths(100)
        if os.path.exists(paths_full['faiss']) and os.path.exists(paths_full['metadata']):
            return paths_full, "100% (FAISS)"
        
        # Sinon données complètes sans FAISS (lent)
        if os.path.exists(paths_full['embeddings']) and os.path.exists(paths_full['metadata']):
            return paths_full, "100% (pas de FAISS)"
        
        return None, None
    
    def _build_faiss_index(self):
        """Construit un index FAISS à partir des embeddings."""
        if self.embeddings is None:
            return
        dim = self.embeddings.shape[1]
        norms = np.linalg.norm(self.embeddings, axis=1, keepdims=True)
        normalized = (self.embeddings / (norms + 1e-8)).astype(np.float32)
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(normalized)
    
    def load_async(self, embeddings_path, metadata_path, on_done, 
                   on_error=None, on_progress=None, faiss_path=None):
        """
        Charge les embeddings de manière asynchrone.
        
        Args:
            embeddings_path: Chemin vers .npy
            metadata_path: Chemin vers .pkl
            on_done: Callback quand terminé
            on_error: Callback en cas d'erreur
            on_progress: Callback pour les messages de progression
            faiss_path: Chemin vers l'index FAISS pré-construit
        """
        # Détecter automatiquement le fichier FAISS si non spécifié
        if faiss_path is None:
            faiss_path = embeddings_path.replace('.npy', '.faiss')
        
        self.loader_thread = EmbeddingLoaderThread(
            embeddings_path, metadata_path, self, faiss_path
        )
        self.loader_thread.finished.connect(on_done)
        if on_error:
            self.loader_thread.error.connect(on_error)
        if on_progress:
            self.loader_thread.progress.connect(on_progress)
        self.loader_thread.start()
    
    def load_best_available(self, on_done, on_error=None, on_progress=None):
        """
        Charge automatiquement les meilleurs fichiers disponibles.
        Préfère les fichiers échantillonnés avec FAISS pré-construit.
        """
        paths, desc = self.find_best_available()
        
        if paths is None:
            if on_error:
                on_error("Aucun fichier d'embeddings trouvé")
            return False
        
        if on_progress:
            on_progress(f"Utilisation: {desc}")
        
        self.load_async(
            paths['embeddings'],
            paths['metadata'],
            on_done,
            on_error,
            on_progress,
            paths['faiss']
        )
        return True
    
    def search(self, query_embedding, top_k=20):
        """
        Recherche les embeddings les plus similaires.
        
        Args:
            query_embedding: Vecteur de requête
            top_k: Nombre de résultats à retourner
            
        Returns:
            Liste de dicts avec 'index', 'similarity', 'metadata'
        """
        if not self.loaded:
            return []
        
        # Normaliser la requête
        query = query_embedding.astype(np.float32)
        query = query / (np.linalg.norm(query) + 1e-8)
        query = query.reshape(1, -1)
        
        # Recherche FAISS (rapide)
        if FAISS_AVAILABLE and self.index is not None:
            similarities, indices = self.index.search(query, top_k)
            results = []
            for i, idx in enumerate(indices[0]):
                if idx >= 0 and idx < len(self.metadata):
                    results.append({
                        'index': int(idx),
                        'similarity': float(similarities[0][i]),
                        'metadata': self.metadata[idx]
                    })
            return results
        
        # Fallback numpy (lent)
        elif self._normalized is not None:
            similarities = np.dot(self._normalized, query.flatten())
            top_indices = np.argpartition(similarities, -top_k)[-top_k:]
            top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]
            results = []
            for idx in top_indices:
                if idx < len(self.metadata):
                    results.append({
                        'index': int(idx),
                        'similarity': float(similarities[idx]),
                        'metadata': self.metadata[idx]
                    })
            return results
        
        return []
    
    def get_embedding(self, index):
        """Retourne l'embedding à l'index donné."""
        if self.embeddings is not None and 0 <= index < len(self.embeddings):
            return self.embeddings[index]
        return None
