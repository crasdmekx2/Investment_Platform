"""Forex data collector using yfinance."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from investment_platform.collectors.base import (
    APIError,
    BaseDataCollector,
    DataCollectionError,
    ValidationError,
)


class ForexCollector(BaseDataCollector):
    """
    Collector for foreign exchange (Forex) data using yfinance.

    Uses yfinance as the data source for reliable forex data collection.
    """

    def __init__(self, output_format: str = "dataframe", **kwargs: Any):
        """
        Initialize the Forex collector.

        Args:
            output_format: Output format ('dataframe' or 'dict'). Defaults to 'dataframe'.
            **kwargs: Additional arguments passed to BaseDataCollector
        """
        super().__init__(output_format=output_format, **kwargs)

        # Initialize yfinance
        try:
            self.yf = self._init_yfinance()
            self.logger.info("Using yfinance as forex data source")
        except DataCollectionError as e:
            raise DataCollectionError(
                "yfinance is not available. Install it with: pip install yfinance"
            ) from e

    def collect_historical_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        **kwargs: Any,
    ) -> Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Collect historical exchange rate data for a currency pair.

        Args:
            symbol: Currency pair in format 'BASE_QUOTE' (e.g., 'USD_EUR', 'GBP_USD')
                   or 'BTC_USD' for Bitcoin rates
            start_date: Start date for data collection (ISO format string or datetime)
            end_date: End date for data collection (ISO format string or datetime)
            **kwargs: Additional parameters

        Returns:
            Historical exchange rate data in the specified output format

        Raises:
            APIError: If data collection fails
            ValidationError: If parameters are invalid

        """
        try:
            # Validate dates
            start_dt, end_dt = self._validate_dates(start_date, end_date)

            # Parse currency pair
            if "_" not in symbol:
                raise ValidationError(
                    f"Invalid symbol format: {symbol}. Expected format: 'BASE_QUOTE' (e.g., 'USD_EUR')"
                )

            base_currency, quote_currency = symbol.split("_", 1)
            base_currency = base_currency.upper()
            quote_currency = quote_currency.upper()

            self.logger.info(
                f"Collecting forex data for {base_currency}/{quote_currency} "
                f"from {start_dt} to {end_dt}"
            )

            # Handle Bitcoin separately
            if base_currency == "BTC":
                return self._collect_btc_data(quote_currency, start_dt, end_dt)

            # Use yfinance for forex data
            return self._collect_with_yfinance(base_currency, quote_currency, start_dt, end_dt)

        except Exception as e:
            self._handle_error(e, f"collect_historical_data for {symbol}")
            raise

    def _collect_with_yfinance(
        self, base_currency: str, quote_currency: str, start_dt: datetime, end_dt: datetime
    ) -> Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Collect forex data using yfinance.

        Args:
            base_currency: Base currency (e.g., 'USD', 'EUR')
            quote_currency: Quote currency (e.g., 'USD', 'EUR')
            start_dt: Start date
            end_dt: End date

        Returns:
            Historical forex rate data
        """
        # yfinance uses standard forex notation: BASEQUOTE=X (e.g., EURUSD=X for EUR/USD)
        # Try both directions since yfinance may have data for one but not the other
        # Standard pairs: EURUSD, GBPUSD, USDJPY, etc.
        yf_symbols = [
            f"{base_currency}{quote_currency}=X",  # Try original order first
            f"{quote_currency}{base_currency}=X",   # Try reversed order as fallback
        ]
        
        df = None
        used_symbol = None
        inverted = False
        
        days_diff = (end_dt - start_dt).days
        
        for yf_symbol in yf_symbols:
            try:
                self.logger.info(f"Trying yfinance symbol: {yf_symbol}")
                
                # Add buffer to ensure we get data (yfinance may return data for trading days near the requested dates)
                # For small ranges, expand slightly; for larger ranges, use exact dates
                if days_diff <= 1:
                    # For very small ranges, expand by a few days to ensure we get data
                    buffer_start = start_dt - timedelta(days=2)
                    buffer_end = end_dt + timedelta(days=2)
                else:
                    # For larger ranges, just add 1 day buffer
                    buffer_start = start_dt - timedelta(days=1)
                    buffer_end = end_dt + timedelta(days=1)
                
                # Fetch historical data using shared method
                df = self._fetch_yfinance_history(
                    symbol=yf_symbol,
                    start_dt=buffer_start,
                    end_dt=buffer_end,
                    interval='1d',
                    auto_adjust=True,
                    prepost=False,
                    actions=False,
                    yf=self.yf,
                )
                
                if not df.empty:
                    used_symbol = yf_symbol
                    # Check if we need to invert the rate
                    if yf_symbol == f"{quote_currency}{base_currency}=X":
                        inverted = True
                    break
            except Exception as e:
                self.logger.debug(f"Failed to get data for {yf_symbol}: {e}")
                continue
        
        if df is None or df.empty:
            self.logger.warning(f"No data returned from yfinance for {base_currency}/{quote_currency}")
            return self._format_output(pd.DataFrame())
        
        # Extract Close price as the rate
        rates = df['Close'].copy()
        
        # If we used the inverted symbol, invert the rate (1/rate)
        if inverted:
            rates = 1.0 / rates
            self.logger.info(f"Inverted rate for {base_currency}/{quote_currency} (used {used_symbol})")
        
        # Create result DataFrame
        df_result = pd.DataFrame({
            'rate': rates,
            'base_currency': base_currency,
            'quote_currency': quote_currency,
        })
        
        # Ensure index is datetime
        if not isinstance(df_result.index, pd.DatetimeIndex):
            df_result.index = pd.to_datetime(df_result.index)
        
        # Filter to requested date range (use date-only comparison for more lenient matching)
        # yfinance returns data for trading days, which may not exactly match requested dates
        # So we compare dates (not datetimes) to allow nearby trading days
        start_date_only = start_dt.date() if hasattr(start_dt, 'date') else pd.to_datetime(start_dt).date()
        end_date_only = end_dt.date() if hasattr(end_dt, 'date') else pd.to_datetime(end_dt).date()
        
        # Get date part of index for comparison
        df_dates = pd.to_datetime(df_result.index).date
        if hasattr(df_dates, 'values'):
            df_dates = [d.date() if hasattr(d, 'date') else pd.to_datetime(d).date() for d in df_result.index]
        else:
            df_dates = [d.date() if hasattr(d, 'date') else pd.to_datetime(d).date() for d in df_result.index]
        
        # Filter: include data where the date is within or near the requested range
        # For very small ranges (1 day), accept data within 2 days
        # For larger ranges, accept data within 1 day
        mask = []
        for idx_date in df_result.index:
            idx_date_only = idx_date.date() if hasattr(idx_date, 'date') else pd.to_datetime(idx_date).date()
            if days_diff <= 1:
                # For 1-day ranges, accept data within 2 days of the range
                days_from_start = abs((idx_date_only - start_date_only).days)
                days_from_end = abs((idx_date_only - end_date_only).days)
                mask.append(days_from_start <= 2 or days_from_end <= 2 or (start_date_only <= idx_date_only <= end_date_only))
            else:
                # For larger ranges, use standard filtering with 1-day tolerance
                mask.append(start_date_only - timedelta(days=1) <= idx_date_only <= end_date_only + timedelta(days=1))
        
        df_result = df_result[mask]
        
        if df_result.empty:
            self.logger.warning(f"No data in date range for {base_currency}/{quote_currency}")
            return self._format_output(pd.DataFrame())
        
        # Validate data
        self._validate_data(df_result, required_columns=["rate"])
        
        self.logger.info(
            f"Successfully collected {len(df_result)} records for {base_currency}/{quote_currency} using yfinance (symbol: {used_symbol})"
        )
        
        return self._format_output(df_result)

    def _collect_btc_data(
        self, quote_currency: str, start_dt: datetime, end_dt: datetime
    ) -> Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Collect Bitcoin exchange rate data using yfinance.

        Args:
            quote_currency: Quote currency (e.g., 'USD', 'EUR')
            start_dt: Start date
            end_dt: End date

        Returns:
            Historical Bitcoin rate data
        """
        # yfinance uses BTC-USD, BTC-EUR format for Bitcoin
        yf_symbol = f"BTC-{quote_currency}"
        
        self.logger.info(f"Collecting Bitcoin data for {yf_symbol} from {start_dt} to {end_dt}")
        
        # Add buffer to ensure we get data
        days_diff = (end_dt - start_dt).days
        if days_diff <= 1:
            buffer_start = start_dt - timedelta(days=2)
            buffer_end = end_dt + timedelta(days=2)
        else:
            buffer_start = start_dt - timedelta(days=1)
            buffer_end = end_dt + timedelta(days=1)
        
        # Fetch historical data using shared method
        df = self._fetch_yfinance_history(
            symbol=yf_symbol,
            start_dt=buffer_start,
            end_dt=buffer_end,
            interval='1d',
            auto_adjust=True,
            prepost=False,
            actions=False,
            yf=self.yf,
        )
        
        if df.empty:
            self.logger.warning(f"No data returned from yfinance for {yf_symbol}")
            return self._format_output(pd.DataFrame())
        
        # Extract Close price as the rate
        rates = df['Close'].copy()
        
        # Create result DataFrame
        df_result = pd.DataFrame({
            'rate': rates,
            'base_currency': 'BTC',
            'quote_currency': quote_currency,
        })
        
        # Ensure index is datetime
        if not isinstance(df_result.index, pd.DatetimeIndex):
            df_result.index = pd.to_datetime(df_result.index)
        
        # Filter to requested date range
        start_date_only = start_dt.date() if hasattr(start_dt, 'date') else pd.to_datetime(start_dt).date()
        end_date_only = end_dt.date() if hasattr(end_dt, 'date') else pd.to_datetime(end_dt).date()
        
        # Get date part of index for comparison
        mask = []
        for idx_date in df_result.index:
            idx_date_only = idx_date.date() if hasattr(idx_date, 'date') else pd.to_datetime(idx_date).date()
            if days_diff <= 1:
                days_from_start = abs((idx_date_only - start_date_only).days)
                days_from_end = abs((idx_date_only - end_date_only).days)
                mask.append(days_from_start <= 2 or days_from_end <= 2 or (start_date_only <= idx_date_only <= end_date_only))
            else:
                mask.append(start_date_only - timedelta(days=1) <= idx_date_only <= end_date_only + timedelta(days=1))
        
        df_result = df_result[mask]
        
        if df_result.empty:
            self.logger.warning(f"No data in date range for {yf_symbol}")
            return self._format_output(pd.DataFrame())
        
        # Validate data
        self._validate_data(df_result, required_columns=["rate"])
        
        self.logger.info(
            f"Successfully collected {len(df_result)} records for {yf_symbol} using yfinance"
        )
        
        return self._format_output(df_result)

    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieve metadata about a currency pair.

        Args:
            symbol: Currency pair in format 'BASE_QUOTE' (e.g., 'USD_EUR', 'GBP_USD')

        Returns:
            Dictionary containing currency pair metadata

        Raises:
            APIError: If asset info retrieval fails
        """
        try:
            # Parse currency pair
            if "_" not in symbol:
                raise ValidationError(
                    f"Invalid symbol format: {symbol}. Expected format: 'BASE_QUOTE'"
                )

            base_currency, quote_currency = symbol.split("_", 1)
            base_currency = base_currency.upper()
            quote_currency = quote_currency.upper()

            self.logger.info(f"Fetching currency pair info for {base_currency}/{quote_currency}")

            # Get current rate to verify pair is valid
            current_rate = None
            
            # Handle Bitcoin separately
            if base_currency == "BTC":
                yf_symbol = f"BTC-{quote_currency}"
                try:
                    ticker = self.yf.Ticker(yf_symbol)
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        current_rate = float(hist['Close'].iloc[-1])
                except Exception as e:
                    self.logger.debug(f"yfinance failed for BTC asset info: {e}")
            else:
                # Try both symbol directions for forex pairs
                yf_symbols = [
                    f"{base_currency}{quote_currency}=X",
                    f"{quote_currency}{base_currency}=X",
                ]
                for yf_symbol in yf_symbols:
                    try:
                        ticker = self.yf.Ticker(yf_symbol)
                        hist = ticker.history(period="1d")
                        if not hist.empty:
                            current_rate = float(hist['Close'].iloc[-1])
                            # If we used inverted symbol, invert the rate
                            if yf_symbol == f"{quote_currency}{base_currency}=X":
                                current_rate = 1.0 / current_rate
                            break
                    except Exception as e:
                        self.logger.debug(f"yfinance failed for {yf_symbol}: {e}")
                        continue
            
            if current_rate is None:
                raise APIError(
                    f"Invalid currency pair {base_currency}/{quote_currency}: "
                    f"Could not get rate from yfinance"
                )

            asset_info = {
                "symbol": symbol,
                "base_currency": base_currency,
                "quote_currency": quote_currency,
                "current_rate": current_rate,
                "type": "forex",
            }

            self.logger.info(
                f"Successfully retrieved currency pair info for {base_currency}/{quote_currency}"
            )

            return asset_info

        except Exception as e:
            self._handle_error(e, f"get_asset_info for {symbol}")
            raise

