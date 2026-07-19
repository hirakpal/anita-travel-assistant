# rag/pinecone_embeddings.py
"""
Shared embedding helper for the RAG modules (youtube_rag, visa_rag,
sim_currency_rag). All three Pinecone indexes were created for the
"llama-text-embed-v2" model (1024 dimensions) — Pinecone's own hosted
inference model, not a local sentence-transformers model. Embedding
locally with a different model (e.g. all-MiniLM-L6-v2, 384 dims) causes
every upsert/query to fail with a dimension mismatch against the index.

Using Pinecone's hosted inference API instead means no local embedding
model to download/run, and the vectors always match the index's actual
dimension.
"""
import os

EMBED_MODEL = "llama-text-embed-v2"

_pc = None


def get_pinecone_client():
    """
    Shared Pinecone client, reused by every RAG module. Each `Pinecone(...)`
    instantiation triggers a slow plugin-discovery scan — creating one per
    module (youtube_rag, visa_rag, sim_currency_rag, this module) instead
    of sharing a single instance was adding tens of seconds per module to
    every request. Construct it once, everywhere.
    """
    global _pc
    if _pc is None:
        from pinecone import Pinecone
        _pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    return _pc


# Backwards-compatible alias for the name used within this module.
_get_client = get_pinecone_client


def embed_texts(texts, input_type="passage"):
    """
    Embed a list of strings via Pinecone's hosted inference model.
    input_type: "passage" when embedding content to store, "query" when
    embedding a search query — Pinecone's model uses this to optimize the
    resulting vector for the right side of the similarity comparison.
    Returns a list of float vectors, one per input text.
    """
    result = _get_client().inference.embed(
        model=EMBED_MODEL,
        inputs=texts,
        parameters={"input_type": input_type},
    )
    return [item["values"] for item in result]
