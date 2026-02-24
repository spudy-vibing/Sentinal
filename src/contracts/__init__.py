"""
SENTINEL CONTRACTS PACKAGE

Central export point for all contracts, schemas, interfaces, and stubs.

Usage:
    from src.contracts import Portfolio, Holding, DriftAgentOutput
    from src.contracts import IGateway, IDriftAgent, ICoordinator
    from src.contracts import Permission, SessionConfig, require_permission
    from src.contracts import StubDriftAgent, StubStorage, StubMerkleChain
"""

# ═══════════════════════════════════════════════════════════════════════════
# SCHEMAS — Pydantic models
# ═══════════════════════════════════════════════════════════════════════════

from .schemas import (
    # Enums
    EventType,
    AgentType,
    RiskProfile,
    TradeAction,
    SystemState,
    Severity,
    DriftDirection,
    TaxOpportunityType,
    CronJobType,
    # Input Events
    InputEvent,
    MarketEventInput,
    HeartbeatInput,
    CronJobInput,
    WebhookInput,
    AgentMessageInput,
    # Data Models
    TaxLot,
    Holding,
    TargetAllocation,
    ClientProfile,
    Portfolio,
    Transaction,
    # Agent Outputs
    ConcentrationRisk,
    DriftMetric,
    RecommendedTrade,
    DriftAgentOutput,
    WashSaleViolation,
    TaxOpportunity,
    TaxAgentOutput,
    # Utility Scoring
    UtilityWeights,
    DimensionScore,
    UtilityScore,
    UTILITY_WEIGHTS_BY_PROFILE,
    # Coordinator / Scenarios
    ActionStep,
    Scenario,
    ConflictInfo,
    CoordinatorOutput,
    # Canvas UI
    UIActionType,
    UIAction,
    CanvasState,
    # Market Data
    MarketDataPoint,
    SectorPerformance,
    PricePoint,
    MarketData,
)

# ═══════════════════════════════════════════════════════════════════════════
# INTERFACES — Abstract Base Classes
# ═══════════════════════════════════════════════════════════════════════════

from .interfaces import (
    # Core
    IGateway,
    IAgent,
    IDriftAgent,
    ITaxAgent,
    ICoordinator,
    # Storage
    IStorage,
    IContextManager,
    IMerkleChain,
    # Scoring
    IUtilityFunction,
    # UI
    ICanvasGenerator,
    # Security
    ISecurityEnforcer,
    ISandbox,
    IEncryption,
    # State
    IStateMachine,
    # Skills & Routing
    ISkillRegistry,
    IPersonaRouter,
)

# ═══════════════════════════════════════════════════════════════════════════
# SECURITY — RBAC, Sessions, Encryption
# ═══════════════════════════════════════════════════════════════════════════

from .security import (
    # Permissions & Roles
    Permission,
    Role,
    ROLE_PERMISSIONS,
    # Sessions
    SessionType,
    SessionConfig,
    SANDBOXED_SESSIONS,
    # Encryption
    EncryptedField,
    EncryptionConfig,
    # Audit
    AuditEventType,
    AuditEvent,
    # Context
    SecurityContext,
    # Sandbox
    SandboxConfig,
    DEFAULT_SANDBOX_CONFIG,
    # Decorators
    require_permission,
    require_portfolio_access,
    # Helpers
    create_advisor_session,
    create_analyst_session,
    create_agent_session,
)

# ═══════════════════════════════════════════════════════════════════════════
# STUBS — Mock Implementations for Testing
# ═══════════════════════════════════════════════════════════════════════════

from .stubs import (
    # Core
    StubGateway,
    StubDriftAgent,
    StubTaxAgent,
    StubCoordinator,
    # Storage
    StubStorage,
    StubMerkleChain,
    StubContextManager,
    # Scoring
    StubUtilityFunction,
    # Security
    StubSecurityEnforcer,
    StubSandbox,
    StubEncryption,
    # State
    StubStateMachine,
    # Skills & Routing
    StubSkillRegistry,
    StubPersonaRouter,
    # UI
    StubCanvasGenerator,
)

# ═══════════════════════════════════════════════════════════════════════════
# VERSION
# ═══════════════════════════════════════════════════════════════════════════

__version__ = "0.1.0"

__all__ = [
    # Schemas
    "EventType",
    "AgentType",
    "RiskProfile",
    "TradeAction",
    "SystemState",
    "Severity",
    "DriftDirection",
    "TaxOpportunityType",
    "CronJobType",
    "InputEvent",
    "MarketEventInput",
    "HeartbeatInput",
    "CronJobInput",
    "WebhookInput",
    "AgentMessageInput",
    "TaxLot",
    "Holding",
    "TargetAllocation",
    "ClientProfile",
    "Portfolio",
    "Transaction",
    "ConcentrationRisk",
    "DriftMetric",
    "RecommendedTrade",
    "DriftAgentOutput",
    "WashSaleViolation",
    "TaxOpportunity",
    "TaxAgentOutput",
    "UtilityWeights",
    "DimensionScore",
    "UtilityScore",
    "UTILITY_WEIGHTS_BY_PROFILE",
    "ActionStep",
    "Scenario",
    "ConflictInfo",
    "CoordinatorOutput",
    "UIActionType",
    "UIAction",
    "CanvasState",
    "MarketDataPoint",
    "SectorPerformance",
    "PricePoint",
    "MarketData",
    # Interfaces
    "IGateway",
    "IAgent",
    "IDriftAgent",
    "ITaxAgent",
    "ICoordinator",
    "IStorage",
    "IContextManager",
    "IMerkleChain",
    "IUtilityFunction",
    "ICanvasGenerator",
    "ISecurityEnforcer",
    "ISandbox",
    "IEncryption",
    "IStateMachine",
    "ISkillRegistry",
    "IPersonaRouter",
    # Security
    "Permission",
    "Role",
    "ROLE_PERMISSIONS",
    "SessionType",
    "SessionConfig",
    "SANDBOXED_SESSIONS",
    "EncryptedField",
    "EncryptionConfig",
    "AuditEventType",
    "AuditEvent",
    "SecurityContext",
    "SandboxConfig",
    "DEFAULT_SANDBOX_CONFIG",
    "require_permission",
    "require_portfolio_access",
    "create_advisor_session",
    "create_analyst_session",
    "create_agent_session",
    # Stubs
    "StubGateway",
    "StubDriftAgent",
    "StubTaxAgent",
    "StubCoordinator",
    "StubStorage",
    "StubMerkleChain",
    "StubContextManager",
    "StubUtilityFunction",
    "StubSecurityEnforcer",
    "StubSandbox",
    "StubEncryption",
    "StubStateMachine",
    "StubSkillRegistry",
    "StubPersonaRouter",
    "StubCanvasGenerator",
]
