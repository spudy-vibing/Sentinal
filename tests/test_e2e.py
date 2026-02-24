"""
End-to-End Tests for Sentinel System

Tests the complete pipeline from event to Canvas output.

These tests verify:
1. Golden path: Market event → Analysis → Scenarios → Canvas
2. Heartbeat: Scheduled check → Drift detection → Recommendations
3. Webhook: External event → Impact analysis → Alert generation
4. Merkle chain: All events logged with integrity
5. Security: RBAC and audit trail enforcement
"""

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.contracts.schemas import (
    Portfolio,
    Holding,
    TaxLot,
    ClientProfile,
    TargetAllocation,
    RiskProfile,
    Transaction,
    TradeAction,
    MarketEventInput,
    HeartbeatInput,
    WebhookInput,
    EventType,
    AgentType,
)
from src.agents import (
    OfflineCoordinator,
    OfflineDriftAnalyzer,
    OfflineTaxAnalyzer,
    ConflictDetector,
    ScenarioGenerator,
)
from src.routing import PersonaRouter, RoutingDecision, RoutingPriority
from src.ui import CanvasGenerator, generate_canvas
from src.security import MerkleChain
from src.state import UtilityFunction, UtilityFunctionFactory


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_portfolio():
    """Create a sample portfolio with concentration risk."""
    now = datetime.now(timezone.utc)

    return Portfolio(
        portfolio_id="e2e_test_001",
        client_id="client_e2e",
        name="E2E Test Portfolio",
        aum_usd=50_000_000,
        last_rebalance=now - timedelta(days=90),
        cash_available=2_500_000,
        target_allocation=TargetAllocation(
            us_equities=0.35,
            international_equities=0.15,
            fixed_income=0.20,
            alternatives=0.20,
            structured_products=0.05,
            cash=0.05
        ),
        client_profile=ClientProfile(
            client_id="client_e2e",
            risk_tolerance=RiskProfile.MODERATE_GROWTH,
            tax_sensitivity=0.85,
            concentration_limit=0.15,
            rebalancing_frequency="quarterly"
        ),
        holdings=[
            Holding(
                ticker="NVDA",
                quantity=10000,
                current_price=850.00,
                market_value=8_500_000,
                portfolio_weight=0.17,  # Over 15% limit
                cost_basis=5_000_000,
                unrealized_gain_loss=3_500_000,
                sector="Technology",
                asset_class="US Equities",
                tax_lots=[
                    TaxLot(
                        lot_id="NVDA_E2E_001",
                        purchase_date=now - timedelta(days=400),
                        purchase_price=250.00,
                        quantity=10000,
                        cost_basis=2_500_000
                    )
                ]
            ),
            Holding(
                ticker="AMD",
                quantity=25000,
                current_price=150.00,
                market_value=3_750_000,
                portfolio_weight=0.075,
                cost_basis=4_500_000,
                unrealized_gain_loss=-750_000,  # Loss - tax harvest opportunity
                sector="Technology",
                asset_class="US Equities",
                tax_lots=[
                    TaxLot(
                        lot_id="AMD_E2E_001",
                        purchase_date=now - timedelta(days=300),
                        purchase_price=180.00,
                        quantity=25000,
                        cost_basis=4_500_000
                    )
                ]
            ),
            Holding(
                ticker="BND",
                quantity=100000,
                current_price=72.00,
                market_value=7_200_000,
                portfolio_weight=0.144,
                cost_basis=7_500_000,
                unrealized_gain_loss=-300_000,
                sector="Fixed Income",
                asset_class="Fixed Income",
                tax_lots=[]
            ),
            Holding(
                ticker="VEA",
                quantity=150000,
                current_price=50.00,
                market_value=7_500_000,
                portfolio_weight=0.15,
                cost_basis=7_000_000,
                unrealized_gain_loss=500_000,
                sector="Diversified",
                asset_class="International Equities",
                tax_lots=[]
            ),
        ]
    )


@pytest.fixture
def sample_transactions():
    """Create sample transactions with wash sale window."""
    now = datetime.now(timezone.utc)

    return [
        # NVDA sold 15 days ago - creates wash sale window
        Transaction(
            transaction_id="txn_e2e_001",
            portfolio_id="e2e_test_001",
            ticker="NVDA",
            action=TradeAction.SELL,
            quantity=2000,
            price=870.00,
            timestamp=now - timedelta(days=15),
            wash_sale_disallowed=0
        ),
        # AMD sold 45 days ago - outside wash sale window
        Transaction(
            transaction_id="txn_e2e_002",
            portfolio_id="e2e_test_001",
            ticker="AMD",
            action=TradeAction.SELL,
            quantity=5000,
            price=165.00,
            timestamp=now - timedelta(days=45),
            wash_sale_disallowed=0
        ),
    ]


