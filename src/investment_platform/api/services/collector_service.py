"""Service for collector metadata and asset search."""

import logging
from typing import Dict, Any, List, Optional
from investment_platform.collectors import (
    StockCollector,
    CryptoCollector,
    ForexCollector,
    BondCollector,
    CommodityCollector,
    EconomicCollector,
)

logger = logging.getLogger(__name__)


# Collector type mapping
COLLECTOR_CLASSES = {
    "stock": StockCollector,
    "crypto": CryptoCollector,
    "forex": ForexCollector,
    "bond": BondCollector,
    "commodity": CommodityCollector,
    "economic_indicator": EconomicCollector,
}


def get_collector_metadata() -> Dict[str, Any]:
    """
    Get metadata for all available collector types.
    
    Returns:
        Dictionary mapping asset types to their capabilities
    """
    metadata = {
        "stock": {
            "name": "Stock",
            "description": "Stock market data (OHLCV, dividends, splits)",
            "collector_class": "StockCollector",
            "intervals": [
                "1m", "2m", "5m", "15m", "30m", "60m", "90m",
                "1h", "1d", "5d", "1wk", "1mo", "3mo"
            ],
            "default_interval": "1d",
            "supports_dividends": True,
            "supports_splits": True,
        },
        "crypto": {
            "name": "Cryptocurrency",
            "description": "Cryptocurrency market data (OHLCV)",
            "collector_class": "CryptoCollector",
            "granularities": [
                "ONE_MINUTE",
                "FIVE_MINUTE",
                "FIFTEEN_MINUTE",
                "ONE_HOUR",
                "SIX_HOUR",
                "ONE_DAY",
            ],
            "default_granularity": "ONE_DAY",
        },
        "forex": {
            "name": "Foreign Exchange",
            "description": "Forex exchange rates",
            "collector_class": "ForexCollector",
            "symbol_format": "BASE_QUOTE (e.g., USD_EUR, GBP_USD)",
        },
        "bond": {
            "name": "Bond",
            "description": "U.S. Treasury bond rates and yields",
            "collector_class": "BondCollector",
            "series_ids": [
                "TB3MS",  # 3-Month Treasury Bill
                "DGS10",  # 10-Year Treasury Note
                "DGS30",  # 30-Year Treasury Bond
                "DFII10",  # 10-Year TIPS
            ],
        },
        "commodity": {
            "name": "Commodity",
            "description": "Commodity futures data (OHLCV)",
            "collector_class": "CommodityCollector",
            "intervals": [
                "1m", "2m", "5m", "15m", "30m", "60m", "90m",
                "1h", "1d", "5d", "1wk", "1mo", "3mo"
            ],
            "default_interval": "1d",
            "common_symbols": [
                "GC=F",  # Gold
                "SI=F",  # Silver
                "CL=F",  # Crude Oil
                "NG=F",  # Natural Gas
            ],
        },
        "economic_indicator": {
            "name": "Economic Indicator",
            "description": "Economic indicators from FRED",
            "collector_class": "EconomicCollector",
            "common_indicators": [
                "GDP",  # Gross Domestic Product
                "UNRATE",  # Unemployment Rate
                "CPIAUCSL",  # Consumer Price Index
                "DGS10",  # 10-Year Treasury Rate
            ],
        },
    }
    
    return metadata


def get_collector_options(asset_type: str) -> Dict[str, Any]:
    """
    Get collector-specific options for an asset type.
    
    Args:
        asset_type: Type of asset (stock, crypto, etc.)
        
    Returns:
        Dictionary with collector-specific options
        
    Raises:
        ValueError: If asset_type is not supported
    """
    if asset_type not in COLLECTOR_CLASSES:
        raise ValueError(f"Unsupported asset type: {asset_type}")
    
    metadata = get_collector_metadata()
    return metadata.get(asset_type, {})


