# ──────────────────────────────── VARIABLES ──────────────────────────────── #
PYTHON        ?= python3
VENV_DIR      ?= .venv
PIP           := $(VENV_DIR)/bin/pip
PYTHON_BIN    := $(VENV_DIR)/bin/python
ACTIVATE      := source $(VENV_DIR)/bin/activate

IMAGE_NAME    ?= pdfquery:latest

# Extras to install dev tooling declared in pyproject.toml [project.optional-dependencies.dev]
DEV_EXTRAS    := .[dev]

# Ensure bash for nicer scripts
SHELL := /usr/bin/env bash

# ──────────────────────────────── TARGETS ───────────────────────────────── #
.PHONY: help venv install test lint format docker-build clean

help:
	@echo "Makefile targets:"
	@echo "  venv           ─ Create virtual environment ($(VENV_DIR))"
	@echo "  install        ─ Install pdfquery in editable mode + dev deps"
	@echo "  test           ─ Run pytest"
	@echo "  lint           ─ Run ruff linting"
	@echo "  format         ─ Run black code formatter"
	@echo "  docker-build   ─ Build local Docker image ($(IMAGE_NAME))"
	@echo "  clean          ─ Remove caches, build artifacts, venv"

# ---------- Setup ----------
venv: $(VENV_DIR)/bin/activate
$(VENV_DIR)/bin/activate: pyproject.toml
	@echo "📦 Creating venv in $(VENV_DIR)"
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "✅ Virtual env ready."

install: venv
	@echo "🔧 Installing package + dev extras"
	$(PIP) install --upgrade pip
	$(PIP) install -e $(DEV_EXTRAS)
	@echo "✅ Install complete."

# ---------- Quality ----------
test: venv
	@$(ACTIVATE); \
	echo "🧪 Running tests…"; \
	pytest -q

lint: venv
	@$(ACTIVATE); \
	$(PIP) install ruff
	echo "🔍 Linting with ruff…"; \
	ruff check .

format: venv
	@$(ACTIVATE); \
	echo "🎨 Formatting with black…"; \
	black .

# ---------- Docker ----------
docker-build:
	@echo "🐳 Building Docker image $(IMAGE_NAME)…"
	docker build -t $(IMAGE_NAME) .

# ---------- Clean ----------
clean:
	@echo "🧹 Cleaning caches & artifacts"
	rm -rf $(VENV_DIR) .pytest_cache .mypy_cache __pycache__ build dist *.egg-info vector
