"""Ingestion engine - main orchestrator for data collection and loading."""

import logging
import time
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta

import pandas as pd

from investment_platform.collectors import (
    StockCollector,
    ForexCollector,
    CryptoCollector,
    BondCollector,
    CommodityCollector,
    EconomicCollector,
    BaseDataCollector,
)
from investment_platform.ingestion.asset_manager import AssetManager
from investment_platform.ingestion.schema_mapper import SchemaMapper
from investment_platform.ingestion.incremental_tracker import IncrementalTracker
from investment_platform.ingestion.data_loader import DataLoader
from investment_platform.ingestion.db_connection import get_db_connection

logger = logging.getLogger(__name__)


class IngestionEngine:
    """Main ingestion engine that orchestrates data collection and loading."""

    # Mapping of asset types to collector classes
    COLLECTOR_MAP = {
        "stock": StockCollector,
        "forex": ForexCollector,
        "crypto": CryptoCollector,
        "bond": BondCollector,
        "commodity": CommodityCollector,
        "economic_indicator": EconomicCollector,
    }

    def __init__(
        self,
        incremental: bool = True,
        on_conflict: str = "do_nothing",
        use_copy: bool = True,
    ):
        """
        Initialize the IngestionEngine.
        
        Args:
            incremental: Whether to use incremental mode (only fetch missing data)
            on_conflict: How to handle conflicts ('do_nothing', 'update', 'skip')
            use_copy: Whether to use PostgreSQL COPY for bulk inserts
        """
        self.logger = logger
        self.incremental = incremental
        self.on_conflict = on_conflict
        self.asset_manager = AssetManager()
        self.schema_mapper = SchemaMapper()
        self.incremental_tracker = IncrementalTracker()
        self.data_loader = DataLoader(use_copy=use_copy)

    def ingest(
        self,
        symbol: str,
        asset_type: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        collector_kwargs: Optional[Dict[str, Any]] = None,
        asset_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Ingest data for a single asset.
        
        Args:
            symbol: Asset symbol
            asset_type: Type of asset (stock, forex, crypto, bond, commodity, economic_indicator)
            start_date: Start date for data collection
            end_date: End date for data collection
            collector_kwargs: Additional kwargs to pass to collector
            asset_metadata: Additional metadata for asset registration
            
        Returns:
            Dictionary with ingestion results:
                - asset_id: Asset ID
                - records_collected: Number of records collected
                - records_loaded: Number of records loaded
                - status: 'success', 'failed', or 'partial'
                - error_message: Error message if failed
                - execution_time_ms: Execution time in milliseconds
        """
        start_time = time.time()
        result = {
            "asset_id": None,
            "records_collected": 0,
            "records_loaded": 0,
            "status": "failed",
            "error_message": None,
            "execution_time_ms": 0,
        }
        
        try:
            # Convert dates to datetime if needed
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            
            self.logger.info(
                f"Starting ingestion for {symbol} ({asset_type}) "
                f"from {start_date} to {end_date}"
            )
            
            # Get or create asset
            asset_info = self._get_asset_info(symbol, asset_type, asset_metadata)
            
            # Extract core fields and metadata separately
            name = asset_info.pop("name", symbol)
            source = asset_info.pop("source", "Unknown")
            asset_info.pop("symbol", None)  # Remove symbol as it's already a parameter
            asset_info.pop("type", None)  # Remove type as it's already a parameter
            
            # Merge with provided asset_metadata
            if asset_metadata:
                asset_info.update(asset_metadata)
            
            asset_id = self.asset_manager.get_or_create_asset(
                symbol=symbol,
                asset_type=asset_type,
                name=name,
                source=source,
                **asset_info,
            )
            result["asset_id"] = asset_id
            
            # Determine date ranges to fetch
            if self.incremental:
                missing_ranges = self.incremental_tracker.calculate_missing_ranges(
                    asset_id, asset_type, start_date, end_date
                )
                
                if not missing_ranges:
                    self.logger.info(
                        f"All data already exists for {symbol}, skipping collection"
                    )
                    result["status"] = "success"
                    result["records_collected"] = 0
                    result["records_loaded"] = 0
                    return result
                
                self.logger.info(
                    f"Found {len(missing_ranges)} missing range(s) for {symbol}"
                )
            else:
                missing_ranges = [(start_date, end_date)]
            
            # Initialize collector
            collector = self._get_collector(asset_type)
            
            # Collect and load data for each range
            total_collected = 0
            total_loaded = 0
            
            for range_start, range_end in missing_ranges:
                self.logger.info(
                    f"Collecting data for {symbol} from {range_start} to {range_end}"
                )
                
                # Collect data
                collect_kwargs = collector_kwargs or {}
                data = collector.collect_historical_data(
                    symbol=symbol,
                    start_date=range_start,
                    end_date=range_end,
                    **collect_kwargs,
                )
                
                # Convert to DataFrame if needed
                if not isinstance(data, pd.DataFrame):
                    if isinstance(data, dict):
                        data = pd.DataFrame([data])
                    elif isinstance(data, list):
                        data = pd.DataFrame(data)
                    else:
                        raise ValueError(f"Unexpected data type: {type(data)}")
                
                if data.empty:
                    self.logger.warning(
                        f"No data collected for {symbol} in range {range_start} to {range_end}"
                    )
                    continue
                
                total_collected += len(data)
                
                # Map to database schema
                mapped_data = self.schema_mapper.map_data(
                    data, asset_type, asset_id
                )
                
                # Load into database
                records_loaded = self.data_loader.load_data(
                    mapped_data, asset_type, on_conflict=self.on_conflict
                )
                total_loaded += records_loaded
                
                self.logger.info(
                    f"Loaded {records_loaded} records for {symbol} "
                    f"in range {range_start} to {range_end}"
                )
            
            # Log collection run
            execution_time_ms = int((time.time() - start_time) * 1000)
            result["execution_time_ms"] = execution_time_ms
            result["records_collected"] = total_collected
            result["records_loaded"] = total_loaded
            
            if total_loaded > 0:
                result["status"] = "success" if total_loaded == total_collected else "partial"
            else:
                result["status"] = "failed"
                result["error_message"] = "No records were loaded"
            
            # Log to data_collection_log table
            self._log_collection_run(
                asset_id=asset_id,
                collector_type=collector.__class__.__name__,
                start_date=start_date,
                end_date=end_date,
                records_collected=total_collected,
                status=result["status"],
                error_message=result["error_message"],
                execution_time_ms=execution_time_ms,
            )
            
            self.logger.info(
                f"Completed ingestion for {symbol}: "
                f"{total_loaded} records loaded, status={result['status']}"
            )
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            result["execution_time_ms"] = execution_time_ms
            result["error_message"] = str(e)
            result["status"] = "failed"
            
            self.logger.error(
                f"Failed to ingest data for {symbol}: {e}", exc_info=True
            )
            
            # Log failed run
            if result["asset_id"]:
                # Ensure dates are datetime objects
                log_start_date = start_date
                log_end_date = end_date
                
                if isinstance(start_date, str):
                    log_start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                if isinstance(end_date, str):
                    log_end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                
                # Get collector class name, handling unknown asset types
                collector_class = self.COLLECTOR_MAP.get(asset_type)
                collector_type_name = collector_class.__name__ if collector_class else "Unknown"
                
                self._log_collection_run(
                    asset_id=result["asset_id"],
                    collector_type=collector_type_name,
                    start_date=log_start_date,
                    end_date=log_end_date,
                    records_collected=result["records_collected"],
                    status="failed",
                    error_message=result["error_message"],
                    execution_time_ms=execution_time_ms,
                )
        
        return result

    def _get_collector(self, asset_type: str) -> BaseDataCollector:
        """
        Get appropriate collector for asset type.
        
        Args:
            asset_type: Type of asset
            
        Returns:
            Collector instance
        """
        collector_class = self.COLLECTOR_MAP.get(asset_type)
        
        if collector_class is None:
            raise ValueError(f"Unknown asset type: {asset_type}")
        
        return collector_class(output_format="dataframe")

    def _get_asset_info(
        self,
        symbol: str,
        asset_type: str,
        asset_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get asset information from collector.
        
        Args:
            symbol: Asset symbol
            asset_type: Type of asset
            asset_metadata: Additional metadata to include
            
        Returns:
            Dictionary with asset information
        """
        try:
            collector = self._get_collector(asset_type)
            info = collector.get_asset_info(symbol)
            
            # Merge with provided metadata
            if asset_metadata:
                info.update(asset_metadata)
            
            return info
        except Exception as e:
            self.logger.warning(
                f"Could not get asset info for {symbol}: {e}. Using defaults."
            )
            # Return default info
            return {
                "name": symbol,
                "source": "Unknown",
                **(asset_metadata or {}),
            }

    def _log_collection_run(
        self,
        asset_id: int,
        collector_type: str,
        start_date: datetime,
        end_date: datetime,
        records_collected: int,
        status: str,
        error_message: Optional[str],
        execution_time_ms: int,
    ) -> None:
        """
        Log collection run to data_collection_log table.
        
        Args:
            asset_id: Asset ID
            collector_type: Collector class name
            start_date: Start date
            end_date: End date
            records_collected: Number of records collected
            status: Status ('success', 'failed', 'partial')
            error_message: Error message if any
            execution_time_ms: Execution time in milliseconds
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO data_collection_log (
                            asset_id, collector_type, start_date, end_date,
                            records_collected, status, error_message, execution_time_ms
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            asset_id,
                            collector_type,
                            start_date,
                            end_date,
                            records_collected,
                            status,
                            error_message,
                            execution_time_ms,
                        ),
                    )
                    conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to log collection run: {e}")

