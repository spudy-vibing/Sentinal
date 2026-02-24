"""
SENTINEL COORDINATOR AGENT

The "hub" in hub-and-spoke architecture.

Responsibilities:
- Dispatch sub-agents (Drift, Tax) in parallel
- Detect conflicts between agent recommendations
- Generate ranked scenarios with utility scoring
- Manage state transitions through analysis pipeline
- Handle UI actions (approve, what-if)

Reference: docs/IMPLEMENTATION_PLAN.md Phase 3, Step 3.1-3.3
"""

from __future__ import annotations

import asyncio
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from src.contracts.interfaces import ICoordinator, IMerkleChain
from src.contracts.schemas import (
    AgentType,
    Portfolio,
    InputEvent,
    ClientProfile,
    CoordinatorOutput,
    DriftAgentOutput,
    TaxAgentOutput,
    ConflictInfo,
    Scenario,
    ActionStep,
    TradeAction,
    RecommendedTrade,
    UtilityScore,
    UIAction,
    UIActionType,
    UTILITY_WEIGHTS_BY_PROFILE,
)
from src.contracts.security import (
    SessionConfig,
    Permission,
    require_permission,
    AuditEventType,
)
from src.data import load_portfolio, load_transactions
from src.state import (
    SentinelStateMachine,
    StateMachineFactory,
    UtilityFunction,
    UtilityFunctionFactory,
    score_and_rank,
)
from src.skills import get_skill_registry, inject_skills_into_prompt

from .base import BaseAgent, REASONING_MODEL
from .drift_agent import DriftAgent, OfflineDriftAnalyzer
from .tax_agent import TaxAgent, OfflineTaxAnalyzer

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════

COORDINATOR_SYSTEM_PROMPT = """You are the Coordination Agent for a UHNW portfolio monitoring system at a major investment bank.

Your role is to:
1. Synthesize findings from the Drift Agent and Tax Agent
2. Detect conflicts between their recommendations
3. Generate resolution scenarios ranked by utility
4. Present clear, actionable recommendations to human advisors

CONFLICT TYPES:
- WASH_SALE_CONFLICT: Drift Agent recommends buying a recently sold security
- TAX_INEFFICIENT: Recommended trade would trigger unnecessary taxes
- CONTRADICTORY_ACTIONS: Agents recommend opposite actions on same security
- TIMING_CONFLICT: Urgent drift action conflicts with tax timing

SCENARIO GENERATION:
For each analysis, generate 2-4 scenarios:
1. "Optimal Balance" - Best overall utility score
2. "Tax Efficient" - Prioritizes tax savings
3. "Risk First" - Addresses risk immediately
4. "Gradual" - Phased approach over time

IMPORTANT:
- Never recommend actions that would trigger wash sales
- Always explain trade-offs clearly
- Consider client's risk tolerance in all recommendations
- Provide specific quantities and timing, not vague suggestions"""


# ═══════════════════════════════════════════════════════════════════════════
# CONFLICT DETECTOR
# ═══════════════════════════════════════════════════════════════════════════

