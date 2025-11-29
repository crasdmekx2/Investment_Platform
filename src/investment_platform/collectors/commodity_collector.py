"""Commodity data collector using yfinance (with investpy as fallback)."""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from investment_platform.collectors.base import (
    APIError,
    BaseDataCollector,
    DataCollectionError,
    RateLimitError,
    ValidationError,
)


class CommodityCollector(BaseDataCollector):
    """
    Collector for commodity data using yfinance (primary) and investpy (fallback).

    Uses yfinance for commodity futures data, with investpy as a fallback option.
    """

    # Mapping of common commodity names to yfinance symbols
    COMMODITY_SYMBOLS = {
        "gold": "GC=F",  # Gold Futures
        "silver": "SI=F",  # Silver Futures
        "copper": "HG=F",  # Copper Futures
        "crude oil": "CL=F",  # Crude Oil Futures
        "natural gas": "NG=F",  # Natural Gas Futures
        "brent oil": "BZ=F",  # Brent Crude Oil Futures
        "wheat": "ZW=F",  # Wheat Futures
        "corn": "ZC=F",  # Corn Futures
        "soybean": "ZS=F",  # Soybean Futures
    }

    def __init__(self, output_format: str = "dataframe", **kwargs: Any):
        """
        Initialize the Commodity collector.

        Args:
            output_format: Output format ('dataframe' or 'dict'). Defaults to 'dataframe'.
            **kwargs: Additional arguments passed to BaseDataCollector
        """
        super().__init__(output_format=output_format, **kwargs)

        # Verify yfinance is available (primary source)
        try:
            import yfinance as yf

            self.yf = yf
        except ImportError:
            raise DataCollectionError(
                "yfinance library is not installed. "
                "Install it with: pip install yfinance"
            )

        # Try to load investpy as fallback (optional)
        try:
            import investpy

            self.investpy = investpy
            self.has_investpy = True
        except ImportError:
            self.has_investpy = False
            self.logger.warning(
                "investpy not available. Will use yfinance only."
            )

    def collect_historical_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        country: str = "united states",
        **kwargs: Any,
    ) -> Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Collect historical commodity data.

        Args:
            symbol: Commodity name or symbol. Common values:
                   - 'Gold', 'Silver', 'Copper', 'Crude Oil', 'Natural Gas'
                   - Or use get_available_commodities() to see all options
            start_date: Start date for data collection (ISO format string or datetime)
            end_date: End date for data collection (ISO format string or datetime)
            country: Country for commodity data. Defaults to 'united states'.
            **kwargs: Additional parameters

        Returns:
            Historical commodity data in the specified output format

        Raises:
            APIError: If data collection fails
            ValidationError: If parameters are invalid
        """
        try:
            # Validate dates
            start_dt, end_dt = self._validate_dates(start_date, end_date)

            self.logger.info(
                f"Collecting commodity data for {symbol} from {start_dt} to {end_dt}"
            )

            # Try yfinance first (more reliable)
            yf_symbol = self._get_yfinance_symbol(symbol)
            
            if yf_symbol:
                self.logger.info(f"Using yfinance for {symbol} (symbol: {yf_symbol})")
                try:
                    ticker = self.yf.Ticker(yf_symbol)
                    df = ticker.history(
                        start=start_dt,
                        end=end_dt,
                        interval="1d",
                        auto_adjust=True,
                        prepost=False,
                    )
                    
                    if not df.empty:
                        # Standardize column names
                        df.columns = [col.lower() for col in df.columns]
                        # Keep only standard columns
                        standard_columns = ["open", "high", "low", "close", "volume"]
                        available_columns = [col for col in standard_columns if col in df.columns]
                        df = df[available_columns]
                except Exception as e:
                    self.logger.warning(f"yfinance failed for {symbol}: {e}")
                    df = pd.DataFrame()
            else:
                df = pd.DataFrame()

            # Fallback to investpy if yfinance didn't work
            if df.empty and self.has_investpy:
                self.logger.info(f"Trying investpy for {symbol}")
                # Format dates for investpy (DD/MM/YYYY)
                start_str = start_dt.strftime("%d/%m/%Y")
                end_str = end_dt.strftime("%d/%m/%Y")

                # Add delay to avoid rate limiting
                time.sleep(2)

                # Fetch historical data with retry logic
                @retry(
                    stop=stop_after_attempt(2),
                    wait=wait_exponential(multiplier=3, min=10, max=60),
                    retry=retry_if_exception_type((APIError, RateLimitError, ConnectionError)),
                    reraise=True,
                )
                def _fetch_commodity_data(commodity, from_date, to_date, country_name):
                    """Internal function to fetch commodity data with retry."""
                    try:
                        return self.investpy.get_commodity_historical_data(
                            commodity=commodity,
                            from_date=from_date,
                            to_date=to_date,
                            country=country_name,
                        )
                    except ConnectionError as e:
                        error_str = str(e).lower()
                        if "403" in error_str or "rate limit" in error_str or "err#0015" in error_str:
                            raise RateLimitError(
                                f"Rate limited by Investing.com: {e}"
                            ) from e
                        raise APIError(f"Connection error fetching commodity data: {e}") from e
                    except Exception as e:
                        error_str = str(e).lower()
                        if "403" in error_str or "err#0015" in error_str:
                            raise RateLimitError(
                                f"Rate limited by Investing.com: {e}"
                            ) from e
                        raise APIError(f"Failed to fetch commodity data: {e}") from e

                try:
                    df = _fetch_commodity_data(symbol, start_str, end_str, country)
                except (RateLimitError, APIError) as e:
                    # Try with different country if default fails
                    if country.lower() != "united states":
                        self.logger.warning(
                            f"Failed with country '{country}', trying 'united states'"
                        )
                        time.sleep(3)
                        try:
                            df = _fetch_commodity_data(symbol, start_str, end_str, "united states")
                        except Exception as e2:
                            raise APIError(
                                f"Failed to fetch commodity data for {symbol}: {e2}"
                            ) from e2
                    else:
                        raise

            if df.empty:
                raise APIError(
                    f"No data returned for {symbol}. "
                    f"Try using a yfinance symbol (e.g., 'GC=F' for Gold) or check if the commodity is available."
                )

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

            df = df[available_columns]

            # Validate data
            self._validate_data(df, required_columns=["open", "high", "low", "close"])

            self.logger.info(f"Successfully collected {len(df)} records for {symbol}")

            return self._format_output(df)

        except Exception as e:
            self._handle_error(e, f"collect_historical_data for {symbol}")
            raise

    def _get_yfinance_symbol(self, symbol: str) -> Optional[str]:
        """
        Get yfinance symbol for a commodity name.
        
        Args:
            symbol: Commodity name or symbol
            
        Returns:
            yfinance symbol or None if not found
        """
        symbol_lower = symbol.lower().strip()
        
        # Check direct mapping
        if symbol_lower in self.COMMODITY_SYMBOLS:
            return self.COMMODITY_SYMBOLS[symbol_lower]
        
        # Check if it's already a yfinance symbol (ends with =F)
        if symbol.endswith("=F") or symbol.endswith("=F"):
            return symbol
        
        # Try common variations
        if "gold" in symbol_lower:
            return "GC=F"
        elif "silver" in symbol_lower:
            return "SI=F"
        elif "copper" in symbol_lower:
            return "HG=F"
        elif "oil" in symbol_lower or "crude" in symbol_lower:
            return "CL=F"
        elif "gas" in symbol_lower and "natural" in symbol_lower:
            return "NG=F"
        
        return None

    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieve metadata about a commodity.

        Args:
            symbol: Commodity name or symbol (e.g., 'Gold', 'Silver', 'Crude Oil')

        Returns:
            Dictionary containing commodity metadata

        Raises:
            APIError: If asset info retrieval fails
        """
        try:
            self.logger.info(f"Fetching commodity info for {symbol}")

            # Try yfinance first
            yf_symbol = self._get_yfinance_symbol(symbol)
            
            if yf_symbol:
                try:
                    ticker = self.yf.Ticker(yf_symbol)
                    info = ticker.info
                    
                    if info:
                        asset_info = {
                            "symbol": symbol,
                            "yfinance_symbol": yf_symbol,
                            "name": info.get("longName", info.get("shortName", symbol)),
                            "type": "commodity",
                            "source": "Yahoo Finance",
                            "exchange": info.get("exchange", ""),
                            "currency": info.get("currency", "USD"),
                        }
                        
                        # Add additional fields
                        optional_fields = [
                            "sector",
                            "industry",
                            "website",
                            "description",
                        ]
                        
                        for field in optional_fields:
                            if field in info:
                                asset_info[field] = info[field]
                        
                        self.logger.info(f"Successfully retrieved commodity info for {symbol}")
                        return asset_info
                except Exception as e:
                    self.logger.warning(f"yfinance failed for {symbol}: {e}")

            # Fallback to investpy
            if self.has_investpy:
                try:
                    info = self.investpy.get_commodity_information(
                        commodity=symbol, country="united states"
                    )
                except Exception:
                    # Try to get basic info from available commodities
                    try:
                        commodities = self.investpy.get_commodities()
                        commodity_info = commodities[
                            commodities["name"].str.lower() == symbol.lower()
                        ]

                        if commodity_info.empty:
                            raise APIError(f"Commodity '{symbol}' not found")

                        info = commodity_info.iloc[0].to_dict()
                    except Exception as e:
                        raise APIError(f"Failed to get commodity info for {symbol}: {e}")

                # Extract relevant information
                if isinstance(info, pd.DataFrame):
                    # If info is a DataFrame, convert to dict
                    if not info.empty:
                        info = info.iloc[0].to_dict()
                    else:
                        raise APIError(f"No information found for {symbol}")

                asset_info = {
                    "symbol": symbol,
                    "name": info.get("name", info.get("title", symbol)),
                    "type": "commodity",
                    "source": "Investing.com",
                }

                # Add additional fields if available
                optional_fields = [
                    "country",
                    "currency",
                    "symbol",
                    "exchange",
                ]

                for field in optional_fields:
                    if field in info:
                        asset_info[field] = info[field]

                self.logger.info(f"Successfully retrieved commodity info for {symbol}")
                return asset_info

            # If both failed
            raise APIError(
                f"Failed to get commodity info for {symbol}. "
                f"Try using a yfinance symbol (e.g., 'GC=F' for Gold)."
            )

        except Exception as e:
            self._handle_error(e, f"get_asset_info for {symbol}")
            raise

    def get_available_commodities(self, country: str = "united states") -> List[Dict[str, Any]]:
        """
        Get list of available commodities.

        Args:
            country: Country to get commodities for. Defaults to 'united states'.

        Returns:
            List of dictionaries containing available commodity information

        Raises:
            APIError: If retrieval fails
        """
        try:
            self.logger.info(f"Fetching available commodities for {country}")

            commodities = self.investpy.get_commodities(country=country)

            if commodities.empty:
                self.logger.warning(f"No commodities found for {country}")
                return []

            # Convert to list of dicts
            commodity_list = []
            for _, row in commodities.iterrows():
                commodity_list.append(
                    {
                        "name": row.get("name", ""),
                        "country": row.get("country", country),
                        "symbol": row.get("symbol", ""),
                    }
                )

            self.logger.info(
                f"Found {len(commodity_list)} available commodities for {country}"
            )

            return commodity_list

        except Exception as e:
            self._handle_error(e, f"get_available_commodities for {country}")
            raise

