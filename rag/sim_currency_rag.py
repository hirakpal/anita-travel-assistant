import os
import pinecone
from datetime import datetime
from sentence_transformers import SentenceTransformer

# -------------------------------
# Config
# -------------------------------
PINECONE_ENV = "us-east-1"
PINECONE_INDEX = "sim-currency"
PINECONE_HOST = "https://travis-ai-0ctdsv7.svc.aped-4627-b74a.pinecone.io"

pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=PINECONE_ENV)
index = pinecone.Index(PINECONE_INDEX, host=PINECONE_HOST)

embedder = SentenceTransformer("llama-text-embed-v2")

# -------------------------------
# Filters
# -------------------------------
def _is_valid_entry(entry):
    """Apply freshness filter (≤ 3 months)."""
    updated = entry.get("last_updated")
    if not updated:
        return False
    if (datetime.now() - updated).days > 90:
        return False
    return True

# -------------------------------
# Add SIM/Currency Entries
# -------------------------------
def add_entries(entries, mode="Online"):
    """
    entries: list of dicts with keys:
        country, sim_provider, sim_plan, currency, exchange_rate, fees, availability, source, last_updated
    mode: "Online" or "Demo"
    """
    if mode == "Demo":
        print("🎬 Demo Mode: Skipping Pinecone upsert, returning stub.")
        return [{"demo": f"Stubbed SIM/currency entry for {e['country']}"} for e in entries]

    valid_entries = [e for e in entries if _is_valid_entry(e)]
    if not valid_entries:
        print("⚠️ No valid entries after filtering.")
        return

    texts = [f"{e['country']} {e['sim_provider']} {e['sim_plan']} {e['currency']} {e['exchange_rate']}" for e in valid_entries]
    vectors = embedder.encode(texts, batch_size=8).tolist()

    upserts = []
    for e, vec in zip(valid_entries, vectors):
        upserts.append((
            f"{e['country']}_{e['sim_provider']}_{e['currency']}",
            vec,
            {
                "country": e["country"],
                "sim_provider": e["sim_provider"],
                "sim_plan": e["sim_plan"],
                "currency": e["currency"],
                "exchange_rate": e["exchange_rate"],
                "fees": e["fees"],
                "availability": e["availability"],
                "source": e["source"],
                "last_updated": str(e["last_updated"])
            }
        ))
    index.upsert(upserts)
    print(f"✅ Upserted {len(upserts)} SIM/currency entries into Pinecone.")

# -------------------------------
# Query SIM/Currency
# -------------------------------
def query_entries(country, interests=None, top_k=3, mode="Online"):
    if mode == "Demo":
        return {
            "insights": [
                f"🎬 Demo SIM info: {country} prepaid SIM 10GB/30 days for $20.",
                f"🎬 Demo currency info: Exchange rate 1 USD ≈ 150 {country} currency."
            ]
        }

    query_text = f"{country} travel sim currency {', '.join(interests or [])}"
    query_vector = embedder.encode([query_text])[0].tolist()

    results = index.query(vector=query_vector, top_k=top_k, include_metadata=True)
    return results

# -------------------------------
# Summarization Agent
# -------------------------------
def summarize_results(results, mode="Online"):
    if mode == "Demo":
        return [
            "🎬 Demo summary: SIM 10GB/30 days $20, available at airport kiosks.",
            "🎬 Demo summary: Exchange rate 1 USD ≈ 150 local currency, fee ~2%."
        ]

    insights = []
    for match in results.get("matches", []):
        meta = match.get("metadata", {})
        insights.append(
            f"📱 {meta.get('country')} SIM by {meta.get('sim_provider')} — {meta.get('sim_plan')}, Fee: {meta.get('fees')}, Available: {meta.get('availability')} | "
            f"💱 Currency: {meta.get('currency')} Rate: {meta.get('exchange_rate')}"
        )
    return insights
