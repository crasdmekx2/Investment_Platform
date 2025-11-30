#!/usr/bin/env python3
"""Quick script to check if tables exist."""

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
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name;
""")

tables = [row[0] for row in cur.fetchall()]
print("Existing tables:")
for table in tables:
    print(f"  - {table}")

conn.close()

