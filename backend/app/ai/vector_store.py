import os
import json
import numpy as np
from typing import List, Tuple, Optional
from app.core.config import settings


class FAISSVectorStore:
    def __init__(self, index_dir: str, dim: int = 384):
        self.index_dir = index_dir
        self.dim = dim
        self._candidate_index = None
        self._candidate_ids: List[str] = []
        self._job_index = None
        self._job_ids: List[str] = []

    def _lazy_import(self):
        import faiss
        return faiss

    def _new_index(self):
        faiss = self._lazy_import()
        return faiss.IndexFlatIP(self.dim)

    def load(self):
        faiss = self._lazy_import()
        os.makedirs(self.index_dir, exist_ok=True)

        c_path = os.path.join(self.index_dir, "candidates.index")
        c_ids_path = os.path.join(self.index_dir, "candidate_ids.json")
        if os.path.exists(c_path) and os.path.exists(c_ids_path):
            self._candidate_index = faiss.read_index(c_path)
            with open(c_ids_path) as f:
                self._candidate_ids = json.load(f)
        else:
            self._candidate_index = self._new_index()

        j_path = os.path.join(self.index_dir, "jobs.index")
        j_ids_path = os.path.join(self.index_dir, "job_ids.json")
        if os.path.exists(j_path) and os.path.exists(j_ids_path):
            self._job_index = faiss.read_index(j_path)
            with open(j_ids_path) as f:
                self._job_ids = json.load(f)
        else:
            self._job_index = self._new_index()

    def _save(self, index_type: str):
        faiss = self._lazy_import()
        if index_type == "candidate":
            faiss.write_index(self._candidate_index, os.path.join(self.index_dir, "candidates.index"))
            with open(os.path.join(self.index_dir, "candidate_ids.json"), "w") as f:
                json.dump(self._candidate_ids, f)
        else:
            faiss.write_index(self._job_index, os.path.join(self.index_dir, "jobs.index"))
            with open(os.path.join(self.index_dir, "job_ids.json"), "w") as f:
                json.dump(self._job_ids, f)

    def upsert_candidate(self, candidate_id: str, embedding: np.ndarray):
        if not self._candidate_index:
            self.load()
        vec = embedding.reshape(1, -1).astype(np.float32)
        if candidate_id in self._candidate_ids:
            idx = self._candidate_ids.index(candidate_id)
            # FAISS FlatIP doesn't support update; rebuild for small sets
            # For production, use IndexIDMap
            pass
        self._candidate_index.add(vec)
        self._candidate_ids.append(candidate_id)
        self._save("candidate")

    def upsert_job(self, job_id: str, embedding: np.ndarray):
        if not self._job_index:
            self.load()
        vec = embedding.reshape(1, -1).astype(np.float32)
        self._job_index.add(vec)
        self._job_ids.append(job_id)
        self._save("job")

    def search_candidates(self, query_embedding: np.ndarray, top_k: int = 20) -> List[Tuple[str, float]]:
        if not self._candidate_index or self._candidate_index.ntotal == 0:
            return []
        k = min(top_k, self._candidate_index.ntotal)
        vec = query_embedding.reshape(1, -1).astype(np.float32)
        scores, indices = self._candidate_index.search(vec, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self._candidate_ids):
                results.append((self._candidate_ids[idx], float(score)))
        return results

    def search_jobs(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        if not self._job_index or self._job_index.ntotal == 0:
            return []
        k = min(top_k, self._job_index.ntotal)
        vec = query_embedding.reshape(1, -1).astype(np.float32)
        scores, indices = self._job_index.search(vec, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self._job_ids):
                results.append((self._job_ids[idx], float(score)))
        return results


vector_store = FAISSVectorStore(index_dir=settings.FAISS_INDEX_DIR, dim=settings.EMBEDDING_DIM)
