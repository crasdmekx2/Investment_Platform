#!/usr/bin/env python3
"""
Direct test of ForexCollector to diagnose issues.
Bypasses API and scheduler to test the collector directly.
"""

import sys
import time
from datetime import datetime, timedelta, timezone

# Add src to path
sys.path.insert(0, 'src')

from investment_platform.collectors.forex_collector import ForexCollector


def test_get_asset_info():
    """Test getting asset info for a currency pair."""
    print("\n" + "="*80)
    print("TEST 1: Get Asset Info")
    print("="*80)
    
    collector = ForexCollector()
    start_time = time.time()
    
    try:
        asset_info = collector.get_asset_info("USD_EUR")
        elapsed = time.time() - start_time
        
        if asset_info and 'current_rate' in asset_info:
            print(f"✅ Success: Asset info retrieved")
            print(f"   Symbol: {asset_info.get('symbol')}")
            print(f"   Base: {asset_info.get('base_currency')}")
            print(f"   Quote: {asset_info.get('quote_currency')}")
            print(f"   Current Rate: {asset_info.get('current_rate')}")
            print(f"⏱️  Time: {elapsed:.2f} seconds")
            return True, elapsed
        else:
            print(f"❌ Failed: Invalid asset info returned")
            print(f"⏱️  Time: {elapsed:.2f} seconds")
            return False, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Failed: {e}")
        print(f"⏱️  Time: {elapsed:.2f} seconds")
        import traceback
        traceback.print_exc()
        return False, elapsed


def test_historical_single_day():
    """Test getting historical rate for a single day."""
    print("\n" + "="*80)
    print("TEST 2: Get Historical Rate for Single Day")
    print("="*80)
    
    collector = ForexCollector()
    test_date = datetime.now(timezone.utc) - timedelta(days=1)
    start_time = time.time()
    
    try:
        result = collector.collect_historical_data(
            symbol="USD_EUR",
            start_date=test_date,
            end_date=test_date
        )
        elapsed = time.time() - start_time
        
        if hasattr(result, 'empty') and not result.empty:
            print(f"✅ Success: Collected {len(result)} record(s)")
            print(f"⏱️  Time: {elapsed:.2f} seconds")
            print(f"📊 Data:\n{result.head()}")
            return True, elapsed
        elif isinstance(result, dict) and result.get('data'):
            data = result['data']
            if hasattr(data, '__len__') and len(data) > 0:
                print(f"✅ Success: Collected {len(data)} record(s)")
            else:
                print(f"✅ Success: Collected data")
            print(f"⏱️  Time: {elapsed:.2f} seconds")
            print(f"📊 Data: {result}")
            return True, elapsed
        else:
            print(f"⚠️  No data returned (empty result)")
            print(f"⏱️  Time: {elapsed:.2f} seconds")
            print(f"📊 Result: {result}")
            return False, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Failed: {e}")
        print(f"⏱️  Time: {elapsed:.2f} seconds")
        import traceback
        traceback.print_exc()
        return False, elapsed


def test_collect_historical_same_day():
    """Test collect_historical_data with same day (should use current rate with timeout)."""
    print("\n" + "="*80)
    print("TEST 3: collect_historical_data - Same Day (Current Rate with 5s Timeout)")
    print("="*80)
    
    collector = ForexCollector()
    end_date = datetime.now(timezone.utc)
    start_date = end_date  # Same day
    
    start_time = time.time()
    
    try:
        result = collector.collect_historical_data(
            symbol="USD_EUR",
            start_date=start_date,
            end_date=end_date
        )
        elapsed = time.time() - start_time
        
        # Check if we got data or empty result (both are valid - empty means API not ready)
        if hasattr(result, 'empty'):
            if not result.empty:
                print(f"✅ Success: Collected {len(result)} record(s)")
                print(f"⏱️  Time: {elapsed:.2f} seconds")
                print(f"📊 Data:\n{result.head()}")
                return True, elapsed
            else:
                print(f"⚠️  Empty result (yfinance may not have data for this date)")
                print(f"⏱️  Time: {elapsed:.2f} seconds")
                return False, elapsed
        elif isinstance(result, dict) and result.get('data'):
            data = result['data']
            if hasattr(data, '__len__') and len(data) > 0:
                print(f"✅ Success: Collected {len(data)} record(s)")
                print(f"⏱️  Time: {elapsed:.2f} seconds")
                print(f"📊 Data: {result}")
                return True, elapsed
            else:
                print(f"⚠️  Empty result (yfinance may not have data for this date)")
                print(f"⏱️  Time: {elapsed:.2f} seconds")
                return False, elapsed
        else:
            print(f"⚠️  No data returned (empty result)")
            print(f"⏱️  Time: {elapsed:.2f} seconds")
            return False, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Failed: {e}")
        print(f"⏱️  Time: {elapsed:.2f} seconds")
        import traceback
        traceback.print_exc()
        return False, elapsed


