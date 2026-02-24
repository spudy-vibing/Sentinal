"""
SENTINEL INTERFACES — Abstract base classes for all components.

Implement these interfaces to ensure compatibility across the system.
Stubs are provided in stubs.py for testing before real implementations.

Reference: docs/IMPLEMENTATION_PLAN.md Phase 0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .schemas import (
        InputEvent,
        Portfolio,
        Transaction,
        DriftAgentOutput,
        TaxAgentOutput,
        RecommendedTrade,
        CoordinatorOutput,
        Scenario,
        UtilityScore,
        UtilityWeights,
        UIAction,
        AgentType,
        ClientProfile,
    )
    from .security import (
        Permission,
        SessionConfig,
        EncryptedField,
    )


# ═══════════════════════════════════════════════════════════════════════════
# GATEWAY
# ═══════════════════════════════════════════════════════════════════════════

class IGateway(ABC):
    """
    Gateway interface for event submission and routing.

    The Gateway is the single entry point for all system inputs.
    It validates events, manages per-session queues, and routes
    to appropriate handlers.
    """

    @abstractmethod
    async def submit(self, event: "InputEvent") -> str:
        """
        Submit event to gateway with validation.

        Args:
            event: Validated InputEvent (MarketEventInput, HeartbeatInput, etc.)

        Returns:
            event_id for tracking

        Raises:
            ValidationError: If event fails schema validation
        """
        pass

    @abstractmethod
    async def process_session(self, session_id: str) -> None:
        """
        Process events for a session serially.

        Events are dequeued by priority and routed to handlers.

        Args:
            session_id: Session identifier (e.g., "advisor:main")
        """
        pass

    @abstractmethod
    def register_handler(self, event_type: str, handler: callable) -> None:
        """
        Register a handler for an event type.

        Args:
            event_type: Event type string (e.g., "market_event")
            handler: Async callable to handle the event
        """
        pass


# ═══════════════════════════════════════════════════════════════════════════
# AGENTS
# ═══════════════════════════════════════════════════════════════════════════

class IAgent(ABC):
    """
    Base agent interface.

    All agents must implement this interface. Agents are specialized
    for specific analysis tasks (drift detection, tax optimization).

    SECURITY: Agents must use hub-and-spoke communication only.
    Direct agent-to-agent communication is FORBIDDEN.
    """

    @abstractmethod
    async def analyze(
        self,
        portfolio_id: str,
        context: dict
    ) -> object:
        """
        Run analysis and return structured output.

        Args:
            portfolio_id: Portfolio to analyze
            context: Additional context (market event, etc.)

        Returns:
            Structured output (DriftAgentOutput, TaxAgentOutput, etc.)
        """
        pass

    @abstractmethod
    def get_agent_type(self) -> "AgentType":
        """Return agent type identifier."""
        pass


class IDriftAgent(IAgent):
    """
    Drift Agent interface for portfolio drift detection.

    Responsibilities:
    - Detect concentration risks (positions > limit)
    - Calculate allocation drift from targets
    - Generate rebalancing recommendations

    Permissions required: READ_HOLDINGS
    """

    @abstractmethod
    async def analyze(
        self,
        portfolio_id: str,
        context: dict
    ) -> "DriftAgentOutput":
        """
        Analyze portfolio for drift and concentration risks.

        Args:
            portfolio_id: Portfolio to analyze
            context: Must include 'market_event' if triggered by market

        Returns:
            DriftAgentOutput with findings and recommendations
        """
        pass


class ITaxAgent(IAgent):
    """
    Tax Agent interface for tax optimization.

    Responsibilities:
    - Detect wash sale violations
    - Identify tax loss harvesting opportunities
    - Analyze tax impact of proposed trades

    Permissions required: READ_HOLDINGS, READ_TAX_LOTS
    """

    @abstractmethod
    async def analyze(
        self,
        portfolio_id: str,
        context: dict,
        proposed_trades: list["RecommendedTrade"]
    ) -> "TaxAgentOutput":
        """
        Analyze tax implications of portfolio and proposed trades.

        Args:
            portfolio_id: Portfolio to analyze
            context: Additional context
            proposed_trades: Trades proposed by Drift Agent

        Returns:
            TaxAgentOutput with violations, opportunities, recommendations
        """
        pass


class ICoordinator(ABC):
    """
    Coordinator Agent interface for multi-agent orchestration.

    Responsibilities:
    - Dispatch sub-agents in parallel
    - Detect conflicts between agent recommendations
    - Generate ranked scenarios with utility scoring
    - Handle UI actions (approve, what-if)

    SECURITY: Only Coordinator may dispatch agents.
    """

    @abstractmethod
    async def execute_analysis(
        self,
        portfolio_id: str,
        event: "InputEvent",
        client_profile: "ClientProfile"
    ) -> "CoordinatorOutput":
        """
        Execute full analysis pipeline.

        1. Dispatch Drift and Tax agents in parallel
        2. Detect conflicts between findings
        3. Generate resolution scenarios
        4. Score scenarios with utility function
        5. Return ranked recommendations

        Args:
            portfolio_id: Portfolio to analyze
            event: Triggering event
            client_profile: Client's risk profile and preferences

        Returns:
            CoordinatorOutput with scenarios and recommendations
        """
        pass

    @abstractmethod
    async def handle_ui_action(
        self,
        action: "UIAction"
    ) -> dict:
        """
        Handle action from Canvas UI.

        Args:
            action: UI action (approve, what-if, adjust)

        Returns:
            Response dict with status and any updated data
        """
        pass


# ═══════════════════════════════════════════════════════════════════════════
# STORAGE
# ═══════════════════════════════════════════════════════════════════════════

class IStorage(ABC):
    """
    Storage interface for portfolios and transactions.

    SECURITY:
    - All PII fields must be envelope-encrypted
    - Access must be checked via RBAC before returning data
    """

    @abstractmethod
    def get_portfolio(self, portfolio_id: str) -> "Portfolio":
        """
        Get portfolio by ID.

        Args:
            portfolio_id: Portfolio identifier

        Returns:
            Portfolio object

        Raises:
            NotFoundError: If portfolio doesn't exist
            PermissionError: If session lacks READ_HOLDINGS
        """
        pass

    @abstractmethod
    def get_transactions(
        self,
        portfolio_id: str,
        days: int = 30
    ) -> list["Transaction"]:
        """
        Get recent transactions for portfolio.

        Args:
            portfolio_id: Portfolio identifier
            days: Number of days to look back

        Returns:
            List of Transaction objects
        """
        pass

    @abstractmethod
    def save_recommendation(self, output: "CoordinatorOutput") -> None:
        """
        Persist coordinator output.

        Args:
            output: CoordinatorOutput to save
        """
        pass

    @abstractmethod
    def list_portfolios(self) -> list[str]:
        """
        List all portfolio IDs.

        Returns:
            List of portfolio ID strings
        """
        pass


# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT & MEMORY
# ═══════════════════════════════════════════════════════════════════════════

class IContextManager(ABC):
    """
    Context management interface for hot/cold memory split.

    Hot context: Expensive, token-limited, current analysis
    Cold memory: Cheap, unlimited, persistent decisions
    """

    @abstractmethod
    def add_to_context(self, item: dict, estimated_tokens: int) -> None:
        """
        Add item to hot context.

        Automatically flushes to cold memory if token limit exceeded.

        Args:
            item: Context item to add
            estimated_tokens: Estimated token count
        """
        pass

    @abstractmethod
    def get_context(self) -> list[dict]:
        """
        Get current hot context.

        Returns:
            List of context items
        """
        pass

    @abstractmethod
    def flush_to_memory(self) -> None:
        """
        Flush hot context to cold memory.

        Extracts key facts and persists before compacting.
        """
        pass

    @abstractmethod
    def search_memory(self, query: str, hybrid: bool = True) -> list[dict]:
        """
        Search cold memory.

        Args:
            query: Search query
            hybrid: Use both semantic and keyword search

        Returns:
            List of matching memory items
        """
        pass


# ═══════════════════════════════════════════════════════════════════════════
# MERKLE CHAIN
# ═══════════════════════════════════════════════════════════════════════════

class IMerkleChain(ABC):
    """
    Merkle chain interface for immutable audit trail.

    SECURITY:
    - Chain is append-only
    - All state transitions must be logged
    - Tampering is detectable via hash verification
    """

    @abstractmethod
    def add_block(self, data: dict) -> str:
        """
        Add block to chain.

        Args:
            data: Block data (event type, details, etc.)

        Returns:
            Block hash
        """
        pass

    @abstractmethod
    def verify_integrity(self) -> bool:
        """
        Verify chain integrity.

        Returns:
            True if chain is intact, False if tampering detected
        """
        pass

    @abstractmethod
    def get_root_hash(self) -> str:
        """
        Get current root hash.

        Returns:
            SHA-256 hash of latest block
        """
        pass

    @abstractmethod
    def get_block_count(self) -> int:
        """
        Get number of blocks in chain.

        Returns:
            Block count
        """
        pass

    @abstractmethod
    def export_chain(self) -> list[dict]:
        """
        Export full chain for audit.

        Returns:
            List of all blocks with hashes
        """
        pass


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

class IUtilityFunction(ABC):
    """
    Utility scoring interface for recommendation ranking.

    Scores scenarios on 5 dimensions:
    - Risk reduction
    - Tax savings
    - Goal alignment
    - Transaction cost
    - Urgency
    """

    @abstractmethod
    def score_scenario(
        self,
        scenario: "Scenario",
        portfolio: "Portfolio",
        weights: "UtilityWeights"
    ) -> "UtilityScore":
        """
        Score a single scenario.

        Args:
            scenario: Scenario to score
            portfolio: Portfolio context
            weights: Dimension weights (from client profile)

        Returns:
            UtilityScore with breakdown
        """
        pass

    @abstractmethod
    def rank_scenarios(
        self,
        scenarios: list["Scenario"],
        portfolio: "Portfolio",
        weights: "UtilityWeights"
    ) -> list["UtilityScore"]:
        """
        Score and rank multiple scenarios.

        Args:
            scenarios: Scenarios to rank
            portfolio: Portfolio context
            weights: Dimension weights

        Returns:
            List of UtilityScores, sorted by total_score descending
        """
        pass


# ═══════════════════════════════════════════════════════════════════════════
# CANVAS UI
# ═══════════════════════════════════════════════════════════════════════════

class ICanvasGenerator(ABC):
    """
    Canvas UI generation interface.

    Generates interactive HTML with a2ui-action attributes
    for advisor interaction.

    Reference: docs/DESIGN_FRAMEWORK.md
    """

    @abstractmethod
    def generate_html(
        self,
        scenarios: list["Scenario"],
        utility_scores: list["UtilityScore"],
        portfolio_id: str
    ) -> str:
        """
        Generate interactive Canvas HTML.

        Args:
            scenarios: Scenarios to display
            utility_scores: Scores for each scenario
            portfolio_id: Portfolio being analyzed

        Returns:
            HTML string with a2ui-action attributes
        """
        pass

    @abstractmethod
    def handle_action(
        self,
        action: "UIAction"
    ) -> dict:
        """
        Handle UI action.

        Args:
            action: Action from Canvas

        Returns:
            Response dict
        """
        pass


# ═══════════════════════════════════════════════════════════════════════════
# SECURITY (See security.py for full implementations)
# ═══════════════════════════════════════════════════════════════════════════

class ISecurityEnforcer(ABC):
    """
    Security enforcement interface.

    Reference: docs/SECURITY_PRACTICES.md §2
    """

    @abstractmethod
    def check_permission(
        self,
        session: "SessionConfig",
        required: "Permission"
    ) -> bool:
        """
        Check if session has required permission.

        Args:
            session: Current session config
            required: Permission to check

        Returns:
            True if permission held
        """
        pass

    @abstractmethod
    def enforce_permission(
        self,
        session: "SessionConfig",
        required: "Permission"
    ) -> None:
        """
        Enforce permission, raising if not held.

        Args:
            session: Current session config
            required: Permission to enforce

        Raises:
            PermissionError: If permission not held
        """
        pass


class ISandbox(ABC):
    """
    Sandbox execution interface.

    Reference: docs/SECURITY_PRACTICES.md §3.2
    """

    @abstractmethod
    async def execute(
        self,
        session: "SessionConfig",
        code: callable
    ) -> dict:
        """
        Execute code in sandbox if required by session type.

        Trusted sessions (advisor:main) run on host.
        Untrusted sessions (analyst, client) run in Docker.

        Args:
            session: Session configuration
            code: Callable to execute

        Returns:
            Execution result
        """
        pass


class IEncryption(ABC):
    """
    Encryption interface for field-level envelope encryption.

    Reference: docs/SECURITY_PRACTICES.md §1.1
    """

    @abstractmethod
    def encrypt_field(self, plaintext: str) -> "EncryptedField":
        """
        Encrypt a field using envelope encryption.

        - Generates unique DEK per field
        - Encrypts data with DEK (AES-256-GCM)
        - Encrypts DEK with master key

        Args:
            plaintext: Data to encrypt

        Returns:
            EncryptedField with ciphertext and encrypted DEK
        """
        pass

    @abstractmethod
    def decrypt_field(self, encrypted: "EncryptedField") -> str:
        """
        Decrypt an envelope-encrypted field.

        Args:
            encrypted: EncryptedField to decrypt

        Returns:
            Decrypted plaintext

        Raises:
            DecryptionError: If decryption fails
        """
        pass


# ═══════════════════════════════════════════════════════════════════════════
# STATE MACHINE
# ═══════════════════════════════════════════════════════════════════════════

class IStateMachine(ABC):
    """
    State machine interface for system state transitions.

    States: MONITOR → DETECT → ANALYZE → CONFLICT_RESOLUTION →
            RECOMMEND → APPROVED → EXECUTE → MONITOR

    All transitions are logged to Merkle chain.
    """

    @abstractmethod
    def get_state(self) -> str:
        """Get current state."""
        pass

    @abstractmethod
    def can_transition(self, to_state: str) -> bool:
        """Check if transition is valid."""
        pass

    @abstractmethod
    def transition(self, to_state: str, metadata: dict = None) -> bool:
        """
        Attempt state transition.

        Args:
            to_state: Target state
            metadata: Additional data for audit log

        Returns:
            True if transition succeeded

        Raises:
            InvalidTransitionError: If transition not allowed
        """
        pass

    @abstractmethod
    def get_transition_history(self) -> list[dict]:
        """Get history of state transitions."""
        pass


# ═══════════════════════════════════════════════════════════════════════════
# SKILL REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

class ISkillRegistry(ABC):
    """
    Skill registry interface for dynamic skill injection.

    Skills are loaded lazily based on context to save tokens.
    """

    @abstractmethod
    def discover_relevant_skills(
        self,
        context: dict,
        token_budget: int = 10_000
    ) -> list[str]:
        """
        Discover skills relevant to current context.

        Args:
            context: Current analysis context
            token_budget: Maximum tokens for skills

        Returns:
            List of skill names to inject
        """
        pass

    @abstractmethod
    def load_skill(self, skill_name: str) -> str:
        """
        Load skill content.

        Args:
            skill_name: Name of skill to load

        Returns:
            Skill content (markdown)
        """
        pass

    @abstractmethod
    def list_skills(self) -> list[dict]:
        """
        List all available skills with metadata.

        Returns:
            List of skill metadata dicts
        """
        pass


# ═══════════════════════════════════════════════════════════════════════════
# PERSONA ROUTER
# ═══════════════════════════════════════════════════════════════════════════

class IPersonaRouter(ABC):
    """
    Persona router interface for risk-profile-based routing.

    Different client profiles get different agent configurations.
    """

    @abstractmethod
    def get_persona(self, client_profile: "ClientProfile") -> dict:
        """
        Get persona configuration for client profile.

        Args:
            client_profile: Client's profile

        Returns:
            Dict with model, prompts, utility weights
        """
        pass

    @abstractmethod
    def build_prompt(
        self,
        base_prompt: str,
        client_profile: "ClientProfile"
    ) -> str:
        """
        Build personalized prompt.

        Args:
            base_prompt: Base agent prompt
            client_profile: Client's profile

        Returns:
            Prompt with persona suffix
        """
        pass
