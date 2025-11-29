"""Stock data collector using yfinance."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from investment_platform.collectors.base import (
    APIError,
    BaseDataCollector,
    DataCollectionError,
)


class StockCollector(BaseDataCollector):
    """
    Collector for stock market data using yfinance.

    Uses the yfinance library to fetch historical stock data including
    OHLCV, dividends, and stock splits.
    """

    def __init__(self, output_format: str = "dataframe", **kwargs: Any):
        """
        Initialize the Stock collector.

        Args:
            output_format: Output format ('dataframe' or 'dict'). Defaults to 'dataframe'.
            **kwargs: Additional arguments passed to BaseDataCollector
        """
        super().__init__(output_format=output_format, **kwargs)

        # Verify yfinance is available
        try:
            import yfinance as yf

            self.yf = yf
        except ImportError:
            raise DataCollectionError(
                "yfinance library is not installed. "
                "Install it with: pip install yfinance"
            )

    def collect_historical_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = "1d",
        include_dividends: bool = True,
        include_splits: bool = True,
        **kwargs: Any,
    ) -> Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Collect historical stock data for a given ticker.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')
            start_date: Start date for data collection (ISO format string or datetime)
            end_date: End date for data collection (ISO format string or datetime)
            interval: Data interval. Valid intervals: '1m', '2m', '5m', '15m', '30m',
                     '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'.
                     Defaults to '1d'.
            include_dividends: Whether to include dividend data. Defaults to True.
            include_splits: Whether to include stock split data. Defaults to True.
            **kwargs: Additional parameters

        Returns:
            Historical stock data in the specified output format

        Raises:
            APIError: If data collection fails
            ValidationError: If parameters are invalid
        """
        try:
            # Validate dates
            start_dt, end_dt = self._validate_dates(start_date, end_date)

            self.logger.info(
                f"Collecting stock data for {symbol} from {start_dt} to {end_dt}"
            )

            # Create ticker object
            ticker = self.yf.Ticker(symbol)

            # Fetch historical data
            df = ticker.history(
                start=start_dt,
                end=end_dt,
                interval=interval,
                auto_adjust=True,
                prepost=False,
                actions=include_dividends or include_splits,
            )

            if df.empty:
                self.logger.warning(f"No data returned for {symbol}")
                return self._format_output(pd.DataFrame())

            # Ensure index is datetime
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            # Standardize column names to lowercase
            df.columns = [col.lower() for col in df.columns]

            # Rename columns to standard OHLCV format if needed
            column_mapping = {
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
            }

            # Keep only standard columns if they exist
            standard_columns = ["open", "high", "low", "close", "volume"]
            available_columns = [col for col in standard_columns if col in df.columns]

            # Add additional columns if they exist
            additional_columns = ["dividends", "stock splits"]
            for col in additional_columns:
                if col in df.columns:
                    available_columns.append(col)

            df = df[available_columns]

            # Validate data
            self._validate_data(df, required_columns=["open", "high", "low", "close"])

            self.logger.info(f"Successfully collected {len(df)} records for {symbol}")

            return self._format_output(df)

        except Exception as e:
            self._handle_error(e, f"collect_historical_data for {symbol}")
            raise

    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieve metadata about a stock.

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')

        Returns:
            Dictionary containing asset metadata

        Raises:
            APIError: If asset info retrieval fails
        """
        try:
            self.logger.info(f"Fetching asset info for {symbol}")

            # Create ticker object
            ticker = self.yf.Ticker(symbol)

            # Get info
            info = ticker.info

            if not info:
                raise APIError(f"No information found for {symbol}")

            # Extract relevant information
            asset_info = {
                "symbol": symbol,
                "name": info.get("longName", info.get("shortName", symbol)),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "exchange": info.get("exchange", ""),
                "currency": info.get("currency", "USD"),
                "market_cap": info.get("marketCap", 0),
                "type": "stock",
            }

            # Add additional useful fields if available
            optional_fields = [
                "website",
                "description",
                "country",
                "fullTimeEmployees",
                "fiftyTwoWeekHigh",
                "fiftyTwoWeekLow",
            ]

            for field in optional_fields:
                if field in info:
                    asset_info[field] = info[field]

            self.logger.info(f"Successfully retrieved asset info for {symbol}")

            return asset_info

        except Exception as e:
            self._handle_error(e, f"get_asset_info for {symbol}")
            raise

