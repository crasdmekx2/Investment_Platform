"""Data loader - loads time-series data into database tables."""

import logging
from typing import Optional
from io import StringIO

import pandas as pd

from investment_platform.ingestion.db_connection import get_db_connection

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads time-series data into appropriate database tables."""

    # Mapping of asset types to their target tables
    ASSET_TYPE_TO_TABLE = {
        "stock": "market_data",
        "crypto": "market_data",
        "commodity": "market_data",
        "forex": "forex_rates",
        "bond": "bond_rates",
        "economic_indicator": "economic_data",
    }

    def __init__(self, use_copy: bool = True):
        """
        Initialize the DataLoader.
        
        Args:
            use_copy: Whether to use PostgreSQL COPY for bulk inserts (faster)
        """
        self.logger = logger
        self.use_copy = use_copy

    def load_data(
        self,
        data: pd.DataFrame,
        asset_type: str,
        on_conflict: str = "do_nothing",
    ) -> int:
        """
        Load data into the appropriate table based on asset type.
        
        Args:
            data: DataFrame with data to load (must be pre-mapped to table format)
            asset_type: Type of asset
            on_conflict: How to handle conflicts ('do_nothing', 'update', 'skip')
            
        Returns:
            Number of records inserted/updated
        """
        if data.empty:
            self.logger.warning("Empty DataFrame provided, nothing to load")
            return 0
        
        table = self.ASSET_TYPE_TO_TABLE.get(asset_type)
        
        if table is None:
            raise ValueError(f"Unknown asset type: {asset_type}")
        
        if self.use_copy and on_conflict == "do_nothing":
            return self._load_with_copy(data, table, on_conflict)
        else:
            return self._load_with_insert(data, table, on_conflict)

    def _load_with_copy(
        self, data: pd.DataFrame, table: str, on_conflict: str
    ) -> int:
        """
        Load data using PostgreSQL COPY (faster for bulk inserts).
        
        Args:
            data: DataFrame to load
            table: Target table name
            on_conflict: Conflict resolution strategy
            
        Returns:
            Number of records inserted
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Create temporary table
                temp_table = f"{table}_temp_{hash(str(data.index))}"
                
                # Get column names from DataFrame
                columns = list(data.columns)
                
                # Create temp table with same structure
                cursor.execute(
                    f"""
                    CREATE TEMP TABLE {temp_table} (LIKE {table} INCLUDING ALL)
                    """
                )
                
                # Use COPY to load into temp table
                buffer = StringIO()
                data.to_csv(buffer, index=False, header=False, na_rep="\\N")
                buffer.seek(0)
                
                cursor.copy_expert(
                    f"COPY {temp_table} ({', '.join(columns)}) FROM STDIN WITH CSV NULL '\\N'",
                    buffer,
                )
                
                # Insert from temp table with conflict handling
                # All time-series tables use (asset_id, time) as primary key
                conflict_cols = "asset_id, time"
                
                if on_conflict == "do_nothing":
                    cursor.execute(
                        f"""
                        INSERT INTO {table} ({', '.join(columns)})
                        SELECT {', '.join(columns)}
                        FROM {temp_table}
                        ON CONFLICT ({conflict_cols}) DO NOTHING
                        """
                    )
                elif on_conflict == "update":
                    # Build UPDATE clause for non-key columns
                    update_cols = [
                        col for col in columns
                        if col not in ["asset_id", "time", "created_at"]
                    ]
                    update_clause = ", ".join(
                        [f"{col} = EXCLUDED.{col}" for col in update_cols]
                    )
                    
                    cursor.execute(
                        f"""
                        INSERT INTO {table} ({', '.join(columns)})
                        SELECT {', '.join(columns)}
                        FROM {temp_table}
                        ON CONFLICT ({conflict_cols})
                        DO UPDATE SET {update_clause}
                        """
                    )
                else:
                    # Simple insert (will fail on conflict)
                    cursor.execute(
                        f"""
                        INSERT INTO {table} ({', '.join(columns)})
                        SELECT {', '.join(columns)}
                        FROM {temp_table}
                        """
                    )
                
                rows_affected = cursor.rowcount
                conn.commit()
                
                self.logger.info(
                    f"Loaded {rows_affected} records into {table} using COPY"
                )
                
                return rows_affected

    def _load_with_insert(
        self, data: pd.DataFrame, table: str, on_conflict: str
    ) -> int:
        """
        Load data using INSERT statements (more flexible conflict handling).
        
        Args:
            data: DataFrame to load
            table: Target table name
            on_conflict: Conflict resolution strategy
            
        Returns:
            Number of records inserted/updated
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                columns = list(data.columns)
                placeholders = ", ".join(["%s"] * len(columns))
                
                rows_inserted = 0
                rows_skipped = 0
                
                for _, row in data.iterrows():
                    values = tuple(row[col] for col in columns)
                    
                    try:
                        if on_conflict == "do_nothing":
                            # Get primary key columns for conflict target
                            if table == "market_data":
                                conflict_cols = "(asset_id, time)"
                            else:
                                conflict_cols = "(asset_id, time)"
                            
                            query = f"""
                                INSERT INTO {table} ({', '.join(columns)})
                                VALUES ({placeholders})
                                ON CONFLICT {conflict_cols} DO NOTHING
                            """
                        elif on_conflict == "update":
                            # Build UPDATE clause for non-key columns
                            update_cols = [
                                col for col in columns
                                if col not in ["asset_id", "time", "created_at"]
                            ]
                            update_clause = ", ".join(
                                [f"{col} = EXCLUDED.{col}" for col in update_cols]
                            )
                            
                            query = f"""
                                INSERT INTO {table} ({', '.join(columns)})
                                VALUES ({placeholders})
                                ON CONFLICT (asset_id, time)
                                DO UPDATE SET {update_clause}
                            """
                        else:
                            # Simple insert (will fail on conflict)
                            query = f"""
                                INSERT INTO {table} ({', '.join(columns)})
                                VALUES ({placeholders})
                            """
                        
                        cursor.execute(query, values)
                        rows_inserted += cursor.rowcount
                        
                    except Exception as e:
                        if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
                            rows_skipped += 1
                            self.logger.debug(f"Skipped duplicate record: {e}")
                        else:
                            self.logger.error(f"Error inserting row: {e}")
                            raise
                
                conn.commit()
                
                self.logger.info(
                    f"Loaded {rows_inserted} records into {table} "
                    f"(skipped {rows_skipped} duplicates)"
                )
                
                return rows_inserted

