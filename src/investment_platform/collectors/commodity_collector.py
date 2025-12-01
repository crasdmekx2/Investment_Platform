"""Commodity data collector using yfinance."""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from investment_platform.collectors.base import (
    APIError,
    BaseDataCollector,
    DataCollectionError,
    ValidationError,
)


class CommodityCollector(BaseDataCollector):
    """
    Collector for commodity data using yfinance.

    Uses yfinance for commodity futures data.
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

        # Initialize yfinance
        self.yf = self._init_yfinance()

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
            symbol: Commodity name or yfinance symbol. Common values:
                   - 'Gold', 'Silver', 'Copper', 'Crude Oil', 'Natural Gas'
                   - Or yfinance symbols like 'GC=F', 'SI=F', 'CL=F', etc.
            start_date: Start date for data collection (ISO format string or datetime)
            end_date: End date for data collection (ISO format string or datetime)
            country: Country for commodity data (deprecated, kept for compatibility). Defaults to 'united states'.
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

            # Get yfinance symbol
            yf_symbol = self._get_yfinance_symbol(symbol)
            
            if not yf_symbol:
                raise APIError(
                    f"Could not determine yfinance symbol for {symbol}. "
                    f"Try using a yfinance symbol directly (e.g., 'GC=F' for Gold) or a recognized commodity name."
                )
            
            self.logger.info(f"Using yfinance for {symbol} (symbol: {yf_symbol})")
            
            # Fetch historical data using shared method
            df = self._fetch_yfinance_history(
                symbol=yf_symbol,
                start_dt=start_dt,
                end_dt=end_dt,
                interval="1d",
                auto_adjust=True,
                prepost=False,
                actions=False,
                yf=self.yf,
            )
            
            if df.empty:
                raise APIError(
                    f"No data returned for {symbol} (yfinance symbol: {yf_symbol}). "
                    f"This may indicate the symbol is invalid or no data exists for the date range."
                )
            
            # Standardize data using shared method
            df = self._standardize_yfinance_data(
                df=df,
                required_columns=["open", "high", "low", "close"],
                include_optional_columns=False,
            )

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

            # Get yfinance symbol
            yf_symbol = self._get_yfinance_symbol(symbol)
            
            if not yf_symbol:
                raise APIError(
                    f"Could not determine yfinance symbol for {symbol}. "
                    f"Try using a yfinance symbol directly (e.g., 'GC=F' for Gold) or a recognized commodity name."
                )
            
            try:
                ticker = self.yf.Ticker(yf_symbol)
                info = ticker.info
                
                if not info:
                    raise APIError(f"No information available for {symbol} (yfinance symbol: {yf_symbol})")
                
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
                raise APIError(
                    f"Failed to get commodity info for {symbol} (yfinance symbol: {yf_symbol}): {e}"
                ) from e

        except Exception as e:
            self._handle_error(e, f"get_asset_info for {symbol}")
            raise

    def get_available_commodities(self, country: str = "united states") -> List[Dict[str, Any]]:
        """
        Get list of available commodities (yfinance symbols).

        Args:
            country: Country parameter (deprecated, kept for compatibility). Defaults to 'united states'.

        Returns:
            List of dictionaries containing available commodity information with yfinance symbols

        Raises:
            APIError: If retrieval fails
        """
        try:
            self.logger.info("Fetching available commodities (yfinance symbols)")

            # Return the predefined commodity symbols
            commodity_list = []
            for name, yf_symbol in self.COMMODITY_SYMBOLS.items():
                commodity_list.append(
                    {
                        "name": name,
                        "symbol": yf_symbol,
                        "yfinance_symbol": yf_symbol,
                        "source": "Yahoo Finance",
                    }
                )

            self.logger.info(
                f"Found {len(commodity_list)} available commodities"
            )

            return commodity_list

        except Exception as e:
            self._handle_error(e, f"get_available_commodities")
            raise

