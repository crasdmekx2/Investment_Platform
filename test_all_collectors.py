#!/usr/bin/env python3
"""
Comprehensive test suite for all data collectors.
Tests each collector with different instruments, timeframes, and resolutions.
"""

import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

# Add src to path
sys.path.insert(0, 'src')

from investment_platform.collectors.stock_collector import StockCollector
from investment_platform.collectors.crypto_collector import CryptoCollector
from investment_platform.collectors.forex_collector import ForexCollector
from investment_platform.collectors.bond_collector import BondCollector
from investment_platform.collectors.commodity_collector import CommodityCollector
from investment_platform.collectors.economic_collector import EconomicCollector


class CollectorTestResult:
    """Result of a single collector test."""
    def __init__(self, collector_name: str, test_name: str, success: bool, 
                 elapsed: float, records: int = 0, error: str = ""):
        self.collector_name = collector_name
        self.test_name = test_name
        self.success = success
        self.elapsed = elapsed
        self.records = records
        self.error = error


def test_stock_collector() -> List[CollectorTestResult]:
    """Test StockCollector with various scenarios."""
    results = []
    collector = StockCollector()
    
    # Test scenarios
    test_cases = [
        {
            "name": "AAPL - 1 day range - 1d interval",
            "symbol": "AAPL",
            "start_date": datetime.now(timezone.utc) - timedelta(days=5),
            "end_date": datetime.now(timezone.utc) - timedelta(days=1),
            "interval": "1d",
        },
        {
            "name": "MSFT - 7 day range - 1d interval",
            "symbol": "MSFT",
            "start_date": datetime.now(timezone.utc) - timedelta(days=10),
            "end_date": datetime.now(timezone.utc) - timedelta(days=3),
            "interval": "1d",
        },
        {
            "name": "GOOGL - 30 day range - 1d interval",
            "symbol": "GOOGL",
            "start_date": datetime.now(timezone.utc) - timedelta(days=35),
            "end_date": datetime.now(timezone.utc) - timedelta(days=5),
            "interval": "1d",
        },
    ]
    
    for test_case in test_cases:
        start_time = time.time()
        try:
            result = collector.collect_historical_data(
                symbol=test_case["symbol"],
                start_date=test_case["start_date"],
                end_date=test_case["end_date"],
                interval=test_case["interval"],
            )
            elapsed = time.time() - start_time
            
            # Check if we got data
            if hasattr(result, 'empty'):
                records = len(result) if not result.empty else 0
                success = not result.empty and records > 0
            elif isinstance(result, dict) and 'data' in result:
                data = result['data']
                records = len(data) if hasattr(data, '__len__') else 0
                success = records > 0
            else:
                records = 0
                success = False
            
            results.append(CollectorTestResult(
                "StockCollector",
                test_case["name"],
                success,
                elapsed,
                records,
                "" if success else "No data returned"
            ))
        except Exception as e:
            elapsed = time.time() - start_time
            results.append(CollectorTestResult(
                "StockCollector",
                test_case["name"],
                False,
                elapsed,
                0,
                str(e)
            ))
    
    return results


def test_crypto_collector() -> List[CollectorTestResult]:
    """Test CryptoCollector with various scenarios."""
    results = []
    collector = CryptoCollector()
    
    test_cases = [
        {
            "name": "BTC-USD - 1 day range - ONE_DAY",
            "symbol": "BTC-USD",
            "start_date": datetime.now(timezone.utc) - timedelta(days=5),
            "end_date": datetime.now(timezone.utc) - timedelta(days=1),
            "granularity": "ONE_DAY",
        },
        {
            "name": "ETH-USD - 7 day range - ONE_DAY",
            "symbol": "ETH-USD",
            "start_date": datetime.now(timezone.utc) - timedelta(days=10),
            "end_date": datetime.now(timezone.utc) - timedelta(days=3),
            "granularity": "ONE_DAY",
        },
    ]
    
    for test_case in test_cases:
        start_time = time.time()
        try:
            result = collector.collect_historical_data(
                symbol=test_case["symbol"],
                start_date=test_case["start_date"],
                end_date=test_case["end_date"],
                granularity=test_case["granularity"],
            )
            elapsed = time.time() - start_time
            
            if hasattr(result, 'empty'):
                records = len(result) if not result.empty else 0
                success = not result.empty and records > 0
            elif isinstance(result, dict) and 'data' in result:
                data = result['data']
                records = len(data) if hasattr(data, '__len__') else 0
                success = records > 0
            else:
                records = 0
                success = False
            
            results.append(CollectorTestResult(
                "CryptoCollector",
                test_case["name"],
                success,
                elapsed,
                records,
                "" if success else "No data returned"
            ))
        except Exception as e:
            elapsed = time.time() - start_time
            results.append(CollectorTestResult(
                "CryptoCollector",
                test_case["name"],
                False,
                elapsed,
                0,
                str(e)
            ))
    
    return results