def search_assets(asset_type: str, query: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Search for assets/symbols of a given type.
    
    Note: This is a basic implementation. In production, this would
    query a database of known assets or use API search endpoints.
    
    Args:
        asset_type: Type of asset to search
        query: Search query (symbol or name)
        limit: Maximum number of results
        
    Returns:
        List of asset dictionaries with symbol, name, etc.
    """
    query_lower = query.lower().strip()
    
    # Basic symbol suggestions based on asset type
    suggestions = []
    
    if asset_type == "stock":
        # Common stock symbols
        common_stocks = [
            {"symbol": "AAPL", "name": "Apple Inc."},
            {"symbol": "MSFT", "name": "Microsoft Corporation"},
            {"symbol": "GOOGL", "name": "Alphabet Inc."},
            {"symbol": "AMZN", "name": "Amazon.com Inc."},
            {"symbol": "TSLA", "name": "Tesla Inc."},
            {"symbol": "META", "name": "Meta Platforms Inc."},
            {"symbol": "NVDA", "name": "NVIDIA Corporation"},
            {"symbol": "JPM", "name": "JPMorgan Chase & Co."},
            {"symbol": "V", "name": "Visa Inc."},
            {"symbol": "JNJ", "name": "Johnson & Johnson"},
        ]
        suggestions = [s for s in common_stocks if query_lower in s["symbol"].lower() or query_lower in s["name"].lower()]
    
    elif asset_type == "crypto":
        # Common crypto pairs
        common_crypto = [
            {"symbol": "BTC-USD", "name": "Bitcoin / US Dollar"},
            {"symbol": "ETH-USD", "name": "Ethereum / US Dollar"},
            {"symbol": "BNB-USD", "name": "Binance Coin / US Dollar"},
            {"symbol": "SOL-USD", "name": "Solana / US Dollar"},
            {"symbol": "ADA-USD", "name": "Cardano / US Dollar"},
            {"symbol": "XRP-USD", "name": "Ripple / US Dollar"},
            {"symbol": "DOGE-USD", "name": "Dogecoin / US Dollar"},
            {"symbol": "DOT-USD", "name": "Polkadot / US Dollar"},
        ]
        suggestions = [s for s in common_crypto if query_lower in s["symbol"].lower() or query_lower in s["name"].lower()]
    
    elif asset_type == "forex":
        # Common forex pairs
        common_forex = [
            {"symbol": "USD_EUR", "name": "US Dollar / Euro"},
            {"symbol": "USD_GBP", "name": "US Dollar / British Pound"},
            {"symbol": "USD_JPY", "name": "US Dollar / Japanese Yen"},
            {"symbol": "USD_CHF", "name": "US Dollar / Swiss Franc"},
            {"symbol": "USD_CAD", "name": "US Dollar / Canadian Dollar"},
            {"symbol": "EUR_GBP", "name": "Euro / British Pound"},
            {"symbol": "EUR_JPY", "name": "Euro / Japanese Yen"},
        ]
        suggestions = [s for s in common_forex if query_lower in s["symbol"].lower() or query_lower in s["name"].lower()]
    
    elif asset_type == "bond":
        # FRED series IDs
        bond_series = [
            {"symbol": "TB3MS", "name": "3-Month Treasury Bill"},
            {"symbol": "DGS10", "name": "10-Year Treasury Note"},
            {"symbol": "DGS30", "name": "30-Year Treasury Bond"},
            {"symbol": "DFII10", "name": "10-Year TIPS"},
        ]
        suggestions = [s for s in bond_series if query_lower in s["symbol"].lower() or query_lower in s["name"].lower()]
    
    elif asset_type == "commodity":
        # Commodity futures
        commodities = [
            {"symbol": "GC=F", "name": "Gold Futures"},
            {"symbol": "SI=F", "name": "Silver Futures"},
            {"symbol": "CL=F", "name": "Crude Oil Futures"},
            {"symbol": "NG=F", "name": "Natural Gas Futures"},
            {"symbol": "BZ=F", "name": "Brent Crude Oil Futures"},
            {"symbol": "ZW=F", "name": "Wheat Futures"},
            {"symbol": "ZC=F", "name": "Corn Futures"},
        ]
        suggestions = [s for s in commodities if query_lower in s["symbol"].lower() or query_lower in s["name"].lower()]
    
    elif asset_type == "economic_indicator":
        # FRED economic indicators
        indicators = [
            {"symbol": "GDP", "name": "Gross Domestic Product"},
            {"symbol": "UNRATE", "name": "Unemployment Rate"},
            {"symbol": "CPIAUCSL", "name": "Consumer Price Index"},
            {"symbol": "DGS10", "name": "10-Year Treasury Rate"},
            {"symbol": "FEDFUNDS", "name": "Federal Funds Rate"},
            {"symbol": "INDPRO", "name": "Industrial Production Index"},
        ]
        suggestions = [s for s in indicators if query_lower in s["symbol"].lower() or query_lower in s["name"].lower()]
    
    return suggestions[:limit]


def validate_collection_params(
    asset_type: str,
    symbol: str,
    collector_kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Validate collection parameters before scheduling.
    
    Args:
        asset_type: Type of asset
        symbol: Asset symbol
        collector_kwargs: Optional collector-specific parameters
        
    Returns:
        Dictionary with validation result and any errors
        
    Raises:
        ValueError: If validation fails
    """
    errors = []
    
    if asset_type not in COLLECTOR_CLASSES:
        errors.append(f"Unsupported asset type: {asset_type}")
    
    if not symbol or not symbol.strip():
        errors.append("Symbol is required")
    
    # Validate collector-specific parameters
    if collector_kwargs:
        if asset_type == "crypto":
            valid_granularities = [
                "ONE_MINUTE", "FIVE_MINUTE", "FIFTEEN_MINUTE",
                "ONE_HOUR", "SIX_HOUR", "ONE_DAY"
            ]
            granularity = collector_kwargs.get("granularity")
            if granularity and granularity not in valid_granularities:
                errors.append(f"Invalid granularity: {granularity}. Must be one of {valid_granularities}")
        
        elif asset_type == "stock":
            valid_intervals = [
                "1m", "2m", "5m", "15m", "30m", "60m", "90m",
                "1h", "1d", "5d", "1wk", "1mo", "3mo"
            ]
            interval = collector_kwargs.get("interval")
            if interval and interval not in valid_intervals:
                errors.append(f"Invalid interval: {interval}. Must be one of {valid_intervals}")
    
    if errors:
        return {
            "valid": False,
            "errors": errors,
        }
    
    return {
        "valid": True,
        "errors": [],
    }

