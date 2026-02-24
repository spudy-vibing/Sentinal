"""
Tests for Sentinel AI Agents.

Tests cover:
- OfflineDriftAnalyzer (rule-based drift detection)
- OfflineTaxAnalyzer (rule-based tax analysis)
- Skill discovery and injection
- Agent factory
"""

import pytest
from datetime import datetime, timezone, timedelta

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
    Severity,
    DriftDirection,
    TaxOpportunityType,
)
from src.agents import (
    OfflineDriftAnalyzer,
    OfflineTaxAnalyzer,
    AgentFactory,
)
from src.skills import (
    SkillRegistry,
    SkillMetadata,
    SkillTrigger,
    get_skill_registry,
    inject_skills_into_prompt,
)


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
                portfolio_weight=0.27,  # Over 15% limit
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
                unrealized_gain_loss=-400_000,  # Loss position
                portfolio_weight=0.072,
                asset_class="US Equities",
                sector="Technology",
                tax_lots=[
                    TaxLot(
                        lot_id="lot_3",
                        purchase_date=now - timedelta(days=90),
                        purchase_price=200.0,
                        quantity=20000,
                        cost_basis=4_000_000
                    )
                ]
            ),
            Holding(
                ticker="MSFT",
                name="Microsoft Corporation",
                quantity=10000,
                current_price=410.0,
                market_value=4_100_000,
                cost_basis=3_000_000,
                unrealized_gain_loss=1_100_000,
                portfolio_weight=0.082,
                asset_class="US Equities",
                sector="Technology",
                tax_lots=[
                    TaxLot(
                        lot_id="lot_4",
                        purchase_date=now - timedelta(days=500),
                        purchase_price=300.0,
                        quantity=10000,
                        cost_basis=3_000_000
                    )
                ]
            ),
            Holding(
                ticker="VEA",
                name="Vanguard FTSE Developed Markets ETF",
                quantity=100000,
                current_price=48.0,
                market_value=4_800_000,
                cost_basis=4_500_000,
                unrealized_gain_loss=300_000,
                portfolio_weight=0.096,
                asset_class="International Equities",
                sector="Diversified",
                tax_lots=[]
            ),
            Holding(
                ticker="BND",
                name="Vanguard Total Bond Market ETF",
                quantity=100000,
                current_price=74.0,
                market_value=7_400_000,
                cost_basis=8_000_000,
                unrealized_gain_loss=-600_000,  # Loss position
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
            ticker="GOOGL",
            action=TradeAction.SELL,
            quantity=1000,
            price=140.0,
            timestamp=now - timedelta(days=35)  # Outside wash sale window
        ),
        Transaction(
            transaction_id="tx_003",
            portfolio_id="test_001",
            ticker="MSFT",
            action=TradeAction.BUY,
            quantity=2000,
            price=400.0,
            timestamp=now - timedelta(days=10)
        )
    ]


@pytest.fixture
def proposed_trades():
    """Create sample proposed trades from drift agent."""
    return [
        RecommendedTrade(
            ticker="NVDA",
            action=TradeAction.SELL,
            quantity=3000,
            rationale="Reduce concentration from 27% to 22%",
            urgency=8,
            estimated_tax_impact=0
        ),
        RecommendedTrade(
            ticker="AAPL",
            action=TradeAction.BUY,
            quantity=2000,
            rationale="Maintain tech exposure after NVDA reduction",
            urgency=5,
            estimated_tax_impact=0
        ),
        RecommendedTrade(
            ticker="VEA",
            action=TradeAction.BUY,
            quantity=20000,
            rationale="Increase international allocation",
            urgency=4,
            estimated_tax_impact=0
        )
    ]