class ConflictDetector:
    """Detect conflicts between Drift and Tax agent recommendations."""

    @staticmethod
    def detect_conflicts(
        drift_output: DriftAgentOutput,
        tax_output: TaxAgentOutput,
        portfolio: Portfolio
    ) -> list[ConflictInfo]:
        """
        Detect conflicts between agent outputs.

        Returns list of ConflictInfo objects describing each conflict.
        """
        conflicts = []

        # Get all recommended trades from drift agent
        drift_trades = {t.ticker: t for t in drift_output.recommended_trades}

        # Check for wash sale conflicts
        for violation in tax_output.wash_sale_violations:
            if violation.ticker in drift_trades:
                drift_trade = drift_trades[violation.ticker]
                if drift_trade.action == TradeAction.BUY:
                    conflicts.append(ConflictInfo(
                        conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
                        conflict_type="WASH_SALE_CONFLICT",
                        agents_involved=[AgentType.DRIFT, AgentType.TAX],
                        description=(
                            f"Drift Agent recommends buying {violation.ticker}, "
                            f"but Tax Agent detected wash sale risk "
                            f"({violation.days_until_clear} days until clear)"
                        ),
                        resolution_options=[
                            f"Wait {violation.days_until_clear} days before purchasing {violation.ticker}",
                            f"Purchase substitute security instead of {violation.ticker}",
                            "Proceed anyway (loss will be disallowed)"
                        ]
                    ))

        # Check for tax-inefficient sells
        for analysis in tax_output.proposed_trades_analysis:
            ticker = analysis.get("ticker")
            tax_impact = analysis.get("tax_impact", 0)

            if ticker in drift_trades and tax_impact > 50000:  # Significant tax impact
                drift_trade = drift_trades[ticker]
                if drift_trade.action == TradeAction.SELL:
                    # Check urgency - if not urgent, flag for timing
                    if drift_trade.urgency < 7:
                        conflicts.append(ConflictInfo(
                            conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
                            conflict_type="TAX_INEFFICIENT",
                            agents_involved=[AgentType.DRIFT, AgentType.TAX],
                            description=(
                                f"Selling {ticker} would generate ${tax_impact:,.0f} in taxes. "
                                f"Drift urgency is {drift_trade.urgency}/10."
                            ),
                            resolution_options=[
                                f"Proceed with sale (urgency may justify tax cost)",
                                f"Delay sale to harvest losses elsewhere first",
                                f"Sell only partial position to reduce tax impact"
                            ]
                        ))

        # Check for contradictory actions
        buy_tickers = {t.ticker for t in drift_output.recommended_trades if t.action == TradeAction.BUY}
        sell_tickers = {t.ticker for t in drift_output.recommended_trades if t.action == TradeAction.SELL}

        contradictions = buy_tickers & sell_tickers
        for ticker in contradictions:
            conflicts.append(ConflictInfo(
                conflict_id=f"conflict_{uuid.uuid4().hex[:8]}",
                conflict_type="CONTRADICTORY_ACTIONS",
                agents_involved=[AgentType.DRIFT],
                description=f"Both BUY and SELL recommended for {ticker}",
                resolution_options=[
                    f"Review position size targets for {ticker}",
                    f"Execute net action only",
                    "Skip this security"
                ]
            ))

        return conflicts


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

