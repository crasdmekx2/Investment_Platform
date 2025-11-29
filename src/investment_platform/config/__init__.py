"""Configuration management module for the Investment Platform."""

import os
from pathlib import Path
from typing import Optional, Tuple

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    
    # Load .env file from project root
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, skip loading .env file
    pass

# Import ConfigurationError from base to avoid duplication
from investment_platform.collectors.base import ConfigurationError

__all__ = ["Config", "ConfigurationError"]


class Config:
    """
    Configuration manager for API keys and settings.

    Supports environment variables and provides defaults for various collectors.
    """

    # FRED API Configuration
    FRED_API_KEY: Optional[str] = os.getenv("FRED_API_KEY", None)

    # Coinbase Advanced API Configuration
    COINBASE_API_KEY: Optional[str] = os.getenv("COINBASE_API_KEY", None)
    COINBASE_API_SECRET: Optional[str] = os.getenv("COINBASE_API_SECRET", None)

    # Default settings
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "30"))
    DEFAULT_MAX_RETRIES: int = int(os.getenv("DEFAULT_MAX_RETRIES", "3"))
    DEFAULT_RATE_LIMIT_CALLS: int = int(os.getenv("DEFAULT_RATE_LIMIT_CALLS", "10"))
    DEFAULT_RATE_LIMIT_PERIOD: int = int(
        os.getenv("DEFAULT_RATE_LIMIT_PERIOD", "60")
    )

    @classmethod
    def get_fred_api_key(cls) -> Optional[str]:
        """
        Get FRED API key from environment.

        Returns:
            FRED API key or None if not set
        """
        return cls.FRED_API_KEY

    @classmethod
    def get_coinbase_credentials(cls) -> Tuple[Optional[str], Optional[str]]:
        """
        Get Coinbase API credentials from environment.

        Returns:
            Tuple of (api_key, api_secret) or (None, None) if not set
        """
        return (cls.COINBASE_API_KEY, cls.COINBASE_API_SECRET)

    @classmethod
    def validate_fred_config(cls) -> bool:
        """
        Validate that FRED API key is configured.

        Returns:
            True if FRED API key is set

        Raises:
            ConfigurationError: If FRED API key is not set
        """
        if cls.FRED_API_KEY is None:
            raise ConfigurationError(
                "FRED_API_KEY environment variable is not set. "
                "Please set it to use the EconomicCollector."
            )
        return True

    @classmethod
    def validate_coinbase_config(cls) -> bool:
        """
        Validate that Coinbase API credentials are configured.

        Returns:
            True if Coinbase credentials are set

        Raises:
            ConfigurationError: If Coinbase credentials are not set
        """
        if cls.COINBASE_API_KEY is None or cls.COINBASE_API_SECRET is None:
            raise ConfigurationError(
                "COINBASE_API_KEY and COINBASE_API_SECRET environment variables "
                "are not set. Please set them to use the CryptoCollector with "
                "Coinbase Advanced API."
            )
            return True
