#!/usr/bin/env python3
"""Test function creation."""

import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='investment_platform',
    user='postgres',
    password='postgres'
)

cur = conn.cursor()

# Test creating a simple function
sql = """
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

try:
    cur.execute(sql)
    conn.commit()
    print("[OK] Function created successfully")
    
    # Check if it exists
    cur.execute("SELECT proname FROM pg_proc WHERE proname = 'update_updated_at_column';")
    result = cur.fetchone()
    if result:
        print(f"[OK] Function exists: {result[0]}")
    else:
        print("[ERROR] Function not found in pg_proc")
except Exception as e:
    print(f"[ERROR] Failed to create function: {e}")
    conn.rollback()

conn.close()