class ScenarioGenerator:
    """Generate resolution scenarios from agent outputs."""

    @staticmethod
    def generate_scenarios(
        drift_output: DriftAgentOutput,
        tax_output: TaxAgentOutput,
        conflicts: list[ConflictInfo],
        portfolio: Portfolio
    ) -> list[Scenario]:
        """
        Generate 2-4 resolution scenarios.

        Each scenario represents a different approach to addressing
        the findings from Drift and Tax agents.
        """
        scenarios = []

        # Scenario 1: Optimal Balance (address all issues, avoid conflicts)
        optimal = ScenarioGenerator._create_optimal_scenario(
            drift_output, tax_output, conflicts, portfolio
        )
        scenarios.append(optimal)

        # Scenario 2: Tax Efficient (minimize tax impact)
        tax_efficient = ScenarioGenerator._create_tax_efficient_scenario(
            drift_output, tax_output, portfolio
        )
        scenarios.append(tax_efficient)

        # Scenario 3: Risk First (address risk immediately, accept tax cost)
        if drift_output.concentration_risks:
            risk_first = ScenarioGenerator._create_risk_first_scenario(
                drift_output, tax_output, portfolio
            )
            scenarios.append(risk_first)

        # Scenario 4: Gradual Rebalance (phased approach)
        if len(drift_output.recommended_trades) > 2:
            gradual = ScenarioGenerator._create_gradual_scenario(
                drift_output, tax_output, portfolio
            )
            scenarios.append(gradual)

        return scenarios

    @staticmethod
    def _create_optimal_scenario(
        drift: DriftAgentOutput,
        tax: TaxAgentOutput,
        conflicts: list[ConflictInfo],
        portfolio: Portfolio
    ) -> Scenario:
        """Create scenario that balances all factors."""
        action_steps = []
        wash_sale_tickers = {v.ticker for v in tax.wash_sale_violations}

        step_num = 1
        for trade in drift.recommended_trades:
            # Skip if would cause wash sale
            if trade.action == TradeAction.BUY and trade.ticker in wash_sale_tickers:
                continue

            action_steps.append(ActionStep(
                step_number=step_num,
                action=trade.action,
                ticker=trade.ticker,
                quantity=trade.quantity,
                timing="immediate" if trade.urgency >= 7 else "within 1 week",
                rationale=trade.rationale
            ))
            step_num += 1

        # Calculate expected outcomes
        total_tax = sum(
            a.get("tax_impact", 0)
            for a in tax.proposed_trades_analysis
        )

        concentration_before = max(
            (r.current_weight for r in drift.concentration_risks),
            default=0
        )
        concentration_after = min(
            (r.limit for r in drift.concentration_risks),
            default=concentration_before
        )

        return Scenario(
            scenario_id=f"scenario_optimal_{uuid.uuid4().hex[:8]}",
            title="Optimal Balance",
            description=(
                "Addresses concentration risks while avoiding wash sales. "
                "Balances risk reduction with tax efficiency."
            ),
            action_steps=action_steps,
            expected_outcomes={
                "concentration_before": concentration_before,
                "concentration_after": concentration_after,
                "tax_impact": total_tax,
                "wash_sale_violations": 0,
                "drift_before": sum(abs(m.drift_pct) for m in drift.drift_metrics),
                "drift_after": sum(abs(m.drift_pct) for m in drift.drift_metrics) * 0.5,
                "urgency_level": drift.urgency_score,
                "addresses_urgent_issues": drift.urgency_score >= 7,
                "issue_urgency": drift.urgency_score,
            },
            risks=[
                f"Tax impact of ${total_tax:,.0f}" if total_tax > 0 else None,
                "Market timing risk on delayed trades",
            ],
            utility_score=None  # Will be calculated by UtilityFunction
        )

    @staticmethod
    def _create_tax_efficient_scenario(
        drift: DriftAgentOutput,
        tax: TaxAgentOutput,
        portfolio: Portfolio
    ) -> Scenario:
        """Create scenario that minimizes tax impact."""
        action_steps = []
        step_num = 1

        # First, harvest any losses
        for opp in tax.tax_opportunities:
            if opp.opportunity_type.value == "harvest_loss":
                holding = portfolio.get_holding(opp.ticker)
                if holding:
                    action_steps.append(ActionStep(
                        step_number=step_num,
                        action=TradeAction.SELL,
                        ticker=opp.ticker,
                        quantity=holding.quantity,
                        timing="immediate",
                        rationale=f"Harvest ${opp.estimated_benefit:,.0f} tax benefit"
                    ))
                    step_num += 1

        # Then, execute only the most urgent drift trades
        for trade in sorted(drift.recommended_trades, key=lambda t: -t.urgency):
            if trade.urgency >= 7:  # Only urgent trades
                action_steps.append(ActionStep(
                    step_number=step_num,
                    action=trade.action,
                    ticker=trade.ticker,
                    quantity=trade.quantity,
                    timing="immediate",
                    rationale=f"[URGENT] {trade.rationale}"
                ))
                step_num += 1

        # Estimate reduced tax impact
        harvest_savings = sum(o.estimated_benefit for o in tax.tax_opportunities)

        return Scenario(
            scenario_id=f"scenario_tax_{uuid.uuid4().hex[:8]}",
            title="Tax Efficient",
            description=(
                "Prioritizes tax-loss harvesting and minimizes tax impact. "
                "Only executes urgent risk actions."
            ),
            action_steps=action_steps,
            expected_outcomes={
                "concentration_before": max((r.current_weight for r in drift.concentration_risks), default=0),
                "concentration_after": max((r.current_weight for r in drift.concentration_risks), default=0) * 0.9,
                "tax_impact": -harvest_savings,  # Negative = savings
                "harvest_opportunities_captured": len(tax.tax_opportunities),
                "wash_sale_violations": 0,
                "drift_before": sum(abs(m.drift_pct) for m in drift.drift_metrics),
                "drift_after": sum(abs(m.drift_pct) for m in drift.drift_metrics) * 0.8,
                "urgency_level": 6,
            },
            risks=[
                "May not fully address concentration risk",
                "Drift may worsen if market moves against positions",
            ],
            utility_score=None
        )

    @staticmethod
    def _create_risk_first_scenario(
        drift: DriftAgentOutput,
        tax: TaxAgentOutput,
        portfolio: Portfolio
    ) -> Scenario:
        """Create scenario that prioritizes risk reduction."""
        action_steps = []
        step_num = 1

        # Execute all concentration risk trades immediately
        for trade in drift.recommended_trades:
            # Find if this addresses concentration risk
            is_concentration_trade = any(
                r.ticker == trade.ticker
                for r in drift.concentration_risks
            )

            if is_concentration_trade or trade.urgency >= 6:
                action_steps.append(ActionStep(
                    step_number=step_num,
                    action=trade.action,
                    ticker=trade.ticker,
                    quantity=trade.quantity,
                    timing="immediate",
                    rationale=f"[RISK PRIORITY] {trade.rationale}"
                ))
                step_num += 1

        total_tax = tax.total_tax_impact

        return Scenario(
            scenario_id=f"scenario_risk_{uuid.uuid4().hex[:8]}",
            title="Risk First",
            description=(
                "Immediately addresses all concentration risks. "
                "Accepts higher tax cost for faster risk reduction."
            ),
            action_steps=action_steps,
            expected_outcomes={
                "concentration_before": max((r.current_weight for r in drift.concentration_risks), default=0),
                "concentration_after": min((r.limit for r in drift.concentration_risks), default=0.15),
                "tax_impact": total_tax,
                "wash_sale_violations": len(tax.wash_sale_violations),
                "drift_before": sum(abs(m.drift_pct) for m in drift.drift_metrics),
                "drift_after": 0.02,  # Near target
                "urgency_level": 9,
                "addresses_urgent_issues": True,
                "issue_urgency": drift.urgency_score,
            },
            risks=[
                f"Significant tax impact of ${total_tax:,.0f}",
                "May trigger wash sale if not careful with timing",
            ],
            utility_score=None
        )

    @staticmethod
    def _create_gradual_scenario(
        drift: DriftAgentOutput,
        tax: TaxAgentOutput,
        portfolio: Portfolio
    ) -> Scenario:
        """Create phased scenario spread over time."""
        action_steps = []
        step_num = 1

        # Sort trades by urgency
        sorted_trades = sorted(drift.recommended_trades, key=lambda t: -t.urgency)

        timings = ["immediate", "within 1 week", "within 2 weeks", "within 1 month"]

        for i, trade in enumerate(sorted_trades):
            timing = timings[min(i, len(timings) - 1)]

            # Reduce quantity for gradual approach
            gradual_qty = trade.quantity * (0.5 if i > 0 else 1.0)

            action_steps.append(ActionStep(
                step_number=step_num,
                action=trade.action,
                ticker=trade.ticker,
                quantity=gradual_qty,
                timing=timing,
                rationale=f"[PHASE {i+1}] {trade.rationale}"
            ))
            step_num += 1

        return Scenario(
            scenario_id=f"scenario_gradual_{uuid.uuid4().hex[:8]}",
            title="Gradual Rebalance",
            description=(
                "Phased approach over 4 weeks. Reduces market impact "
                "and allows for tax planning between phases."
            ),
            action_steps=action_steps,
            expected_outcomes={
                "concentration_before": max((r.current_weight for r in drift.concentration_risks), default=0),
                "concentration_after": max((r.current_weight for r in drift.concentration_risks), default=0) * 0.7,
                "tax_impact": tax.total_tax_impact * 0.7,  # Phased = potentially lower
                "wash_sale_violations": 0,
                "drift_before": sum(abs(m.drift_pct) for m in drift.drift_metrics),
                "drift_after": sum(abs(m.drift_pct) for m in drift.drift_metrics) * 0.3,
                "urgency_level": 5,
            },
            risks=[
                "Market may move unfavorably during phased execution",
                "Requires monitoring between phases",
                "May not address urgent issues fast enough",
            ],
            utility_score=None
        )


