"""Incremental tracking - determines existing data ranges for incremental updates."""

import logging
from typing import List, Tuple, Optional
from datetime import datetime, timedelta

from investment_platform.ingestion.db_connection import get_db_connection

logger = logging.getLogger(__name__)


class IncrementalTracker:
    """Tracks existing data ranges and calculates gaps for incremental updates."""

    # Mapping of asset types to their time-series tables
    ASSET_TYPE_TO_TABLE = {
        "stock": "market_data",
        "crypto": "market_data",
        "commodity": "market_data",
        "forex": "forex_rates",
        "bond": "bond_rates",
        "economic_indicator": "economic_data",
    }

    def __init__(self):
        """Initialize the IncrementalTracker."""
        self.logger = logger

    def get_existing_data_range(
        self, asset_id: int, asset_type: str
    ) -> Optional[Tuple[datetime, datetime]]:
        """
        Get the existing data range for an asset.
        
        Args:
            asset_id: Asset ID
            asset_type: Type of asset
            
        Returns:
            Tuple of (min_time, max_time) if data exists, None otherwise
        """
        table = self.ASSET_TYPE_TO_TABLE.get(asset_type)
        
        if table is None:
            raise ValueError(f"Unknown asset type: {asset_type}")
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                query = f"""
                    SELECT MIN(time) as min_time, MAX(time) as max_time
                    FROM {table}
                    WHERE asset_id = %s
                """
                cursor.execute(query, (asset_id,))
                result = cursor.fetchone()
                
                if result and result[0] and result[1]:
                    return (result[0], result[1])
                
                return None

    def calculate_missing_ranges(
        self,
        asset_id: int,
        asset_type: str,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Tuple[datetime, datetime]]:
        """
        Calculate missing date ranges for an asset.
        
        Args:
            asset_id: Asset ID
            asset_type: Type of asset
            start_date: Desired start date
            end_date: Desired end date
            
        Returns:
            List of (start, end) tuples representing missing ranges
        """
        existing_range = self.get_existing_data_range(asset_id, asset_type)
        
        if existing_range is None:
            # No existing data, return full range
            return [(start_date, end_date)]
        
        min_time, max_time = existing_range
        missing_ranges = []
        
        # Ensure timezone consistency
        if start_date.tzinfo is None and min_time.tzinfo is not None:
            from datetime import timezone
            start_date = start_date.replace(tzinfo=timezone.utc)
        elif start_date.tzinfo is not None and min_time.tzinfo is None:
            start_date = start_date.replace(tzinfo=None)
        
        if end_date.tzinfo is None and max_time.tzinfo is not None:
            from datetime import timezone
            end_date = end_date.replace(tzinfo=timezone.utc)
        elif end_date.tzinfo is not None and max_time.tzinfo is None:
            end_date = end_date.replace(tzinfo=None)
        
        # Check for gap before existing data
        if start_date < min_time:
            # Add range from start_date to just before min_time
            gap_end = min_time - timedelta(days=1)
            missing_ranges.append((start_date, gap_end))
        
        # Check for gap after existing data
        if end_date > max_time:
            # Add range from just after max_time to end_date
            gap_start = max_time + timedelta(days=1)
            # Ensure timezone consistency for gap_start
            if gap_start.tzinfo is None and end_date.tzinfo is not None:
                from datetime import timezone
                gap_start = gap_start.replace(tzinfo=timezone.utc)
            elif gap_start.tzinfo is not None and end_date.tzinfo is None:
                gap_start = gap_start.replace(tzinfo=None)
            missing_ranges.append((gap_start, end_date))
        
        # If no gaps, return empty list (all data exists)
        return missing_ranges

    def has_data_in_range(
        self,
        asset_id: int,
        asset_type: str,
        start_date: datetime,
        end_date: datetime,
    ) -> bool:
        """
        Check if data exists in the specified range.
        
        Args:
            asset_id: Asset ID
            asset_type: Type of asset
            start_date: Start date
            end_date: End date
            
        Returns:
            True if any data exists in the range, False otherwise
        """
        table = self.ASSET_TYPE_TO_TABLE.get(asset_type)
        
        if table is None:
            raise ValueError(f"Unknown asset type: {asset_type}")
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                query = f"""
                    SELECT EXISTS(
                        SELECT 1
                        FROM {table}
                        WHERE asset_id = %s
                        AND time >= %s
                        AND time <= %s
                    )
                """
                cursor.execute(query, (asset_id, start_date, end_date))
                result = cursor.fetchone()
                return result[0] if result else False

    def get_latest_timestamp(
        self, asset_id: int, asset_type: str
    ) -> Optional[datetime]:
        """
        Get the latest timestamp for an asset.
        
        Args:
            asset_id: Asset ID
            asset_type: Type of asset
            
        Returns:
            Latest timestamp or None if no data exists
        """
        table = self.ASSET_TYPE_TO_TABLE.get(asset_type)
        
        if table is None:
            raise ValueError(f"Unknown asset type: {asset_type}")
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                query = f"""
                    SELECT MAX(time)
                    FROM {table}
                    WHERE asset_id = %s
                """
                cursor.execute(query, (asset_id,))
                result = cursor.fetchone()
                return result[0] if result and result[0] else None

    def get_data_count(
        self, asset_id: int, asset_type: str
    ) -> int:
        """
        Get the total number of records for an asset.
        
        Args:
            asset_id: Asset ID
            asset_type: Type of asset
            
        Returns:
            Number of records
        """
        table = self.ASSET_TYPE_TO_TABLE.get(asset_type)
        
        if table is None:
            raise ValueError(f"Unknown asset type: {asset_type}")
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                query = f"""
                    SELECT COUNT(*)
                    FROM {table}
                    WHERE asset_id = %s
                """
                cursor.execute(query, (asset_id,))
                result = cursor.fetchone()
                return result[0] if result else 0

