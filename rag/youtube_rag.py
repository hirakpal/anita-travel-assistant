#rag/youtube_rag.py
from datetime import datetime
from rag.pinecone_embeddings import embed_texts, get_pinecone_client

# -------------------------------
# Config
# -------------------------------
PINECONE_INDEX = "youtube-travel-blogs"
PINECONE_HOST = "https://travis-ai-0ctdsv7.svc.aped-4627-b74a.pinecone.io"

_index = None


def _get_index():
    """Lazily connect to Pinecone (via the shared client) so Demo mode never needs credentials/network."""
    global _index
    if _index is None:
        _index = get_pinecone_client().Index(PINECONE_INDEX, host=PINECONE_HOST)
    return _index

# -------------------------------
# Filters
# -------------------------------
def _is_valid_video(video):
    """Apply freshness + popularity filters."""
    if video.get("views", 0) < 1000:
        return False
    upload_date = video.get("upload_date")
    if not upload_date:
        return False
    if (datetime.now() - upload_date).days > 180:
        return False
    return True

# -------------------------------
# Add Videos (Batch)
# -------------------------------
def add_videos_to_index(videos, mode="Online"):
    """
    videos: list of dicts with keys:
        video_id, title, description, transcript, views, upload_date, destination, tags, creator
    mode: "Online" or "Demo"
    """
    if mode == "Demo":
        print("🎬 Demo Mode: Skipping Pinecone upsert, returning stub.")
        return [{"demo": f"Stubbed video for {v['destination']}"} for v in videos]

    valid_videos = [v for v in videos if _is_valid_video(v)]
    if not valid_videos:
        print("⚠️ No valid videos after filtering.")
        return

    # Batch text for embeddings
    texts = [
        f"{v['title']} {v['description']} {v.get('transcript','')}"
        for v in valid_videos
    ]
    vectors = embed_texts(texts, input_type="passage")

    # Upsert into Pinecone
    upserts = []
    for v, vec in zip(valid_videos, vectors):
        upserts.append((
            v["video_id"],
            vec,
            {
                "title": v["title"],
                "description": v["description"],
                "destination": v["destination"],
                "tags": v.get("tags", []),
                "creator": v["creator"],
                "views": v["views"],
                "upload_date": str(v["upload_date"]),
                # Full-ish transcript excerpt (well under Pinecone's 40KB
                # metadata cap) so a downstream Gemini call has enough real
                # spoken content to synthesize an actual summary from,
                # instead of just the first sentence or two.
                "transcript_excerpt": (v.get("transcript") or "")[:2500],
            }
        ))
    _get_index().upsert(upserts)
    print(f"✅ Upserted {len(upserts)} videos into Pinecone.")

# -------------------------------
# Query RAG
# -------------------------------
def query_videos(destination, interests, top_k=5, mode="Online"):
    """
    Query Pinecone for relevant travel vlogs.
    destination: str (e.g., "Rome")
    interests: list of str (e.g., ["food", "culture"])
    mode: "Online" or "Demo"
    """
    if mode == "Demo":
        return {
            "insights": [
                f"🎥 Demo vlog: {destination} street food highlights",
                f"🎥 Demo vlog: {destination} cultural walking tour"
            ]
        }

    query_text = f"{destination} travel {', '.join(interests)}"
    query_vector = embed_texts([query_text], input_type="query")[0]

    results = _get_index().query(vector=query_vector, top_k=top_k, include_metadata=True)
    return results

# -------------------------------
# Raw matches (for cross-video synthesis, e.g. the Guide tab's summary)
# -------------------------------
def get_video_transcripts(destination, top_k=8, mode="Online"):
    """
    Return the raw {title, creator, excerpt} for the top indexed videos on
    this destination, so a caller can synthesize ONE combined summary
    across all of them (rather than listing each video's snippet
    separately, which just reads like disconnected quotes).
    """
    if mode == "Demo":
        return [
            {"title": f"Demo: {destination} highlights reel", "creator": "Demo Creator",
             "excerpt": f"Demo transcript excerpt covering {destination}'s top sights and food."}
        ]

    query_text = f"{destination} travel guide things to do highlights culture food tips"
    query_vector = embed_texts([query_text], input_type="query")[0]
    results = _get_index().query(vector=query_vector, top_k=top_k, include_metadata=True)

    videos = []
    for match in results.get("matches", []):
        meta = match.get("metadata", {})
        excerpt = (meta.get("transcript_excerpt") or "").strip()
        if not excerpt:
            continue
        videos.append({
            "title": meta.get("title", ""),
            "creator": meta.get("creator", ""),
            "excerpt": excerpt,
        })
    return videos

# -------------------------------
# Summarization Agent
# -------------------------------
def summarize_results(results, mode="Online"):
    """
    Summarize retrieved vlog metadata into user-friendly insights.
    """
    if mode == "Demo":
        return [
            "🎥 Demo vlog: Rome pasta tour — highlights authentic trattorias",
            "🎥 Demo vlog: Paris night walk — Eiffel Tower lighting show"
        ]

    insights = []
    for match in results.get("matches", []):
        meta = match.get("metadata", {})
        excerpt = (meta.get("transcript_excerpt") or "").strip()
        line = f"🎥 **{meta.get('title')}** ({meta.get('creator')})"
        if excerpt:
            # Trim to a clean sentence-ish boundary so it doesn't cut off mid-word
            snippet = excerpt[:220].rsplit(" ", 1)[0]
            line += f": “{snippet}...”"
        insights.append(line)
    return insights
