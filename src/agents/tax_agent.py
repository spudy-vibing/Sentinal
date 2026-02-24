"""
SENTINEL TAX AGENT

Tax optimization and wash sale detection.

Responsibilities:
- Detect wash sale violations (31-day rule)
- Identify tax-loss harvesting opportunities
- Analyze tax impact of proposed trades
- Consider long-term vs short-term capital gains

Reference: docs/IMPLEMENTATION_PLAN.md Phase 2, Step 2.3
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional

from src.contracts.interfaces import ITaxAgent, IMerkleChain
from src.contracts.schemas import (
    AgentType,
    Portfolio,
    TaxAgentOutput,
    WashSaleViolation,
    TaxOpportunity,
    TaxOpportunityType,
    RecommendedTrade,
    TradeAction,
    Transaction,
)
from src.contracts.security import (
    SessionConfig,
    Permission,
    require_permission,
)
from src.data import load_portfolio, load_transactions

from .base import BaseAgent


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════

TAX_AGENT_SYSTEM_PROMPT = """You are a Tax Optimization Agent for ultra-high-net-worth (UHNW) clients at a major investment bank.

Your role is to:
1. Detect wash sale violations (IRS 31-day rule)
2. Identify tax-loss harvesting opportunities
3. Analyze tax impact of proposed trades from the Drift Agent
4. Recommend optimal lot selection for sales

WASH SALE RULES (IRS Section 1091):
- A wash sale occurs when selling a security at a loss and buying the same or "substantially identical" security within 31 days before or after the sale
- The disallowed loss is added to the cost basis of the replacement shares
- The 31-day window applies both before AND after the sale date

TAX-LOSS HARVESTING:
- Selling securities at a loss to offset capital gains
- Can offset up to $3,000 in ordinary income per year
- Losses carry forward indefinitely
- Must avoid wash sales when harvesting

CAPITAL GAINS RATES (2024):
- Short-term (held < 1 year): Ordinary income rates (up to 37%)
- Long-term (held > 1 year): 0%, 15%, or 20% based on income
- Net Investment Income Tax: Additional 3.8% for high earners
- For UHNW clients, assume 23.8% for long-term, 40.8% for short-term

LOT SELECTION STRATEGIES:
- HIFO (Highest In, First Out): Minimizes gains by selling highest cost lots first
- FIFO (First In, First Out): Default method, sells oldest lots first
- Specific ID: Choose specific lots to optimize tax outcome
- Tax-efficient: Balance between minimizing gains and avoiding wash sales