def test_forex_collector() -> List[CollectorTestResult]:
    """Test ForexCollector with various scenarios."""
    results = []
    collector = ForexCollector()
    
    test_cases = [
        {
            "name": "USD_EUR - 1 day range",
            "symbol": "USD_EUR",
            "start_date": datetime.now(timezone.utc) - timedelta(days=1),
            "end_date": datetime.now(timezone.utc) - timedelta(days=1),
        },
        {
            "name": "USD_EUR - 7 day range",
            "symbol": "USD_EUR",
            "start_date": datetime.now(timezone.utc) - timedelta(days=10),
            "end_date": datetime.now(timezone.utc) - timedelta(days=3),
        },
        {
            "name": "GBP_USD - 1 day range",
            "symbol": "GBP_USD",
            "start_date": datetime.now(timezone.utc) - timedelta(days=1),
            "end_date": datetime.now(timezone.utc) - timedelta(days=1),
        },
    ]
    
    for test_case in test_cases:
        start_time = time.time()
        try:
            result = collector.collect_historical_data(
                symbol=test_case["symbol"],
                start_date=test_case["start_date"],
                end_date=test_case["end_date"],
            )
            elapsed = time.time() - start_time
            
            if hasattr(result, 'empty'):
                records = len(result) if not result.empty else 0
                success = not result.empty and records > 0
            elif isinstance(result, dict) and 'data' in result:
                data = result['data']
                records = len(data) if hasattr(data, '__len__') else 0
                success = records > 0
            else:
                records = 0
                success = False
            
            results.append(CollectorTestResult(
                "ForexCollector",
                test_case["name"],
                success,
                elapsed,
                records,
                "" if success else "No data returned"
            ))
        except Exception as e:
            elapsed = time.time() - start_time
            results.append(CollectorTestResult(
                "ForexCollector",
                test_case["name"],
                False,
                elapsed,
                0,
                str(e)
            ))
    
    return results


def test_bond_collector() -> List[CollectorTestResult]:
    """Test BondCollector with various scenarios."""
    results = []
    
    try:
        collector = BondCollector()
    except Exception as e:
        # If FRED API key not configured, skip tests
        return [CollectorTestResult(
            "BondCollector",
            "Initialization",
            False,
            0.0,
            0,
            f"FRED API key not configured: {e}"
        )]
    
    test_cases = [
        {
            "name": "DGS10 - 30 day range",
            "symbol": "DGS10",
            "start_date": datetime.now(timezone.utc) - timedelta(days=35),
            "end_date": datetime.now(timezone.utc) - timedelta(days=5),
        },
        {
            "name": "TREASURY_BILLS - 30 day range",
            "symbol": "TREASURY_BILLS",
            "start_date": datetime.now(timezone.utc) - timedelta(days=35),
            "end_date": datetime.now(timezone.utc) - timedelta(days=5),
        },
    ]
    
    for test_case in test_cases:
        start_time = time.time()
        try:
            result = collector.collect_historical_data(
                symbol=test_case["symbol"],
                start_date=test_case["start_date"],
                end_date=test_case["end_date"],
            )
            elapsed = time.time() - start_time
            
            if hasattr(result, 'empty'):
                records = len(result) if not result.empty else 0
                success = not result.empty and records > 0
            elif isinstance(result, dict) and 'data' in result:
                data = result['data']
                records = len(data) if hasattr(data, '__len__') else 0
                success = records > 0
            else:
                records = 0
                success = False
            
            results.append(CollectorTestResult(
                "BondCollector",
                test_case["name"],
                success,
                elapsed,
                records,
                "" if success else "No data returned"
            ))
        except Exception as e:
            elapsed = time.time() - start_time
            results.append(CollectorTestResult(
                "BondCollector",
                test_case["name"],
                False,
                elapsed,
                0,
                str(e)
            ))
    
    return results


