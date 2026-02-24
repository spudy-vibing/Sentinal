"""
Tests for Phase 3: Orchestration

Tests cover:
- Coordinator (offline mode)
- Conflict detection
- Scenario generation
- Utility scoring integration
- Persona router
- Canvas generation
- UI components
"""

import pytest
from datetime import datetime, timezone, timedelta
import json

from src.contracts.schemas import (
    Portfolio,
    Holding,
    TaxLot,
    ClientProfile,
    TargetAllocation,
    RiskProfile,
    Transaction,
    TradeAction,
    RecommendedTrade,
    InputEvent,
    EventType,
    MarketEventInput,
    HeartbeatInput,
    WebhookInput,
    DriftAgentOutput,
    TaxAgentOutput,
    ConcentrationRisk,
    DriftMetric,
    DriftDirection,
    WashSaleViolation,
    TaxOpportunity,
    TaxOpportunityType,
    Severity,
)
from src.agents import (
    OfflineCoordinator,
    OfflineDriftAnalyzer,
    OfflineTaxAnalyzer,
    ConflictDetector,
    ScenarioGenerator,
)
from src.routing import (
    PersonaRouter,
    RoutingDecision,
    RoutingPriority,
    route_event,
)
from src.ui import (
    CanvasGenerator,
    generate_canvas,
    components,
    Badge,
    Button,
    ScoreBar,
    MetricCard,
    TradeRow,
    AlertBanner,
    BadgeVariant,
    ButtonVariant,
)
from src.security import MerkleChain


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_portfolio():
    """Create a sample portfolio with concentration risk."""
    now = datetime.now(timezone.utc)

    return Portfolio(
        portfolio_id="test_001",
        client_id="client_001",
        name="Test Growth Portfolio",
        aum_usd=50_000_000,
        client_profile=ClientProfile(
            client_id="client_001",
            risk_tolerance=RiskProfile.MODERATE_GROWTH,
            tax_sensitivity=0.8,
            concentration_limit=0.15,
            rebalancing_frequency="quarterly"
        ),
        target_allocation=TargetAllocation(
            us_equities=0.60,
            international_equities=0.15,
            fixed_income=0.15,
            alternatives=0.05,
            structured_products=0.03,
            cash=0.02
        ),
        holdings=[
            Holding(
                ticker="NVDA",
                name="NVIDIA Corporation",
                quantity=15000,
                current_price=900.0,
                market_value=13_500_000,
                cost_basis=8_000_000,
                unrealized_gain_loss=5_500_000,
                portfolio_weight=0.27,
                asset_class="US Equities",
                sector="Technology",
                tax_lots=[
                    TaxLot(
                        lot_id="lot_1",
                        purchase_date=now - timedelta(days=400),
                        purchase_price=400.0,
                        quantity=10000,
                        cost_basis=4_000_000
                    ),
                    TaxLot(
                        lot_id="lot_2",
                        purchase_date=now - timedelta(days=180),
                        purchase_price=600.0,
                        quantity=5000,
                        cost_basis=3_000_000
                    )
                ]
            ),
            Holding(
                ticker="AAPL",
                name="Apple Inc.",
                quantity=20000,
                current_price=180.0,
                market_value=3_600_000,
                cost_basis=4_000_000,
                unrealized_gain_loss=-400_000,
                portfolio_weight=0.072,
                asset_class="US Equities",
                sector="Technology",
                tax_lots=[]
            ),
            Holding(
                ticker="BND",
                name="Vanguard Total Bond Market ETF",
                quantity=100000,
                current_price=74.0,
                market_value=7_400_000,
                cost_basis=8_000_000,
                unrealized_gain_loss=-600_000,
                portfolio_weight=0.148,
                asset_class="Fixed Income",
                sector="Bonds",
                tax_lots=[]
            )
        ],
        cash_available=500_000,
        last_rebalance=now - timedelta(days=45)
    )


@pytest.fixture
def sample_transactions():
    """Create sample recent transactions."""
    now = datetime.now(timezone.utc)

    return [
        Transaction(
            transaction_id="tx_001",
            portfolio_id="test_001",
            ticker="AAPL",
            action=TradeAction.SELL,
            quantity=5000,
            price=175.0,
            timestamp=now - timedelta(days=20)
        ),
        Transaction(
            transaction_id="tx_002",
            portfolio_id="test_001",
            ticker="MSFT",
            action=TradeAction.BUY,
            quantity=2000,
            price=400.0,
            timestamp=now - timedelta(days=10)
        )
    ]


