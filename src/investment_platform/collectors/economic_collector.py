"""Economic data collector using FRED API."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from investment_platform.collectors.base import (
    APIError,
    BaseDataCollector,
    ConfigurationError,
    DataCollectionError,
)
from investment_platform.config import Config


class EconomicCollector(BaseDataCollector):
    """
    Collector for economic data using FRED (Federal Reserve Economic Data) API.

    Uses the fredapi library to fetch economic indicators such as GDP,
    unemployment, inflation, interest rates, etc.
    """

    def __init__(
        self,
        output_format: str = "dataframe",
        api_key: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize the Economic data collector.

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
        Collect historical economic data for a given FRED series.

        Args:
            symbol: FRED series ID (e.g., 'GDP', 'UNRATE', 'CPIAUCSL', 'DGS10')
            start_date: Start date for data collection (ISO format string or datetime)
            end_date: End date for data collection (ISO format string or datetime)
            **kwargs: Additional parameters

        Returns:
            Historical economic data in the specified output format

        Raises:
            APIError: If data collection fails
            ValidationError: If parameters are invalid
        """
        try:
            # Validate dates
            start_dt, end_dt = self._validate_dates(start_date, end_date)

            self.logger.info(
                f"Collecting economic data for {symbol} from {start_dt} to {end_dt}"
            )

            # Fetch data from FRED
            series = self.client.get_series(
                symbol, observation_start=start_dt, observation_end=end_dt
            )

            if series.empty:
                self.logger.warning(f"No data returned for {symbol}")
                return self._format_output(pd.DataFrame())

            # Convert Series to DataFrame
            df = pd.DataFrame({symbol: series})

            # Ensure index is datetime
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            # Rename index to 'date' for consistency
            df.index.name = "date"

            # Filter out rows with NaN/null values (FRED API returns NaN for missing dates)
            # The database requires value to be NOT NULL, so we must drop these rows
            initial_count = len(df)
            df = df.dropna(subset=[symbol])
            dropped_count = initial_count - len(df)
            
            if dropped_count > 0:
                self.logger.warning(
                    f"Dropped {dropped_count} records with null/NaN values "
                    f"(out of {initial_count} total records)"
                )

            if df.empty:
                self.logger.warning(f"No valid data (after filtering nulls) for {symbol}")
                return self._format_output(pd.DataFrame())

            # Reset index to make date a column
            df = df.reset_index()

            # Validate data
            self._validate_data(df, required_columns=[symbol])

            self.logger.info(f"Successfully collected {len(df)} records for {symbol}")

            return self._format_output(df)

        except Exception as e:
            self._handle_error(e, f"collect_historical_data for {symbol}")
            raise

    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieve metadata about an economic series.

        Args:
            symbol: FRED series ID (e.g., 'GDP', 'UNRATE', 'CPIAUCSL')

        Returns:
            Dictionary containing series metadata

        Raises:
            APIError: If asset info retrieval fails
        """
        try:
            self.logger.info(f"Fetching series info for {symbol}")

            # Get series information
            info = self.client.get_series_info(symbol)

            # Check if info is valid (handle Series, dict, or None)
            if info is None:
                raise APIError(f"No information found for {symbol}")
            
            # If info is a pandas Series, check if it's empty
            if isinstance(info, pd.Series):
                if info.empty:
                    raise APIError(f"No information found for {symbol}")
                # Convert Series to dict for easier access
                info = info.to_dict()
            elif isinstance(info, dict):
                # Check if dict is empty
                if not info:
                    raise APIError(f"No information found for {symbol}")
            else:
                # Unknown type, try to proceed
                self.logger.warning(f"Unexpected info type: {type(info)}")

            # Extract relevant information
            asset_info = {
                "symbol": symbol,
                "title": info.get("title", symbol),
                "observation_start": info.get("observation_start", ""),
                "observation_end": info.get("observation_end", ""),
                "frequency": info.get("frequency", ""),
                "units": info.get("units", ""),
                "seasonal_adjustment": info.get("seasonal_adjustment", ""),
                "type": "economic_indicator",
            }

            # Add additional useful fields if available
            optional_fields = [
                "notes",
                "popularity",
                "group_popularity",
            ]

            for field in optional_fields:
                if field in info:
                    asset_info[field] = info[field]

            self.logger.info(f"Successfully retrieved series info for {symbol}")

            return asset_info

        except Exception as e:
            self._handle_error(e, f"get_asset_info for {symbol}")
            raise

    def search_series(self, search_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for FRED series by text.

        Args:
            search_text: Text to search for
            limit: Maximum number of results to return. Defaults to 10.

        Returns:
            List of dictionaries containing series information

        Raises:
            APIError: If search fails
        """
        try:
            self.logger.info(f"Searching for series: {search_text}")

            # Search for series
            results = self.client.search(search_text)

            if results.empty:
                self.logger.warning(f"No results found for: {search_text}")
                return []

            # Convert to list of dicts
            series_list = []
            for idx, row in results.head(limit).iterrows():
                series_list.append(
                    {
                        "id": row.get("id", ""),
                        "title": row.get("title", ""),
                        "observation_start": row.get("observation_start", ""),
                        "observation_end": row.get("observation_end", ""),
                        "frequency": row.get("frequency", ""),
                    }
                )

            self.logger.info(f"Found {len(series_list)} series matching: {search_text}")

            return series_list

        except Exception as e:
            self._handle_error(e, f"search_series for {search_text}")
            raise

