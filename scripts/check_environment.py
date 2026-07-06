#!/usr/bin/env python3
"""Verify Python environment, dependencies, and optional runtime resources."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def check(name: str, ok: bool, detail: str = "") -> bool:
    status = "OK" if ok else "FAIL"
    msg = f"[{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    return ok


def main() -> int:
    print("=== AI Email Intelligence — Environment Check ===\n")
    all_ok = True

    py_ok = sys.version_info >= (3, 12)
    all_ok &= check("Python >= 3.12", py_ok, sys.version.split()[0])

    packages = [
        "fastapi",
        "uvicorn",
        "langgraph",
        "langchain_core",
        "langchain_anthropic",
        "anthropic",
        "chromadb",
        "sentence_transformers",
        "torch",
        "numpy",
        "bert_score",
        "rapidfuzz",
        "httpx",
        "pydantic",
        "pydantic_settings",
        "sqlalchemy",
        "psycopg2",
        "jwt",
        "typer",
        "rich",
        "orjson",
    ]
    print("\n--- Installed packages ---")
    for pkg in packages:
        try:
            importlib.import_module(pkg)
            all_ok &= check(pkg, True)
        except ImportError as exc:
            all_ok &= check(pkg, False, str(exc))

    print("\n--- Application import ---")
    try:
        from app.main import app  # noqa: F401

        all_ok &= check("app.main:app", True)
    except Exception as exc:
        all_ok &= check("app.main:app", False, str(exc))

    print("\n--- Configuration ---")
    try:
        from app.config import get_settings

        settings = get_settings()
        all_ok &= check("ANTHROPIC_API_KEY", bool(settings.anthropic_api_key), "optional")
        all_ok &= check("GEMINI/GOOGLE API key", bool(settings.effective_gemini_key), "optional")
        all_ok &= check("DATABASE_URL", bool(settings.database_url), "optional — file fallback")
        all_ok &= check("CLERK_SECRET_KEY", bool(settings.clerk_secret_key), "optional")
        all_ok &= check("CLERK_JWKS_URL", bool(settings.clerk_jwks_url), "required when DB + auth enabled")
    except Exception as exc:
        all_ok &= check("settings", False, str(exc))

    print("\n--- Files & directories ---")
    paths = {
        "knowledge/": PROJECT_ROOT / "knowledge",
        "knowledge_graph.json": PROJECT_ROOT / "knowledge" / "knowledge_graph.json",
        "dataset/": PROJECT_ROOT / "dataset",
        "results/": PROJECT_ROOT / "results",
    }
    for label, path in paths.items():
        all_ok &= check(label, path.exists(), str(path))

    print("\n--- ChromaDB ---")
    try:
        from app.retriever.vector_store import get_vector_store

        vs = get_vector_store()
        count = vs.document_count
        check("ChromaDB", True, f"{count} documents indexed")
    except Exception as exc:
        check("ChromaDB", False, str(exc))

    print("\n--- LangGraph ---")
    try:
        from app.graph import get_generate_graph

        g = get_generate_graph()
        check("LangGraph compile", g is not None)
    except Exception as exc:
        all_ok &= check("LangGraph compile", False, str(exc))

    print("\n=== Summary ===")
    if all_ok:
        print("All critical checks passed.")
        return 0
    print("Some checks failed — review output above.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
