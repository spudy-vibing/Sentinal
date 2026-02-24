"""
SENTINEL DRIFT AGENT

Portfolio drift detection and concentration risk analysis.

Responsibilities:
- Detect positions exceeding concentration limits
- Calculate allocation drift from targets
- Generate rebalancing recommendations
- Assess urgency based on market conditions

Reference: docs/IMPLEMENTATION_PLAN.md Phase 2, Step 2.2
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from src.contracts.interfaces import IDriftAgent, IMerkleChain
from src.contracts.schemas import (
    AgentType,
    Portfolio,
    DriftAgentOutput,
    ConcentrationRisk,
    DriftMetric,
    RecommendedTrade,
    TradeAction,
    Severity,
    DriftDirection,
)
from src.contracts.security import (
    SessionConfig,
    Permission,
    require_permission,
)
from src.data import load_portfolio, PortfolioAnalytics

from .base import BaseAgent


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════

DRIFT_AGENT_SYSTEM_PROMPT = """You are a Portfolio Drift Detection Agent for ultra-high-net-worth (UHNW) clients at a major investment bank.

Your role is to:
1. Analyze portfolio holdings for concentration risks (positions exceeding limits)
2. Calculate allocation drift from target allocations
3. Generate actionable rebalancing recommendations
4. Assess urgency based on market conditions and risk levels

IMPORTANT GUIDELINES:
- Be precise with numbers and percentages
- Consider the client's risk tolerance when assessing severity
- Recommend specific quantities to trade, not vague suggestions
- Always explain your reasoning clearly
- Flag any position that exceeds the concentration limit as a risk

CONCENTRATION RISK SEVERITY:
- Low: 0-2% over limit
- Medium: 2-5% over limit
- High: 5-10% over limit
- Critical: >10% over limit

DRIFT SEVERITY:
- Minor: <2% drift from target
- Moderate: 2-5% drift
- Significant: 5-10% drift
- Severe: >10% drift

When recommending trades:
- Consider transaction costs and market impact
- Prioritize reducing the highest-risk positions first
- Suggest gradual rebalancing for large positions
- Calculate approximate quantities based on current prices"""


# ═══════════════════════════════════════════════════════════════════════════
# DRIFT AGENT
# ═══════════════════════════════════════════════════════════════════════════

class DriftAgent(BaseAgent, IDriftAgent):
    """
    Drift detection agent using Claude for analysis.

    Detects:
    - Concentration risks (positions > client limit)
    - Allocation drift from targets
    - Sector overweight/underweight

    Usage:
        agent = DriftAgent(session=session, merkle_chain=chain)
        result = await agent.analyze("portfolio_a", {"market_event": {...}})
    """

    def __init__(
        self,
        session: Optional[SessionConfig] = None,
        merkle_chain: Optional[IMerkleChain] = None,
        api_key: Optional[str] = None,
    ):
        super().__init__(
            agent_type=AgentType.DRIFT,
            system_prompt=DRIFT_AGENT_SYSTEM_PROMPT,
            session=session,
            merkle_chain=merkle_chain,
            api_key=api_key,
        )

    @require_permission(Permission.READ_HOLDINGS)
    async def analyze(
        self,
        portfolio_id: str,
        context: dict
    ) -> DriftAgentOutput:
        """
        Analyze portfolio for drift and concentration risks.

        Args:
            portfolio_id: Portfolio to analyze
            context: Additional context including:
                - market_event: Market event that triggered analysis (optional)
                - affected_sectors: Sectors affected by market event (optional)

        Returns:
            DriftAgentOutput with findings and recommendations
        """
        # Load portfolio
        portfolio = load_portfolio(portfolio_id)

        # Build analysis prompt
        prompt = self._build_analysis_prompt(portfolio, context)

        # Call Claude for analysis
        result = await self._call_claude(prompt, DriftAgentOutput)

        return result

    async def analyze_with_portfolio(
        self,
        portfolio: Portfolio,
        context: dict
    ) -> DriftAgentOutput:
        """
        Analyze portfolio object directly (for testing or when already loaded).
        """
        prompt = self._build_analysis_prompt(portfolio, context)
        return await self._call_claude(prompt, DriftAgentOutput)

    def _build_analysis_prompt(
        self,
        portfolio: Portfolio,
        context: dict
    ) -> str:
        """Build the analysis prompt for Claude."""
        # Calculate current allocations
        asset_weights = PortfolioAnalytics.calculate_asset_class_weights(portfolio)
        sector_weights = PortfolioAnalytics.calculate_sector_weights(portfolio)
        drift = PortfolioAnalytics.calculate_drift(portfolio)

        # Find concentration risks (pre-compute for context)
        concentration_risks = PortfolioAnalytics.find_concentration_risks(portfolio)

        # Format market event if present
        market_event_text = ""
        if "market_event" in context:
            event = context["market_event"]
            market_event_text = f"""
