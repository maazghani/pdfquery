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
):
    """Create or update an index from *source* PDF under *name*."""
    build_index(source, name)

@app.command("query")
def cmd_query(
    name: str = typer.Option(..., "--name", help="Index name to query."),
    question: str = typer.Argument(..., help="Question to ask about the PDF(s)."),  # noqa: D401
    model: str = typer.Option("gpt-4o", help="OpenAI chat completion model to use."),
    top_k: int = typer.Option(5, help="Number of text chunks to retrieve as context."),
):
    """Ask *question* about the indexed PDF and print GPT's answer."""
    chunks: List[str] = query_index(name, question, top_k=top_k)
    context = "\n---\n".join(chunks)

    system_prompt = (
        "You are a helpful assistant. Answer the user's question ONLY using the provided PDF context.\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        },
    ]

    response = openai.chat.completions.create(model=model, messages=messages)
    answer = response.choices[0].message.content.strip()
    typer.echo(answer)

def main() -> None:  # entry_point
    app()

if __name__ == "__main__":
    main()
