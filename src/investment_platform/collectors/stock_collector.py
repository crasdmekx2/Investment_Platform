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

        # Initialize yfinance
        self.yf = self._init_yfinance()

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

            self.logger.info(f"Collecting stock data for {symbol} from {start_dt} to {end_dt}")

            # Fetch historical data using shared method
            df = self._fetch_yfinance_history(
                symbol=symbol,
                start_dt=start_dt,
                end_dt=end_dt,
                interval=interval,
                auto_adjust=True,
                prepost=False,
                actions=include_dividends or include_splits,
                yf=self.yf,
            )

            if df.empty:
                self.logger.warning(f"No data returned for {symbol}")
                return self._format_output(pd.DataFrame())

            # Standardize data using shared method
            df = self._standardize_yfinance_data(
                df=df,
                required_columns=["open", "high", "low", "close"],
                include_optional_columns=True,
            )

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

    def collect_historical_data_batch(
        self,
        symbols: List[str],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = "1d",
        include_dividends: bool = True,
        include_splits: bool = True,
        **kwargs: Any,
    ) -> List[pd.DataFrame]:
        """
        Collect historical stock data for multiple symbols in a single batch request.

        Uses yfinance's download() function which is more efficient than making
        separate requests for each symbol.

        Args:
            symbols: List of stock ticker symbols (e.g., ['AAPL', 'MSFT', 'GOOGL'])
            start_date: Start date for data collection (ISO format string or datetime)
            end_date: End date for data collection (ISO format string or datetime)
            interval: Data interval. Valid intervals: '1m', '2m', '5m', '15m', '30m',
                     '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo'.
                     Defaults to '1d'.
            include_dividends: Whether to include dividend data. Defaults to True.
            include_splits: Whether to include stock split data. Defaults to True.
            **kwargs: Additional parameters

        Returns:
            List of DataFrames, one for each symbol in the same order as input

        Raises:
            APIError: If data collection fails
            ValidationError: If parameters are invalid
        """
        try:
            # Validate dates
            start_dt, end_dt = self._validate_dates(start_date, end_date)

            self.logger.info(
                f"Collecting batch stock data for {len(symbols)} symbols "
                f"({', '.join(symbols[:5])}{'...' if len(symbols) > 5 else ''}) "
                f"from {start_dt} to {end_dt}"
            )

            # Use yfinance download for batch collection
            # This is more efficient than individual Ticker() calls
            df_batch = self.yf.download(
                tickers=symbols,
                start=start_dt,
                end=end_dt,
                interval=interval,
                auto_adjust=True,
                prepost=False,
                actions=include_dividends or include_splits,
                group_by="ticker",
                progress=False,
            )

            if df_batch.empty:
                self.logger.warning(f"No data returned for batch request")
                return [pd.DataFrame()] * len(symbols)

            # Process results - yfinance.download returns a MultiIndex DataFrame
            # with columns grouped by ticker
            results = []

            for symbol in symbols:
                try:
                    # Extract data for this symbol
                    if len(symbols) == 1:
                        # Single symbol - DataFrame is not MultiIndex
                        df = df_batch.copy()
                    else:
                        # Multiple symbols - DataFrame has MultiIndex columns
                        # Get columns for this symbol
                        symbol_cols = [col for col in df_batch.columns if col[0] == symbol]
                        if not symbol_cols:
                            # Symbol not found in results
                            self.logger.warning(f"No data found for {symbol} in batch")
                            results.append(pd.DataFrame())
                            continue

                        # Extract columns for this symbol
                        df = df_batch[symbol_cols].copy()
                        # Flatten column names (remove MultiIndex level)
                        df.columns = [
                            col[1] if isinstance(col, tuple) else col for col in df.columns
                        ]

                    if df.empty:
                        self.logger.warning(f"No data returned for {symbol}")
                        results.append(pd.DataFrame())
                        continue

                    # Ensure index is datetime
                    if not isinstance(df.index, pd.DatetimeIndex):
                        df.index = pd.to_datetime(df.index)

                    # Standardize column names to lowercase
                    df.columns = [col.lower() for col in df.columns]

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
                    if not df.empty:
                        self._validate_data(df, required_columns=["open", "high", "low", "close"])

                    results.append(df)

                except Exception as e:
                    self.logger.error(f"Error processing {symbol} from batch: {e}", exc_info=True)
                    results.append(pd.DataFrame())

            self.logger.info(
                f"Successfully collected batch data: {sum(1 for r in results if not r.empty)}/{len(symbols)} symbols"
            )

            return results

        except Exception as e:
            self._handle_error(e, f"collect_historical_data_batch for {len(symbols)} symbols")
            raise
