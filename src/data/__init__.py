"""
SENTINEL DATA PACKAGE

Data layer for loading portfolios, market data, and transactions.

Usage:
    from src.data import load_portfolio, load_transactions
    from src.data import get_market_cache, get_price, get_substitutes
    from src.data import PortfolioAnalytics
"""

from .models import (
    # Loaders
    PortfolioLoader,
    TransactionLoader,
    get_portfolio_loader,
    get_transaction_loader,
    # Convenience functions
    load_portfolio,
    load_transactions,
    # Analytics
    PortfolioAnalytics,
    # Paths
    DATA_DIR,
    PORTFOLIOS_DIR,
    MARKET_CACHE_DIR,
)

from .market_cache import (
    # Cache
    MarketDataCache,
    CachedMarketData,
    get_market_cache,
    # Convenience functions
    get_price,
    get_substitutes,
    # Sector data
    SectorData,
    # Substitutes
    SubstituteFinder,
)

from .vector_store import (
    # Config
    VectorStoreConfig,
    SearchResult,
    # Stores
    VectorStore,
    MemoryStore,
    # Functions
    get_vector_store,
    get_memory_store,
    is_chromadb_available,
)

__all__ = [
    # Loaders
    "PortfolioLoader",
    "TransactionLoader",
    "get_portfolio_loader",
    "get_transaction_loader",
    # Convenience
    "load_portfolio",
    "load_transactions",
    # Analytics
    "PortfolioAnalytics",
    # Market Cache
    "MarketDataCache",
    "CachedMarketData",
    "get_market_cache",
    "get_price",
    "get_substitutes",
    "SectorData",
    "SubstituteFinder",
    # Vector Store
    "VectorStoreConfig",
    "SearchResult",
    "VectorStore",
    "MemoryStore",
    "get_vector_store",
    "get_memory_store",
    "is_chromadb_available",
    # Paths
    "DATA_DIR",
    "PORTFOLIOS_DIR",
    "MARKET_CACHE_DIR",
]