def test_commodity_collector() -> List[CollectorTestResult]:
    """Test CommodityCollector with various scenarios."""
    results = []
    collector = CommodityCollector()
    
    test_cases = [
        {
            "name": "Gold - 7 day range",
            "symbol": "Gold",
            "start_date": datetime.now(timezone.utc) - timedelta(days=10),
            "end_date": datetime.now(timezone.utc) - timedelta(days=3),
        },
        {
            "name": "GC=F - 30 day range",
            "symbol": "GC=F",
            "start_date": datetime.now(timezone.utc) - timedelta(days=35),
            "end_date": datetime.now(timezone.utc) - timedelta(days=5),
        },
        {
            "name": "CL=F (Crude Oil) - 7 day range",
            "symbol": "CL=F",
            "start_date": datetime.now(timezone.utc) - timedelta(days=10),
            "end_date": datetime.now(timezone.utc) - timedelta(days=3),
        },
    ]
    
    for test_case in test_cases:
        start_time = time.time()
        try:
            result = collector.collect_historical_data(
                symbol=test_case["symbol"],
                start_date=test_case["start_date"],
                end_date=test_case["end_date"],
            )
            elapsed = time.time() - start_time
            
            if hasattr(result, 'empty'):
                records = len(result) if not result.empty else 0
                success = not result.empty and records > 0
            elif isinstance(result, dict) and 'data' in result:
                data = result['data']
                records = len(data) if hasattr(data, '__len__') else 0
                success = records > 0
            else:
                records = 0
                success = False
            
            results.append(CollectorTestResult(
                "CommodityCollector",
                test_case["name"],
                success,
                elapsed,
                records,
                "" if success else "No data returned"
            ))
        except Exception as e:
            elapsed = time.time() - start_time
            results.append(CollectorTestResult(
                "CommodityCollector",
                test_case["name"],
                False,
                elapsed,
                0,
                str(e)
            ))
    
    return results


def test_economic_collector() -> List[CollectorTestResult]:
    """Test EconomicCollector with various scenarios."""
    results = []
    
    try:
        collector = EconomicCollector()
    except Exception as e:
        # If FRED API key not configured, skip tests
        return [CollectorTestResult(
            "EconomicCollector",
            "Initialization",
            False,
            0.0,
            0,
            f"FRED API key not configured: {e}"
        )]
    
    test_cases = [
        {
            "name": "UNRATE - 90 day range",
            "symbol": "UNRATE",
            "start_date": datetime.now(timezone.utc) - timedelta(days=95),
            "end_date": datetime.now(timezone.utc) - timedelta(days=5),
        },
        {
            "name": "CPIAUCSL - 90 day range",
            "symbol": "CPIAUCSL",
            "start_date": datetime.now(timezone.utc) - timedelta(days=95),
            "end_date": datetime.now(timezone.utc) - timedelta(days=5),
        },
    ]
    
    for test_case in test_cases:
        start_time = time.time()
        try:
            result = collector.collect_historical_data(
                symbol=test_case["symbol"],
                start_date=test_case["start_date"],
                end_date=test_case["end_date"],
            )
            elapsed = time.time() - start_time
            
            if hasattr(result, 'empty'):
                records = len(result) if not result.empty else 0
                success = not result.empty and records > 0
            elif isinstance(result, dict) and 'data' in result:
                data = result['data']
                records = len(data) if hasattr(data, '__len__') else 0
                success = records > 0
            else:
                records = 0
                success = False
            
            results.append(CollectorTestResult(
                "EconomicCollector",
                test_case["name"],
                success,
                elapsed,
                records,
                "" if success else "No data returned"
            ))
        except Exception as e:
            elapsed = time.time() - start_time
            results.append(CollectorTestResult(
                "EconomicCollector",
                test_case["name"],
                False,
                elapsed,
                0,
                str(e)
            ))
    
    return results


