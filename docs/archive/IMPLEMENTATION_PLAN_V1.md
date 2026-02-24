# Sentinel Implementation Plan

## Parallel Execution Strategy

This plan enables **multiple agents to work simultaneously** by:
1. Defining API contracts and interfaces upfront
2. Creating stubs for dependent components
3. Organizing work into independent workstreams
4. Specifying clear integration points

---

## Security Requirements (Cross-Cutting)

> **Reference**: See `docs/SECURITY_PRACTICES.md` for complete security specifications.

Security is not a phase — it's embedded in every step. All implementations MUST follow these requirements:

### Mandatory Security Patterns

| Category | Requirement | Enforced In |
|----------|-------------|-------------|
| **Encryption at Rest** | AES-256-GCM envelope encryption for PII | Phase 1 (Step 1.7) |
| **Key Management** | Master key in `.env` only, never hardcoded | All phases |
| **RBAC** | `@require_permission` decorator on all data access | Phase 2 (Step 2.7) |
| **Session Isolation** | Docker sandbox for untrusted sessions | Phase 2 (Step 2.8) |
| **Hub-and-Spoke** | Agents NEVER communicate directly | Phase 2-3 (All agents) |
| **Audit Trail** | Merkle chain logs all state transitions | Phase 1 (Step 1.8) |
| **Input Validation** | Pydantic schemas at Gateway | Phase 1 (Step 1.6) |
| **Output Sanitization** | HTML sanitized, PII redacted from logs | Phase 3 (Step 3.5) |

### Security Checkpoints by Phase

```
Phase 0: ✓ Security enums in schemas (SessionType, Permission)
Phase 1: ✓ Encryption module    ✓ Merkle chain    ✓ Parameterized SQL
Phase 2: ✓ RBAC decorators      ✓ Docker sandbox  ✓ Agent isolation
Phase 3: ✓ Hub-and-spoke only   ✓ HTML sanitize   ✓ No raw PII in Canvas
Phase 4: ✓ Merkle verification  ✓ Security tests  ✓ Compliance checklist
```

### Field-Level Encryption Requirements

| Data Type | Encryption | Agent Access |
|-----------|------------|--------------|
| Client PII (name, SSN, address) | **Required** | Human Advisor only |
| Financial constraints | **Required** | Coordinator only |
| Tax lot details | **Required** | Tax Agent, Coordinator |
| Holdings (ticker, quantity) | Not required | All agents |
| Recommendations | Not required | All agents |

### RBAC Permission Matrix

| Role | READ_HOLDINGS | READ_TAX_LOTS | READ_CLIENT_PII | WRITE_RECS | APPROVE_TRADES |
|------|---------------|---------------|-----------------|------------|----------------|
| `DRIFT_AGENT` | ✓ | - | - | - | - |
| `TAX_AGENT` | ✓ | ✓ | - | - | - |
| `COORDINATOR` | ✓ | ✓ | - | ✓ | - |
| `HUMAN_ADVISOR` | ✓ | ✓ | ✓ | ✓ | ✓ |

### Security Anti-Patterns (FORBIDDEN)

```python
# ❌ FORBIDDEN: Direct agent communication
drift_agent.send_message(tax_agent, data)

# ❌ FORBIDDEN: Hardcoded secrets
MASTER_KEY = "abc123..."

# ❌ FORBIDDEN: String concatenation in SQL
cursor.execute(f"SELECT * FROM holdings WHERE ticker='{ticker}'")

# ❌ FORBIDDEN: Unvalidated input to agents
agent.analyze(request.body)  # No schema validation

# ❌ FORBIDDEN: PII in logs
logger.info(f"Processing client {client.ssn}")
```

### Security Test Requirements

Each phase must pass these security tests before completion:

| Phase | Test | Command |
|-------|------|---------|
| 1 | Encryption round-trip | `pytest tests/test_encryption.py` |
| 1 | Merkle tamper detection | `pytest tests/test_merkle.py` |
| 2 | RBAC enforcement | `pytest tests/test_rbac.py` |
| 2 | Session isolation | `pytest tests/test_sessions.py` |
| 3 | Hub-and-spoke compliance | `pytest tests/test_agent_communication.py` |
| 4 | Full security audit | `pytest tests/test_security.py -v` |

---

## Progress Tracker

### Phase Overview

| Phase | Name | Status | Workstreams | Dependencies |
|-------|------|--------|-------------|--------------|
| 0 | Contracts & Interfaces | 🟢 Complete | 1 | None |
| 1 | Foundation | 🟢 Complete | 3 | Phase 0 ✓ |
| 2 | Core Agents | 🟢 Complete | 2 | Phase 1 ✓ |
| 3 | Orchestration | 🟢 Complete | 2 | Phase 2 ✓ |
| 4 | Integration & Demo | 🟢 Complete | 2 | Phase 3 ✓ |

### Detailed Progress

```
Legend: 🔴 Not Started | 🟡 In Progress | 🟢 Complete | ⏸️ Blocked
```

#### Phase 0: Contracts & Interfaces ✅
| Step | Task | Status | Assigned | Notes |
|------|------|--------|----------|-------|
| 0.1 | Define all Pydantic schemas | 🟢 | Claude | `src/contracts/schemas.py` |
| 0.2 | Define agent input/output contracts | 🟢 | Claude | In schemas.py |
| 0.3 | Define API interfaces | 🟢 | Claude | `src/contracts/interfaces.py` |
| 0.4 | Create stub implementations | 🟢 | Claude | `src/contracts/stubs.py` |
| 0.5 | Define security contracts (RBAC, Session, Encryption) | 🟢 | Claude | `src/contracts/security.py` |

#### Phase 1: Foundation
| Step | Task | Status | Assigned | Workstream |
|------|------|--------|----------|------------|
| 1.1 | Project setup (pyproject.toml) | 🟢 | Claude | Setup |
| 1.2 | Data models (Portfolio, Holding, TaxLot) | 🟢 | Claude | Data ✓ |
| 1.3 | Synthetic portfolios JSON | 🟢 | Claude | Data ✓ |
| 1.4 | Market data cache | 🟢 | Claude | Data ✓ |
| 1.5 | Gateway core | 🟢 | Claude | Gateway ✓ |
| 1.6 | Event schemas (Pydantic) | 🟢 | Claude | Gateway ✓ |
| 1.7 | SQLite + encryption | 🟢 | Claude | Storage ✓ |
| 1.8 | Merkle chain foundation | 🟢 | Claude | Storage ✓ |
| 1.9 | Context manager (hot/cold) | 🟢 | Claude | Memory ✓ |
| 1.10 | ChromaDB setup | 🟢 | Claude | Memory ✓ |

#### Phase 2: Core Agents ✅
| Step | Task | Status | Assigned | Workstream |
|------|------|--------|----------|------------|
| 2.1 | Base agent class | 🟢 | Claude | Agents ✓ |
| 2.2 | Drift agent | 🟢 | Claude | Agents ✓ |
| 2.3 | Tax agent | 🟢 | Claude | Agents ✓ |
| 2.4 | Skill registry | 🟢 | Claude | Agents ✓ |
| 2.5 | State machine | 🟢 | Claude | State ✓ |
| 2.6 | Utility function | 🟢 | Claude | State ✓ |
| 2.7 | RBAC system | 🟢 | Claude | Security ✓ |
| 2.8 | Session boundaries | 🟢 | Claude | Security ✓ |

