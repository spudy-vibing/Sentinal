"""
SENTINEL CONTRACTS — All Pydantic schemas for system-wide type safety.

This module defines the canonical data structures used throughout Sentinel.
Import from here to ensure consistency across all components.

Reference: docs/IMPLEMENTATION_PLAN.md Phase 0
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, Any
from datetime import datetime, timezone
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════

class EventType(str, Enum):
    """Types of events that can flow through the Gateway"""
    MARKET_EVENT = "market_event"
    HEARTBEAT = "heartbeat"
    CRON = "cron"
    WEBHOOK = "webhook"
    AGENT_MESSAGE = "agent_message"


class AgentType(str, Enum):
    """Types of agents in the system"""
    COORDINATOR = "coordinator"
    DRIFT = "drift"
    TAX = "tax"


class RiskProfile(str, Enum):
    """Client risk tolerance profiles"""
    CONSERVATIVE = "conservative"
    MODERATE_GROWTH = "moderate_growth"
    AGGRESSIVE = "aggressive"


class TradeAction(str, Enum):
    """Possible trade actions"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class SystemState(str, Enum):
    """State machine states"""
    MONITOR = "monitor"
    DETECT = "detect"
    ANALYZE = "analyze"
    CONFLICT_RESOLUTION = "conflict_resolution"
    RECOMMEND = "recommend"
    APPROVED = "approved"
    EXECUTE = "execute"


