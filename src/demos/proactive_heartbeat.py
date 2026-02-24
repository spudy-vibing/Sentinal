"""
SENTINEL PROACTIVE HEARTBEAT DEMO

Demonstrates the system's proactive monitoring capability:

1. Scheduled heartbeat runs (simulated cron job)
2. System detects portfolio drift that wasn't triggered by market event
3. Concentration risk found during routine check
4. Tax harvesting opportunities discovered
5. Advisor notified proactively

This showcases the "always watching" nature of Sentinel.

Usage:
    python -m src.demos.proactive_heartbeat
"""

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.contracts.schemas import (
    HeartbeatInput,
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
from src.routing import PersonaRouter
from src.ui import generate_canvas, save_canvas
from src.security import MerkleChain
from src.data import load_portfolio


# ═══════════════════════════════════════════════════════════════════════════
# DEMO CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

DEMO_PORTFOLIO_ID = "portfolio_a"
OUTPUT_DIR = Path("output")


def create_heartbeat_event() -> HeartbeatInput:
    """Create a routine heartbeat event."""
    return HeartbeatInput(
        event_id="heartbeat_daily_001",
        event_type=EventType.HEARTBEAT,
        session_id="demo_session_heartbeat",
        timestamp=datetime.now(timezone.utc),
        priority=5,  # Normal priority
        portfolio_ids=[DEMO_PORTFOLIO_ID]
    )


def print_header():
    """Print demo header."""
    print()
    print("═" * 70)
    print("  SENTINEL PROACTIVE HEARTBEAT DEMO")
    print("  Scheduled Portfolio Monitoring")
    print("═" * 70)
    print()


def print_section(title: str):
    """Print section header."""
    print()
    print(f"┌{'─' * 68}┐")
    print(f"│  {title:<66}│")
    print(f"└{'─' * 68}┘")
    print()


def run_demo():
    """Run the Heartbeat demo."""
    print_header()

    # Step 1: Heartbeat triggered
    print_section("STEP 1: Scheduled Heartbeat Triggered")
    heartbeat = create_heartbeat_event()
    print(f"  Time:           {heartbeat.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Event Type:     {heartbeat.event_type.value}")
    print(f"  Portfolios:     {heartbeat.portfolio_ids}")
    print(f"  Schedule:       Daily @ 06:00 UTC (simulated)")

    # Step 2: Load portfolio
    print_section("STEP 2: Loading Portfolio for Health Check")
    try:
        portfolio = load_portfolio(DEMO_PORTFOLIO_ID)
    except Exception:
        portfolio = _create_demo_portfolio()

    print(f"  Portfolio:      {portfolio.name}")
    print(f"  AUM:            ${portfolio.aum_usd:,.0f}")
    print(f"  Last Rebalance: {portfolio.last_rebalance.strftime('%Y-%m-%d')}")

    days_since_rebalance = (datetime.now(timezone.utc) - portfolio.last_rebalance.replace(tzinfo=timezone.utc)).days
    print(f"  Days Since:     {days_since_rebalance} days")

    # Step 3: Route the heartbeat
    print_section("STEP 3: Routing Decision")
    router = PersonaRouter()

    import src.routing.persona_router as router_module
    original_load = router_module.load_portfolio
    router_module.load_portfolio = lambda x: portfolio

    try:
        decision = router.route(heartbeat, DEMO_PORTFOLIO_ID)
        print(f"  Should Process: {decision.should_process}")
        print(f"  Priority:       {decision.priority.value.upper()}")
        print(f"  Context:")
        for key, value in decision.context_additions.items():
            print(f"    • {key}: {value}")
        print(f"  Reasoning:      {decision.reasoning[:60]}...")
    finally:
        router_module.load_portfolio = original_load

    # Step 4: Execute analysis
    print_section("STEP 4: Proactive Analysis")
    merkle_chain = MerkleChain()
    coordinator = OfflineCoordinator(merkle_chain=merkle_chain)

    # Add some transactions that create tax opportunities
    transactions = [
        Transaction(
            transaction_id="txn_hb_001",
            portfolio_id=DEMO_PORTFOLIO_ID,
            ticker="AMD",
            action=TradeAction.SELL,
            quantity=5000,
            price=165.00,
            timestamp=datetime.now(timezone.utc) - timedelta(days=40),
            wash_sale_disallowed=0
        ),
    ]

    print("  Running health check analysis...")
    print()
    result = coordinator.execute_analysis(
        portfolio=portfolio,
        transactions=transactions,
        context={"heartbeat_check": True, "scheduled": True}
    )

    # Show findings
    print("  📋 HEALTH CHECK RESULTS:")
    print()

    # Concentration check
    print("  Concentration Risk Check:")
    if result.drift_findings.concentration_risks:
        for risk in result.drift_findings.concentration_risks:
            status = "❌ OVER LIMIT" if risk.current_weight > risk.limit else "✓ OK"
            print(f"    {risk.ticker:<6} {risk.current_weight:>6.1%} / {risk.limit:.0%} limit  {status}")
    else:
        print("    ✓ All positions within limits")

    # Drift check
    print()
    print("  Allocation Drift Check:")
    for metric in result.drift_findings.drift_metrics:
        drift_pct = abs(metric.drift_pct)
        status = "⚠️ DRIFT" if drift_pct > 0.03 else "✓ OK"
        direction = "↑" if metric.drift_direction == "over" else "↓"
        print(f"    {metric.asset_class:<20} {direction} {drift_pct:>5.1%} drift  {status}")

    # Tax opportunities
    print()
    print("  Tax Optimization Check:")
    if result.tax_findings.tax_opportunities:
        total_savings = sum(o.estimated_benefit for o in result.tax_findings.tax_opportunities)
        print(f"    💰 Potential tax savings found: ${total_savings:,.0f}")
        for opp in result.tax_findings.tax_opportunities:
            print(f"      • {opp.ticker}: {opp.opportunity_type.value} - ${opp.estimated_benefit:,.0f}")
    else:
        print("    No immediate opportunities")

    # Show recommended action
    print_section("STEP 5: Proactive Recommendation")

    if result.scenarios:
        top_scenario = result.scenarios[0]
        print(f"  Recommended Action: {top_scenario.title}")
        print(f"  Utility Score: {top_scenario.utility_score.total_score:.1f}/100" if top_scenario.utility_score else "")
        print()
        print("  Action Steps:")
        for step in top_scenario.action_steps[:3]:
            print(f"    {step.step_number}. {step.action.value.upper()} {step.quantity:,.0f} {step.ticker}")
            print(f"       Timing: {step.timing}")
            print(f"       Reason: {step.rationale[:50]}...")

    # Generate output
    print_section("STEP 6: Generating Advisor Notification")

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / "heartbeat_canvas.html"
    save_canvas(result, str(output_path))

    print(f"  Canvas saved: {output_path}")
    print()
    print("  📧 Notification would be sent to advisor:")
    print("     Subject: [SENTINEL] Portfolio Health Check - Action Recommended")
    print(f"     Body: {len(result.drift_findings.concentration_risks)} concentration risks,")
    print(f"           {len(result.tax_findings.tax_opportunities)} tax opportunities found")

    # Summary
    print()
    print("═" * 70)
    print("  HEARTBEAT DEMO COMPLETE")
    print("═" * 70)
    print()
    print("  This demo showed Sentinel's proactive monitoring:")
    print("  ✓ Scheduled health checks run automatically")
    print("  ✓ Drift and concentration tracked continuously")
    print("  ✓ Tax opportunities surfaced before year-end")
    print("  ✓ Advisors notified only when action needed")
    print()

    return result


def _create_demo_portfolio() -> Portfolio:
    """Create demo portfolio."""
    now = datetime.now(timezone.utc)

    return Portfolio(
        portfolio_id=DEMO_PORTFOLIO_ID,
        client_id="CLIENT_001",
        name="Growth Portfolio - Heartbeat Demo",
        aum_usd=50_000_000,
        last_rebalance=now - timedelta(days=95),  # Almost due for quarterly
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
                portfolio_weight=0.17,
                cost_basis=5_000_000,
                unrealized_gain_loss=3_500_000,
                sector="Technology",
                asset_class="US Equities",
                tax_lots=[
                    TaxLot(
                        lot_id="NVDA_LOT_001",
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
                unrealized_gain_loss=-750_000,
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


if __name__ == "__main__":
    run_demo()
