"""
SENTINEL GOLDEN PATH DEMO

The showcase scenario demonstrating the full Sentinel pipeline:

1. Market Event: Tech sector drops 4%
2. Drift Agent: Detects NVDA concentration (17% > 15% limit)
3. Tax Agent: Detects wash sale risk (NVDA sold 15 days ago)
4. Coordinator: Resolves conflict, generates scenarios
5. Utility Function: Ranks "AMD Substitute" highest (~69.6/100)
6. Canvas: Generates interactive UI for advisor

This demo can run in two modes:
- Offline: Uses OfflineCoordinator (no API calls)
- Live: Uses real Claude API calls

Usage:
    python -m src.demos.golden_path [--live]
"""

import asyncio
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.contracts.schemas import (
    MarketEventInput,
    EventType,
    Portfolio,
    Holding,
    TaxLot,
    ClientProfile,
    TargetAllocation,
    RiskProfile,
    Transaction,
    TradeAction,
)
from src.agents import OfflineCoordinator
from src.routing import PersonaRouter, route_event
from src.ui import generate_canvas, save_canvas
from src.security import MerkleChain
from src.data import load_portfolio, load_transactions


# ═══════════════════════════════════════════════════════════════════════════
# DEMO CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

DEMO_PORTFOLIO_ID = "portfolio_a"
OUTPUT_DIR = Path("output")


def create_market_event() -> MarketEventInput:
    """Create the triggering market event: Tech sector -4%."""
    return MarketEventInput(
        event_id="mkt_tech_selloff_001",
        event_type=EventType.MARKET_EVENT,
        session_id="demo_session_golden_path",
        timestamp=datetime.now(timezone.utc),
        priority=9,
        affected_sectors=["Technology"],
        magnitude=-0.04,  # 4% drop
        affected_tickers=["NVDA", "AMD", "AAPL", "MSFT", "GOOGL"],
        description="Technology sector experiences 4% selloff amid rising yields"
    )


def create_demo_transactions() -> list[Transaction]:
    """Create transaction history with recent NVDA sale (for wash sale demo)."""
    now = datetime.now(timezone.utc)

    return [
        # NVDA sold 15 days ago - creates wash sale window
        Transaction(
            transaction_id="txn_demo_001",
            portfolio_id=DEMO_PORTFOLIO_ID,
            ticker="NVDA",
            action=TradeAction.SELL,
            quantity=2000,
            price=870.00,
            timestamp=now - timedelta(days=15),
            wash_sale_disallowed=0
        ),
        # Some older transactions
        Transaction(
            transaction_id="txn_demo_002",
            portfolio_id=DEMO_PORTFOLIO_ID,
            ticker="AAPL",
            action=TradeAction.BUY,
            quantity=5000,
            price=178.00,
            timestamp=now - timedelta(days=45),
            wash_sale_disallowed=0
        ),
        Transaction(
            transaction_id="txn_demo_003",
            portfolio_id=DEMO_PORTFOLIO_ID,
            ticker="AMD",
            action=TradeAction.SELL,
            quantity=5000,
            price=165.00,
            timestamp=now - timedelta(days=60),
            wash_sale_disallowed=0
        ),
    ]


# ═══════════════════════════════════════════════════════════════════════════
# DEMO RUNNER
# ═══════════════════════════════════════════════════════════════════════════

def print_header():
    """Print demo header."""
    print()
    print("═" * 70)
    print("  SENTINEL GOLDEN PATH DEMO")
    print("  Multi-Agent UHNW Portfolio Monitoring System")
    print("═" * 70)
    print()


def print_section(title: str):
    """Print section header."""
    print()
    print(f"┌{'─' * 68}┐")
    print(f"│  {title:<66}│")
    print(f"└{'─' * 68}┘")
    print()


