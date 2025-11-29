#!/usr/bin/env python3
"""
Script to test all data collectors by pulling sample data.
"""

import sys
from datetime import datetime, timedelta
from typing import Dict, Any

# Import all collectors
from investment_platform.collectors import (
    StockCollector,
    ForexCollector,
    CryptoCollector,
    BondCollector,
    CommodityCollector,
    EconomicCollector,
    APIError,
    ConfigurationError,
    DataCollectionError,
    ValidationError,
)


def test_collector(
    collector_name: str,
    collector_class: Any,
    symbol: str,
    init_kwargs: Dict[str, Any] = None,
    collect_kwargs: Dict[str, Any] = None,
) -> bool:
    """
    Test a collector by initializing it and pulling sample data.
    
    Args:
        collector_name: Name of the collector for display
        collector_class: Collector class to test
        symbol: Symbol to test with
        init_kwargs: Optional kwargs for collector initialization
        collect_kwargs: Optional kwargs for collect_historical_data
        
    Returns:
        True if test passed, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Testing {collector_name}")
    print(f"{'='*60}")
    
    if init_kwargs is None:
        init_kwargs = {}
    if collect_kwargs is None:
        collect_kwargs = {}
    
    try:
        # Initialize collector
        print(f"Initializing {collector_name}...")
        collector = collector_class(**init_kwargs)
        print("✓ Collector initialized successfully")
        
        # Test get_asset_info
        print(f"\nTesting get_asset_info() with symbol: {symbol}")
        try:
            asset_info = collector.get_asset_info(symbol)
            print("✓ get_asset_info() succeeded")
            print(f"  Asset info keys: {list(asset_info.keys())}")
            if 'name' in asset_info:
                print(f"  Name: {asset_info['name']}")
            elif 'title' in asset_info:
                print(f"  Title: {asset_info['title']}")
        except Exception as e:
            print(f"✗ get_asset_info() failed: {e}")
            return False
        
        # Test collect_historical_data
        print(f"\nTesting collect_historical_data() with symbol: {symbol}")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"  Date range: {start_date.date()} to {end_date.date()}")
        
        try:
            data = collector.collect_historical_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                **collect_kwargs
            )
            
            # Check if data was actually collected
            record_count = 0
            if isinstance(data, list):
                record_count = len(data)
                print(f"✓ collect_historical_data() succeeded")
                print(f"  Records collected: {record_count}")
                if record_count > 0:
                    print(f"  Sample record keys: {list(data[0].keys())}")
            elif hasattr(data, '__len__'):
                record_count = len(data)
                print(f"✓ collect_historical_data() succeeded")
                print(f"  Records collected: {record_count}")
                if hasattr(data, 'columns'):
                    print(f"  Columns: {list(data.columns)}")
            else:
                print(f"✓ collect_historical_data() succeeded")
                print(f"  Data type: {type(data)}")
                # For dict or other types, try to determine if it's empty
                if isinstance(data, dict):
                    record_count = 1 if data else 0
            
            # Validate that records were actually collected
            if record_count == 0:
                print(f"✗ No data returned - test FAILED")
                print(f"  Expected at least 1 record, but got 0")
                return False
            
            print(f"\n✓ {collector_name} test PASSED")
            return True
            
        except Exception as e:
            print(f"✗ collect_historical_data() failed: {e}")
            print(f"  Error type: {type(e).__name__}")
            return False
            
    except ConfigurationError as e:
        print(f"✗ Configuration error: {e}")
        print(f"  This collector requires API keys or configuration.")
        print(f"  Check your .env file or environment variables.")
        return False
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print(f"  Required library may not be installed.")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        print(f"  Error type: {type(e).__name__}")
        return False


def main():
    """Run tests for all collectors."""
    print("="*60)
    print("Data Collector Test Suite")
    print("="*60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test StockCollector
    results['StockCollector'] = test_collector(
        "StockCollector",
        StockCollector,
        "AAPL"
    )
    
    # Test ForexCollector
    results['ForexCollector'] = test_collector(
        "ForexCollector",
        ForexCollector,
        "USD_EUR"
    )
    
    # Test CryptoCollector
    results['CryptoCollector'] = test_collector(
        "CryptoCollector",
        CryptoCollector,
        "BTC-USD",
        collect_kwargs={"granularity": "ONE_DAY"}
    )
    
    # Test BondCollector
    results['BondCollector'] = test_collector(
        "BondCollector",
        BondCollector,
        "TBILLS"
    )
    
    # Test CommodityCollector
    results['CommodityCollector'] = test_collector(
        "CommodityCollector",
        CommodityCollector,
        "Gold"
    )
    
    # Test EconomicCollector (using DGS10 - 10-Year Treasury Rate, daily data)
    results['EconomicCollector'] = test_collector(
        "EconomicCollector",
        EconomicCollector,
        "DGS10"
    )
    
    # Print summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for collector_name, success in results.items():
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{collector_name:25s} {status}")
    
    print(f"\nTotal: {passed}/{total} collectors passed")
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()

