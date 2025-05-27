"""Index-building and search utilities."""
from __future__ import annotations

import json
import os
from typing import List

import faiss
import numpy as np
import PyPDF2
from tqdm import tqdm

from .embedding import embed_texts

CHUNK_SIZE = 1000          # characters or ~800 tokens
CHUNK_OVERLAP = 200        # only used when a page is huge


# --------------------------------------------------------------------------- #
# Chunk helpers
# --------------------------------------------------------------------------- #
def _split_by_tokens(text: str, size: int, overlap: int) -> List[str]:
    """
    Split *text* by tokens (preferable). Falls back to char splitting if tiktoken
    isn't available.
    """
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        ids = enc.encode(text)
        out, start = [], 0
        while start < len(ids):
            end = min(len(ids), start + size)
            chunk_txt = enc.decode(ids[start:end]).strip()
            if chunk_txt:
                out.append(chunk_txt)
            start += size - overlap
        return out
    except ModuleNotFoundError:
        # char fallback
        out, start = [], 0
        while start < len(text):
            end = min(len(text), start + size)
            out.append(text[start:end].strip())
            start += size - overlap
        return out


def _chunk_page_text(text: str, page_number: int, size: int = CHUNK_SIZE,
                     overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Chunk a single page into overlapping (token-aware) blocks."""
    text = text.strip()
    if not text:
        return []

    # small page -> single chunk
    if len(text) <= size:
        return [f"Page {page_number}:\n{text}"]

    chunks = _split_by_tokens(text, size, overlap)
    prefixed = [f"Page {page_number} – chunk {i+1}:\n{c}"
                for i, c in enumerate(chunks)]
    return prefixed


# --------------------------------------------------------------------------- #
# Index management
# --------------------------------------------------------------------------- #
def build_index(pdf_path: str, index_name: str, out_dir: str = "vector") -> None:
    """
    Create a FAISS index from *pdf_path* and write it under *out_dir/index_name*.
    """
    out_path = os.path.join(out_dir, index_name)
    os.makedirs(out_path, exist_ok=True)

    print(f"[*] Reading {pdf_path} …")
    reader = PyPDF2.PdfReader(pdf_path)
    chunks: List[str] = []

    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        chunks.extend(_chunk_page_text(page_text, page_number=i + 1))

    print(f"[*] Generating embeddings for {len(chunks)} chunks …")
    embeds = np.stack(embed_texts(chunks)).astype("float32")  # list → ndarray
    faiss.normalize_L2(embeds)
    dim = embeds.shape[1]
    # inner-product == cosine on L2-normed vectors
    index = faiss.IndexFlatIP(dim)
    index.add(embeds)

    # ── Persist ───────────────────────────────────────────
    faiss.write_index(index, os.path.join(out_path, "faiss.index"))
    with open(os.path.join(out_path, "metadata.jsonl"), "w", encoding="utf-8") as fh:
        for idx, chunk in enumerate(chunks):
            meta = {"page": chunk.split(
                ":\n", 1)[0], "chunk_id": idx, "text": chunk}
            fh.write(json.dumps(meta) + "\n")

    print(f"[✓] Index stored in {out_path}")


def load_index(index_name: str, out_dir: str = "vector"):
    idx_path = os.path.join(out_dir, index_name, "faiss.index")
    meta_path = os.path.join(out_dir, index_name, "metadata.jsonl")
    if not (os.path.exists(idx_path) and os.path.exists(meta_path)):
        raise FileNotFoundError(
            f"Index '{index_name}' not found in {out_dir}/")

    index = faiss.read_index(idx_path)
    metadata = [json.loads(l) for l in open(meta_path, encoding="utf-8")]
    return index, metadata


def query_index(index_name: str, question: str, top_k: int = 5):
    """
    Return *top_k* most relevant chunks from *index_name* for *question*.
    """
    from .embedding import embed_texts  # avoid circular import

    index, metadata = load_index(index_name)
    q_vec = embed_texts([question])[0].astype("float32")
    faiss.normalize_L2(q_vec.reshape(1, -1))

    D, I = index.search(np.array([q_vec]), top_k)
    # Filter out any -1 indices (can happen if fewer than top_k docs)
    chunks = []
    for idx in I[0]:
        if idx == -1:
            continue
        chunks.append(metadata[idx]["text"])
    return chunks
