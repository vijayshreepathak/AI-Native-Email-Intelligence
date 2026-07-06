"""ChromaDB vector store for knowledge documents."""

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

from ..config import KNOWLEDGE_DIR, POLICIES_DIR, get_settings
from ..utils.helpers import load_json
from ..utils.logger import get_logger

logger = get_logger(__name__)

COLLECTION_NAME = "knowledge_documents"


class VectorStore:
    """ChromaDB-backed vector store using built-in ONNX embeddings."""

    def __init__(self) -> None:
        settings = get_settings()
        self._persist_dir = Path(settings.chroma_persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        self._client = chromadb.PersistentClient(
            path=str(self._persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def document_count(self) -> int:
        return self._collection.count()

    def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        safe_metas = [_sanitize_metadata(m) for m in metadatas]
        self._collection.upsert(ids=ids, documents=documents, metadatas=safe_metas)
        logger.info("Added %d documents to vector store", len(ids))

    def query(self, query_text: str, top_k: int = 3) -> list[dict[str, Any]]:
        if self._collection.count() == 0:
            logger.warning("Vector store is empty, returning no results")
            return []

        results = self._collection.query(
            query_texts=[query_text],
            n_results=min(top_k, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        documents: list[dict[str, Any]] = []
        if not results["ids"] or not results["ids"][0]:
            return documents

        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i] if results["distances"] else 0.0
            score = 1.0 - distance
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            documents.append(
                {
                    "id": doc_id,
                    "content": results["documents"][0][i],
                    "score": round(score, 4),
                    "node": metadata.get("node", ""),
                    "category": metadata.get("category", ""),
                    "title": metadata.get("title", ""),
                    "metadata": metadata,
                }
            )
        return documents

    def ingest_policies(self) -> int:
        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for policy_file in sorted(POLICIES_DIR.glob("*.json")):
            data = load_json(policy_file)
            node = data.get("node", policy_file.stem.title())
            for policy in data.get("policies", []):
                doc_id = policy["id"]
                content = f"{policy['title']}: {policy['content']}"
                ids.append(doc_id)
                documents.append(content)
                metadatas.append(
                    {
                        "node": node,
                        "category": "policy",
                        "title": policy["title"],
                        "tags": ",".join(policy.get("tags", [])),
                        "source_file": policy_file.name,
                    }
                )

        faq_dir = KNOWLEDGE_DIR / "faq"
        for faq_file in sorted(faq_dir.glob("*.json")):
            data = load_json(faq_file)
            node = data.get("node", "General")
            for idx, faq in enumerate(data.get("faqs", [])):
                doc_id = f"faq-{node.lower()}-{idx}"
                content = f"Q: {faq['question']} A: {faq['answer']}"
                ids.append(doc_id)
                documents.append(content)
                metadatas.append(
                    {
                        "node": node,
                        "category": "faq",
                        "title": faq["question"],
                        "tags": "",
                        "source_file": faq_file.name,
                    }
                )

        if ids:
            self.add_documents(ids, documents, metadatas)

        logger.info("Ingested %d knowledge documents", len(ids))
        return len(ids)

    def clear(self) -> None:
        self._client.delete_collection(COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )


def _sanitize_metadata(meta: dict[str, Any]) -> dict[str, str | int | float | bool]:
    """ChromaDB requires scalar metadata values."""
    clean: dict[str, str | int | float | bool] = {}
    for k, v in meta.items():
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        else:
            clean[k] = str(v)
    return clean


_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