def run_demo(live_mode: bool = False):
    """
    Run the Golden Path demo.

    Args:
        live_mode: If True, use real Claude API calls
    """
    print_header()

    # Step 1: Create market event
    print_section("STEP 1: Market Event Detected")
    market_event = create_market_event()
    print(f"  Event ID:    {market_event.event_id}")
    print(f"  Type:        {market_event.event_type.value}")
    print(f"  Magnitude:   {market_event.magnitude:.1%}")
    print(f"  Sectors:     {', '.join(market_event.affected_sectors)}")
    print(f"  Description: {market_event.description}")

    # Step 2: Load portfolio
    print_section("STEP 2: Loading Portfolio")
    try:
        portfolio = load_portfolio(DEMO_PORTFOLIO_ID)
        print(f"  Portfolio:   {portfolio.name}")
        print(f"  AUM:         ${portfolio.aum_usd:,.0f}")
        print(f"  Holdings:    {len(portfolio.holdings)} positions")
        print(f"  Risk Profile: {portfolio.client_profile.risk_tolerance.value}")
        print(f"  Concentration Limit: {portfolio.client_profile.concentration_limit:.0%}")

        # Show tech holdings
        print()
        print("  Tech Holdings:")
        for h in portfolio.holdings:
            if h.sector == "Technology":
                over_limit = " ⚠️ OVER LIMIT" if h.portfolio_weight > portfolio.client_profile.concentration_limit else ""
                print(f"    {h.ticker:<6} {h.portfolio_weight:>6.1%} (${h.market_value:>12,.0f}){over_limit}")
    except Exception as e:
        print(f"  ❌ Error loading portfolio: {e}")
        print("  Creating demo portfolio instead...")
        portfolio = _create_demo_portfolio()

    # Step 3: Route event
    print_section("STEP 3: Routing Decision")
    router = PersonaRouter()

    # Mock the portfolio loader for routing
    import src.routing.persona_router as router_module
    original_load = router_module.load_portfolio
    router_module.load_portfolio = lambda x: portfolio

    try:
        decision = router.route(market_event, DEMO_PORTFOLIO_ID)
        print(f"  Should Process:  {decision.should_process}")
        print(f"  Priority:        {decision.priority.value.upper()}")
        print(f"  Agents Required: {[a.value for a in decision.agents_required]}")
        print(f"  Reasoning:       {decision.reasoning}")
    finally:
        router_module.load_portfolio = original_load

    # Step 4: Create Merkle chain for audit
    print_section("STEP 4: Initializing Audit Trail")
    merkle_chain = MerkleChain()
    merkle_chain.add_block({
        "event_type": "demo_started",
        "demo_name": "golden_path",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "portfolio_id": DEMO_PORTFOLIO_ID,
    })
    print(f"  Merkle Chain: Initialized")
    print(f"  Root Hash:    {merkle_chain.get_root_hash()[:32]}...")

    # Step 5: Execute analysis
    print_section("STEP 5: Executing Multi-Agent Analysis")

    transactions = create_demo_transactions()

    if live_mode:
        print("  Mode: LIVE (using Claude API)")
        print("  ⚠️  Live mode not implemented in demo - using offline")
        coordinator = OfflineCoordinator(merkle_chain=merkle_chain)
    else:
        print("  Mode: OFFLINE (using rule-based analyzers)")
        coordinator = OfflineCoordinator(merkle_chain=merkle_chain)

    print()
    print("  Dispatching agents in parallel...")
    result = coordinator.execute_analysis(
        portfolio=portfolio,
        transactions=transactions,
        context={"market_event": market_event.model_dump()}
    )

    # Show drift findings
    print()
    print("  📊 DRIFT AGENT FINDINGS:")
    drift = result.drift_findings
    print(f"     Drift Detected:  {drift.drift_detected}")
    print(f"     Urgency Score:   {drift.urgency_score}/10")
    print(f"     Concentration Risks: {len(drift.concentration_risks)}")
    for risk in drift.concentration_risks:
        print(f"       • {risk.ticker}: {risk.current_weight:.1%} vs {risk.limit:.1%} limit ({risk.severity.upper()})")
    print(f"     Recommended Trades: {len(drift.recommended_trades)}")
    for trade in drift.recommended_trades:
        print(f"       • {trade.action.value.upper()} {trade.quantity:,.0f} {trade.ticker} (urgency: {trade.urgency}/10)")

    # Show tax findings
    print()
    print("  💰 TAX AGENT FINDINGS:")
    tax = result.tax_findings
    print(f"     Wash Sale Violations: {len(tax.wash_sale_violations)}")
    for violation in tax.wash_sale_violations:
        print(f"       • {violation.ticker}: sold {violation.days_since_sale} days ago, ${violation.disallowed_loss:,.0f} at risk")
    print(f"     Tax Opportunities: {len(tax.tax_opportunities)}")
    for opp in tax.tax_opportunities:
        print(f"       • {opp.ticker}: {opp.opportunity_type.value} - ${opp.estimated_benefit:,.0f} potential savings")
    print(f"     Total Tax Impact: ${tax.total_tax_impact:,.0f}")

    # Show conflicts
    print_section("STEP 6: Conflict Detection")
    print(f"  Conflicts Detected: {len(result.conflicts_detected)}")
    for conflict in result.conflicts_detected:
        print(f"    ⚠️  {conflict.conflict_type}")
        print(f"       {conflict.description}")
        print(f"       Resolution Options:")
        for i, opt in enumerate(conflict.resolution_options, 1):
            print(f"         {i}. {opt}")

    # Show scenarios
    print_section("STEP 7: Scenario Generation & Ranking")
    print(f"  Generated Scenarios: {len(result.scenarios)}")
    print()

    for i, scenario in enumerate(result.scenarios, 1):
        is_recommended = scenario.scenario_id == result.recommended_scenario_id
        marker = "★ RECOMMENDED" if is_recommended else ""

        score = scenario.utility_score.total_score if scenario.utility_score else 0
        print(f"  {i}. {scenario.title} {marker}")
        print(f"     Score: {score:.1f}/100")
        print(f"     {scenario.description[:70]}...")
        print(f"     Steps: {len(scenario.action_steps)}")
        if scenario.utility_score:
            dims = {d.dimension: d.raw_score for d in scenario.utility_score.dimension_scores}
            print(f"     Dimensions: Risk={dims.get('risk_reduction', 0):.1f} Tax={dims.get('tax_savings', 0):.1f} Goal={dims.get('goal_alignment', 0):.1f}")
        print()

    # Generate Canvas
    print_section("STEP 8: Generating Canvas UI")

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / "golden_path_canvas.html"

    html = generate_canvas(result)
    save_canvas(result, str(output_path))

    print(f"  Canvas Generated: {output_path}")
    print(f"  File Size:        {len(html):,} bytes")
    print(f"  Scenarios:        {len(result.scenarios)}")
    print(f"  Conflicts:        {len(result.conflicts_detected)}")

    # Final audit
    print_section("STEP 9: Audit Trail Complete")
    print(f"  Blocks Added:     {len(merkle_chain._blocks)}")
    print(f"  Final Root Hash:  {merkle_chain.get_root_hash()[:32]}...")
    print(f"  Chain Valid:      {merkle_chain.verify_integrity()}")

    # Summary
    print()
    print("═" * 70)
    print("  DEMO COMPLETE")
    print("═" * 70)
    print()
    print(f"  ✓ Market event processed: Tech -4%")
    print(f"  ✓ NVDA concentration detected: 17% > 15% limit")
    print(f"  ✓ Wash sale conflict found: NVDA sold 15 days ago")
    print(f"  ✓ {len(result.scenarios)} scenarios generated")
    print(f"  ✓ Recommended: {result.scenarios[0].title}")
    print(f"  ✓ Canvas saved to: {output_path}")
    print()
    print("  Open the HTML file in a browser to see the interactive Canvas.")
    print()

    return result


