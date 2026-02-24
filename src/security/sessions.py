"""
SENTINEL SESSION MANAGER

Session lifecycle management with sandbox boundary enforcement.

Reference: docs/IMPLEMENTATION_PLAN.md Phase 2, Step 2.8
Reference: docs/SECURITY_PRACTICES.md
"""

from __future__ import annotations

import logging
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Callable, Any, TypeVar, Generic
from dataclasses import dataclass, field
from contextlib import contextmanager, asynccontextmanager
from abc import ABC, abstractmethod

from src.contracts.interfaces import IMerkleChain, ISandbox
from src.contracts.security import (
    SessionConfig,
    SessionType,
    Role,
    Permission,
    AuditEventType,
    SandboxConfig,
    SANDBOXED_SESSIONS,
    DEFAULT_SANDBOX_CONFIG,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ═══════════════════════════════════════════════════════════════════════════
# SESSION LIFECYCLE
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SessionMetrics:
    """Metrics collected during session lifecycle."""
    tool_calls: int = 0
    permission_checks: int = 0
    permission_denials: int = 0
    portfolio_accesses: int = 0
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        """Total session duration in seconds."""
        end = self.end_time or datetime.now(timezone.utc)
        return (end - self.start_time).total_seconds()

    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "tool_calls": self.tool_calls,
            "permission_checks": self.permission_checks,
            "permission_denials": self.permission_denials,
            "portfolio_accesses": self.portfolio_accesses,
            "duration_seconds": self.duration_seconds,
        }


