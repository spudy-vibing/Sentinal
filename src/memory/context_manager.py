"""
SENTINEL CONTEXT MANAGER

Hot/cold memory split for efficient token management.

Hot Context:
- Expensive (token-limited)
- Current analysis, recent events
- Auto-flushes to cold memory when limit exceeded

Cold Memory:
- Cheap (unlimited)
- Persistent decisions, historical data
- Searchable via vector store

Reference: docs/IMPLEMENTATION_PLAN.md Phase 1, Step 1.9
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any, Callable
from pathlib import Path
from collections import deque

from src.contracts.interfaces import IContextManager


# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT ITEM
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ContextItem:
    """
    Single item in the context window.

    Attributes:
        item_id: Unique identifier
        content: The actual content (dict)
        estimated_tokens: Approximate token count
        priority: Higher priority items are kept longer (1-10)
        created_at: When item was added
        category: Classification for routing (event, analysis, decision, etc.)
        metadata: Additional searchable metadata
    """
    item_id: str
    content: dict
    estimated_tokens: int
    priority: int = 5
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    category: str = "general"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "item_id": self.item_id,
            "content": self.content,
            "estimated_tokens": self.estimated_tokens,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "category": self.category,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ContextItem":
        """Reconstruct from dictionary."""
        return cls(
            item_id=d["item_id"],
            content=d["content"],
            estimated_tokens=d["estimated_tokens"],
            priority=d.get("priority", 5),
            created_at=datetime.fromisoformat(d["created_at"]),
            category=d.get("category", "general"),
            metadata=d.get("metadata", {})
        )


# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class ContextManager(IContextManager):
    """
    Manages hot context with automatic overflow to cold memory.

    Hot context maintains a token budget. When exceeded:
    1. Low-priority items are flushed first
    2. Flushed items go to cold memory (vector store)
    3. Oldest items are removed if budget still exceeded

    Usage:
        manager = ContextManager(token_limit=8000)

        # Add items to context
        manager.add_to_context({"event": "market_drop"}, estimated_tokens=50)

        # Get current context for LLM
        context = manager.get_context()

        # Query cold memory
        results = manager.search_memory("tech sector drop")
    """

    DEFAULT_TOKEN_LIMIT = 8000  # Default hot context limit

    def __init__(
        self,
        token_limit: int = DEFAULT_TOKEN_LIMIT,
        flush_callback: Optional[Callable[[list[ContextItem]], None]] = None,
        persistence_path: Optional[Path] = None
    ):
        """
        Initialize context manager.

        Args:
            token_limit: Maximum tokens in hot context
            flush_callback: Called when items are flushed to cold memory
            persistence_path: Path to persist hot context (optional)
        """
        self.token_limit = token_limit
        self._flush_callback = flush_callback
        self._persistence_path = persistence_path

        # Hot context storage
        self._items: list[ContextItem] = []
        self._current_tokens = 0

        # Session tracking
        self._session_id: Optional[str] = None

        # Statistics
        self._total_items_added = 0
        self._total_items_flushed = 0

        # Load persisted context if available
        if persistence_path and persistence_path.exists():
            self._load_context()

    def add_to_context(
        self,
        item: dict,
        estimated_tokens: int,
        priority: int = 5,
        category: str = "general",
        metadata: Optional[dict] = None
    ) -> str:
        """
        Add item to hot context.

        Automatically flushes to cold memory if token limit exceeded.

        Args:
            item: Content dictionary
            estimated_tokens: Approximate token count
            priority: Retention priority (1-10, higher = kept longer)
            category: Item category for filtering
            metadata: Additional searchable metadata

        Returns:
            Item ID for reference
        """
        context_item = ContextItem(
            item_id=str(uuid.uuid4()),
            content=item,
            estimated_tokens=estimated_tokens,
            priority=max(1, min(10, priority)),  # Clamp to 1-10
            category=category,
            metadata=metadata or {}
        )

        # Add item
        self._items.append(context_item)
        self._current_tokens += estimated_tokens
        self._total_items_added += 1

        # Check if we need to flush
        if self._current_tokens > self.token_limit:
            self._auto_flush()

        return context_item.item_id

    def get_context(self) -> list[dict]:
        """
        Get current hot context for LLM consumption.

        Returns:
            List of content dictionaries, ordered by creation time
        """
        # Return sorted by timestamp (oldest first)
        sorted_items = sorted(self._items, key=lambda x: x.created_at)
        return [item.content for item in sorted_items]

    def get_context_with_metadata(self) -> list[ContextItem]:
        """Get context items with full metadata."""
        return sorted(self._items, key=lambda x: x.created_at)

    def get_context_by_category(self, category: str) -> list[dict]:
        """Get context items filtered by category."""
        items = [i for i in self._items if i.category == category]
        return [item.content for item in sorted(items, key=lambda x: x.created_at)]

    def flush_to_memory(self) -> list[ContextItem]:
        """
        Manually flush all items to cold memory.

        Returns:
            List of flushed items
        """
        flushed = list(self._items)

        if flushed and self._flush_callback:
            self._flush_callback(flushed)

        self._total_items_flushed += len(flushed)
        self._items.clear()
        self._current_tokens = 0

        return flushed

    def _auto_flush(self) -> None:
        """
        Automatically flush lowest-priority items until under limit.

        Strategy:
        1. Sort items by priority (ascending)
        2. Flush lowest priority items first
        3. Continue until under token limit
        """
        # Sort by priority (low to high), then by age (oldest first)
        sorted_items = sorted(
            self._items,
            key=lambda x: (x.priority, x.created_at)
        )

        to_flush = []
        kept_items = []

        running_tokens = 0
        for item in reversed(sorted_items):  # Start with highest priority
            if running_tokens + item.estimated_tokens <= self.token_limit:
                kept_items.append(item)
                running_tokens += item.estimated_tokens
            else:
                to_flush.append(item)

        # Update state
        self._items = kept_items
        self._current_tokens = running_tokens

        # Callback for flushed items
        if to_flush and self._flush_callback:
            self._flush_callback(to_flush)

        self._total_items_flushed += len(to_flush)

    def remove_item(self, item_id: str) -> bool:
        """
        Remove specific item from context.

        Args:
            item_id: Item to remove

        Returns:
            True if item was found and removed
        """
        for i, item in enumerate(self._items):
            if item.item_id == item_id:
                self._current_tokens -= item.estimated_tokens
                self._items.pop(i)
                return True
        return False

    def clear(self) -> None:
        """Clear all items from hot context without flushing."""
        self._items.clear()
        self._current_tokens = 0

    def search_memory(self, query: str, hybrid: bool = True) -> list[dict]:
        """
        Search cold memory (IContextManager interface).

        This is a placeholder - actual search requires vector store integration.
        For now, searches hot context as fallback.

        Args:
            query: Search query
            hybrid: Use both semantic and keyword search

        Returns:
            List of matching memory items
        """
        # Simple keyword search in hot context as fallback
        # Real implementation would search vector store
        query_lower = query.lower()
        results = []

        for item in self._items:
            content_str = str(item.content).lower()
            if query_lower in content_str:
                results.append(item.content)

        return results

    # ─── Session Management ───────────────────────────────────────────────────

    def set_session(self, session_id: str) -> None:
        """Set current session ID for context tracking."""
        self._session_id = session_id

    def get_session_context(self, session_id: str) -> list[dict]:
        """Get context items for a specific session."""
        items = [
            i for i in self._items
            if i.metadata.get("session_id") == session_id
        ]
        return [item.content for item in sorted(items, key=lambda x: x.created_at)]

    # ─── Statistics ───────────────────────────────────────────────────────────

    @property
    def current_tokens(self) -> int:
        """Current token usage."""
        return self._current_tokens

    @property
    def available_tokens(self) -> int:
        """Available tokens before flush."""
        return max(0, self.token_limit - self._current_tokens)

    @property
    def utilization(self) -> float:
        """Context utilization as percentage."""
        return (self._current_tokens / self.token_limit) * 100

    @property
    def item_count(self) -> int:
        """Number of items in hot context."""
        return len(self._items)

    def get_stats(self) -> dict:
        """Get context manager statistics."""
        return {
            "token_limit": self.token_limit,
            "current_tokens": self._current_tokens,
            "available_tokens": self.available_tokens,
            "utilization_pct": round(self.utilization, 1),
            "item_count": len(self._items),
            "total_items_added": self._total_items_added,
            "total_items_flushed": self._total_items_flushed
        }

    # ─── Persistence ──────────────────────────────────────────────────────────

    def persist(self) -> None:
        """Persist hot context to disk."""
        if not self._persistence_path:
            return

        self._persistence_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "1.0",
            "token_limit": self.token_limit,
            "current_tokens": self._current_tokens,
            "session_id": self._session_id,
            "items": [item.to_dict() for item in self._items],
            "stats": {
                "total_items_added": self._total_items_added,
                "total_items_flushed": self._total_items_flushed
            }
        }

        with open(self._persistence_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _load_context(self) -> None:
        """Load persisted context from disk."""
        if not self._persistence_path or not self._persistence_path.exists():
            return

        with open(self._persistence_path, "r") as f:
            data = json.load(f)

        self._items = [ContextItem.from_dict(i) for i in data.get("items", [])]
        self._current_tokens = sum(i.estimated_tokens for i in self._items)
        self._session_id = data.get("session_id")

        stats = data.get("stats", {})
        self._total_items_added = stats.get("total_items_added", 0)
        self._total_items_flushed = stats.get("total_items_flushed", 0)


# ═══════════════════════════════════════════════════════════════════════════
# SESSION CONTEXT
# ═══════════════════════════════════════════════════════════════════════════

class SessionContext:
    """
    Per-session context wrapper.

    Manages context for a single session, automatically tagging
    items with session ID.
    """

    def __init__(
        self,
        session_id: str,
        manager: ContextManager
    ):
        """
        Initialize session context.

        Args:
            session_id: Session identifier
            manager: Parent context manager
        """
        self.session_id = session_id
        self._manager = manager

    def add(
        self,
        item: dict,
        estimated_tokens: int,
        priority: int = 5,
        category: str = "general"
    ) -> str:
        """Add item to context, tagged with session ID."""
        return self._manager.add_to_context(
            item=item,
            estimated_tokens=estimated_tokens,
            priority=priority,
            category=category,
            metadata={"session_id": self.session_id}
        )

    def get_context(self) -> list[dict]:
        """Get context items for this session."""
        return self._manager.get_session_context(self.session_id)

    def flush(self) -> None:
        """Flush this session's items only."""
        items_to_remove = [
            i.item_id for i in self._manager._items
            if i.metadata.get("session_id") == self.session_id
        ]
        for item_id in items_to_remove:
            self._manager.remove_item(item_id)


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Get or create default context manager."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


def create_session_context(session_id: str) -> SessionContext:
    """Create a session-scoped context wrapper."""
    return SessionContext(session_id, get_context_manager())


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Simple heuristic: ~4 characters per token (English text).
    For more accuracy, use tiktoken library.

    Args:
        text: Text to estimate

    Returns:
        Estimated token count
    """
    return max(1, len(text) // 4)


def estimate_dict_tokens(data: dict) -> int:
    """
    Estimate token count for dictionary.

    Args:
        data: Dictionary to estimate

    Returns:
        Estimated token count
    """
    json_str = json.dumps(data, default=str)
    return estimate_tokens(json_str)
