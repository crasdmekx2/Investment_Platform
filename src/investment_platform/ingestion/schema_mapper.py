"""Schema mapping - transforms collector output to database schema format."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


class SchemaMapper:
    """Maps collector output formats to database schema formats."""

    # Mapping of asset types to their target tables
    ASSET_TYPE_TO_TABLE = {
        "stock": "market_data",
        "crypto": "market_data",
        "commodity": "market_data",
        "forex": "forex_rates",
        "bond": "bond_rates",
        "economic_indicator": "economic_data",
    }

    def __init__(self):
        """Initialize the SchemaMapper."""
        self.logger = logger

    def map_to_market_data(self, data: pd.DataFrame, asset_id: int) -> pd.DataFrame:
        """
        Map collector data to market_data table format.

        Args:
            data: DataFrame from collector (should have OHLCV columns)
            asset_id: Asset ID

        Returns:
            DataFrame formatted for market_data table
        """
        if data.empty:
            return pd.DataFrame()

        # Ensure index is datetime
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)

        # Normalize column names to lowercase
        data.columns = [col.lower().strip() for col in data.columns]

        # Required columns for market_data
        required_cols = ["open", "high", "low", "close"]
        missing_cols = [col for col in required_cols if col not in data.columns]

        if missing_cols:
            raise ValueError(f"Missing required columns for market_data: {missing_cols}")

        # Build result DataFrame
        result = pd.DataFrame(index=data.index)
        result["time"] = data.index
        result["asset_id"] = asset_id
        result["open"] = data["open"]
        result["high"] = data["high"]
        result["low"] = data["low"]
        result["close"] = data["close"]

        # Optional columns
        if "volume" in data.columns:
            # Convert volume to numeric first (handles string decimals like '954.43296228')
            # Then convert to int64 for BIGINT database column
            # Use pd.to_numeric to handle string values, then convert to int
            volume_series = pd.to_numeric(data["volume"], errors="coerce").fillna(0)
            result["volume"] = volume_series.astype("int64")
        else:
            result["volume"] = None

        if "dividends" in data.columns:
            result["dividends"] = data["dividends"].fillna(0)
        else:
            result["dividends"] = None

        if "stock splits" in data.columns or "stock_splits" in data.columns:
            splits_col = "stock splits" if "stock splits" in data.columns else "stock_splits"
            result["stock_splits"] = data[splits_col].fillna(0)
        else:
            result["stock_splits"] = None

        # Reset index for easier insertion
        result = result.reset_index(drop=True)

        return result

    def map_to_forex_rates(self, data: pd.DataFrame, asset_id: int) -> pd.DataFrame:
        """
        Map collector data to forex_rates table format.

        Args:
            data: DataFrame from collector (should have rate column)
            asset_id: Asset ID

        Returns:
            DataFrame formatted for forex_rates table
        """
        if data.empty:
            return pd.DataFrame()

        # Ensure index is datetime
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)

        # Normalize column names
        data.columns = [col.lower().strip() for col in data.columns]

        # Find rate column (could be 'rate', 'close', or index-based)
        rate_col = None
        for col in ["rate", "close", "value"]:
            if col in data.columns:
                rate_col = col
                break

        if rate_col is None and len(data.columns) == 1:
            rate_col = data.columns[0]

        if rate_col is None:
            raise ValueError(
                "Could not find rate column in forex data. "
                "Expected one of: 'rate', 'close', 'value'"
            )

        # Build result DataFrame with rate and optional currency columns
        result = pd.DataFrame(
            {
                "time": data.index,
                "asset_id": asset_id,
                "rate": data[rate_col].values,
            }
        )

        # Add base_currency and quote_currency if present in source data
        if "base_currency" in data.columns:
            result["base_currency"] = data["base_currency"].values
        if "quote_currency" in data.columns:
            result["quote_currency"] = data["quote_currency"].values

        # Reset index
        result = result.reset_index(drop=True)

        return result

    def map_to_bond_rates(self, data: pd.DataFrame, asset_id: int) -> pd.DataFrame:
        """
        Map collector data to bond_rates table format.

        Args:
            data: DataFrame from collector (should have rate/value column)
            asset_id: Asset ID

        Returns:
            DataFrame formatted for bond_rates table
        """
        if data.empty:
            return pd.DataFrame()

        # Ensure index is datetime
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)

        # Normalize column names
        data.columns = [col.lower().strip() for col in data.columns]

        # Find rate column
        rate_col = None
        for col in ["rate", "value", "close"]:
            if col in data.columns:
                rate_col = col
                break

        if rate_col is None and len(data.columns) == 1:
            rate_col = data.columns[0]

        if rate_col is None:
            raise ValueError(
                "Could not find rate column in bond data. "
                "Expected one of: 'rate', 'value', 'close'"
            )

        result = pd.DataFrame(
            {
                "time": data.index,
                "asset_id": asset_id,
                "rate": data[rate_col].values,
            }
        )

        # Reset index
        result = result.reset_index(drop=True)

        return result

    def map_to_economic_data(self, data: pd.DataFrame, asset_id: int) -> pd.DataFrame:
        """
        Map collector data to economic_data table format.

        Args:
            data: DataFrame from collector (should have value column or symbol as column name)
            asset_id: Asset ID

        Returns:
            DataFrame formatted for economic_data table
        """
        if data.empty:
            return pd.DataFrame()

        # Handle case where date is a column (economic collector resets index)
        if "date" in data.columns:
            # Set date column as index
            data = data.set_index("date")

        # Ensure index is datetime
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)

        # Normalize column names
        data.columns = [col.lower().strip() for col in data.columns]

        # Find value column - economic collector uses symbol name as column
        # Try standard names first, then any numeric column
        value_col = None
        for col in ["value", "rate", "close"]:
            if col in data.columns:
                value_col = col
                break

        # If not found, look for any numeric column (economic collector uses symbol as column name)
        if value_col is None:
            numeric_cols = data.select_dtypes(include=["number"]).columns.tolist()
            if len(numeric_cols) == 1:
                value_col = numeric_cols[0]
            elif len(data.columns) == 1:
                value_col = data.columns[0]
            elif len(numeric_cols) > 1:
                # Multiple numeric columns - use the first one (should be the symbol)
                value_col = numeric_cols[0]
                self.logger.warning(
                    f"Multiple numeric columns found in economic data: {numeric_cols}. "
                    f"Using first column '{value_col}' as value column."
                )

        if value_col is None:
            # Log detailed information for debugging
            self.logger.error(
                f"Could not find value column in economic data. "
                f"Data shape: {data.shape}, "
                f"Columns: {list(data.columns)}, "
                f"Column types: {data.dtypes.to_dict()}, "
                f"Sample data:\n{data.head() if not data.empty else 'Empty DataFrame'}"
            )
            raise ValueError(
                f"Could not find value column in economic data. "
                f"Available columns: {list(data.columns)}. "
                f"Expected one of: 'value', 'rate', 'close', or a numeric column with the symbol name."
            )

        result = pd.DataFrame(
            {
                "time": data.index,
                "asset_id": asset_id,
                "value": data[value_col].values,
            }
        )

        # Reset index
        result = result.reset_index(drop=True)

        return result

    def map_data(self, data: pd.DataFrame, asset_type: str, asset_id: int) -> pd.DataFrame:
        """
        Map collector data to appropriate database table format.

        Args:
            data: DataFrame from collector
            asset_type: Type of asset
            asset_id: Asset ID

        Returns:
            DataFrame formatted for the appropriate table
        """
        table = self.ASSET_TYPE_TO_TABLE.get(asset_type)

        if table is None:
            raise ValueError(f"Unknown asset type: {asset_type}")

        if table == "market_data":
            return self.map_to_market_data(data, asset_id)
        elif table == "forex_rates":
            return self.map_to_forex_rates(data, asset_id)
        elif table == "bond_rates":
            return self.map_to_bond_rates(data, asset_id)
        elif table == "economic_data":
            return self.map_to_economic_data(data, asset_id)
        else:
            raise ValueError(f"Unknown table: {table}")
