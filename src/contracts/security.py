"""
SENTINEL SECURITY CONTRACTS

Per docs/SECURITY_PRACTICES.md specifications.

This module defines:
- Permissions and roles for RBAC
- Session configuration for security boundaries
- Encryption field structures
- Audit event types

Reference: docs/IMPLEMENTATION_PLAN.md Phase 0, Step 0.5
"""

from __future__ import annotations

from enum import Enum, Flag, auto
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from functools import wraps

if TYPE_CHECKING:
    from .interfaces import IMerkleChain


# ═══════════════════════════════════════════════════════════════════════════
# PERMISSIONS & ROLES
# ═══════════════════════════════════════════════════════════════════════════

class Permission(Flag):
    """
    Fine-grained permissions for RBAC.

    Use Flag for composable permissions.

    Reference: docs/SECURITY_PRACTICES.md §2.1
    """
    NONE = 0

    # Read permissions
    READ_HOLDINGS = auto()          # View holdings (ticker, quantity, value)
    READ_TAX_LOTS = auto()          # View tax lot details
    READ_CLIENT_PII = auto()        # View client personal info (name, SSN)
    READ_TRANSACTIONS = auto()      # View transaction history
    READ_RECOMMENDATIONS = auto()   # View generated recommendations

    # Write permissions
    WRITE_RECOMMENDATIONS = auto()  # Generate recommendations
    APPROVE_TRADES = auto()         # Approve recommended trades
    EXECUTE_TRADES = auto()         # Execute approved trades

    # Admin permissions
    CONFIGURE_SYSTEM = auto()       # Modify system configuration
    MANAGE_USERS = auto()           # Create/modify users
    VIEW_AUDIT_LOG = auto()         # View full audit trail
    ADMIN = auto()                  # Full admin access

    # ─── Composite Permissions (Role Templates) ─────────────────────────────

    # Drift Agent: Holdings only, no PII, no tax lots
    DRIFT_AGENT = READ_HOLDINGS

    # Tax Agent: Holdings + tax lots, no PII
    TAX_AGENT = READ_HOLDINGS | READ_TAX_LOTS | READ_TRANSACTIONS

    # Coordinator: Can write recommendations
    COORDINATOR = READ_HOLDINGS | READ_TAX_LOTS | READ_TRANSACTIONS | WRITE_RECOMMENDATIONS

    # Human Advisor: Full read + approve
    HUMAN_ADVISOR = (
        READ_HOLDINGS |
        READ_TAX_LOTS |
        READ_CLIENT_PII |
        READ_TRANSACTIONS |
        READ_RECOMMENDATIONS |
        WRITE_RECOMMENDATIONS |
        APPROVE_TRADES
    )

    # Analyst: Read-only subset
    ANALYST = READ_HOLDINGS | READ_RECOMMENDATIONS

    # Client: Own portfolio only (enforced at session level)
    CLIENT = READ_HOLDINGS | READ_RECOMMENDATIONS


class Role(str, Enum):
    """
    System roles mapped to permission sets.

    Reference: docs/SECURITY_PRACTICES.md §2.1
    """
    DRIFT_AGENT = "drift_agent"
    TAX_AGENT = "tax_agent"
    COORDINATOR = "coordinator"
    HUMAN_ADVISOR = "human_advisor"
    ANALYST = "analyst"
    CLIENT = "client"
    SYSTEM = "system"
    ADMIN = "admin"


# Role to Permission mapping
ROLE_PERMISSIONS: dict[Role, Permission] = {
    Role.DRIFT_AGENT: Permission.DRIFT_AGENT,
    Role.TAX_AGENT: Permission.TAX_AGENT,
    Role.COORDINATOR: Permission.COORDINATOR,
    Role.HUMAN_ADVISOR: Permission.HUMAN_ADVISOR,
    Role.ANALYST: Permission.ANALYST,
    Role.CLIENT: Permission.CLIENT,
    Role.SYSTEM: Permission.NONE,
    Role.ADMIN: Permission.ADMIN | Permission.CONFIGURE_SYSTEM | Permission.MANAGE_USERS | Permission.VIEW_AUDIT_LOG,
}