#### Phase 3: Orchestration ✅
| Step | Task | Status | Assigned | Workstream |
|------|------|--------|----------|------------|
| 3.1 | Coordinator agent | 🟢 | Claude | Orchestration |
| 3.2 | Parallel dispatch (asyncio) | 🟢 | Claude | Orchestration |
| 3.3 | Conflict resolution | 🟢 | Claude | Orchestration |
| 3.4 | Persona router | 🟢 | Claude | Orchestration |
| 3.5 | Canvas generator | 🟢 | Claude | UI |
| 3.6 | Rich CLI | 🔴 | - | UI |
| 3.7 | a2ui-action handlers | 🟢 | Claude | UI |

#### Phase 4: Integration & Demo ✅
| Step | Task | Status | Assigned | Workstream |
|------|------|--------|----------|------------|
| 4.1 | Golden path demo | 🟢 | Claude | Demo |
| 4.2 | Heartbeat demo | 🟢 | Claude | Demo |
| 4.3 | Webhook demo | 🟢 | Claude | Demo |
| 4.4 | Canvas HTML output | 🟢 | Claude | Demo |
| 4.5 | End-to-end tests | 🟢 | Claude | Testing |
| 4.6 | Merkle verification | 🟢 | Claude | Testing |
| 4.7 | Security compliance tests | 🔴 | - | Security |
| 4.8 | Documentation polish | 🔴 | - | Docs |

---

## Phase 0: Contracts & Interfaces

**Purpose**: Define all interfaces upfront so workstreams can proceed independently.

**Duration**: Must complete before other phases begin.

### Step 0.1: Pydantic Schemas

Create `src/contracts/schemas.py`:

```python
"""
SENTINEL CONTRACTS — All Pydantic schemas for system-wide type safety.
Import this file in any module that needs shared types.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime
from enum import Enum

# ═══════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════

class EventType(str, Enum):
    MARKET_EVENT = "market_event"
    HEARTBEAT = "heartbeat"
    CRON = "cron"
    WEBHOOK = "webhook"
    AGENT_MESSAGE = "agent_message"

class SessionType(str, Enum):
    ADVISOR_MAIN = "advisor:main"
    ANALYST = "analyst"
    CLIENT_PORTAL = "client"
    SYSTEM = "system"

class AgentType(str, Enum):
    COORDINATOR = "coordinator"
    DRIFT = "drift"
    TAX = "tax"

class RiskProfile(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE_GROWTH = "moderate_growth"
    AGGRESSIVE = "aggressive"

class TradeAction(str, Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class SystemState(str, Enum):
    MONITOR = "monitor"
    DETECT = "detect"
    ANALYZE = "analyze"
    CONFLICT_RESOLUTION = "conflict_resolution"
    RECOMMEND = "recommend"
    APPROVED = "approved"
    EXECUTE = "execute"

# ═══════════════════════════════════════════════════════════════════════════
# INPUT EVENTS (Gateway)
# ═══════════════════════════════════════════════════════════════════════════

class InputEvent(BaseModel):
    """Base class for all gateway inputs"""
    event_id: str
    event_type: EventType
    timestamp: datetime
    session_id: str
    priority: int = Field(ge=0, le=10, default=5)

class MarketEventInput(InputEvent):
    event_type: Literal[EventType.MARKET_EVENT] = EventType.MARKET_EVENT
    affected_sectors: list[str]
    magnitude: float = Field(ge=-1.0, le=1.0)
    affected_tickers: list[str] = []
    description: str

class HeartbeatInput(InputEvent):
    event_type: Literal[EventType.HEARTBEAT] = EventType.HEARTBEAT
    portfolio_ids: list[str]

class CronJobInput(InputEvent):
    event_type: Literal[EventType.CRON] = EventType.CRON
    job_type: Literal["daily_review", "eod_tax", "quarterly_rebalance"]
    instructions: str

class WebhookInput(InputEvent):
    event_type: Literal[EventType.WEBHOOK] = EventType.WEBHOOK
    source: str
    payload: dict

# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════

class TaxLot(BaseModel):
    """Individual tax lot for a holding"""
    lot_id: str
    purchase_date: datetime
    purchase_price: float
    quantity: float
    cost_basis: float

class Holding(BaseModel):
    """Single position in a portfolio"""
    ticker: str
    quantity: float
    current_price: float
    market_value: float
    portfolio_weight: float
    cost_basis: float
    unrealized_gain_loss: float
    tax_lots: list[TaxLot] = []
    sector: str
    asset_class: str

class TargetAllocation(BaseModel):
    """Target allocation percentages"""
    us_equities: float
    international_equities: float
    fixed_income: float
    alternatives: float
    structured_products: float
    cash: float

class ClientProfile(BaseModel):
    """Client risk profile and preferences"""
    client_id: str
    risk_tolerance: RiskProfile
    tax_sensitivity: float = Field(ge=0, le=1)
    concentration_limit: float = Field(ge=0, le=1, default=0.15)
    rebalancing_frequency: str = "quarterly"

class Portfolio(BaseModel):
    """Complete portfolio snapshot"""
    portfolio_id: str
    client_id: str
    name: str
    aum_usd: float
    holdings: list[Holding]
    target_allocation: TargetAllocation
    client_profile: ClientProfile
    last_rebalance: datetime
    cash_available: float

class Transaction(BaseModel):
    """Historical transaction record"""
    transaction_id: str
    portfolio_id: str
    ticker: str
    action: TradeAction
    quantity: float
    price: float
    timestamp: datetime
    wash_sale_disallowed: float = 0

# ═══════════════════════════════════════════════════════════════════════════
# AGENT OUTPUTS
# ═══════════════════════════════════════════════════════════════════════════

class ConcentrationRisk(BaseModel):
    """Detected concentration risk"""
    ticker: str
    current_weight: float
    limit: float
    excess: float
    severity: Literal["low", "medium", "high", "critical"]

class DriftMetric(BaseModel):
    """Allocation drift measurement"""
    asset_class: str
    target_weight: float
    current_weight: float
    drift_pct: float
    drift_direction: Literal["over", "under"]

class RecommendedTrade(BaseModel):
    """Single trade recommendation"""
    ticker: str
    action: TradeAction
    quantity: float
    rationale: str
    urgency: int = Field(ge=1, le=10)
    estimated_tax_impact: float = 0

class DriftAgentOutput(BaseModel):
    """Structured output from Drift Agent"""
    portfolio_id: str
    analysis_timestamp: datetime
    drift_detected: bool
    concentration_risks: list[ConcentrationRisk]
    drift_metrics: list[DriftMetric]
    recommended_trades: list[RecommendedTrade]
    urgency_score: int = Field(ge=1, le=10)
    reasoning: str

class WashSaleViolation(BaseModel):
    """Detected wash sale issue"""
    ticker: str
    prior_sale_date: datetime
    days_since_sale: int
    disallowed_loss: float
    recommendation: str

class TaxOpportunity(BaseModel):
    """Tax optimization opportunity"""
    ticker: str
    opportunity_type: Literal["harvest_loss", "harvest_gain", "lot_selection"]
    estimated_benefit: float
    action_required: str

class TaxAgentOutput(BaseModel):
    """Structured output from Tax Agent"""
    portfolio_id: str
    analysis_timestamp: datetime
    wash_sale_violations: list[WashSaleViolation]
    tax_opportunities: list[TaxOpportunity]
    proposed_trades_analysis: list[dict]
    total_tax_impact: float
    recommendations: list[str]
    reasoning: str

# ═══════════════════════════════════════════════════════════════════════════
# UTILITY SCORING
# ═══════════════════════════════════════════════════════════════════════════

class UtilityWeights(BaseModel):
    """Weights for utility function dimensions"""
    risk_reduction: float = Field(ge=0, le=1)
    tax_savings: float = Field(ge=0, le=1)
    goal_alignment: float = Field(ge=0, le=1)
    transaction_cost: float = Field(ge=0, le=1)
    urgency: float = Field(ge=0, le=1)

class DimensionScore(BaseModel):
    """Score for single utility dimension"""
    dimension: str
    raw_score: float = Field(ge=0, le=10)
    weight: float
    weighted_score: float

class UtilityScore(BaseModel):
    """Complete utility score breakdown"""
    scenario_id: str
    dimension_scores: list[DimensionScore]
    total_score: float = Field(ge=0, le=100)
    rank: int

# ═══════════════════════════════════════════════════════════════════════════
# COORDINATOR / SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════

class ActionStep(BaseModel):
    """Single step in a scenario"""
    step_number: int
    action: TradeAction
    ticker: str
    quantity: float
    timing: str
    rationale: str

class Scenario(BaseModel):
    """Complete recommendation scenario"""
    scenario_id: str
    title: str
    description: str
    action_steps: list[ActionStep]
    expected_outcomes: dict
    risks: list[str]
    utility_score: Optional[UtilityScore] = None

class CoordinatorOutput(BaseModel):
    """Final coordinator synthesis"""
    portfolio_id: str
    trigger_event: str
    analysis_timestamp: datetime
    drift_findings: DriftAgentOutput
    tax_findings: TaxAgentOutput
    conflicts_detected: list[str]
    scenarios: list[Scenario]
    recommended_scenario_id: str
    merkle_hash: str

# ═══════════════════════════════════════════════════════════════════════════
# CANVAS UI
# ═══════════════════════════════════════════════════════════════════════════

class UIAction(BaseModel):
    """Action from Canvas UI"""
    action_type: Literal["approve", "reject", "what_if", "adjust"]
    scenario_id: str
    parameters: dict = {}
    session_id: str
    timestamp: datetime

class CanvasState(BaseModel):
    """Current state of Canvas UI"""
    scenarios: list[Scenario]
    selected_scenario_id: Optional[str]
    slider_values: dict[str, float] = {}
    approved: bool = False
```