# ═══════════════════════════════════════════════════════════════════════════
# COORDINATOR AGENT
# ═══════════════════════════════════════════════════════════════════════════

class Coordinator(BaseAgent, ICoordinator):
    """
    Coordinator Agent - the hub in hub-and-spoke architecture.

    Orchestrates Drift and Tax agents, resolves conflicts,
    and generates ranked recommendation scenarios.

    Usage:
        coordinator = Coordinator(session=session, merkle_chain=chain)
        result = await coordinator.execute_analysis(
            portfolio_id="portfolio_a",
            event=market_event,
            client_profile=profile
        )
    """

    def __init__(
        self,
        session: Optional[SessionConfig] = None,
        merkle_chain: Optional[IMerkleChain] = None,
        api_key: Optional[str] = None,
        use_offline_agents: bool = False,
    ):
        """
        Initialize Coordinator.

        Args:
            session: Security session for RBAC
            merkle_chain: Audit chain for logging
            api_key: Anthropic API key
            use_offline_agents: If True, use offline analyzers (no API calls)
        """
        super().__init__(
            agent_type=AgentType.COORDINATOR,
            system_prompt=COORDINATOR_SYSTEM_PROMPT,
            model=REASONING_MODEL,
            session=session,
            merkle_chain=merkle_chain,
            api_key=api_key if not use_offline_agents else "offline-mode",
        )

        self._use_offline = use_offline_agents
        self._utility_fn = UtilityFunction()

        # Create sub-agents (will be initialized on first use)
        self._drift_agent: Optional[DriftAgent] = None
        self._tax_agent: Optional[TaxAgent] = None

    def _get_drift_agent(self) -> DriftAgent:
        """Get or create Drift Agent."""
        if self._drift_agent is None:
            self._drift_agent = DriftAgent(
                session=self._session,
                merkle_chain=self._audit_chain,
            )
        return self._drift_agent

    def _get_tax_agent(self) -> TaxAgent:
        """Get or create Tax Agent."""
        if self._tax_agent is None:
            self._tax_agent = TaxAgent(
                session=self._session,
                merkle_chain=self._audit_chain,
            )
        return self._tax_agent

    @require_permission(Permission.WRITE_RECOMMENDATIONS)
    async def execute_analysis(
        self,
        portfolio_id: str,
        event: InputEvent,
        client_profile: Optional[ClientProfile] = None
    ) -> CoordinatorOutput:
        """
        Execute full analysis pipeline.

        1. Load portfolio and context
        2. Dispatch Drift and Tax agents in parallel
        3. Detect conflicts between findings
        4. Generate resolution scenarios
        5. Score and rank scenarios
        6. Return comprehensive output

        Args:
            portfolio_id: Portfolio to analyze
            event: Triggering event
            client_profile: Override client profile (optional)

        Returns:
            CoordinatorOutput with all findings and recommendations
        """
        logger.info(f"Starting analysis for portfolio {portfolio_id}")

        # Load portfolio
        portfolio = load_portfolio(portfolio_id)
        transactions = load_transactions(portfolio_id, days=60)
        profile = client_profile or portfolio.client_profile

        # Build context for skill discovery
        context = {
            "holdings": portfolio.holdings,
            "recent_transactions": transactions,
            "concentration_limit": profile.concentration_limit,
            "market_event": event.model_dump() if hasattr(event, "model_dump") else {},
        }

        # Discover relevant skills
        skill_registry = get_skill_registry()
        relevant_skills = skill_registry.discover_relevant_skills(context)
        logger.debug(f"Discovered skills: {relevant_skills}")

        # Dispatch agents in parallel
        drift_result, tax_result = await self._dispatch_agents(
            portfolio, transactions, context
        )

        # Detect conflicts
        conflicts = ConflictDetector.detect_conflicts(
            drift_result, tax_result, portfolio
        )
        logger.info(f"Detected {len(conflicts)} conflicts")

        # Generate scenarios
        scenarios = ScenarioGenerator.generate_scenarios(
            drift_result, tax_result, conflicts, portfolio
        )

        # Score and rank scenarios
        weights = UtilityFunctionFactory.get_weights_for_profile(
            profile.risk_tolerance
        )
        scored = self._utility_fn.rank_scenarios(scenarios, portfolio, weights)

        # Attach scores to scenarios
        score_map = {s.scenario_id: s for s in scored}
        for scenario in scenarios:
            scenario.utility_score = score_map.get(scenario.scenario_id)

        # Sort scenarios by score
        scenarios.sort(
            key=lambda s: s.utility_score.total_score if s.utility_score else 0,
            reverse=True
        )

        # Get recommended scenario
        recommended_id = scored[0].scenario_id if scored else scenarios[0].scenario_id

        # Log to Merkle chain
        merkle_hash = self._log_analysis_complete(
            portfolio_id, len(conflicts), len(scenarios), recommended_id
        )

        return CoordinatorOutput(
            portfolio_id=portfolio_id,
            trigger_event=str(event.event_id) if hasattr(event, "event_id") else "manual",
            analysis_timestamp=datetime.now(timezone.utc),
            drift_findings=drift_result,
            tax_findings=tax_result,
            conflicts_detected=conflicts,
            scenarios=scenarios,
            recommended_scenario_id=recommended_id,
            merkle_hash=merkle_hash
        )

    async def _dispatch_agents(
        self,
        portfolio: Portfolio,
        transactions: list,
        context: dict
    ) -> tuple[DriftAgentOutput, TaxAgentOutput]:
        """
        Dispatch Drift and Tax agents in parallel.

        Uses asyncio.gather for concurrent execution.
        """
        if self._use_offline:
            # Use offline analyzers
            drift_result = OfflineDriftAnalyzer.analyze(portfolio, context)
            tax_result = OfflineTaxAnalyzer.analyze(
                portfolio,
                transactions,
                drift_result.recommended_trades,
                context
            )
            return drift_result, tax_result

        # Use real agents with parallel dispatch
        drift_task = self._get_drift_agent().analyze_with_portfolio(
            portfolio, context
        )
        tax_task = self._get_tax_agent().analyze_with_portfolio(
            portfolio, transactions, [], context
        )

        drift_result, tax_result = await asyncio.gather(
            drift_task, tax_task
        )

        # Now run tax agent again with drift recommendations
        tax_result = await self._get_tax_agent().analyze_with_portfolio(
            portfolio,
            transactions,
            drift_result.recommended_trades,
            context
        )

        return drift_result, tax_result

    async def handle_ui_action(
        self,
        action: UIAction,
        current_output: CoordinatorOutput
    ) -> CoordinatorOutput:
        """
        Handle UI action from Canvas.

        Args:
            action: UI action (approve, reject, what-if, adjust)
            current_output: Current coordinator output

        Returns:
            Updated CoordinatorOutput
        """
        if action.action_type == UIActionType.APPROVE:
            return await self._handle_approve(action, current_output)
        elif action.action_type == UIActionType.REJECT:
            return await self._handle_reject(action, current_output)
        elif action.action_type == UIActionType.WHAT_IF:
            return await self._handle_what_if(action, current_output)
        elif action.action_type == UIActionType.ADJUST:
            return await self._handle_adjust(action, current_output)
        else:
            raise ValueError(f"Unknown action type: {action.action_type}")

    async def _handle_approve(
        self,
        action: UIAction,
        output: CoordinatorOutput
    ) -> CoordinatorOutput:
        """Handle scenario approval."""
        logger.info(f"Scenario {action.scenario_id} approved")

        # Log to Merkle chain
        if self._audit_chain:
            self._audit_chain.add_block({
                "event_type": AuditEventType.ACTION_APPROVED.value,
                "session_id": self._session.session_id if self._session else "unknown",
                "actor": "human_advisor",
                "action": "approve_scenario",
                "resource": action.scenario_id,
                "portfolio_id": output.portfolio_id,
            })

        return output

    async def _handle_reject(
        self,
        action: UIAction,
        output: CoordinatorOutput
    ) -> CoordinatorOutput:
        """Handle scenario rejection."""
        logger.info(f"Scenario {action.scenario_id} rejected")

        # Log to Merkle chain
        if self._audit_chain:
            self._audit_chain.add_block({
                "event_type": AuditEventType.ACTION_REJECTED.value,
                "session_id": self._session.session_id if self._session else "unknown",
                "actor": "human_advisor",
                "action": "reject_scenario",
                "resource": action.scenario_id,
                "portfolio_id": output.portfolio_id,
            })

        return output

    async def _handle_what_if(
        self,
        action: UIAction,
        output: CoordinatorOutput
    ) -> CoordinatorOutput:
        """Handle what-if scenario request."""
        logger.info(f"What-if requested for scenario {action.scenario_id}")
        # In production, this would re-run analysis with modified parameters
        return output

    async def _handle_adjust(
        self,
        action: UIAction,
        output: CoordinatorOutput
    ) -> CoordinatorOutput:
        """Handle scenario adjustment (e.g., slider changes)."""
        logger.info(f"Adjustment requested: {action.parameters}")
        # In production, this would recalculate with new parameters
        return output

    def _log_analysis_complete(
        self,
        portfolio_id: str,
        conflict_count: int,
        scenario_count: int,
        recommended_id: str
    ) -> str:
        """Log analysis completion to Merkle chain."""
        if not self._audit_chain:
            return ""

        return self._audit_chain.add_block({
            "event_type": AuditEventType.AGENT_COMPLETED.value,
            "session_id": self._session.session_id if self._session else "unknown",
            "actor": AgentType.COORDINATOR.value,
            "action": "analysis_complete",
            "resource": portfolio_id,
            "conflicts_detected": conflict_count,
            "scenarios_generated": scenario_count,
            "recommended_scenario": recommended_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # Required abstract method from BaseAgent
    async def analyze(self, portfolio_id: str, context: dict):
        """Redirect to execute_analysis."""
        from src.contracts.schemas import InputEvent, EventType
        event = InputEvent(
            event_id=f"manual_{uuid.uuid4().hex[:8]}",
            event_type=EventType.HEARTBEAT,
            source="manual",
            timestamp=datetime.now(timezone.utc),
            payload=context
        )
        return await self.execute_analysis(portfolio_id, event)


# ═══════════════════════════════════════════════════════════════════════════
# OFFLINE COORDINATOR (for testing)
# ═══════════════════════════════════════════════════════════════════════════

class OfflineCoordinator:
    """
    Offline coordinator that doesn't require API calls.

    Uses OfflineDriftAnalyzer and OfflineTaxAnalyzer for testing.
    """

    def __init__(self, merkle_chain: Optional[IMerkleChain] = None):
        self._merkle_chain = merkle_chain
        self._utility_fn = UtilityFunction()

    def execute_analysis(
        self,
        portfolio: Portfolio,
        transactions: list = None,
        context: dict = None
    ) -> CoordinatorOutput:
        """
        Execute analysis using offline analyzers.

        Returns same structure as Coordinator but without API calls.
        """
        transactions = transactions or []
        context = context or {}

        # Run drift analysis
        drift_result = OfflineDriftAnalyzer.analyze(portfolio, context)

        # Run tax analysis with drift recommendations
        tax_result = OfflineTaxAnalyzer.analyze(
            portfolio,
            transactions,
            drift_result.recommended_trades,
            context
        )

        # Detect conflicts
        conflicts = ConflictDetector.detect_conflicts(
            drift_result, tax_result, portfolio
        )

        # Generate scenarios
        scenarios = ScenarioGenerator.generate_scenarios(
            drift_result, tax_result, conflicts, portfolio
        )

        # Score scenarios
        weights = UtilityFunctionFactory.get_weights_for_profile(
            portfolio.client_profile.risk_tolerance
        )
        scored = self._utility_fn.rank_scenarios(scenarios, portfolio, weights)

        # Attach scores
        score_map = {s.scenario_id: s for s in scored}
        for scenario in scenarios:
            scenario.utility_score = score_map.get(scenario.scenario_id)

        scenarios.sort(
            key=lambda s: s.utility_score.total_score if s.utility_score else 0,
            reverse=True
        )

        recommended_id = scored[0].scenario_id if scored else scenarios[0].scenario_id

        # Log to Merkle chain
        merkle_hash = ""
        if self._merkle_chain:
            merkle_hash = self._merkle_chain.add_block({
                "event_type": AuditEventType.AGENT_COMPLETED.value,
                "session_id": "offline",
                "actor": AgentType.COORDINATOR.value,
                "action": "offline_analysis_complete",
                "resource": portfolio.portfolio_id,
            })

        return CoordinatorOutput(
            portfolio_id=portfolio.portfolio_id,
            trigger_event="offline_analysis",
            analysis_timestamp=datetime.now(timezone.utc),
            drift_findings=drift_result,
            tax_findings=tax_result,
            conflicts_detected=conflicts,
            scenarios=scenarios,
            recommended_scenario_id=recommended_id,
            merkle_hash=merkle_hash
        )
