from pdfquery.index import _chunk_page_text


def test_basic_page_chunking():
    text = "A" * 500  # shorter than CHUNK_SIZE (1 000)
    chunks = _chunk_page_text(text, page_number=1)
    assert len(chunks) == 1
    assert chunks[0].startswith("Page 1")


def test_long_page_gets_split():
    text = "B" * 1500  # longer than CHUNK_SIZE
    chunks = _chunk_page_text(text, page_number=2, size=1000, overlap=200)
    # Expect 2 chunks with overlap
    assert len(chunks) == 2
    assert chunks[0].startswith("Page 2 – chunk 1")
    assert chunks[1].startswith("Page 2 – chunk 2")
