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

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Break *text* into overlapping chunks so GPT context windows aren't exceeded."""
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end])
        start += size - overlap
    return chunks

# --------------------------------------------------------------------- #
# Index management
# --------------------------------------------------------------------- #
def build_index(pdf_path: str, index_name: str, out_dir: str = "vector") -> None:
    """Create a FAISS index from *pdf_path* and write it under *out_dir/index_name*."""
    out_path = os.path.join(out_dir, index_name)
    os.makedirs(out_path, exist_ok=True)

    print(f"[*] Reading {pdf_path} ...")
    reader = PyPDF2.PdfReader(pdf_path)
    all_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    chunks = _chunk_text(all_text)

    print(f"[*] Generating embeddings for {len(chunks)} chunks ...")
    embeddings = embed_texts(chunks)

    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.stack(embeddings))

    faiss.write_index(index, os.path.join(out_path, "faiss.index"))
    with open(os.path.join(out_path, "metadata.jsonl"), "w", encoding="utf-8") as meta_f:
        for chunk in chunks:
            meta_f.write(json.dumps({"text": chunk}) + "\n")

    print(f"[✓] Index stored in {out_path}")

def load_index(index_name: str, out_dir: str = "vector"):
    index_path = os.path.join(out_dir, index_name, "faiss.index")
    meta_path = os.path.join(out_dir, index_name, "metadata.jsonl")
    if not (os.path.exists(index_path) and os.path.exists(meta_path)):
        raise FileNotFoundError(f"Index '{index_name}' not found in {out_dir}/")
    index = faiss.read_index(index_path)
    metadata = [json.loads(l) for l in open(meta_path, "r", encoding="utf-8")]
    return index, metadata

def query_index(index_name: str, question: str, top_k: int = 5):
    """Return *top_k* most relevant chunks from *index_name* for *question*."""
    from .embedding import embed_texts  # local import to avoid circular deps

    index, metadata = load_index(index_name)
    q_embed = embed_texts([question])[0]
    D, I = index.search(np.array([q_embed]), top_k)
    return [metadata[i]["text"] for i in I[0]]