# ═══════════════════════════════════════════════════════════════════════════
# OFFLINE DRIFT ANALYZER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestOfflineDriftAnalyzer:
    """Tests for OfflineDriftAnalyzer."""

    def test_detect_concentration_risk(self, sample_portfolio):
        """Test detection of concentration risk."""
        result = OfflineDriftAnalyzer.analyze(sample_portfolio)

        assert result.drift_detected
        assert len(result.concentration_risks) > 0

        # NVDA should be flagged
        nvda_risk = next(
            (r for r in result.concentration_risks if r.ticker == "NVDA"),
            None
        )
        assert nvda_risk is not None
        assert nvda_risk.current_weight == 0.27
        assert nvda_risk.limit == 0.15
        assert nvda_risk.excess == pytest.approx(0.12, abs=0.01)

    def test_concentration_severity_calculation(self, sample_portfolio):
        """Test severity is calculated correctly."""
        result = OfflineDriftAnalyzer.analyze(sample_portfolio)

        nvda_risk = next(
            r for r in result.concentration_risks if r.ticker == "NVDA"
        )
        # 12% over limit = CRITICAL (>10%)
        assert nvda_risk.severity == Severity.CRITICAL

    def test_drift_metrics_calculated(self, sample_portfolio):
        """Test drift metrics are calculated for all asset classes."""
        result = OfflineDriftAnalyzer.analyze(sample_portfolio)

        assert len(result.drift_metrics) > 0

        # Check we have metrics for major asset classes
        asset_classes = [m.asset_class for m in result.drift_metrics]
        assert any("Equit" in ac for ac in asset_classes)

    def test_recommended_trades_generated(self, sample_portfolio):
        """Test recommended trades are generated for concentration risks."""
        result = OfflineDriftAnalyzer.analyze(sample_portfolio)

        # Should recommend selling NVDA
        nvda_trade = next(
            (t for t in result.recommended_trades if t.ticker == "NVDA"),
            None
        )
        assert nvda_trade is not None
        assert nvda_trade.action == TradeAction.SELL
        assert nvda_trade.quantity > 0

    def test_urgency_score(self, sample_portfolio):
        """Test urgency score reflects severity."""
        result = OfflineDriftAnalyzer.analyze(sample_portfolio)

        # With CRITICAL concentration risk, urgency should be high (9)
        assert result.urgency_score >= 7

    def test_reasoning_included(self, sample_portfolio):
        """Test reasoning is included in output."""
        result = OfflineDriftAnalyzer.analyze(sample_portfolio)

        assert result.reasoning
        assert "NVDA" in result.reasoning or "concentration" in result.reasoning.lower()

    def test_portfolio_without_risks(self):
        """Test analysis of portfolio without concentration risks."""
        now = datetime.now(timezone.utc)

        safe_portfolio = Portfolio(
            portfolio_id="safe_001",
            client_id="client_safe",
            name="Safe Portfolio",
            aum_usd=10_000_000,
            client_profile=ClientProfile(
                client_id="client_safe",
                risk_tolerance=RiskProfile.MODERATE_GROWTH,
                tax_sensitivity=0.5,
                concentration_limit=0.20,
                rebalancing_frequency="quarterly"
            ),
            target_allocation=TargetAllocation(
                us_equities=0.60,
                international_equities=0.20,
                fixed_income=0.15,
                alternatives=0.05,
                structured_products=0.0,
                cash=0.0
            ),
            holdings=[
                Holding(
                    ticker="SPY",
                    name="S&P 500 ETF",
                    quantity=10000,
                    current_price=500.0,
                    market_value=5_000_000,
                    cost_basis=4_000_000,
                    unrealized_gain_loss=1_000_000,
                    portfolio_weight=0.10,
                    asset_class="US Equities",
                    sector="Diversified",
                    tax_lots=[]
                )
            ],
            cash_available=100_000,
            last_rebalance=now - timedelta(days=30)
        )

        result = OfflineDriftAnalyzer.analyze(safe_portfolio)

        assert len(result.concentration_risks) == 0


