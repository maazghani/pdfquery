# tests/test_query_index.py
from pdfquery.index import build_index, query_index


def test_query_retrieves_expected_pages(tmp_path):
    out_dir = tmp_path / "vector"
    build_index("dummy.pdf", index_name="aws", out_dir=out_dir.as_posix())

    chunks = query_index(
        "aws",
        "Does it discuss security?",
        top_k=3,
        out_dir=out_dir.as_posix(),
    )

    # Fake first page contains the word "Security"
    assert any("Security" in c for c in chunks)
