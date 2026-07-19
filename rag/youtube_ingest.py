# rag/youtube_ingest.py
"""
Populates the "youtube-travel-blogs" Pinecone index with real travel-vlog
content for a destination, so youtube_rag.query_videos() has something
real to find instead of an empty index.

Uses SearchAPI.io (https://www.searchapi.io) — its `youtube` engine finds
relevant videos, its `youtube_transcripts` engine pulls the actual spoken
content, which we then hand to youtube_rag.add_videos_to_index() to embed
and upsert. Every network call here is best-effort: any failure just means
fewer (or zero) videos get indexed, never a crash.
"""
import os
import requests
from datetime import datetime, timedelta

SEARCHAPI_URL = "https://www.searchapi.io/api/v1/search"
MIN_TRANSCRIPT_CHARS = 200
MAX_TRANSCRIPT_CHARS = 4000


def _search_videos(query, num=8):
    api_key = os.getenv("SEARCHAPI_KEY")
    if not api_key:
        return []
    try:
        resp = requests.get(SEARCHAPI_URL, params={
            "engine": "youtube",
            "q": query,
            "api_key": api_key,
        }, timeout=15)
        resp.raise_for_status()
        return (resp.json().get("videos") or [])[:num]
    except Exception as e:
        print(f"⚠️ YouTube search error: {e!r}")
        return []


def _fetch_transcript(video_id):
    api_key = os.getenv("SEARCHAPI_KEY")
    if not api_key:
        return ""
    try:
        resp = requests.get(SEARCHAPI_URL, params={
            "engine": "youtube_transcripts",
            "video_id": video_id,
            "api_key": api_key,
        }, timeout=15)
        resp.raise_for_status()
        segments = resp.json().get("transcripts") or []
        return " ".join(seg.get("text", "") for seg in segments)
    except Exception as e:
        print(f"⚠️ Transcript fetch error for video {video_id}: {e!r}")
        return ""


def ingest_destination_videos(destination, num_videos=5):
    """
    Search for real travel videos about `destination`, pull their
    transcripts, and upsert them into the youtube-travel-blogs index.
    Returns how many videos were actually indexed (0 if SEARCHAPI_KEY is
    missing, nothing relevant was found, or every call failed).
    """
    from rag.youtube_rag import add_videos_to_index

    if not os.getenv("SEARCHAPI_KEY"):
        return 0

    search_results = _search_videos(f"{destination} travel guide things to do")

    videos = []
    for v in search_results:
        video_id = v.get("id")
        if not video_id:
            continue

        transcript = _fetch_transcript(video_id)
        if len(transcript) < MIN_TRANSCRIPT_CHARS:
            continue  # no usable spoken content (captions disabled, etc.)

        channel = v.get("channel") or {}
        views = v.get("views")
        if not isinstance(views, int):
            views = 100000  # assume reputable if the API didn't give a count

        videos.append({
            "video_id": video_id,
            "title": v.get("title", ""),
            "description": v.get("description", ""),
            "transcript": transcript[:MAX_TRANSCRIPT_CHARS],
            "views": views,
            "upload_date": datetime.now() - timedelta(days=30),  # API gives relative text, not a real date
            "destination": destination,
            "tags": ["travel", destination],
            "creator": channel.get("title", "Unknown"),
        })
        if len(videos) >= num_videos:
            break

    if not videos:
        return 0

    add_videos_to_index(videos, mode="Online")
    return len(videos)
