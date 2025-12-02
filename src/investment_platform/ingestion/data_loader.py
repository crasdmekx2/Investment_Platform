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

    def _load_with_copy(self, data: pd.DataFrame, table: str, on_conflict: str) -> int:
        """
        Load data using PostgreSQL COPY (faster for bulk inserts).

        Args:
            data: DataFrame to load
            table: Target table name
            on_conflict: Conflict resolution strategy

        Returns:
            Number of records inserted
        """
        initial_count = len(data)
        self.logger.info(f"Attempting to load {initial_count} records into {table} using COPY")

        # Validate data before loading
        validation_errors = self._validate_data_before_load(data, table)
        if validation_errors:
            self.logger.error(
                f"Data validation failed for {table}: {validation_errors}\n"
                f"Sample data (first row): {data.iloc[0].to_dict() if not data.empty else 'N/A'}"
            )
            raise ValueError(f"Data validation failed: {validation_errors}")

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Create temporary table with unique name (include timestamp to avoid collisions)
                import time
                import uuid

                unique_id = f"{abs(hash(str(data.index)))}_{int(time.time() * 1000000)}_{uuid.uuid4().hex[:8]}"
                temp_table = f"{table}_temp_{unique_id}"

                # Get column names from DataFrame
                columns = list(data.columns)

                # Create temp table with same structure (IF NOT EXISTS to handle race conditions)
                cursor.execute(
                    f"""
                    CREATE TEMP TABLE IF NOT EXISTS {temp_table} (LIKE {table} INCLUDING ALL)
                    """
                )

                # Use COPY to load into temp table
                buffer = StringIO()
                data.to_csv(buffer, index=False, header=False, na_rep="\\N")
                buffer.seek(0)

                try:
                    cursor.copy_expert(
                        f"COPY {temp_table} ({', '.join(columns)}) FROM STDIN WITH CSV NULL '\\N'",
                        buffer,
                    )
                except Exception as e:
                    self.logger.error(
                        f"COPY to temp table failed: {e}\n"
                        f"Data shape: {data.shape}, Columns: {columns}\n"
                        f"Sample data (first 3 rows):\n{data.head(3).to_dict('records')}"
                    )
                    raise

                # Count records in temp table
                cursor.execute(f"SELECT COUNT(*) FROM {temp_table}")
                temp_count = cursor.fetchone()[0]

                if temp_count != initial_count:
                    self.logger.warning(
                        f"Record count mismatch: {initial_count} in DataFrame, {temp_count} in temp table"
                    )

                # Insert from temp table with conflict handling
                # All time-series tables use (asset_id, time) as primary key
                conflict_cols = "asset_id, time"

                try:
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
                            col for col in columns if col not in ["asset_id", "time", "created_at"]
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

                    # Log detailed information about dropped records
                    if rows_affected < temp_count:
                        dropped_count = temp_count - rows_affected
                        self.logger.warning(
                            f"Only {rows_affected} of {temp_count} records loaded into {table}. "
                            f"{dropped_count} records were dropped."
                        )

                        # Query to find which records were skipped (duplicates or constraint violations)
                        if on_conflict == "do_nothing":
                            # Check for duplicates
                            cursor.execute(
                                f"""
                                SELECT t.*
                                FROM {temp_table} t
                                LEFT JOIN {table} e ON t.asset_id = e.asset_id AND t.time = e.time
                                WHERE e.asset_id IS NULL
                                LIMIT 10
                                """
                            )
                            skipped_records = cursor.fetchall()
                            if skipped_records:
                                self.logger.warning(
                                    f"Sample of {len(skipped_records)} skipped records (likely duplicates or constraint violations):\n"
                                    f"{skipped_records[:5]}"
                                )

                        # Check for constraint violations by attempting to identify problematic records
                        # This is a best-effort check since COPY doesn't provide detailed error info
                        self.logger.warning(
                            f"Investigate why {dropped_count} records were not loaded. "
                            f"Possible causes: duplicate (asset_id, time) pairs, constraint violations, "
                            f"or invalid data types."
                        )

                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    self.logger.error(
                        f"Error loading data into {table} using COPY: {e}", exc_info=True
                    )
                    # Log sample data for debugging
                    if not data.empty:
                        self.logger.debug(f"Sample data (first row): {data.iloc[0].to_dict()}")
                    raise

                self.logger.info(
                    f"Loaded {rows_affected} of {initial_count} records into {table} using COPY"
                )

                return rows_affected

    def _validate_data_before_load(self, data: pd.DataFrame, table: str) -> Optional[str]:
        """
        Validate data before loading to catch issues early.

        Args:
            data: DataFrame to validate
            table: Target table name

        Returns:
            Error message if validation fails, None if valid
        """
        if data.empty:
            return None

        errors = []

        # Check required columns
        required_cols = {
            "market_data": ["asset_id", "time", "open", "high", "low", "close"],
            "forex_rates": ["asset_id", "time", "rate"],
            "bond_rates": ["asset_id", "time", "rate"],
            "economic_data": ["asset_id", "time", "value"],
        }

        required = required_cols.get(table, ["asset_id", "time"])
        missing = [col for col in required if col not in data.columns]
        if missing:
            errors.append(f"Missing required columns: {missing}")

        # Check for null values in required columns
        for col in required:
            if col in data.columns:
                null_count = data[col].isna().sum()
                if null_count > 0:
                    errors.append(f"Column '{col}' has {null_count} null values (not allowed)")

        # Check for invalid data types
        if "asset_id" in data.columns:
            if not pd.api.types.is_integer_dtype(data["asset_id"]):
                errors.append("Column 'asset_id' must be integer type")

        if "time" in data.columns:
            if not pd.api.types.is_datetime64_any_dtype(data["time"]):
                errors.append("Column 'time' must be datetime type")

        # Check OHLC constraints for market_data
        if table == "market_data":
            for col in ["open", "high", "low", "close"]:
                if col in data.columns:
                    # Check for negative values
                    negative = (data[col] < 0).sum()
                    if negative > 0:
                        errors.append(
                            f"Column '{col}' has {negative} negative values (not allowed)"
                        )

            # Check OHLC logical constraints: high >= low, high >= open, high >= close, low <= open, low <= close
            if all(col in data.columns for col in ["open", "high", "low", "close"]):
                invalid_ohlc = (
                    (data["high"] < data["low"])
                    | (data["high"] < data["open"])
                    | (data["high"] < data["close"])
                    | (data["low"] > data["open"])
                    | (data["low"] > data["close"])
                ).sum()
                if invalid_ohlc > 0:
                    errors.append(
                        f"OHLC constraint violations: {invalid_ohlc} records have invalid OHLC relationships"
                    )

        # Check rate constraints for forex/bond rates
        if table in ["forex_rates", "bond_rates"]:
            if "rate" in data.columns:
                # Rate must be positive
                non_positive = (data["rate"] <= 0).sum()
                if non_positive > 0:
                    errors.append(
                        f"Column 'rate' has {non_positive} non-positive values (must be > 0)"
                    )

        if errors:
            return "; ".join(errors)
        return None

    def _load_with_insert(self, data: pd.DataFrame, table: str, on_conflict: str) -> int:
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
                                col
                                for col in columns
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
                        error_str = str(e).lower()
                        if "duplicate key" in error_str or "unique constraint" in error_str:
                            rows_skipped += 1
                            self.logger.debug(f"Skipped duplicate record: {e}")
                        elif "check constraint" in error_str or "constraint" in error_str:
                            # Constraint violation (e.g., OHLC check, volume >= 0)
                            self.logger.error(
                                f"Constraint violation inserting row into {table}: {e}\n"
                                f"Row data: {dict(zip(columns, values))}"
                            )
                            rows_skipped += 1
                        else:
                            self.logger.error(
                                f"Error inserting row into {table}: {e}\n"
                                f"Row data: {dict(zip(columns, values))}"
                            )
                            raise

                conn.commit()

                self.logger.info(
                    f"Loaded {rows_inserted} records into {table} "
                    f"(skipped {rows_skipped} duplicates)"
                )

                return rows_inserted
