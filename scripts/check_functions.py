#!/usr/bin/env python3
"""Check if functions exist."""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='investment_platform',
    user='postgres',
    password='postgres'
)

cur = conn.cursor()
cur.execute("""
    SELECT proname, pronargs 
    FROM pg_proc 
    WHERE proname IN ('update_updated_at_column', 'get_asset_by_symbol', 'get_latest_market_data', 'check_data_freshness', 'get_collection_stats')
    ORDER BY proname;
""")

functions = cur.fetchall()
print("Functions found:")
for func in functions:
    print(f"  - {func[0]} (args: {func[1]})")

if not functions:
    print("  No functions found!")

conn.close()

