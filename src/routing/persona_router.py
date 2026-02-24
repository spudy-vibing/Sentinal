"""
SENTINEL PERSONA ROUTER

Routes events to appropriate agents based on context.

The router analyzes incoming events and determines:
1. Which agents should be involved
2. What priority to assign
3. What context to provide

Reference: docs/IMPLEMENTATION_PLAN.md Phase 3
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional
from enum import Enum

from src.contracts.schemas import (
    InputEvent,
    EventType,
    AgentType,
    Portfolio,
    MarketEventInput,
    HeartbeatInput,
    WebhookInput,
    CronJobInput,
)
from src.data import load_portfolio, PortfolioAnalytics

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# ROUTING DECISION
# ═══════════════════════════════════════════════════════════════════════════

class RoutingPriority(str, Enum):
    """Priority levels for routing decisions."""
    CRITICAL = "critical"     # Immediate attention required
    HIGH = "high"             # Process soon
    NORMAL = "normal"         # Standard processing
    LOW = "low"               # Background processing
    SKIP = "skip"             # Don't process


@dataclass
class RoutingDecision:
    """Decision about how to route an event."""
    should_process: bool
    priority: RoutingPriority
    agents_required: list[AgentType]
    context_additions: dict
    reasoning: str

    @property
    def requires_coordinator(self) -> bool:
        """True if multiple agents or conflicts expected."""
        return len(self.agents_required) > 1 or AgentType.COORDINATOR in self.agents_required


# ═══════════════════════════════════════════════════════════════════════════
# PERSONA ROUTER
# ═══════════════════════════════════════════════════════════════════════════

class PersonaRouter:
    """
    Routes events to appropriate agents based on context analysis.

    The router examines:
    - Event type and payload
    - Portfolio characteristics
    - Current market conditions
    - Historical patterns

    Usage:
        router = PersonaRouter()
        decision = router.route(event, portfolio_id)

        if decision.should_process:
            coordinator.execute_analysis(
                portfolio_id,
                event,
                additional_context=decision.context_additions
            )
    """

    # Thresholds for routing decisions
    CONCENTRATION_THRESHOLD = 0.12  # 12% triggers concentration analysis
    DRIFT_THRESHOLD = 0.05          # 5% drift triggers rebalance analysis
    TAX_LOSS_THRESHOLD = 50000      # $50k loss triggers tax analysis
    URGENCY_MARKET_DROP = 0.10      # 10% drop = urgent

    def __init__(self):
        self._routing_history: list[RoutingDecision] = []

    def route(
        self,
        event: InputEvent,
        portfolio_id: str
    ) -> RoutingDecision:
        """
        Determine routing for an event.

        Args:
            event: The incoming event
            portfolio_id: Portfolio to analyze

        Returns:
            RoutingDecision with agents and priority
        """
        # Load portfolio for context
        try:
            portfolio = load_portfolio(portfolio_id)
        except Exception as e:
            logger.error(f"Failed to load portfolio {portfolio_id}: {e}")
            return RoutingDecision(
                should_process=False,
                priority=RoutingPriority.SKIP,
                agents_required=[],
                context_additions={},
                reasoning=f"Portfolio load failed: {e}"
            )

        # Route based on event type
        if event.event_type == EventType.MARKET_EVENT:
            return self._route_market_event(event, portfolio)
        elif event.event_type == EventType.HEARTBEAT:
            return self._route_heartbeat(event, portfolio)
        elif event.event_type == EventType.WEBHOOK:
            return self._route_webhook(event, portfolio)
        elif event.event_type == EventType.CRON_JOB:
            return self._route_cron(event, portfolio)
        else:
            return self._route_default(event, portfolio)

    def _route_market_event(
        self,
        event: InputEvent,
        portfolio: Portfolio
    ) -> RoutingDecision:
        """Route market events based on impact analysis."""
        # Handle both MarketEventInput and generic InputEvent
        if isinstance(event, MarketEventInput):
            magnitude = abs(event.magnitude)
            affected_sectors = event.affected_sectors
        else:
            # Fallback for generic InputEvent
            magnitude = abs(getattr(event, 'magnitude', 0))
            affected_sectors = getattr(event, 'affected_sectors', [])

        # Check portfolio exposure to affected sectors
        sector_weights = PortfolioAnalytics.calculate_sector_weights(portfolio)
        portfolio_exposure = sum(
            sector_weights.get(sector, 0)
            for sector in affected_sectors
        )

        agents = []
        priority = RoutingPriority.NORMAL
        context = {"market_event": {"magnitude": magnitude, "affected_sectors": affected_sectors}}

        # Determine urgency based on magnitude and exposure
        if magnitude >= self.URGENCY_MARKET_DROP:
            priority = RoutingPriority.CRITICAL
            agents = [AgentType.DRIFT, AgentType.TAX, AgentType.COORDINATOR]
            context["urgency_reason"] = f"Market drop of {magnitude:.1%}"

        elif magnitude >= 0.05 and portfolio_exposure > 0.20:
            priority = RoutingPriority.HIGH
            agents = [AgentType.DRIFT, AgentType.TAX, AgentType.COORDINATOR]
            context["urgency_reason"] = f"Significant exposure ({portfolio_exposure:.1%}) to affected sectors"

        elif portfolio_exposure > 0.10:
            priority = RoutingPriority.NORMAL
            agents = [AgentType.DRIFT, AgentType.COORDINATOR]

        else:
            priority = RoutingPriority.LOW
            agents = [AgentType.DRIFT]

        return RoutingDecision(
            should_process=True,
            priority=priority,
            agents_required=agents,
            context_additions=context,
            reasoning=(
                f"Market event: {magnitude:.1%} move, "
                f"portfolio exposure: {portfolio_exposure:.1%}"
            )
        )

    def _route_heartbeat(
        self,
        event: InputEvent,
        portfolio: Portfolio
    ) -> RoutingDecision:
        """Route periodic heartbeat checks."""
        # Analyze current portfolio state
        concentration_risks = PortfolioAnalytics.find_concentration_risks(portfolio)
        drift = PortfolioAnalytics.calculate_drift(portfolio)
        max_drift = max(abs(v) for v in drift.values()) if drift else 0

        # Check for unrealized losses (tax harvesting opportunities)
        total_losses = sum(
            abs(h.unrealized_gain_loss)
            for h in portfolio.holdings
            if h.unrealized_gain_loss < 0
        )

        agents = []
        priority = RoutingPriority.LOW
        context = {}

        # Concentration risk check
        if concentration_risks:
            highest_excess = max(
                h.portfolio_weight - portfolio.client_profile.concentration_limit
                for h in concentration_risks
            )
            if highest_excess > 0.10:  # 10% over limit
                priority = RoutingPriority.HIGH
                agents.append(AgentType.DRIFT)
                context["concentration_alert"] = True
            elif highest_excess > 0.05:
                priority = RoutingPriority.NORMAL
                agents.append(AgentType.DRIFT)

        # Drift check
        if max_drift > self.DRIFT_THRESHOLD:
            agents.append(AgentType.DRIFT)
            context["drift_detected"] = True
            if max_drift > 0.10:
                priority = RoutingPriority.HIGH

        # Tax loss check
        if total_losses > self.TAX_LOSS_THRESHOLD:
            agents.append(AgentType.TAX)
            context["tax_harvest_opportunity"] = total_losses

        # If multiple agents needed, add coordinator
        if len(agents) > 1:
            agents.append(AgentType.COORDINATOR)

        # Skip if nothing to do
        if not agents:
            return RoutingDecision(
                should_process=False,
                priority=RoutingPriority.SKIP,
                agents_required=[],
                context_additions={},
                reasoning="No issues detected in heartbeat check"
            )

        return RoutingDecision(
            should_process=True,
            priority=priority,
            agents_required=list(set(agents)),  # Dedupe
            context_additions=context,
            reasoning=(
                f"Heartbeat: {len(concentration_risks)} concentration risks, "
                f"max drift {max_drift:.1%}, losses ${total_losses:,.0f}"
            )
        )

    def _route_webhook(
        self,
        event: InputEvent,
        portfolio: Portfolio
    ) -> RoutingDecision:
        """Route webhook events (external triggers)."""
        # Handle both WebhookInput and generic InputEvent
        if isinstance(event, WebhookInput):
            payload = event.payload
        else:
            payload = getattr(event, 'payload', {}) or {}
        webhook_type = payload.get("type", "unknown")

        if webhook_type == "trade_execution":
            # Trade executed, need to check for wash sales
            return RoutingDecision(
                should_process=True,
                priority=RoutingPriority.HIGH,
                agents_required=[AgentType.TAX],
                context_additions={"trade_executed": payload.get("trade")},
                reasoning="Trade execution webhook - checking tax implications"
            )

        elif webhook_type == "price_alert":
            # Price alert triggered
            return RoutingDecision(
                should_process=True,
                priority=RoutingPriority.NORMAL,
                agents_required=[AgentType.DRIFT, AgentType.COORDINATOR],
                context_additions={"price_alert": payload},
                reasoning="Price alert webhook - checking drift"
            )

        elif webhook_type == "news_alert":
            # News alert - check if relevant to holdings
            affected_tickers = payload.get("tickers", [])
            portfolio_tickers = {h.ticker for h in portfolio.holdings}
            overlap = set(affected_tickers) & portfolio_tickers

            if overlap:
                return RoutingDecision(
                    should_process=True,
                    priority=RoutingPriority.NORMAL,
                    agents_required=[AgentType.DRIFT, AgentType.COORDINATOR],
                    context_additions={"news_alert": payload, "affected_holdings": list(overlap)},
                    reasoning=f"News affecting portfolio holdings: {overlap}"
                )

        return RoutingDecision(
            should_process=False,
            priority=RoutingPriority.SKIP,
            agents_required=[],
            context_additions={},
            reasoning=f"Unhandled webhook type: {webhook_type}"
        )

    def _route_cron(
        self,
        event: InputEvent,
        portfolio: Portfolio
    ) -> RoutingDecision:
        """Route scheduled cron jobs."""
        # Handle both CronJobInput and generic InputEvent
        if isinstance(event, CronJobInput):
            job_type = event.job_type.value if hasattr(event.job_type, 'value') else str(event.job_type)
        else:
            job_type = getattr(event, 'job_type', 'daily_review')

        if job_type == "daily_review":
            return RoutingDecision(
                should_process=True,
                priority=RoutingPriority.NORMAL,
                agents_required=[AgentType.DRIFT, AgentType.TAX, AgentType.COORDINATOR],
                context_additions={"scheduled_review": True},
                reasoning="Daily review cron job"
            )

        elif job_type == "eod_tax":
            return RoutingDecision(
                should_process=True,
                priority=RoutingPriority.NORMAL,
                agents_required=[AgentType.TAX],
                context_additions={"eod_tax_check": True},
                reasoning="End-of-day tax check"
            )

        elif job_type == "quarterly_rebalance":
            return RoutingDecision(
                should_process=True,
                priority=RoutingPriority.HIGH,
                agents_required=[AgentType.DRIFT, AgentType.TAX, AgentType.COORDINATOR],
                context_additions={"quarterly_rebalance": True},
                reasoning="Quarterly rebalance review"
            )

        return RoutingDecision(
            should_process=True,
            priority=RoutingPriority.LOW,
            agents_required=[AgentType.DRIFT],
            context_additions={},
            reasoning=f"Cron job: {job_type}"
        )

    def _route_default(
        self,
        event: InputEvent,
        portfolio: Portfolio
    ) -> RoutingDecision:
        """Default routing for unhandled event types."""
        return RoutingDecision(
            should_process=True,
            priority=RoutingPriority.NORMAL,
            agents_required=[AgentType.DRIFT, AgentType.COORDINATOR],
            context_additions={},
            reasoning=f"Default routing for event type: {event.event_type}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

_router: Optional[PersonaRouter] = None


def get_router() -> PersonaRouter:
    """Get or create default router."""
    global _router
    if _router is None:
        _router = PersonaRouter()
    return _router


def route_event(event: InputEvent, portfolio_id: str) -> RoutingDecision:
    """Convenience function to route an event."""
    return get_router().route(event, portfolio_id)