class Severity(str, Enum):
    """Risk severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DriftDirection(str, Enum):
    """Direction of allocation drift"""
    OVER = "over"
    UNDER = "under"


class TaxOpportunityType(str, Enum):
    """Types of tax optimization opportunities"""
    HARVEST_LOSS = "harvest_loss"
    HARVEST_GAIN = "harvest_gain"
    LOT_SELECTION = "lot_selection"


class CronJobType(str, Enum):
    """Types of scheduled jobs"""
    DAILY_REVIEW = "daily_review"
    EOD_TAX = "eod_tax"
    QUARTERLY_REBALANCE = "quarterly_rebalance"


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

    model_config = {"frozen": False}


class MarketEventInput(InputEvent):
    """Market event triggering portfolio analysis"""
    event_type: Literal[EventType.MARKET_EVENT] = EventType.MARKET_EVENT
    affected_sectors: list[str]
    magnitude: float = Field(ge=-1.0, le=1.0)
    affected_tickers: list[str] = Field(default_factory=list)
    description: str = Field(max_length=500)

    @field_validator("affected_sectors")
    @classmethod
    def validate_sectors(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("At least one affected sector required")
        return v


class HeartbeatInput(InputEvent):
    """Periodic heartbeat for proactive monitoring"""
    event_type: Literal[EventType.HEARTBEAT] = EventType.HEARTBEAT
    portfolio_ids: list[str]


class CronJobInput(InputEvent):
    """Scheduled job input"""
    event_type: Literal[EventType.CRON] = EventType.CRON
    job_type: CronJobType
    instructions: str = Field(max_length=1000)


class WebhookInput(InputEvent):
    """External webhook input (SEC filings, earnings, etc.)"""
    event_type: Literal[EventType.WEBHOOK] = EventType.WEBHOOK
    source: str
    payload: dict[str, Any]


class AgentMessageInput(InputEvent):
    """Agent-to-agent message (via Coordinator only)"""
    event_type: Literal[EventType.AGENT_MESSAGE] = EventType.AGENT_MESSAGE
    from_agent: AgentType
    to_agent: AgentType
    context: dict[str, Any]


# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS — Portfolio & Holdings
# ═══════════════════════════════════════════════════════════════════════════

class TaxLot(BaseModel):
    """Individual tax lot for a holding"""
    lot_id: str
    purchase_date: datetime
    purchase_price: float = Field(gt=0)
    quantity: float = Field(gt=0)
    cost_basis: float = Field(ge=0)

    @property
    def holding_period_days(self) -> int:
        """Days since purchase"""
        now = datetime.now(timezone.utc)
        purchase = self.purchase_date
        # Handle timezone-naive dates by assuming UTC
        if purchase.tzinfo is None:
            purchase = purchase.replace(tzinfo=timezone.utc)
        return (now - purchase).days

    @property
    def is_long_term(self) -> bool:
        """True if held > 1 year (long-term capital gains)"""
        return self.holding_period_days > 365


class Holding(BaseModel):
    """Single position in a portfolio"""
    ticker: str = Field(min_length=1, max_length=10)
    quantity: float = Field(gt=0)
    current_price: float = Field(gt=0)
    market_value: float = Field(ge=0)
    portfolio_weight: float = Field(ge=0, le=1)
    cost_basis: float = Field(ge=0)
    unrealized_gain_loss: float
    tax_lots: list[TaxLot] = Field(default_factory=list)
    sector: str
    asset_class: str

    @property
    def gain_loss_pct(self) -> float:
        """Unrealized gain/loss as percentage"""
        if self.cost_basis == 0:
            return 0.0
        return self.unrealized_gain_loss / self.cost_basis


class TargetAllocation(BaseModel):
    """Target allocation percentages (must sum to 1.0)"""
    us_equities: float = Field(ge=0, le=1)
    international_equities: float = Field(ge=0, le=1)
    fixed_income: float = Field(ge=0, le=1)
    alternatives: float = Field(ge=0, le=1)
    structured_products: float = Field(ge=0, le=1)
    cash: float = Field(ge=0, le=1)

    @field_validator("cash")
    @classmethod
    def validate_total(cls, v: float, info) -> float:
        total = (
            info.data.get("us_equities", 0) +
            info.data.get("international_equities", 0) +
            info.data.get("fixed_income", 0) +
            info.data.get("alternatives", 0) +
            info.data.get("structured_products", 0) +
            v
        )
        if not (0.99 <= total <= 1.01):  # Allow small rounding errors
            raise ValueError(f"Allocations must sum to 1.0, got {total}")
        return v


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
    aum_usd: float = Field(gt=0)
    holdings: list[Holding]
    target_allocation: TargetAllocation
    client_profile: ClientProfile
    last_rebalance: datetime
    cash_available: float = Field(ge=0)

    @property
    def total_market_value(self) -> float:
        """Sum of all holdings market values"""
        return sum(h.market_value for h in self.holdings)

    def get_holding(self, ticker: str) -> Optional[Holding]:
        """Get holding by ticker"""
        for h in self.holdings:
            if h.ticker == ticker:
                return h
        return None

    def get_sector_weight(self, sector: str) -> float:
        """Get total weight for a sector"""
        return sum(h.portfolio_weight for h in self.holdings if h.sector == sector)


class Transaction(BaseModel):
    """Historical transaction record"""
    transaction_id: str
    portfolio_id: str
    ticker: str
    action: TradeAction
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)
    timestamp: datetime
    wash_sale_disallowed: float = Field(default=0, ge=0)

    @property
    def total_value(self) -> float:
        """Total transaction value"""
        return self.quantity * self.price


# ═══════════════════════════════════════════════════════════════════════════
# AGENT OUTPUTS
# ═══════════════════════════════════════════════════════════════════════════

class ConcentrationRisk(BaseModel):
    """Detected concentration risk"""
    ticker: str
    current_weight: float = Field(ge=0, le=1)
    limit: float = Field(ge=0, le=1)
    excess: float = Field(ge=0)
    severity: Severity

    @property
    def excess_pct(self) -> float:
        """Excess as percentage points"""
        return self.excess * 100


class DriftMetric(BaseModel):
    """Allocation drift measurement"""
    asset_class: str
    target_weight: float = Field(ge=0, le=1)
    current_weight: float = Field(ge=0, le=1)
    drift_pct: float
    drift_direction: DriftDirection

    @property
    def abs_drift(self) -> float:
        """Absolute drift value"""
        return abs(self.drift_pct)


class RecommendedTrade(BaseModel):
    """Single trade recommendation"""
    ticker: str
    action: TradeAction
    quantity: float = Field(ge=0)
    rationale: str = Field(max_length=500)
    urgency: int = Field(ge=1, le=10)
    estimated_tax_impact: float = Field(default=0)

    @property
    def is_urgent(self) -> bool:
        """True if urgency >= 7"""
        return self.urgency >= 7


class DriftAgentOutput(BaseModel):
    """Structured output from Drift Agent"""
    portfolio_id: str
    analysis_timestamp: datetime
    drift_detected: bool
    concentration_risks: list[ConcentrationRisk]
    drift_metrics: list[DriftMetric]
    recommended_trades: list[RecommendedTrade]
    urgency_score: int = Field(ge=1, le=10)
    reasoning: str = Field(max_length=2000)

    @property
    def has_critical_risks(self) -> bool:
        """True if any critical concentration risks"""
        return any(r.severity == Severity.CRITICAL for r in self.concentration_risks)


class WashSaleViolation(BaseModel):
    """Detected wash sale issue"""
    ticker: str
    prior_sale_date: datetime
    days_since_sale: int = Field(ge=0)
    disallowed_loss: float = Field(ge=0)
    recommendation: str = Field(max_length=500)

    @property
    def days_until_clear(self) -> int:
        """Days until wash sale window clears (31 days)"""
        return max(0, 31 - self.days_since_sale)


class TaxOpportunity(BaseModel):
    """Tax optimization opportunity"""
    ticker: str
    opportunity_type: TaxOpportunityType
    estimated_benefit: float
    action_required: str = Field(max_length=500)


class TaxAgentOutput(BaseModel):
    """Structured output from Tax Agent"""
    portfolio_id: str
    analysis_timestamp: datetime
    wash_sale_violations: list[WashSaleViolation]
    tax_opportunities: list[TaxOpportunity]
    proposed_trades_analysis: list[dict[str, Any]]
    total_tax_impact: float
    recommendations: list[str]
    reasoning: str = Field(max_length=2000)

    @property
    def has_violations(self) -> bool:
        """True if any wash sale violations"""
        return len(self.wash_sale_violations) > 0


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY SCORING
# ═══════════════════════════════════════════════════════════════════════════

class UtilityWeights(BaseModel):
    """Weights for utility function dimensions (must sum to 1.0)"""
    risk_reduction: float = Field(ge=0, le=1)
    tax_savings: float = Field(ge=0, le=1)
    goal_alignment: float = Field(ge=0, le=1)
    transaction_cost: float = Field(ge=0, le=1)
    urgency: float = Field(ge=0, le=1)

    @field_validator("urgency")
    @classmethod
    def validate_total(cls, v: float, info) -> float:
        total = (
            info.data.get("risk_reduction", 0) +
            info.data.get("tax_savings", 0) +
            info.data.get("goal_alignment", 0) +
            info.data.get("transaction_cost", 0) +
            v
        )
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v


# Predefined weights by risk profile
UTILITY_WEIGHTS_BY_PROFILE: dict[RiskProfile, UtilityWeights] = {
    RiskProfile.CONSERVATIVE: UtilityWeights(
        risk_reduction=0.40,
        tax_savings=0.20,
        goal_alignment=0.20,
        transaction_cost=0.15,
        urgency=0.05
    ),
    RiskProfile.MODERATE_GROWTH: UtilityWeights(
        risk_reduction=0.25,
        tax_savings=0.30,
        goal_alignment=0.25,
        transaction_cost=0.10,
        urgency=0.10
    ),
    RiskProfile.AGGRESSIVE: UtilityWeights(
        risk_reduction=0.15,
        tax_savings=0.20,
        goal_alignment=0.30,
        transaction_cost=0.10,
        urgency=0.25
    ),
}


class DimensionScore(BaseModel):
    """Score for single utility dimension"""
    dimension: str
    raw_score: float = Field(ge=0, le=10)
    weight: float = Field(ge=0, le=1)
    weighted_score: float = Field(ge=0)

    @classmethod
    def create(cls, dimension: str, raw_score: float, weight: float) -> "DimensionScore":
        """Factory method with automatic weighted score calculation"""
        return cls(
            dimension=dimension,
            raw_score=raw_score,
            weight=weight,
            weighted_score=raw_score * weight * 10
        )


class UtilityScore(BaseModel):
    """Complete utility score breakdown"""
    scenario_id: str
    dimension_scores: list[DimensionScore]
    total_score: float = Field(ge=0, le=100)
    rank: int = Field(ge=1)

    @classmethod
    def calculate(
        cls,
        scenario_id: str,
        raw_scores: dict[str, float],
        weights: UtilityWeights,
        rank: int = 1
    ) -> "UtilityScore":
        """Calculate utility score from raw dimension scores"""
        dimension_scores = [
            DimensionScore.create("risk_reduction", raw_scores.get("risk_reduction", 5), weights.risk_reduction),
            DimensionScore.create("tax_savings", raw_scores.get("tax_savings", 5), weights.tax_savings),
            DimensionScore.create("goal_alignment", raw_scores.get("goal_alignment", 5), weights.goal_alignment),
            DimensionScore.create("transaction_cost", raw_scores.get("transaction_cost", 5), weights.transaction_cost),
            DimensionScore.create("urgency", raw_scores.get("urgency", 5), weights.urgency),
        ]
        total = sum(d.weighted_score for d in dimension_scores)
        return cls(
            scenario_id=scenario_id,
            dimension_scores=dimension_scores,
            total_score=total,
            rank=rank
        )


# ═══════════════════════════════════════════════════════════════════════════
# COORDINATOR / SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════

class ActionStep(BaseModel):
    """Single step in a scenario"""
    step_number: int = Field(ge=1)
    action: TradeAction
    ticker: str
    quantity: float = Field(ge=0)
    timing: str
    rationale: str = Field(max_length=500)


class Scenario(BaseModel):
    """Complete recommendation scenario"""
    scenario_id: str
    title: str = Field(max_length=100)
    description: str = Field(max_length=1000)
    action_steps: list[ActionStep]
    expected_outcomes: dict[str, Any]
    risks: list[str]
    utility_score: Optional[UtilityScore] = None

    @property
    def total_trades(self) -> int:
        """Number of trades in this scenario"""
        return len(self.action_steps)


class ConflictInfo(BaseModel):
    """Information about a detected conflict"""
    conflict_id: str
    conflict_type: str
    agents_involved: list[AgentType]
    description: str
    resolution_options: list[str]


class CoordinatorOutput(BaseModel):
    """Final coordinator synthesis"""
    portfolio_id: str
    trigger_event: str
    analysis_timestamp: datetime
    drift_findings: DriftAgentOutput
    tax_findings: TaxAgentOutput
    conflicts_detected: list[ConflictInfo]
    scenarios: list[Scenario]
    recommended_scenario_id: str
    merkle_hash: str

    @property
    def recommended_scenario(self) -> Optional[Scenario]:
        """Get the recommended scenario"""
        for s in self.scenarios:
            if s.scenario_id == self.recommended_scenario_id:
                return s
        return None


# ═══════════════════════════════════════════════════════════════════════════
# CANVAS UI
# ═══════════════════════════════════════════════════════════════════════════

class UIActionType(str, Enum):
    """Types of UI actions"""
    APPROVE = "approve"
    REJECT = "reject"
    WHAT_IF = "what_if"
    ADJUST = "adjust"


class UIAction(BaseModel):
    """Action from Canvas UI"""
    action_type: UIActionType
    scenario_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    session_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CanvasState(BaseModel):
    """Current state of Canvas UI"""
    portfolio_id: str
    scenarios: list[Scenario]
    utility_scores: list[UtilityScore]
    selected_scenario_id: Optional[str] = None
    slider_values: dict[str, float] = Field(default_factory=dict)
    approved: bool = False
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════════════════════════════
# MARKET DATA
# ═══════════════════════════════════════════════════════════════════════════

class MarketDataPoint(BaseModel):
    """Single market data point (OHLCV)"""
    ticker: str
    date: datetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: int = Field(ge=0)

    @property
    def daily_change(self) -> float:
        """Daily change as percentage"""
        return (self.close - self.open) / self.open if self.open > 0 else 0


class SectorPerformance(BaseModel):
    """Sector-level performance data"""
    sector: str
    daily_change: float
    weekly_change: float
    monthly_change: float
    top_gainers: list[str]
    top_losers: list[str]


class PricePoint(BaseModel):
    """Single price point for time series data"""
    timestamp: datetime
    price: float = Field(gt=0)
    volume: int = Field(ge=0, default=0)


class MarketData(BaseModel):
    """Comprehensive market data for a security"""
    ticker: str
    current_price: float = Field(gt=0)
    previous_close: float = Field(gt=0)
    change_percent: float
    high_52w: float = Field(gt=0)
    low_52w: float = Field(gt=0)
    beta: float
    dividend_yield: float = Field(ge=0)
    pe_ratio: Optional[float] = None
    market_cap: float = Field(gt=0)
    sector: str
    industry: str
    exchange: str
    last_updated: datetime
