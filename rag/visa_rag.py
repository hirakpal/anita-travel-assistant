#rag/visa_rag.py
from datetime import datetime
from rag.pinecone_embeddings import embed_texts, get_pinecone_client

# -------------------------------
# Config
# -------------------------------
PINECONE_INDEX = "visa-requirements"
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
def _is_valid_entry(entry):
    """Apply freshness filter (≤ 12 months)."""
    updated = entry.get("last_updated")
    if not updated:
        return False
    if (datetime.now() - updated).days > 365:
        return False
    return True

# -------------------------------
# Add Visa Requirements
# -------------------------------
def add_requirements(entries, mode="Online"):
    """
    entries: list of dicts with keys:
        country, visa_type, requirements, duration, documents, fees, processing, source, last_updated
    mode: "Online" or "Demo"
    """
    if mode == "Demo":
        print("🎬 Demo Mode: Skipping Pinecone upsert, returning stub.")
        return [{"demo": f"Stubbed visa entry for {e['country']}"} for e in entries]

    valid_entries = [e for e in entries if _is_valid_entry(e)]
    if not valid_entries:
        print("⚠️ No valid entries after filtering.")
        return

    texts = [f"{e['country']} {e['visa_type']} {e['requirements']}" for e in valid_entries]
    vectors = embed_texts(texts, input_type="passage")

    upserts = []
    for e, vec in zip(valid_entries, vectors):
        upserts.append((
            f"{e['country']}_{e['visa_type']}",
            vec,
            {
                "country": e["country"],
                "visa_type": e["visa_type"],
                "requirements": e["requirements"],
                "duration": e["duration"],
                "documents": e.get("documents", []),
                "fees": e["fees"],
                "processing": e["processing"],
                "source": e["source"],
                "last_updated": str(e["last_updated"])
            }
        ))
    _get_index().upsert(upserts)
    print(f"✅ Upserted {len(upserts)} visa entries into Pinecone.")

# -------------------------------
# Query Visa Requirements
# -------------------------------
def query_requirements(country, visa_type="tourist", top_k=3, mode="Online"):
    if mode == "Demo":
        return {
            "insights": [
                f"🎬 Demo visa info: {country} {visa_type} visa valid 30 days.",
                f"🎬 Demo visa info: Requires passport + proof of funds."
            ]
        }

    query_text = f"{country} {visa_type} visa requirements"
    query_vector = embed_texts([query_text], input_type="query")[0]

    results = _get_index().query(vector=query_vector, top_k=top_k, include_metadata=True)
    return results

# -------------------------------
# Summarization Agent
# -------------------------------
def summarize_results(results, mode="Online"):
    if mode == "Demo":
        return [
            "🎬 Demo summary: Tourist visa valid 30 days, fee $50.",
            "🎬 Demo summary: Documents required — passport, photos, proof of funds."
        ]

    insights = []
    for match in results.get("matches", []):
        meta = match.get("metadata", {})
        insights.append(
            f"🛂 {meta.get('country')} {meta.get('visa_type')} visa — "
            f"Duration: {meta.get('duration')}, Fee: {meta.get('fees')}, "
            f"Processing: {meta.get('processing')}, Docs: {meta.get('documents')}"
        )
    return insights
