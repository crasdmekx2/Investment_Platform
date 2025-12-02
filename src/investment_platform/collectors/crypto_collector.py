"""Crypto data collector using Coinbase Advanced API."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from investment_platform.collectors.base import (
    APIError,
    BaseDataCollector,
    DataCollectionError,
)
from investment_platform.config import Config


class CryptoCollector(BaseDataCollector):
    """
    Collector for cryptocurrency data using Coinbase Advanced API.

    Uses the coinbase-advanced-py library to fetch historical OHLCV data
    for cryptocurrency trading pairs.

    Note: Coinbase Advanced API may require authentication for some endpoints.
    For public data, the library can work without credentials, but some
    features may require API keys.
    """

    def __init__(
        self,
        output_format: str = "dataframe",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize the Crypto collector.

        Args:
            output_format: Output format ('dataframe' or 'dict'). Defaults to 'dataframe'.
            api_key: Optional Coinbase API key. If not provided, uses config or public access.
            api_secret: Optional Coinbase API secret. If not provided, uses config or public access.
            **kwargs: Additional arguments passed to BaseDataCollector
        """
        super().__init__(output_format=output_format, **kwargs)

        # Get API credentials
        if api_key and api_secret:
            self.api_key = api_key
            self.api_secret = api_secret
        else:
            self.api_key, self.api_secret = Config.get_coinbase_credentials()

        # Initialize Coinbase client
        try:
            from coinbase.rest import RESTClient

            if self.api_key and self.api_secret:
                self.client = RESTClient(api_key=self.api_key, api_secret=self.api_secret)
            else:
                # Try to use public client (may have limited functionality)
                self.client = RESTClient()
                self.logger.warning(
                    "No API credentials provided. Using public access (may have limited functionality)."
                )
        except ImportError:
            raise DataCollectionError(
                "coinbase-advanced-py library is not installed. "
                "Install it with: pip install coinbase-advanced-py"
            )

    def collect_historical_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        granularity: str = "ONE_DAY",
        **kwargs: Any,
    ) -> Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Collect historical OHLCV data for a cryptocurrency pair.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USD', 'ETH-USD')
            start_date: Start date for data collection (ISO format string or datetime)
            end_date: End date for data collection (ISO format string or datetime)
            granularity: Candle granularity. Options: 'ONE_MINUTE', 'FIVE_MINUTE',
                        'FIFTEEN_MINUTE', 'ONE_HOUR', 'SIX_HOUR', 'ONE_DAY'.
                        Defaults to 'ONE_DAY'.
            **kwargs: Additional parameters

        Returns:
            Historical OHLCV data in the specified output format

        Raises:
            APIError: If data collection fails
            ValidationError: If parameters are invalid
        """
        try:
            # Validate dates
            start_dt, end_dt = self._validate_dates(start_date, end_date)

            self.logger.info(f"Collecting crypto data for {symbol} from {start_dt} to {end_dt}")

            # Convert dates to Unix timestamps (seconds since epoch)
            # Coinbase Advanced API expects timestamps as Unix timestamps (seconds)
            start_timestamp = int(start_dt.timestamp())
            end_timestamp = int(end_dt.timestamp())

            # Fetch historical candles
            response = self.client.get_candles(
                product_id=symbol,
                start=str(start_timestamp),
                end=str(end_timestamp),
                granularity=granularity,
            )

            # Response is a GetProductCandlesResponse object
            # Access candles attribute directly
            if not response:
                raise APIError(f"No data returned for {symbol}")

            # Try to get candles from the response object
            if hasattr(response, "candles"):
                candles = response.candles
            elif hasattr(response, "to_dict"):
                response_dict = response.to_dict()
                candles = response_dict.get("candles", [])
            elif hasattr(response, "__dict__"):
                candles = response.__dict__.get("candles", [])
            else:
                # Try to access as dict-like
                try:
                    candles = response["candles"]
                except (TypeError, KeyError):
                    raise APIError(f"Unexpected response format from Coinbase API for {symbol}")

            if not candles:
                self.logger.warning(f"No candles returned for {symbol}")
                return self._format_output(pd.DataFrame())

            # Convert candles to list of dicts if they are objects
            candles_list = []
            for candle in candles:
                if isinstance(candle, dict):
                    candles_list.append(candle)
                elif isinstance(candle, (list, tuple)) and len(candle) >= 6:
                    # Handle list format: [timestamp, low, high, open, close, volume]
                    # Or: [start, open, high, low, close, volume]
                    candles_list.append(
                        {
                            "start": candle[0],
                            "open": candle[3] if len(candle) > 3 else candle[1],
                            "high": candle[2] if len(candle) > 2 else candle[1],
                            "low": candle[1] if len(candle) > 1 else candle[0],
                            "close": candle[4] if len(candle) > 4 else candle[2],
                            "volume": candle[5] if len(candle) > 5 else candle[3],
                        }
                    )
                elif hasattr(candle, "to_dict"):
                    candles_list.append(candle.to_dict())
                elif hasattr(candle, "__dict__"):
                    candles_list.append(candle.__dict__)
                else:
                    # Try to access common attributes
                    candle_dict = {}
                    for attr in ["start", "open", "high", "low", "close", "volume"]:
                        if hasattr(candle, attr):
                            candle_dict[attr] = getattr(candle, attr)
                    if candle_dict:
                        candles_list.append(candle_dict)
                    else:
                        # Fallback: try to convert to dict
                        try:
                            candles_list.append(dict(candle) if hasattr(candle, "__iter__") else {})
                        except (TypeError, ValueError):
                            self.logger.warning(f"Could not convert candle to dict: {type(candle)}")
                            continue

            if not candles_list:
                self.logger.warning(f"No valid candle data for {symbol}")
                return self._format_output(pd.DataFrame())

            # Convert to DataFrame
            df = pd.DataFrame(candles_list)

            # Log actual columns for debugging
            if df.empty:
                self.logger.warning(f"Empty DataFrame created for {symbol}")
                return self._format_output(df)

            self.logger.debug(f"DataFrame columns before mapping: {list(df.columns)}")

            # Rename columns to standard OHLCV format if needed
            column_mapping = {
                "start": "timestamp",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
            }

            # Map columns if they exist
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns and new_col not in df.columns:
                    df = df.rename(columns={old_col: new_col})

            # If timestamp column doesn't exist but we have an index, use that
            if "timestamp" not in df.columns and not df.empty:
                # Check if index might be timestamp
                if isinstance(df.index, pd.DatetimeIndex):
                    df["timestamp"] = df.index
                elif df.index.name in ["start", "time", "date"]:
                    df["timestamp"] = df.index
                    df = df.reset_index(drop=True)

            # Ensure timestamp is datetime
            if "timestamp" in df.columns:
                # Check if timestamp is numeric (Unix timestamp)
                sample_value = df["timestamp"].iloc[0] if len(df) > 0 else None
                if sample_value is not None:
                    # Try to convert to numeric if it's a string
                    try:
                        if isinstance(sample_value, str):
                            numeric_value = float(sample_value)
                        else:
                            numeric_value = float(sample_value)

                        # If it's a numeric Unix timestamp (seconds), convert with unit='s'
                        # Unix timestamps are typically > 1000000000 (year 2001)
                        if numeric_value > 1000000000:
                            # Unix timestamp in seconds
                            df["timestamp"] = pd.to_datetime(
                                df["timestamp"].astype(float), unit="s"
                            )
                        else:
                            # Try to parse as datetime string
                            df["timestamp"] = pd.to_datetime(df["timestamp"])
                    except (ValueError, TypeError):
                        # If conversion fails, try to parse as datetime string
                        df["timestamp"] = pd.to_datetime(df["timestamp"])
                else:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])

            # Set timestamp as index if it exists
            if "timestamp" in df.columns:
                df = df.set_index("timestamp")

            # Validate data
            self._validate_data(df, required_columns=["open", "high", "low", "close"])

            self.logger.info(f"Successfully collected {len(df)} records for {symbol}")

            return self._format_output(df)

        except Exception as e:
            self._handle_error(e, f"collect_historical_data for {symbol}")
            raise

    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieve metadata about a cryptocurrency trading pair.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USD', 'ETH-USD')

        Returns:
            Dictionary containing asset metadata

        Raises:
            APIError: If asset info retrieval fails
        """
        try:
            self.logger.info(f"Fetching asset info for {symbol}")

            # Get product information
            response = self.client.get_product(symbol)

            if not response:
                raise APIError(f"No product information found for {symbol}")

            # Extract relevant information
            # Response is a GetProductResponse object, access attributes directly
            # or convert to dict if it has that method
            if hasattr(response, "to_dict"):
                response_dict = response.to_dict()
            elif hasattr(response, "__dict__"):
                response_dict = response.__dict__
            else:
                # Try to access attributes directly
                response_dict = {}
                for attr in [
                    "product_id",
                    "base_currency",
                    "quote_currency",
                    "display_name",
                    "status",
                ]:
                    if hasattr(response, attr):
                        response_dict[attr] = getattr(response, attr)

            asset_info = {
                "symbol": symbol,
                "product_id": response_dict.get(
                    "product_id", getattr(response, "product_id", symbol)
                ),
                "base_currency": response_dict.get(
                    "base_currency", getattr(response, "base_currency", "")
                ),
                "quote_currency": response_dict.get(
                    "quote_currency", getattr(response, "quote_currency", "")
                ),
                "display_name": response_dict.get(
                    "display_name", getattr(response, "display_name", symbol)
                ),
                "status": response_dict.get("status", getattr(response, "status", "unknown")),
                "type": "cryptocurrency",
            }

            self.logger.info(f"Successfully retrieved asset info for {symbol}")

            return asset_info

        except Exception as e:
            self._handle_error(e, f"get_asset_info for {symbol}")
            raise
