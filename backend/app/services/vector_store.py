"""
Vector Store Service — ChromaDB + HuggingFace sentence-transformers.
Handles embedding, storage, retrieval of knowledge base chunks.
"""
import os
import json
from typing import List, Dict, Optional
from datetime import datetime

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.logger import log

settings = get_settings()


class VectorStoreService:
    def __init__(self):
        log.info(f"Initializing ChromaDB at {settings.chroma_persist_dir}")
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        log.info(f"Loading embedding model: {settings.embedding_model_id}")
        self._embedder = SentenceTransformer(settings.embedding_model_id)
        log.info("VectorStoreService ready.")

    def _embed(self, texts: List[str]) -> List[List[float]]:
        return self._embedder.encode(texts, show_progress_bar=False).tolist()

    # ─── Ingestion ────────────────────────────────────────────────────────────

    def add_document(
        self, doc_id: str, chunks: List[str], metadata: dict
    ) -> int:
        """Add document chunks to the vector store."""
        ids = [f"{doc_id}__chunk__{i}" for i in range(len(chunks))]
        embeddings = self._embed(chunks)
        metas = [
            {
                **{k: str(v) for k, v in metadata.items()},
                "chunk_index": str(i),
            }
            for i in range(len(chunks))
        ]
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metas,
        )
        log.info(f"Added {len(chunks)} chunks for doc_id={doc_id}")
        return len(chunks)

    # ─── Retrieval ────────────────────────────────────────────────────────────

    def search(
        self, query: str, top_k: int = None, threshold: float = None
    ) -> List[Dict]:
        """Semantic search over the knowledge base."""
        top_k = top_k or settings.top_k_results
        threshold = threshold or settings.similarity_threshold

        query_emb = self._embed([query])
        results = self._collection.query(
            query_embeddings=query_emb,
            n_results=min(top_k, max(1, self._collection.count())),
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            similarity = 1 - dist  # cosine distance → similarity
            if similarity >= threshold:
                hits.append(
                    {
                        "doc_id": meta.get("doc_id", ""),
                        "filename": meta.get("filename", ""),
                        "chunk_index": int(meta.get("chunk_index", 0)),
                        "similarity_score": round(similarity, 4),
                        "excerpt": doc[:300] + ("…" if len(doc) > 300 else ""),
                        "full_text": doc,
                    }
                )
        hits.sort(key=lambda x: x["similarity_score"], reverse=True)
        log.debug(f"Search '{query[:60]}…' → {len(hits)} hits above threshold={threshold}")
        return hits

    # ─── Document Management ──────────────────────────────────────────────────

    def delete_document(self, doc_id: str) -> int:
        """Delete all chunks belonging to a document."""
        all_ids = self._collection.get(
            where={"doc_id": doc_id}, include=[]
        )["ids"]
        if all_ids:
            self._collection.delete(ids=all_ids)
        log.info(f"Deleted {len(all_ids)} chunks for doc_id={doc_id}")
        return len(all_ids)

    def list_documents(self) -> List[Dict]:
        """Return unique document metadata list."""
        if self._collection.count() == 0:
            return []
        all_metas = self._collection.get(include=["metadatas"])["metadatas"]
        seen, docs = set(), []
        for m in all_metas:
            did = m.get("doc_id", "")
            if did not in seen:
                seen.add(did)
                docs.append(
                    {
                        "doc_id": did,
                        "filename": m.get("filename", ""),
                        "file_type": m.get("file_type", ""),
                        "chunks": 0,  # filled below
                        "size_bytes": int(m.get("size_bytes", 0)),
                        "uploaded_at": m.get("uploaded_at", ""),
                    }
                )
        # Count chunks per doc
        chunk_counts: Dict[str, int] = {}
        for m in all_metas:
            chunk_counts[m.get("doc_id", "")] = chunk_counts.get(m.get("doc_id", ""), 0) + 1
        for d in docs:
            d["chunks"] = chunk_counts.get(d["doc_id"], 0)
        return docs

    def stats(self) -> Dict:
        docs = self.list_documents()
        return {
            "total_documents": len(docs),
            "total_chunks": self._collection.count(),
            "supported_formats": ["pdf", "docx", "txt", "md", "html", "url"],
            "last_updated": docs[-1]["uploaded_at"] if docs else None,
        }


# Singleton
_vector_store: Optional[VectorStoreService] = None


def get_vector_store() -> VectorStoreService:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store
