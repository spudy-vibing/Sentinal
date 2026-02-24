"""
SENTINEL MAIN ENTRY POINT

Command-line interface for running Sentinel demos and utilities.

Usage:
    python -m src.main --demo golden_path     # Run golden path demo
    python -m src.main --demo heartbeat       # Run heartbeat demo
    python -m src.main --demo webhook         # Run webhook demo
    python -m src.main --verify-merkle        # Verify Merkle chain integrity
    python -m src.main --generate-canvas      # Generate sample Canvas
"""

import argparse
import sys
from pathlib import Path


def main():
    """Main entry point for Sentinel CLI."""
    parser = argparse.ArgumentParser(
        prog="sentinel",
        description="SENTINEL: Multi-Agent UHNW Portfolio Monitoring System"
    )

    # Demo commands
    parser.add_argument(
        "--demo",
        choices=["golden_path", "heartbeat", "webhook"],
        help="Run a specific demo"
    )

    # Verification commands
    parser.add_argument(
        "--verify-merkle",
        action="store_true",
        help="Verify Merkle chain integrity"
    )

    # Generation commands
    parser.add_argument(
        "--generate-canvas",
        action="store_true",
        help="Generate a sample Canvas HTML"
    )

    # Output options
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output",
        help="Output directory (default: output)"
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    if args.demo:
        run_demo(args.demo)
    elif args.verify_merkle:
        verify_merkle_chain()
    elif args.generate_canvas:
        generate_sample_canvas(output_dir)
    else:
        parser.print_help()


def run_demo(demo_name: str):
    """Run a specific demo."""
    print()
    print("═" * 70)
    print(f"  SENTINEL — Running {demo_name.replace('_', ' ').title()} Demo")
    print("═" * 70)
    print()

    if demo_name == "golden_path":
        from src.demos.golden_path import run_demo as run
        run()
    elif demo_name == "heartbeat":
        from src.demos.proactive_heartbeat import run_demo as run
        run()
    elif demo_name == "webhook":
        from src.demos.webhook_trigger import run_demo as run
        run()


def verify_merkle_chain():
    """Verify Merkle chain integrity."""
    print()
    print("═" * 70)
    print("  SENTINEL — Merkle Chain Verification")
    print("═" * 70)
    print()

    from src.security import MerkleChain
    from datetime import datetime, timezone

    # Create a test chain with sample events
    print("  Creating sample Merkle chain for verification...")
    print()

    chain = MerkleChain()

    # Add sample events
    events = [
        {"event_type": "system_initialized", "session_id": "verify_session"},
        {"event_type": "market_event_detected", "session_id": "verify_session", "magnitude": -0.04},
        {"event_type": "agent_invoked", "session_id": "verify_session", "agent": "drift"},
        {"event_type": "agent_invoked", "session_id": "verify_session", "agent": "tax"},
        {"event_type": "agent_completed", "session_id": "verify_session", "agent": "drift"},
        {"event_type": "agent_completed", "session_id": "verify_session", "agent": "tax"},
        {"event_type": "conflict_detected", "session_id": "verify_session", "type": "WASH_SALE"},
        {"event_type": "recommendation_generated", "session_id": "verify_session", "scenarios": 4},
    ]

    for event in events:
        chain.add_block(event)

    # Display chain info
    print("  Chain Statistics:")
    print(f"    Blocks:     {len(chain._blocks)}")
    print(f"    Root Hash:  {chain.get_root_hash()[:32]}...")
    print()

    # Verify chain
    print("  Running Integrity Check...")
    print()

    is_valid = chain.verify_integrity()

    if is_valid:
        print("  ✓ CHAIN VERIFIED")
        print("    All blocks are valid and properly linked.")
        print("    No tampering detected.")
    else:
        print("  ✗ CHAIN VERIFICATION FAILED")
        print("    Potential tampering or corruption detected!")

    print()

    # Display block details
    print("  Block Details:")
    print("  " + "─" * 66)

    for i, block in enumerate(chain._blocks):
        print(f"    Block {i}:")
        print(f"      Event:     {block.event_type}")
        print(f"      Time:      {block.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"      Hash:      {block.current_hash[:24]}...")
        print(f"      Prev Hash: {block.previous_hash[:24] if block.previous_hash else 'GENESIS'}...")
        print()

    print("  " + "─" * 66)
    print()

    # Final status
    print("  Verification Complete")
    print(f"    Status:     {'PASSED' if is_valid else 'FAILED'}")
    print(f"    Timestamp:  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    return is_valid


def generate_sample_canvas(output_dir: Path):
    """Generate a sample Canvas HTML file."""
    print()
    print("═" * 70)
    print("  SENTINEL — Canvas Generation")
    print("═" * 70)
    print()

    from datetime import datetime, timezone, timedelta
    from src.contracts.schemas import (
        Portfolio, Holding, TaxLot, ClientProfile, TargetAllocation, RiskProfile
    )
    from src.agents import OfflineCoordinator
    from src.ui import save_canvas

    # Create sample portfolio
    now = datetime.now(timezone.utc)

    portfolio = Portfolio(
        portfolio_id="sample_portfolio",
        client_id="sample_client",
        name="Sample Growth Portfolio",
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
            client_id="sample_client",
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
                        lot_id="LOT_001",
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

    print("  Running analysis...")

    # Run analysis
    coordinator = OfflineCoordinator()
    result = coordinator.execute_analysis(
        portfolio=portfolio,
        transactions=[],
        context={}
    )

    # Generate Canvas
    output_path = output_dir / "sample_canvas.html"
    save_canvas(result, str(output_path))

    print()
    print(f"  ✓ Canvas generated: {output_path}")
    print(f"    Portfolio:  {portfolio.name}")
    print(f"    AUM:        ${portfolio.aum_usd:,.0f}")
    print(f"    Scenarios:  {len(result.scenarios)}")
    print(f"    Conflicts:  {len(result.conflicts_detected)}")
    print()
    print("  Open the HTML file in a browser to view the Canvas.")
    print()


if __name__ == "__main__":
    main()
