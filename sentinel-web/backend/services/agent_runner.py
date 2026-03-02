"""
SENTINEL V2 — Agent Runner Service

Orchestrates real LLM agents or offline analyzers based on configuration.
Provides WebSocket status updates between pipeline steps.
Gracefully degrades per-agent if an API call fails.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from src.agents import (
    DriftAgent,
    TaxAgent,
    OfflineDriftAnalyzer,
    OfflineTaxAnalyzer,
    ConflictDetector,
    ScenarioGenerator,
)
from src.contracts.schemas import (
    Portfolio,
    Transaction,
    DriftAgentOutput,
    TaxAgentOutput,
    CoordinatorOutput,
    ConflictInfo,
    Scenario,
)
from src.security import MerkleChain
from src.state import UtilityFunction, UtilityFunctionFactory
from src.contracts.security import AuditEventType
from src.contracts.schemas import AgentType
from src.data import load_transactions
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class AgentRunnerConfig:
    """Configuration for the agent runner."""
    use_real_agents: bool = False
    api_key: str = ""
    model: str = "claude-3-5-haiku-20241022"


class AgentRunner:
    """
    Orchestrates agent execution with real or offline agents.

    Pipeline:
    1. Run DriftAgent (real or offline)
    2. Run TaxAgent with drift recommendations (real or offline)
    3. ConflictDetector.detect_conflicts() (pure logic)
    4. ScenarioGenerator.generate_scenarios() (pure logic)
    5. UtilityFunction scoring (pure logic)

    Falls back to offline per-agent on API failure.
    """

    def __init__(self, config: AgentRunnerConfig, merkle_chain: Optional[MerkleChain] = None):
        self.config = config
        self.merkle_chain = merkle_chain
        self._utility_fn = UtilityFunction()
        self._real_agents_available = config.use_real_agents and bool(config.api_key)

    async def run(
        self,
        portfolio: Portfolio,
        context: dict,
        ws_manager=None,
    ) -> CoordinatorOutput:
        """
        Execute the full agent pipeline.

        Returns CoordinatorOutput with findings, conflicts, and ranked scenarios.
        """
        transactions = self._load_transactions(portfolio.portfolio_id)

        # Step 1 & 2: Run agents
        drift_result, tax_result, agents_used = await self._run_agents(
            portfolio, transactions, context, ws_manager
        )

        # Step 3: Detect conflicts (pure logic)
        if ws_manager:
            await ws_manager.send_agent_activity({
                "agent": "coordinator",
                "status": "active",
                "message": "Detecting conflicts between agent findings..."
            })

        conflicts = ConflictDetector.detect_conflicts(drift_result, tax_result, portfolio)

        if ws_manager and conflicts:
            await ws_manager.send_agent_activity({
                "agent": "coordinator",
                "status": "warning",
                "message": f"CONFLICT DETECTED: {len(conflicts)} conflicts found",
                "conflicts": [
                    {
                        "type": c.conflict_type,
                        "description": c.description,
                        "agents": [a.value for a in c.agents_involved]
                    }
                    for c in conflicts
                ]
            })

        # Step 4: Generate scenarios (pure logic)
        scenarios = ScenarioGenerator.generate_scenarios(
            drift_result, tax_result, conflicts, portfolio
        )

        # Step 5: Score and rank (pure logic)
        weights = UtilityFunctionFactory.get_weights_for_profile(
            portfolio.client_profile.risk_tolerance
        )
        scored = self._utility_fn.rank_scenarios(scenarios, portfolio, weights)

        score_map = {s.scenario_id: s for s in scored}
        for scenario in scenarios:
            scenario.utility_score = score_map.get(scenario.scenario_id)

        scenarios.sort(
            key=lambda s: s.utility_score.total_score if s.utility_score else 0,
            reverse=True
        )
        recommended_id = scored[0].scenario_id if scored else scenarios[0].scenario_id

        # Merkle chain logging
        merkle_hash = ""
        if self.merkle_chain:
            merkle_hash = self.merkle_chain.add_block({
                "event_type": AuditEventType.AGENT_COMPLETED.value,
                "session_id": "web",
                "actor": AgentType.COORDINATOR.value,
                "action": "analysis_complete",
                "resource": portfolio.portfolio_id,
                "agents_used": agents_used,
            })

        return CoordinatorOutput(
            portfolio_id=portfolio.portfolio_id,
            trigger_event="web_event_injection",
            analysis_timestamp=datetime.now(timezone.utc),
            drift_findings=drift_result,
            tax_findings=tax_result,
            conflicts_detected=conflicts,
            scenarios=scenarios,
            recommended_scenario_id=recommended_id,
            merkle_hash=merkle_hash,
        )

    async def _run_agents(
        self,
        portfolio: Portfolio,
        transactions: list[Transaction],
        context: dict,
        ws_manager=None,
    ) -> tuple[DriftAgentOutput, TaxAgentOutput, dict]:
        """Run drift and tax agents, with per-agent fallback."""
        agents_used = {"drift": "offline", "tax": "offline"}

        if not self._real_agents_available:
            logger.info("Using offline agents (no API key or USE_REAL_AGENTS=false)")
            drift_result = OfflineDriftAnalyzer.analyze(portfolio, context)
            tax_result = OfflineTaxAnalyzer.analyze(
                portfolio, transactions, drift_result.recommended_trades, context
            )
            return drift_result, tax_result, agents_used

        # Try real agents with per-agent fallback
        drift_result = await self._run_drift_agent(portfolio, context, ws_manager)
        if drift_result is None:
            logger.warning("Drift agent API call failed, falling back to offline")
            drift_result = OfflineDriftAnalyzer.analyze(portfolio, context)
        else:
            agents_used["drift"] = "real"

        tax_result = await self._run_tax_agent(
            portfolio, transactions, drift_result.recommended_trades, context, ws_manager
        )
        if tax_result is None:
            logger.warning("Tax agent API call failed, falling back to offline")
            tax_result = OfflineTaxAnalyzer.analyze(
                portfolio, transactions, drift_result.recommended_trades, context
            )
        else:
            agents_used["tax"] = "real"

        return drift_result, tax_result, agents_used

    async def _run_drift_agent(
        self,
        portfolio: Portfolio,
        context: dict,
        ws_manager=None,
    ) -> Optional[DriftAgentOutput]:
        """Run real drift agent, return None on failure."""
        try:
            if ws_manager:
                await ws_manager.send_agent_activity({
                    "agent": "drift",
                    "status": "active",
                    "message": "Analyzing portfolio drift and concentration (LLM)..."
                })

            agent = DriftAgent(
                api_key=self.config.api_key,
                model=self.config.model,
            )
            result = await agent.analyze_with_portfolio(portfolio, context)

            if ws_manager:
                await ws_manager.send_agent_activity({
                    "agent": "drift",
                    "status": "complete",
                    "message": f"Found {len(result.concentration_risks)} concentration risks (LLM)",
                    "findings": {
                        "concentration_risks": [
                            {
                                "ticker": r.ticker,
                                "current_weight": r.current_weight,
                                "limit": r.limit,
                                "severity": r.severity.value if hasattr(r.severity, 'value') else str(r.severity),
                            }
                            for r in result.concentration_risks
                        ],
                        "drift_detected": result.drift_detected,
                        "urgency_score": result.urgency_score,
                    }
                })

            return result

        except Exception as e:
            logger.error(f"Drift agent failed: {e}")
            if ws_manager:
                await ws_manager.send_agent_activity({
                    "agent": "drift",
                    "status": "active",
                    "message": f"LLM call failed, using rule-based analysis..."
                })
            return None

    async def _run_tax_agent(
        self,
        portfolio: Portfolio,
        transactions: list[Transaction],
        proposed_trades: list,
        context: dict,
        ws_manager=None,
    ) -> Optional[TaxAgentOutput]:
        """Run real tax agent, return None on failure."""
        try:
            if ws_manager:
                await ws_manager.send_agent_activity({
                    "agent": "tax",
                    "status": "active",
                    "message": "Checking tax implications and wash sale risks (LLM)..."
                })

            agent = TaxAgent(
                api_key=self.config.api_key,
                model=self.config.model,
            )
            result = await agent.analyze_with_portfolio(
                portfolio, transactions, proposed_trades, context
            )

            if ws_manager:
                await ws_manager.send_agent_activity({
                    "agent": "tax",
                    "status": "complete",
                    "message": f"Found {len(result.wash_sale_violations)} wash sale risks, {len(result.tax_opportunities)} opportunities (LLM)",
                    "findings": {
                        "wash_sales": [
                            {
                                "ticker": w.ticker,
                                "days_since_sale": w.days_since_sale,
                                "disallowed_loss": w.disallowed_loss,
                            }
                            for w in result.wash_sale_violations
                        ],
                        "opportunities": [
                            {
                                "ticker": o.ticker,
                                "type": str(o.opportunity_type) if hasattr(o.opportunity_type, 'value') else o.opportunity_type,
                                "benefit": o.estimated_benefit,
                            }
                            for o in result.tax_opportunities
                        ],
                    }
                })

            return result

        except Exception as e:
            logger.error(f"Tax agent failed: {e}")
            if ws_manager:
                await ws_manager.send_agent_activity({
                    "agent": "tax",
                    "status": "active",
                    "message": f"LLM call failed, using rule-based analysis..."
                })
            return None

    def _load_transactions(self, portfolio_id: str) -> list[Transaction]:
        """Load transactions, return empty list on failure."""
        try:
            return load_transactions(portfolio_id, days=60)
        except Exception:
            return []
