"""
SENTINEL V2 — Portfolios Router
Handles portfolio data retrieval and management.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

router = APIRouter()


class HoldingResponse(BaseModel):
    """Holding data for API response."""
    ticker: str
    quantity: float
    current_price: float
    market_value: float
    portfolio_weight: float
    cost_basis: float
    unrealized_gain_loss: float
    sector: str
    asset_class: str


class PortfolioResponse(BaseModel):
    """Portfolio data for API response."""
    portfolio_id: str
    client_id: str
    name: str
    aum_usd: float
    cash_available: float
    holdings: List[HoldingResponse]
    last_rebalance: str
    risk_tolerance: str
    tax_sensitivity: float
    concentration_limit: float


class PortfolioSummary(BaseModel):
    """Brief portfolio summary for list view."""
    portfolio_id: str
    name: str
    aum_usd: float
    holdings_count: int
    top_holding: str
    top_holding_weight: float


@router.get("/", response_model=List[PortfolioSummary])
async def list_portfolios():
    """Get list of available portfolios."""
    try:
        from src.data import load_portfolio

        portfolios = []
        for pid in ["portfolio_a", "portfolio_b", "portfolio_c"]:
            try:
                p = load_portfolio(pid)
                top_holding = max(p.holdings, key=lambda h: h.portfolio_weight)
                portfolios.append(PortfolioSummary(
                    portfolio_id=p.portfolio_id,
                    name=p.name,
                    aum_usd=p.aum_usd,
                    holdings_count=len(p.holdings),
                    top_holding=top_holding.ticker,
                    top_holding_weight=top_holding.portfolio_weight
                ))
            except Exception:
                continue

        # Add demo portfolios if none found
        if not portfolios:
            portfolios = [
                PortfolioSummary(
                    portfolio_id="portfolio_a",
                    name="Growth Portfolio A",
                    aum_usd=50_000_000,
                    holdings_count=5,
                    top_holding="NVDA",
                    top_holding_weight=0.17
                ),
                PortfolioSummary(
                    portfolio_id="portfolio_b",
                    name="Conservative Portfolio B",
                    aum_usd=80_000_000,
                    holdings_count=8,
                    top_holding="BND",
                    top_holding_weight=0.25
                ),
                PortfolioSummary(
                    portfolio_id="portfolio_c",
                    name="Liquidity Event Portfolio C",
                    aum_usd=30_000_000,
                    holdings_count=3,
                    top_holding="PRIVATE",
                    top_holding_weight=0.60
                ),
            ]

        return portfolios

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(portfolio_id: str):
    """Get detailed portfolio data."""
    try:
        from src.data import load_portfolio

        try:
            portfolio = load_portfolio(portfolio_id)
        except Exception:
            # Return demo data if not found
            from src.demos.golden_path import _create_demo_portfolio
            portfolio = _create_demo_portfolio()

        return PortfolioResponse(
            portfolio_id=portfolio.portfolio_id,
            client_id=portfolio.client_id,
            name=portfolio.name,
            aum_usd=portfolio.aum_usd,
            cash_available=portfolio.cash_available,
            holdings=[
                HoldingResponse(
                    ticker=h.ticker,
                    quantity=h.quantity,
                    current_price=h.current_price,
                    market_value=h.market_value,
                    portfolio_weight=h.portfolio_weight,
                    cost_basis=h.cost_basis,
                    unrealized_gain_loss=h.unrealized_gain_loss,
                    sector=h.sector,
                    asset_class=h.asset_class
                )
                for h in portfolio.holdings
            ],
            last_rebalance=portfolio.last_rebalance.isoformat(),
            risk_tolerance=portfolio.client_profile.risk_tolerance.value,
            tax_sensitivity=portfolio.client_profile.tax_sensitivity,
            concentration_limit=portfolio.client_profile.concentration_limit
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}/risks")
async def get_portfolio_risks(portfolio_id: str):
    """Get risk analysis for a portfolio."""
    try:
        from src.data import load_portfolio
        from src.agents import DriftAgent

        try:
            portfolio = load_portfolio(portfolio_id)
        except Exception:
            from src.demos.golden_path import _create_demo_portfolio
            portfolio = _create_demo_portfolio()

        # Run drift analysis
        drift_agent = DriftAgent()
        result = drift_agent.analyze(portfolio, {})

        return {
            "portfolio_id": portfolio_id,
            "drift_detected": result.drift_detected,
            "urgency_score": result.urgency_score,
            "concentration_risks": [
                {
                    "ticker": r.ticker,
                    "current_weight": r.current_weight,
                    "limit": r.limit,
                    "excess": r.excess,
                    "severity": r.severity
                }
                for r in result.concentration_risks
            ],
            "drift_metrics": [
                {
                    "asset_class": m.asset_class,
                    "target_weight": m.target_weight,
                    "current_weight": m.current_weight,
                    "drift_pct": m.drift_pct,
                    "direction": m.drift_direction
                }
                for m in result.drift_metrics
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