@pytest.fixture
def sample_event():
    """Create a sample market event with high magnitude."""
    return MarketEventInput(
        event_id="evt_001",
        event_type=EventType.MARKET_EVENT,
        session_id="test_session",
        timestamp=datetime.now(timezone.utc),
        priority=8,
        affected_sectors=["Technology"],
        magnitude=-0.12,  # 12% drop - critical
        affected_tickers=["NVDA", "AAPL"],
        description="Major tech sector selloff"
    )


@pytest.fixture
def sample_drift_output():
    """Create sample drift agent output."""
    return DriftAgentOutput(
        portfolio_id="test_001",
        analysis_timestamp=datetime.now(timezone.utc),
        drift_detected=True,
        concentration_risks=[
            ConcentrationRisk(
                ticker="NVDA",
                current_weight=0.27,
                limit=0.15,
                excess=0.12,
                severity=Severity.CRITICAL
            )
        ],
        drift_metrics=[
            DriftMetric(
                asset_class="US Equities",
                target_weight=0.60,
                current_weight=0.72,
                drift_pct=0.12,
                drift_direction=DriftDirection.OVER
            )
        ],
        recommended_trades=[
            RecommendedTrade(
                ticker="NVDA",
                action=TradeAction.SELL,
                quantity=3000,
                rationale="Reduce concentration from 27% to 22%",
                urgency=8
            ),
            RecommendedTrade(
                ticker="AAPL",
                action=TradeAction.BUY,
                quantity=2000,
                rationale="Maintain tech exposure",
                urgency=5
            )
        ],
        urgency_score=8,
        reasoning="NVDA concentration exceeds limit by 12%"
    )


@pytest.fixture
def sample_tax_output():
    """Create sample tax agent output with wash sale."""
    now = datetime.now(timezone.utc)

    return TaxAgentOutput(
        portfolio_id="test_001",
        analysis_timestamp=now,
        wash_sale_violations=[
            WashSaleViolation(
                ticker="AAPL",
                prior_sale_date=now - timedelta(days=20),
                days_since_sale=20,
                disallowed_loss=100000,
                recommendation="Wait 11 more days before buying AAPL"
            )
        ],
        tax_opportunities=[
            TaxOpportunity(
                ticker="BND",
                opportunity_type=TaxOpportunityType.HARVEST_LOSS,
                estimated_benefit=150000,
                action_required="Harvest $600k loss to offset gains"
            )
        ],
        proposed_trades_analysis=[
            {
                "ticker": "NVDA",
                "action": "sell",
                "quantity": 3000,
                "tax_impact": 262000,
                "holding_period": "mixed"
            }
        ],
        total_tax_impact=262000,
        recommendations=["Use HIFO lot selection"],
        reasoning="NVDA sale would trigger significant tax. AAPL buy would cause wash sale."
    )


# ═══════════════════════════════════════════════════════════════════════════
# CONFLICT DETECTOR TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestConflictDetector:
    """Tests for ConflictDetector."""

    def test_detect_wash_sale_conflict(
        self,
        sample_portfolio,
        sample_drift_output,
        sample_tax_output
    ):
        """Test detection of wash sale conflicts."""
        conflicts = ConflictDetector.detect_conflicts(
            sample_drift_output,
            sample_tax_output,
            sample_portfolio
        )

        # Should detect AAPL wash sale conflict
        wash_conflicts = [c for c in conflicts if c.conflict_type == "WASH_SALE_CONFLICT"]
        assert len(wash_conflicts) == 1
        assert "AAPL" in wash_conflicts[0].description

    def test_detect_tax_inefficient_conflict(
        self,
        sample_portfolio,
        sample_drift_output,
        sample_tax_output
    ):
        """Test detection of tax-inefficient trades."""
        # Modify drift output to have lower urgency NVDA sell
        sample_drift_output.recommended_trades[0].urgency = 5

        conflicts = ConflictDetector.detect_conflicts(
            sample_drift_output,
            sample_tax_output,
            sample_portfolio
        )

        # Should detect tax-inefficient conflict for NVDA
        tax_conflicts = [c for c in conflicts if c.conflict_type == "TAX_INEFFICIENT"]
        assert len(tax_conflicts) >= 1

    def test_no_conflicts_when_clean(self, sample_portfolio):
        """Test no conflicts when outputs are clean."""
        drift = DriftAgentOutput(
            portfolio_id="test_001",
            analysis_timestamp=datetime.now(timezone.utc),
            drift_detected=False,
            concentration_risks=[],
            drift_metrics=[],
            recommended_trades=[],
            urgency_score=3,
            reasoning="No issues"
        )

        tax = TaxAgentOutput(
            portfolio_id="test_001",
            analysis_timestamp=datetime.now(timezone.utc),
            wash_sale_violations=[],
            tax_opportunities=[],
            proposed_trades_analysis=[],
            total_tax_impact=0,
            recommendations=[],
            reasoning="No issues"
        )

        conflicts = ConflictDetector.detect_conflicts(drift, tax, sample_portfolio)
        assert len(conflicts) == 0


