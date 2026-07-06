#!/usr/bin/env python3
"""Embed knowledge base policies into ChromaDB."""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.retriever.vector_store import get_vector_store
from app.utils.logger import setup_logging

app = typer.Typer(help="Embed knowledge base into ChromaDB")
console = Console()


@app.command()
def embed(
    clear: bool = typer.Option(False, "--clear", help="Clear existing embeddings first"),
) -> None:
    """Ingest all policy and FAQ documents into ChromaDB."""
    setup_logging()
    vector_store = get_vector_store()

    if clear:
        console.print("[yellow]Clearing existing embeddings...[/yellow]")
        vector_store.clear()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Embedding knowledge documents...", total=None)
        count = vector_store.ingest_policies()

    console.print(f"[green]Successfully embedded {count} documents[/green]")
    console.print(f"Vector store count: {vector_store.document_count}")


if __name__ == "__main__":
    app()
