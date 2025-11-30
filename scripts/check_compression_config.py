#!/usr/bin/env python3
"""Check compression policy config format."""

import psycopg2
import json

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='investment_platform',
    user='postgres',
    password='postgres'
)

cur = conn.cursor()

cur.execute("""
    SELECT hypertable_name, config 
    FROM timescaledb_information.jobs 
    WHERE proc_name = 'policy_compression'
    LIMIT 1;
""")

row = cur.fetchone()
if row:
    print(f"Hypertable: {row[0]}")
    print(f"Config type: {type(row[1])}")
    print(f"Config: {json.dumps(row[1], indent=2, default=str)}")
else:
    print("No compression policies found")

conn.close()

