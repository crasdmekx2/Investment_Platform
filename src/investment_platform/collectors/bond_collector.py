"""Bond data collector using FRED API for U.S. Treasury bond data."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from investment_platform.collectors.base import (
    APIError,
    BaseDataCollector,
    ConfigurationError,
    DataCollectionError,
    ValidationError,
)
from investment_platform.config import Config


class BondCollector(BaseDataCollector):
    """
    Collector for U.S. Treasury bond data using FRED (Federal Reserve Economic Data) API.

    Fetches Treasury bond rates and yields from FRED API using standard series IDs.
    """

    # FRED series ID mappings for different bond types
    SERIES_MAPPING = {
        "TBILLS": "TB3MS",  # 3-Month Treasury Bill
        "TREASURY_BILLS": "TB3MS",
        "TNOTES": "DGS10",  # 10-Year Treasury Note
        "TREASURY_NOTES": "DGS10",
        "TBONDS": "DGS30",  # 30-Year Treasury Bond
        "TREASURY_BONDS": "DGS30",
        "TIPS": "DFII10",  # 10-Year TIPS
    }

    def __init__(
        self,
        output_format: str = "dataframe",
        api_key: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize the Bond collector.

        Args:
            output_format: Output format ('dataframe' or 'dict'). Defaults to 'dataframe'.
            api_key: Optional FRED API key. If not provided, uses config.
            **kwargs: Additional arguments passed to BaseDataCollector

        Raises:
            ConfigurationError: If FRED API key is not configured
        """
        super().__init__(output_format=output_format, **kwargs)

        # Get API key
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = Config.get_fred_api_key()

        if not self.api_key:
            raise ConfigurationError(
                "FRED API key is required. Set FRED_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Initialize FRED client
        try:
            from fredapi import Fred

            self.client = Fred(api_key=self.api_key)
        except ImportError:
            raise DataCollectionError(
                "fredapi library is not installed. "
                "Install it with: pip install fredapi"
            )

    def collect_historical_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        **kwargs: Any,
    ) -> Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Collect historical Treasury bond data.

        Args:
            symbol: Bond type identifier. Common values:
                   - 'TREASURY_BILLS' or 'TBILLS' for Treasury Bills (3-Month)
                   - 'TREASURY_NOTES' or 'TNOTES' for Treasury Notes (10-Year)
                   - 'TREASURY_BONDS' or 'TBONDS' for Treasury Bonds (30-Year)
                   - 'TIPS' for Treasury Inflation-Protected Securities (10-Year)
                   - Or specific FRED series ID (e.g., 'DGS10', 'DGS30', 'TB3MS')
            start_date: Start date for data collection (ISO format string or datetime)
            end_date: End date for data collection (ISO format string or datetime)
            **kwargs: Additional parameters

        Returns:
            Historical bond data in the specified output format

        Raises:
            APIError: If data collection fails
            ValidationError: If parameters are invalid
        """
        try:
            # Validate dates
            start_dt, end_dt = self._validate_dates(start_date, end_date)

            self.logger.info(
                f"Collecting bond data for {symbol} from {start_dt} to {end_dt}"
            )

            # Map symbol to FRED series ID
            series_id = self.SERIES_MAPPING.get(symbol.upper(), symbol.upper())

            # Fetch data from FRED
            try:
                series = self.client.get_series(
                    series_id, observation_start=start_dt, observation_end=end_dt
                )
            except Exception as e:
                # If series ID not found, try the symbol as-is
                if series_id != symbol.upper():
                    self.logger.warning(
                        f"Series {series_id} not found, trying {symbol.upper()}"
                    )
                    series = self.client.get_series(
                        symbol.upper(), observation_start=start_dt, observation_end=end_dt
                    )
                else:
                    raise APIError(f"Failed to fetch data for {symbol}: {e}") from e

            if series.empty:
                self.logger.warning(f"No data returned for {symbol}")
                return self._format_output(pd.DataFrame())

            # Convert Series to DataFrame
            df = pd.DataFrame({"rate": series})
            df.index.name = "date"

            # Filter out rows with NaN/null rate values (FRED API returns NaN for missing dates)
            # The database requires rate to be NOT NULL, so we must drop these rows
            initial_count = len(df)
            df = df.dropna(subset=["rate"])
            dropped_count = initial_count - len(df)
            
            if dropped_count > 0:
                self.logger.warning(
                    f"Dropped {dropped_count} records with null/NaN rate values "
                    f"(out of {initial_count} total records)"
                )

            if df.empty:
                self.logger.warning(f"No valid data (after filtering nulls) for {symbol}")
                return self._format_output(pd.DataFrame())

            # Validate data
            self._validate_data(df, required_columns=["rate"])

            self.logger.info(f"Successfully collected {len(df)} records for {symbol}")

            return self._format_output(df)

        except Exception as e:
            self._handle_error(e, f"collect_historical_data for {symbol}")
            raise

    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieve metadata about a Treasury bond type.

        Args:
            symbol: Bond type identifier (e.g., 'TBILLS', 'TNOTES', 'TBONDS', 'TIPS')

        Returns:
            Dictionary containing bond type metadata

        Raises:
            APIError: If asset info retrieval fails
        """
        try:
            self.logger.info(f"Fetching bond info for {symbol}")

            # Map symbol to FRED series ID and get info
            series_id = self.SERIES_MAPPING.get(symbol.upper(), symbol.upper())

            # Get series information from FRED
            try:
                info = self.client.get_series_info(series_id)
            except Exception:
                # If series not found, try symbol as-is
                if series_id != symbol.upper():
                    info = self.client.get_series_info(symbol.upper())
                    series_id = symbol.upper()
                else:
                    raise

            # Map symbol to bond type info
            bond_info_mapping = {
                "TREASURY_BILLS": {"type": "TBILLS", "name": "3-Month Treasury Bill"},
                "TBILLS": {"type": "TBILLS", "name": "3-Month Treasury Bill"},
                "TREASURY_NOTES": {"type": "TNOTES", "name": "10-Year Treasury Note"},
                "TNOTES": {"type": "TNOTES", "name": "10-Year Treasury Note"},
                "TREASURY_BONDS": {"type": "TBONDS", "name": "30-Year Treasury Bond"},
                "TBONDS": {"type": "TBONDS", "name": "30-Year Treasury Bond"},
                "TIPS": {"type": "TIPS", "name": "10-Year Treasury Inflation-Protected Security"},
            }

            bond_info = bond_info_mapping.get(
                symbol.upper(), {"type": symbol, "name": symbol}
            )

            # Extract relevant information from FRED
            asset_info = {
                "symbol": symbol,
                "series_id": series_id,
                "security_type": bond_info["type"],
                "name": bond_info["name"],
                "title": info.get("title", bond_info["name"]),
                "issuer": "U.S. Treasury",
                "type": "bond",
                "source": "FRED API",
                "frequency": info.get("frequency", ""),
                "units": info.get("units", ""),
            }

            # Add additional useful fields if available
            optional_fields = [
                "observation_start",
                "observation_end",
                "seasonal_adjustment",
                "notes",
            ]

            for field in optional_fields:
                if field in info:
                    asset_info[field] = info[field]

            self.logger.info(f"Successfully retrieved bond info for {symbol}")

            return asset_info

        except Exception as e:
            self._handle_error(e, f"get_asset_info for {symbol}")
            raise

    def get_yield_curve(
        self, date: Optional[Union[str, datetime]] = None
    ) -> Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Get Treasury yield curve data for a specific date.

        Fetches multiple Treasury maturities to construct a yield curve.

        Args:
            date: Date for yield curve (ISO format string or datetime).
                 If None, uses most recent available date.

        Returns:
            Yield curve data in the specified output format

        Raises:
            APIError: If yield curve retrieval fails
        """
        try:
            # Common Treasury yield curve series IDs
            yield_curve_series = {
                "1M": "DGS1MO",  # 1-Month
                "3M": "TB3MS",   # 3-Month
                "6M": "DGS6MO",  # 6-Month
                "1Y": "DGS1",    # 1-Year
                "2Y": "DGS2",    # 2-Year
                "3Y": "DGS3",    # 3-Year
                "5Y": "DGS5",    # 5-Year
                "7Y": "DGS7",    # 7-Year
                "10Y": "DGS10",  # 10-Year
                "20Y": "DGS20",  # 20-Year
                "30Y": "DGS30",  # 30-Year
            }

            if date:
                date_dt = (
                    datetime.fromisoformat(date.replace("Z", "+00:00"))
                    if isinstance(date, str)
                    else date
                )
            else:
                date_dt = datetime.now()

            # Fetch data for each maturity
            yield_data = []
            for maturity, series_id in yield_curve_series.items():
                try:
                    series = self.client.get_series(
                        series_id,
                        observation_start=date_dt - pd.Timedelta(days=7),
                        observation_end=date_dt,
                    )
                    if not series.empty:
                        # Get the most recent value
                        latest_value = series.iloc[-1]
                        latest_date = series.index[-1]
                        yield_data.append(
                            {
                                "date": latest_date,
                                "maturity": maturity,
                                "series_id": series_id,
                                "yield": latest_value,
                            }
                        )
                except Exception as e:
                    self.logger.warning(f"Failed to fetch {maturity} ({series_id}): {e}")
                    continue

            if not yield_data:
                self.logger.warning("No yield curve data returned")
                return self._format_output(pd.DataFrame())

            df = pd.DataFrame(yield_data)
            df = df.set_index("date")

            self.logger.info(f"Successfully retrieved yield curve data ({len(df)} records)")

            return self._format_output(df)

        except Exception as e:
            self._handle_error(e, "get_yield_curve")
            raise

