# utils/cache.py
"""
Fragment cache (a.k.a. tool-output cache) — the "inner loop" optimization.

Caches the output of individual tool/API calls (each agent's Gemini or
external-API request) keyed on the exact (service, params) pair, so
calling the same tool with the same arguments again never re-spends
tokens or re-hits the network. This is usually the highest-value cache
in an agent pipeline since the same sub-calls (e.g. "flights BLR->JAI")
repeat often across a session.

For caching further out — the whole agent response for a near-duplicate
user request — see utils/semantic_cache.py. For caching the agent's
static system prompt/instructions, see utils/prompt_cache.py.

Two storage layers:
- In-memory dict  -> fastest, cleared when the process restarts.
- SQLite file      -> persists across restarts so repeated runs of the app
                      (e.g. Streamlit reruns) keep saving tokens.

Hit/miss counters are tracked in-memory for the current process and are
used to report `savings_percent()` — the share of calls that were served
from cache instead of hitting the (token-costing) API.
"""

import hashlib
import json
import os
import sqlite3
import time

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "anita_cache.sqlite3")

_hits = 0
_misses = 0
_memory_cache = {}


def _connect():
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            expires_at REAL
        )
        """
    )
    return conn


def _make_key(service, params) -> str:
    payload = json.dumps({"service": service, "params": params}, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_cached(service, params):
    """Return the cached value for (service, params), or None on a miss."""
    key = _make_key(service, params)
    now = time.time()

    entry = _memory_cache.get(key)
    if entry and (entry["expires_at"] is None or entry["expires_at"] > now):
        return entry["value"]

    conn = _connect()
    try:
        row = conn.execute(
            "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
    finally:
        conn.close()

    if not row:
        return None

    value_json, expires_at = row
    if expires_at is not None and expires_at <= now:
        return None

    value = json.loads(value_json)
    _memory_cache[key] = {"value": value, "expires_at": expires_at}
    return value


def set_cached(service, params, value, ttl=3600):
    """Store `value` for (service, params). ttl in seconds, None = never expires."""
    key = _make_key(service, params)
    expires_at = (time.time() + ttl) if ttl else None

    _memory_cache[key] = {"value": value, "expires_at": expires_at}

    conn = _connect()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
            (key, json.dumps(value, default=str), expires_at),
        )
        conn.commit()
    finally:
        conn.close()


def call_api(service, params, fetch_fn=None, ttl=3600):
    """
    Cache-aware call wrapper.

    service:  short name identifying the API/agent call, e.g. "gemini:hotel"
    params:   dict of request params; identical params → cache hit
    fetch_fn: zero-arg callable that performs the real (token-costing) call.
              If omitted, a deterministic stub response is returned/cached
              (useful for tests/demos with no live API).
    ttl:      seconds to keep the cached result (default 1 hour)
    """
    global _hits, _misses

    cached = get_cached(service, params)
    if cached is not None:
        _hits += 1
        return cached

    _misses += 1
    value = fetch_fn() if fetch_fn else {"service": service, "params": params}
    set_cached(service, params, value, ttl=ttl)
    return value


def get_cache_stats():
    total = _hits + _misses
    return {
        "hits": _hits,
        "misses": _misses,
        "total_calls": total,
        "savings_percent": round((_hits / total) * 100, 1) if total else 0.0,
    }


def savings_percent():
    return get_cache_stats()["savings_percent"]


def reset_cache_stats():
    """Reset in-memory hit/miss counters (does not clear cached entries)."""
    global _hits, _misses
    _hits = 0
    _misses = 0


def clear_cache():
    """Wipe all cached entries (memory + SQLite). Mainly for tests."""
    _memory_cache.clear()
    conn = _connect()
    try:
        conn.execute("DELETE FROM cache")
        conn.commit()
    finally:
        conn.close()
