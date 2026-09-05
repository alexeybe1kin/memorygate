"""Embedding access, with an honest answer when no provider is available.

MemoryGate previously shipped an `EMBED_MODEL=hash` mode that derived every
vector component from `sha256(f"{index}:{text}")`. That is a hash of the text,
not a representation of it: near-identical sentences produced uncorrelated
vectors, so cosine similarity over them was noise. Retrieval looked like it
worked and silently returned confident nonsense. It has been removed - see
ADR-0004 in the Conker repository.

There is deliberately no fallback here. When no embedding provider can be
reached this module raises `EmbeddingUnavailable`, and callers degrade to
lexical retrieval *and say so*.
"""

from typing import Any

from app.core.config import EMBED_DIMENSION, EMBED_MODEL

REMOVED_HASH_MODEL = "hash"


class EmbeddingUnavailable(RuntimeError):
    """No embedding provider can produce a vector right now."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


# Either {"model": <model>} once a provider has loaded, or {"reason": <str>}
# once one has failed to. Failures are cached too, so a missing provider does
# not cost an import attempt on every single retrieval.
_provider: dict[str, Any] = {}


def _load_provider() -> dict[str, Any]:
    if _provider:
        return _provider
    if EMBED_MODEL == REMOVED_HASH_MODEL:
        _provider["reason"] = (
            "EMBED_MODEL=hash was removed: it produced vectors with no semantic "
            "meaning. Unset EMBED_MODEL or point it at a real model."
        )
        return _provider
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        _provider["reason"] = f"embedding provider for {EMBED_MODEL!r} is not installed"
        return _provider
    try:
        _provider["model"] = SentenceTransformer(EMBED_MODEL)
    except Exception:
        _provider["reason"] = f"embedding model {EMBED_MODEL!r} could not be loaded"
    return _provider


def get_embedding_model() -> Any:
    """Return the loaded embedding model, or raise `EmbeddingUnavailable`."""
    provider = _load_provider()
    if "model" not in provider:
        raise EmbeddingUnavailable(provider["reason"])
    return provider["model"]


def embed_text(text: str) -> list[float]:
    """Embed one string, or raise `EmbeddingUnavailable`. Never returns noise."""
    model = get_embedding_model()
    vec = model.encode(text, normalize_embeddings=True)
    return [float(x) for x in vec.tolist()]


def embedding_health() -> dict:
    """Coarse provider status for `/health`. Never raises, never guesses."""
    provider = _load_provider()
    if "model" in provider:
        return {"status": "ok", "model": EMBED_MODEL, "dimension": EMBED_DIMENSION}
    return {
        "status": "unavailable",
        "model": EMBED_MODEL,
        "dimension": EMBED_DIMENSION,
        "reason": provider["reason"],
    }


def reset_provider_cache() -> None:
    """Forget a cached provider result, so a test can re-probe after reconfiguring."""
    _provider.clear()
