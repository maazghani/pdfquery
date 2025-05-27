# pdfquery

**pdfquery** is a command‑line tool that turns your PDFs into searchable
vector indices (FAISS) and lets GPT answer questions using only the relevant
passages.

Use the instructions below or use the Makefile:

| Command        | Description                                      |
|----------------|--------------------------------------------------|
| `make venv`         | Create virtual environment (`.venv`)             |
| `make install`      | Install `pdfquery` in editable mode + dev deps   |
| `make test`         | Run `pytest`                                     |
| `make lint`         | Run `ruff` linting                               |
| `make format`       | Run `black` code formatter                       |
| `make docker-build` | Build local Docker image (`pdfquery:latest`)     |
| `make clean`        | Remove caches, build artifacts, and `.venv`      |

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

## Docker instructions

```bash
# build the image
docker build -t pdfquery:latest .

# run
docker run --rm pdfquery:latest

# example: index a PDF inside the container
docker run -e OPENAI_API_KEY=${OPENAI_API_KEY} --rm -v $PWD:/data pdfquery:latest \
       index --source /data/my.pdf --name mydoc
```