def print_results(all_results: List[CollectorTestResult]):
    """Print comprehensive test results."""
    print("\n" + "="*80)
    print("COMPREHENSIVE COLLECTOR TEST RESULTS")
    print("="*80)
    
    # Group by collector
    by_collector: Dict[str, List[CollectorTestResult]] = {}
    for result in all_results:
        if result.collector_name not in by_collector:
            by_collector[result.collector_name] = []
        by_collector[result.collector_name].append(result)
    
    # Print summary by collector
    total_tests = len(all_results)
    total_passed = sum(1 for r in all_results if r.success)
    total_failed = total_tests - total_passed
    total_time = sum(r.elapsed for r in all_results)
    
    print(f"\nOVERALL SUMMARY")
    print(f"  Total Tests: {total_tests}")
    print(f"  ✅ Passed: {total_passed}")
    print(f"  ❌ Failed: {total_failed}")
    print(f"  ⏱️  Total Time: {total_time:.2f} seconds")
    
    # Print by collector
    print(f"\n{'='*80}")
    print("RESULTS BY COLLECTOR")
    print("="*80)
    
    for collector_name in sorted(by_collector.keys()):
        results = by_collector[collector_name]
        passed = sum(1 for r in results if r.success)
        failed = len(results) - passed
        collector_time = sum(r.elapsed for r in results)
        
        print(f"\n{collector_name}:")
        print(f"  Tests: {len(results)} | ✅ Passed: {passed} | ❌ Failed: {failed} | ⏱️  Time: {collector_time:.2f}s")
        
        for result in results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            records_info = f" ({result.records} records)" if result.records > 0 else ""
            error_info = f" - {result.error}" if result.error else ""
            print(f"    {status} - {result.test_name}{records_info} - {result.elapsed:.2f}s{error_info}")
    
    # Print failures summary
    failures = [r for r in all_results if not r.success]
    if failures:
        print(f"\n{'='*80}")
        print("FAILED TESTS SUMMARY")
        print("="*80)
        for result in failures:
            print(f"  ❌ {result.collector_name} - {result.test_name}")
            print(f"     Error: {result.error}")
            print(f"     Time: {result.elapsed:.2f}s")
    
    return total_failed == 0


def main():
    """Run all collector tests."""
    print("\n" + "="*80)
    print("ALL COLLECTORS COMPREHENSIVE TEST")
    print("="*80)
    print("Testing all data collectors with various instruments, timeframes, and resolutions")
    print(f"Start Time: {datetime.now().isoformat()}")
    
    all_results = []
    
    # Test each collector
    print("\n" + "="*80)
    print("Testing StockCollector...")
    print("="*80)
    all_results.extend(test_stock_collector())
    
    print("\n" + "="*80)
    print("Testing CryptoCollector...")
    print("="*80)
    all_results.extend(test_crypto_collector())
    
    print("\n" + "="*80)
    print("Testing ForexCollector...")
    print("="*80)
    all_results.extend(test_forex_collector())
    
    print("\n" + "="*80)
    print("Testing BondCollector...")
    print("="*80)
    all_results.extend(test_bond_collector())
    
    print("\n" + "="*80)
    print("Testing CommodityCollector...")
    print("="*80)
    all_results.extend(test_commodity_collector())
    
    print("\n" + "="*80)
    print("Testing EconomicCollector...")
    print("="*80)
    all_results.extend(test_economic_collector())
    
    # Print comprehensive results
    success = print_results(all_results)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

