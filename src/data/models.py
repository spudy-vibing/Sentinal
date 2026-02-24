"""
SENTINEL DATA MODELS

Data layer for loading and managing portfolios, holdings, and transactions.
Uses contracts from src/contracts for type safety.

Reference: docs/IMPLEMENTATION_PLAN.md Phase 1, Workstream A
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.contracts import (
    Portfolio,
    Holding,
    TaxLot,
    TargetAllocation,
    ClientProfile,
    Transaction,
    TradeAction,
    RiskProfile,
)


# ═══════════════════════════════════════════════════════════════════════════
# DATA PATHS
# ═══════════════════════════════════════════════════════════════════════════

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PORTFOLIOS_DIR = DATA_DIR / "portfolios"
MARKET_CACHE_DIR = DATA_DIR / "market_cache"


# ═══════════════════════════════════════════════════════════════════════════
# PORTFOLIO LOADER
# ═══════════════════════════════════════════════════════════════════════════

class PortfolioLoader:
    """
    Load and parse portfolio data from JSON files.

    Portfolios are stored as JSON in data/portfolios/ directory.
    """

    def __init__(self, portfolios_dir: Optional[Path] = None):
        self.portfolios_dir = portfolios_dir or PORTFOLIOS_DIR
        self._cache: dict[str, Portfolio] = {}

    def load_portfolio(self, portfolio_id: str, force_reload: bool = False) -> Portfolio:
        """
        Load portfolio from JSON file.

        Args:
            portfolio_id: Portfolio identifier (matches filename without .json)
            force_reload: If True, bypass cache

        Returns:
            Portfolio object

        Raises:
            FileNotFoundError: If portfolio file doesn't exist
            ValidationError: If JSON doesn't match schema
        """
        if not force_reload and portfolio_id in self._cache:
            return self._cache[portfolio_id]

        file_path = self.portfolios_dir / f"{portfolio_id}.json"

        if not file_path.exists():
            raise FileNotFoundError(f"Portfolio file not found: {file_path}")

        with open(file_path, "r") as f:
            data = json.load(f)

        portfolio = self._parse_portfolio(data)
        self._cache[portfolio_id] = portfolio

        return portfolio

    def _parse_portfolio(self, data: dict) -> Portfolio:
        """Parse raw JSON into Portfolio model."""
        # Parse holdings with tax lots
        holdings = []
        for h in data.get("holdings", []):
            tax_lots = [
                TaxLot(
                    lot_id=lot["lot_id"],
                    purchase_date=datetime.fromisoformat(lot["purchase_date"]),
                    purchase_price=lot["purchase_price"],
                    quantity=lot["quantity"],
                    cost_basis=lot["cost_basis"]
                )
                for lot in h.get("tax_lots", [])
            ]

            holdings.append(Holding(
                ticker=h["ticker"],
                quantity=h["quantity"],
                current_price=h["current_price"],
                market_value=h["market_value"],
                portfolio_weight=h["portfolio_weight"],
                cost_basis=h["cost_basis"],
                unrealized_gain_loss=h["unrealized_gain_loss"],
                tax_lots=tax_lots,
                sector=h["sector"],
                asset_class=h["asset_class"]
            ))

        # Parse target allocation
        target = data["target_allocation"]
        target_allocation = TargetAllocation(
            us_equities=target["us_equities"],
            international_equities=target["international_equities"],
            fixed_income=target["fixed_income"],
            alternatives=target["alternatives"],
            structured_products=target["structured_products"],
            cash=target["cash"]
        )

        # Parse client profile
        profile = data["client_profile"]
        client_profile = ClientProfile(
            client_id=profile["client_id"],
            risk_tolerance=RiskProfile(profile["risk_tolerance"]),
            tax_sensitivity=profile["tax_sensitivity"],
            concentration_limit=profile.get("concentration_limit", 0.15),
            rebalancing_frequency=profile.get("rebalancing_frequency", "quarterly")
        )

        return Portfolio(
            portfolio_id=data["portfolio_id"],
            client_id=data["client_id"],
            name=data["name"],
            aum_usd=data["aum_usd"],
            holdings=holdings,
            target_allocation=target_allocation,
            client_profile=client_profile,
            last_rebalance=datetime.fromisoformat(data["last_rebalance"]),
            cash_available=data["cash_available"]
        )

    def list_portfolios(self) -> list[str]:
        """List all available portfolio IDs."""
        return [
            f.stem for f in self.portfolios_dir.glob("*.json")
            if f.is_file()
        ]

    def load_all_portfolios(self) -> dict[str, Portfolio]:
        """Load all portfolios from directory."""
        portfolios = {}
        for portfolio_id in self.list_portfolios():
            try:
                portfolios[portfolio_id] = self.load_portfolio(portfolio_id)
            except Exception as e:
                print(f"Warning: Failed to load {portfolio_id}: {e}")
        return portfolios


# ═══════════════════════════════════════════════════════════════════════════
# TRANSACTION LOADER
# ═══════════════════════════════════════════════════════════════════════════

class TransactionLoader:
    """
    Load transaction history for portfolios.

    Transactions are embedded in portfolio JSON or stored separately.
    """

    def __init__(self, portfolios_dir: Optional[Path] = None):
        self.portfolios_dir = portfolios_dir or PORTFOLIOS_DIR

    def load_transactions(
        self,
        portfolio_id: str,
        days: int = 30
    ) -> list[Transaction]:
        """
        Load recent transactions for a portfolio.

        Args:
            portfolio_id: Portfolio identifier
            days: Number of days to look back

        Returns:
            List of Transaction objects within the time window
        """
        file_path = self.portfolios_dir / f"{portfolio_id}.json"

        if not file_path.exists():
            return []

        with open(file_path, "r") as f:
            data = json.load(f)

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        transactions = []

        for t in data.get("transactions", []):
            timestamp = datetime.fromisoformat(t["timestamp"])
            if timestamp >= cutoff:
                transactions.append(Transaction(
                    transaction_id=t["transaction_id"],
                    portfolio_id=portfolio_id,
                    ticker=t["ticker"],
                    action=TradeAction(t["action"]),
                    quantity=t["quantity"],
                    price=t["price"],
                    timestamp=timestamp,
                    wash_sale_disallowed=t.get("wash_sale_disallowed", 0)
                ))

        return sorted(transactions, key=lambda x: x.timestamp, reverse=True)


# ═══════════════════════════════════════════════════════════════════════════
# PORTFOLIO ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════

class PortfolioAnalytics:
    """
    Utility functions for portfolio analysis.
    """

    @staticmethod
    def calculate_sector_weights(portfolio: Portfolio) -> dict[str, float]:
        """Calculate total weight per sector."""
        sector_weights: dict[str, float] = {}
        for holding in portfolio.holdings:
            sector_weights[holding.sector] = sector_weights.get(holding.sector, 0) + holding.portfolio_weight
        return sector_weights

    @staticmethod
    def calculate_asset_class_weights(portfolio: Portfolio) -> dict[str, float]:
        """Calculate total weight per asset class."""
        class_weights: dict[str, float] = {}
        for holding in portfolio.holdings:
            class_weights[holding.asset_class] = class_weights.get(holding.asset_class, 0) + holding.portfolio_weight
        return class_weights

    @staticmethod
    def find_concentration_risks(
        portfolio: Portfolio,
        limit: Optional[float] = None
    ) -> list[Holding]:
        """
        Find holdings exceeding concentration limit.

        Args:
            portfolio: Portfolio to analyze
            limit: Override concentration limit (default: use client profile)

        Returns:
            List of holdings exceeding limit
        """
        threshold = limit or portfolio.client_profile.concentration_limit
        return [h for h in portfolio.holdings if h.portfolio_weight > threshold]

    @staticmethod
    def calculate_drift(portfolio: Portfolio) -> dict[str, float]:
        """
        Calculate allocation drift from targets.

        Returns:
            Dict mapping asset class to drift percentage
        """
        current = PortfolioAnalytics.calculate_asset_class_weights(portfolio)
        target = portfolio.target_allocation

        drift = {}
        target_dict = {
            "US Equities": target.us_equities,
            "International Equities": target.international_equities,
            "Fixed Income": target.fixed_income,
            "Alternatives": target.alternatives,
            "Structured Products": target.structured_products,
            "Cash": target.cash,
        }

        for asset_class, target_weight in target_dict.items():
            current_weight = current.get(asset_class, 0)
            drift[asset_class] = current_weight - target_weight

        return drift

    @staticmethod
    def find_wash_sale_risks(
        transactions: list[Transaction],
        proposed_ticker: str,
        days: int = 30
    ) -> list[Transaction]:
        """
        Find transactions that would cause wash sale if ticker is sold.

        Args:
            transactions: Recent transaction history
            proposed_ticker: Ticker to check
            days: Wash sale window (default 30)

        Returns:
            List of recent sales that would trigger wash sale
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return [
            t for t in transactions
            if t.ticker == proposed_ticker
            and t.action == TradeAction.SELL
            and t.timestamp >= cutoff
        ]


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

# Default loader instances
_portfolio_loader: Optional[PortfolioLoader] = None
_transaction_loader: Optional[TransactionLoader] = None


def get_portfolio_loader() -> PortfolioLoader:
    """Get or create default portfolio loader."""
    global _portfolio_loader
    if _portfolio_loader is None:
        _portfolio_loader = PortfolioLoader()
    return _portfolio_loader


def get_transaction_loader() -> TransactionLoader:
    """Get or create default transaction loader."""
    global _transaction_loader
    if _transaction_loader is None:
        _transaction_loader = TransactionLoader()
    return _transaction_loader


def load_portfolio(portfolio_id: str) -> Portfolio:
    """Convenience function to load a portfolio."""
    return get_portfolio_loader().load_portfolio(portfolio_id)


def load_transactions(portfolio_id: str, days: int = 30) -> list[Transaction]:
    """Convenience function to load transactions."""
    return get_transaction_loader().load_transactions(portfolio_id, days)
