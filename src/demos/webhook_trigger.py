"""
SENTINEL WEBHOOK TRIGGER DEMO

Demonstrates external event integration:

1. SEC filing webhook arrives (earnings surprise)
2. News affects portfolio holdings
3. System triggers immediate analysis
4. Quick response recommendations generated

This shows Sentinel's ability to respond to real-world events.

Usage:
    python -m src.demos.webhook_trigger
"""

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.contracts.schemas import (
    WebhookInput,
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


def create_webhook_event() -> WebhookInput:
    """Create SEC filing webhook event."""
    return WebhookInput(
        event_id="webhook_sec_001",
        event_type=EventType.WEBHOOK,
        session_id="demo_session_webhook",
        timestamp=datetime.now(timezone.utc),
        priority=8,
        source="sec_edgar_feed",
        payload={
            "type": "news_alert",
            "filing_type": "8-K",
            "company": "NVIDIA Corporation",
            "tickers": ["NVDA"],
            "headline": "NVIDIA Announces Record Q4 Revenue, Beats Estimates by 15%",
            "summary": "NVIDIA Corp. reported Q4 revenue of $22.1B, exceeding analyst estimates. Data center revenue grew 400% YoY driven by AI demand.",
            "sentiment": "positive",
            "price_impact_estimate": 0.08,  # +8% expected
            "urgency": "high",
            "source_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001045810"
        }
    )


def print_header():
    """Print demo header."""
    print()
    print("═" * 70)
    print("  SENTINEL WEBHOOK TRIGGER DEMO")
    print("  External Event Response System")
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
    """Run the Webhook demo."""
    print_header()

    # Step 1: Webhook received
    print_section("STEP 1: External Webhook Received")
    webhook = create_webhook_event()
    payload = webhook.payload

    print(f"  Source:    {webhook.source}")
    print(f"  Type:      {payload['type']}")
    print(f"  Filing:    {payload['filing_type']}")
    print(f"  Company:   {payload['company']}")
    print(f"  Tickers:   {payload['tickers']}")
    print()
    print(f"  📰 HEADLINE:")
    print(f"     {payload['headline']}")
    print()
    print(f"  Summary:   {payload['summary'][:60]}...")
    print(f"  Sentiment: {payload['sentiment'].upper()}")
    print(f"  Est. Impact: {payload['price_impact_estimate']:+.0%}")

    # Step 2: Load portfolio
    print_section("STEP 2: Checking Portfolio Exposure")
    try:
        portfolio = load_portfolio(DEMO_PORTFOLIO_ID)
    except Exception:
        portfolio = _create_demo_portfolio()

    # Check exposure to affected tickers
    affected_tickers = set(payload['tickers'])
    exposed_holdings = [h for h in portfolio.holdings if h.ticker in affected_tickers]

    print(f"  Portfolio: {portfolio.name}")
    print(f"  AUM:       ${portfolio.aum_usd:,.0f}")
    print()

    if exposed_holdings:
        total_exposure = sum(h.market_value for h in exposed_holdings)
        total_weight = sum(h.portfolio_weight for h in exposed_holdings)

        print(f"  ⚠️  EXPOSURE DETECTED:")
        print(f"     Total Exposure: ${total_exposure:,.0f} ({total_weight:.1%} of portfolio)")
        print()
        for h in exposed_holdings:
            gain_loss = "+" if h.unrealized_gain_loss >= 0 else ""
            print(f"     {h.ticker}:")
            print(f"       Position:     {h.quantity:,} shares @ ${h.current_price:.2f}")
            print(f"       Market Value: ${h.market_value:,.0f}")
            print(f"       Weight:       {h.portfolio_weight:.1%}")
            print(f"       Unrealized:   {gain_loss}${h.unrealized_gain_loss:,.0f}")
    else:
        print("  ✓ No direct exposure to affected securities")

    # Step 3: Route the webhook
    print_section("STEP 3: Routing Decision")
    router = PersonaRouter()

    import src.routing.persona_router as router_module
    original_load = router_module.load_portfolio
    router_module.load_portfolio = lambda x: portfolio

    try:
        decision = router.route(webhook, DEMO_PORTFOLIO_ID)
        print(f"  Should Process: {decision.should_process}")
        print(f"  Priority:       {decision.priority.value.upper()}")
        print(f"  Agents:         {[a.value for a in decision.agents_required]}")
        print(f"  Reasoning:      {decision.reasoning}")
    finally:
        router_module.load_portfolio = original_load

    # Step 4: Execute analysis
    print_section("STEP 4: Rapid Response Analysis")
    merkle_chain = MerkleChain()
    coordinator = OfflineCoordinator(merkle_chain=merkle_chain)

    print("  Analyzing position impact...")
    print()

    result = coordinator.execute_analysis(
        portfolio=portfolio,
        transactions=[],
        context={
            "webhook": webhook.model_dump(),
            "news_event": payload,
            "affected_holdings": [h.ticker for h in exposed_holdings]
        }
    )

    # Impact analysis
    print("  📊 POSITION ANALYSIS:")
    print()

    if exposed_holdings:
        nvda = exposed_holdings[0]  # Assuming NVDA
        estimated_gain = nvda.market_value * payload['price_impact_estimate']
        new_value = nvda.market_value + estimated_gain
        new_weight = new_value / portfolio.aum_usd

        print(f"  If +{payload['price_impact_estimate']:.0%} price move occurs:")
        print(f"    Current Value:  ${nvda.market_value:,.0f}")
        print(f"    Estimated Gain: ${estimated_gain:,.0f}")
        print(f"    New Value:      ${new_value:,.0f}")
        print(f"    New Weight:     {new_weight:.1%}")

        if new_weight > portfolio.client_profile.concentration_limit:
            excess = new_weight - portfolio.client_profile.concentration_limit
            print()
            print(f"    ⚠️  Would exceed concentration limit by {excess:.1%}")
            print(f"       Consider proactive rebalancing")

    # Show recommendations
    print_section("STEP 5: Event-Driven Recommendations")

    print("  Conflict Analysis:")
    if result.conflicts_detected:
        for conflict in result.conflicts_detected:
            print(f"    ⚠️ {conflict.conflict_type}")
            print(f"       {conflict.description[:60]}...")
    else:
        print("    ✓ No conflicts detected")

    print()
    print("  Generated Scenarios:")
    for i, scenario in enumerate(result.scenarios, 1):
        is_top = scenario.scenario_id == result.recommended_scenario_id
        marker = " ★" if is_top else ""
        score = scenario.utility_score.total_score if scenario.utility_score else 0
        print(f"    {i}. {scenario.title}{marker} (Score: {score:.1f})")

    if result.scenarios:
        top = result.scenarios[0]
        print()
        print(f"  Recommended: {top.title}")
        print(f"  Rationale: {top.description[:70]}...")

    # Generate output
    print_section("STEP 6: Alert Generation")

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / "webhook_canvas.html"
    save_canvas(result, str(output_path))

    print(f"  Canvas saved: {output_path}")
    print()
    print("  📱 Push notification would be sent:")
    print(f"     Title: NVDA Earnings Beat - Review Required")
    print(f"     Body: Your position may exceed concentration limits.")
    print(f"           {len(result.scenarios)} scenarios ready for review.")

    # Summary
    print()
    print("═" * 70)
    print("  WEBHOOK DEMO COMPLETE")
    print("═" * 70)
    print()
    print("  This demo showed Sentinel's external event handling:")
    print("  ✓ SEC filing webhook processed in real-time")
    print("  ✓ Portfolio exposure automatically checked")
    print("  ✓ Concentration risk projection calculated")
    print("  ✓ Proactive recommendations generated")
    print("  ✓ Advisor alerted before market opens")
    print()

    return result


def _create_demo_portfolio() -> Portfolio:
    """Create demo portfolio."""
    now = datetime.now(timezone.utc)

    return Portfolio(
        portfolio_id=DEMO_PORTFOLIO_ID,
        client_id="CLIENT_001",
        name="Growth Portfolio - Webhook Demo",
        aum_usd=50_000_000,
        last_rebalance=now - timedelta(days=60),
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
                tax_lots=[]
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
        ]
    )


if __name__ == "__main__":
    run_demo()
