# utils/prompt_cache.py
"""
Prompt / instruction caching — the agent's "base state".

Each agent's system prompt (HOTEL_PROMPT, FLIGHT_PROMPT, TOUR_PROMPT, ...)
is large and completely static — today the code re-sends that full text on
every single Gemini call. Gemini's cachedContents API lets us upload that
static instruction once and reference it by a short handle on every later
call, instead of paying input-token cost for the same instructions again
on every step.

This module creates/reuses one cached-content handle per (agent, prompt,
model). If the caching API is unavailable for any reason (no API key,
model doesn't support caching, network error), get_cached_system_handle()
returns None and callers fall back to inlining the prompt text directly —
this must never be the thing that breaks an agent call.
"""
import os
import time
import hashlib
import requests

GEMINI_CACHE_URL = "https://generativelanguage.googleapis.com/v1beta/cachedContents"
DEFAULT_TTL_SECONDS = 3600
DEFAULT_MODEL = "models/gemini-1.5-flash-001"

_handles = {}  # prompt_hash -> {"name": str, "expires_at": float}
_hits = 0
_creates = 0
_unavailable = 0


def _prompt_hash(agent_name: str, system_prompt: str, model: str) -> str:
    return hashlib.sha256(f"{agent_name}:{model}:{system_prompt}".encode("utf-8")).hexdigest()


def get_cached_system_handle(agent_name: str, system_prompt: str, model: str = DEFAULT_MODEL, ttl: int = DEFAULT_TTL_SECONDS):
    """
    Return a Gemini cachedContent resource name for this agent's static
    system prompt, creating it once and reusing it until it expires.
    Returns None when caching isn't available — the caller must then send
    the prompt inline as before.
    """
    global _hits, _creates, _unavailable

    key = _prompt_hash(agent_name, system_prompt, model)
    cached = _handles.get(key)
    if cached and cached["expires_at"] > time.time():
        _hits += 1
        return cached["name"]

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        _unavailable += 1
        return None

    try:
        resp = requests.post(
            GEMINI_CACHE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "systemInstruction": {"parts": [{"text": system_prompt}]},
                "ttl": f"{ttl}s",
            },
            timeout=10,
        )
        resp.raise_for_status()
        name = resp.json()["name"]
    except Exception:
        _unavailable += 1
        return None

    _handles[key] = {"name": name, "expires_at": time.time() + ttl}
    _creates += 1
    return name


def build_gemini_request(agent_name: str, system_prompt: str, dynamic_text: str,
                          model: str = DEFAULT_MODEL, ttl: int = DEFAULT_TTL_SECONDS) -> dict:
    """
    Build the Gemini generateContent request body, using a cached-content
    handle for the static system prompt when available so only the
    per-call dynamic text (origin/destination/preferences/...) is billed
    as fresh input tokens. Falls back to inlining the full prompt when
    caching isn't available.
    """
    handle = get_cached_system_handle(agent_name, system_prompt, model=model, ttl=ttl)
    if handle:
        return {
            "cachedContent": handle,
            "contents": [{"parts": [{"text": dynamic_text}]}],
        }
    return {
        "contents": [{"parts": [{"text": f"{system_prompt}\n{dynamic_text}"}]}],
    }


def get_prompt_cache_stats():
    total = _hits + _creates
    return {
        "handle_reuses": _hits,
        "handles_created": _creates,
        "unavailable": _unavailable,
        "reuse_percent": round((_hits / total) * 100, 1) if total else 0.0,
    }


def clear_handles():
    global _hits, _creates, _unavailable
    _handles.clear()
    _hits = _creates = _unavailable = 0
