# ─────────────── Stage 1 — build ──────────────────────────────────────────────
FROM python:3.11-slim AS build

WORKDIR /app

# System deps for wheels that need compilation (faiss-cpu, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy source code
COPY . /app

# Install package and strip pip cache
RUN pip install --upgrade pip && \
    pip install . && \
    rm -rf /root/.cache/pip

# ─────────────── Stage 2 — runtime image ──────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy just the installed site-packages & entrypoint from stage-1
COPY --from=build /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=build /usr/local/bin/pdfquery /usr/local/bin/pdfquery

# Default command shows the CLI help
ENTRYPOINT ["pdfquery"]
CMD ["--help"]