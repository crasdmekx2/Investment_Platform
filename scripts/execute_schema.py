#!/usr/bin/env python3
"""
Script to execute database schema SQL files in the correct order.

This script executes the SQL initialization files to set up the complete
database schema including tables, indexes, hypertables, functions, triggers,
and TimescaleDB policies.
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'investment_platform'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# SQL files in execution order
SQL_FILES = [
    '01-init-timescaledb.sql',
    '02-create-schema.sql',
    '04-create-functions.sql',
    '03-create-policies.sql'
]


def read_sql_file(file_path: Path) -> str:
    """Read SQL file content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"✗ Error: SQL file not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error reading SQL file {file_path}: {e}")
        sys.exit(1)


def execute_sql_file(conn, file_path: Path, file_name: str):
    """Execute a SQL file."""
    print(f"\n{'='*60}")
    print(f"Executing: {file_name}")
    print(f"{'='*60}")
    
    sql_content = read_sql_file(file_path)
    
    cursor = conn.cursor()
    errors = []
    
    # Split SQL into statements by semicolons, but handle functions and dollar quotes
    # Simple approach: split on ';' that's at end of line and not in quotes
    statements = []
    current = []
    in_dollar_quote = False
    dollar_tag = None
    
    for line in sql_content.split('\n'):
        stripped = line.strip()
        
        # Skip empty lines and comments
        if not stripped or stripped.startswith('--'):
            continue
        
        # Track dollar-quoted strings (used in functions)
        import re
        # Find all dollar quote tags in the line
        dollar_matches = list(re.finditer(r'\$[^$]*\$', line))
        
        for match in dollar_matches:
            tag = match.group(0)
            if not in_dollar_quote:
                # Entering a dollar quote
                dollar_tag = tag
                in_dollar_quote = True
            elif tag == dollar_tag:
                # Exiting the dollar quote (same tag)
                in_dollar_quote = False
                dollar_tag = None
        
        current.append(line)
        
        # End of statement: semicolon at end of line, not in dollar quote
        if (not in_dollar_quote and stripped.endswith(';')):
            stmt = '\n'.join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
    
    # Add remaining statement
    if current:
        stmt = '\n'.join(current).strip()
        if stmt and not stmt.startswith('--'):
            statements.append(stmt)
    
    # Execute each statement
    for i, statement in enumerate(statements, 1):
        statement = statement.strip()
        if not statement:
            continue
        
        try:
            cursor.execute(statement)
            conn.commit()
        except psycopg2.Error as e:
            # Some errors are expected and can be ignored
            error_str = str(e).lower()
            
            # Ignore "already exists" errors for CREATE IF NOT EXISTS
            if 'already exists' in error_str and ('if not exists' in statement.lower() or 'create or replace' in statement.lower()):
                continue
            
            # Ignore "does not exist" errors for DROP IF EXISTS
            if 'does not exist' in error_str and 'if exists' in statement.lower():
                continue
            
            error_msg = f"Error in statement {i}: {str(e)}"
            errors.append(error_msg)
            conn.rollback()
    
    cursor.close()
    
    if errors:
        print(f"\n[WARN] Completed with {len(errors)} error(s)")
        if len(errors) <= 5:
            for err in errors:
                print(f"  - {err}")
        else:
            print(f"  (showing first 5 of {len(errors)} errors)")
            for err in errors[:5]:
                print(f"  - {err}")
        return False
    else:
        print(f"[OK] Successfully executed {file_name}")
        return True


def main():
    """Main execution function."""
    print("="*60)
    print("Database Schema Execution")
    print("="*60)
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    init_db_dir = project_root / 'init-db'
    
    if not init_db_dir.exists():
        print(f"✗ Error: init-db directory not found: {init_db_dir}")
        sys.exit(1)
    
    # Connect to database
    try:
        print("\nConnecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print("[OK] Connected to database")
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Connection failed: {e}")
        print("\nMake sure the database container is running:")
        print("  docker-compose up -d")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        sys.exit(1)
    
    # Execute SQL files in order
    success_count = 0
    failed_files = []
    
    for sql_file in SQL_FILES:
        file_path = init_db_dir / sql_file
        
        if not file_path.exists():
            print(f"✗ Error: SQL file not found: {file_path}")
            failed_files.append(sql_file)
            continue
        
        success = execute_sql_file(conn, file_path, sql_file)
        if success:
            success_count += 1
        else:
            failed_files.append(sql_file)
    
    # Close connection
    conn.close()
    
    # Summary
    print("\n" + "="*60)
    print("Execution Summary")
    print("="*60)
    print(f"Files executed successfully: {success_count}/{len(SQL_FILES)}")
    
    if failed_files:
        print(f"\n[WARN] Files with errors: {', '.join(failed_files)}")
        print("\nReview the errors above and fix any issues.")
        sys.exit(1)
    else:
        print("\n[OK] All SQL files executed successfully!")
        print("\nNext steps:")
        print("  1. Run schema verification tests: pytest tests/test_schema_verification.py")
        print("  2. Run all database tests: pytest tests/ -v")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