# ═══════════════════════════════════════════════════════════════════════════
# SCENARIO GENERATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestScenarioGenerator:
    """Tests for ScenarioGenerator."""

    def test_generate_scenarios(
        self,
        sample_portfolio,
        sample_drift_output,
        sample_tax_output
    ):
        """Test scenario generation."""
        conflicts = ConflictDetector.detect_conflicts(
            sample_drift_output,
            sample_tax_output,
            sample_portfolio
        )

        scenarios = ScenarioGenerator.generate_scenarios(
            sample_drift_output,
            sample_tax_output,
            conflicts,
            sample_portfolio
        )

        # Should generate 2-4 scenarios
        assert 2 <= len(scenarios) <= 4

        # Each scenario should have required fields
        for scenario in scenarios:
            assert scenario.scenario_id
            assert scenario.title
            assert scenario.description
            assert scenario.expected_outcomes

    def test_optimal_scenario_avoids_wash_sales(
        self,
        sample_portfolio,
        sample_drift_output,
        sample_tax_output
    ):
        """Test that optimal scenario avoids wash sales."""
        conflicts = ConflictDetector.detect_conflicts(
            sample_drift_output,
            sample_tax_output,
            sample_portfolio
        )

        scenarios = ScenarioGenerator.generate_scenarios(
            sample_drift_output,
            sample_tax_output,
            conflicts,
            sample_portfolio
        )

        # Find optimal scenario
        optimal = next(s for s in scenarios if "Optimal" in s.title)

        # Should not have AAPL BUY action (wash sale risk)
        aapl_buys = [
            step for step in optimal.action_steps
            if step.ticker == "AAPL" and step.action == TradeAction.BUY
        ]
        assert len(aapl_buys) == 0

    def test_tax_efficient_scenario_harvests_losses(
        self,
        sample_portfolio,
        sample_drift_output,
        sample_tax_output
    ):
        """Test that tax-efficient scenario includes loss harvesting."""
        conflicts = []

        scenarios = ScenarioGenerator.generate_scenarios(
            sample_drift_output,
            sample_tax_output,
            conflicts,
            sample_portfolio
        )

        # Find tax-efficient scenario
        tax_scenario = next(s for s in scenarios if "Tax" in s.title)

        # Expected outcomes should show tax savings
        assert tax_scenario.expected_outcomes.get("harvest_opportunities_captured", 0) > 0


# ═══════════════════════════════════════════════════════════════════════════
# OFFLINE COORDINATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestOfflineCoordinator:
    """Tests for OfflineCoordinator."""

    def test_execute_analysis(self, sample_portfolio, sample_transactions):
        """Test full analysis execution."""
        coordinator = OfflineCoordinator()

        result = coordinator.execute_analysis(
            sample_portfolio,
            sample_transactions,
            context={"market_event": {"magnitude": -0.15}}
        )

        assert result.portfolio_id == sample_portfolio.portfolio_id
        assert result.drift_findings is not None
        assert result.tax_findings is not None
        assert len(result.scenarios) >= 2
        assert result.recommended_scenario_id

    def test_scenarios_are_scored(self, sample_portfolio):
        """Test that scenarios have utility scores."""
        coordinator = OfflineCoordinator()

        result = coordinator.execute_analysis(sample_portfolio)

        # All scenarios should have utility scores
        for scenario in result.scenarios:
            assert scenario.utility_score is not None
            assert 0 <= scenario.utility_score.total_score <= 100

    def test_scenarios_are_ranked(self, sample_portfolio):
        """Test that scenarios are sorted by score."""
        coordinator = OfflineCoordinator()

        result = coordinator.execute_analysis(sample_portfolio)

        scores = [s.utility_score.total_score for s in result.scenarios]
        assert scores == sorted(scores, reverse=True)

    def test_recommended_is_top_scored(self, sample_portfolio):
        """Test that recommended scenario is top scored."""
        coordinator = OfflineCoordinator()

        result = coordinator.execute_analysis(sample_portfolio)

        recommended = result.recommended_scenario
        assert recommended is not None
        assert recommended.utility_score.rank == 1

    def test_merkle_logging(self, sample_portfolio):
        """Test that analysis is logged to Merkle chain."""
        chain = MerkleChain()
        initial_length = len(chain)

        coordinator = OfflineCoordinator(merkle_chain=chain)
        coordinator.execute_analysis(sample_portfolio)

        # Should have added a block
        assert len(chain) > initial_length