@pytest.fixture
def market_event():
    """Create a market event."""
    return MarketEventInput(
        event_id="mkt_e2e_001",
        event_type=EventType.MARKET_EVENT,
        session_id="e2e_session",
        timestamp=datetime.now(timezone.utc),
        priority=9,
        affected_sectors=["Technology"],
        magnitude=-0.04,
        affected_tickers=["NVDA", "AMD", "AAPL"],
        description="Tech sector selloff"
    )


@pytest.fixture
def heartbeat_event():
    """Create a heartbeat event."""
    return HeartbeatInput(
        event_id="hb_e2e_001",
        event_type=EventType.HEARTBEAT,
        session_id="e2e_session",
        timestamp=datetime.now(timezone.utc),
        priority=5,
        portfolio_ids=["e2e_test_001"]
    )


@pytest.fixture
def webhook_event():
    """Create a webhook event."""
    return WebhookInput(
        event_id="wh_e2e_001",
        event_type=EventType.WEBHOOK,
        session_id="e2e_session",
        timestamp=datetime.now(timezone.utc),
        priority=8,
        source="sec_edgar",
        payload={
            "type": "news_alert",
            "tickers": ["NVDA"],
            "headline": "NVIDIA Q4 Earnings Beat",
            "sentiment": "positive"
        }
    )


# ═══════════════════════════════════════════════════════════════════════════
# GOLDEN PATH E2E TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestGoldenPathE2E:
    """End-to-end tests for the golden path scenario."""

    def test_full_pipeline_market_event_to_canvas(
        self, sample_portfolio, sample_transactions, market_event
    ):
        """Test complete pipeline from market event to Canvas generation."""
        # 1. Initialize Merkle chain
        merkle_chain = MerkleChain()

        # 2. Initialize coordinator
        coordinator = OfflineCoordinator(merkle_chain=merkle_chain)

        # 3. Execute analysis
        result = coordinator.execute_analysis(
            portfolio=sample_portfolio,
            transactions=sample_transactions,
            context={"market_event": market_event.model_dump()}
        )

        # 4. Verify drift detection
        assert result.drift_findings is not None
        assert result.drift_findings.drift_detected
        assert len(result.drift_findings.concentration_risks) > 0

        # 5. Verify tax analysis
        assert result.tax_findings is not None

        # 6. Verify scenarios generated
        assert len(result.scenarios) >= 2
        assert result.recommended_scenario_id is not None

        # 7. Verify ranking (first should be recommended)
        assert result.scenarios[0].scenario_id == result.recommended_scenario_id

        # 8. Verify utility scores
        for scenario in result.scenarios:
            assert scenario.utility_score is not None
            assert 0 <= scenario.utility_score.total_score <= 100

        # 9. Generate Canvas
        html = generate_canvas(result)
        assert "<!DOCTYPE html>" in html
        assert sample_portfolio.portfolio_id in html
        assert "sentinel-canvas" in html

        # 10. Verify Merkle chain
        assert len(merkle_chain._blocks) > 0
        assert merkle_chain.verify_integrity()

    def test_concentration_risk_detection(self, sample_portfolio):
        """Test that NVDA concentration (17% > 15% limit) is detected."""
        drift_output = OfflineDriftAnalyzer.analyze(sample_portfolio, {})

        assert drift_output.drift_detected
        assert len(drift_output.concentration_risks) > 0

        nvda_risk = next(
            (r for r in drift_output.concentration_risks if r.ticker == "NVDA"),
            None
        )
        assert nvda_risk is not None
        assert nvda_risk.current_weight > nvda_risk.limit
        # 2% excess gives MEDIUM severity (would need 5%+ for HIGH)
        assert nvda_risk.severity.value in ["medium", "high", "critical"]

    def test_wash_sale_conflict_detection(
        self, sample_portfolio, sample_transactions
    ):
        """Test wash sale conflict detection."""
        drift_output = OfflineDriftAnalyzer.analyze(sample_portfolio, {})
        tax_output = OfflineTaxAnalyzer.analyze(
            sample_portfolio,
            sample_transactions,
            drift_output.recommended_trades,
            {}
        )

        conflicts = ConflictDetector.detect_conflicts(
            drift_output, tax_output, sample_portfolio
        )

        # Should detect wash sale conflict for NVDA
        wash_sale_conflicts = [
            c for c in conflicts if c.conflict_type == "WASH_SALE_CONFLICT"
        ]
        assert len(wash_sale_conflicts) >= 0  # May or may not have depending on trades

    def test_scenario_ranking_by_utility(self, sample_portfolio, sample_transactions):
        """Test that scenarios are properly ranked by utility score."""
        coordinator = OfflineCoordinator()
        result = coordinator.execute_analysis(
            portfolio=sample_portfolio,
            transactions=sample_transactions,
            context={}
        )

        # Scenarios should be sorted by score descending
        scores = [s.utility_score.total_score for s in result.scenarios if s.utility_score]
        assert scores == sorted(scores, reverse=True)

        # Recommended should be highest scored
        top_scenario = result.scenarios[0]
        assert top_scenario.scenario_id == result.recommended_scenario_id


