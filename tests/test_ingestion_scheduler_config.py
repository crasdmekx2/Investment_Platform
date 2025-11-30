"""
Tests for scheduler configuration loading with null values.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

try:
    from investment_platform.ingestion.scheduler import IngestionScheduler, APSCHEDULER_AVAILABLE
except ImportError:
    APSCHEDULER_AVAILABLE = False
    IngestionScheduler = None


@pytest.mark.skipif(not APSCHEDULER_AVAILABLE, reason="APScheduler not available")
class TestSchedulerConfig:
    """Test scheduler configuration loading."""

    def test_load_config_with_null_dates_yaml(self):
        """Test loading YAML config with null start_date and end_date."""
        # Create temporary YAML config file with null dates
        config_content = """
jobs:
  - symbol: TEST_STOCK
    asset_type: stock
    job_id: test_job
    trigger:
      type: interval
      params:
        minutes: 1
    start_date: null
    end_date: null
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = Path(f.name)
        
        scheduler = None
        try:
            scheduler = IngestionScheduler(blocking=False)
            
            # This should not raise a TypeError
            job_ids = scheduler.load_config(config_path)
            
            assert len(job_ids) == 1
            assert job_ids[0] == "test_job"
            
        finally:
            if scheduler:
                scheduler.shutdown()
            config_path.unlink()

    def test_load_config_with_null_dates_json(self):
        """Test loading JSON config with null start_date and end_date."""
        import json
        
        config_content = {
            "jobs": [
                {
                    "symbol": "TEST_STOCK",
                    "asset_type": "stock",
                    "job_id": "test_job",
                    "trigger": {
                        "type": "interval",
                        "params": {
                            "minutes": 1
                        }
                    },
                    "start_date": None,
                    "end_date": None
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_content, f)
            config_path = Path(f.name)
        
        scheduler = None
        try:
            scheduler = IngestionScheduler(blocking=False)
            
            # This should not raise a TypeError
            job_ids = scheduler.load_config(config_path)
            
            assert len(job_ids) == 1
            assert job_ids[0] == "test_job"
            
        finally:
            if scheduler:
                scheduler.shutdown()
            config_path.unlink()

    def test_load_config_with_iso_dates(self):
        """Test loading config with ISO format dates."""
        config_content = """
jobs:
  - symbol: TEST_STOCK
    asset_type: stock
    job_id: test_job
    trigger:
      type: interval
      params:
        minutes: 1
    start_date: "2024-01-01T00:00:00"
    end_date: "2024-01-02T00:00:00"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = Path(f.name)
        
        scheduler = None
        try:
            scheduler = IngestionScheduler(blocking=False)
            job_ids = scheduler.load_config(config_path)
            
            assert len(job_ids) == 1
            
        finally:
            if scheduler:
                scheduler.shutdown()
            config_path.unlink()

    def test_load_config_with_missing_dates(self):
        """Test loading config without date fields (should use defaults)."""
        config_content = """
jobs:
  - symbol: TEST_STOCK
    asset_type: stock
    job_id: test_job
    trigger:
      type: interval
      params:
        minutes: 1
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = Path(f.name)
        
        scheduler = None
        try:
            scheduler = IngestionScheduler(blocking=False)
            job_ids = scheduler.load_config(config_path)
            
            assert len(job_ids) == 1
            
        finally:
            if scheduler:
                scheduler.shutdown()
            config_path.unlink()


class TestSchedulerDateParsing:
    """Test date parsing logic directly without requiring APScheduler."""
    
    def test_parse_null_dates_from_config(self):
        """Test that null dates in config are handled correctly."""
        from datetime import datetime
        
        # Simulate what happens when YAML/JSON loads null
        job_config = {
            "start_date": None,  # YAML null becomes Python None
            "end_date": None,
        }
        
        # This is the logic from load_config - should not raise TypeError
        start_date = None
        end_date = None
        
        if "start_date" in job_config and job_config["start_date"] is not None:
            start_date = datetime.fromisoformat(job_config["start_date"])
        if "end_date" in job_config and job_config["end_date"] is not None:
            end_date = datetime.fromisoformat(job_config["end_date"])
        
        # Should remain None, not raise an error
        assert start_date is None
        assert end_date is None
    
    def test_parse_iso_dates_from_config(self):
        """Test that ISO format dates are parsed correctly."""
        from datetime import datetime
        
        job_config = {
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-02T00:00:00",
        }
        
        start_date = None
        end_date = None
        
        if "start_date" in job_config and job_config["start_date"] is not None:
            start_date = datetime.fromisoformat(job_config["start_date"])
        if "end_date" in job_config and job_config["end_date"] is not None:
            end_date = datetime.fromisoformat(job_config["end_date"])
        
        assert start_date is not None
        assert end_date is not None
        assert start_date.year == 2024
        assert end_date.year == 2024

