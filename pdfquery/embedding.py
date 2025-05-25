"""Utility for creating OpenAI text embeddings."""
import numpy as np
import openai

EMBED_MODEL = "text-embedding-3-small"

def embed_texts(texts, model: str = EMBED_MODEL, batch_size: int = 1000):
    """Return a list of np.float32 embeddings for *texts*."""
    embeddings = []
    for i in range(0, len(texts), batch_size):
        resp = openai.embeddings.create(model=model, input=texts[i : i + batch_size])

        # NEW: use `.embedding` attribute instead of ["embedding"]
        batch_embeds = [
            np.array(e.embedding, dtype=np.float32) for e in resp.data
        ]
        embeddings.extend(batch_embeds)

    return embeddings
