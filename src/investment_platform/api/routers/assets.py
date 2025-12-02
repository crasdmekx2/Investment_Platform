"""Assets API router."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Path
from psycopg2.extras import RealDictCursor
from psycopg2 import sql

from investment_platform.api.constants import (
    DEFAULT_PAGE_LIMIT,
    DEFAULT_PAGE_OFFSET,
    MAX_PAGE_LIMIT,
    MIN_PAGE_LIMIT,
)
from investment_platform.ingestion.db_connection import get_db_connection

router = APIRouter()

# Security: Whitelist of allowed table names and column names to prevent SQL injection
# Only these values can be used in dynamic SQL queries
ALLOWED_TABLES = {
    "market_data": {"time_column": "time"},
    "forex_rates": {"time_column": "time"},
    "bond_rates": {"time_column": "time"},
    "economic_data": {"time_column": "time"},
}

# Mapping of asset types to their corresponding table names
ASSET_TYPE_TO_TABLE = {
    "stock": "market_data",
    "crypto": "market_data",
    "commodity": "market_data",
    "forex": "forex_rates",
    "bond": "bond_rates",
    "economic_indicator": "economic_data",
}


def _get_table_and_column(asset_type: str) -> tuple[str, str]:
    """
    Get safe table name and time column name for an asset type.

    Security: Uses whitelist validation to prevent SQL injection.
    Only predefined table/column combinations are allowed.

    Args:
        asset_type: Type of asset (must be in ASSET_TYPE_TO_TABLE mapping)

    Returns:
        Tuple of (table_name, time_column_name)

    Raises:
        ValueError: If asset_type is not in the whitelist
    """
    table = ASSET_TYPE_TO_TABLE.get(asset_type)

    if table is None or table not in ALLOWED_TABLES:
        raise ValueError(f"Invalid asset type: {asset_type}")

    time_column = ALLOWED_TABLES[table]["time_column"]

    return table, time_column


@router.get(
    "",
    response_model=List[Dict[str, Any]],
    summary="List registered assets",
    description="Retrieve a paginated list of all registered assets in the system.",
    responses={
        200: {"description": "List of assets retrieved successfully"},
        500: {"description": "Internal server error"},
    },
)
async def list_assets(
    asset_type: Optional[str] = Query(
        None,
        description="Filter by asset type",
        examples=["stock", "crypto", "forex", "bond", "commodity", "economic_indicator"],
    ),
    limit: int = Query(
        DEFAULT_PAGE_LIMIT,
        ge=MIN_PAGE_LIMIT,
        le=MAX_PAGE_LIMIT,
        description="Maximum number of results",
        example=100,
    ),
    offset: int = Query(
        DEFAULT_PAGE_OFFSET, ge=0, description="Offset for pagination", example=0
    ),
) -> List[Dict[str, Any]]:
    """
    List all registered assets.
    
    Returns a paginated list of active assets. Results are ordered by creation
    date (newest first). Use the asset_type parameter to filter by specific
    asset types.
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = "SELECT * FROM assets WHERE is_active = TRUE"
            params = []

            if asset_type:
                query += " AND asset_type = %s"
                params.append(asset_type)

            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, params)
            results = cursor.fetchall()

            return [dict(row) for row in results]


@router.get("/{asset_id}", response_model=Dict[str, Any])
async def get_asset(asset_id: int) -> Dict[str, Any]:
    """Get asset details."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM assets WHERE asset_id = %s AND is_active = TRUE",
                (asset_id,),
            )
            result = cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

            return dict(result)


@router.get("/{asset_id}/data-coverage", response_model=Dict[str, Any])
async def get_data_coverage(asset_id: int) -> Dict[str, Any]:
    """Get data coverage information (date ranges) for an asset."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get asset info
            cursor.execute(
                "SELECT asset_type FROM assets WHERE asset_id = %s AND is_active = TRUE",
                (asset_id,),
            )
            asset = cursor.fetchone()

            if not asset:
                raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

            asset_type = asset["asset_type"]

            # Security: Use whitelist validation to get safe table/column names
            try:
                table, time_column = _get_table_and_column(asset_type)
            except ValueError:
                # Invalid asset type - return empty result
                return {
                    "asset_id": asset_id,
                    "asset_type": asset_type,
                    "has_data": False,
                    "earliest_date": None,
                    "latest_date": None,
                    "record_count": 0,
                }

            # Get date range and count
            # Security: Use psycopg2.sql.Identifier for table/column names
            # This ensures proper escaping and prevents SQL injection
            query = sql.SQL(
                """
                SELECT 
                    MIN({time_col}) as earliest_date,
                    MAX({time_col}) as latest_date,
                    COUNT(*) as record_count
                FROM {table_name}
                WHERE asset_id = %s
            """
            ).format(
                time_col=sql.Identifier(time_column),
                table_name=sql.Identifier(table),
            )

            cursor.execute(query, (asset_id,))
            result = cursor.fetchone()

            if result and result["record_count"] > 0:
                return {
                    "asset_id": asset_id,
                    "asset_type": asset_type,
                    "has_data": True,
                    "earliest_date": (
                        result["earliest_date"].isoformat() if result["earliest_date"] else None
                    ),
                    "latest_date": (
                        result["latest_date"].isoformat() if result["latest_date"] else None
                    ),
                    "record_count": result["record_count"],
                }
            else:
                return {
                    "asset_id": asset_id,
                    "asset_type": asset_type,
                    "has_data": False,
                    "earliest_date": None,
                    "latest_date": None,
                    "record_count": 0,
                }
