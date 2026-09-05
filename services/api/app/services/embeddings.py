import hashlib
import math
from functools import lru_cache
from typing import Any

from app.core.config import EMBED_DIMENSION, EMBED_MODEL


@lru_cache(maxsize=1)
def get_embedding_model() -> Any | None:
    if EMBED_MODEL == "hash":
        return None
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "sentence-transformers is required when EMBED_MODEL is not 'hash'. "
            "Install the optional embedding dependencies or set EMBED_MODEL=hash."
        ) from exc
    return SentenceTransformer(EMBED_MODEL)


def _hash_embed_text(text: str) -> list[float]:
    values = [0.0] * EMBED_DIMENSION
    for index in range(EMBED_DIMENSION):
        digest = hashlib.sha256(f"{index}:{text}".encode("utf-8")).digest()
        raw = int.from_bytes(digest[:8], "big") / float(2**64 - 1)
        values[index] = (raw * 2.0) - 1.0
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]


def embed_text(text: str) -> list[float]:
    model = get_embedding_model()
    if model is None:
        return _hash_embed_text(text)
    vec = model.encode(text, normalize_embeddings=True)
    return [float(x) for x in vec.tolist()]
