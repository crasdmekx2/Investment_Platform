"""Data collectors module for the Investment Platform."""

from investment_platform.collectors.base import (
    APIError,
    BaseDataCollector,
    ConfigurationError,
    DataCollectionError,
    RateLimitError,
    ValidationError,
)
from investment_platform.collectors.bond_collector import BondCollector
from investment_platform.collectors.commodity_collector import CommodityCollector
from investment_platform.collectors.crypto_collector import CryptoCollector
from investment_platform.collectors.economic_collector import EconomicCollector
from investment_platform.collectors.forex_collector import ForexCollector
from investment_platform.collectors.stock_collector import StockCollector

__all__ = [
    # Base classes and exceptions
    "BaseDataCollector",
    "DataCollectionError",
    "APIError",
    "RateLimitError",
    "ValidationError",
    "ConfigurationError",
    # Collectors
    "CryptoCollector",
    "StockCollector",
    "EconomicCollector",
    "ForexCollector",
    "BondCollector",
    "CommodityCollector",
]
