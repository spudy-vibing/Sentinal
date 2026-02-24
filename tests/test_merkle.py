"""
SENTINEL MERKLE CHAIN TESTS

Tests for immutable audit trail.

Reference: docs/IMPLEMENTATION_PLAN.md Phase 1, Security Tests
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from src.security.merkle import (
    MerkleBlock,
    MerkleChain,
    get_merkle_chain,
    get_persistent_chain,
    verify_chain_file,
)
from src.contracts.security import AuditEventType


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def merkle_chain():
    """Create a fresh Merkle chain for testing."""
    return MerkleChain()


@pytest.fixture
def temp_chain_file():
    """Create temporary file for chain persistence."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        yield Path(f.name)


# ═══════════════════════════════════════════════════════════════════════════
# BASIC CHAIN TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestMerkleChainBasics:
    """Test basic chain operations."""

    def test_chain_starts_with_genesis_block(self, merkle_chain):
        """Test that chain starts with genesis block."""
        assert len(merkle_chain) == 1
        genesis = merkle_chain.get_block(0)
        assert genesis is not None
        assert genesis.event_type == AuditEventType.SYSTEM_INITIALIZED.value
        assert genesis.previous_hash == MerkleChain.GENESIS_HASH

    def test_add_block_increases_length(self, merkle_chain):
        """Test that adding blocks increases chain length."""
        initial_length = len(merkle_chain)

        merkle_chain.add_block({
            "event_type": AuditEventType.MARKET_EVENT_DETECTED.value,
            "session_id": "test_session",
            "actor": "system",
            "action": "market_event"
        })

        assert len(merkle_chain) == initial_length + 1

    def test_add_block_returns_hash(self, merkle_chain):
        """Test that add_block returns the block hash."""
        hash = merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test_session",
            "actor": "system",
            "action": "transition"
        })

        assert hash is not None
        assert len(hash) == 64  # SHA-256 hex

    def test_blocks_are_linked(self, merkle_chain):
        """Test that blocks are properly linked."""
        merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "test"
        })

        block_0 = merkle_chain.get_block(0)
        block_1 = merkle_chain.get_block(1)

        assert block_1.previous_hash == block_0.current_hash


class TestMerkleBlockRequired:
    """Test required fields in blocks."""

    def test_event_type_required(self, merkle_chain):
        """Test that event_type is required."""
        with pytest.raises(ValueError, match="event_type is required"):
            merkle_chain.add_block({
                "session_id": "test",
                "actor": "test",
                "action": "test"
            })

    def test_default_values_for_optional(self, merkle_chain):
        """Test that optional fields have defaults."""
        merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value
        })

        block = merkle_chain.get_block(1)
        assert block.session_id == "unknown"
        assert block.actor == "unknown"
        assert block.action == "unknown"


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRITY TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestChainIntegrity:
    """Test chain integrity verification."""

    def test_verify_integrity_passes_valid_chain(self, merkle_chain):
        """Test that valid chain passes integrity check."""
        # Add some blocks
        for i in range(5):
            merkle_chain.add_block({
                "event_type": AuditEventType.STATE_TRANSITION.value,
                "session_id": f"test_{i}",
                "actor": "system",
                "action": f"action_{i}"
            })

        assert merkle_chain.verify_integrity() is True

    def test_verify_integrity_fails_on_tampered_hash(self, merkle_chain):
        """Test that tampered hash is detected."""
        merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "test"
        })

        # Tamper with block hash
        merkle_chain._blocks[1].current_hash = "0" * 64

        assert merkle_chain.verify_integrity() is False

    def test_verify_integrity_fails_on_broken_chain(self, merkle_chain):
        """Test that broken chain link is detected."""
        merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "test"
        })

        # Break chain link
        merkle_chain._blocks[1].previous_hash = "1" * 64

        assert merkle_chain.verify_integrity() is False

    def test_verify_integrity_fails_on_tampered_data(self, merkle_chain):
        """Test that tampered data is detected."""
        merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "original_action"
        })

        # Tamper with data (this won't update hash)
        merkle_chain._blocks[1].action = "tampered_action"

        assert merkle_chain.verify_integrity() is False


class TestBlockVerification:
    """Test individual block verification."""

    def test_block_verify_passes_valid(self, merkle_chain):
        """Test that valid block passes verification."""
        merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "test"
        })

        block = merkle_chain.get_block(1)
        assert block.verify() is True

    def test_block_verify_fails_tampered(self, merkle_chain):
        """Test that tampered block fails verification."""
        merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "original"
        })

        block = merkle_chain.get_block(1)
        block.action = "tampered"

        assert block.verify() is False


