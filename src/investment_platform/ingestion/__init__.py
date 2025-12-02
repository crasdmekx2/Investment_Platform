"""Data ingestion module for the Investment Platform."""

from investment_platform.ingestion.db_connection import get_db_connection
from investment_platform.ingestion.asset_manager import AssetManager
from investment_platform.ingestion.schema_mapper import SchemaMapper
from investment_platform.ingestion.incremental_tracker import IncrementalTracker
from investment_platform.ingestion.data_loader import DataLoader
from investment_platform.ingestion.ingestion_engine import IngestionEngine
from investment_platform.ingestion.scheduler import IngestionScheduler

__all__ = [
    "get_db_connection",
    "AssetManager",
    "SchemaMapper",
    "IncrementalTracker",
    "DataLoader",
    "IngestionEngine",
    "IngestionScheduler",
]