# ═══════════════════════════════════════════════════════════════════════════
# OFFLINE TAX ANALYZER TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestOfflineTaxAnalyzer:
    """Tests for OfflineTaxAnalyzer."""

    def test_detect_wash_sale_risk(
        self,
        sample_portfolio,
        sample_transactions,
        proposed_trades
    ):
        """Test detection of wash sale violations."""
        result = OfflineTaxAnalyzer.analyze(
            sample_portfolio,
            sample_transactions,
            proposed_trades
        )

        # AAPL was sold within 31 days, buying it would trigger wash sale
        aapl_violation = next(
            (v for v in result.wash_sale_violations if v.ticker == "AAPL"),
            None
        )
        assert aapl_violation is not None
        assert aapl_violation.days_since_sale < 31

    def test_wash_sale_days_until_clear(
        self,
        sample_portfolio,
        sample_transactions,
        proposed_trades
    ):
        """Test wash sale window calculation."""
        result = OfflineTaxAnalyzer.analyze(
            sample_portfolio,
            sample_transactions,
            proposed_trades
        )

        aapl_violation = next(
            v for v in result.wash_sale_violations if v.ticker == "AAPL"
        )
        # 20 days ago, so 11 days until clear
        assert aapl_violation.days_until_clear == pytest.approx(11, abs=1)

    def test_tax_loss_harvesting_opportunities(self, sample_portfolio):
        """Test identification of tax-loss harvesting opportunities."""
        result = OfflineTaxAnalyzer.analyze(
            sample_portfolio,
            context={"year_to_date_gains": 1_000_000}
        )

        # AAPL and BND have losses
        assert len(result.tax_opportunities) > 0

        tickers = [o.ticker for o in result.tax_opportunities]
        assert "AAPL" in tickers or "BND" in tickers

    def test_tax_opportunities_sorted_by_benefit(self, sample_portfolio):
        """Test opportunities are sorted by estimated benefit."""
        result = OfflineTaxAnalyzer.analyze(
            sample_portfolio,
            context={"year_to_date_gains": 1_000_000}
        )

        if len(result.tax_opportunities) >= 2:
            benefits = [o.estimated_benefit for o in result.tax_opportunities]
            assert benefits == sorted(benefits, reverse=True)

    def test_proposed_trade_tax_impact(
        self,
        sample_portfolio,
        proposed_trades
    ):
        """Test tax impact calculation for proposed trades."""
        result = OfflineTaxAnalyzer.analyze(
            sample_portfolio,
            proposed_trades=proposed_trades
        )

        assert len(result.proposed_trades_analysis) > 0

        # NVDA sell should have tax impact (it has gains)
        nvda_analysis = next(
            (a for a in result.proposed_trades_analysis if a["ticker"] == "NVDA"),
            None
        )
        assert nvda_analysis is not None
        assert nvda_analysis["tax_impact"] > 0

    def test_total_tax_impact_calculation(
        self,
        sample_portfolio,
        proposed_trades
    ):
        """Test total tax impact is calculated."""
        result = OfflineTaxAnalyzer.analyze(
            sample_portfolio,
            proposed_trades=proposed_trades
        )

        # Should have some tax impact from NVDA gains
        assert result.total_tax_impact > 0

    def test_recommendations_generated(
        self,
        sample_portfolio,
        sample_transactions,
        proposed_trades
    ):
        """Test recommendations are generated."""
        result = OfflineTaxAnalyzer.analyze(
            sample_portfolio,
            sample_transactions,
            proposed_trades
        )

        assert len(result.recommendations) > 0

    def test_wash_sale_recommendation_content(
        self,
        sample_portfolio,
        sample_transactions,
        proposed_trades
    ):
        """Test wash sale violation includes recommendation."""
        result = OfflineTaxAnalyzer.analyze(
            sample_portfolio,
            sample_transactions,
            proposed_trades
        )

        if result.wash_sale_violations:
            violation = result.wash_sale_violations[0]
            assert violation.recommendation
            assert "wait" in violation.recommendation.lower() or "substitute" in violation.recommendation.lower()


