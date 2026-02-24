"""
SENTINEL TEST FIXTURES

Shared fixtures for all tests.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator

from src.contracts.schemas import (
    EventType,
    RiskProfile,
    Portfolio,
    Holding,
    TaxLot,
    TargetAllocation,
    ClientProfile,
    Transaction,
    TradeAction,
)
from src.contracts.stubs import StubMerkleChain
from src.gateway import Gateway


# ═══════════════════════════════════════════════════════════════════════════
# EVENT LOOP
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ═══════════════════════════════════════════════════════════════════════════
# GATEWAY FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def merkle_chain():
    """Create a stub Merkle chain for testing."""
    return StubMerkleChain()


@pytest.fixture
async def gateway(merkle_chain) -> AsyncGenerator[Gateway, None]:
    """Create a gateway instance for testing."""
    gw = Gateway(
        merkle_chain=merkle_chain,
        enable_scheduler=False,  # Disable scheduler for most tests
    )
    await gw.start()
    yield gw
    await gw.stop()


@pytest.fixture
async def gateway_with_scheduler(merkle_chain) -> AsyncGenerator[Gateway, None]:
    """Create a gateway with scheduler enabled."""
    gw = Gateway(
        merkle_chain=merkle_chain,
        enable_scheduler=True,
    )
    await gw.start()
    yield gw
    await gw.stop()


# ═══════════════════════════════════════════════════════════════════════════
# PORTFOLIO FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_portfolio() -> Portfolio:
    """Create sample portfolio for testing."""
    return Portfolio(
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


@pytest.fixture
def sample_transactions() -> list[Transaction]:
    """Create sample transactions for testing."""
    return [
        Transaction(
            transaction_id="TXN_001",
            portfolio_id="UHNW_001",
            ticker="NVDA",
            action=TradeAction.SELL,
            quantity=5000,
            price=870.0,
            timestamp=datetime.now(timezone.utc),
            wash_sale_disallowed=0
        )
    ]
