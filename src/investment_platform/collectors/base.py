"""Abstract base class for data collectors."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from ratelimit import limits, sleep_and_retry
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from investment_platform.collectors.rate_limiter import SharedRateLimiter


class DataCollectionError(Exception):
    """Base exception for data collection errors."""

    pass


class APIError(DataCollectionError):
    """Exception raised when API calls fail."""

    pass


class RateLimitError(DataCollectionError):
    """Exception raised when rate limits are exceeded."""

    pass


class ValidationError(DataCollectionError):
    """Exception raised when data validation fails."""

    pass


class ConfigurationError(DataCollectionError):
    """Exception raised when configuration is invalid."""

    pass


class BaseDataCollector(ABC):
    """
    Abstract base class for data collectors.

    Provides common functionality including error handling, retries, rate limiting,
    logging, and data format conversion. Subclasses must implement abstract methods
    for specific data sources.

    Attributes:
        logger: Logger instance for the collector
        output_format: Desired output format ('dataframe' or 'dict')
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
        rate_limit_calls: Number of calls allowed per rate limit period
        rate_limit_period: Rate limit period in seconds
    """

    def __init__(
        self,
        output_format: str = "dataframe",
        max_retries: int = 3,
        timeout: int = 30,
        rate_limit_calls: int = 10,
        rate_limit_period: int = 60,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the base data collector.

        Args:
            output_format: Output format ('dataframe' or 'dict'). Defaults to 'dataframe'.
            max_retries: Maximum number of retry attempts. Defaults to 3.
            timeout: Request timeout in seconds. Defaults to 30.
            rate_limit_calls: Number of calls allowed per rate limit period. Defaults to 10.
            rate_limit_period: Rate limit period in seconds. Defaults to 60.
            logger: Optional logger instance. If not provided, creates a new one.
        """
        self.output_format = output_format
        self.max_retries = max_retries
        self.timeout = timeout
        self.rate_limit_calls = rate_limit_calls
        self.rate_limit_period = rate_limit_period

        # Set up logging
        if logger is None:
            self.logger = logging.getLogger(self.__class__.__name__)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
        else:
            self.logger = logger

    @abstractmethod
    def collect_historical_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        **kwargs: Any,
    ) -> Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Collect historical data for a given symbol and date range.

        Args:
            symbol: Asset symbol or identifier (e.g., ticker, pair, series ID)
            start_date: Start date for data collection (ISO format string or datetime)
            end_date: End date for data collection (ISO format string or datetime)
            **kwargs: Additional parameters specific to the collector

        Returns:
            Historical data in the specified output format (DataFrame, dict, or list)

        Raises:
            DataCollectionError: If data collection fails
        """
        pass

    @abstractmethod
    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieve metadata about the asset.

        Args:
            symbol: Asset symbol or identifier

        Returns:
            Dictionary containing asset metadata (name, type, exchange, etc.)

        Raises:
            DataCollectionError: If asset info retrieval fails
        """
        pass

    def _retry_on_failure(self, func):
        """
        Decorator for retrying functions with exponential backoff.

        Args:
            func: Function to wrap with retry logic

        Returns:
            Wrapped function with retry logic
        """

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((APIError, RateLimitError)),
            reraise=True,
        )
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    def _rate_limit(self, func):
        """
        Decorator for rate limiting function calls using shared rate limiter.

        Uses a shared rate limiter per collector class to ensure all instances
        of the same collector type share the same rate limit, preventing issues
        when multiple jobs use the same collector simultaneously.

        Args:
            func: Function to wrap with rate limiting

        Returns:
            Wrapped function with rate limiting
        """
        # Get shared rate limiter for this collector class
        collector_class_name = self.__class__.__name__
        limiter = SharedRateLimiter.get_limiter(
            collector_class_name, calls=self.rate_limit_calls, period=self.rate_limit_period
        )

        # Apply the shared rate limiter decorator
        return limiter(func)

    def _convert_to_dataframe(
        self, data: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]
    ) -> pd.DataFrame:
        """
        Convert data to pandas DataFrame format.

        Args:
            data: Data in DataFrame, dict, or list format

        Returns:
            Data as pandas DataFrame

        Raises:
            ValidationError: If data cannot be converted to DataFrame
        """
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict):
            # If dict has a single key with list values, convert to DataFrame
            if len(data) == 1:
                key = list(data.keys())[0]
                if isinstance(data[key], list):
                    return pd.DataFrame(data[key])
            # Otherwise, convert dict to DataFrame with single row
            return pd.DataFrame([data])
        elif isinstance(data, list):
            if len(data) == 0:
                return pd.DataFrame()
            if isinstance(data[0], dict):
                return pd.DataFrame(data)
            else:
                return pd.DataFrame(data)
        else:
            raise ValidationError(f"Cannot convert {type(data)} to DataFrame")

    def _convert_to_dict(
        self, data: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Convert data to dictionary format.

        Args:
            data: Data in DataFrame, dict, or list format

        Returns:
            Data as dict or list of dicts

        Raises:
            ValidationError: If data cannot be converted to dict
        """
        if isinstance(data, pd.DataFrame):
            # Convert DataFrame to list of dicts
            return data.to_dict("records")
        elif isinstance(data, dict):
            return data
        elif isinstance(data, list):
            return data
        else:
            raise ValidationError(f"Cannot convert {type(data)} to dict")

    def _format_output(
        self, data: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]
    ) -> Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Format output data according to the specified output format.

        Args:
            data: Raw data from collector

        Returns:
            Formatted data in the requested output format
        """
        if self.output_format == "dataframe":
            return self._convert_to_dataframe(data)
        elif self.output_format == "dict":
            return self._convert_to_dict(data)
        else:
            raise ConfigurationError(
                f"Invalid output_format: {self.output_format}. Must be 'dataframe' or 'dict'"
            )

    def _validate_dates(
        self, start_date: Union[str, datetime], end_date: Union[str, datetime]
    ) -> Tuple[datetime, datetime]:
        """
        Validate and convert date strings to datetime objects.

        Args:
            start_date: Start date (string or datetime)
            end_date: End date (string or datetime)

        Returns:
            Tuple of (start_date, end_date) as datetime objects

        Raises:
            ValidationError: If dates are invalid or start_date > end_date
        """
        try:
            if isinstance(start_date, str):
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            else:
                start_dt = start_date

            if isinstance(end_date, str):
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            else:
                end_dt = end_date

            if start_dt > end_dt:
                raise ValidationError(f"Start date ({start_dt}) must be before end date ({end_dt})")

            return start_dt, end_dt
        except (ValueError, AttributeError) as e:
            raise ValidationError(f"Invalid date format: {e}")

    def _validate_data(
        self,
        data: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]],
        required_columns: Optional[List[str]] = None,
    ) -> bool:
        """
        Validate collected data structure and content.

        Args:
            data: Data to validate
            required_columns: Optional list of required column names

        Returns:
            True if validation passes

        Raises:
            ValidationError: If validation fails
        """
        if data is None:
            raise ValidationError("Data is None")

        df = self._convert_to_dataframe(data)

        if df.empty:
            self.logger.warning("Collected data is empty")
            return True  # Empty data is valid, just log a warning

        if required_columns:
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                raise ValidationError(f"Missing required columns: {missing_columns}")

        # Check for all-NaN rows
        if df.isna().all(axis=1).any():
            self.logger.warning("Data contains rows with all NaN values")

        return True

    def _handle_error(self, error: Exception, context: str = "") -> None:
        """
        Handle and log errors with context.

        Args:
            error: Exception that occurred
            context: Additional context about where the error occurred
        """
        error_msg = f"Error in {self.__class__.__name__}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"

        self.logger.error(error_msg, exc_info=True)

        # Re-raise as appropriate exception type
        if isinstance(error, DataCollectionError):
            raise error
        elif "rate limit" in str(error).lower() or "429" in str(error):
            raise RateLimitError(error_msg) from error
        elif "timeout" in str(error).lower() or "408" in str(error):
            raise APIError(error_msg) from error
        else:
            raise APIError(error_msg) from error

    def _init_yfinance(self) -> Any:
        """
        Initialize yfinance library.

        Returns:
            yfinance module

        Raises:
            DataCollectionError: If yfinance is not installed
        """
        try:
            import yfinance as yf

            return yf
        except ImportError:
            raise DataCollectionError(
                "yfinance library is not installed. " "Install it with: pip install yfinance"
            )

    def _fetch_yfinance_history(
        self,
        symbol: str,
        start_dt: datetime,
        end_dt: datetime,
        interval: str = "1d",
        auto_adjust: bool = True,
        prepost: bool = False,
        actions: bool = True,
        yf: Optional[Any] = None,
    ) -> pd.DataFrame:
        """
        Fetch historical data from yfinance.

        Args:
            symbol: yfinance ticker symbol
            start_dt: Start date
            end_dt: End date
            interval: Data interval (default: '1d')
            auto_adjust: Auto-adjust prices (default: True)
            prepost: Include pre/post market data (default: False)
            actions: Include dividends and splits (default: True)
            yf: Optional yfinance module (if not provided, will initialize)

        Returns:
            DataFrame with historical data

        Raises:
            APIError: If data fetch fails
        """
        if yf is None:
            yf = self._init_yfinance()

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_dt,
                end=end_dt,
                interval=interval,
                auto_adjust=auto_adjust,
                prepost=prepost,
                actions=actions,
            )

            if df.empty:
                self.logger.warning(f"No data returned from yfinance for {symbol}")
                return pd.DataFrame()

            return df

        except Exception as e:
            raise APIError(f"Failed to fetch yfinance data for {symbol}: {e}") from e

    def _standardize_yfinance_data(
        self,
        df: pd.DataFrame,
        required_columns: Optional[List[str]] = None,
        include_optional_columns: bool = True,
    ) -> pd.DataFrame:
        """
        Standardize yfinance DataFrame format.

        This method:
        - Ensures index is DatetimeIndex
        - Converts column names to lowercase
        - Filters to standard OHLCV columns
        - Optionally includes dividends and stock splits

        Args:
            df: Raw DataFrame from yfinance
            required_columns: Optional list of required columns (default: ['open', 'high', 'low', 'close'])
            include_optional_columns: Whether to include dividends and stock splits (default: True)

        Returns:
            Standardized DataFrame
        """
        if df.empty:
            return df

        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Standardize column names to lowercase
        df.columns = [col.lower() for col in df.columns]

        # Define standard columns
        standard_columns = ["open", "high", "low", "close", "volume"]
        available_columns = [col for col in standard_columns if col in df.columns]

        # Add optional columns if requested
        if include_optional_columns:
            optional_columns = ["dividends", "stock splits"]
            for col in optional_columns:
                if col in df.columns:
                    available_columns.append(col)

        # Filter to available columns
        df = df[available_columns]

        # Validate required columns if specified
        if required_columns:
            missing = set(required_columns) - set(df.columns)
            if missing:
                self.logger.warning(
                    f"Missing required columns: {missing}. Available: {list(df.columns)}"
                )

        return df