# ═══════════════════════════════════════════════════════════════════════════
# PERSONA ROUTER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestPersonaRouter:
    """Tests for PersonaRouter."""

    def test_route_market_event_high_magnitude(self, sample_portfolio, sample_event):
        """Test routing of high-magnitude market event."""
        router = PersonaRouter()

        # Mock load_portfolio
        import src.routing.persona_router as router_module
        original_load = router_module.load_portfolio
        router_module.load_portfolio = lambda x: sample_portfolio

        try:
            decision = router.route(sample_event, "test_001")

            assert decision.should_process
            assert decision.priority == RoutingPriority.CRITICAL
            assert decision.requires_coordinator
        finally:
            router_module.load_portfolio = original_load

    def test_route_heartbeat_with_concentration(self, sample_portfolio):
        """Test routing of heartbeat when concentration risk exists."""
        router = PersonaRouter()

        import src.routing.persona_router as router_module
        original_load = router_module.load_portfolio
        router_module.load_portfolio = lambda x: sample_portfolio

        try:
            event = HeartbeatInput(
                event_id="hb_001",
                event_type=EventType.HEARTBEAT,
                session_id="test_session",
                timestamp=datetime.now(timezone.utc),
                portfolio_ids=["test_001"]
            )

            decision = router.route(event, "test_001")

            assert decision.should_process
            assert "concentration_alert" in decision.context_additions or \
                   "drift_detected" in decision.context_additions
        finally:
            router_module.load_portfolio = original_load

    def test_route_webhook_trade_execution(self, sample_portfolio):
        """Test routing of trade execution webhook."""
        router = PersonaRouter()

        import src.routing.persona_router as router_module
        original_load = router_module.load_portfolio
        router_module.load_portfolio = lambda x: sample_portfolio

        try:
            event = WebhookInput(
                event_id="wh_001",
                event_type=EventType.WEBHOOK,
                session_id="test_session",
                timestamp=datetime.now(timezone.utc),
                source="trading_system",
                payload={"type": "trade_execution", "trade": {"ticker": "NVDA"}}
            )

            decision = router.route(event, "test_001")

            assert decision.should_process
            assert decision.priority == RoutingPriority.HIGH
        finally:
            router_module.load_portfolio = original_load


# ═══════════════════════════════════════════════════════════════════════════
# CANVAS GENERATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestCanvasGenerator:
    """Tests for CanvasGenerator."""

    def test_generate_canvas(self, sample_portfolio):
        """Test canvas generation."""
        coordinator = OfflineCoordinator()
        result = coordinator.execute_analysis(sample_portfolio)

        html = generate_canvas(result)

        assert "<!DOCTYPE html>" in html
        assert sample_portfolio.portfolio_id in html
        assert "sentinel-canvas" in html

    def test_canvas_includes_scenarios(self, sample_portfolio):
        """Test that canvas includes all scenarios."""
        coordinator = OfflineCoordinator()
        result = coordinator.execute_analysis(sample_portfolio)

        html = generate_canvas(result)

        for scenario in result.scenarios:
            assert scenario.title in html

    def test_canvas_highlights_recommended(self, sample_portfolio):
        """Test that recommended scenario is highlighted."""
        coordinator = OfflineCoordinator()
        result = coordinator.execute_analysis(sample_portfolio)

        html = generate_canvas(result)

        # Recommended badge should appear
        assert "Recommended" in html
        assert "recommended" in html  # CSS class

    def test_canvas_shows_conflicts(self, sample_portfolio, sample_transactions):
        """Test that canvas shows conflicts when present."""
        coordinator = OfflineCoordinator()
        result = coordinator.execute_analysis(
            sample_portfolio,
            sample_transactions
        )

        html = generate_canvas(result)

        if result.conflicts_detected:
            assert "conflicts-panel" in html
            assert "Conflicts Detected" in html

    def test_canvas_includes_design_tokens(self, sample_portfolio):
        """Test that canvas includes design tokens."""
        coordinator = OfflineCoordinator()
        result = coordinator.execute_analysis(sample_portfolio)

        html = generate_canvas(result)

        assert "--s-obsidian-900" in html
        assert "--s-champagne-500" in html
        assert "Cormorant Garamond" in html


