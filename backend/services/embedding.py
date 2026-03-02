"""
services/embedding.py — Sentence embedding + FAISS vector store.

The SentenceTransformer model is loaded ONCE at app startup and reused.
Each analysis gets its own ephemeral FAISS index (in-memory, not persisted).

Also handles idea deduplication: if a new idea embeds within 0.92 cosine
similarity of an existing cached idea, we return the cached analysis.
"""
import numpy as np
import structlog

log = structlog.get_logger(__name__)

# Global model instance — loaded once in lifespan, never reloaded
_model = None


def load_model(model_name: str = "all-MiniLM-L6-v2") -> None:
    """Call this once during app startup inside the lifespan handler."""
    global _model
    from sentence_transformers import SentenceTransformer
    log.info("embedding.loading_model", model=model_name)
    _model = SentenceTransformer(model_name)
    log.info("embedding.model_ready")


def get_model():
    if _model is None:
        raise RuntimeError("Embedding model not loaded. Call load_model() at startup.")
    return _model


def embed(text: str) -> list[float]:
    """Embed a single string. Returns a plain Python float list for JSON storage."""
    model = get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()


def embed_batch(texts: list[str]) -> np.ndarray:
    """Embed multiple strings. Returns (N, D) float32 ndarray."""
    model = get_model()
    return model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two already-normalised vectors."""
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    return float(np.dot(va, vb))  # works because both are L2-normalised


# ── Per-analysis ephemeral FAISS index ────────────────────────────────────────

class EphemeralIndex:
    """
    Lightweight FAISS flat index scoped to a single analysis run.
    Stores search snippet embeddings so agents can do semantic retrieval
    on the collected search results without a persistent vector DB.
    """

    def __init__(self):
        self._dim: int | None = None
        self._index = None
        self._texts: list[str] = []
        self._vectors: np.ndarray | None = None
        self._faiss = None

        # faiss-cpu 1.8.0 wheels are compiled against NumPy 1.x.
        # If NumPy 2.x is present, skip FAISS and use a safe numpy fallback.
        numpy_major = int(np.__version__.split(".", 1)[0])
        if numpy_major >= 2:
            log.warning("embedding.faiss_disabled_numpy2", numpy_version=np.__version__)
            return

        try:
            import faiss
            self._faiss = faiss
        except Exception as exc:  # pragma: no cover - env-dependent import failure
            log.warning("embedding.faiss_unavailable", error=str(exc))

    def add(self, texts: list[str]) -> None:
        """Embed and index a list of text snippets."""
        if not texts:
            return

        vecs = embed_batch(texts).astype(np.float32)

        if self._faiss is not None:
            if self._index is None:
                self._dim = vecs.shape[1]
                self._index = self._faiss.IndexFlatIP(self._dim)   # cosine on normalised vecs

            self._index.add(vecs)
        else:
            if self._vectors is None:
                self._vectors = vecs
            else:
                self._vectors = np.vstack((self._vectors, vecs))

        self._texts.extend(texts)

    def query(self, query_text: str, top_k: int = 8) -> list[str]:
        """Return the top-k most relevant snippets for the query."""
        if not self._texts:
            return []

        if self._faiss is not None and self._index is not None and self._index.ntotal > 0:
            q_vec = np.array([embed(query_text)], dtype=np.float32)
            k = min(top_k, self._index.ntotal)
            _, indices = self._index.search(q_vec, k)
            return [self._texts[i] for i in indices[0] if i >= 0]

        if self._vectors is None or self._vectors.shape[0] == 0:
            return []

        q_vec = np.array(embed(query_text), dtype=np.float32)
        sims = self._vectors @ q_vec
        k = min(top_k, sims.shape[0])
        top_indices = np.argsort(-sims)[:k]
        return [self._texts[int(i)] for i in top_indices]
