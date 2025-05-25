# pdfquery

**pdfquery** is a tiny command‑line tool that turns your PDFs into searchable
vector indexes (FAISS) and lets GPT answer questions using only the relevant
passages.

## Quickstart

```bash
# Install locally (editable mode)
pip install -e .

# Build an index (stores files under ./vector/<NAME>/)
pdfquery index --source path/to/file.pdf --name my‑pdf

# Ask a question
pdfquery query --name my‑pdf "What are the main requirements?"
```

Set your OpenAI key first:

```bash
export OPENAI_API_KEY="sk‑..."  # required
```
