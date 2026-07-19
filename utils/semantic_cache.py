# utils/semantic_cache.py
"""
Semantic cache for the outer layer — where a full user request arrives
(ANITA.orchestrate). Unlike the exact-match fragment cache in cache.py,
this matches requests that are semantically similar even when the wording
differs slightly (e.g. "vegetarian food" vs "veg options"), so the entire
multi-agent pipeline can be skipped for near-duplicate trips.

Uses sentence-transformers embeddings + cosine similarity when available;
falls back to a lightweight text-similarity heuristic (difflib) so the
cache still works without that (heavy) dependency installed.
"""
import difflib
import time

_embedder = None  # None = not tried yet, False = unavailable, else the model
_entries = []  # [{"text":, "embedding":, "value":, "expires_at":}]

_hits = 0
_misses = 0


def _get_embedder():
    global _embedder
    if _embedder is False:
        return None
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            _embedder = False
            return None
    return _embedder


def _embed(text):
    embedder = _get_embedder()
    if embedder is None:
        return None
    return embedder.encode([text])[0]


def _cosine(a, b):
    import numpy as np
    a, b = np.asarray(a), np.asarray(b)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom else 0.0


def _similarity(text_a, embedding_a, text_b, embedding_b):
    if embedding_a is not None and embedding_b is not None:
        return _cosine(embedding_a, embedding_b)
    # Fallback when sentence-transformers isn't installed
    return difflib.SequenceMatcher(None, text_a, text_b).ratio()


def semantic_call(query_text, fetch_fn, threshold=0.92, ttl=3600):
    """
    Return a cached result for a semantically similar prior query_text,
    or run fetch_fn() and cache it under this query_text.
    """
    global _hits, _misses
    now = time.time()
    query_embedding = _embed(query_text)

    best_score, best_entry = 0.0, None
    for entry in _entries:
        if entry["expires_at"] is not None and entry["expires_at"] <= now:
            continue
        score = _similarity(query_text, query_embedding, entry["text"], entry["embedding"])
        if score > best_score:
            best_score, best_entry = score, entry

    if best_entry is not None and best_score >= threshold:
        _hits += 1
        return best_entry["value"]

    _misses += 1
    value = fetch_fn()
    _entries.append({
        "text": query_text,
        "embedding": query_embedding,
        "value": value,
        "expires_at": (now + ttl) if ttl else None,
    })
    return value


def get_semantic_cache_stats():
    total = _hits + _misses
    return {
        "hits": _hits,
        "misses": _misses,
        "total_calls": total,
        "savings_percent": round((_hits / total) * 100, 1) if total else 0.0,
    }


def reset_semantic_cache():
    global _hits, _misses
    _hits = 0
    _misses = 0
    _entries.clear()
