"""pdfquery CLI implemented with Typer."""

from __future__ import annotations

import os
from typing import List

import openai
import typer

from .index import build_index, query_index

app = typer.Typer(add_help_option=True, rich_markup_mode="rich")

# ------------------------------------------------------------------ #
# Commands
# ------------------------------------------------------------------ #


@app.command("index")
def cmd_index(
    source: str = typer.Option(..., "--source", help="Path to the PDF file to index."),
    name: str = typer.Option(..., "--name", help="Index name (used for storage)."),
    key: str = typer.Option(None, "--key", help="OpenAI API key (optional)"),
):
    """Create or update an index from *source* PDF under *name*."""
    if key:
        os.environ["OPENAI_API_KEY"] = key
    build_index(source, name)


@app.command("query")
def cmd_query(
    name: str = typer.Option(..., "--name", help="Index name to query."),
    question: str = typer.Argument(..., help="Question to ask about the PDF(s)."),
    model: str = typer.Option(
        "gpt-4o-mini", help="OpenAI chat completion model to use."
    ),
    top_k: int = typer.Option(5, help="Number of text chunks to retrieve as context."),
    key: str = typer.Option(None, "--key", help="OpenAI API key (optional)"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print retrieved chunks without calling GPT."
    ),
):
    """Ask *question* about the indexed PDF and optionally run GPT on the context."""
    if key:
        os.environ["OPENAI_API_KEY"] = key

    chunks: List[str] = query_index(name, question, top_k=top_k)

    if dry_run:
        for i, c in enumerate(chunks, 1):
            print(f"\n--- Chunk {i} ---\n{c.strip()}")
        return

    context = "\n---\n".join(chunks)

    system_prompt = "You are a helpful assistant. Answer the user's question ONLY using the provided PDF context.\n"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]

    response = openai.chat.completions.create(model=model, messages=messages)
    answer_text = response.choices[0].message.content.strip()
    typer.echo(answer_text)


def main() -> None:  # entry_point
    app()


if __name__ == "__main__":
    main()