MARKET EVENT TRIGGER:
- Description: {event.get('description', 'Unknown')}
- Affected Sectors: {', '.join(event.get('affected_sectors', []))}
- Magnitude: {event.get('magnitude', 0):.1%}
"""

        prompt = f"""Analyze this UHNW portfolio for drift and concentration risks.

PORTFOLIO: {portfolio.name}
Portfolio ID: {portfolio.portfolio_id}
AUM: ${portfolio.aum_usd:,.0f}
Last Rebalance: {portfolio.last_rebalance.strftime('%Y-%m-%d')}
Cash Available: ${portfolio.cash_available:,.0f}

CLIENT PROFILE:
- Risk Tolerance: {portfolio.client_profile.risk_tolerance.value}
- Tax Sensitivity: {portfolio.client_profile.tax_sensitivity:.0%}
- Concentration Limit: {portfolio.client_profile.concentration_limit:.0%}
- Rebalancing Frequency: {portfolio.client_profile.rebalancing_frequency}
{market_event_text}

TARGET ALLOCATION:
- US Equities: {portfolio.target_allocation.us_equities:.0%}
- International Equities: {portfolio.target_allocation.international_equities:.0%}
- Fixed Income: {portfolio.target_allocation.fixed_income:.0%}
- Alternatives: {portfolio.target_allocation.alternatives:.0%}
- Structured Products: {portfolio.target_allocation.structured_products:.0%}
- Cash: {portfolio.target_allocation.cash:.0%}

CURRENT ALLOCATION BY ASSET CLASS:
{self._format_allocation(asset_weights)}

ALLOCATION DRIFT FROM TARGETS:
{self._format_drift(drift)}

CURRENT HOLDINGS:
{self._format_holdings_for_prompt(portfolio.holdings)}

SECTOR BREAKDOWN:
{self._format_allocation(sector_weights)}

PRE-COMPUTED CONCENTRATION RISKS:
{self._format_concentration_risks(concentration_risks, portfolio.client_profile.concentration_limit)}

Please analyze this portfolio and provide:
1. All concentration risks (positions exceeding {portfolio.client_profile.concentration_limit:.0%} limit)
2. Allocation drift metrics for each asset class
3. Recommended trades to address risks
4. Overall urgency score (1-10)
5. Clear reasoning for your recommendations

Consider:
- The client's {portfolio.client_profile.risk_tolerance.value} risk tolerance
- Tax sensitivity of {portfolio.client_profile.tax_sensitivity:.0%}
- Available cash of ${portfolio.cash_available:,.0f}

