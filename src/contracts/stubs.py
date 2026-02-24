"""
SENTINEL STUBS — Mock implementations for parallel development.

Replace these with real implementations as they're built.
Use these for testing before real implementations are ready.

Reference: docs/IMPLEMENTATION_PLAN.md Phase 0
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from .interfaces import (
    IGateway,
    IDriftAgent,
    ITaxAgent,
    ICoordinator,
    IStorage,
    IContextManager,
    IMerkleChain,
    IUtilityFunction,
    ICanvasGenerator,
    ISecurityEnforcer,
    ISandbox,
    IEncryption,
    IStateMachine,
    ISkillRegistry,
    IPersonaRouter,
)
from .schemas import (
    InputEvent,
    Portfolio,
    Holding,
    TaxLot,
    TargetAllocation,
    ClientProfile,
    Transaction,
    DriftAgentOutput,
    TaxAgentOutput,
    ConcentrationRisk,
    DriftMetric,
    RecommendedTrade,
    WashSaleViolation,
    TaxOpportunity,
    Scenario,
    ActionStep,
    ConflictInfo,
    CoordinatorOutput,
    UtilityScore,
    UtilityWeights,
    DimensionScore,
    UIAction,
    AgentType,
    TradeAction,
    RiskProfile,
    Severity,
    DriftDirection,
    TaxOpportunityType,
    SystemState,
    UTILITY_WEIGHTS_BY_PROFILE,
)
from .security import (
    Permission,
    SessionConfig,
    EncryptedField,
    Role,
    SessionType,
    AuditEventType,
)


# ═══════════════════════════════════════════════════════════════════════════
# STUB: Gateway
# ═══════════════════════════════════════════════════════════════════════════

class StubGateway(IGateway):
    """Stub gateway for testing."""

    def __init__(self):
        self.events: list[InputEvent] = []
        self.queues: dict[str, asyncio.Queue] = {}
        self.handlers: dict[str, callable] = {}

    async def submit(self, event: InputEvent) -> str:
        self.events.append(event)
        if event.session_id not in self.queues:
            self.queues[event.session_id] = asyncio.Queue()
        await self.queues[event.session_id].put((event.priority, event))
        return event.event_id

    async def process_session(self, session_id: str) -> None:
        if session_id not in self.queues:
            return
        while not self.queues[session_id].empty():
            _, event = await self.queues[session_id].get()
            handler = self.handlers.get(event.event_type.value)
            if handler:
                await handler(event)

    def register_handler(self, event_type: str, handler: callable) -> None:
        self.handlers[event_type] = handler


# ═══════════════════════════════════════════════════════════════════════════
# STUB: Drift Agent
# ═══════════════════════════════════════════════════════════════════════════

class StubDriftAgent(IDriftAgent):
    """Stub drift agent returning mock data for NVDA concentration scenario."""

    async def analyze(
        self,
        portfolio_id: str,
        context: dict
    ) -> DriftAgentOutput:
        return DriftAgentOutput(
            portfolio_id=portfolio_id,
            analysis_timestamp=datetime.now(timezone.utc),
            drift_detected=True,
            concentration_risks=[
                ConcentrationRisk(
                    ticker="NVDA",
                    current_weight=0.17,
                    limit=0.15,
                    excess=0.02,
                    severity=Severity.HIGH
                )
            ],
            drift_metrics=[
                DriftMetric(
                    asset_class="Technology",
                    target_weight=0.25,
                    current_weight=0.29,
                    drift_pct=0.04,
                    drift_direction=DriftDirection.OVER
                ),
                DriftMetric(
                    asset_class="Fixed Income",
                    target_weight=0.20,
                    current_weight=0.18,
                    drift_pct=0.02,
                    drift_direction=DriftDirection.UNDER
                )
            ],
            recommended_trades=[
                RecommendedTrade(
                    ticker="NVDA",
                    action=TradeAction.SELL,
                    quantity=15000,
                    rationale="Reduce concentration risk below 15% limit",
                    urgency=7,
                    estimated_tax_impact=-50000
                )
            ],
            urgency_score=7,
            reasoning="NVDA concentration at 17% exceeds 15% limit. Tech sector overweight by 4%. Recommend reducing NVDA position to restore target allocation."
        )

    def get_agent_type(self) -> AgentType:
        return AgentType.DRIFT


# ═══════════════════════════════════════════════════════════════════════════
# STUB: Tax Agent
# ═══════════════════════════════════════════════════════════════════════════

class StubTaxAgent(ITaxAgent):
    """Stub tax agent returning mock wash sale violation."""

    async def analyze(
        self,
        portfolio_id: str,
        context: dict,
        proposed_trades: list[RecommendedTrade]
    ) -> TaxAgentOutput:
        return TaxAgentOutput(
            portfolio_id=portfolio_id,
            analysis_timestamp=datetime.now(timezone.utc),
            wash_sale_violations=[
                WashSaleViolation(
                    ticker="NVDA",
                    prior_sale_date=datetime.now(timezone.utc) - timedelta(days=15),
                    days_since_sale=15,
                    disallowed_loss=25000.0,
                    recommendation="Wait 16 more days to clear wash sale window, or use AMD as correlated substitute"
                )
            ],
            tax_opportunities=[
                TaxOpportunity(
                    ticker="AMD",
                    opportunity_type=TaxOpportunityType.HARVEST_LOSS,
                    estimated_benefit=15000.0,
                    action_required="Sell AMD lots with embedded losses before year-end"
                )
            ],
            proposed_trades_analysis=[
                {
                    "ticker": "NVDA",
                    "proposed_action": "sell",
                    "wash_sale_risk": True,
                    "days_until_clear": 16,
                    "estimated_tax_impact": -25000
                }
            ],
            total_tax_impact=-25000.0,
            recommendations=[
                "Avoid selling NVDA for 16 days to clear wash sale window",
                "Consider AMD as correlated substitute to maintain sector exposure",
                "Harvest AMD losses before year-end if selling NVDA"
            ],
            reasoning="NVDA sale would trigger wash sale due to prior sale 15 days ago. Recommend waiting or using AMD substitute to avoid $25K disallowed loss."
        )

    def get_agent_type(self) -> AgentType:
        return AgentType.TAX


# ═══════════════════════════════════════════════════════════════════════════
# STUB: Storage
# ═══════════════════════════════════════════════════════════════════════════

class StubStorage(IStorage):
    """Stub storage with sample portfolio data."""

    def __init__(self):
        self.portfolios = self._create_sample_portfolios()
        self.transactions = self._create_sample_transactions()
        self.recommendations: list[CoordinatorOutput] = []

    def _create_sample_portfolios(self) -> dict[str, Portfolio]:
        """Create sample portfolios for testing."""
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
                        tax_lots=[
                            TaxLot(
                                lot_id="LOT_001",
                                purchase_date=datetime(2023, 1, 15),
                                purchase_price=250.0,
                                quantity=5000,
                                cost_basis=1_250_000
                            ),
                            TaxLot(
                                lot_id="LOT_002",
                                purchase_date=datetime(2023, 6, 1),
                                purchase_price=400.0,
                                quantity=5000,
                                cost_basis=2_000_000
                            )
                        ],
                        sector="Technology",
                        asset_class="US Equities"
                    ),
                    Holding(
                        ticker="AMD",
                        quantity=20000,
                        current_price=150.0,
                        market_value=3_000_000,
                        portfolio_weight=0.06,
                        cost_basis=3_500_000,
                        unrealized_gain_loss=-500_000,
                        sector="Technology",
                        asset_class="US Equities"
                    ),
                    Holding(
                        ticker="AAPL",
                        quantity=15000,
                        current_price=180.0,
                        market_value=2_700_000,
                        portfolio_weight=0.054,
                        cost_basis=2_000_000,
                        unrealized_gain_loss=700_000,
                        sector="Technology",
                        asset_class="US Equities"
                    ),
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

    def _create_sample_transactions(self) -> dict[str, list[Transaction]]:
        """Create sample transactions for wash sale testing."""
        return {
            "UHNW_001": [
                Transaction(
                    transaction_id="TXN_001",
                    portfolio_id="UHNW_001",
                    ticker="NVDA",
                    action=TradeAction.SELL,
                    quantity=5000,
                    price=870.0,
                    timestamp=datetime.now(timezone.utc) - timedelta(days=15),
                    wash_sale_disallowed=0
                )
            ]
        }

    def get_portfolio(self, portfolio_id: str) -> Portfolio:
        if portfolio_id not in self.portfolios:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        return self.portfolios[portfolio_id]

    def get_transactions(
        self,
        portfolio_id: str,
        days: int = 30
    ) -> list[Transaction]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return [
            t for t in self.transactions.get(portfolio_id, [])
            if t.timestamp >= cutoff
        ]

    def save_recommendation(self, output: CoordinatorOutput) -> None:
        self.recommendations.append(output)

    def list_portfolios(self) -> list[str]:
        return list(self.portfolios.keys())


# ═══════════════════════════════════════════════════════════════════════════
# STUB: Merkle Chain
# ═══════════════════════════════════════════════════════════════════════════

class StubMerkleChain(IMerkleChain):
    """Stub Merkle chain for audit logging."""

    def __init__(self):
        self.blocks: list[dict] = []
        self._add_genesis_block()

    def _add_genesis_block(self):
        genesis = {
            "index": 0,
            "event_type": "system_initialized",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {"message": "Sentinel initialized"},
            "previous_hash": "0" * 64,
            "hash": self._hash({"index": 0, "previous_hash": "0" * 64})
        }
        self.blocks.append(genesis)

    def _hash(self, data: dict) -> str:
        return hashlib.sha256(
            json.dumps(data, sort_keys=True, default=str).encode()
        ).hexdigest()

    def add_block(self, data: dict) -> str:
        previous_hash = self.blocks[-1]["hash"]
        block = {
            "index": len(self.blocks),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
            "previous_hash": previous_hash,
            "hash": ""
        }
        block["hash"] = self._hash(block)
        self.blocks.append(block)
        return block["hash"]

    def verify_integrity(self) -> bool:
        for i in range(1, len(self.blocks)):
            if self.blocks[i]["previous_hash"] != self.blocks[i - 1]["hash"]:
                return False
            expected_hash = self._hash({
                "index": self.blocks[i]["index"],
                "timestamp": self.blocks[i]["timestamp"],
                "data": self.blocks[i]["data"],
                "previous_hash": self.blocks[i]["previous_hash"],
                "hash": ""
            })
            if self.blocks[i]["hash"] != expected_hash:
                return False
        return True

    def get_root_hash(self) -> str:
        return self.blocks[-1]["hash"]

    def get_block_count(self) -> int:
        return len(self.blocks)

    def export_chain(self) -> list[dict]:
        return self.blocks.copy()


# ═══════════════════════════════════════════════════════════════════════════
# STUB: Utility Function
# ═══════════════════════════════════════════════════════════════════════════

class StubUtilityFunction(IUtilityFunction):
    """Stub utility function with mock scoring."""

    def score_scenario(
        self,
        scenario: Scenario,
        portfolio: Portfolio,
        weights: UtilityWeights
    ) -> UtilityScore:
        # Generate deterministic scores based on scenario_id
        seed = hash(scenario.scenario_id) % 100
        raw_scores = {
            "risk_reduction": 5 + (seed % 5),
            "tax_savings": 6 + ((seed + 10) % 4),
            "goal_alignment": 5 + ((seed + 20) % 5),
            "transaction_cost": 7 + ((seed + 30) % 3),
            "urgency": 5 + ((seed + 40) % 5),
        }
        return UtilityScore.calculate(
            scenario_id=scenario.scenario_id,
            raw_scores=raw_scores,
            weights=weights
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


# ═══════════════════════════════════════════════════════════════════════════
# STUB: Context Manager
# ═══════════════════════════════════════════════════════════════════════════

class StubContextManager(IContextManager):
    """Stub context manager for hot/cold memory."""

    def __init__(self, max_tokens: int = 100_000):
        self.max_tokens = max_tokens
        self.token_count = 0
        self.context: list[dict] = []
        self.memory: list[dict] = []

    def add_to_context(self, item: dict, estimated_tokens: int) -> None:
        if self.token_count + estimated_tokens > self.max_tokens:
            self.flush_to_memory()
        self.context.append(item)
        self.token_count += estimated_tokens

    def get_context(self) -> list[dict]:
        return self.context.copy()

    def flush_to_memory(self) -> None:
        # Move all but last 5 items to memory
        if len(self.context) > 5:
            self.memory.extend(self.context[:-5])
            self.context = self.context[-5:]
            self.token_count = sum(100 for _ in self.context)  # Rough estimate

    def search_memory(self, query: str, hybrid: bool = True) -> list[dict]:
        # Simple keyword search
        query_lower = query.lower()
        return [
            item for item in self.memory
            if query_lower in json.dumps(item).lower()
        ]


# ═══════════════════════════════════════════════════════════════════════════
# STUB: Security
# ═══════════════════════════════════════════════════════════════════════════

class StubSecurityEnforcer(ISecurityEnforcer):
    """Stub security enforcer."""

    def check_permission(
        self,
        session: SessionConfig,
        required: Permission
    ) -> bool:
        return session.has_permission(required)

    def enforce_permission(
        self,
        session: SessionConfig,
        required: Permission
    ) -> None:
        if not self.check_permission(session, required):
            raise PermissionError(
                f"Permission {required.name} required"
            )


class StubSandbox(ISandbox):
    """Stub sandbox that runs code directly (no Docker)."""

    async def execute(
        self,
        session: SessionConfig,
        code: callable
    ) -> dict:
        # In stub, just execute directly
        if asyncio.iscoroutinefunction(code):
            result = await code()
        else:
            result = code()
        return {"result": result, "sandboxed": session.requires_sandbox}


class StubEncryption(IEncryption):
    """Stub encryption using base64 (NOT SECURE - for testing only)."""

    def encrypt_field(self, plaintext: str) -> EncryptedField:
        import base64
        encoded = base64.b64encode(plaintext.encode())
        return EncryptedField(
            ciphertext=encoded,
            encrypted_dek=b"stub_dek",
            nonce=b"stub_nonce12",
            tag=b"stub_tag_16bytes",
            key_version=1
        )

    def decrypt_field(self, encrypted: EncryptedField) -> str:
        import base64
        return base64.b64decode(encrypted.ciphertext).decode()


# ═══════════════════════════════════════════════════════════════════════════
# STUB: State Machine
# ═══════════════════════════════════════════════════════════════════════════

class StubStateMachine(IStateMachine):
    """Stub state machine."""

    VALID_TRANSITIONS = {
        SystemState.MONITOR: [SystemState.DETECT],
        SystemState.DETECT: [SystemState.ANALYZE, SystemState.MONITOR],
        SystemState.ANALYZE: [SystemState.CONFLICT_RESOLUTION, SystemState.RECOMMEND],
        SystemState.CONFLICT_RESOLUTION: [SystemState.RECOMMEND],
        SystemState.RECOMMEND: [SystemState.APPROVED, SystemState.MONITOR],
        SystemState.APPROVED: [SystemState.EXECUTE],
        SystemState.EXECUTE: [SystemState.MONITOR],
    }

    def __init__(self, initial_state: SystemState = SystemState.MONITOR):
        self.state = initial_state
        self.history: list[dict] = []

    def get_state(self) -> str:
        return self.state.value

    def can_transition(self, to_state: str) -> bool:
        target = SystemState(to_state)
        valid = self.VALID_TRANSITIONS.get(self.state, [])
        return target in valid

    def transition(self, to_state: str, metadata: dict = None) -> bool:
        if not self.can_transition(to_state):
            raise ValueError(
                f"Invalid transition: {self.state.value} -> {to_state}"
            )
        old_state = self.state
        self.state = SystemState(to_state)
        self.history.append({
            "from": old_state.value,
            "to": to_state,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        })
        return True

    def get_transition_history(self) -> list[dict]:
        return self.history.copy()


# ═══════════════════════════════════════════════════════════════════════════
# STUB: Skill Registry
# ═══════════════════════════════════════════════════════════════════════════

class StubSkillRegistry(ISkillRegistry):
    """Stub skill registry."""

    SKILLS = {
        "concentration_risk": {
            "triggers": ["position_weight > 0.15"],
            "token_cost": 500,
            "content": "# Concentration Risk Analysis\n\nCheck positions exceeding concentration limits..."
        },
        "wash_sale": {
            "triggers": ["recent_sale_within_30_days"],
            "token_cost": 600,
            "content": "# Wash Sale Rules\n\nIRS wash sale rule applies when..."
        },
        "tax_loss_harvesting": {
            "triggers": ["unrealized_loss > 10000"],
            "token_cost": 400,
            "content": "# Tax Loss Harvesting\n\nOpportunities to harvest losses..."
        }
    }

    def discover_relevant_skills(
        self,
        context: dict,
        token_budget: int = 10_000
    ) -> list[str]:
        relevant = []
        total_tokens = 0

        # Check concentration risk
        holdings = context.get("holdings", [])
        if any(getattr(h, "portfolio_weight", 0) > 0.15 for h in holdings):
            if total_tokens + 500 <= token_budget:
                relevant.append("concentration_risk")
                total_tokens += 500

        # Check wash sale
        transactions = context.get("recent_transactions", [])
        if len(transactions) > 0:
            if total_tokens + 600 <= token_budget:
                relevant.append("wash_sale")
                total_tokens += 600

        return relevant

    def load_skill(self, skill_name: str) -> str:
        skill = self.SKILLS.get(skill_name)
        if skill:
            return skill["content"]
        raise ValueError(f"Skill {skill_name} not found")

    def list_skills(self) -> list[dict]:
        return [
            {"name": name, **{k: v for k, v in data.items() if k != "content"}}
            for name, data in self.SKILLS.items()
        ]


# ═══════════════════════════════════════════════════════════════════════════
# STUB: Persona Router
# ═══════════════════════════════════════════════════════════════════════════

class StubPersonaRouter(IPersonaRouter):
    """Stub persona router."""

    PERSONAS = {
        RiskProfile.CONSERVATIVE: {
            "model": "claude-sonnet-4-5-20250514",
            "prompt_suffix": "\n\nPERSONA: Risk-Averse Advisor\n- Emphasize capital preservation\n- Flag ANY concentration risk >10%\n- Use conservative language",
            "utility_weights": UTILITY_WEIGHTS_BY_PROFILE[RiskProfile.CONSERVATIVE]
        },
        RiskProfile.MODERATE_GROWTH: {
            "model": "claude-sonnet-4-5-20250514",
            "prompt_suffix": "\n\nPERSONA: Balanced Growth Advisor\n- Balance risk and return\n- Prioritize tax efficiency\n- Neutral, professional tone",
            "utility_weights": UTILITY_WEIGHTS_BY_PROFILE[RiskProfile.MODERATE_GROWTH]
        },
        RiskProfile.AGGRESSIVE: {
            "model": "claude-sonnet-4-5-20250514",
            "prompt_suffix": "\n\nPERSONA: Growth-Focused Advisor\n- Emphasize long-term appreciation\n- Accept higher volatility\n- Direct, action-oriented language",
            "utility_weights": UTILITY_WEIGHTS_BY_PROFILE[RiskProfile.AGGRESSIVE]
        }
    }

    def get_persona(self, client_profile: ClientProfile) -> dict:
        return self.PERSONAS.get(
            client_profile.risk_tolerance,
            self.PERSONAS[RiskProfile.MODERATE_GROWTH]
        )

    def build_prompt(
        self,
        base_prompt: str,
        client_profile: ClientProfile
    ) -> str:
        persona = self.get_persona(client_profile)
        return base_prompt + persona["prompt_suffix"]


# ═══════════════════════════════════════════════════════════════════════════
# STUB: Canvas Generator
# ═══════════════════════════════════════════════════════════════════════════

class StubCanvasGenerator(ICanvasGenerator):
    """Stub canvas generator returning minimal HTML."""

    def generate_html(
        self,
        scenarios: list[Scenario],
        utility_scores: list[UtilityScore],
        portfolio_id: str
    ) -> str:
        cards = ""
        for scenario, score in zip(scenarios, utility_scores):
            cards += f"""
            <div class="s-card" data-scenario-id="{scenario.scenario_id}">
                <h3>{scenario.title}</h3>
                <p>Score: {score.total_score:.1f}/100</p>
                <button data-a2ui-action="approve">Approve</button>
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head><title>Sentinel Canvas - {portfolio_id}</title></head>
        <body>
            <h1>Recommendations for {portfolio_id}</h1>
            {cards}
        </body>
        </html>
        """

    def handle_action(self, action: UIAction) -> dict:
        return {
            "status": "received",
            "action": action.action_type.value,
            "scenario_id": action.scenario_id
        }


# ═══════════════════════════════════════════════════════════════════════════
# STUB: Coordinator
# ═══════════════════════════════════════════════════════════════════════════

class StubCoordinator(ICoordinator):
    """Stub coordinator for testing orchestration."""

    def __init__(self):
        self.drift_agent = StubDriftAgent()
        self.tax_agent = StubTaxAgent()
        self.utility_fn = StubUtilityFunction()
        self.merkle_chain = StubMerkleChain()

    async def execute_analysis(
        self,
        portfolio_id: str,
        event: InputEvent,
        client_profile: ClientProfile
    ) -> CoordinatorOutput:
        # Parallel dispatch
        drift_result, tax_result = await asyncio.gather(
            self.drift_agent.analyze(portfolio_id, {"event": event}),
            self.tax_agent.analyze(portfolio_id, {"event": event}, [])
        )

        # Detect conflict
        conflicts = []
        if drift_result.recommended_trades and tax_result.wash_sale_violations:
            conflicts.append(ConflictInfo(
                conflict_id=f"conflict_{uuid4().hex[:8]}",
                conflict_type="drift_vs_wash_sale",
                agents_involved=[AgentType.DRIFT, AgentType.TAX],
                description="Drift agent recommends selling NVDA, but Tax agent detects wash sale violation",
                resolution_options=[
                    "Wait for wash sale window to clear",
                    "Use correlated substitute (AMD)",
                    "Accept wash sale penalty"
                ]
            ))

        # Generate scenarios
        scenarios = [
            Scenario(
                scenario_id="scenario_a",
                title="Sell NVDA Now (Accept Wash Sale)",
                description="Immediately reduce NVDA concentration, accepting wash sale penalty",
                action_steps=[
                    ActionStep(step_number=1, action=TradeAction.SELL, ticker="NVDA", quantity=15000, timing="immediate", rationale="Reduce concentration")
                ],
                expected_outcomes={"concentration_reduced": True, "wash_sale_penalty": 25000},
                risks=["$25K wash sale disallowed loss"]
            ),
            Scenario(
                scenario_id="scenario_b",
                title="Wait 16 Days",
                description="Wait for wash sale window to clear before selling",
                action_steps=[
                    ActionStep(step_number=1, action=TradeAction.HOLD, ticker="NVDA", quantity=0, timing="wait_16_days", rationale="Clear wash sale window"),
                    ActionStep(step_number=2, action=TradeAction.SELL, ticker="NVDA", quantity=15000, timing="after_window", rationale="Then reduce concentration")
                ],
                expected_outcomes={"concentration_reduced": True, "wash_sale_penalty": 0},
                risks=["Market risk during wait period"]
            ),
            Scenario(
                scenario_id="scenario_c",
                title="AMD Substitute Strategy",
                description="Sell NVDA and buy AMD to maintain sector exposure while avoiding wash sale",
                action_steps=[
                    ActionStep(step_number=1, action=TradeAction.SELL, ticker="NVDA", quantity=15000, timing="immediate", rationale="Reduce concentration"),
                    ActionStep(step_number=2, action=TradeAction.BUY, ticker="AMD", quantity=20000, timing="same_day", rationale="Maintain tech exposure with correlated substitute")
                ],
                expected_outcomes={"concentration_reduced": True, "sector_exposure_maintained": True, "wash_sale_penalty": 0},
                risks=["AMD tracking error vs NVDA"]
            ),
        ]

        # Score scenarios
        weights = UTILITY_WEIGHTS_BY_PROFILE[client_profile.risk_tolerance]
        scores = self.utility_fn.rank_scenarios(scenarios, None, weights)

        # Attach scores to scenarios
        for scenario in scenarios:
            for score in scores:
                if score.scenario_id == scenario.scenario_id:
                    scenario.utility_score = score

        # Log to Merkle chain
        merkle_hash = self.merkle_chain.add_block({
            "event_type": "recommendation_generated",
            "portfolio_id": portfolio_id,
            "scenarios": [s.scenario_id for s in scenarios],
            "recommended": scores[0].scenario_id
        })

        return CoordinatorOutput(
            portfolio_id=portfolio_id,
            trigger_event=event.event_id,
            analysis_timestamp=datetime.now(timezone.utc),
            drift_findings=drift_result,
            tax_findings=tax_result,
            conflicts_detected=conflicts,
            scenarios=scenarios,
            recommended_scenario_id=scores[0].scenario_id,
            merkle_hash=merkle_hash
        )

    async def handle_ui_action(self, action: UIAction) -> dict:
        self.merkle_chain.add_block({
            "event_type": "human_decision",
            "action": action.action_type.value,
            "scenario_id": action.scenario_id,
            "session_id": action.session_id
        })
        return {"status": "approved", "scenario_id": action.scenario_id}
