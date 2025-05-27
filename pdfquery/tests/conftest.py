# tests/conftest.py
"""
Global pytest fixtures for pdfquery tests.

• Replaces PyPDF2.PdfReader so tests never read a real PDF file.
• Mocks embed_texts everywhere to avoid hitting the OpenAI API.
"""

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Fake PDF content
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def fake_pdf_text():
    """Three deterministic pages of text used by all tests."""
    return [
        "Security is top priority.\nWe protect data.",
        "Reliability keeps workloads running.",
        "Cost optimization reduces wastage.",
    ]


# ---------------------------------------------------------------------------
# Patch PyPDF2 so build_index() reads fake pages
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def patch_pypdf2(monkeypatch, fake_pdf_text):
    """Replace PyPDF2.PdfReader with a stub that returns fake pages."""

    class _FakePage:
        def __init__(self, txt):
            self._t = txt

        def extract_text(self):
            return self._t

    class _FakeReader:
        def __init__(self, *_):
            self.pages = [_FakePage(t) for t in fake_pdf_text]

    import PyPDF2

    monkeypatch.setattr(PyPDF2, "PdfReader", _FakeReader)
    return _FakeReader


# ---------------------------------------------------------------------------
# Patch embed_texts in BOTH pdfquery.embedding AND pdfquery.index
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def patch_embed(monkeypatch):
    """
    Monkey-patch embed_texts everywhere so tests run offline
    and produce deterministic 5-dim vectors.
    """

    def _fake_embed(texts, *_, **__):
        # Simple deterministic vector: [i, i, i, i, i]
        return [np.full((5,), i, dtype=np.float32) for i, _ in enumerate(texts)]

    # Patch original module
    monkeypatch.setattr("pdfquery.embedding.embed_texts", _fake_embed, raising=False)
    # Patch alias imported in pdfquery.index (if already imported)
    monkeypatch.setattr("pdfquery.index.embed_texts", _fake_embed, raising=False)

    return _fake_embed
