#!/usr/bin/env python3
"""Check TimescaleDB information view columns."""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='investment_platform',
    user='postgres',
    password='postgres'
)

cur = conn.cursor()

# Check hypertables view columns
print("Hypertables view columns:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'timescaledb_information' 
    AND table_name = 'hypertables'
    ORDER BY ordinal_position;
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\nJobs view columns:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'timescaledb_information' 
    AND table_name = 'jobs'
    ORDER BY ordinal_position;
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}")

print("\nSample hypertable data:")
cur.execute("""
    SELECT * FROM timescaledb_information.hypertables 
    WHERE hypertable_name = 'market_data'
    LIMIT 1;
""")
if cur.description:
    print("Columns:", [desc[0] for desc in cur.description])
    row = cur.fetchone()
    if row:
        print("Sample row:", dict(zip([desc[0] for desc in cur.description], row)))

conn.close()