### Step 0.2: Interface Definitions

Create `src/contracts/interfaces.py`:

```python
"""
SENTINEL INTERFACES — Abstract base classes for all components.
Implement these interfaces to ensure compatibility.
"""

from abc import ABC, abstractmethod
from typing import Optional
from .schemas import *

class IGateway(ABC):
    """Gateway interface for event submission"""

    @abstractmethod
    async def submit(self, event: InputEvent) -> str:
        """Submit event and return event_id"""
        pass

    @abstractmethod
    async def process_session(self, session_id: str) -> None:
        """Process events for a session"""
        pass

class IAgent(ABC):
    """Base agent interface"""

    @abstractmethod
    async def analyze(
        self,
        portfolio_id: str,
        context: dict
    ) -> BaseModel:
        """Run analysis and return structured output"""
        pass

    @abstractmethod
    def get_agent_type(self) -> AgentType:
        """Return agent type"""
        pass

class IDriftAgent(IAgent):
    """Drift agent interface"""

    @abstractmethod
    async def analyze(
        self,
        portfolio_id: str,
        context: dict
    ) -> DriftAgentOutput:
        pass

class ITaxAgent(IAgent):
    """Tax agent interface"""

    @abstractmethod
    async def analyze(
        self,
        portfolio_id: str,
        context: dict,
        proposed_trades: list[RecommendedTrade]
    ) -> TaxAgentOutput:
        pass

class ICoordinator(ABC):
    """Coordinator interface"""

    @abstractmethod
    async def execute_analysis(
        self,
        portfolio_id: str,
        event: InputEvent,
        client_profile: ClientProfile
    ) -> CoordinatorOutput:
        pass

    @abstractmethod
    async def handle_ui_action(
        self,
        action: UIAction
    ) -> dict:
        pass

class IContextManager(ABC):
    """Context management interface"""

    @abstractmethod
    def add_to_context(self, item: dict, estimated_tokens: int) -> None:
        pass

    @abstractmethod
    def get_context(self) -> list[dict]:
        pass

    @abstractmethod
    def flush_to_memory(self) -> None:
        pass

class IStorage(ABC):
    """Storage interface for portfolios and transactions"""

    @abstractmethod
    def get_portfolio(self, portfolio_id: str) -> Portfolio:
        pass

    @abstractmethod
    def get_transactions(
        self,
        portfolio_id: str,
        days: int = 30
    ) -> list[Transaction]:
        pass

    @abstractmethod
    def save_recommendation(self, output: CoordinatorOutput) -> None:
        pass

class IMerkleChain(ABC):
    """Merkle chain interface"""

    @abstractmethod
    def add_block(self, data: dict) -> str:
        pass

    @abstractmethod
    def verify_integrity(self) -> bool:
        pass

    @abstractmethod
    def get_root_hash(self) -> str:
        pass

class IUtilityFunction(ABC):
    """Utility scoring interface"""

    @abstractmethod
    def score_scenario(
        self,
        scenario: Scenario,
        portfolio: Portfolio,
        weights: UtilityWeights
    ) -> UtilityScore:
        pass

    @abstractmethod
    def rank_scenarios(
        self,
        scenarios: list[Scenario],
        portfolio: Portfolio,
        weights: UtilityWeights
    ) -> list[UtilityScore]:
        pass

class ICanvasGenerator(ABC):
    """Canvas UI generation interface"""

    @abstractmethod
    def generate_html(
        self,
        scenarios: list[Scenario],
        utility_scores: list[UtilityScore]
    ) -> str:
        pass

    @abstractmethod
    def handle_action(
        self,
        action: UIAction
    ) -> dict:
        pass
```

### Step 0.3: Stub Implementations

Create `src/contracts/stubs.py`:

```python
"""
SENTINEL STUBS — Mock implementations for parallel development.
Replace these with real implementations as they're built.
"""

from .interfaces import *
from .schemas import *
from datetime import datetime
import json

class StubGateway(IGateway):
    """Stub gateway for testing"""

    def __init__(self):
        self.events: list[InputEvent] = []

    async def submit(self, event: InputEvent) -> str:
        self.events.append(event)
        return event.event_id

    async def process_session(self, session_id: str) -> None:
        pass

class StubDriftAgent(IDriftAgent):
    """Stub drift agent returning mock data"""

    async def analyze(
        self,
        portfolio_id: str,
        context: dict
    ) -> DriftAgentOutput:
        return DriftAgentOutput(
            portfolio_id=portfolio_id,
            analysis_timestamp=datetime.utcnow(),
            drift_detected=True,
            concentration_risks=[
                ConcentrationRisk(
                    ticker="NVDA",
                    current_weight=0.17,
                    limit=0.15,
                    excess=0.02,
                    severity="high"
                )
            ],
            drift_metrics=[
                DriftMetric(
                    asset_class="Technology",
                    target_weight=0.25,
                    current_weight=0.29,
                    drift_pct=0.04,
                    drift_direction="over"
                )
            ],
            recommended_trades=[
                RecommendedTrade(
                    ticker="NVDA",
                    action=TradeAction.SELL,
                    quantity=15000,
                    rationale="Reduce concentration risk",
                    urgency=7
                )
            ],
            urgency_score=7,
            reasoning="NVDA concentration exceeds 15% limit after tech selloff"
        )

    def get_agent_type(self) -> AgentType:
        return AgentType.DRIFT

class StubTaxAgent(ITaxAgent):
    """Stub tax agent returning mock data"""

    async def analyze(
        self,
        portfolio_id: str,
        context: dict,
        proposed_trades: list[RecommendedTrade]
    ) -> TaxAgentOutput:
        return TaxAgentOutput(
            portfolio_id=portfolio_id,
            analysis_timestamp=datetime.utcnow(),
            wash_sale_violations=[
                WashSaleViolation(
                    ticker="NVDA",
                    prior_sale_date=datetime(2024, 3, 1),
                    days_since_sale=15,
                    disallowed_loss=25000.0,
                    recommendation="Wait 16 more days or use correlated substitute"
                )
            ],
            tax_opportunities=[
                TaxOpportunity(
                    ticker="AMD",
                    opportunity_type="harvest_loss",
                    estimated_benefit=15000.0,
                    action_required="Sell AMD lots with losses"
                )
            ],
            proposed_trades_analysis=[],
            total_tax_impact=-25000.0,
            recommendations=[
                "Avoid selling NVDA for 16 days to clear wash sale window",
                "Consider AMD as correlated substitute"
            ],
            reasoning="NVDA sale would trigger wash sale; AMD substitute available"
        )

    def get_agent_type(self) -> AgentType:
        return AgentType.TAX

class StubStorage(IStorage):
    """Stub storage with sample portfolio data"""

    def __init__(self):
        self.portfolios = self._load_sample_portfolios()

    def _load_sample_portfolios(self) -> dict:
        # Return mock portfolio
        return {
            "UHNW_001": Portfolio(
                portfolio_id="UHNW_001",
                client_id="CLIENT_001",
                name="Growth Portfolio A",
                aum_usd=50_000_000,
                holdings=[
                    Holding(
                        ticker="NVDA",
                        quantity=10000,
                        current_price=850.0,
                        market_value=8_500_000,
                        portfolio_weight=0.17,
                        cost_basis=5_000_000,
                        unrealized_gain_loss=3_500_000,
                        sector="Technology",
                        asset_class="US Equities"
                    )
                ],
                target_allocation=TargetAllocation(
                    us_equities=0.35,
                    international_equities=0.15,
                    fixed_income=0.20,
                    alternatives=0.20,
                    structured_products=0.05,
                    cash=0.05
                ),
                client_profile=ClientProfile(
                    client_id="CLIENT_001",
                    risk_tolerance=RiskProfile.MODERATE_GROWTH,
                    tax_sensitivity=0.85,
                    concentration_limit=0.15
                ),
                last_rebalance=datetime(2024, 1, 15),
                cash_available=2_500_000
            )
        }

    def get_portfolio(self, portfolio_id: str) -> Portfolio:
        return self.portfolios.get(portfolio_id)

    def get_transactions(
        self,
        portfolio_id: str,
        days: int = 30
    ) -> list[Transaction]:
        return [
            Transaction(
                transaction_id="TXN_001",
                portfolio_id=portfolio_id,
                ticker="NVDA",
                action=TradeAction.SELL,
                quantity=5000,
                price=870.0,
                timestamp=datetime(2024, 3, 1)
            )
        ]

    def save_recommendation(self, output: CoordinatorOutput) -> None:
        pass

class StubUtilityFunction(IUtilityFunction):
    """Stub utility function with mock scoring"""

    def score_scenario(
        self,
        scenario: Scenario,
        portfolio: Portfolio,
        weights: UtilityWeights
    ) -> UtilityScore:
        # Mock scoring
        dimension_scores = [
            DimensionScore(dimension="risk_reduction", raw_score=7.5, weight=weights.risk_reduction, weighted_score=7.5 * weights.risk_reduction * 10),
            DimensionScore(dimension="tax_savings", raw_score=8.2, weight=weights.tax_savings, weighted_score=8.2 * weights.tax_savings * 10),
            DimensionScore(dimension="goal_alignment", raw_score=6.8, weight=weights.goal_alignment, weighted_score=6.8 * weights.goal_alignment * 10),
            DimensionScore(dimension="transaction_cost", raw_score=7.0, weight=weights.transaction_cost, weighted_score=7.0 * weights.transaction_cost * 10),
            DimensionScore(dimension="urgency", raw_score=6.5, weight=weights.urgency, weighted_score=6.5 * weights.urgency * 10),
        ]

        total = sum(d.weighted_score for d in dimension_scores)

        return UtilityScore(
            scenario_id=scenario.scenario_id,
            dimension_scores=dimension_scores,
            total_score=total,
            rank=1
        )

    def rank_scenarios(
        self,
        scenarios: list[Scenario],
        portfolio: Portfolio,
        weights: UtilityWeights
    ) -> list[UtilityScore]:
        scores = [self.score_scenario(s, portfolio, weights) for s in scenarios]
        scores.sort(key=lambda x: x.total_score, reverse=True)
        for i, score in enumerate(scores):
            score.rank = i + 1
        return scores
```

### Step 0.5: Security Contracts

Create `src/contracts/security.py`:

```python
"""
SENTINEL SECURITY CONTRACTS
Per SECURITY_PRACTICES.md specifications
"""

from enum import Enum, Flag, auto
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# PERMISSIONS & ROLES
# ═══════════════════════════════════════════════════════════════════════════

class Permission(Flag):
    """Fine-grained permissions for RBAC"""
    NONE = 0
    READ_HOLDINGS = auto()
    READ_TAX_LOTS = auto()
    READ_CLIENT_PII = auto()
    WRITE_RECOMMENDATIONS = auto()
    APPROVE_TRADES = auto()
    EXECUTE_TRADES = auto()
    ADMIN = auto()

    # Composite permissions
    DRIFT_AGENT = READ_HOLDINGS
    TAX_AGENT = READ_HOLDINGS | READ_TAX_LOTS
    COORDINATOR = READ_HOLDINGS | READ_TAX_LOTS | WRITE_RECOMMENDATIONS
    HUMAN_ADVISOR = READ_HOLDINGS | READ_TAX_LOTS | READ_CLIENT_PII | WRITE_RECOMMENDATIONS | APPROVE_TRADES

class Role(str, Enum):
    DRIFT_AGENT = "drift_agent"
    TAX_AGENT = "tax_agent"
    COORDINATOR = "coordinator"
    HUMAN_ADVISOR = "human_advisor"
    ANALYST = "analyst"
    CLIENT = "client"
    SYSTEM = "system"
    ADMIN = "admin"

ROLE_PERMISSIONS: dict[Role, Permission] = {
    Role.DRIFT_AGENT: Permission.DRIFT_AGENT,
    Role.TAX_AGENT: Permission.TAX_AGENT,
    Role.COORDINATOR: Permission.COORDINATOR,
    Role.HUMAN_ADVISOR: Permission.HUMAN_ADVISOR,
    Role.ANALYST: Permission.READ_HOLDINGS,
    Role.CLIENT: Permission.READ_HOLDINGS,
    Role.SYSTEM: Permission.NONE,
    Role.ADMIN: Permission.ADMIN,
}

# ═══════════════════════════════════════════════════════════════════════════
# SESSION SECURITY
# ═══════════════════════════════════════════════════════════════════════════

class SessionType(str, Enum):
    ADVISOR_MAIN = "advisor:main"    # Full access, host process
    ANALYST = "analyst"               # Read-only, Docker sandbox
    CLIENT_PORTAL = "client"          # Own portfolio only, Docker sandbox
    SYSTEM = "system"                 # Internal processes, host process

class SessionConfig(BaseModel):
    """Security boundary for a session"""
    session_id: str
    session_type: SessionType
    role: Role
    allowed_portfolios: Optional[list[str]] = None  # None = all (for advisors)
    sandbox_mode: bool = True
    max_tool_calls: int = Field(default=10, ge=1, le=100)
    timeout_seconds: int = Field(default=300, ge=30, le=3600)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def permissions(self) -> Permission:
        return ROLE_PERMISSIONS.get(self.role, Permission.NONE)

    def has_permission(self, perm: Permission) -> bool:
        return bool(self.permissions & perm)

    def can_access_portfolio(self, portfolio_id: str) -> bool:
        if self.allowed_portfolios is None:
            return True  # Advisor has full access
        return portfolio_id in self.allowed_portfolios

# ═══════════════════════════════════════════════════════════════════════════
# ENCRYPTION
# ═══════════════════════════════════════════════════════════════════════════

class EncryptedField(BaseModel):
    """Envelope-encrypted field structure"""
    ciphertext: bytes
    encrypted_dek: bytes  # DEK encrypted with master key
    nonce: bytes
    tag: bytes
    key_version: int = 1

class EncryptionConfig(BaseModel):
    """Encryption configuration"""
    algorithm: str = "AES-256-GCM"
    kdf_iterations: int = 256000
    key_derivation: str = "PBKDF2-SHA256"

# ═══════════════════════════════════════════════════════════════════════════
# AUDIT TRAIL
# ═══════════════════════════════════════════════════════════════════════════

class AuditEventType(str, Enum):
    SYSTEM_INITIALIZED = "system_initialized"
    MARKET_EVENT_DETECTED = "market_event_detected"
    STATE_TRANSITION = "state_transition"
    AGENT_INVOKED = "agent_invoked"
    AGENT_COMPLETED = "agent_completed"
    CONFLICT_DETECTED = "conflict_detected"
    RECOMMENDATION_GENERATED = "recommendation_generated"
    HUMAN_DECISION = "human_decision"
    TRADE_EXECUTED = "trade_executed"
    PERMISSION_DENIED = "permission_denied"
    SESSION_CREATED = "session_created"
    SESSION_TERMINATED = "session_terminated"

class AuditEvent(BaseModel):
    """Single audit event for Merkle chain"""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    session_id: str
    actor: str  # Agent name or user ID
    action: str
    resource: Optional[str] = None  # Portfolio ID, etc.
    details: dict = {}
    previous_hash: str
    current_hash: str

# ═══════════════════════════════════════════════════════════════════════════
# SECURITY DECORATORS (Interface)
# ═══════════════════════════════════════════════════════════════════════════

class ISecurityContext:
    """Interface for security context injection"""
    session: SessionConfig
    audit_chain: "IMerkleChain"

    def require_permission(self, perm: Permission) -> None:
        """Raise PermissionError if permission not held"""
        if not self.session.has_permission(perm):
            raise PermissionError(
                f"Permission {perm.name} required. "
                f"Session {self.session.session_id} has role {self.session.role.value}"
            )

    def log_access(self, resource: str, action: str) -> None:
        """Log access attempt to audit chain"""
        pass  # Implemented by concrete class
```

Add to `src/contracts/interfaces.py`:

```python
# Add these to interfaces.py

from .security import Permission, SessionConfig, AuditEvent

class ISecurityEnforcer(ABC):
    """Security enforcement interface"""

    @abstractmethod
    def check_permission(
        self,
        session: SessionConfig,
        required: Permission
    ) -> bool:
        """Check if session has required permission"""
        pass

    @abstractmethod
    def enforce_permission(
        self,
        session: SessionConfig,
        required: Permission
    ) -> None:
        """Raise PermissionError if permission not held"""
        pass

class ISandbox(ABC):
    """Sandbox execution interface"""

    @abstractmethod
    async def execute(
        self,
        session: SessionConfig,
        code: callable
    ) -> dict:
        """Execute code in sandbox if session requires it"""
        pass

class IEncryption(ABC):
    """Encryption interface"""

    @abstractmethod
    def encrypt_field(self, plaintext: str) -> "EncryptedField":
        """Encrypt a field using envelope encryption"""
        pass

    @abstractmethod
    def decrypt_field(self, encrypted: "EncryptedField") -> str:
        """Decrypt an envelope-encrypted field"""
        pass
```

---

## Phase 1: Foundation

**Parallelization**: 3 independent workstreams can proceed simultaneously.

```
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   WORKSTREAM A  │   │   WORKSTREAM B  │   │   WORKSTREAM C  │
│   Data & Models │   │ Gateway & Events│   │ Storage & Memory│
├─────────────────┤   ├─────────────────┤   ├─────────────────┤
│ 1.2 Data models │   │ 1.5 Gateway core│   │ 1.7 SQLite+Enc  │
│ 1.3 Portfolios  │   │ 1.6 Event schemas│  │ 1.8 Merkle chain│
│ 1.4 Market cache│   │                 │   │ 1.9 Context mgr │
│                 │   │                 │   │ 1.10 ChromaDB   │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                     │
         └─────────────────────┴─────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  1.1 Project Setup  │
                    │  (Must complete     │
                    │   first)            │
                    └─────────────────────┘
```