IMPORTANT GUIDELINES:
- Be precise with tax calculations
- Always consider the client's tax sensitivity
- Flag any trade that would trigger a wash sale
- Recommend substitute securities when appropriate
- Calculate estimated tax impact using appropriate rates
- Consider whether gains are long-term or short-term"""


# ═══════════════════════════════════════════════════════════════════════════
# TAX AGENT
# ═══════════════════════════════════════════════════════════════════════════

class TaxAgent(BaseAgent, ITaxAgent):
    """
    Tax optimization agent using Claude for analysis.

    Detects:
    - Wash sale violations
    - Tax-loss harvesting opportunities
    - Optimal lot selection

    Usage:
        agent = TaxAgent(session=session, merkle_chain=chain)
        result = await agent.analyze(
            "portfolio_a",
            {"market_event": {...}},
            proposed_trades=[RecommendedTrade(...)]
        )
    """

    def __init__(
        self,
        session: Optional[SessionConfig] = None,
        merkle_chain: Optional[IMerkleChain] = None,
        api_key: Optional[str] = None,
    ):
        super().__init__(
            agent_type=AgentType.TAX,
            system_prompt=TAX_AGENT_SYSTEM_PROMPT,
            session=session,
            merkle_chain=merkle_chain,
            api_key=api_key,
        )

    @require_permission(Permission.READ_TAX_LOTS)
    async def analyze(
        self,
        portfolio_id: str,
        context: dict,
        proposed_trades: list[RecommendedTrade] = None
    ) -> TaxAgentOutput:
        """
        Analyze portfolio for tax optimization opportunities.

        Args:
            portfolio_id: Portfolio to analyze
            context: Additional context including:
                - market_event: Market event that triggered analysis (optional)
                - year_to_date_gains: YTD realized gains (optional)
            proposed_trades: Trades recommended by Drift Agent to analyze

        Returns:
            TaxAgentOutput with findings and recommendations
        """
        proposed_trades = proposed_trades or []

        # Load portfolio and recent transactions
        portfolio = load_portfolio(portfolio_id)
        transactions = load_transactions(portfolio_id, days=60)  # 60 days for wash sale window

        # Build analysis prompt
        prompt = self._build_analysis_prompt(portfolio, transactions, proposed_trades, context)

        # Call Claude for analysis
        result = await self._call_claude(prompt, TaxAgentOutput)

        return result

    async def analyze_with_portfolio(
        self,
        portfolio: Portfolio,
        transactions: list[Transaction],
        proposed_trades: list[RecommendedTrade],
        context: dict
    ) -> TaxAgentOutput:
        """
        Analyze portfolio object directly (for testing or when already loaded).
        """
        prompt = self._build_analysis_prompt(portfolio, transactions, proposed_trades, context)
        return await self._call_claude(prompt, TaxAgentOutput)

    def _build_analysis_prompt(
        self,
        portfolio: Portfolio,
        transactions: list[Transaction],
        proposed_trades: list[RecommendedTrade],
        context: dict
    ) -> str:
        """Build the analysis prompt for Claude."""
        # Find recent sales for wash sale analysis
        recent_sales = [
            t for t in transactions
            if t.action == TradeAction.SELL
        ]

        # Calculate unrealized losses (potential harvesting opportunities)
        positions_with_losses = [
            h for h in portfolio.holdings
            if h.unrealized_gain_loss < 0
        ]

        # Format YTD gains if provided
        ytd_gains_text = ""
        if "year_to_date_gains" in context:
            ytd_gains = context["year_to_date_gains"]
            ytd_gains_text = f"\nYEAR-TO-DATE REALIZED GAINS: ${ytd_gains:,.0f}"

        prompt = f"""Analyze this UHNW portfolio for tax optimization opportunities.

PORTFOLIO: {portfolio.name}
Portfolio ID: {portfolio.portfolio_id}
AUM: ${portfolio.aum_usd:,.0f}
Cash Available: ${portfolio.cash_available:,.0f}
{ytd_gains_text}

CLIENT PROFILE:
- Risk Tolerance: {portfolio.client_profile.risk_tolerance.value}
- Tax Sensitivity: {portfolio.client_profile.tax_sensitivity:.0%}
- Concentration Limit: {portfolio.client_profile.concentration_limit:.0%}

CURRENT HOLDINGS WITH TAX LOTS:
{self._format_holdings_for_prompt(portfolio.holdings, include_tax_lots=True)}

POSITIONS WITH UNREALIZED LOSSES (Harvesting Candidates):
{self._format_loss_positions(positions_with_losses)}

RECENT TRANSACTIONS (Last 60 Days):
{self._format_transactions_for_prompt(transactions)}

RECENT SALES (For Wash Sale Analysis):
{self._format_recent_sales(recent_sales)}

PROPOSED TRADES FROM DRIFT AGENT:
{self._format_proposed_trades(proposed_trades)}

Please analyze and provide:
1. Any wash sale violations that would occur if proposed trades execute
2. Tax-loss harvesting opportunities (positions with losses that could offset gains)
3. Tax impact analysis for each proposed trade
4. Total estimated tax impact
5. Recommendations for tax-efficient execution
6. Clear reasoning for your recommendations

Consider:
- The client's tax sensitivity of {portfolio.client_profile.tax_sensitivity:.0%}
- Whether each lot is long-term or short-term
- The 31-day wash sale window (before AND after)
- Available substitutes to maintain market exposure