Respond with a complete DriftAgentOutput JSON object."""

        return prompt

    def _format_allocation(self, weights: dict) -> str:
        """Format allocation weights for display."""
        lines = []
        for asset_class, weight in sorted(weights.items(), key=lambda x: -x[1]):
            lines.append(f"- {asset_class}: {weight:.1%}")
        return "\n".join(lines)

    def _format_drift(self, drift: dict) -> str:
        """Format drift metrics for display."""
        lines = []
        for asset_class, drift_value in sorted(drift.items(), key=lambda x: -abs(x[1])):
            direction = "over" if drift_value > 0 else "under"
            lines.append(f"- {asset_class}: {drift_value:+.1%} ({direction}weight)")
        return "\n".join(lines)

    def _format_concentration_risks(
        self,
        risks: list,
        limit: float
    ) -> str:
        """Format pre-computed concentration risks."""
        if not risks:
            return "No positions currently exceed concentration limit."

        lines = []
        for h in risks:
            excess = h.portfolio_weight - limit
            lines.append(
                f"- {h.ticker}: {h.portfolio_weight:.1%} "
                f"(exceeds {limit:.0%} limit by {excess:.1%})"
            )
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# OFFLINE DRIFT ANALYZER (No LLM, for testing)
# ═══════════════════════════════════════════════════════════════════════════

class OfflineDriftAnalyzer:
    """
    Offline drift analyzer that doesn't require Claude API.

    Useful for testing and when LLM calls aren't needed.
    Uses rule-based analysis instead of AI.
    """

    @staticmethod
    def analyze(portfolio: Portfolio, context: dict = None) -> DriftAgentOutput:
        """
        Analyze portfolio using rule-based logic.

        Returns same structure as DriftAgent but without LLM.
        """
        context = context or {}
        limit = portfolio.client_profile.concentration_limit

        # Find concentration risks
        concentration_risks = []
        for h in portfolio.holdings:
            if h.portfolio_weight > limit:
                excess = h.portfolio_weight - limit
                severity = OfflineDriftAnalyzer._calculate_severity(excess)
                concentration_risks.append(ConcentrationRisk(
                    ticker=h.ticker,
                    current_weight=h.portfolio_weight,
                    limit=limit,
                    excess=excess,
                    severity=severity
                ))

        # Calculate drift metrics
        drift = PortfolioAnalytics.calculate_drift(portfolio)
        drift_metrics = []
        for asset_class, drift_value in drift.items():
            target = getattr(portfolio.target_allocation, asset_class.lower().replace(" ", "_"), 0)
            current = PortfolioAnalytics.calculate_asset_class_weights(portfolio).get(asset_class, 0)
            drift_metrics.append(DriftMetric(
                asset_class=asset_class,
                target_weight=target,
                current_weight=current,
                drift_pct=abs(drift_value),
                drift_direction=DriftDirection.OVER if drift_value > 0 else DriftDirection.UNDER
            ))

        # Generate recommended trades
        recommended_trades = []
        for risk in concentration_risks:
            # Calculate shares to sell to get back to limit
            holding = next(h for h in portfolio.holdings if h.ticker == risk.ticker)
            target_value = portfolio.aum_usd * limit
            current_value = holding.market_value
            excess_value = current_value - target_value
            shares_to_sell = int(excess_value / holding.current_price)

            if shares_to_sell > 0:
                recommended_trades.append(RecommendedTrade(
                    ticker=risk.ticker,
                    action=TradeAction.SELL,
                    quantity=shares_to_sell,
                    rationale=f"Reduce {risk.ticker} from {risk.current_weight:.1%} to {limit:.1%} limit",
                    urgency=OfflineDriftAnalyzer._severity_to_urgency(risk.severity),
                    estimated_tax_impact=0  # Would need tax agent for this
                ))

        # Calculate overall urgency
        urgency = max(
            [OfflineDriftAnalyzer._severity_to_urgency(r.severity) for r in concentration_risks],
            default=3
        )

        # Build reasoning
        reasoning_parts = []
        if concentration_risks:
            tickers = [r.ticker for r in concentration_risks]
            reasoning_parts.append(
                f"Concentration risks detected in: {', '.join(tickers)}. "
                f"These positions exceed the {limit:.0%} limit."
            )
        if any(abs(d.drift_pct) > 0.05 for d in drift_metrics):
            reasoning_parts.append("Significant allocation drift detected from targets.")

        if not reasoning_parts:
            reasoning_parts.append("Portfolio is within acceptable drift and concentration limits.")

        return DriftAgentOutput(
            portfolio_id=portfolio.portfolio_id,
            analysis_timestamp=datetime.now(timezone.utc),
            drift_detected=bool(concentration_risks) or any(abs(d.drift_pct) > 0.02 for d in drift_metrics),
            concentration_risks=concentration_risks,
            drift_metrics=drift_metrics,
            recommended_trades=recommended_trades,
            urgency_score=urgency,
            reasoning=" ".join(reasoning_parts)
        )

    @staticmethod
    def _calculate_severity(excess: float) -> Severity:
        """Calculate severity based on excess over limit."""
        if excess > 0.10:
            return Severity.CRITICAL
        elif excess > 0.05:
            return Severity.HIGH
        elif excess > 0.02:
            return Severity.MEDIUM
        else:
            return Severity.LOW

    @staticmethod
    def _severity_to_urgency(severity: Severity) -> int:
        """Convert severity to urgency score."""
        mapping = {
            Severity.LOW: 3,
            Severity.MEDIUM: 5,
            Severity.HIGH: 7,
            Severity.CRITICAL: 9
        }
        return mapping.get(severity, 5)