### Step 1.1: Project Setup

**File**: `pyproject.toml`

```toml
[tool.poetry]
name = "sentinel"
version = "0.1.0"
description = "Multi-agent UHNW portfolio monitoring and tax optimization"
authors = ["Shubham"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.12"
anthropic = "^0.39.0"
pydantic = "^2.5.0"
transitions = "^0.9.0"
sqlcipher3 = "^0.5.0"
chromadb = "^0.4.0"
cryptography = "^42.0.0"
rich = "^13.7.0"
apscheduler = "^3.10.0"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
pytest-cov = "^4.1.0"

[tool.poetry.scripts]
sentinel = "src.main:main"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**Directory Structure**:
```
sentinel/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── contracts/
│   │   ├── __init__.py
│   │   ├── schemas.py
│   │   ├── interfaces.py
│   │   └── stubs.py
│   ├── gateway/
│   │   ├── __init__.py
│   │   ├── gateway.py
│   │   ├── events.py
│   │   └── inputs.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── drift_agent.py
│   │   ├── tax_agent.py
│   │   └── coordinator.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── storage.py
│   │   ├── market_cache.py
│   │   └── vector_store.py
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── context_manager.py
│   │   └── persistent.py
│   ├── security/
│   │   ├── __init__.py
│   │   ├── encryption.py
│   │   ├── rbac.py
│   │   ├── merkle.py
│   │   └── sessions.py
│   ├── state/
│   │   ├── __init__.py
│   │   ├── machine.py
│   │   └── utility.py
│   ├── skills/
│   │   ├── __init__.py
│   │   └── skill_registry.py
│   ├── routing/
│   │   ├── __init__.py
│   │   └── persona_router.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── canvas.py
│   │   └── cli.py
│   └── demos/
│       ├── __init__.py
│       ├── golden_path.py
│       ├── proactive_heartbeat.py
│       └── webhook_trigger.py
├── data/
│   ├── market_cache/
│   ├── portfolios/
│   └── regulatory/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_gateway.py
│   ├── test_agents.py
│   ├── test_utility.py
│   ├── test_encryption.py
│   ├── test_sessions.py
│   └── test_state_machine.py
├── docs/
├── .env.example
├── pyproject.toml
├── README.md
└── CLAUDE.md
```

### Workstream A: Data & Models (Steps 1.2-1.4)

**Agent Assignment**: Data Agent

| Step | File | Description |
|------|------|-------------|
| 1.2 | `src/data/models.py` | Portfolio, Holding, TaxLot dataclasses |
| 1.3 | `data/portfolios/*.json` | 3 synthetic portfolios |
| 1.4 | `data/market_cache/*.json` | Pre-cached market data |

**Deliverables**:
- `Portfolio`, `Holding`, `TaxLot` classes matching `schemas.py`
- `portfolio_a.json`: $50M Growth (NVDA heavy)
- `portfolio_b.json`: $80M Conservative (fixed income)
- `portfolio_c.json`: $30M Liquidity Event (single stock)
- Market data for NVDA, AMD, AAPL, MSFT, GOOGL

### Workstream B: Gateway & Events (Steps 1.5-1.6)

**Agent Assignment**: Gateway Agent

| Step | File | Description |
|------|------|-------------|
| 1.5 | `src/gateway/gateway.py` | Gateway class with queue management |
| 1.6 | `src/gateway/events.py` | Pydantic event schemas |

**Deliverables**:
- `Gateway` class implementing `IGateway`
- Per-session queue management
- Event validation via Pydantic
- `test_gateway.py` passing

### Workstream C: Storage & Memory (Steps 1.7-1.10)

**Agent Assignment**: Storage Agent

| Step | File | Description |
|------|------|-------------|
| 1.7 | `src/security/encryption.py` | AES-256-GCM envelope encryption |
| 1.8 | `src/security/merkle.py` | Merkle chain with SHA-256 |
| 1.9 | `src/memory/context_manager.py` | Hot context with auto-flush |
| 1.10 | `src/data/vector_store.py` | ChromaDB integration |

**Deliverables**:
- Encrypt/decrypt round-trip working
- Merkle chain with integrity verification
- Context manager with token tracking
- ChromaDB collection for semantic search

---

## Phase 2: Core Agents

**Parallelization**: 2 workstreams (Agents + State/Security)

```
┌─────────────────────┐   ┌─────────────────────┐
│    WORKSTREAM D     │   │    WORKSTREAM E     │
│   Agent Development │   │  State & Security   │
├─────────────────────┤   ├─────────────────────┤
│ 2.1 Base agent class│   │ 2.5 State machine   │
│ 2.2 Drift agent     │   │ 2.6 Utility function│
│ 2.3 Tax agent       │   │ 2.7 RBAC system     │
│ 2.4 Skill registry  │   │ 2.8 Session bounds  │
└─────────────────────┘   └─────────────────────┘
```

### Workstream D: Agent Development (Steps 2.1-2.4)

**Agent Assignment**: Agent Developer

| Step | File | Description |
|------|------|-------------|
| 2.1 | `src/agents/base.py` | Base agent with Claude API |
| 2.2 | `src/agents/drift_agent.py` | Drift detection agent |
| 2.3 | `src/agents/tax_agent.py` | Tax optimization agent |
| 2.4 | `src/skills/skill_registry.py` | Dynamic skill loading |

**Key Implementation Details**:

```python
# src/agents/base.py
class BaseAgent(IAgent):
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-5-20250514",
        system_prompt: str = ""
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.system_prompt = system_prompt

    async def _call_claude(
        self,
        user_prompt: str,
        output_schema: type[BaseModel]
    ) -> BaseModel:
        """Call Claude with structured output"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        # Parse response into output_schema
        return output_schema.model_validate_json(response.content[0].text)
```

### Workstream E: State & Security (Steps 2.5-2.8)

**Agent Assignment**: Security Agent

> **Reference**: Implement per `docs/SECURITY_PRACTICES.md` sections 2-4.

| Step | File | Description | Security Ref |
|------|------|-------------|--------------|
| 2.5 | `src/state/machine.py` | State machine with transitions lib | §4.1 Audit |
| 2.6 | `src/state/utility.py` | 5-dimensional utility scoring | - |
| 2.7 | `src/security/rbac.py` | Role-based access control | §2.1 RBAC |
| 2.8 | `src/security/sessions.py` | Session boundaries + Docker | §2.2, §3.2 Sandbox |

**State Machine States**:
```
MONITOR → DETECT → ANALYZE → CONFLICT_RESOLUTION → RECOMMEND → APPROVED → EXECUTE → MONITOR
```
All transitions MUST be logged to Merkle chain (§4.1).

**RBAC Implementation** (per §2.1):
```python
from functools import wraps

def require_permission(perm: Permission):
    """Decorator to enforce RBAC on methods"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            session = self._get_session()
            if not session.has_permission(perm):
                # Log denial to Merkle chain
                self._audit_chain.add_block({
                    "event_type": "permission_denied",
                    "session_id": session.session_id,
                    "required_permission": perm.name,
                    "attempted_action": func.__name__
                })
                raise PermissionError(
                    f"{perm.name} required for {func.__name__}"
                )
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

# Usage
class TaxAgent:
    @require_permission(Permission.READ_TAX_LOTS)
    def get_tax_lots(self, portfolio_id: str) -> list[TaxLot]:
        ...
```

**Session Sandbox** (per §2.2, §3.2):
```python
class SessionBoundary:
    async def execute(self, session: SessionConfig, agent_fn: callable):
        if session.session_type in [SessionType.ANALYST, SessionType.CLIENT_PORTAL]:
            # Untrusted → Docker sandbox
            return await self._execute_in_docker(session, agent_fn)
        else:
            # Trusted → Host process
            return await agent_fn()

    async def _execute_in_docker(self, session: SessionConfig, agent_fn: callable):
        container = docker.containers.run(
            image="sentinel-agent-runtime",
            mem_limit="512m",
            network_mode="none",  # No network (§3.2)
            cpu_period=100000,
            cpu_quota=50000,      # 0.5 CPU
            remove=True
        )
        ...
```

**Utility Function Formula**:
```python
weighted_score = sum(
    dimension_score * weight * 10
    for dimension_score, weight in zip(
        [risk, tax, goal, cost, urgency],
        [w.risk_reduction, w.tax_savings, w.goal_alignment, w.transaction_cost, w.urgency]
    )
)
```

---

## Phase 3: Orchestration

**Parallelization**: 2 workstreams (Orchestration + UI)

```
┌─────────────────────┐   ┌─────────────────────┐
│    WORKSTREAM F     │   │    WORKSTREAM G     │
│   Orchestration     │   │      UI Layer       │
├─────────────────────┤   ├─────────────────────┤
│ 3.1 Coordinator     │   │ 3.5 Canvas generator│
│ 3.2 Parallel dispatch│  │ 3.6 Rich CLI        │
│ 3.3 Conflict resolve│   │ 3.7 a2ui handlers   │
│ 3.4 Persona router  │   │                     │
└─────────────────────┘   └─────────────────────┘
         │                         │
         └────────┬────────────────┘
                  │
         Uses contracts from Phase 0
         Uses stubs until integration
```

### Workstream F: Orchestration (Steps 3.1-3.4)

**Agent Assignment**: Orchestration Agent

| Step | File | Description |
|------|------|-------------|
| 3.1 | `src/agents/coordinator.py` | Coordinator agent (Opus) |
| 3.2 | (in coordinator.py) | asyncio.gather for parallel dispatch |
| 3.3 | (in coordinator.py) | Conflict detection and resolution |
| 3.4 | `src/routing/persona_router.py` | Risk profile routing |

**Parallel Dispatch Pattern**:
```python
async def execute_analysis(self, portfolio_id: str, event: InputEvent):
    drift_task = self.drift_agent.analyze(portfolio_id, context)
    tax_task = self.tax_agent.analyze(portfolio_id, context, [])

    drift_result, tax_result = await asyncio.gather(drift_task, tax_task)

    # Detect conflicts
    conflicts = self._detect_conflicts(drift_result, tax_result)

    # Generate scenarios
    scenarios = await self._generate_scenarios(drift_result, tax_result, conflicts)

    return CoordinatorOutput(...)
```

### Workstream G: UI Layer (Steps 3.5-3.7)

**Agent Assignment**: UI Agent

| Step | File | Description |
|------|------|-------------|
| 3.5 | `src/ui/canvas.py` | HTML generation with design system |
| 3.6 | `src/ui/cli.py` | Rich CLI output |
| 3.7 | (in canvas.py) | a2ui-action event handling |

**Canvas uses DESIGN_FRAMEWORK.md tokens**:
- Import `--s-obsidian-*`, `--s-champagne-*` colors
- Use `.s-card`, `.s-btn`, `.s-score-bar` components
- Include Google Fonts: Cormorant Garamond, DM Sans, JetBrains Mono

---

## Phase 4: Integration & Demo

**Parallelization**: 2 workstreams (Demo + Testing)

```
┌─────────────────────┐   ┌─────────────────────┐
│    WORKSTREAM H     │   │    WORKSTREAM I     │
│   Demo Development  │   │   Testing & Docs    │
├─────────────────────┤   ├─────────────────────┤
│ 4.1 Golden path     │   │ 4.5 E2E tests       │
│ 4.2 Heartbeat demo  │   │ 4.6 Merkle verify   │
│ 4.3 Webhook demo    │   │ 4.7 Doc polish      │
│ 4.4 Canvas output   │   │                     │
└─────────────────────┘   └─────────────────────┘
```

### Workstream H: Demo Development (Steps 4.1-4.4)

**Agent Assignment**: Demo Agent

| Step | File | Description |
|------|------|-------------|
| 4.1 | `src/demos/golden_path.py` | Tech drop → AMD substitute |
| 4.2 | `src/demos/proactive_heartbeat.py` | Scheduled check finds drift |
| 4.3 | `src/demos/webhook_trigger.py` | SEC filing triggers analysis |
| 4.4 | `sentinel-demo.html` | Standalone Canvas demo |

**Golden Path Sequence**:
```
1. Create MarketEventInput (Tech -4%)
2. Submit to Gateway
3. Gateway routes to Coordinator
4. Coordinator dispatches Drift + Tax in parallel
5. Drift detects NVDA concentration (17% > 15%)
6. Tax detects wash sale (sold NVDA 15 days ago)
7. Coordinator detects conflict
8. Generate 3 scenarios:
   A) Sell NVDA now (accept wash sale)
   B) Wait 31 days
   C) Sell NVDA, buy AMD (substitute)
9. Utility scoring ranks C highest (69.6/100)
10. Canvas UI generated
11. Merkle chain logs all steps
```

### Workstream I: Testing & Docs (Steps 4.5-4.7)

**Agent Assignment**: QA Agent

| Step | File | Description |
|------|------|-------------|
| 4.5 | `tests/test_e2e.py` | End-to-end integration tests |
| 4.6 | (in main.py) | `--verify-merkle` command |
| 4.7 | `docs/INTERVIEW_NOTES.md` | Talking points |

---

## Dependency Graph

```
Phase 0 ─────────────────────────────────────────────────────────────┐
  │                                                                  │
  │ Contracts & Interfaces                                          │
  │ (Must complete first)                                           │
  │                                                                  │
  ▼                                                                  │
Phase 1 ─────────────────────────────────────────────────────────────┤
  │                                                                  │
  │  ┌─────────┐  ┌─────────┐  ┌─────────┐                          │
  │  │ Data    │  │ Gateway │  │ Storage │   Can run in parallel    │
  │  │ Models  │  │ Events  │  │ Memory  │                          │
  │  └────┬────┘  └────┬────┘  └────┬────┘                          │
  │       │            │            │                               │
  │       └────────────┼────────────┘                               │
  │                    │                                            │
  ▼                    ▼                                            │
Phase 2 ─────────────────────────────────────────────────────────────┤
  │                                                                  │
  │  ┌─────────────┐  ┌─────────────┐                               │
  │  │ Agents      │  │ State &     │   Can run in parallel        │
  │  │ Development │  │ Security    │   (use stubs for deps)        │
  │  └──────┬──────┘  └──────┬──────┘                               │
  │         │                │                                      │
  │         └────────┬───────┘                                      │
  │                  │                                              │
  ▼                  ▼                                              │
Phase 3 ─────────────────────────────────────────────────────────────┤
  │                                                                  │
  │  ┌─────────────┐  ┌─────────────┐                               │
  │  │ Orchestration│ │ UI Layer   │   Can run in parallel         │
  │  │ Coordinator │  │ Canvas/CLI │   (UI uses contracts)          │
  │  └──────┬──────┘  └──────┬──────┘                               │
  │         │                │                                      │
  │         └────────┬───────┘                                      │
  │                  │                                              │
  ▼                  ▼                                              │
Phase 4 ─────────────────────────────────────────────────────────────┘
  │
  │  ┌─────────────┐  ┌─────────────┐
  │  │ Demo        │  │ Testing &   │   Can run in parallel
  │  │ Development │  │ Docs        │
  │  └─────────────┘  └─────────────┘
  │
  ▼
  ✓ COMPLETE
```

---

## Integration Points

### Contract-Based Integration

All workstreams integrate through the contracts defined in Phase 0:

| Workstream | Produces | Consumes |
|------------|----------|----------|
| A (Data) | `Portfolio`, `Holding` | - |
| B (Gateway) | `InputEvent` routing | `IAgent` interface |
| C (Storage) | `IStorage` impl | `Portfolio` models |
| D (Agents) | `DriftAgentOutput`, `TaxAgentOutput` | `Portfolio`, `IStorage` |
| E (State) | `UtilityScore`, `SessionConfig` | Agent outputs |
| F (Orchestration) | `CoordinatorOutput` | All agent outputs |
| G (UI) | HTML with a2ui-actions | `Scenario`, `UtilityScore` |
| H (Demo) | Runnable demos | All components |
| I (Testing) | Test coverage | All components |

### Stub Replacement Schedule

| Phase | Replace Stub | With Real |
|-------|--------------|-----------|
| 1 | - | Initial stubs created |
| 2 | `StubDriftAgent` | `DriftAgent` |
| 2 | `StubTaxAgent` | `TaxAgent` |
| 2 | `StubStorage` | `SQLiteStorage` |
| 3 | `StubUtilityFunction` | `UtilityFunction` |
| 4 | `StubGateway` | `Gateway` |

---

## Commands Reference

```bash
# Setup
poetry install
cp .env.example .env  # Add ANTHROPIC_API_KEY

# Development
poetry run pytest                           # Run all tests
poetry run pytest tests/test_gateway.py -v  # Run specific test
poetry run pytest --cov=src tests/          # With coverage

# Demos
poetry run python -m src.main --demo golden_path
poetry run python -m src.main --demo heartbeat
poetry run python -m src.main --demo webhook

# Utilities
poetry run python -m src.main --verify-merkle
poetry run python -m src.data.generate_portfolios

# Development server (for Canvas)
python -m http.server 8000
open http://localhost:8000/sentinel-demo.html
```

---

## Success Criteria

### Phase 0 Complete When:
- [ ] All Pydantic schemas validate correctly
- [ ] All interfaces have matching stub implementations
- [ ] Security contracts defined (Permission, SessionConfig, AuditEvent)
- [ ] `pytest tests/test_contracts.py` passes

### Phase 1 Complete When:
- [ ] `poetry install` succeeds
- [ ] Gateway validates/rejects events correctly
- [ ] Portfolios load from JSON
- [ ] **SECURITY**: Encryption round-trip works (AES-256-GCM)
- [ ] **SECURITY**: Merkle chain verifies integrity
- [ ] **SECURITY**: No hardcoded secrets (bandit check passes)
- [ ] `pytest tests/test_encryption.py tests/test_merkle.py` passes

### Phase 2 Complete When:
- [ ] Drift agent returns structured `DriftAgentOutput`
- [ ] Tax agent detects wash sale violations
- [ ] State machine transitions correctly (all logged to Merkle)
- [ ] Utility function scores scenarios
- [ ] **SECURITY**: RBAC decorator blocks unauthorized access
- [ ] **SECURITY**: Session sandbox executes untrusted sessions in Docker
- [ ] **SECURITY**: Agents use hub-and-spoke only (no direct communication)
- [ ] `pytest tests/test_rbac.py tests/test_sessions.py` passes

### Phase 3 Complete When:
- [ ] Coordinator dispatches agents in parallel
- [ ] Conflicts detected between drift and tax
- [ ] Persona router selects correct weights
- [ ] Canvas generates valid HTML
- [ ] **SECURITY**: HTML output sanitized (no raw PII)
- [ ] **SECURITY**: a2ui-actions validated before execution
- [ ] a2ui-actions trigger tool calls

### Phase 4 Complete When:
- [ ] Golden path demo runs end-to-end
- [ ] AMD substitute ranks #1 (score ~69.6)
- [ ] Heartbeat detects drift proactively
- [ ] Webhook triggers analysis
- [ ] **SECURITY**: Merkle chain integrity verified
- [ ] **SECURITY**: Full security compliance checklist passes
- [ ] All tests pass with >80% coverage
- [ ] `pytest tests/test_security.py -v` passes

### Security Compliance Checklist (Phase 4)

| Requirement | Test | Status |
|-------------|------|--------|
| Encryption at rest | `test_encryption.py::test_roundtrip` | ⬜ |
| No hardcoded secrets | `bandit -r src/` | ⬜ |
| RBAC enforcement | `test_rbac.py::test_permission_denied` | ⬜ |
| Session isolation | `test_sessions.py::test_sandbox_execution` | ⬜ |
| Hub-and-spoke only | `test_agent_communication.py` | ⬜ |
| Merkle integrity | `test_merkle.py::test_tamper_detection` | ⬜ |
| Input validation | `test_gateway.py::test_invalid_rejected` | ⬜ |
| Output sanitization | `test_canvas.py::test_no_raw_pii` | ⬜ |
| Parameterized SQL | `bandit -r src/ -t B608` | ⬜ |
| Audit trail complete | `test_merkle.py::test_all_events_logged` | ⬜ |

---

## Workstream Assignment Template

When assigning work to agents, use this template:

```markdown
## Assignment: [Workstream Letter] - [Workstream Name]

**Agent**: [Agent Name]
**Phase**: [Phase Number]
**Steps**: [Step Numbers]

### Context
[Brief description of what this workstream accomplishes]

### Dependencies
- **Requires**: [List of completed steps/phases]
- **Blocked By**: [Any blocking issues]

### Deliverables
| File | Description | Status |
|------|-------------|--------|
| ... | ... | ... |

### Contracts to Implement
- `I[Interface]` from `src/contracts/interfaces.py`

### Tests to Pass
- `tests/test_[component].py`

### Done When
- [ ] Criteria 1
- [ ] Criteria 2
```

---

*Last Updated*: 2026-02-21
*Plan Version*: 1.0
