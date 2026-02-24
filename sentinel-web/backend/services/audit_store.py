"""
SENTINEL V2 - SQLite Audit Store

Persistent storage for Merkle chain audit trail.
Supports filtering, searching, and reporting.
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pathlib import Path
from contextlib import contextmanager
import threading

# Database file location
DB_PATH = Path(__file__).parent.parent / "data" / "audit_trail.db"


class AuditStore:
    """
    SQLite-backed audit trail storage.
    Thread-safe with connection pooling.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern for shared store."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Ensure data directory exists
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_db()
        self._initialized = True
        print(f"  [AuditStore] Initialized at {DB_PATH}")

    @contextmanager
    def _get_connection(self):
        """Get a database connection with proper cleanup."""
        conn = sqlite3.connect(str(DB_PATH), timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Create database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Main audit blocks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    block_index INTEGER NOT NULL,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    actor TEXT,
                    action TEXT,
                    resource TEXT,
                    data TEXT,
                    previous_hash TEXT,
                    current_hash TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Indexes for fast queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_type
                ON audit_blocks(event_type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON audit_blocks(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_actor
                ON audit_blocks(actor)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_id
                ON audit_blocks(session_id)
            """)

            conn.commit()

    def add_block(self, block: Dict[str, Any]) -> int:
        """
        Add a new block to the audit trail.

        Args:
            block: Block data with event_type, timestamp, etc.

        Returns:
            The inserted block ID.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Extract fields
            data_json = json.dumps(block.get("data", {})) if block.get("data") else None

            cursor.execute("""
                INSERT INTO audit_blocks (
                    block_index, event_id, event_type, timestamp,
                    session_id, actor, action, resource,
                    data, previous_hash, current_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                block.get("index", 0),
                block.get("event_id", f"evt_{datetime.now().timestamp()}"),
                block.get("event_type", "unknown"),
                block.get("timestamp", datetime.now(timezone.utc).isoformat()),
                block.get("session_id"),
                block.get("actor", "system"),
                block.get("action"),
                block.get("resource"),
                data_json,
                block.get("previous_hash"),
                block.get("current_hash", block.get("hash", ""))
            ))

            conn.commit()
            return cursor.lastrowid

    def get_blocks(
        self,
        event_type: Optional[str] = None,
        actor: Optional[str] = None,
        session_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Query blocks with filtering.

        Args:
            event_type: Filter by event type
            actor: Filter by actor
            session_id: Filter by session
            from_date: Start date (ISO format)
            to_date: End date (ISO format)
            search: Full-text search in data
            limit: Max results
            offset: Pagination offset

        Returns:
            List of matching blocks.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM audit_blocks WHERE 1=1"
            params = []

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)

            if actor:
                query += " AND actor = ?"
                params.append(actor)

            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)

            if from_date:
                query += " AND timestamp >= ?"
                params.append(from_date)

            if to_date:
                query += " AND timestamp <= ?"
                params.append(to_date)

            if search:
                query += " AND (data LIKE ? OR action LIKE ? OR resource LIKE ?)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term])

            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_dict(row) for row in rows]

    def get_block_by_hash(self, hash: str) -> Optional[Dict[str, Any]]:
        """Get a specific block by its hash."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM audit_blocks WHERE current_hash LIKE ?",
                (f"{hash}%",)
            )
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None

    def get_stats(self) -> Dict[str, Any]:
        """Get audit trail statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Total blocks
            cursor.execute("SELECT COUNT(*) FROM audit_blocks")
            total = cursor.fetchone()[0]

            # By event type
            cursor.execute("""
                SELECT event_type, COUNT(*) as count
                FROM audit_blocks
                GROUP BY event_type
                ORDER BY count DESC
            """)
            by_type = {row[0]: row[1] for row in cursor.fetchall()}

            # By actor
            cursor.execute("""
                SELECT actor, COUNT(*) as count
                FROM audit_blocks
                WHERE actor IS NOT NULL
                GROUP BY actor
                ORDER BY count DESC
            """)
            by_actor = {row[0]: row[1] for row in cursor.fetchall()}

            # Recent activity (last 24h)
            cursor.execute("""
                SELECT COUNT(*) FROM audit_blocks
                WHERE timestamp >= datetime('now', '-1 day')
            """)
            last_24h = cursor.fetchone()[0]

            # Last block timestamp
            cursor.execute("""
                SELECT timestamp FROM audit_blocks
                ORDER BY timestamp DESC LIMIT 1
            """)
            last_row = cursor.fetchone()
            last_activity = last_row[0] if last_row else None

            # Decisions (approvals)
            cursor.execute("""
                SELECT COUNT(*) FROM audit_blocks
                WHERE event_type LIKE '%approved%' OR event_type LIKE '%decision%'
            """)
            decisions = cursor.fetchone()[0]

            return {
                "total_blocks": total,
                "by_event_type": by_type,
                "by_actor": by_actor,
                "last_24h_count": last_24h,
                "last_activity": last_activity,
                "decisions_logged": decisions
            }

    def get_event_types(self) -> List[str]:
        """Get all distinct event types."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT event_type FROM audit_blocks ORDER BY event_type")
            return [row[0] for row in cursor.fetchall()]

    def get_actors(self) -> List[str]:
        """Get all distinct actors."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT actor FROM audit_blocks
                WHERE actor IS NOT NULL
                ORDER BY actor
            """)
            return [row[0] for row in cursor.fetchall()]

    def verify_chain(self) -> Dict[str, Any]:
        """
        Verify chain integrity by checking hash linkage.

        Returns:
            Verification result with any issues found.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT block_index, current_hash, previous_hash
                FROM audit_blocks
                ORDER BY block_index
            """)
            rows = cursor.fetchall()

            if not rows:
                return {"valid": True, "blocks_checked": 0, "issues": []}

            issues = []
            prev_hash = None

            for row in rows:
                idx, curr_hash, stored_prev = row

                if prev_hash is not None and stored_prev != prev_hash:
                    issues.append({
                        "block_index": idx,
                        "expected_previous": prev_hash,
                        "actual_previous": stored_prev
                    })

                prev_hash = curr_hash

            return {
                "valid": len(issues) == 0,
                "blocks_checked": len(rows),
                "issues": issues
            }

    def export_csv(self, filepath: str, **filters) -> int:
        """Export blocks to CSV file."""
        import csv

        blocks = self.get_blocks(limit=10000, **filters)

        if not blocks:
            return 0

        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=blocks[0].keys())
            writer.writeheader()
            writer.writerows(blocks)

        return len(blocks)

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert SQLite row to dictionary."""
        d = dict(row)

        # Parse JSON data field
        if d.get("data"):
            try:
                d["data"] = json.loads(d["data"])
            except json.JSONDecodeError:
                pass

        # Add block_hash alias for frontend compatibility
        d["block_hash"] = d.get("current_hash", "")

        return d

    def clear(self):
        """Clear all blocks (use with caution!)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM audit_blocks")
            conn.commit()


# Global singleton instance
audit_store = AuditStore()
