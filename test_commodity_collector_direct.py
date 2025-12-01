"""Direct test of CommodityCollector to verify yfinance integration."""

import sys
from datetime import datetime, timedelta, timezone

from investment_platform.collectors.commodity_collector import CommodityCollector


def test_commodity_collector():
    """Test CommodityCollector with various symbols and date ranges."""
    print("=" * 80)
    print("COMMODITY COLLECTOR DIRECT TEST")
    print("=" * 80)
    print(f"Start Time: {datetime.now().isoformat()}\n")

    collector = CommodityCollector()

    # Test cases
    test_cases = [
        {
            "name": "Gold (GC=F) - 30 day range",
            "symbol": "GC=F",
            "start_date": datetime.now(timezone.utc) - timedelta(days=35),
            "end_date": datetime.now(timezone.utc) - timedelta(days=5),
        },
        {
            "name": "Crude Oil (CL=F) - 30 day range",
            "symbol": "CL=F",
            "start_date": datetime.now(timezone.utc) - timedelta(days=35),
            "end_date": datetime.now(timezone.utc) - timedelta(days=5),
        },
        {
            "name": "Silver (SI=F) - 14 day range",
            "symbol": "SI=F",
            "start_date": datetime.now(timezone.utc) - timedelta(days=17),
            "end_date": datetime.now(timezone.utc) - timedelta(days=3),
        },
        {
            "name": "Gold (name) - 30 day range",
            "symbol": "Gold",
            "start_date": datetime.now(timezone.utc) - timedelta(days=35),
            "end_date": datetime.now(timezone.utc) - timedelta(days=5),
        },
        {
            "name": "Crude Oil (name) - 14 day range",
            "symbol": "Crude Oil",
            "start_date": datetime.now(timezone.utc) - timedelta(days=17),
            "end_date": datetime.now(timezone.utc) - timedelta(days=3),
        },
    ]

    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}: {test_case['name']}")
        print(f"{'=' * 80}")
        print(f"Symbol: {test_case['symbol']}")
        print(f"Start Date: {test_case['start_date']}")
        print(f"End Date: {test_case['end_date']}")

        try:
            # Test symbol mapping
            yf_symbol = collector._get_yfinance_symbol(test_case["symbol"])
            print(f"YFinance Symbol: {yf_symbol}")

            if not yf_symbol:
                print("❌ FAILED: Could not determine yfinance symbol")
                results.append({"test": test_case["name"], "status": "FAIL", "error": "No yfinance symbol"})
                continue

            # Collect data
            print("\nCollecting data...")
            df = collector.collect_historical_data(
                symbol=test_case["symbol"],
                start_date=test_case["start_date"],
                end_date=test_case["end_date"],
            )

            if df.empty:
                print("❌ FAILED: No data returned")
                results.append({"test": test_case["name"], "status": "FAIL", "error": "Empty DataFrame"})
                continue

            print(f"✅ SUCCESS: Collected {len(df)} records")
            print(f"\nDataFrame Info:")
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {list(df.columns)}")
            print(f"  Date Range: {df.index.min()} to {df.index.max()}")
            print(f"\nFirst few rows:")
            print(df.head())
            print(f"\nLast few rows:")
            print(df.tail())

            # Verify required columns
            required_cols = ["open", "high", "low", "close"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"⚠️  WARNING: Missing columns: {missing_cols}")
            else:
                print("✅ All required columns present")

            results.append({
                "test": test_case["name"],
                "status": "PASS",
                "records": len(df),
                "columns": list(df.columns),
            })

        except Exception as e:
            print(f"❌ FAILED: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append({"test": test_case["name"], "status": "FAIL", "error": str(e)})

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = total - passed

    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed > 0:
        print("\nFailed Tests:")
        for result in results:
            if result["status"] == "FAIL":
                print(f"  - {result['test']}")
                if "error" in result:
                    print(f"    Error: {result['error']}")

    return failed == 0


if __name__ == "__main__":
    success = test_commodity_collector()
    sys.exit(0 if success else 1)

