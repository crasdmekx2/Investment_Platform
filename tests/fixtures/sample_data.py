"""
Sample data fixtures for testing.
"""

from datetime import datetime, timedelta
from decimal import Decimal


def get_sample_stock_asset():
    """Get sample stock asset data."""
    return {
        'symbol': 'AAPL',
        'asset_type': 'stock',
        'name': 'Apple Inc.',
        'exchange': 'NASDAQ',
        'currency': 'USD',
        'sector': 'Technology',
        'industry': 'Consumer Electronics',
        'source': 'Yahoo Finance'
    }


def get_sample_forex_asset():
    """Get sample forex asset data."""
    return {
        'symbol': 'EURUSD',
        'asset_type': 'forex',
        'name': 'EUR/USD',
        'base_currency': 'EUR',
        'quote_currency': 'USD',
        'source': 'Test'
    }


def get_sample_crypto_asset():
    """Get sample crypto asset data."""
    return {
        'symbol': 'BTC-USD',
        'asset_type': 'crypto',
        'name': 'Bitcoin',
        'exchange': 'Coinbase',
        'base_currency': 'BTC',
        'quote_currency': 'USD',
        'source': 'Coinbase'
    }


def get_sample_bond_asset():
    """Get sample bond asset data."""
    return {
        'symbol': 'DGS10',
        'asset_type': 'bond',
        'name': '10-Year Treasury Constant Maturity Rate',
        'series_id': 'DGS10',
        'security_type': 'TNOTES',
        'source': 'FRED'
    }


def get_sample_economic_indicator_asset():
    """Get sample economic indicator asset data."""
    return {
        'symbol': 'GDP',
        'asset_type': 'economic_indicator',
        'name': 'Gross Domestic Product',
        'series_id': 'GDP',
        'source': 'FRED'
    }


def get_sample_market_data_points(count=10, start_time=None):
    """Get sample market data points."""
    if start_time is None:
        start_time = datetime.now() - timedelta(days=count)
    
    data_points = []
    for i in range(count):
        base_price = 100.0 + (i * 0.5)
        data_points.append({
            'time': start_time + timedelta(hours=i*6),
            'open': Decimal(str(base_price)),
            'high': Decimal(str(base_price + 5.0)),
            'low': Decimal(str(base_price - 5.0)),
            'close': Decimal(str(base_price + 2.0)),
            'volume': 1000000 + (i * 10000)
        })
    
    return data_points


def get_sample_forex_rates(count=10, start_time=None):
    """Get sample forex rate data points."""
    if start_time is None:
        start_time = datetime.now() - timedelta(days=count)
    
    data_points = []
    base_rate = 1.10
    for i in range(count):
        data_points.append({
            'time': start_time + timedelta(hours=i*6),
            'rate': Decimal(str(base_rate + (i * 0.001)))
        })
    
    return data_points


def get_sample_bond_rates(count=10, start_time=None):
    """Get sample bond rate data points."""
    if start_time is None:
        start_time = datetime.now() - timedelta(days=count)
    
    data_points = []
    base_rate = 2.5
    for i in range(count):
        data_points.append({
            'time': start_time + timedelta(hours=i*6),
            'rate': Decimal(str(base_rate + (i * 0.01)))
        })
    
    return data_points


def get_sample_economic_data(count=10, start_time=None):
    """Get sample economic data points."""
    if start_time is None:
        start_time = datetime.now() - timedelta(days=count)
    
    data_points = []
    base_value = 100.0
    for i in range(count):
        data_points.append({
            'time': start_time + timedelta(hours=i*6),
            'value': Decimal(str(base_value + (i * 0.5)))
        })
    
    return data_points


def get_sample_collection_log_entry():
    """Get sample data collection log entry."""
    return {
        'collector_type': 'StockCollector',
        'start_date': datetime.now() - timedelta(days=1),
        'end_date': datetime.now(),
        'records_collected': 100,
        'status': 'success',
        'execution_time_ms': 5000
    }

