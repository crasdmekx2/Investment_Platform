"""Asset management for ingestion - handles asset registration and metadata."""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import psycopg2.extras

from investment_platform.ingestion.db_connection import get_db_connection

logger = logging.getLogger(__name__)


class AssetManager:
    """Manages asset registration and metadata in the assets table."""

    def __init__(self):
        """Initialize the AssetManager."""
        self.logger = logger

    def get_or_create_asset(
        self,
        symbol: str,
        asset_type: str,
        name: str,
        source: str,
        **kwargs: Any,
    ) -> int:
        """
        Get existing asset or create a new one.

        Args:
            symbol: Asset symbol (unique identifier)
            asset_type: Type of asset (stock, forex, crypto, bond, commodity, economic_indicator)
            name: Asset name
            source: Data source (e.g., 'Yahoo Finance', 'FRED', 'Coinbase')
            **kwargs: Additional asset metadata fields:
                - exchange: Exchange name
                - currency: ISO currency code
                - sector: Business sector (for stocks)
                - industry: Industry classification (for stocks)
                - base_currency: Base currency (for forex/crypto)
                - quote_currency: Quote currency (for forex/crypto)
                - series_id: FRED series ID (for bonds/economic indicators)
                - security_type: Security type (for bonds)
                - metadata: JSONB metadata dictionary

        Returns:
            asset_id: The asset ID (existing or newly created)
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Check if asset exists
                cursor.execute(
                    "SELECT asset_id FROM assets WHERE symbol = %s",
                    (symbol,),
                )
                result = cursor.fetchone()

                if result:
                    asset_id = result[0]
                    self.logger.debug(f"Asset {symbol} already exists with asset_id={asset_id}")

                    # Update asset metadata if provided
                    if kwargs:
                        self._update_asset_metadata(cursor, asset_id, **kwargs)
                        conn.commit()

                    return asset_id

                # Create new asset
                fields = ["symbol", "asset_type", "name", "source"]
                values = [symbol, asset_type, name, source]
                placeholders = ["%s"] * len(fields)

                # Add optional fields
                optional_fields = [
                    "exchange",
                    "currency",
                    "sector",
                    "industry",
                    "base_currency",
                    "quote_currency",
                    "series_id",
                    "security_type",
                ]

                metadata = kwargs.pop("metadata", None)

                for field in optional_fields:
                    if field in kwargs:
                        fields.append(field)
                        values.append(kwargs[field])
                        placeholders.append("%s")

                # Add any remaining kwargs to metadata
                if kwargs:
                    if metadata is None:
                        metadata = {}
                    else:
                        metadata = dict(metadata) if isinstance(metadata, dict) else {}

                    # Merge remaining kwargs into metadata
                    metadata.update(kwargs)

                # Add metadata as JSONB if we have any
                if metadata:
                    fields.append("metadata")
                    values.append(psycopg2.extras.Json(metadata))
                    placeholders.append("%s::jsonb")

                query = f"""
                    INSERT INTO assets ({', '.join(fields)})
                    VALUES ({', '.join(placeholders)})
                    RETURNING asset_id;
                """

                cursor.execute(query, tuple(values))
                asset_id = cursor.fetchone()[0]
                conn.commit()

                self.logger.info(
                    f"Created new asset: {symbol} (asset_id={asset_id}, type={asset_type})"
                )

                return asset_id

    def _update_asset_metadata(self, cursor, asset_id: int, **kwargs: Any) -> None:
        """
        Update asset metadata fields.

        Args:
            cursor: Database cursor
            asset_id: Asset ID to update
            **kwargs: Fields to update
        """
        if not kwargs:
            return

        # Separate regular fields from metadata
        regular_fields = [
            "exchange",
            "currency",
            "sector",
            "industry",
            "base_currency",
            "quote_currency",
            "series_id",
            "security_type",
        ]

        updates = []
        values = []

        # Handle regular fields
        for field in regular_fields:
            if field in kwargs:
                updates.append(f"{field} = %s")
                values.append(kwargs.pop(field))

        # Handle metadata
        if kwargs:
            # Get existing metadata
            cursor.execute(
                "SELECT metadata FROM assets WHERE asset_id = %s",
                (asset_id,),
            )
            result = cursor.fetchone()
            existing_metadata = result[0] if result and result[0] else {}

            # Merge with new metadata
            if isinstance(existing_metadata, dict):
                existing_metadata.update(kwargs)
            else:
                existing_metadata = kwargs

            updates.append("metadata = %s::jsonb")
            values.append(psycopg2.extras.Json(existing_metadata))

        # Always update updated_at
        updates.append("updated_at = NOW()")

        if updates:
            query = f"""
                UPDATE assets
                SET {', '.join(updates)}
                WHERE asset_id = %s
            """
            values.append(asset_id)
            cursor.execute(query, tuple(values))

            self.logger.debug(f"Updated metadata for asset_id={asset_id}")

    def get_asset_id(self, symbol: str) -> Optional[int]:
        """
        Get asset ID by symbol.

        Args:
            symbol: Asset symbol

        Returns:
            asset_id if found, None otherwise
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT asset_id FROM assets WHERE symbol = %s AND is_active = TRUE",
                    (symbol,),
                )
                result = cursor.fetchone()
                return result[0] if result else None

    def get_asset_info(self, asset_id: int) -> Optional[Dict[str, Any]]:
        """
        Get asset information by asset_id.

        Args:
            asset_id: Asset ID

        Returns:
            Dictionary with asset information or None if not found
        """
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT 
                        asset_id, symbol, asset_type, name, exchange, currency,
                        sector, industry, base_currency, quote_currency,
                        series_id, security_type, source, metadata, is_active,
                        created_at, updated_at
                    FROM assets
                    WHERE asset_id = %s
                    """,
                    (asset_id,),
                )
                result = cursor.fetchone()

                if not result:
                    return None

                columns = [
                    "asset_id",
                    "symbol",
                    "asset_type",
                    "name",
                    "exchange",
                    "currency",
                    "sector",
                    "industry",
                    "base_currency",
                    "quote_currency",
                    "series_id",
                    "security_type",
                    "source",
                    "metadata",
                    "is_active",
                    "created_at",
                    "updated_at",
                ]

                return dict(zip(columns, result))
