#!/usr/bin/env python3
"""Check TimescaleDB details for chunk interval and compression."""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='investment_platform',
    user='postgres',
    password='postgres'
)

cur = conn.cursor()

print("Dimensions view columns:")
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'timescaledb_information' 
    AND table_name = 'dimensions'
    ORDER BY ordinal_position;
""")
for row in cur.fetchall():
    print(f"  {row[0]}")

print("\nDimensions for market_data:")
cur.execute("""
    SELECT * FROM timescaledb_information.dimensions 
    WHERE hypertable_name = 'market_data';
""")
if cur.description:
    cols = [desc[0] for desc in cur.description]
    print("Columns:", cols)
    row = cur.fetchone()
    if row:
        print("Data:", dict(zip(cols, row)))

print("\nCompression settings from pg_class:")
cur.execute("""
    SELECT reloptions 
    FROM pg_class 
    WHERE relname = 'market_data';
""")
relopts = cur.fetchone()
print("Rel options:", relopts)

print("\nJobs with compression policies:")
cur.execute("""
    SELECT job_id, hypertable_name, config 
    FROM timescaledb_information.jobs 
    WHERE proc_name = 'policy_compression';
""")
for row in cur.fetchall():
    print(f"  Job {row[0]}: {row[1]}, config: {row[2]}")

conn.close()