Respond with a complete TaxAgentOutput JSON object."""

        return prompt

    def _format_loss_positions(self, positions: list) -> str:
        """Format positions with unrealized losses."""
        if not positions:
            return "No positions with unrealized losses."

        lines = []
        for h in sorted(positions, key=lambda x: x.unrealized_gain_loss):
            lines.append(
                f"- {h.ticker}: ${abs(h.unrealized_gain_loss):,.0f} loss "
                f"({h.portfolio_weight:.1%} of portfolio)"
            )
        return "\n".join(lines)

    def _format_recent_sales(self, sales: list[Transaction]) -> str:
        """Format recent sales for wash sale analysis."""
        if not sales:
            return "No recent sales in the last 60 days."

        lines = []
        for t in sorted(sales, key=lambda x: x.timestamp, reverse=True):
            days_ago = (datetime.now(timezone.utc) - t.timestamp).days
            days_until_clear = max(0, 31 - days_ago)
            lines.append(
                f"- {t.timestamp.strftime('%Y-%m-%d')}: SOLD {t.quantity:,.0f} {t.ticker} "
                f"@ ${t.price:.2f} ({days_ago} days ago, "
                f"{'CLEAR' if days_until_clear == 0 else f'{days_until_clear} days until clear'})"
            )
        return "\n".join(lines)

    def _format_proposed_trades(self, trades: list[RecommendedTrade]) -> str:
        """Format proposed trades for analysis."""
        if not trades:
            return "No proposed trades to analyze."

        lines = []
        for t in trades:
            lines.append(
                f"- {t.action.value.upper()} {t.quantity:,.0f} {t.ticker} "
                f"(Urgency: {t.urgency}/10) - {t.rationale}"
            )
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# OFFLINE TAX ANALYZER (No LLM, for testing)
# ═══════════════════════════════════════════════════════════════════════════

class OfflineTaxAnalyzer:
    """
    Offline tax analyzer that doesn't require Claude API.

    Useful for testing and when LLM calls aren't needed.
    Uses rule-based analysis instead of AI.
    """

    # Tax rates for UHNW clients
    SHORT_TERM_RATE = 0.408  # 37% + 3.8% NIIT
    LONG_TERM_RATE = 0.238   # 20% + 3.8% NIIT

    @staticmethod
    def analyze(
        portfolio: Portfolio,
        transactions: list[Transaction] = None,
        proposed_trades: list[RecommendedTrade] = None,
        context: dict = None
    ) -> TaxAgentOutput:
        """
        Analyze portfolio using rule-based logic.

        Returns same structure as TaxAgent but without LLM.
        """
        transactions = transactions or []
        proposed_trades = proposed_trades or []
        context = context or {}

        # Find wash sale violations
        wash_sale_violations = OfflineTaxAnalyzer._detect_wash_sales(
            portfolio, transactions, proposed_trades
        )

        # Find tax opportunities
        tax_opportunities = OfflineTaxAnalyzer._find_opportunities(
            portfolio, context.get("year_to_date_gains", 0)
        )

        # Analyze proposed trades
        proposed_analysis, total_tax_impact = OfflineTaxAnalyzer._analyze_proposed_trades(
            portfolio, proposed_trades
        )

        # Generate recommendations
        recommendations = OfflineTaxAnalyzer._generate_recommendations(
            wash_sale_violations, tax_opportunities, proposed_trades
        )

        # Build reasoning
        reasoning = OfflineTaxAnalyzer._build_reasoning(
            wash_sale_violations, tax_opportunities, total_tax_impact
        )

        return TaxAgentOutput(
            portfolio_id=portfolio.portfolio_id,
            analysis_timestamp=datetime.now(timezone.utc),
            wash_sale_violations=wash_sale_violations,
            tax_opportunities=tax_opportunities,
            proposed_trades_analysis=proposed_analysis,
            total_tax_impact=total_tax_impact,
            recommendations=recommendations,
            reasoning=reasoning
        )

    @staticmethod
    def _detect_wash_sales(
        portfolio: Portfolio,
        transactions: list[Transaction],
        proposed_trades: list[RecommendedTrade]
    ) -> list[WashSaleViolation]:
        """Detect potential wash sale violations."""
        violations = []
        now = datetime.now(timezone.utc)

        # Get recent sales (within 31 days)
        recent_sales = {}
        for t in transactions:
            if t.action == TradeAction.SELL:
                days_ago = (now - t.timestamp).days
                if days_ago <= 31:
                    if t.ticker not in recent_sales:
                        recent_sales[t.ticker] = []
                    recent_sales[t.ticker].append({
                        "date": t.timestamp,
                        "days_ago": days_ago,
                        "quantity": t.quantity,
                        "price": t.price
                    })

        # Check if any proposed BUY would trigger wash sale
        for trade in proposed_trades:
            if trade.action == TradeAction.BUY and trade.ticker in recent_sales:
                for sale in recent_sales[trade.ticker]:
                    # Find the holding to estimate loss
                    holding = next(
                        (h for h in portfolio.holdings if h.ticker == trade.ticker),
                        None
                    )
                    estimated_loss = 0
                    if holding and holding.unrealized_gain_loss < 0:
                        estimated_loss = abs(holding.unrealized_gain_loss)

                    violations.append(WashSaleViolation(
                        ticker=trade.ticker,
                        prior_sale_date=sale["date"],
                        days_since_sale=sale["days_ago"],
                        disallowed_loss=estimated_loss,
                        recommendation=(
                            f"Wait {31 - sale['days_ago']} more days before buying {trade.ticker}, "
                            f"or purchase a substitute security to maintain exposure."
                        )
                    ))

        # Check if any proposed SELL followed by BUY in holdings would trigger
        sell_tickers = {t.ticker for t in proposed_trades if t.action == TradeAction.SELL}
        buy_tickers = {t.ticker for t in proposed_trades if t.action == TradeAction.BUY}

        for ticker in sell_tickers & buy_tickers:
            holding = next((h for h in portfolio.holdings if h.ticker == ticker), None)
            if holding and holding.unrealized_gain_loss < 0:
                violations.append(WashSaleViolation(
                    ticker=ticker,
                    prior_sale_date=now,
                    days_since_sale=0,
                    disallowed_loss=abs(holding.unrealized_gain_loss),
                    recommendation=(
                        f"Cannot sell and immediately repurchase {ticker} at a loss. "
                        f"Consider using a substitute security instead."
                    )
                ))

        return violations

    @staticmethod
    def _find_opportunities(
        portfolio: Portfolio,
        ytd_gains: float = 0
    ) -> list[TaxOpportunity]:
        """Find tax-loss harvesting opportunities."""
        opportunities = []

        for h in portfolio.holdings:
            if h.unrealized_gain_loss < 0:
                loss = abs(h.unrealized_gain_loss)

                # Calculate potential benefit
                if ytd_gains > 0:
                    # Can offset gains
                    benefit = min(loss, ytd_gains) * OfflineTaxAnalyzer.SHORT_TERM_RATE
                    action = f"Harvest ${loss:,.0f} loss to offset ${min(loss, ytd_gains):,.0f} in gains"
                else:
                    # Can offset up to $3,000 in ordinary income
                    benefit = min(loss, 3000) * OfflineTaxAnalyzer.SHORT_TERM_RATE
                    action = f"Harvest ${loss:,.0f} loss to offset ordinary income"

                opportunities.append(TaxOpportunity(
                    ticker=h.ticker,
                    opportunity_type=TaxOpportunityType.HARVEST_LOSS,
                    estimated_benefit=benefit,
                    action_required=action
                ))

        # Sort by benefit descending
        return sorted(opportunities, key=lambda x: -x.estimated_benefit)

    @staticmethod
    def _analyze_proposed_trades(
        portfolio: Portfolio,
        proposed_trades: list[RecommendedTrade]
    ) -> tuple[list[dict], float]:
        """Analyze tax impact of proposed trades."""
        analysis = []
        total_impact = 0

        for trade in proposed_trades:
            holding = next(
                (h for h in portfolio.holdings if h.ticker == trade.ticker),
                None
            )

            if not holding:
                analysis.append({
                    "ticker": trade.ticker,
                    "action": trade.action.value,
                    "quantity": trade.quantity,
                    "tax_impact": 0,
                    "notes": "New position - no tax impact on purchase"
                })
                continue

            if trade.action == TradeAction.SELL:
                # Calculate proportional gain/loss
                sell_ratio = min(trade.quantity / holding.quantity, 1.0)
                gain_loss = holding.unrealized_gain_loss * sell_ratio

                # Determine rate based on holding period
                # Check tax lots for weighted average holding period
                is_long_term = OfflineTaxAnalyzer._is_long_term_average(holding)
                rate = (
                    OfflineTaxAnalyzer.LONG_TERM_RATE
                    if is_long_term
                    else OfflineTaxAnalyzer.SHORT_TERM_RATE
                )

                tax_impact = gain_loss * rate if gain_loss > 0 else 0
                total_impact += tax_impact

                analysis.append({
                    "ticker": trade.ticker,
                    "action": trade.action.value,
                    "quantity": trade.quantity,
                    "realized_gain_loss": gain_loss,
                    "holding_period": "long-term" if is_long_term else "short-term",
                    "tax_rate": rate,
                    "tax_impact": tax_impact,
                    "notes": (
                        f"{'Gain' if gain_loss > 0 else 'Loss'} of ${abs(gain_loss):,.0f} "
                        f"taxed at {rate:.1%}"
                    )
                })
            else:
                analysis.append({
                    "ticker": trade.ticker,
                    "action": trade.action.value,
                    "quantity": trade.quantity,
                    "tax_impact": 0,
                    "notes": "Purchase - no immediate tax impact"
                })

        return analysis, total_impact

    @staticmethod
    def _is_long_term_average(holding) -> bool:
        """Check if holding is predominantly long-term."""
        if not holding.tax_lots:
            return True  # Assume long-term if no lot info

        total_qty = sum(lot.quantity for lot in holding.tax_lots)
        long_term_qty = sum(
            lot.quantity for lot in holding.tax_lots
            if lot.is_long_term
        )

        return long_term_qty > total_qty / 2

    @staticmethod
    def _generate_recommendations(
        violations: list[WashSaleViolation],
        opportunities: list[TaxOpportunity],
        proposed_trades: list[RecommendedTrade]
    ) -> list[str]:
        """Generate actionable recommendations."""
        recs = []

        if violations:
            recs.append(
                f"WARNING: {len(violations)} potential wash sale violation(s) detected. "
                "Review proposed trades before execution."
            )

        if opportunities:
            top_opp = opportunities[0]
            recs.append(
                f"Consider harvesting {top_opp.ticker} loss for estimated "
                f"${top_opp.estimated_benefit:,.0f} tax benefit."
            )

        if proposed_trades:
            sell_trades = [t for t in proposed_trades if t.action == TradeAction.SELL]
            if sell_trades:
                recs.append(
                    "Use HIFO (Highest In, First Out) lot selection to minimize gains."
                )

        if not recs:
            recs.append("Portfolio is tax-efficient. No immediate action required.")

        return recs

    @staticmethod
    def _build_reasoning(
        violations: list[WashSaleViolation],
        opportunities: list[TaxOpportunity],
        total_impact: float
    ) -> str:
        """Build reasoning explanation."""
        parts = []

        if violations:
            tickers = [v.ticker for v in violations]
            parts.append(
                f"Detected {len(violations)} wash sale risk(s) involving {', '.join(tickers)}. "
                "These trades should be modified or delayed to avoid IRS penalties."
            )

        if opportunities:
            total_benefit = sum(o.estimated_benefit for o in opportunities)
            parts.append(
                f"Identified {len(opportunities)} tax-loss harvesting opportunity(ies) "
                f"with total estimated benefit of ${total_benefit:,.0f}."
            )

        if total_impact > 0:
            parts.append(
                f"Proposed trades would result in estimated tax liability of ${total_impact:,.0f}."
            )
        elif total_impact < 0:
            parts.append(
                f"Proposed trades would generate ${abs(total_impact):,.0f} in realizable losses."
            )

        if not parts:
            parts.append("No significant tax implications identified.")

        return " ".join(parts)
