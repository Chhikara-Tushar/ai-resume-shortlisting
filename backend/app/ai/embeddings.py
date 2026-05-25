import numpy as np
from typing import List, Union
from functools import lru_cache
from app.core.config import settings


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings.HF_MODEL_NAME)


def embed_text(text: str) -> np.ndarray:
    model = _get_model()
    embedding = model.encode([text[:8192]], normalize_embeddings=True, show_progress_bar=False)
    return embedding[0].astype(np.float32)


def embed_batch(texts: List[str]) -> np.ndarray:
    model = _get_model()
    truncated = [t[:8192] for t in texts]
    embeddings = model.encode(truncated, normalize_embeddings=True, show_progress_bar=False, batch_size=32)
    return embeddings.astype(np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a_norm = a / (np.linalg.norm(a) + 1e-10)
    b_norm = b / (np.linalg.norm(b) + 1e-10)
    return float(np.dot(a_norm, b_norm))
