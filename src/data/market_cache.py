"""
SENTINEL MARKET DATA CACHE

Cached market data loader for demo purposes.
In production, this would integrate with real market data providers.

Reference: docs/IMPLEMENTATION_PLAN.md Phase 1, Workstream A
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from src.contracts import (
    MarketData,
    PricePoint,
)


# ═══════════════════════════════════════════════════════════════════════════
# DATA PATHS
# ═══════════════════════════════════════════════════════════════════════════

DATA_DIR = Path(__file__).parent.parent.parent / "data"
MARKET_CACHE_DIR = DATA_DIR / "market_cache"


# ═══════════════════════════════════════════════════════════════════════════
# MARKET DATA CACHE
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class CachedMarketData:
    """
    Cached market data for a single ticker.

    Designed for demo scenarios with realistic but static data.
    """
    ticker: str
    current_price: float
    previous_close: float
    change_percent: float
    high_52w: float
    low_52w: float
    beta: float
    dividend_yield: float
    pe_ratio: Optional[float]
    market_cap: float
    sector: str
    industry: str
    exchange: str
    last_updated: datetime
    price_history: list[PricePoint] = field(default_factory=list)
    news_headlines: list[str] = field(default_factory=list)


class MarketDataCache:
    """
    Load and manage cached market data.

    For demo purposes, market data is stored as JSON files.
    This simulates what would be a real-time market data feed.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or MARKET_CACHE_DIR
        self._cache: dict[str, CachedMarketData] = {}

    def get_market_data(self, ticker: str) -> Optional[CachedMarketData]:
        """
        Get cached market data for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            CachedMarketData or None if not found
        """
        if ticker in self._cache:
            return self._cache[ticker]

        file_path = self.cache_dir / f"{ticker.lower()}.json"

        if not file_path.exists():
            return None

        with open(file_path, "r") as f:
            data = json.load(f)

        market_data = self._parse_market_data(data)
        self._cache[ticker] = market_data

        return market_data

    def _parse_market_data(self, data: dict) -> CachedMarketData:
        """Parse JSON into CachedMarketData."""
        price_history = [
            PricePoint(
                timestamp=datetime.fromisoformat(p["timestamp"]),
                price=p["price"],
                volume=p.get("volume", 0)
            )
            for p in data.get("price_history", [])
        ]

        return CachedMarketData(
            ticker=data["ticker"],
            current_price=data["current_price"],
            previous_close=data["previous_close"],
            change_percent=data["change_percent"],
            high_52w=data["high_52w"],
            low_52w=data["low_52w"],
            beta=data["beta"],
            dividend_yield=data["dividend_yield"],
            pe_ratio=data.get("pe_ratio"),
            market_cap=data["market_cap"],
            sector=data["sector"],
            industry=data["industry"],
            exchange=data["exchange"],
            last_updated=datetime.fromisoformat(data["last_updated"]),
            price_history=price_history,
            news_headlines=data.get("news_headlines", [])
        )

    def get_price(self, ticker: str) -> Optional[float]:
        """Get current price for a ticker."""
        data = self.get_market_data(ticker)
        return data.current_price if data else None

    def get_change_percent(self, ticker: str) -> Optional[float]:
        """Get daily change percentage for a ticker."""
        data = self.get_market_data(ticker)
        return data.change_percent if data else None

    def get_beta(self, ticker: str) -> Optional[float]:
        """Get beta (volatility) for a ticker."""
        data = self.get_market_data(ticker)
        return data.beta if data else None

    def list_cached_tickers(self) -> list[str]:
        """List all tickers in cache directory."""
        return [
            f.stem.upper() for f in self.cache_dir.glob("*.json")
            if f.is_file()
        ]

    def preload_all(self) -> dict[str, CachedMarketData]:
        """Preload all cached market data."""
        result = {}
        for ticker in self.list_cached_tickers():
            data = self.get_market_data(ticker)
            if data:
                result[ticker] = data
        return result

    def clear_cache(self):
        """Clear in-memory cache."""
        self._cache.clear()


