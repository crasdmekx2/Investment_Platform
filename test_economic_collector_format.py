"""Test economic collector output format."""
import sys
sys.path.insert(0, 'src')

from investment_platform.collectors.economic_collector import EconomicCollector
from datetime import datetime, timedelta, timezone

collector = EconomicCollector()

# Test with the same date range as the test
end_date = datetime.now(timezone.utc) - timedelta(days=30)
start_date = end_date - timedelta(days=180)  # 6 months back

print(f"Testing with date range: {start_date} to {end_date}")

df = collector.collect_historical_data('UNRATE', start_date, end_date)

print(f"\nType: {type(df)}")
print(f"Columns: {list(df.columns) if hasattr(df, 'columns') else 'N/A'}")
print(f"Shape: {df.shape if hasattr(df, 'shape') else 'N/A'}")
print(f"Empty: {df.empty if hasattr(df, 'empty') else 'N/A'}")
print(f"\nHead:\n{df.head() if hasattr(df, 'head') else df}")
print(f"\nDtypes:\n{df.dtypes if hasattr(df, 'dtypes') else 'N/A'}")