# ═══════════════════════════════════════════════════════════════════════════
# SKILL REGISTRY TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestSkillRegistry:
    """Tests for SkillRegistry."""

    def test_builtin_skills_loaded(self):
        """Test built-in skills are loaded."""
        registry = SkillRegistry()
        skills = registry.list_skills()

        assert len(skills) >= 6

        names = [s["name"] for s in skills]
        assert "concentration_risk" in names
        assert "wash_sale" in names
        assert "tax_loss_harvest" in names

    def test_discover_concentration_risk_skill(self, sample_portfolio):
        """Test concentration risk skill is discovered for high concentration."""
        registry = SkillRegistry()

        context = {
            "holdings": sample_portfolio.holdings,
            "concentration_limit": 0.15
        }

        skills = registry.discover_relevant_skills(context)

        assert "concentration_risk" in skills

    def test_discover_wash_sale_skill(self, sample_transactions):
        """Test wash sale skill is discovered when recent sales exist."""
        registry = SkillRegistry()

        context = {"recent_transactions": sample_transactions}

        skills = registry.discover_relevant_skills(context)

        assert "wash_sale" in skills

    def test_discover_tax_loss_harvest_skill(self, sample_portfolio):
        """Test tax loss harvest skill discovered for loss positions."""
        registry = SkillRegistry()

        context = {"holdings": sample_portfolio.holdings}

        skills = registry.discover_relevant_skills(context)

        assert "tax_loss_harvest" in skills

    def test_token_budget_respected(self, sample_portfolio, sample_transactions):
        """Test token budget limits skills loaded."""
        registry = SkillRegistry()

        context = {
            "holdings": sample_portfolio.holdings,
            "recent_transactions": sample_transactions,
            "concentration_limit": 0.15
        }

        # Very low budget
        skills_low = registry.discover_relevant_skills(context, token_budget=500)

        # High budget
        skills_high = registry.discover_relevant_skills(context, token_budget=10000)

        assert len(skills_low) <= len(skills_high)

    def test_load_skill_content(self):
        """Test loading skill content."""
        registry = SkillRegistry()

        content = registry.load_skill("concentration_risk")

        assert content
        assert "Concentration" in content
        assert "severity" in content.lower()

    def test_load_invalid_skill_raises(self):
        """Test loading non-existent skill raises KeyError."""
        registry = SkillRegistry()

        with pytest.raises(KeyError):
            registry.load_skill("nonexistent_skill")

    def test_get_skill_content_multiple(self):
        """Test getting content for multiple skills."""
        registry = SkillRegistry()

        content = registry.get_skill_content(["concentration_risk", "wash_sale"])

        assert "Concentration" in content
        assert "Wash Sale" in content

    def test_inject_skills_into_prompt(self, sample_portfolio):
        """Test skill injection into prompt."""
        base_prompt = "Analyze this portfolio."

        context = {
            "holdings": sample_portfolio.holdings,
            "concentration_limit": 0.15
        }

        enhanced = inject_skills_into_prompt(base_prompt, context)

        assert "Analyze this portfolio" in enhanced
        assert "RELEVANT SKILLS" in enhanced
        assert "Concentration" in enhanced

    def test_register_custom_skill(self):
        """Test registering a custom skill."""
        registry = SkillRegistry()

        custom = SkillMetadata(
            name="custom_skill",
            description="A custom skill",
            triggers=[SkillTrigger.MARKET_EVENT],
            token_cost=100,
            priority=1,
            content="# Custom Skill\n\nCustom content here."
        )

        registry.register_skill(custom)

        assert "custom_skill" in [s["name"] for s in registry.list_skills()]
        assert registry.load_skill("custom_skill") == custom.content

    def test_unregister_skill(self):
        """Test unregistering a skill."""
        registry = SkillRegistry()

        initial_count = len(registry.list_skills())
        registry.unregister_skill("rebalance")

        assert len(registry.list_skills()) == initial_count - 1
        assert "rebalance" not in [s["name"] for s in registry.list_skills()]

    def test_get_total_token_cost(self):
        """Test calculating total token cost."""
        registry = SkillRegistry()

        cost = registry.get_total_token_cost(["concentration_risk", "wash_sale"])

        # concentration_risk = 800, wash_sale = 700
        assert cost == 1500

    def test_global_registry(self):
        """Test global skill registry singleton."""
        registry1 = get_skill_registry()
        registry2 = get_skill_registry()

        assert registry1 is registry2