# ═══════════════════════════════════════════════════════════════════════════
# SECTOR DATA
# ═══════════════════════════════════════════════════════════════════════════

class SectorData:
    """
    Sector-level market data for sector rotation analysis.
    """

    # Sector ETF mappings for benchmarking
    SECTOR_ETFS = {
        "Technology": "XLK",
        "Healthcare": "XLV",
        "Financials": "XLF",
        "Consumer Discretionary": "XLY",
        "Consumer Staples": "XLP",
        "Energy": "XLE",
        "Industrials": "XLI",
        "Materials": "XLB",
        "Utilities": "XLU",
        "Real Estate": "XLRE",
        "Communication Services": "XLC",
    }

    @staticmethod
    def get_sector_etf(sector: str) -> Optional[str]:
        """Get the ETF ticker for a sector."""
        return SectorData.SECTOR_ETFS.get(sector)

    @staticmethod
    def get_all_sectors() -> list[str]:
        """Get list of all tracked sectors."""
        return list(SectorData.SECTOR_ETFS.keys())


# ═══════════════════════════════════════════════════════════════════════════
# SUBSTITUTE FINDER
# ═══════════════════════════════════════════════════════════════════════════

class SubstituteFinder:
    """
    Find substitute securities for tax-loss harvesting.

    Substitutes should be:
    - Different enough to avoid wash sale rules
    - Similar enough to maintain portfolio exposure
    """

    # Pre-defined substitute mappings for demo
    SUBSTITUTES = {
        "NVDA": ["AMD", "AVGO", "QCOM", "INTC"],
        "AMD": ["NVDA", "AVGO", "QCOM", "INTC"],
        "AAPL": ["MSFT", "GOOGL", "META"],
        "MSFT": ["AAPL", "GOOGL", "AMZN"],
        "GOOGL": ["META", "MSFT", "AMZN"],
        "META": ["GOOGL", "SNAP", "PINS"],
        "AMZN": ["MSFT", "GOOGL", "WMT"],
        "TSLA": ["RIVN", "F", "GM"],
        "VEA": ["VXUS", "EFA", "IEFA"],
        "BND": ["AGG", "SCHZ", "VCIT"],
        "VNQ": ["IYR", "SCHH", "XLRE"],
        "GLD": ["IAU", "SGOL", "GLDM"],
    }

    @staticmethod
    def get_substitutes(ticker: str) -> list[str]:
        """
        Get list of potential substitute securities.

        Args:
            ticker: Original ticker to find substitutes for

        Returns:
            List of substitute tickers, ordered by preference
        """
        return SubstituteFinder.SUBSTITUTES.get(ticker, [])

    @staticmethod
    def is_substantially_identical(ticker1: str, ticker2: str) -> bool:
        """
        Check if two securities are substantially identical.

        For wash sale purposes, substantially identical securities
        cannot be used as substitutes.

        Args:
            ticker1: First ticker
            ticker2: Second ticker

        Returns:
            True if securities are substantially identical
        """
        # Same ticker is always identical
        if ticker1 == ticker2:
            return True

        # Class shares of same company
        identical_pairs = {
            ("GOOGL", "GOOG"),
            ("BRK.A", "BRK.B"),
        }

        pair = tuple(sorted([ticker1, ticker2]))
        return pair in identical_pairs


# ═══════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

_market_cache: Optional[MarketDataCache] = None


def get_market_cache() -> MarketDataCache:
    """Get or create default market data cache."""
    global _market_cache
    if _market_cache is None:
        _market_cache = MarketDataCache()
    return _market_cache


def get_price(ticker: str) -> Optional[float]:
    """Convenience function to get current price."""
    return get_market_cache().get_price(ticker)


def get_substitutes(ticker: str) -> list[str]:
    """Convenience function to get substitute securities."""
    return SubstituteFinder.get_substitutes(ticker)