# ═══════════════════════════════════════════════════════════════════════════
# QUERY TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestChainQueries:
    """Test chain query methods."""

    def test_get_block_by_index(self, merkle_chain):
        """Test getting block by index."""
        merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "test"
        })

        block = merkle_chain.get_block(1)
        assert block is not None
        assert block.index == 1

    def test_get_block_invalid_index(self, merkle_chain):
        """Test getting block with invalid index."""
        assert merkle_chain.get_block(999) is None
        assert merkle_chain.get_block(-1) is None

    def test_get_block_by_hash(self, merkle_chain):
        """Test getting block by hash."""
        hash = merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "test"
        })

        block = merkle_chain.get_block_by_hash(hash)
        assert block is not None
        assert block.current_hash == hash

    def test_get_blocks_by_session(self, merkle_chain):
        """Test filtering blocks by session."""
        merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "session_1",
            "actor": "test",
            "action": "test"
        })
        merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "session_2",
            "actor": "test",
            "action": "test"
        })
        merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "session_1",
            "actor": "test",
            "action": "test2"
        })

        session_1_blocks = merkle_chain.get_blocks_by_session("session_1")
        assert len(session_1_blocks) == 2

    def test_get_blocks_by_event_type(self, merkle_chain):
        """Test filtering blocks by event type."""
        merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "transition"
        })
        merkle_chain.add_block({
            "event_type": AuditEventType.AGENT_INVOKED.value,
            "session_id": "test",
            "actor": "test",
            "action": "invoke"
        })

        transition_blocks = merkle_chain.get_blocks_by_event_type(
            AuditEventType.STATE_TRANSITION
        )
        assert len(transition_blocks) == 1

    def test_get_root_hash(self, merkle_chain):
        """Test getting root hash."""
        hash = merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "test"
        })

        assert merkle_chain.get_root_hash() == hash


# ═══════════════════════════════════════════════════════════════════════════
# PERSISTENCE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestChainPersistence:
    """Test chain persistence to disk."""

    def test_persist_and_load(self, temp_chain_file):
        """Test persisting and loading chain."""
        # Create and populate chain
        chain = MerkleChain(persistence_path=temp_chain_file)
        chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "test_action"
        })
        chain.persist()

        # Load chain from disk
        loaded_chain = MerkleChain(persistence_path=temp_chain_file)

        assert len(loaded_chain) == len(chain)
        assert loaded_chain.get_root_hash() == chain.get_root_hash()
        assert loaded_chain.verify_integrity() is True

    def test_auto_persist(self, temp_chain_file):
        """Test auto-persist mode."""
        chain = MerkleChain(
            persistence_path=temp_chain_file,
            auto_persist=True
        )

        chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "test"
        })

        # File should exist and be loadable
        loaded = MerkleChain(persistence_path=temp_chain_file)
        assert len(loaded) == 2  # Genesis + 1 block

    def test_verify_chain_file(self, temp_chain_file):
        """Test chain file verification."""
        chain = MerkleChain(persistence_path=temp_chain_file)
        chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "test"
        })
        chain.persist()

        assert verify_chain_file(temp_chain_file) is True

    def test_tampered_file_fails_verification(self, temp_chain_file):
        """Test that tampered file fails verification."""
        chain = MerkleChain(persistence_path=temp_chain_file)
        chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "test"
        })
        chain.persist()

        # Tamper with file
        with open(temp_chain_file, "r") as f:
            content = f.read()

        tampered = content.replace("test", "tampered")

        with open(temp_chain_file, "w") as f:
            f.write(tampered)

        # Should fail verification
        with pytest.raises(ValueError, match="failed integrity check"):
            MerkleChain(persistence_path=temp_chain_file)


# ═══════════════════════════════════════════════════════════════════════════
# EXPORT TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestChainExport:
    """Test chain export functionality."""

    def test_export_chain(self, merkle_chain):
        """Test exporting chain as dictionaries."""
        merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "test"
        })

        exported = merkle_chain.export_chain()

        assert len(exported) == 2
        assert exported[1]["event_type"] == AuditEventType.STATE_TRANSITION.value

    def test_export_audit_events(self, merkle_chain):
        """Test exporting as AuditEvent models."""
        merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "test"
        })

        events = merkle_chain.export_audit_events()

        assert len(events) == 1  # Excludes genesis
        assert events[0].event_type == AuditEventType.STATE_TRANSITION


# ═══════════════════════════════════════════════════════════════════════════
# ITERATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestChainIteration:
    """Test chain iteration."""

    def test_iterate_over_chain(self, merkle_chain):
        """Test iterating over chain blocks."""
        for i in range(3):
            merkle_chain.add_block({
                "event_type": AuditEventType.STATE_TRANSITION.value,
                "session_id": "test",
                "actor": "test",
                "action": f"action_{i}"
            })

        blocks = list(merkle_chain)
        assert len(blocks) == 4  # Genesis + 3 blocks

    def test_chain_length(self, merkle_chain):
        """Test chain length."""
        assert len(merkle_chain) == 1  # Genesis only

        merkle_chain.add_block({
            "event_type": AuditEventType.STATE_TRANSITION.value,
            "session_id": "test",
            "actor": "test",
            "action": "test"
        })

        assert len(merkle_chain) == 2
