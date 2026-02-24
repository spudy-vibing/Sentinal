"""
SENTINEL VECTOR STORE

ChromaDB integration for cold memory and semantic search.

Cold memory stores:
- Historical analysis results
- Past decisions and their outcomes
- Flushed context items from hot context
- Searchable via semantic similarity

Reference: docs/IMPLEMENTATION_PLAN.md Phase 1, Step 1.10
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Any
from pathlib import Path
from dataclasses import dataclass

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════
# VECTOR STORE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class VectorStoreConfig:
    """Configuration for vector store."""
    persist_directory: Optional[Path] = None
    collection_name: str = "sentinel_memory"
    embedding_function: Optional[str] = None  # Use default
    distance_function: str = "cosine"  # cosine, l2, or ip


# ═══════════════════════════════════════════════════════════════════════════
# SEARCH RESULT
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SearchResult:
    """Single search result from vector store."""
    id: str
    content: dict
    metadata: dict
    distance: float
    relevance_score: float  # 1 - distance for cosine

    @classmethod
    def from_chroma_result(
        cls,
        id: str,
        document: str,
        metadata: dict,
        distance: float
    ) -> "SearchResult":
        """Create from ChromaDB result."""
        try:
            content = json.loads(document)
        except json.JSONDecodeError:
            content = {"text": document}

        return cls(
            id=id,
            content=content,
            metadata=metadata,
            distance=distance,
            relevance_score=max(0, 1 - distance)
        )


# ═══════════════════════════════════════════════════════════════════════════
# VECTOR STORE
# ═══════════════════════════════════════════════════════════════════════════

class VectorStore:
    """
    ChromaDB-backed vector store for semantic search.

    Usage:
        store = VectorStore()

        # Add items
        store.add("analysis_001", {"type": "drift", "severity": "high"}, "NVDA concentration risk detected")

        # Search
        results = store.search("concentration issues in tech sector", n_results=5)

        # Get by ID
        item = store.get("analysis_001")
    """

    def __init__(self, config: Optional[VectorStoreConfig] = None):
        """
        Initialize vector store.

        Args:
            config: Store configuration
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "ChromaDB not available. Install with: pip install chromadb"
            )

        self.config = config or VectorStoreConfig()
        self._client = self._create_client()
        self._collection = self._get_or_create_collection()

    def _create_client(self) -> "chromadb.Client":
        """Create ChromaDB client."""
        if self.config.persist_directory:
            # Persistent client
            self.config.persist_directory.mkdir(parents=True, exist_ok=True)
            return chromadb.PersistentClient(
                path=str(self.config.persist_directory)
            )
        else:
            # In-memory client (for testing)
            return chromadb.Client()

    def _get_or_create_collection(self):
        """Get or create the collection."""
        return self._client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"hnsw:space": self.config.distance_function}
        )

    def add(
        self,
        id: str,
        content: dict,
        text: str,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Add item to vector store.

        Args:
            id: Unique identifier
            content: Structured content (JSON serializable)
            text: Text for embedding generation
            metadata: Additional searchable metadata

        Returns:
            Item ID
        """
        doc_metadata = metadata or {}
        doc_metadata["created_at"] = datetime.now(timezone.utc).isoformat()
        doc_metadata["content_json"] = json.dumps(content, default=str)

        self._collection.add(
            ids=[id],
            documents=[text],
            metadatas=[doc_metadata]
        )

        return id

    def add_many(
        self,
        items: list[tuple[str, dict, str, Optional[dict]]]
    ) -> list[str]:
        """
        Add multiple items to vector store.

        Args:
            items: List of (id, content, text, metadata) tuples

        Returns:
            List of item IDs
        """
        if not items:
            return []

        ids = []
        documents = []
        metadatas = []

        for id, content, text, metadata in items:
            doc_metadata = metadata or {}
            doc_metadata["created_at"] = datetime.now(timezone.utc).isoformat()
            doc_metadata["content_json"] = json.dumps(content, default=str)

            ids.append(id)
            documents.append(text)
            metadatas.append(doc_metadata)

        self._collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        return ids

    def search(
        self,
        query: str,
        n_results: int = 10,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None
    ) -> list[SearchResult]:
        """
        Search for similar items.

        Args:
            query: Search query text
            n_results: Maximum results to return
            where: Metadata filter (e.g., {"category": "drift"})
            where_document: Document content filter

        Returns:
            List of SearchResult objects
        """
        results = self._collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"]
        )

        search_results = []

        if results and results["ids"] and results["ids"][0]:
            for i, id in enumerate(results["ids"][0]):
                search_results.append(SearchResult.from_chroma_result(
                    id=id,
                    document=results["documents"][0][i],
                    metadata=results["metadatas"][0][i],
                    distance=results["distances"][0][i]
                ))

        return search_results

    def get(self, id: str) -> Optional[dict]:
        """
        Get item by ID.

        Args:
            id: Item identifier

        Returns:
            Content dictionary or None if not found
        """
        result = self._collection.get(ids=[id], include=["metadatas"])

        if result and result["ids"]:
            metadata = result["metadatas"][0]
            content_json = metadata.get("content_json", "{}")
            try:
                return json.loads(content_json)
            except json.JSONDecodeError:
                return {"raw": content_json}

        return None

    def get_many(self, ids: list[str]) -> dict[str, dict]:
        """
        Get multiple items by ID.

        Args:
            ids: List of item identifiers

        Returns:
            Dictionary mapping ID to content
        """
        result = self._collection.get(ids=ids, include=["metadatas"])

        items = {}
        if result and result["ids"]:
            for i, id in enumerate(result["ids"]):
                metadata = result["metadatas"][i]
                content_json = metadata.get("content_json", "{}")
                try:
                    items[id] = json.loads(content_json)
                except json.JSONDecodeError:
                    items[id] = {"raw": content_json}

        return items

    def delete(self, id: str) -> bool:
        """
        Delete item by ID.

        Args:
            id: Item identifier

        Returns:
            True if deleted
        """
        try:
            self._collection.delete(ids=[id])
            return True
        except Exception:
            return False

    def delete_many(self, ids: list[str]) -> int:
        """
        Delete multiple items.

        Args:
            ids: List of item identifiers

        Returns:
            Number of items deleted
        """
        try:
            self._collection.delete(ids=ids)
            return len(ids)
        except Exception:
            return 0

    def count(self) -> int:
        """Get total number of items in store."""
        return self._collection.count()

    def clear(self) -> None:
        """Delete all items in the collection."""
        # ChromaDB doesn't have a clear method, so we recreate the collection
        self._client.delete_collection(self.config.collection_name)
        self._collection = self._get_or_create_collection()


# ═══════════════════════════════════════════════════════════════════════════
# MEMORY STORE (Higher-level abstraction)
# ═══════════════════════════════════════════════════════════════════════════

class MemoryStore:
    """
    Higher-level memory store for Sentinel.

    Provides specialized methods for storing different types of memories:
    - Analysis results
    - Decisions
    - Context flushes
    - Events
    """

    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initialize memory store.

        Args:
            vector_store: Underlying vector store (creates default if not provided)
        """
        self._store = vector_store or VectorStore()

    def store_analysis(
        self,
        portfolio_id: str,
        agent_type: str,
        analysis: dict,
        summary: str
    ) -> str:
        """
        Store an agent analysis result.

        Args:
            portfolio_id: Portfolio identifier
            agent_type: Type of agent (drift, tax, coordinator)
            analysis: Full analysis content
            summary: Text summary for search

        Returns:
            Memory ID
        """
        id = f"analysis_{agent_type}_{uuid.uuid4().hex[:8]}"

        return self._store.add(
            id=id,
            content=analysis,
            text=f"{agent_type} analysis for {portfolio_id}: {summary}",
            metadata={
                "type": "analysis",
                "portfolio_id": portfolio_id,
                "agent_type": agent_type
            }
        )

    def store_decision(
        self,
        portfolio_id: str,
        decision_type: str,
        decision: dict,
        rationale: str
    ) -> str:
        """
        Store a decision record.

        Args:
            portfolio_id: Portfolio identifier
            decision_type: Type of decision (approve, reject, modify)
            decision: Decision content
            rationale: Human-readable rationale

        Returns:
            Memory ID
        """
        id = f"decision_{uuid.uuid4().hex[:8]}"

        return self._store.add(
            id=id,
            content=decision,
            text=f"Decision ({decision_type}) for {portfolio_id}: {rationale}",
            metadata={
                "type": "decision",
                "portfolio_id": portfolio_id,
                "decision_type": decision_type
            }
        )

    def store_context_flush(
        self,
        session_id: str,
        items: list[dict]
    ) -> list[str]:
        """
        Store flushed context items.

        Args:
            session_id: Session identifier
            items: List of context items

        Returns:
            List of memory IDs
        """
        store_items = []

        for item in items:
            id = f"context_{uuid.uuid4().hex[:8]}"
            content = item.get("content", item)
            text = json.dumps(content, default=str)[:500]  # Truncate for embedding

            store_items.append((
                id,
                content,
                text,
                {
                    "type": "context",
                    "session_id": session_id,
                    "category": item.get("category", "general")
                }
            ))

        return self._store.add_many(store_items)

    def search_analyses(
        self,
        query: str,
        portfolio_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        n_results: int = 10
    ) -> list[SearchResult]:
        """
        Search past analyses.

        Args:
            query: Search query
            portfolio_id: Filter by portfolio (optional)
            agent_type: Filter by agent type (optional)
            n_results: Maximum results

        Returns:
            List of matching analyses
        """
        where = {"type": "analysis"}

        if portfolio_id:
            where["portfolio_id"] = portfolio_id
        if agent_type:
            where["agent_type"] = agent_type

        return self._store.search(query, n_results=n_results, where=where)

    def search_decisions(
        self,
        query: str,
        portfolio_id: Optional[str] = None,
        n_results: int = 10
    ) -> list[SearchResult]:
        """
        Search past decisions.

        Args:
            query: Search query
            portfolio_id: Filter by portfolio (optional)
            n_results: Maximum results

        Returns:
            List of matching decisions
        """
        where = {"type": "decision"}

        if portfolio_id:
            where["portfolio_id"] = portfolio_id

        return self._store.search(query, n_results=n_results, where=where)

    def get_similar_situations(
        self,
        description: str,
        n_results: int = 5
    ) -> list[SearchResult]:
        """
        Find similar past situations across all memory types.

        Args:
            description: Description of current situation
            n_results: Maximum results

        Returns:
            List of similar past situations
        """
        return self._store.search(description, n_results=n_results)


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

_vector_store: Optional[VectorStore] = None
_memory_store: Optional[MemoryStore] = None


def get_vector_store() -> VectorStore:
    """Get or create default vector store."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def get_memory_store() -> MemoryStore:
    """Get or create default memory store."""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store


def is_chromadb_available() -> bool:
    """Check if ChromaDB is available."""
    return CHROMADB_AVAILABLE