# ═══════════════════════════════════════════════════════════════════════════
# UI COMPONENTS TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestUIComponents:
    """Tests for UI components."""

    def test_badge_render(self):
        """Test badge component rendering."""
        badge = Badge(text="CRITICAL", variant=BadgeVariant.DANGER)
        html = badge.render()

        assert "CRITICAL" in html
        assert "sentinel-badge" in html
        assert "negative" in html.lower()

    def test_button_render(self):
        """Test button component rendering."""
        button = Button(
            text="Approve",
            variant=ButtonVariant.PRIMARY,
            onclick="approve()"
        )
        html = button.render()

        assert "Approve" in html
        assert "approve()" in html
        assert "sentinel-btn" in html

    def test_score_bar_render(self):
        """Test score bar component rendering."""
        bar = ScoreBar(value=75, label="Utility Score")

        html = bar.render()

        assert "75" in html
        assert "Utility Score" in html
        assert "width: 75%" in html

    def test_metric_card_render(self):
        """Test metric card component rendering."""
        metric = MetricCard(
            label="Total AUM",
            value="$50M",
            change=5.2
        )
        html = metric.render()

        assert "Total AUM" in html
        assert "$50M" in html
        assert "5.2%" in html

    def test_trade_row_render(self):
        """Test trade row component rendering."""
        trade = TradeRow(
            ticker="NVDA",
            action="SELL",
            quantity=3000,
            price=900.0
        )
        html = trade.render()

        assert "NVDA" in html
        assert "SELL" in html
        assert "3,000" in html
        assert "negative" in html.lower()

    def test_alert_banner_render(self):
        """Test alert banner component rendering."""
        alert = AlertBanner(
            message="Wash sale detected",
            variant="warning"
        )
        html = alert.render()

        assert "Wash sale detected" in html
        assert "warning" in html.lower()

    def test_component_factory(self):
        """Test component factory methods."""
        badge = components.badge("NEW", "accent")
        assert isinstance(badge, Badge)

        button = components.button("Click", "secondary")
        assert isinstance(button, Button)

        score = components.score_bar(80, "Score")
        assert isinstance(score, ScoreBar)


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestPhase3Integration:
    """Integration tests for Phase 3 components."""

    def test_full_pipeline(self, sample_portfolio, sample_transactions):
        """Test complete analysis pipeline."""
        # 1. Run coordinator
        coordinator = OfflineCoordinator()
        result = coordinator.execute_analysis(
            sample_portfolio,
            sample_transactions,
            context={"market_event": {"magnitude": -0.10}}
        )

        # 2. Generate canvas
        html = generate_canvas(result)

        # 3. Verify all components present
        assert result.drift_findings.drift_detected
        assert len(result.scenarios) >= 2
        assert result.recommended_scenario_id in html
        assert "Approve" in html

    def test_routing_to_coordinator(self, sample_portfolio, sample_event):
        """Test routing decision leads to coordinator."""
        router = PersonaRouter()

        import src.routing.persona_router as router_module
        original_load = router_module.load_portfolio
        router_module.load_portfolio = lambda x: sample_portfolio

        try:
            decision = router.route(sample_event, "test_001")

            # High-impact event should require coordinator
            assert decision.requires_coordinator

            # Context should include market event
            assert "market_event" in decision.context_additions
        finally:
            router_module.load_portfolio = original_load

    def test_conflict_resolution_in_scenarios(
        self,
        sample_portfolio,
        sample_transactions
    ):
        """Test that conflicts are addressed in scenarios."""
        coordinator = OfflineCoordinator()
        result = coordinator.execute_analysis(
            sample_portfolio,
            sample_transactions
        )

        # If there are conflicts, scenarios should address them
        if result.conflicts_detected:
            # Optimal scenario should avoid wash sales
            optimal = result.recommended_scenario
            for step in optimal.action_steps:
                wash_sale_tickers = [c.ticker for c in result.tax_findings.wash_sale_violations]
                if step.action == TradeAction.BUY:
                    assert step.ticker not in wash_sale_tickers
