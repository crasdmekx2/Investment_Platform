"""Assets API router."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from psycopg2.extras import RealDictCursor

from investment_platform.ingestion.db_connection import get_db_connection

router = APIRouter()


@router.get("", response_model=List[Dict[str, Any]])
async def list_assets(
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> List[Dict[str, Any]]:
    """List all registered assets."""
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

            # Determine which table to query based on asset type
            if asset_type in ["stock", "crypto", "commodity"]:
                table = "market_data"
                time_column = "time"
            elif asset_type == "forex":
                table = "forex_rates"
                time_column = "time"
            elif asset_type == "bond":
                table = "bond_rates"
                time_column = "time"
            elif asset_type == "economic_indicator":
                table = "economic_data"
                time_column = "time"
            else:
                return {
                    "asset_id": asset_id,
                    "asset_type": asset_type,
                    "has_data": False,
                    "earliest_date": None,
                    "latest_date": None,
                    "record_count": 0,
                }

            # Get date range and count
            cursor.execute(
                f"""
                SELECT 
                    MIN({time_column}) as earliest_date,
                    MAX({time_column}) as latest_date,
                    COUNT(*) as record_count
                FROM {table}
                WHERE asset_id = %s
                """,
                (asset_id,),
            )
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