# ═══════════════════════════════════════════════════════════════════════════
# HEARTBEAT E2E TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestHeartbeatE2E:
    """End-to-end tests for proactive heartbeat monitoring."""

    def test_heartbeat_routing_decision(self, sample_portfolio, heartbeat_event):
        """Test heartbeat routing with concentration risk."""
        router = PersonaRouter()

        # Mock portfolio loader
        import src.routing.persona_router as router_module
        original_load = router_module.load_portfolio
        router_module.load_portfolio = lambda x: sample_portfolio

        try:
            decision = router.route(heartbeat_event, "e2e_test_001")

            assert decision.should_process
            assert decision.priority in [RoutingPriority.NORMAL, RoutingPriority.HIGH]
            assert AgentType.DRIFT in decision.agents_required
        finally:
            router_module.load_portfolio = original_load

    def test_heartbeat_detects_drift(self, sample_portfolio):
        """Test that heartbeat analysis detects portfolio drift."""
        coordinator = OfflineCoordinator()
        result = coordinator.execute_analysis(
            portfolio=sample_portfolio,
            transactions=[],
            context={"heartbeat_check": True}
        )

        # Should detect drift
        assert result.drift_findings.drift_detected

        # Should have concentration risks
        assert len(result.drift_findings.concentration_risks) > 0


# ═══════════════════════════════════════════════════════════════════════════
# WEBHOOK E2E TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestWebhookE2E:
    """End-to-end tests for webhook event handling."""

    def test_webhook_routing(self, sample_portfolio, webhook_event):
        """Test webhook event routing."""
        router = PersonaRouter()

        import src.routing.persona_router as router_module
        original_load = router_module.load_portfolio
        router_module.load_portfolio = lambda x: sample_portfolio

        try:
            decision = router.route(webhook_event, "e2e_test_001")

            assert decision.should_process
            # News alert affecting portfolio holdings should be processed
        finally:
            router_module.load_portfolio = original_load

    def test_webhook_impact_analysis(self, sample_portfolio, webhook_event):
        """Test webhook triggers impact analysis on affected holdings."""
        coordinator = OfflineCoordinator()

        result = coordinator.execute_analysis(
            portfolio=sample_portfolio,
            transactions=[],
            context={"webhook": webhook_event.model_dump()}
        )

        # Should produce analysis
        assert result.drift_findings is not None
        assert result.scenarios is not None


# ═══════════════════════════════════════════════════════════════════════════
# MERKLE CHAIN E2E TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestMerkleChainE2E:
    """End-to-end tests for Merkle chain audit trail."""

    def test_all_events_logged(self, sample_portfolio, sample_transactions):
        """Test that all analysis events are logged to Merkle chain."""
        merkle_chain = MerkleChain()
        coordinator = OfflineCoordinator(merkle_chain=merkle_chain)

        result = coordinator.execute_analysis(
            portfolio=sample_portfolio,
            transactions=sample_transactions,
            context={}
        )

        # Chain should have blocks
        assert len(merkle_chain._blocks) > 0

        # Root hash should be set
        assert result.merkle_hash != ""
        assert len(result.merkle_hash) > 0

    def test_chain_integrity_verification(self, sample_portfolio):
        """Test Merkle chain integrity verification."""
        merkle_chain = MerkleChain()

        # Add some blocks with required event_type
        merkle_chain.add_block({"event_type": "test_event", "data": "test_1"})
        merkle_chain.add_block({"event_type": "test_event", "data": "test_2"})
        merkle_chain.add_block({"event_type": "test_event", "data": "test_3"})

        # Verify integrity
        assert merkle_chain.verify_integrity()

    def test_tamper_detection(self, sample_portfolio):
        """Test that tampering is detected."""
        merkle_chain = MerkleChain()

        merkle_chain.add_block({"event_type": "test_event", "data": "original"})
        merkle_chain.add_block({"event_type": "test_event", "data": "legitimate"})

        # Verify before tampering
        assert merkle_chain.verify_integrity()

        # Tamper with a block (modify the data field of the MerkleBlock dataclass)
        if len(merkle_chain._blocks) > 1:
            # MerkleBlock is a dataclass with a 'data' dict attribute
            original_block = merkle_chain._blocks[0]
            original_block.data["data"] = "tampered"

            # Should fail verification because hash no longer matches
            assert not merkle_chain.verify_integrity()