# ═══════════════════════════════════════════════════════════════════════════
# SESSION SECURITY
# ═══════════════════════════════════════════════════════════════════════════

class SessionType(str, Enum):
    """
    Session types with execution boundaries.

    Reference: docs/SECURITY_PRACTICES.md §2.2
    """
    ADVISOR_MAIN = "advisor:main"    # Full access, host process
    ANALYST = "analyst"               # Read-only, Docker sandbox
    CLIENT_PORTAL = "client"          # Own portfolio only, Docker sandbox
    SYSTEM = "system"                 # Internal processes, host process


# Sessions requiring Docker sandbox
SANDBOXED_SESSIONS = {SessionType.ANALYST, SessionType.CLIENT_PORTAL}


class SessionConfig(BaseModel):
    """
    Security boundary for a session.

    Reference: docs/SECURITY_PRACTICES.md §2.2
    """
    session_id: str
    session_type: SessionType
    role: Role
    user_id: Optional[str] = None
    allowed_portfolios: Optional[list[str]] = None  # None = all (for advisors)
    sandbox_mode: bool = True
    max_tool_calls: int = Field(default=10, ge=1, le=100)
    timeout_seconds: int = Field(default=300, ge=30, le=3600)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None

    model_config = {"frozen": False}

    @property
    def permissions(self) -> Permission:
        """Get permissions for this session's role."""
        return ROLE_PERMISSIONS.get(self.role, Permission.NONE)

    def has_permission(self, perm: Permission) -> bool:
        """Check if session has a specific permission."""
        if self.role == Role.ADMIN:
            return True  # Admin has all permissions
        return bool(self.permissions & perm)

    def can_access_portfolio(self, portfolio_id: str) -> bool:
        """Check if session can access a specific portfolio."""
        if self.allowed_portfolios is None:
            return True  # Advisor has full access
        return portfolio_id in self.allowed_portfolios

    @property
    def requires_sandbox(self) -> bool:
        """Check if session requires Docker sandbox."""
        return self.session_type in SANDBOXED_SESSIONS

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def validate_access(self, portfolio_id: str, permission: Permission) -> None:
        """
        Validate session can access portfolio with permission.

        Raises:
            PermissionError: If access denied
        """
        if self.is_expired:
            raise PermissionError(f"Session {self.session_id} has expired")

        if not self.can_access_portfolio(portfolio_id):
            raise PermissionError(
                f"Session {self.session_id} cannot access portfolio {portfolio_id}"
            )

        if not self.has_permission(permission):
            raise PermissionError(
                f"Session {self.session_id} lacks permission {permission.name}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# RBAC DECORATOR
# ═══════════════════════════════════════════════════════════════════════════

def require_permission(perm: Permission):
    """
    Decorator to enforce RBAC on methods.

    Usage:
        @require_permission(Permission.READ_TAX_LOTS)
        def get_tax_lots(self, portfolio_id: str) -> list[TaxLot]:
            ...

    The decorated method's class must have:
        - self._session: SessionConfig
        - self._audit_chain: IMerkleChain (optional)

    Reference: docs/SECURITY_PRACTICES.md §2.1
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            session: SessionConfig = getattr(self, "_session", None)

            if session is None:
                raise RuntimeError(
                    f"Method {func.__name__} requires RBAC but no session configured"
                )

            if not session.has_permission(perm):
                # Log denial to audit chain if available
                audit_chain: Optional[IMerkleChain] = getattr(self, "_audit_chain", None)
                if audit_chain:
                    audit_chain.add_block({
                        "event_type": "permission_denied",
                        "session_id": session.session_id,
                        "role": session.role.value,
                        "required_permission": perm.name,
                        "attempted_action": func.__name__,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

                raise PermissionError(
                    f"Permission {perm.name} required for {func.__name__}. "
                    f"Session {session.session_id} has role {session.role.value}."
                )

            return func(self, *args, **kwargs)
        return wrapper
    return decorator


def require_portfolio_access(func):
    """
    Decorator to enforce portfolio-level access.

    The first positional argument must be portfolio_id.
    """
    @wraps(func)
    def wrapper(self, portfolio_id: str, *args, **kwargs):
        session: SessionConfig = getattr(self, "_session", None)

        if session is None:
            raise RuntimeError(
                f"Method {func.__name__} requires session but none configured"
            )

        if not session.can_access_portfolio(portfolio_id):
            raise PermissionError(
                f"Session {session.session_id} cannot access portfolio {portfolio_id}"
            )

        return func(self, portfolio_id, *args, **kwargs)
    return wrapper


# ═══════════════════════════════════════════════════════════════════════════
# ENCRYPTION
# ═══════════════════════════════════════════════════════════════════════════

class EncryptedField(BaseModel):
    """
    Envelope-encrypted field structure.

    AES-256-GCM encryption with per-field DEK.

    Reference: docs/SECURITY_PRACTICES.md §1.1
    """
    ciphertext: bytes
    encrypted_dek: bytes  # DEK encrypted with master key
    nonce: bytes          # 12 bytes for GCM
    tag: bytes            # 16 bytes authentication tag
    key_version: int = Field(default=1, ge=1)

    model_config = {"arbitrary_types_allowed": True}


class EncryptionConfig(BaseModel):
    """Encryption configuration parameters."""
    algorithm: str = "AES-256-GCM"
    kdf_iterations: int = Field(default=256000, ge=100000)
    key_derivation: str = "PBKDF2-SHA256"
    nonce_length: int = Field(default=12, ge=12)
    tag_length: int = Field(default=16, ge=16)


# ═══════════════════════════════════════════════════════════════════════════
# AUDIT TRAIL
# ═══════════════════════════════════════════════════════════════════════════

class AuditEventType(str, Enum):
    """
    Types of events logged to Merkle chain.

    Reference: docs/SECURITY_PRACTICES.md §4.1
    """
    # System events
    SYSTEM_INITIALIZED = "system_initialized"
    SYSTEM_SHUTDOWN = "system_shutdown"

    # Session events
    SESSION_CREATED = "session_created"
    SESSION_TERMINATED = "session_terminated"
    SESSION_EXPIRED = "session_expired"

    # Market events
    MARKET_EVENT_DETECTED = "market_event_detected"
    HEARTBEAT_TRIGGERED = "heartbeat_triggered"
    CRON_JOB_EXECUTED = "cron_job_executed"
    WEBHOOK_RECEIVED = "webhook_received"

    # State transitions
    STATE_TRANSITION = "state_transition"

    # Agent events
    AGENT_INVOKED = "agent_invoked"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"

    # Conflict & recommendation events
    CONFLICT_DETECTED = "conflict_detected"
    SCENARIO_GENERATED = "scenario_generated"
    RECOMMENDATION_GENERATED = "recommendation_generated"

    # Human interaction events
    HUMAN_DECISION = "human_decision"
    UI_ACTION = "ui_action"

    # Trade events
    TRADE_APPROVED = "trade_approved"
    TRADE_REJECTED = "trade_rejected"
    TRADE_EXECUTED = "trade_executed"

    # Security events
    PERMISSION_DENIED = "permission_denied"
    ACCESS_GRANTED = "access_granted"
    ENCRYPTION_KEY_ROTATED = "encryption_key_rotated"


class AuditEvent(BaseModel):
    """
    Single audit event for Merkle chain.

    Reference: docs/SECURITY_PRACTICES.md §4.1
    """
    event_id: str
    event_type: AuditEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: str
    actor: str  # Agent name, user ID, or "system"
    action: str
    resource: Optional[str] = None  # Portfolio ID, scenario ID, etc.
    details: dict = Field(default_factory=dict)
    previous_hash: str
    current_hash: str

    model_config = {"frozen": True}  # Immutable after creation


# ═══════════════════════════════════════════════════════════════════════════
# SECURITY CONTEXT
# ═══════════════════════════════════════════════════════════════════════════

class SecurityContext:
    """
    Security context for dependency injection.

    Provides session and audit chain to components that need them.
    """

    def __init__(
        self,
        session: SessionConfig,
        audit_chain: Optional["IMerkleChain"] = None
    ):
        self.session = session
        self.audit_chain = audit_chain

    def require_permission(self, perm: Permission) -> None:
        """Raise PermissionError if permission not held."""
        if not self.session.has_permission(perm):
            self._log_denial(perm)
            raise PermissionError(
                f"Permission {perm.name} required. "
                f"Session {self.session.session_id} has role {self.session.role.value}"
            )

    def require_portfolio_access(self, portfolio_id: str) -> None:
        """Raise PermissionError if portfolio not accessible."""
        if not self.session.can_access_portfolio(portfolio_id):
            raise PermissionError(
                f"Session {self.session.session_id} cannot access portfolio {portfolio_id}"
            )

    def log_access(self, resource: str, action: str) -> None:
        """Log access attempt to audit chain."""
        if self.audit_chain:
            self.audit_chain.add_block({
                "event_type": AuditEventType.ACCESS_GRANTED.value,
                "session_id": self.session.session_id,
                "actor": self.session.user_id or self.session.role.value,
                "resource": resource,
                "action": action,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

    def _log_denial(self, perm: Permission) -> None:
        """Log permission denial to audit chain."""
        if self.audit_chain:
            self.audit_chain.add_block({
                "event_type": AuditEventType.PERMISSION_DENIED.value,
                "session_id": self.session.session_id,
                "actor": self.session.user_id or self.session.role.value,
                "required_permission": perm.name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })


# ═══════════════════════════════════════════════════════════════════════════
# SANDBOX CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

class SandboxConfig(BaseModel):
    """
    Docker sandbox configuration.

    Reference: docs/SECURITY_PRACTICES.md §3.2
    """
    image: str = "sentinel-agent-runtime"
    memory_limit: str = "512m"
    cpu_quota: int = Field(default=50000, ge=10000)  # 0.5 CPU
    cpu_period: int = Field(default=100000)
    network_mode: str = "none"  # No network access
    read_only_root: bool = True
    auto_remove: bool = True
    workspace_path: str = "/workspace"


# Default sandbox config per SECURITY_PRACTICES.md
DEFAULT_SANDBOX_CONFIG = SandboxConfig()


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def create_advisor_session(
    session_id: str,
    user_id: Optional[str] = None
) -> SessionConfig:
    """Create a trusted advisor session."""
    return SessionConfig(
        session_id=session_id,
        session_type=SessionType.ADVISOR_MAIN,
        role=Role.HUMAN_ADVISOR,
        user_id=user_id,
        allowed_portfolios=None,  # Full access
        sandbox_mode=False
    )


def create_analyst_session(
    session_id: str,
    allowed_portfolios: list[str],
    user_id: Optional[str] = None
) -> SessionConfig:
    """Create a sandboxed analyst session."""
    return SessionConfig(
        session_id=session_id,
        session_type=SessionType.ANALYST,
        role=Role.ANALYST,
        user_id=user_id,
        allowed_portfolios=allowed_portfolios,
        sandbox_mode=True
    )


def create_agent_session(
    agent_type: str,
    parent_session_id: str
) -> SessionConfig:
    """Create session for an agent within a parent session."""
    role_map = {
        "drift": Role.DRIFT_AGENT,
        "tax": Role.TAX_AGENT,
        "coordinator": Role.COORDINATOR,
    }
    role = role_map.get(agent_type, Role.SYSTEM)

    return SessionConfig(
        session_id=f"{parent_session_id}:agent:{agent_type}",
        session_type=SessionType.SYSTEM,
        role=role,
        allowed_portfolios=None,  # Inherits from parent
        sandbox_mode=False  # Agents run in host process
    )
