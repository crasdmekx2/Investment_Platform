"""
Database helper utilities for testing.
"""

import psycopg2
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta


def execute_query(cursor, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
    """
    Execute a query and return results as a list of dictionaries.
    
    Args:
        cursor: Database cursor
        query: SQL query string
        params: Optional query parameters
        
    Returns:
        List of dictionaries representing rows
    """
    cursor.execute(query, params)
    
    if cursor.description:
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    else:
        return []


def table_exists(cursor, table_name: str, schema: str = 'public') -> bool:
    """
    Check if a table exists.
    
    Args:
        cursor: Database cursor
        table_name: Name of the table
        schema: Schema name (default: public)
        
    Returns:
        True if table exists, False otherwise
    """
    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = %s 
            AND table_name = %s
        );
    """
    cursor.execute(query, (schema, table_name))
    return cursor.fetchone()[0]


def index_exists(cursor, index_name: str, schema: str = 'public') -> bool:
    """
    Check if an index exists.
    
    Args:
        cursor: Database cursor
        index_name: Name of the index
        schema: Schema name (default: public)
        
    Returns:
        True if index exists, False otherwise
    """
    query = """
        SELECT EXISTS (
            SELECT FROM pg_indexes 
            WHERE schemaname = %s 
            AND indexname = %s
        );
    """
    cursor.execute(query, (schema, index_name))
    return cursor.fetchone()[0]


def function_exists(cursor, function_name: str, schema: str = 'public') -> bool:
    """
    Check if a function exists.
    
    Args:
        cursor: Database cursor
        function_name: Name of the function
        schema: Schema name (default: public)
        
    Returns:
        True if function exists, False otherwise
    """
    query = """
        SELECT EXISTS (
            SELECT FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = %s 
            AND p.proname = %s
        );
    """
    cursor.execute(query, (schema, function_name))
    return cursor.fetchone()[0]


def trigger_exists(cursor, trigger_name: str, table_name: str, schema: str = 'public') -> bool:
    """
    Check if a trigger exists on a table.
    
    Args:
        cursor: Database cursor
        trigger_name: Name of the trigger
        table_name: Name of the table
        schema: Schema name (default: public)
        
    Returns:
        True if trigger exists, False otherwise
    """
    query = """
        SELECT EXISTS (
            SELECT FROM pg_trigger t
            JOIN pg_class c ON t.tgrelid = c.oid
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = %s 
            AND c.relname = %s
            AND t.tgname = %s
        );
    """
    cursor.execute(query, (schema, table_name, trigger_name))
    return cursor.fetchone()[0]


def constraint_exists(cursor, constraint_name: str, schema: str = 'public') -> bool:
    """
    Check if a constraint exists.
    
    Args:
        cursor: Database cursor
        constraint_name: Name of the constraint
        schema: Schema name (default: public)
        
    Returns:
        True if constraint exists, False otherwise
    """
    query = """
        SELECT EXISTS (
            SELECT FROM information_schema.table_constraints 
            WHERE constraint_schema = %s 
            AND constraint_name = %s
        );
    """
    cursor.execute(query, (schema, constraint_name))
    return cursor.fetchone()[0]


def is_hypertable(cursor, table_name: str) -> bool:
    """
    Check if a table is a TimescaleDB hypertable.
    
    Args:
        cursor: Database cursor
        table_name: Name of the table
        
    Returns:
        True if table is a hypertable, False otherwise
    """
    query = """
        SELECT EXISTS (
            SELECT FROM timescaledb_information.hypertables 
            WHERE hypertable_name = %s
        );
    """
    cursor.execute(query, (table_name,))
    return cursor.fetchone()[0]


def get_table_columns(cursor, table_name: str, schema: str = 'public') -> List[Dict[str, Any]]:
    """
    Get column information for a table.
    
    Args:
        cursor: Database cursor
        table_name: Name of the table
        schema: Schema name (default: public)
        
    Returns:
        List of dictionaries with column information
    """
    query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = %s 
        AND table_name = %s
        ORDER BY ordinal_position;
    """
    return execute_query(cursor, query, (schema, table_name))


def get_table_indexes(cursor, table_name: str, schema: str = 'public') -> List[Dict[str, Any]]:
    """
    Get index information for a table.
    
    Args:
        cursor: Database cursor
        table_name: Name of the table
        schema: Schema name (default: public)
        
    Returns:
        List of dictionaries with index information
    """
    query = """
        SELECT 
            i.indexname,
            i.indexdef
        FROM pg_indexes i
        WHERE i.schemaname = %s 
        AND i.tablename = %s;
    """
    return execute_query(cursor, query, (schema, table_name))


def get_foreign_keys(cursor, table_name: str, schema: str = 'public') -> List[Dict[str, Any]]:
    """
    Get foreign key constraints for a table.
    
    Args:
        cursor: Database cursor
        table_name: Name of the table
        schema: Schema name (default: public)
        
    Returns:
        List of dictionaries with foreign key information
    """
    query = """
        SELECT
            tc.constraint_name,
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            rc.delete_rule
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        JOIN information_schema.referential_constraints AS rc
            ON rc.constraint_name = tc.constraint_name
            AND rc.constraint_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = %s
        AND tc.table_name = %s;
    """
    return execute_query(cursor, query, (schema, table_name))


def explain_query(cursor, query: str, params: Optional[Tuple] = None) -> str:
    """
    Get query execution plan using EXPLAIN.
    
    Args:
        cursor: Database cursor
        query: SQL query string
        params: Optional query parameters
        
    Returns:
        Query plan as string
    """
    explain_query_str = f"EXPLAIN ANALYZE {query}"
    cursor.execute(explain_query_str, params)
    return '\n'.join([row[0] for row in cursor.fetchall()])


def insert_sample_asset(
    cursor,
    symbol: str,
    asset_type: str,
    name: str,
    source: str = 'Test',
    **kwargs
) -> int:
    """
    Insert a sample asset and return the asset_id.
    
    Args:
        cursor: Database cursor
        symbol: Asset symbol
        asset_type: Asset type (stock, forex, crypto, etc.)
        name: Asset name
        source: Data source
        **kwargs: Additional asset fields
        
    Returns:
        asset_id of the inserted asset
    """
    # Build insert query dynamically
    fields = ['symbol', 'asset_type', 'name', 'source']
    values = [symbol, asset_type, name, source]
    placeholders = ['%s'] * len(fields)
    
    for key, value in kwargs.items():
        fields.append(key)
        values.append(value)
        placeholders.append('%s')
    
    query = f"""
        INSERT INTO assets ({', '.join(fields)})
        VALUES ({', '.join(placeholders)})
        RETURNING asset_id;
    """
    cursor.execute(query, tuple(values))
    return cursor.fetchone()[0]

