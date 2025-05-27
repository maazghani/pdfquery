"""Index-building and search utilities."""

from __future__ import annotations

import json
import os
from typing import List

import faiss
import numpy as np
import PyPDF2
from tqdm import tqdm

# NOTE: we import embed_texts lazily so tests can monkey-patch it
CHUNK_SIZE = 1000  # ≈ 800 tokens
CHUNK_OVERLAP = 200


# ──────────────────────────── Chunking helpers ──────────────────────────────
def _split_by_tokens(text: str, size: int, overlap: int) -> List[str]:
    """Token-aware splitter; falls back to char split if tiktoken unavailable."""
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
        out, start = [], 0
        while start < len(text):
            end = min(len(text), start + size)
            out.append(text[start:end].strip())
            start += size - overlap
        return out


def _chunk_page_text(
    text: str, page_number: int, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> List[str]:
    text = text.strip()
    if not text:
        return []

    # small page → single chunk
    if len(text) <= size:
        return [f"Page {page_number}:\n{text}"]

    chunks = _split_by_tokens(text, size, overlap)
    return [f"Page {page_number} – chunk {i + 1}:\n{c}" for i, c in enumerate(chunks)]


# ───────────────────────────── Index builders ───────────────────────────────
def build_index(pdf_path: str, index_name: str, out_dir: str = "vector") -> None:
    """Create FAISS index from *pdf_path* and store under *out_dir/index_name*."""
    out_path = os.path.join(out_dir, index_name)
    os.makedirs(out_path, exist_ok=True)

    print(f"[*] Reading {pdf_path} …")
    reader = PyPDF2.PdfReader(pdf_path)
    chunks: List[str] = []

    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        chunks.extend(_chunk_page_text(page_text, page_number=i + 1))

    print(f"[*] Generating embeddings for {len(chunks)} chunks …")
    from .embedding import embed_texts  # local import for test monkey-patching

    embeds = np.stack(embed_texts(chunks)).astype("float32")

    # L2-normalize for cosine similarity & use inner-product index
    faiss.normalize_L2(embeds)
    dim = embeds.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeds)

    faiss.write_index(index, os.path.join(out_path, "faiss.index"))
    with open(os.path.join(out_path, "metadata.jsonl"), "w", encoding="utf-8") as fh:
        for idx, chunk in enumerate(chunks):
            meta = {
                "page": chunk.split(":\n", 1)[0],
                "chunk_id": idx,
                "text": chunk,
            }
            fh.write(json.dumps(meta) + "\n")

    print(f"[✓] Index stored in {out_path}")


def load_index(index_name: str, out_dir: str = "vector"):
    idx_path = os.path.join(out_dir, index_name, "faiss.index")
    meta_path = os.path.join(out_dir, index_name, "metadata.jsonl")
    if not (os.path.exists(idx_path) and os.path.exists(meta_path)):
        raise FileNotFoundError(f"Index '{index_name}' not found in {out_dir}/")
    index = faiss.read_index(idx_path)
    metadata = [json.loads(l) for l in open(meta_path, encoding="utf-8")]
    return index, metadata


def query_index(
    index_name: str, question: str, top_k: int = 5, out_dir: str = "vector"
) -> List[str]:
    """Return *top_k* most relevant chunks as plain strings."""
    from .embedding import embed_texts  # local import to allow monkey-patching

    index, metadata = load_index(index_name, out_dir=out_dir)
    q_vec = embed_texts([question])[0].astype("float32")
    faiss.normalize_L2(q_vec.reshape(1, -1))

    D, I = index.search(np.array([q_vec]), top_k)

    chunks = []
    for idx in I[0]:
        if idx == -1:
            continue
        chunks.append(metadata[idx]["text"])
    return chunks