def test_collect_historical_1_day_range():
    """Test collect_historical_data with 1 day range."""
    print("\n" + "="*80)
    print("TEST 4: collect_historical_data - 1 Day Range")
    print("="*80)
    
    collector = ForexCollector()
    end_date = datetime.now(timezone.utc) - timedelta(days=1)
    start_date = end_date  # Same day = 1 day range
    
    start_time = time.time()
    
    try:
        result = collector.collect_historical_data(
            symbol="USD_EUR",
            start_date=start_date,
            end_date=end_date
        )
        elapsed = time.time() - start_time
        
        if hasattr(result, 'empty') and not result.empty:
            print(f"✅ Success: Collected {len(result)} record(s)")
            print(f"⏱️  Time: {elapsed:.2f} seconds")
            print(f"📊 Data:\n{result.head()}")
            return True, elapsed
        elif isinstance(result, dict) and result.get('data'):
            data = result['data']
            if hasattr(data, '__len__'):
                print(f"✅ Success: Collected {len(data)} record(s)")
            else:
                print(f"✅ Success: Collected data")
            print(f"⏱️  Time: {elapsed:.2f} seconds")
            print(f"📊 Data: {result}")
            return True, elapsed
        else:
            print(f"⚠️  No data returned (empty result)")
            print(f"⏱️  Time: {elapsed:.2f} seconds")
            print(f"📊 Result: {result}")
            return False, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Failed: {e}")
        print(f"⏱️  Time: {elapsed:.2f} seconds")
        import traceback
        traceback.print_exc()
        return False, elapsed


def test_collect_historical_3_days():
    """Test collect_historical_data with 3 day range."""
    print("\n" + "="*80)
    print("TEST 5: collect_historical_data - 3 Day Range")
    print("="*80)
    
    collector = ForexCollector()
    end_date = datetime.now(timezone.utc) - timedelta(days=1)
    start_date = end_date - timedelta(days=2)  # 3 days total
    
    start_time = time.time()
    
    try:
        result = collector.collect_historical_data(
            symbol="USD_EUR",
            start_date=start_date,
            end_date=end_date
        )
        elapsed = time.time() - start_time
        
        if hasattr(result, 'empty') and not result.empty:
            print(f"✅ Success: Collected {len(result)} record(s)")
            print(f"⏱️  Time: {elapsed:.2f} seconds")
            print(f"📊 Data:\n{result.head()}")
            return True, elapsed
        elif isinstance(result, dict) and result.get('data'):
            data = result['data']
            if hasattr(data, '__len__'):
                print(f"✅ Success: Collected {len(data)} record(s)")
            else:
                print(f"✅ Success: Collected data")
            print(f"⏱️  Time: {elapsed:.2f} seconds")
            print(f"📊 Data: {result}")
            return True, elapsed
        else:
            print(f"⚠️  No data returned (empty result)")
            print(f"⏱️  Time: {elapsed:.2f} seconds")
            print(f"📊 Result: {result}")
            return False, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Failed: {e}")
        print(f"⏱️  Time: {elapsed:.2f} seconds")
        import traceback
        traceback.print_exc()
        return False, elapsed


def main():
    """Run all tests, stopping on first failure."""
    print("\n" + "="*80)
    print("FOREX COLLECTOR DIRECT TEST")
    print("="*80)
    print("Testing ForexCollector directly (bypassing API)")
    print("Mode: Stop on first failure")
    print(f"Start Time: {datetime.now().isoformat()}")
    
    results = []
    
    # Test 1: Get asset info
    print("\n▶️  Running Test 1...")
    success, elapsed = test_get_asset_info()
    results.append(("Get Asset Info", success, elapsed))
    if not success:
        print("\n⚠️  Stopping tests after first failure: Get Asset Info")
        return print_summary(results)
    
    # Test 2: Historical single day
    print("\n▶️  Running Test 2...")
    success, elapsed = test_historical_single_day()
    results.append(("Historical Single Day", success, elapsed))
    if not success:
        print("\n⚠️  Stopping tests after first failure: Historical Single Day")
        return print_summary(results)
    
    # Test 3: collect_historical_data same day
    print("\n▶️  Running Test 3...")
    success, elapsed = test_collect_historical_same_day()
    results.append(("collect_historical_data (same day)", success, elapsed))
    if not success:
        print("\n⚠️  Stopping tests after first failure: collect_historical_data (same day)")
        return print_summary(results)
    
    # Test 4: collect_historical_data 1 day range
    print("\n▶️  Running Test 4...")
    success, elapsed = test_collect_historical_1_day_range()
    results.append(("collect_historical_data (1 day)", success, elapsed))
    if not success:
        print("\n⚠️  Stopping tests after first failure: collect_historical_data (1 day)")
        return print_summary(results)
    
    # Test 5: collect_historical_data 3 days
    print("\n▶️  Running Test 5...")
    success, elapsed = test_collect_historical_3_days()
    results.append(("collect_historical_data (3 days)", success, elapsed))
    if not success:
        print("\n⚠️  Stopping tests after first failure: collect_historical_data (3 days)")
        return print_summary(results)
    
    # All tests passed
    return print_summary(results)


def print_summary(results):
    """Print test summary."""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total = len(results)
    passed = sum(1 for _, success, _ in results if success)
    failed = total - passed
    total_time = sum(elapsed for _, _, elapsed in results)
    
    print(f"Total Tests Run: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total Time: {total_time:.2f} seconds")
    
    if results:
        print("\nDetailed Results:")
        for name, success, elapsed in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} - {name}: {elapsed:.2f}s")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

