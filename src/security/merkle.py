"""
SENTINEL MERKLE CHAIN

Immutable audit trail using Merkle chain structure.

Each block contains:
- event_id: Unique identifier
- timestamp: When event occurred
- data: Event payload (JSON serializable)
- previous_hash: Hash of previous block
- current_hash: SHA-256 hash of this block

SECURITY:
- Chain is append-only (no updates or deletes)
- Tampering is detectable via hash verification
- All state transitions must be logged

Reference: docs/SECURITY_PRACTICES.md §4.1
Reference: docs/IMPLEMENTATION_PLAN.md Phase 1, Step 1.8
"""

from __future__ import annotations

import json
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any
from pathlib import Path

from src.contracts.interfaces import IMerkleChain
from src.contracts.security import AuditEvent, AuditEventType


# ═══════════════════════════════════════════════════════════════════════════
# MERKLE BLOCK
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class MerkleBlock:
    """
    Single block in the Merkle chain.

    Immutable after creation. Hash is computed from all fields.
    """
    index: int
    event_id: str
    timestamp: datetime
    event_type: str
    session_id: str
    actor: str
    action: str
    resource: Optional[str]
    data: dict
    previous_hash: str
    current_hash: str = field(default="")

    def __post_init__(self):
        """Compute hash after initialization if not set."""
        if not self.current_hash:
            self.current_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """
        Compute SHA-256 hash of block contents.

        Hash includes all fields except current_hash itself.
        """
        content = {
            "index": self.index,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "session_id": self.session_id,
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "data": self.data,
            "previous_hash": self.previous_hash
        }
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def verify(self) -> bool:
        """Verify block hash is valid."""
        return self.current_hash == self._compute_hash()

    def to_dict(self) -> dict:
        """Convert block to dictionary for serialization."""
        return {
            "index": self.index,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "session_id": self.session_id,
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MerkleBlock":
        """Reconstruct block from dictionary."""
        return cls(
            index=d["index"],
            event_id=d["event_id"],
            timestamp=datetime.fromisoformat(d["timestamp"]),
            event_type=d["event_type"],
            session_id=d["session_id"],
            actor=d["actor"],
            action=d["action"],
            resource=d.get("resource"),
            data=d.get("data", {}),
            previous_hash=d["previous_hash"],
            current_hash=d["current_hash"]
        )

    def to_audit_event(self) -> AuditEvent:
        """Convert to AuditEvent model."""
        return AuditEvent(
            event_id=self.event_id,
            event_type=AuditEventType(self.event_type),
            timestamp=self.timestamp,
            session_id=self.session_id,
            actor=self.actor,
            action=self.action,
            resource=self.resource,
            details=self.data,
            previous_hash=self.previous_hash,
            current_hash=self.current_hash
        )


# ═══════════════════════════════════════════════════════════════════════════
# MERKLE CHAIN
# ═══════════════════════════════════════════════════════════════════════════

class MerkleChain(IMerkleChain):
    """
    Append-only Merkle chain for audit logging.

    SECURITY:
    - Blocks cannot be modified after creation
    - verify_integrity() detects any tampering
    - Chain can be persisted to disk for durability

    Usage:
        chain = MerkleChain()
        hash = chain.add_block({
            "event_type": "state_transition",
            "session_id": "sess_123",
            "from_state": "MONITOR",
            "to_state": "DETECT"
        })
        assert chain.verify_integrity()
    """

    # Genesis block hash (fixed for reproducibility)
    GENESIS_HASH = "0" * 64

    def __init__(
        self,
        persistence_path: Optional[Path] = None,
        auto_persist: bool = False
    ):
        """
        Initialize Merkle chain.

        Args:
            persistence_path: Path to persist chain (optional)
            auto_persist: If True, persist after each block addition
        """
        self._blocks: list[MerkleBlock] = []
        self._persistence_path = persistence_path
        self._auto_persist = auto_persist

        # Create genesis block
        self._create_genesis_block()

        # Load existing chain if persistence path exists
        if persistence_path and persistence_path.exists():
            self._load_from_disk()

    def _create_genesis_block(self) -> None:
        """Create the genesis (first) block."""
        genesis = MerkleBlock(
            index=0,
            event_id="genesis",
            timestamp=datetime.now(timezone.utc),
            event_type=AuditEventType.SYSTEM_INITIALIZED.value,
            session_id="system",
            actor="system",
            action="chain_initialized",
            resource=None,
            data={"version": "1.0"},
            previous_hash=self.GENESIS_HASH
        )
        self._blocks.append(genesis)

    def add_block(self, data: dict) -> str:
        """
        Add new block to chain.

        Args:
            data: Event data dictionary. Must include:
                - event_type: AuditEventType value
                - session_id: Session identifier
                - actor: Who performed the action
                - action: What was done

                Optional:
                - resource: Resource identifier (portfolio, etc.)
                - Additional fields in data

        Returns:
            Hash of the new block

        Raises:
            ValueError: If required fields missing
        """
        # Extract required fields
        event_type = data.get("event_type")
        session_id = data.get("session_id", "unknown")
        actor = data.get("actor", "unknown")
        action = data.get("action", "unknown")
        resource = data.get("resource")

        if not event_type:
            raise ValueError("event_type is required in block data")

        # Get previous block hash
        previous_hash = self._blocks[-1].current_hash

        # Create new block
        block = MerkleBlock(
            index=len(self._blocks),
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            event_type=event_type if isinstance(event_type, str) else event_type.value,
            session_id=session_id,
            actor=actor,
            action=action,
            resource=resource,
            data={k: v for k, v in data.items()
                  if k not in ("event_type", "session_id", "actor", "action", "resource")},
            previous_hash=previous_hash
        )

        self._blocks.append(block)

        # Auto-persist if configured
        if self._auto_persist and self._persistence_path:
            self._persist_to_disk()

        return block.current_hash

    def verify_integrity(self) -> bool:
        """
        Verify entire chain integrity.

        Checks:
        1. Each block's hash is valid
        2. Each block's previous_hash matches prior block
        3. Genesis block hash is correct

        Returns:
            True if chain is valid, False if tampered
        """
        if not self._blocks:
            return False

        # Verify genesis block
        if self._blocks[0].previous_hash != self.GENESIS_HASH:
            return False

        # Verify each block
        for i, block in enumerate(self._blocks):
            # Verify block's own hash
            if not block.verify():
                return False

            # Verify chain linkage (except genesis)
            if i > 0:
                if block.previous_hash != self._blocks[i - 1].current_hash:
                    return False

        return True

    def get_root_hash(self) -> str:
        """
        Get the current chain root (latest block hash).

        Returns:
            Hash of the most recent block
        """
        if not self._blocks:
            return self.GENESIS_HASH
        return self._blocks[-1].current_hash

    def get_block(self, index: int) -> Optional[MerkleBlock]:
        """Get block by index."""
        if 0 <= index < len(self._blocks):
            return self._blocks[index]
        return None

    def get_block_by_hash(self, hash: str) -> Optional[MerkleBlock]:
        """Get block by hash."""
        for block in self._blocks:
            if block.current_hash == hash:
                return block
        return None

    def get_blocks_by_session(self, session_id: str) -> list[MerkleBlock]:
        """Get all blocks for a session."""
        return [b for b in self._blocks if b.session_id == session_id]

    def get_blocks_by_event_type(self, event_type: AuditEventType) -> list[MerkleBlock]:
        """Get all blocks of a specific event type."""
        event_type_str = event_type.value if isinstance(event_type, AuditEventType) else event_type
        return [b for b in self._blocks if b.event_type == event_type_str]

    def get_blocks_in_range(
        self,
        start: datetime,
        end: datetime
    ) -> list[MerkleBlock]:
        """Get blocks within a time range."""
        return [b for b in self._blocks if start <= b.timestamp <= end]

    def __len__(self) -> int:
        """Return number of blocks in chain."""
        return len(self._blocks)

    def get_block_count(self) -> int:
        """Get number of blocks in chain (IMerkleChain interface)."""
        return len(self._blocks)

    def __iter__(self):
        """Iterate over blocks."""
        return iter(self._blocks)

    # ─── Persistence ──────────────────────────────────────────────────────────

    def _persist_to_disk(self) -> None:
        """Save chain to disk."""
        if not self._persistence_path:
            return

        self._persistence_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "1.0",
            "block_count": len(self._blocks),
            "root_hash": self.get_root_hash(),
            "blocks": [b.to_dict() for b in self._blocks]
        }

        with open(self._persistence_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _load_from_disk(self) -> None:
        """Load chain from disk."""
        if not self._persistence_path or not self._persistence_path.exists():
            return

        # Check if file has content
        if self._persistence_path.stat().st_size == 0:
            return

        with open(self._persistence_path, "r") as f:
            data = json.load(f)

        # Clear current blocks and load from file
        self._blocks = [MerkleBlock.from_dict(b) for b in data["blocks"]]

        # Verify loaded chain
        if not self.verify_integrity():
            raise ValueError(
                f"Merkle chain at {self._persistence_path} failed integrity check. "
                "Chain may have been tampered with."
            )

    def persist(self) -> None:
        """Manually persist chain to disk."""
        self._persist_to_disk()

    def export_chain(self) -> list[dict]:
        """Export chain as list of dictionaries."""
        return [b.to_dict() for b in self._blocks]

    def export_audit_events(self) -> list[AuditEvent]:
        """Export chain as AuditEvent models."""
        return [b.to_audit_event() for b in self._blocks[1:]]  # Skip genesis


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

_merkle_chain: Optional[MerkleChain] = None


def get_merkle_chain() -> MerkleChain:
    """Get or create default Merkle chain."""
    global _merkle_chain
    if _merkle_chain is None:
        _merkle_chain = MerkleChain()
    return _merkle_chain


def get_persistent_chain(path: Path, auto_persist: bool = True) -> MerkleChain:
    """
    Get or create a persistent Merkle chain.

    Args:
        path: Path to chain file
        auto_persist: If True, persist after each block

    Returns:
        MerkleChain instance
    """
    return MerkleChain(persistence_path=path, auto_persist=auto_persist)


def verify_chain_file(path: Path) -> bool:
    """
    Verify integrity of a persisted chain file.

    Args:
        path: Path to chain file

    Returns:
        True if chain is valid
    """
    try:
        chain = MerkleChain(persistence_path=path)
        return chain.verify_integrity()
    except Exception:
        return False