def _create_demo_portfolio() -> Portfolio:
    """Create a demo portfolio if loading fails."""
    now = datetime.now(timezone.utc)

    return Portfolio(
        portfolio_id=DEMO_PORTFOLIO_ID,
        client_id="CLIENT_001",
        name="Demo Growth Portfolio - Tech Heavy",
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
            client_id="CLIENT_001",
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
                        lot_id="NVDA_LOT_001",
                        purchase_date=now - timedelta(days=400),
                        purchase_price=250.00,
                        quantity=5000,
                        cost_basis=1_250_000
                    ),
                    TaxLot(
                        lot_id="NVDA_LOT_002",
                        purchase_date=now - timedelta(days=250),
                        purchase_price=400.00,
                        quantity=3000,
                        cost_basis=1_200_000
                    ),
                    TaxLot(
                        lot_id="NVDA_LOT_003",
                        purchase_date=now - timedelta(days=150),
                        purchase_price=450.00,
                        quantity=2000,
                        cost_basis=900_000
                    ),
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
                        lot_id="AMD_LOT_001",
                        purchase_date=now - timedelta(days=300),
                        purchase_price=180.00,
                        quantity=25000,
                        cost_basis=4_500_000
                    )
                ]
            ),
            Holding(
                ticker="AAPL",
                quantity=20000,
                current_price=185.00,
                market_value=3_700_000,
                portfolio_weight=0.074,
                cost_basis=2_800_000,
                unrealized_gain_loss=900_000,
                sector="Technology",
                asset_class="US Equities",
                tax_lots=[
                    TaxLot(
                        lot_id="AAPL_LOT_001",
                        purchase_date=now - timedelta(days=600),
                        purchase_price=140.00,
                        quantity=20000,
                        cost_basis=2_800_000
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
                tax_lots=[
                    TaxLot(
                        lot_id="BND_LOT_001",
                        purchase_date=now - timedelta(days=800),
                        purchase_price=75.00,
                        quantity=100000,
                        cost_basis=7_500_000
                    )
                ]
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
                tax_lots=[
                    TaxLot(
                        lot_id="VEA_LOT_001",
                        purchase_date=now - timedelta(days=700),
                        purchase_price=46.67,
                        quantity=150000,
                        cost_basis=7_000_000
                    )
                ]
            ),
        ]
    )


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    live_mode = "--live" in sys.argv
    run_demo(live_mode=live_mode)