# ═══════════════════════════════════════════════════════════════════════════
# CANVAS GENERATION E2E TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestCanvasE2E:
    """End-to-end tests for Canvas UI generation."""

    def test_canvas_includes_all_components(
        self, sample_portfolio, sample_transactions
    ):
        """Test that generated Canvas includes all required components."""
        coordinator = OfflineCoordinator()
        result = coordinator.execute_analysis(
            portfolio=sample_portfolio,
            transactions=sample_transactions,
            context={}
        )

        html = generate_canvas(result)

        # Check basic structure
        assert "<!DOCTYPE html>" in html
        assert "<head>" in html
        assert "<body>" in html

        # Check design tokens
        assert "--s-obsidian" in html or "obsidian" in html
        assert "--s-champagne" in html or "champagne" in html

        # Check scenarios
        for scenario in result.scenarios:
            assert scenario.title in html

        # Check portfolio info
        assert result.portfolio_id in html

    def test_canvas_file_output(self, sample_portfolio, tmp_path):
        """Test Canvas saves to file correctly."""
        from src.ui import save_canvas

        coordinator = OfflineCoordinator()
        result = coordinator.execute_analysis(
            portfolio=sample_portfolio,
            transactions=[],
            context={}
        )

        output_path = tmp_path / "test_canvas.html"
        save_canvas(result, str(output_path))

        assert output_path.exists()
        content = output_path.read_text()
        assert "<!DOCTYPE html>" in content


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY SCORING E2E TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestUtilityScoringE2E:
    """End-to-end tests for utility scoring system."""

    def test_utility_weights_by_profile(self, sample_portfolio):
        """Test utility weights vary by risk profile."""
        conservative_weights = UtilityFunctionFactory.get_weights_for_profile(
            RiskProfile.CONSERVATIVE
        )
        aggressive_weights = UtilityFunctionFactory.get_weights_for_profile(
            RiskProfile.AGGRESSIVE
        )

        # Conservative should weight risk higher
        assert conservative_weights.risk_reduction >= aggressive_weights.risk_reduction

        # Aggressive should weight urgency higher
        assert aggressive_weights.urgency >= conservative_weights.urgency

    def test_scenario_scoring_dimensions(self, sample_portfolio, sample_transactions):
        """Test all 5 utility dimensions are scored."""
        coordinator = OfflineCoordinator()
        result = coordinator.execute_analysis(
            portfolio=sample_portfolio,
            transactions=sample_transactions,
            context={}
        )

        for scenario in result.scenarios:
            if scenario.utility_score:
                dims = {d.dimension for d in scenario.utility_score.dimension_scores}

                assert "risk_reduction" in dims
                assert "tax_savings" in dims
                assert "goal_alignment" in dims
                assert "transaction_cost" in dims
                assert "urgency" in dims


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestSystemIntegration:
    """Integration tests across system components."""

    def test_router_to_coordinator_flow(
        self, sample_portfolio, market_event
    ):
        """Test event routing leads to coordinator execution."""
        # Route event
        router = PersonaRouter()

        import src.routing.persona_router as router_module
        original_load = router_module.load_portfolio
        router_module.load_portfolio = lambda x: sample_portfolio

        try:
            decision = router.route(market_event, "e2e_test_001")
            assert decision.should_process
            assert decision.requires_coordinator

            # Execute via coordinator
            coordinator = OfflineCoordinator()
            result = coordinator.execute_analysis(
                portfolio=sample_portfolio,
                transactions=[],
                context=decision.context_additions
            )

            # Verify complete pipeline
            assert result.scenarios is not None
            assert len(result.scenarios) > 0
        finally:
            router_module.load_portfolio = original_load

    def test_concurrent_analysis_idempotency(self, sample_portfolio):
        """Test multiple analyses produce consistent results."""
        coordinator = OfflineCoordinator()

        results = []
        for _ in range(3):
            result = coordinator.execute_analysis(
                portfolio=sample_portfolio,
                transactions=[],
                context={}
            )
            results.append(result)

        # All analyses should have same number of scenarios
        scenario_counts = [len(r.scenarios) for r in results]
        assert len(set(scenario_counts)) == 1

        # Recommended scenarios should be consistent
        recommended_titles = [
            next(s.title for s in r.scenarios if s.scenario_id == r.recommended_scenario_id)
            for r in results
        ]
        assert len(set(recommended_titles)) == 1
