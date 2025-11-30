#!/usr/bin/env python3
"""Execute functions SQL file with proper dollar quote handling."""

import psycopg2
from pathlib import Path
import re

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='investment_platform',
    user='postgres',
    password='postgres'
)

cur = conn.cursor()

sql_file = Path('init-db/04-create-functions.sql')
sql_content = sql_file.read_text(encoding='utf-8')

# Split SQL into statements, properly handling dollar quotes
statements = []
current = []
in_dollar_quote = False
dollar_tag = None

for line in sql_content.split('\n'):
    stripped = line.strip()
    
    # Skip empty lines and comments
    if not stripped or stripped.startswith('--'):
        continue
    
    # Track dollar quotes - toggle state when we see the tag
    dollar_matches = list(re.finditer(r'\$[^$]*\$', line))
    for match in dollar_matches:
        tag = match.group(0)
        if not in_dollar_quote:
            # Entering dollar quote
            dollar_tag = tag
            in_dollar_quote = True
        elif tag == dollar_tag:
            # Exiting dollar quote (same tag)
            in_dollar_quote = False
            dollar_tag = None
    
    current.append(line)
    
    # End of statement: semicolon at end, not in dollar quote
    if (not in_dollar_quote and stripped.endswith(';')):
        stmt = '\n'.join(current).strip()
        if stmt:
            statements.append(stmt)
        current = []

# Add remaining
if current:
    stmt = '\n'.join(current).strip()
    if stmt and not stmt.startswith('--'):
        statements.append(stmt)

print(f"Found {len(statements)} statements")
print("\nFirst 3 statements:")
for i, stmt in enumerate(statements[:3], 1):
    print(f"\n--- Statement {i} (first 200 chars) ---")
    print(stmt[:200])

# Execute each statement
errors = []
for i, statement in enumerate(statements, 1):
    statement = statement.strip()
    if not statement:
        continue
    
    try:
        cur.execute(statement)
        conn.commit()
    except psycopg2.Error as e:
        error_str = str(e).lower()
        # Ignore "already exists" errors
        if 'already exists' in error_str and ('if not exists' in statement.lower() or 'create or replace' in statement.lower()):
            continue
        # Ignore "does not exist" errors for DROP IF EXISTS
        if 'does not exist' in error_str and 'if exists' in statement.lower():
            continue
        
        print(f"Error in statement {i}: {str(e)}")
        errors.append((i, str(e)))
        conn.rollback()

if errors:
    print(f"\nCompleted with {len(errors)} error(s)")
else:
    print("\n[OK] All statements executed successfully!")

# Verify functions were created
cur.execute("""
    SELECT proname 
    FROM pg_proc 
    WHERE proname IN ('update_updated_at_column', 'get_asset_by_symbol', 'get_latest_market_data', 'check_data_freshness', 'get_collection_stats')
    ORDER BY proname;
""")
functions = cur.fetchall()
print(f"\nFunctions found: {len(functions)}")
for func in functions:
    print(f"  - {func[0]}")

cur.close()
conn.close()