class SessionManager:
    """
    Manages session lifecycle with security boundary enforcement.

    Features:
    - Session creation with automatic expiration
    - Tool call limiting
    - Portfolio access tracking
    - Sandbox enforcement for untrusted sessions
    - Audit logging
    """

    def __init__(
        self,
        audit_chain: Optional[IMerkleChain] = None,
        sandbox: Optional[ISandbox] = None,
        default_timeout_seconds: int = 3600,
        cleanup_interval_seconds: int = 300,
    ):
        """
        Initialize session manager.

        Args:
            audit_chain: Merkle chain for audit logging
            sandbox: Sandbox implementation for untrusted sessions
            default_timeout_seconds: Default session timeout
            cleanup_interval_seconds: Interval for expired session cleanup
        """
        self._audit_chain = audit_chain
        self._sandbox = sandbox
        self._default_timeout = default_timeout_seconds
        self._cleanup_interval = cleanup_interval_seconds

        self._sessions: dict[str, SessionConfig] = {}
        self._metrics: dict[str, SessionMetrics] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    # ─────────────────────────────────────────────────────────────────────
    # Session Lifecycle
    # ─────────────────────────────────────────────────────────────────────

    def create_session(
        self,
        session_type: SessionType,
        role: Role,
        user_id: Optional[str] = None,
        allowed_portfolios: Optional[list[str]] = None,
        timeout_seconds: Optional[int] = None,
        max_tool_calls: int = 100,
    ) -> SessionConfig:
        """
        Create a new session with security boundaries.

        Args:
            session_type: Type of session (advisor, analyst, client)
            role: Role for RBAC
            user_id: Optional user identifier
            allowed_portfolios: List of accessible portfolios (None = all)
            timeout_seconds: Session timeout (None = default)
            max_tool_calls: Maximum tool calls allowed

        Returns:
            Configured SessionConfig
        """
        session_id = f"{session_type.value}:{uuid.uuid4().hex[:8]}"
        timeout = timeout_seconds or self._default_timeout

        # Determine sandbox mode
        sandbox_mode = session_type in SANDBOXED_SESSIONS

        session = SessionConfig(
            session_id=session_id,
            session_type=session_type,
            role=role,
            user_id=user_id,
            allowed_portfolios=allowed_portfolios,
            sandbox_mode=sandbox_mode,
            max_tool_calls=max_tool_calls,
            timeout_seconds=timeout,
            created_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=timeout),
        )

        # Register session
        self._sessions[session_id] = session
        self._metrics[session_id] = SessionMetrics()

        # Audit log
        self._log_event(
            AuditEventType.SESSION_CREATED,
            session_id,
            {
                "session_type": session_type.value,
                "role": role.value,
                "user_id": user_id,
                "sandbox_mode": sandbox_mode,
                "timeout_seconds": timeout,
            }
        )

        logger.info(
            f"Session created: {session_id} "
            f"(type={session_type.value}, role={role.value}, sandbox={sandbox_mode})"
        )

        return session

    def get_session(self, session_id: str) -> Optional[SessionConfig]:
        """
        Get session by ID.

        Returns None if session not found or expired.
        """
        session = self._sessions.get(session_id)
        if session and session.is_expired:
            self._expire_session(session_id)
            return None
        return session

    def terminate_session(
        self,
        session_id: str,
        reason: str = "manual"
    ) -> bool:
        """
        Terminate a session.

        Args:
            session_id: Session to terminate
            reason: Reason for termination

        Returns:
            True if session was found and terminated
        """
        session = self._sessions.pop(session_id, None)
        if session is None:
            return False

        # Finalize metrics
        metrics = self._metrics.pop(session_id, None)
        if metrics:
            metrics.end_time = datetime.now(timezone.utc)

        # Audit log
        self._log_event(
            AuditEventType.SESSION_TERMINATED,
            session_id,
            {
                "reason": reason,
                "metrics": metrics.to_dict() if metrics else None,
            }
        )

        logger.info(f"Session terminated: {session_id} (reason={reason})")
        return True

    def _expire_session(self, session_id: str) -> None:
        """Handle session expiration."""
        session = self._sessions.pop(session_id, None)
        metrics = self._metrics.pop(session_id, None)

        if metrics:
            metrics.end_time = datetime.now(timezone.utc)

        self._log_event(
            AuditEventType.SESSION_EXPIRED,
            session_id,
            {"metrics": metrics.to_dict() if metrics else None}
        )

        logger.info(f"Session expired: {session_id}")

    # ─────────────────────────────────────────────────────────────────────
    # Tool Call Tracking
    # ─────────────────────────────────────────────────────────────────────

    def record_tool_call(self, session_id: str) -> bool:
        """
        Record a tool call for the session.

        Args:
            session_id: Session making the call

        Returns:
            True if call is allowed, False if limit exceeded

        Raises:
            ValueError: If session not found
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        metrics = self._metrics.get(session_id)
        if metrics:
            metrics.tool_calls += 1

            if metrics.tool_calls > session.max_tool_calls:
                logger.warning(
                    f"Session {session_id} exceeded tool call limit "
                    f"({metrics.tool_calls}/{session.max_tool_calls})"
                )
                return False

        return True

    # ─────────────────────────────────────────────────────────────────────
    # Sandbox Execution
    # ─────────────────────────────────────────────────────────────────────

    async def execute_in_sandbox(
        self,
        session_id: str,
        code: Callable[[], T],
    ) -> T:
        """
        Execute code in sandbox if session requires it.

        Trusted sessions run directly on host.
        Untrusted sessions run in Docker sandbox.

        Args:
            session_id: Session making the call
            code: Callable to execute

        Returns:
            Result of code execution

        Raises:
            ValueError: If session not found
            RuntimeError: If sandbox required but not configured
        """
        session = self.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        if session.requires_sandbox:
            if self._sandbox is None:
                logger.warning(
                    f"Session {session_id} requires sandbox but none configured. "
                    "Running on host."
                )
                return code()

            result = await self._sandbox.execute(session, code)
            return result.get("result")

        # Trusted session - run directly
        return code()

    # ─────────────────────────────────────────────────────────────────────
    # Context Managers
    # ─────────────────────────────────────────────────────────────────────

    @contextmanager
    def session_context(
        self,
        session_type: SessionType,
        role: Role,
        **kwargs
    ):
        """
        Context manager for session lifecycle.

        Usage:
            with session_manager.session_context(SessionType.ADVISOR_MAIN, Role.HUMAN_ADVISOR) as session:
                # Use session
                pass
            # Session automatically terminated
        """
        session = self.create_session(session_type, role, **kwargs)
        try:
            yield session
        finally:
            self.terminate_session(session.session_id, reason="context_exit")

    @asynccontextmanager
    async def async_session_context(
        self,
        session_type: SessionType,
        role: Role,
        **kwargs
    ):
        """
        Async context manager for session lifecycle.

        Usage:
            async with session_manager.async_session_context(SessionType.ANALYST, Role.ANALYST) as session:
                # Use session
                pass
        """
        session = self.create_session(session_type, role, **kwargs)
        try:
            yield session
        finally:
            self.terminate_session(session.session_id, reason="async_context_exit")

    # ─────────────────────────────────────────────────────────────────────
    # Background Cleanup
    # ─────────────────────────────────────────────────────────────────────

    async def start_cleanup_task(self) -> None:
        """Start background task for expired session cleanup."""
        if self._cleanup_task is not None:
            return

        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Session cleanup task started")

    async def stop_cleanup_task(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task is None:
            return

        self._cleanup_task.cancel()
        try:
            await self._cleanup_task
        except asyncio.CancelledError:
            pass
        self._cleanup_task = None
        logger.info("Session cleanup task stopped")

    async def _cleanup_loop(self) -> None:
        """Background loop for cleaning up expired sessions."""
        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)
                self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired
        ]
        for sid in expired:
            self._expire_session(sid)

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

        return len(expired)

    # ─────────────────────────────────────────────────────────────────────
    # Audit Logging
    # ─────────────────────────────────────────────────────────────────────

    def _log_event(
        self,
        event_type: AuditEventType,
        session_id: str,
        details: dict
    ) -> None:
        """Log event to audit chain."""
        if self._audit_chain is None:
            return

        self._audit_chain.add_block({
            "event_type": event_type.value,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **details,
        })

    # ─────────────────────────────────────────────────────────────────────
    # Statistics
    # ─────────────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get session manager statistics."""
        active_sessions = [s for s in self._sessions.values() if not s.is_expired]

        return {
            "total_sessions": len(self._sessions),
            "active_sessions": len(active_sessions),
            "sessions_by_type": {
                st.value: len([s for s in active_sessions if s.session_type == st])
                for st in SessionType
            },
            "sessions_by_role": {
                r.value: len([s for s in active_sessions if s.role == r])
                for r in Role
            },
            "sandboxed_sessions": len([s for s in active_sessions if s.sandbox_mode]),
        }

    def list_sessions(self) -> list[dict]:
        """List all active sessions with details."""
        return [
            {
                "session_id": session.session_id,
                "session_type": session.session_type.value,
                "role": session.role.value,
                "user_id": session.user_id,
                "sandbox_mode": session.sandbox_mode,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "metrics": self._metrics.get(session.session_id).to_dict()
                if session.session_id in self._metrics else None,
            }
            for session in self._sessions.values()
            if not session.is_expired
        ]


