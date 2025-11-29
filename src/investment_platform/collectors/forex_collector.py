"""Forex data collector using forex-python."""

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
    Collector for foreign exchange (Forex) data using forex-python.

    Uses the forex-python library to fetch historical exchange rates.
    Note: forex-python has limited historical data capabilities and primarily
    provides current rates. For extensive historical data, consider using
    alternative sources or APIs.
    """

    def __init__(self, output_format: str = "dataframe", **kwargs: Any):
        """
        Initialize the Forex collector.

        Args:
            output_format: Output format ('dataframe' or 'dict'). Defaults to 'dataframe'.
            **kwargs: Additional arguments passed to BaseDataCollector
        """
        super().__init__(output_format=output_format, **kwargs)

        # Verify forex-python is available
        try:
            from forex_python.converter import CurrencyRates
            from forex_python.bitcoin import BtcConverter

            self.currency_rates = CurrencyRates()
            self.btc_converter = BtcConverter()
        except ImportError:
            raise DataCollectionError(
                "forex-python library is not installed. "
                "Install it with: pip install forex-python"
            )

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

        Note:
            forex-python has limited historical data support. This implementation
            attempts to collect daily rates, but the library may not support
            all date ranges. For comprehensive historical data, consider using
            alternative data sources.
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

            # Collect daily rates
            rates = []
            current_date = start_dt

            # Limit date range to avoid excessive API calls
            max_days = 365  # Limit to 1 year
            days_diff = (end_dt - start_dt).days
            if days_diff > max_days:
                self.logger.warning(
                    f"Date range exceeds {max_days} days. Limiting to {max_days} days."
                )
                end_dt = start_dt + timedelta(days=max_days)

            while current_date <= end_dt:
                try:
                    # Get rate for specific date
                    rate = self.currency_rates.get_rate(
                        base_currency, quote_currency, current_date
                    )

                    rates.append(
                        {
                            "date": current_date,
                            "base_currency": base_currency,
                            "quote_currency": quote_currency,
                            "rate": rate,
                        }
                    )

                    # Move to next day
                    current_date += timedelta(days=1)

                except Exception as e:
                    self.logger.warning(
                        f"Failed to get rate for {current_date}: {e}. Skipping."
                    )
                    current_date += timedelta(days=1)
                    continue

            if not rates:
                self.logger.warning(
                    f"No rates collected for {base_currency}/{quote_currency}"
                )
                return self._format_output(pd.DataFrame())

            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")

            # Validate data
            self._validate_data(df, required_columns=["rate"])

            self.logger.info(
                f"Successfully collected {len(df)} records for {base_currency}/{quote_currency}"
            )

            return self._format_output(df)

        except Exception as e:
            self._handle_error(e, f"collect_historical_data for {symbol}")
            raise

    def _collect_btc_data(
        self, quote_currency: str, start_dt: datetime, end_dt: datetime
    ) -> Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Collect Bitcoin exchange rate data.

        Args:
            quote_currency: Quote currency (e.g., 'USD', 'EUR')
            start_dt: Start date
            end_dt: End date

        Returns:
            Historical Bitcoin rate data
        """
        rates = []
        current_date = start_dt

        # Limit date range
        max_days = 365
        days_diff = (end_dt - start_dt).days
        if days_diff > max_days:
            end_dt = start_dt + timedelta(days=max_days)

        while current_date <= end_dt:
            try:
                rate = self.btc_converter.get_previous_price(quote_currency, current_date)

                rates.append(
                    {
                        "date": current_date,
                        "base_currency": "BTC",
                        "quote_currency": quote_currency,
                        "rate": rate,
                    }
                )

                current_date += timedelta(days=1)

            except Exception as e:
                self.logger.warning(
                    f"Failed to get BTC rate for {current_date}: {e}. Skipping."
                )
                current_date += timedelta(days=1)
                continue

        if not rates:
            return self._format_output(pd.DataFrame())

        df = pd.DataFrame(rates)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

        self._validate_data(df, required_columns=["rate"])

        return self._format_output(df)

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
            try:
                if base_currency == "BTC":
                    current_rate = self.btc_converter.get_latest_price(quote_currency)
                else:
                    current_rate = self.currency_rates.get_rate(
                        base_currency, quote_currency
                    )
            except Exception as e:
                raise APIError(f"Invalid currency pair {base_currency}/{quote_currency}: {e}")

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