# ═══════════════════════════════════════════════════════════════════════════
# AGENT FACTORY TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestAgentFactory:
    """Tests for AgentFactory."""

    def test_create_drift_agent(self):
        """Test creating a drift agent."""
        factory = AgentFactory()

        # This will fail without API key, which is expected
        with pytest.raises(RuntimeError, match="API key"):
            factory.create_drift_agent()

    def test_create_tax_agent(self):
        """Test creating a tax agent."""
        factory = AgentFactory()

        with pytest.raises(RuntimeError, match="API key"):
            factory.create_tax_agent()

    def test_factory_with_api_key(self, monkeypatch):
        """Test factory with API key configured."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-12345")

        factory = AgentFactory()
        drift = factory.create_drift_agent()
        tax = factory.create_tax_agent()

        assert drift is not None
        assert tax is not None


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestAgentIntegration:
    """Integration tests for agent workflow."""

    def test_drift_to_tax_workflow(
        self,
        sample_portfolio,
        sample_transactions
    ):
        """Test drift agent output can be used by tax agent."""
        # Run drift analysis
        drift_result = OfflineDriftAnalyzer.analyze(sample_portfolio)

        # Pass drift recommendations to tax agent
        tax_result = OfflineTaxAnalyzer.analyze(
            sample_portfolio,
            sample_transactions,
            proposed_trades=drift_result.recommended_trades
        )

        # Tax agent should analyze drift agent's recommendations
        assert len(tax_result.proposed_trades_analysis) == len(drift_result.recommended_trades)

    def test_skills_discovered_for_drift_result(self, sample_portfolio):
        """Test relevant skills are discovered based on drift analysis."""
        drift_result = OfflineDriftAnalyzer.analyze(sample_portfolio)

        registry = SkillRegistry()

        # Build context from drift result
        context = {
            "holdings": sample_portfolio.holdings,
            "concentration_limit": sample_portfolio.client_profile.concentration_limit
        }

        skills = registry.discover_relevant_skills(context)

        # Should include concentration risk skill since drift detected it
        if drift_result.concentration_risks:
            assert "concentration_risk" in skills

    def test_complete_analysis_pipeline(
        self,
        sample_portfolio,
        sample_transactions
    ):
        """Test complete analysis pipeline."""
        # 1. Discover skills
        registry = SkillRegistry()
        context = {
            "holdings": sample_portfolio.holdings,
            "recent_transactions": sample_transactions,
            "concentration_limit": sample_portfolio.client_profile.concentration_limit
        }
        skills = registry.discover_relevant_skills(context)

        # 2. Run drift analysis
        drift_result = OfflineDriftAnalyzer.analyze(sample_portfolio)

        # 3. Run tax analysis on recommendations
        tax_result = OfflineTaxAnalyzer.analyze(
            sample_portfolio,
            sample_transactions,
            drift_result.recommended_trades,
            context
        )

        # 4. Verify complete output
        assert drift_result.portfolio_id == sample_portfolio.portfolio_id
        assert tax_result.portfolio_id == sample_portfolio.portfolio_id
        assert len(skills) > 0

        # 5. Results should be actionable
        if drift_result.concentration_risks:
            assert drift_result.recommended_trades

        if tax_result.wash_sale_violations:
            # Should warn about wash sale
            assert any("wash" in r.lower() for r in tax_result.recommendations)