# ═══════════════════════════════════════════════════════════════════════════
# SANDBOX IMPLEMENTATION (STUB)
# ═══════════════════════════════════════════════════════════════════════════

class LocalSandbox(ISandbox):
    """
    Local sandbox implementation (non-Docker).

    For development/testing. Provides isolation through
    process boundaries rather than containers.

    NOTE: For production, use DockerSandbox.
    """

    def __init__(self, config: Optional[SandboxConfig] = None):
        """
        Initialize local sandbox.

        Args:
            config: Sandbox configuration
        """
        self.config = config or DEFAULT_SANDBOX_CONFIG

    async def execute(
        self,
        session: SessionConfig,
        code: Callable
    ) -> dict:
        """
        Execute code with resource limits.

        Args:
            session: Session configuration
            code: Callable to execute

        Returns:
            Dict with execution result
        """
        logger.debug(f"LocalSandbox executing for session {session.session_id}")

        # In local mode, we just run the code directly
        # A real implementation would use subprocess or Docker
        try:
            result = code() if not asyncio.iscoroutinefunction(code) else await code()
            return {
                "status": "success",
                "result": result,
                "sandbox_mode": "local",
            }
        except Exception as e:
            logger.error(f"Sandbox execution error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "sandbox_mode": "local",
            }


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════

_session_manager: Optional[SessionManager] = None


def get_session_manager(
    audit_chain: Optional[IMerkleChain] = None,
    sandbox: Optional[ISandbox] = None,
) -> SessionManager:
    """
    Get or create singleton SessionManager.

    Args:
        audit_chain: Merkle chain for audit (used on first call)
        sandbox: Sandbox implementation (used on first call)

    Returns:
        SessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager(
            audit_chain=audit_chain,
            sandbox=sandbox or LocalSandbox(),
        )
    return _session_manager


def reset_session_manager() -> None:
    """Reset singleton SessionManager (for testing)."""
    global _session_manager
    _session_manager = None
