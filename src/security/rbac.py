"""
SENTINEL RBAC SERVICE

Role-Based Access Control implementation with session tracking and audit logging.

Reference: docs/IMPLEMENTATION_PLAN.md Phase 2, Step 2.7
Reference: docs/SECURITY_PRACTICES.md
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Callable, TypeVar, ParamSpec
from functools import wraps
from dataclasses import dataclass, field

from src.contracts.interfaces import IMerkleChain, ISecurityEnforcer
from src.contracts.security import (
    Permission,
    Role,
    SessionConfig,
    SessionType,
    AuditEventType,
    SecurityContext,
    ROLE_PERMISSIONS,
    SANDBOXED_SESSIONS,
    create_advisor_session,
    create_analyst_session,
    create_agent_session,
)

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


# ═══════════════════════════════════════════════════════════════════════════
# ACCESS DECISION
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class AccessDecision:
    """Result of an access control check."""
    allowed: bool
    reason: str
    checked_permission: Permission
    session_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Convert to dictionary for audit logging."""
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "permission": self.checked_permission.name,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
        }


# ═══════════════════════════════════════════════════════════════════════════
# RBAC SERVICE
# ═══════════════════════════════════════════════════════════════════════════

class RBACService(ISecurityEnforcer):
    """
    Role-Based Access Control service.

    Provides:
    - Permission checking
    - Session validation
    - Audit logging of access decisions
    - Thread-local session context
    """

    def __init__(
        self,
        audit_chain: Optional[IMerkleChain] = None,
        default_session_timeout: int = 3600,  # 1 hour
    ):
        """
        Initialize RBAC service.

        Args:
            audit_chain: Merkle chain for audit logging
            default_session_timeout: Default session timeout in seconds
        """
        self._audit_chain = audit_chain
        self._default_timeout = default_session_timeout
        self._sessions: dict[str, SessionConfig] = {}
        self._active_context: Optional[SecurityContext] = None

    # ─────────────────────────────────────────────────────────────────────
    # ISecurityEnforcer Implementation
    # ─────────────────────────────────────────────────────────────────────

    def check_permission(
        self,
        session: SessionConfig,
        required: Permission
    ) -> bool:
        """
        Check if session has required permission.

        Args:
            session: Current session config
            required: Permission to check

        Returns:
            True if permission held
        """
        # Validate session is active
        if session.is_expired:
            self._log_decision(session, required, False, "Session expired")
            return False

        # Check permission
        has_perm = session.has_permission(required)

        # Log decision
        self._log_decision(
            session, required, has_perm,
            "Permission granted" if has_perm else "Permission denied"
        )

        return has_perm

    def enforce_permission(
        self,
        session: SessionConfig,
        required: Permission
    ) -> None:
        """
        Enforce permission, raising if not held.

        Args:
            session: Current session config
            required: Permission to enforce

        Raises:
            PermissionError: If permission not held
        """
        if not self.check_permission(session, required):
            raise PermissionError(
                f"Permission {required.name} required. "
                f"Session {session.session_id} has role {session.role.value}"
            )

    # ─────────────────────────────────────────────────────────────────────
    # Session Management
    # ─────────────────────────────────────────────────────────────────────

    def register_session(self, session: SessionConfig) -> None:
        """
        Register a session with the RBAC service.

        Args:
            session: Session to register
        """
        self._sessions[session.session_id] = session

        # Log session creation
        if self._audit_chain:
            self._audit_chain.add_block({
                "event_type": AuditEventType.SESSION_CREATED.value,
                "session_id": session.session_id,
                "session_type": session.session_type.value,
                "role": session.role.value,
                "user_id": session.user_id,
                "sandbox_mode": session.sandbox_mode,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        logger.info(
            f"Session registered: {session.session_id} "
            f"(role: {session.role.value}, sandbox: {session.sandbox_mode})"
        )

    def get_session(self, session_id: str) -> Optional[SessionConfig]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            SessionConfig if found and not expired
        """
        session = self._sessions.get(session_id)
        if session and session.is_expired:
            self.terminate_session(session_id, reason="expired")
            return None
        return session

    def terminate_session(self, session_id: str, reason: str = "manual") -> bool:
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

        # Log session termination
        event_type = (
            AuditEventType.SESSION_EXPIRED
            if reason == "expired"
            else AuditEventType.SESSION_TERMINATED
        )

        if self._audit_chain:
            self._audit_chain.add_block({
                "event_type": event_type.value,
                "session_id": session_id,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        logger.info(f"Session terminated: {session_id} (reason: {reason})")
        return True

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.

        Returns:
            Number of sessions removed
        """
        expired = [
            sid for sid, session in self._sessions.items()
            if session.is_expired
        ]
        for sid in expired:
            self.terminate_session(sid, reason="expired")
        return len(expired)

    # ─────────────────────────────────────────────────────────────────────
    # Context Management
    # ─────────────────────────────────────────────────────────────────────

    def create_context(self, session: SessionConfig) -> SecurityContext:
        """
        Create a security context for a session.

        Args:
            session: Session to create context for

        Returns:
            SecurityContext for the session
        """
        return SecurityContext(session=session, audit_chain=self._audit_chain)

    def get_current_context(self) -> Optional[SecurityContext]:
        """Get the currently active security context."""
        return self._active_context

    def set_current_context(self, context: Optional[SecurityContext]) -> None:
        """Set the currently active security context."""
        self._active_context = context

    # ─────────────────────────────────────────────────────────────────────
    # Session Factory Methods
    # ─────────────────────────────────────────────────────────────────────

    def create_advisor_session(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ) -> SessionConfig:
        """
        Create and register a trusted advisor session.

        Args:
            session_id: Session identifier
            user_id: Optional user ID

        Returns:
            Registered SessionConfig
        """
        session = create_advisor_session(session_id, user_id)
        session.expires_at = datetime.now(timezone.utc) + timedelta(seconds=self._default_timeout)
        self.register_session(session)
        return session

    def create_analyst_session(
        self,
        session_id: str,
        allowed_portfolios: list[str],
        user_id: Optional[str] = None
    ) -> SessionConfig:
        """
        Create and register a sandboxed analyst session.

        Args:
            session_id: Session identifier
            allowed_portfolios: List of accessible portfolio IDs
            user_id: Optional user ID

        Returns:
            Registered SessionConfig
        """
        session = create_analyst_session(session_id, allowed_portfolios, user_id)
        session.expires_at = datetime.now(timezone.utc) + timedelta(seconds=self._default_timeout)
        self.register_session(session)
        return session

    def create_agent_session(
        self,
        agent_type: str,
        parent_session_id: str
    ) -> SessionConfig:
        """
        Create a session for an agent within a parent session.

        Args:
            agent_type: Type of agent (drift, tax, coordinator)
            parent_session_id: Parent session ID

        Returns:
            Registered SessionConfig
        """
        parent = self.get_session(parent_session_id)
        if parent is None:
            raise ValueError(f"Parent session {parent_session_id} not found or expired")

        session = create_agent_session(agent_type, parent_session_id)

        # Inherit portfolio restrictions from parent
        session.allowed_portfolios = parent.allowed_portfolios

        # Agent sessions don't expire independently
        session.expires_at = parent.expires_at

        self.register_session(session)
        return session

    # ─────────────────────────────────────────────────────────────────────
    # Audit Logging
    # ─────────────────────────────────────────────────────────────────────

    def _log_decision(
        self,
        session: SessionConfig,
        permission: Permission,
        allowed: bool,
        reason: str
    ) -> None:
        """Log access decision to audit chain."""
        if not self._audit_chain:
            return

        event_type = (
            AuditEventType.ACCESS_GRANTED
            if allowed
            else AuditEventType.PERMISSION_DENIED
        )

        self._audit_chain.add_block({
            "event_type": event_type.value,
            "session_id": session.session_id,
            "role": session.role.value,
            "permission": permission.name,
            "allowed": allowed,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # ─────────────────────────────────────────────────────────────────────
    # Statistics
    # ─────────────────────────────────────────────────────────────────────

    def get_active_sessions(self) -> list[dict]:
        """Get list of all active sessions."""
        return [
            {
                "session_id": session.session_id,
                "session_type": session.session_type.value,
                "role": session.role.value,
                "user_id": session.user_id,
                "sandbox_mode": session.sandbox_mode,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            }
            for session in self._sessions.values()
            if not session.is_expired
        ]

    def get_session_count(self) -> int:
        """Get count of active sessions."""
        return len([s for s in self._sessions.values() if not s.is_expired])


# ═══════════════════════════════════════════════════════════════════════════
# DECORATORS FOR CLASS METHODS
# ═══════════════════════════════════════════════════════════════════════════

def with_session(session_provider: Callable[[], SessionConfig]):
    """
    Decorator to inject session into methods.

    The decorated method will have access to the session via `_session` attribute.

    Args:
        session_provider: Callable that returns the current session
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(self, *args: P.args, **kwargs: P.kwargs) -> T:
            self._session = session_provider()
            try:
                return func(self, *args, **kwargs)
            finally:
                self._session = None
        return wrapper
    return decorator


def require_permissions(*permissions: Permission):
    """
    Decorator to require multiple permissions.

    All permissions must be held for the method to execute.

    Usage:
        @require_permissions(Permission.READ_HOLDINGS, Permission.READ_TAX_LOTS)
        def get_tax_data(self, portfolio_id: str):
            ...
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(self, *args: P.args, **kwargs: P.kwargs) -> T:
            session: SessionConfig = getattr(self, "_session", None)

            if session is None:
                raise RuntimeError(
                    f"Method {func.__name__} requires RBAC but no session configured"
                )

            for perm in permissions:
                if not session.has_permission(perm):
                    raise PermissionError(
                        f"Permission {perm.name} required for {func.__name__}. "
                        f"Session {session.session_id} has role {session.role.value}"
                    )

            return func(self, *args, **kwargs)
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════

_rbac_service: Optional[RBACService] = None


def get_rbac_service(
    audit_chain: Optional[IMerkleChain] = None
) -> RBACService:
    """
    Get or create the singleton RBAC service.

    Args:
        audit_chain: Merkle chain for audit (only used on first call)

    Returns:
        RBACService instance
    """
    global _rbac_service
    if _rbac_service is None:
        _rbac_service = RBACService(audit_chain=audit_chain)
    return _rbac_service


def reset_rbac_service() -> None:
    """Reset the singleton RBAC service (for testing)."""
    global _rbac_service
    _rbac_service = None
