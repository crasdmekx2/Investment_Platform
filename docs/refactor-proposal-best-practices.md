# Best Practices Refactor Proposal
## Investment Platform - Full Stack Development Review

**Document Version:** 3.0  
**Date:** 2024-12-01  
**Author:** Full Stack Engineering Team  
**Status:** Proposal for Execution  
**Last Updated:** Comprehensive codebase review including OOP standards analysis completed

---

## Executive Summary

This document outlines a comprehensive refactoring proposal to address best practice violations identified throughout the Investment Platform codebase. The review identified multiple areas where hard-coded values, magic numbers, configuration management issues, code duplication, and security vulnerabilities create maintenance challenges and reduce system flexibility and security.

**Key Findings:**
- 13 major issue categories identified
- Security vulnerabilities (CORS, SQL injection risks, hard-coded credentials)
- Extensive hard-coded asset symbols and configuration values
- Code duplication across multiple modules
- Missing input validation in some areas
- Object-oriented programming standards violations (encapsulation, SOLID principles, design patterns)

**Priority:** High  
**Estimated Effort:** 4-5 weeks  
**Risk Level:** Medium (requires careful testing)

---

## Table of Contents

1. [Issues Identified](#issues-identified)
2. [Refactoring Strategy](#refactoring-strategy)
3. [Detailed Refactoring Plan](#detailed-refactoring-plan)
4. [Implementation Phases](#implementation-phases)
5. [Testing Strategy](#testing-strategy)
6. [Migration Plan](#migration-plan)
7. [Success Criteria](#success-criteria)

---

## Issues Identified

### 1. Hard-Coded Asset Symbols ⚠️ **CRITICAL**

**Problem:** Asset symbols are hard-coded throughout the codebase in multiple locations, making it difficult to:
- Add new assets without code changes
- Maintain a consistent asset registry
- Support dynamic asset discovery
- Test with different asset sets

**Locations Found:**
- `src/investment_platform/api/services/collector_service.py` (lines 154-227)
  - Hard-coded stock symbols: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA, JPM, V, JNJ
  - Hard-coded crypto pairs: BTC-USD, ETH-USD, BNB-USD, SOL-USD, etc.
  - Hard-coded forex pairs: USD_EUR, USD_GBP, USD_JPY, etc.
  - Hard-coded bond series: TB3MS, DGS10, DGS30, DFII10
  - Hard-coded commodities: GC=F, SI=F, CL=F, NG=F, etc.
  - Hard-coded economic indicators: GDP, UNRATE, CPIAUCSL, DGS10, FEDFUNDS, INDPRO

- `src/investment_platform/collectors/commodity_collector.py` (lines 24-34)
  - `COMMODITY_SYMBOLS` dictionary with hard-coded mappings

- `src/investment_platform/collectors/bond_collector.py` (lines 26-34, 268-280)
  - `SERIES_MAPPING` dictionary
  - `yield_curve_series` dictionary

- Test files (multiple locations)
  - Hard-coded symbols in test fixtures and test cases

- Frontend test fixtures
  - `frontend/src/test/fixtures/marketData.ts` contains hard-coded symbols

**Impact:**
- **Maintainability:** Adding new assets requires code changes
- **Scalability:** Cannot dynamically discover or add assets
- **Testing:** Difficult to test with different asset sets
- **Consistency:** Risk of symbol mismatches across components

---

### 2. Hard-Coded Currency Defaults ⚠️ **HIGH**

**Problem:** Default currency values are hard-coded as "USD" in multiple locations.

**Locations Found:**
- `src/investment_platform/collectors/stock_collector.py` (line 141)
  - `"currency": info.get("currency", "USD")`
- `src/investment_platform/collectors/commodity_collector.py` (line 205)
  - `"currency": info.get("currency", "USD")`
- `src/investment_platform/ingestion/schema_mapper.py` (multiple locations)
- Test fixtures and sample data

**Impact:**
- Assumes USD for all assets, which may not be accurate
- Difficult to support multi-currency portfolios
- May cause data quality issues for non-USD assets

---

### 3. Hard-Coded Configuration Values ⚠️ **HIGH**

**Problem:** Timeouts, retries, intervals, and other configuration values are hard-coded throughout the codebase.

**Locations Found:**

**Timeouts:**
- `test_scheduler_api_comprehensive.py`: Multiple hard-coded timeouts (10, 30, 60, 90, 180 seconds)
- `src/investment_platform/ingestion/ingestion_engine.py` (line 188): `timeout=300.0`
- `run_scheduler_api_tests_cycle.py`: `max_wait = 120`

**Intervals/Granularities:**
- `src/investment_platform/api/services/collector_service.py` (lines 40-43, 52-59, 83-86)
  - Hard-coded interval lists: `["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]`
  - Hard-coded granularities: `["ONE_MINUTE", "FIVE_MINUTE", "FIFTEEN_MINUTE", "ONE_HOUR", "SIX_HOUR", "ONE_DAY"]`
- `src/investment_platform/collectors/forex_collector.py` (lines 146, 262, 351, 365): `interval='1d'`
- `src/investment_platform/collectors/commodity_collector.py` (line 101): `interval="1d"`

**Retry Configuration:**
- `src/investment_platform/config/__init__.py` (lines 40-45)
  - Defaults exist but are not consistently used
  - Some code uses hard-coded values instead

**Database Configuration:**
- `docker-compose.yml`: Hard-coded database credentials
- `src/investment_platform/ingestion/db_connection.py` (lines 26-30): Default values in code

**Impact:**
- Cannot adjust behavior without code changes
- Difficult to optimize for different environments
- Testing requires code modifications
- Inconsistent behavior across components

---

### 4. Magic Numbers ⚠️ **MEDIUM**

**Problem:** Numeric literals used without named constants or configuration.

**Examples Found:**
- Date buffer calculations: `timedelta(days=1)`, `timedelta(days=2)`, `timedelta(days=7)`
- Rate limit values: `calls=5, period=10`
- Pagination limits: `limit=50`, `limit=100`
- Health check intervals: `interval=30s`, `timeout=10s`
- Connection pool sizes: `min_conn: int = 1, max_conn: int = 10`

**Impact:**
- Unclear intent behind numeric values
- Difficult to maintain and adjust
- Risk of inconsistent values across codebase

---

### 5. Code Duplication ⚠️ **MEDIUM**

**Problem:** Similar logic repeated across multiple files.

**Examples:**
- Asset symbol lists duplicated in `collector_service.py` and individual collectors
- Date validation and formatting logic repeated
- Error handling patterns duplicated
- Database connection logic could be more centralized

**Impact:**
- Maintenance burden (changes must be made in multiple places)
- Risk of inconsistencies
- Increased code size

---

### 6. Configuration Management Issues ⚠️ **MEDIUM**

**Problem:** Inconsistent configuration management approach.

**Issues:**
- Some configuration in `Config` class, some in environment variables, some hard-coded
- No centralized configuration validation
- Missing configuration for many values that should be configurable
- No configuration schema or documentation

**Impact:**
- Difficult to understand what can be configured
- Risk of misconfiguration
- Inconsistent behavior across environments

---

### 7. Error Handling Patterns ⚠️ **LOW-MEDIUM**

**Problem:** Some inconsistencies in error handling.

**Issues:**
- Some functions catch generic `Exception` without specific handling
- Error messages sometimes lack context
- Some error handling could be more specific

**Note:** Overall error handling is reasonable, but could be more consistent.

---

### 8. Security Issues ⚠️ **CRITICAL**

**Problem:** Several security vulnerabilities and poor security practices identified.

**Locations Found:**

**CORS Configuration:**
- `src/investment_platform/api/main.py` (line 93)
  - `allow_origins=["*"]` - Allows all origins (security risk in production)
  - Should be restricted to specific domains

**Hard-Coded Database Credentials:**
- `scripts/execute_functions.py` (lines 8-14)
  - Hard-coded database connection with credentials
- `scripts/execute_schema.py` (similar pattern)
  - Should use environment variables or configuration

**SQL Injection Risks:**
- `src/investment_platform/ingestion/data_loader.py` (multiple locations)
  - Uses f-strings for table names and column names in SQL queries
  - While table/column names are controlled, this is still a risk
  - Should use parameterized queries or whitelisting
  - Examples: lines 108, 119, 147, 175, 196, 351, 366, 374

**Error Message Exposure:**
- Some error messages may expose internal details
- Should sanitize error messages before returning to clients

**Impact:**
- **Security Risk:** CORS allows any origin to access API
- **Data Exposure:** Hard-coded credentials could be exposed
- **SQL Injection:** Potential vulnerability if table/column names become user-controlled
- **Information Disclosure:** Error messages may reveal system internals

---

### 9. Code Duplication ⚠️ **MEDIUM**

**Problem:** Significant code duplication across multiple files.

**Locations Found:**

**Asset Type to Table Mapping:**
- `src/investment_platform/ingestion/schema_mapper.py` (lines 16-23)
  - `ASSET_TYPE_TO_TABLE` dictionary
- `src/investment_platform/ingestion/data_loader.py` (lines 18-25)
  - Identical `ASSET_TYPE_TO_TABLE` dictionary
- Should be centralized in a single location

**Date Validation Logic:**
- Repeated date parsing and validation in multiple collectors
- Similar patterns in `ingestion_engine.py` and collectors

**Error Classification:**
- Error indicator lists in `error_classifier.py` are hard-coded
- Could be configurable

**Impact:**
- **Maintainability:** Changes must be made in multiple places
- **Consistency Risk:** Mappings may become out of sync
- **Code Size:** Increased codebase size

---

### 10. Missing Input Validation ⚠️ **MEDIUM**

**Problem:** Some API endpoints and functions lack comprehensive input validation.

**Locations Found:**

**API Endpoints:**
- Some endpoints accept user input without sufficient validation
- Symbol validation could be more strict (e.g., SQL injection prevention)
- Date range validation could be more comprehensive

**Collector Parameters:**
- Collector kwargs are not fully validated in all cases
- Some parameters may accept invalid values

**Impact:**
- **Security:** Potential for invalid input to cause errors
- **Data Quality:** Invalid data may be stored
- **User Experience:** Poor error messages for invalid input

---

### 11. Hard-Coded Retry Configuration ⚠️ **MEDIUM**

**Problem:** Retry logic uses hard-coded values.

**Locations Found:**
- `src/investment_platform/collectors/base.py` (lines 159-163)
  - `stop_after_attempt(3)` - hard-coded retry count
  - `wait_exponential(multiplier=1, min=2, max=10)` - hard-coded wait times
  - Should use Config values

**Impact:**
- Cannot adjust retry behavior without code changes
- Inconsistent with other configuration management

---

### 12. Connection Pool Hard-Coding ⚠️ **MEDIUM**

**Problem:** Database connection pool sizes are hard-coded.

**Locations Found:**
- `src/investment_platform/api/main.py` (line 31)
  - `initialize_connection_pool(min_conn=2, max_conn=20)` - hard-coded values
- `src/investment_platform/ingestion/db_connection.py` (line 34)
  - Default values in function signature

**Impact:**
- Cannot optimize connection pool for different environments
- May cause connection issues under load

---

### 13. Object-Oriented Programming Standards ⚠️ **MEDIUM-HIGH**

**Problem:** Multiple violations of OOP principles and best practices.

**Issues Found:**

#### 13.1 Encapsulation Violations

**Problem:** All class attributes are public with no encapsulation.

**Locations:**
- `src/investment_platform/collectors/base.py`
  - All attributes public: `self.output_format`, `self.max_retries`, `self.timeout`, etc.
  - No properties for getters/setters
  - No private/protected attributes (no `_` prefix convention)
- `src/investment_platform/ingestion/ingestion_engine.py`
  - Public attributes: `self.incremental`, `self.on_conflict`, `self.asset_manager`, etc.
- All collector classes and service classes

**Impact:**
- No control over attribute access/modification
- Cannot add validation or side effects when attributes change
- Difficult to maintain invariants
- Poor API design (exposes implementation details)

#### 13.2 Missing Dunder Methods

**Problem:** Classes lack standard Python dunder methods for proper object behavior.

**Locations:**
- All collector classes - no `__str__` or `__repr__`
- All service classes - no string representation
- No `__eq__` methods for value comparison
- No `__hash__` methods for use in sets/dictionaries

**Impact:**
- Poor debugging experience (can't easily inspect objects)
- Cannot compare objects for equality
- Cannot use objects as dictionary keys or in sets
- Objects print as `<ClassName object at 0x...>`

#### 13.3 Functional vs Object-Oriented Design

**Problem:** Many functions should be class methods or part of classes.

**Locations:**
- `src/investment_platform/api/services/collector_service.py`
  - `get_collector_metadata()` - should be a class method or instance method
  - `search_assets()` - should be part of a service class
  - `validate_collection_params()` - should be part of a validator class
- `src/investment_platform/ingestion/error_classifier.py`
  - `classify_error()` - should be a class method or part of an ErrorClassifier class
- Global functions instead of organized class methods

**Impact:**
- Poor code organization
- Difficult to test (no dependency injection)
- No state management
- Harder to extend or override behavior

#### 13.4 SOLID Principle Violations

**Single Responsibility Principle (SRP):**
- `IngestionEngine` class does too many things:
  - Asset management
  - Data collection
  - Schema mapping
  - Data loading
  - Logging
  - Error handling
- Should be split into smaller, focused classes

**Open/Closed Principle (OCP):**
- Hard-coded collector mappings in multiple places
- `COLLECTOR_MAP` dictionaries hard-coded
- Cannot extend without modifying existing code

**Dependency Inversion Principle (DIP):**
- Direct dependencies on concrete classes
- No interfaces/protocols
- `IngestionEngine` directly imports concrete collectors
- `RequestCoordinator` directly imports concrete collectors

**Liskov Substitution Principle (LSP):**
- Generally followed (collectors properly inherit from BaseDataCollector)
- But some inconsistencies in method signatures

#### 13.5 Missing Design Patterns

**Problem:** Common design patterns are not used where appropriate.

**Missing Patterns:**
- **Factory Pattern:** No factory for creating collectors
- **Dependency Injection:** Direct instantiation everywhere
- **Singleton Pattern:** Config class uses class methods but not true singleton
- **Strategy Pattern:** Could be used for different data loading strategies
- **Repository Pattern:** Database access scattered, not centralized

**Locations:**
- Collector instantiation scattered across codebase
- No centralized factory for collectors
- Direct database access in multiple classes
- Global state management (singleton-like but not proper singleton)

#### 13.6 Class Design Issues

**Problem:** Several class design problems identified.

**Issues:**
- **No Interfaces/Protocols:** No use of `typing.Protocol` for interfaces
- **Class Variables vs Instance Variables:** Some confusion (e.g., `COLLECTOR_MAP` as class variable)
- **No Abstract Properties:** Only abstract methods, no abstract properties
- **Missing Type Hints:** Some methods lack proper type hints
- **No Class Documentation:** Some classes lack comprehensive docstrings

**Impact:**
- Difficult to create test doubles/mocks
- No clear contracts for classes
- Harder to understand class responsibilities
- Poor IDE support and type checking

#### 13.7 Global State Management

**Problem:** Use of global variables and singleton-like patterns.

**Locations:**
- `src/investment_platform/ingestion/request_coordinator.py`
  - Global `_coordinator` variable
  - `get_coordinator()` function (singleton-like)
- `src/investment_platform/ingestion/db_connection.py`
  - Global `_connection_pool` variable
- `src/investment_platform/collectors/rate_limiter.py`
  - Class-level `_limiters` dictionary

**Impact:**
- Difficult to test (global state)
- Cannot have multiple instances
- Thread safety concerns
- Harder to manage lifecycle

**Impact Summary:**
- **Maintainability:** Poor encapsulation makes changes risky
- **Testability:** Hard to test due to global state and direct dependencies
- **Extensibility:** Hard to extend without modifying existing code
- **Code Quality:** Violates multiple OOP principles
- **Debugging:** Poor object representation makes debugging harder

---

## Refactoring Strategy

### Principles

1. **Configuration Over Code:** Move hard-coded values to configuration
2. **Single Source of Truth:** Centralize asset definitions and constants
3. **Database-Driven Assets:** Store asset metadata in database
4. **Environment-Aware:** Support different configurations per environment
5. **Backward Compatible:** Maintain API compatibility during migration
6. **Testable:** Make it easy to test with different configurations

### Approach

1. **Phase 1:** Create configuration infrastructure
2. **Phase 2:** Migrate hard-coded values to configuration
3. **Phase 3:** Implement database-driven asset registry
4. **Phase 4:** Update all consumers to use new system
5. **Phase 5:** Remove old hard-coded values

---

## Detailed Refactoring Plan

### 1. Asset Symbol Management

#### 1.1 Create Asset Registry Service

**New File:** `src/investment_platform/services/asset_registry.py`

```python
"""
Asset Registry Service

Provides centralized asset symbol and metadata management.
Supports both database-backed and configuration-based asset definitions.
"""

from typing import Dict, List, Optional, Any
from investment_platform.ingestion.db_connection import get_db_connection
from investment_platform.config import Config

class AssetRegistry:
    """
    Centralized asset registry service.
    
    Provides asset lookup, search, and metadata retrieval.
    Assets are primarily stored in the database 'assets' table,
    with fallback to configuration for common assets.
    """
    
    # Cache for asset metadata
    _cache: Dict[str, Dict[str, Any]] = {}
    _cache_ttl: int = 3600  # 1 hour
    
    @classmethod
    def get_asset(cls, symbol: str, asset_type: str) -> Optional[Dict[str, Any]]:
        """Get asset metadata from database or cache."""
        # Implementation: Query database, use cache, fallback to config
        pass
    
    @classmethod
    def search_assets(
        cls, 
        asset_type: str, 
        query: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search assets by type and query string."""
        # Implementation: Query database with LIKE/ILIKE, return results
        pass
    
    @classmethod
    def get_common_assets(cls, asset_type: str) -> List[Dict[str, Any]]:
        """Get list of common/popular assets for a type."""
        # Implementation: Query database for commonly used assets
        pass
```

#### 1.2 Create Asset Configuration File

**New File:** `config/assets.yaml`

```yaml
# Asset Configuration
# This file provides default/common assets that are seeded into the database.
# In production, assets should primarily come from the database.

common_assets:
  stock:
    - symbol: AAPL
      name: Apple Inc.
      exchange: NASDAQ
      currency: USD
      sector: Technology
      is_active: true
    - symbol: MSFT
      name: Microsoft Corporation
      exchange: NASDAQ
      currency: USD
      sector: Technology
      is_active: true
    # ... more stocks

  crypto:
    - symbol: BTC-USD
      name: Bitcoin / US Dollar
      base_currency: BTC
      quote_currency: USD
      is_active: true
    # ... more crypto pairs

  forex:
    - symbol: USD_EUR
      name: US Dollar / Euro
      base_currency: USD
      quote_currency: EUR
      is_active: true
    # ... more forex pairs

  bond:
    - symbol: TB3MS
      name: 3-Month Treasury Bill
      series_id: TB3MS
      security_type: TBILLS
      is_active: true
    # ... more bonds

  commodity:
    - symbol: GC=F
      name: Gold Futures
      yfinance_symbol: GC=F
      currency: USD
      is_active: true
    # ... more commodities

  economic_indicator:
    - symbol: GDP
      name: Gross Domestic Product
      series_id: GDP
      is_active: true
    # ... more indicators
```

#### 1.3 Update Collector Service

**File:** `src/investment_platform/api/services/collector_service.py`

**Changes:**
- Replace hard-coded asset lists with calls to `AssetRegistry`
- Remove `search_assets()` function's hard-coded lists
- Use database queries for asset search

#### 1.4 Update Collectors

**Files to Update:**
- `src/investment_platform/collectors/commodity_collector.py`
- `src/investment_platform/collectors/bond_collector.py`

**Changes:**
- Move symbol mappings to configuration or database
- Use `AssetRegistry` for symbol lookups
- Keep mappings as fallback for backward compatibility

#### 1.5 Database Migration

**New File:** `init-db/08-seed-common-assets.sql`

```sql
-- Seed common assets into the assets table
-- This script populates the database with commonly used assets
-- Assets can also be added via the API or admin interface

-- Stocks
INSERT INTO assets (symbol, asset_type, name, exchange, currency, sector, source, is_active)
VALUES 
  ('AAPL', 'stock', 'Apple Inc.', 'NASDAQ', 'USD', 'Technology', 'Yahoo Finance', true),
  ('MSFT', 'stock', 'Microsoft Corporation', 'NASDAQ', 'USD', 'Technology', 'Yahoo Finance', true),
  -- ... more stocks
ON CONFLICT (symbol) DO UPDATE SET
  name = EXCLUDED.name,
  updated_at = NOW();

-- Similar inserts for other asset types
```

---

### 2. Configuration Management

#### 2.1 Enhanced Config Class

**File:** `src/investment_platform/config/__init__.py`

**Changes:**
- Add comprehensive configuration constants
- Support configuration file loading (YAML)
- Add configuration validation
- Add environment-specific defaults

**New Structure:**

```python
class Config:
    """Enhanced configuration manager."""
    
    # API Configuration
    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "30"))
    DEFAULT_MAX_RETRIES: int = int(os.getenv("DEFAULT_MAX_RETRIES", "3"))
    DEFAULT_RATE_LIMIT_CALLS: int = int(os.getenv("DEFAULT_RATE_LIMIT_CALLS", "10"))
    DEFAULT_RATE_LIMIT_PERIOD: int = int(os.getenv("DEFAULT_RATE_LIMIT_PERIOD", "60"))
    
    # Data Collection Configuration
    COLLECTION_TIMEOUT: int = int(os.getenv("COLLECTION_TIMEOUT", "300"))  # 5 minutes
    COLLECTION_RETRY_DELAY: int = int(os.getenv("COLLECTION_RETRY_DELAY", "60"))  # 1 minute
    
    # Date Buffer Configuration
    DATE_BUFFER_DAYS_SMALL: int = int(os.getenv("DATE_BUFFER_DAYS_SMALL", "2"))
    DATE_BUFFER_DAYS_LARGE: int = int(os.getenv("DATE_BUFFER_DAYS_LARGE", "1"))
    DATE_BUFFER_DAYS_YIELD_CURVE: int = int(os.getenv("DATE_BUFFER_DAYS_YIELD_CURVE", "7"))
    
    # Default Intervals
    DEFAULT_STOCK_INTERVAL: str = os.getenv("DEFAULT_STOCK_INTERVAL", "1d")
    DEFAULT_COMMODITY_INTERVAL: str = os.getenv("DEFAULT_COMMODITY_INTERVAL", "1d")
    DEFAULT_FOREX_INTERVAL: str = os.getenv("DEFAULT_FOREX_INTERVAL", "1d")
    DEFAULT_CRYPTO_GRANULARITY: str = os.getenv("DEFAULT_CRYPTO_GRANULARITY", "ONE_DAY")
    
    # Valid Intervals (from config file or env)
    VALID_STOCK_INTERVALS: List[str] = _load_intervals("VALID_STOCK_INTERVALS", [
        "1m", "2m", "5m", "15m", "30m", "60m", "90m",
        "1h", "1d", "5d", "1wk", "1mo", "3mo"
    ])
    
    VALID_CRYPTO_GRANULARITIES: List[str] = _load_intervals("VALID_CRYPTO_GRANULARITIES", [
        "ONE_MINUTE", "FIVE_MINUTE", "FIFTEEN_MINUTE",
        "ONE_HOUR", "SIX_HOUR", "ONE_DAY"
    ])
    
    # Pagination Defaults
    DEFAULT_PAGE_LIMIT: int = int(os.getenv("DEFAULT_PAGE_LIMIT", "50"))
    MAX_PAGE_LIMIT: int = int(os.getenv("MAX_PAGE_LIMIT", "1000"))
    
    # Connection Pool Configuration
    DB_POOL_MIN_CONN: int = int(os.getenv("DB_POOL_MIN_CONN", "1"))
    DB_POOL_MAX_CONN: int = int(os.getenv("DB_POOL_MAX_CONN", "10"))
    
    # Test Configuration
    TEST_TIMEOUT_SHORT: int = int(os.getenv("TEST_TIMEOUT_SHORT", "10"))
    TEST_TIMEOUT_MEDIUM: int = int(os.getenv("TEST_TIMEOUT_MEDIUM", "30"))
    TEST_TIMEOUT_LONG: int = int(os.getenv("TEST_TIMEOUT_LONG", "60"))
    TEST_TIMEOUT_VERY_LONG: int = int(os.getenv("TEST_TIMEOUT_VERY_LONG", "180"))
    
    # Default Currency
    DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "USD")
    
    @classmethod
    def _load_intervals(cls, env_var: str, default: List[str]) -> List[str]:
        """Load interval list from environment or use default."""
        env_value = os.getenv(env_var)
        if env_value:
            return [i.strip() for i in env_value.split(",")]
        return default
```

#### 2.2 Configuration File

**New File:** `config/platform_config.yaml`

```yaml
# Platform Configuration
# Environment-specific overrides can be provided via environment variables

data_collection:
  timeout: 300  # 5 minutes
  retry_delay: 60  # 1 minute
  max_retries: 3
  
date_buffers:
  small_range_days: 2
  large_range_days: 1
  yield_curve_days: 7

intervals:
  stock:
    default: "1d"
    valid:
      - "1m"
      - "2m"
      - "5m"
      - "15m"
      - "30m"
      - "60m"
      - "90m"
      - "1h"
      - "1d"
      - "5d"
      - "1wk"
      - "1mo"
      - "3mo"
  
  crypto:
    default: "ONE_DAY"
    valid:
      - "ONE_MINUTE"
      - "FIVE_MINUTE"
      - "FIFTEEN_MINUTE"
      - "ONE_HOUR"
      - "SIX_HOUR"
      - "ONE_DAY"

pagination:
  default_limit: 50
  max_limit: 1000

connection_pool:
  min_connections: 1
  max_connections: 10

defaults:
  currency: "USD"
```

#### 2.3 Update Code to Use Config

**Files to Update:**
- All collector files (use `Config.DEFAULT_STOCK_INTERVAL` instead of `"1d"`)
- Test files (use `Config.TEST_TIMEOUT_*` constants)
- Ingestion engine (use `Config.COLLECTION_TIMEOUT`)
- Database connection (use `Config.DB_POOL_*`)

---

### 3. Constants Module

#### 3.1 Create Constants Module

**New File:** `src/investment_platform/constants.py`

```python
"""
Application-wide constants.

This module provides named constants for magic numbers and commonly used values.
"""

from datetime import timedelta

# Time Constants
SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 86400

# Date Buffer Constants
DATE_BUFFER_SMALL_RANGE = timedelta(days=2)
DATE_BUFFER_LARGE_RANGE = timedelta(days=1)
DATE_BUFFER_YIELD_CURVE = timedelta(days=7)

# Rate Limiting
DEFAULT_RATE_LIMIT_CALLS = 5
DEFAULT_RATE_LIMIT_PERIOD_SECONDS = 10

# Pagination
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 1000

# Health Check
HEALTH_CHECK_INTERVAL_SECONDS = 30
HEALTH_CHECK_TIMEOUT_SECONDS = 10
HEALTH_CHECK_START_PERIOD_SECONDS = 5
HEALTH_CHECK_RETRIES = 3

# Asset Types
ASSET_TYPE_STOCK = "stock"
ASSET_TYPE_CRYPTO = "crypto"
ASSET_TYPE_FOREX = "forex"
ASSET_TYPE_BOND = "bond"
ASSET_TYPE_COMMODITY = "commodity"
ASSET_TYPE_ECONOMIC_INDICATOR = "economic_indicator"

# Data Sources
DATA_SOURCE_YAHOO_FINANCE = "Yahoo Finance"
DATA_SOURCE_FRED = "FRED API"
DATA_SOURCE_COINBASE = "Coinbase Advanced API"
```

#### 3.2 Update Code to Use Constants

Replace magic numbers with named constants throughout the codebase.

---

### 4. Database Configuration

#### 4.1 Remove Hard-Coded Database Credentials

**File:** `docker-compose.yml`

**Changes:**
- Use environment variables for all database credentials
- Provide `.env.example` file
- Document required environment variables

**File:** `src/investment_platform/ingestion/db_connection.py`

**Changes:**
- Remove default values (require environment variables)
- Add validation for required database configuration
- Provide clear error messages if configuration is missing

**Files:** `scripts/execute_functions.py`, `scripts/execute_schema.py`

**Changes:**
- Remove hard-coded database credentials
- Use environment variables or configuration file
- Add error handling for missing configuration

---

### 5. Security Improvements

#### 5.1 Fix CORS Configuration

**File:** `src/investment_platform/api/main.py`

**Changes:**
- Replace `allow_origins=["*"]` with environment-based configuration
- Add `CORS_ORIGINS` environment variable
- Default to empty list (no CORS) in production
- Allow configuration via Config class

**Implementation:**
```python
# In Config class
CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []

# In main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS if Config.CORS_ORIGINS else ["*"],  # Development fallback
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 5.2 SQL Injection Prevention

**File:** `src/investment_platform/ingestion/data_loader.py`

**Changes:**
- Create whitelist of valid table names
- Use `psycopg2.sql.Identifier` for table/column names
- Validate table names against whitelist before use
- Use parameterized queries for all user input

**Implementation:**
```python
from psycopg2 import sql

# Whitelist of valid tables
VALID_TABLES = {"market_data", "forex_rates", "bond_rates", "economic_data"}

def _validate_table_name(table: str) -> str:
    """Validate table name against whitelist."""
    if table not in VALID_TABLES:
        raise ValueError(f"Invalid table name: {table}")
    return table

# Use sql.Identifier for table names
cursor.execute(
    sql.SQL("CREATE TEMP TABLE IF NOT EXISTS {} (LIKE {} INCLUDING ALL)").format(
        sql.Identifier(temp_table),
        sql.Identifier(table)
    )
)
```

#### 5.3 Error Message Sanitization

**Files:** All API routers

**Changes:**
- Create error sanitization utility
- Remove internal details from error messages
- Log full errors internally, return sanitized messages to clients

**Implementation:**
```python
def sanitize_error_message(error: Exception, include_details: bool = False) -> str:
    """Sanitize error messages for client responses."""
    if include_details:
        return str(error)
    
    # Return generic message for production
    error_type = type(error).__name__
    if "database" in str(error).lower():
        return "Database operation failed"
    elif "validation" in str(error).lower():
        return "Invalid input provided"
    else:
        return "An error occurred processing your request"
```

---

### 6. Code Duplication Reduction

#### 6.1 Centralize Asset Type Mapping

**New File:** `src/investment_platform/ingestion/table_mapping.py`

```python
"""Centralized mapping of asset types to database tables."""

ASSET_TYPE_TO_TABLE = {
    "stock": "market_data",
    "crypto": "market_data",
    "commodity": "market_data",
    "forex": "forex_rates",
    "bond": "bond_rates",
    "economic_indicator": "economic_data",
}

def get_table_for_asset_type(asset_type: str) -> str:
    """Get database table name for asset type."""
    table = ASSET_TYPE_TO_TABLE.get(asset_type)
    if table is None:
        raise ValueError(f"Unknown asset type: {asset_type}")
    return table
```

**Files to Update:**
- `src/investment_platform/ingestion/schema_mapper.py` - Import from table_mapping
- `src/investment_platform/ingestion/data_loader.py` - Import from table_mapping

#### 6.2 Centralize Date Validation

**New File:** `src/investment_platform/utils/date_utils.py`

```python
"""Date utility functions."""

from datetime import datetime
from typing import Union, Tuple

def parse_and_validate_dates(
    start_date: Union[str, datetime],
    end_date: Union[str, datetime]
) -> Tuple[datetime, datetime]:
    """Parse and validate date strings or datetime objects."""
    # Centralized date parsing logic
    pass
```

---

### 7. Input Validation Enhancement

#### 7.1 Symbol Validation

**File:** `src/investment_platform/api/services/collector_service.py`

**Changes:**
- Add strict symbol validation
- Prevent SQL injection in symbol names
- Validate symbol format per asset type

**Implementation:**
```python
import re

SYMBOL_PATTERNS = {
    "stock": re.compile(r"^[A-Z0-9]{1,10}$"),
    "crypto": re.compile(r"^[A-Z0-9-]{1,20}$"),
    "forex": re.compile(r"^[A-Z]{3}_[A-Z]{3}$"),
    # ... more patterns
}

def validate_symbol(symbol: str, asset_type: str) -> bool:
    """Validate symbol format for asset type."""
    pattern = SYMBOL_PATTERNS.get(asset_type)
    if pattern and pattern.match(symbol):
        return True
    return False
```

#### 7.2 Enhanced API Input Validation

**Files:** All API routers

**Changes:**
- Add Pydantic validators for all request models
- Validate date ranges (start < end, reasonable ranges)
- Validate limits and offsets
- Add custom validation error messages

---

### 8. Retry Configuration

#### 8.1 Configurable Retry Logic

**File:** `src/investment_platform/collectors/base.py`

**Changes:**
- Use Config values for retry configuration
- Make retry parameters configurable per collector type

**Implementation:**
```python
# In Config class
DEFAULT_RETRY_ATTEMPTS: int = int(os.getenv("DEFAULT_RETRY_ATTEMPTS", "3"))
DEFAULT_RETRY_MULTIPLIER: int = int(os.getenv("DEFAULT_RETRY_MULTIPLIER", "1"))
DEFAULT_RETRY_MIN_WAIT: int = int(os.getenv("DEFAULT_RETRY_MIN_WAIT", "2"))
DEFAULT_RETRY_MAX_WAIT: int = int(os.getenv("DEFAULT_RETRY_MAX_WAIT", "10"))

# In base.py
@retry(
    stop=stop_after_attempt(Config.DEFAULT_RETRY_ATTEMPTS),
    wait=wait_exponential(
        multiplier=Config.DEFAULT_RETRY_MULTIPLIER,
        min=Config.DEFAULT_RETRY_MIN_WAIT,
        max=Config.DEFAULT_RETRY_MAX_WAIT
    ),
    retry=retry_if_exception_type((APIError, RateLimitError)),
    reraise=True,
)
```

---

### 9. Connection Pool Configuration

#### 9.1 Configurable Connection Pools

**File:** `src/investment_platform/api/main.py`

**Changes:**
- Use Config values for connection pool sizes
- Different pool sizes for different environments

**Implementation:**
```python
# In Config class
DB_POOL_MIN_CONN: int = int(os.getenv("DB_POOL_MIN_CONN", "2"))
DB_POOL_MAX_CONN: int = int(os.getenv("DB_POOL_MAX_CONN", "20"))

# In main.py
initialize_connection_pool(
    min_conn=Config.DB_POOL_MIN_CONN,
    max_conn=Config.DB_POOL_MAX_CONN
)
```

---

### 11. Object-Oriented Programming Improvements

#### 11.1 Encapsulation Enhancement

**Files to Update:** All collector classes, service classes, engine classes

**Changes:**
- Add private attributes (use `_` prefix)
- Add properties for getters/setters
- Add validation in setters
- Protect internal state

**Implementation Example:**
```python
class BaseDataCollector(ABC):
    def __init__(self, output_format: str = "dataframe", ...):
        self._output_format = output_format
        self._max_retries = max_retries
        self._timeout = timeout
        # ... other private attributes
    
    @property
    def output_format(self) -> str:
        """Get output format."""
        return self._output_format
    
    @output_format.setter
    def output_format(self, value: str) -> None:
        """Set output format with validation."""
        if value not in ["dataframe", "dict"]:
            raise ValueError(f"Invalid output_format: {value}")
        self._output_format = value
    
    @property
    def max_retries(self) -> int:
        """Get maximum retry attempts."""
        return self._max_retries
    
    @max_retries.setter
    def max_retries(self, value: int) -> None:
        """Set max retries with validation."""
        if value < 0:
            raise ValueError("max_retries must be >= 0")
        self._max_retries = value
```

#### 11.2 Add Dunder Methods

**Files to Update:** All classes

**Changes:**
- Add `__str__` and `__repr__` methods
- Add `__eq__` for value comparison where appropriate
- Add `__hash__` for immutable classes

**Implementation Example:**
```python
class BaseDataCollector(ABC):
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"{self.__class__.__name__}("
            f"output_format={self._output_format!r}, "
            f"max_retries={self._max_retries}, "
            f"timeout={self._timeout})"
        )
    
    def __str__(self) -> str:
        """User-friendly string representation."""
        return f"{self.__class__.__name__} (format: {self._output_format})"
    
    def __eq__(self, other: object) -> bool:
        """Compare collectors for equality."""
        if not isinstance(other, BaseDataCollector):
            return False
        return (
            self.__class__ == other.__class__ and
            self._output_format == other._output_format and
            self._max_retries == other._max_retries and
            self._timeout == other._timeout
        )
```

#### 11.3 Refactor Functions to Classes

**File:** `src/investment_platform/api/services/collector_service.py`

**Changes:**
- Create `CollectorService` class
- Move functions to class methods
- Add dependency injection support

**Implementation:**
```python
class CollectorService:
    """Service for collector metadata and asset search."""
    
    def __init__(self, asset_registry: Optional[AssetRegistry] = None):
        """Initialize collector service."""
        self._asset_registry = asset_registry or AssetRegistry()
        self._collector_classes = {
            "stock": StockCollector,
            "crypto": CryptoCollector,
            # ... etc
        }
    
    def get_collector_metadata(self) -> Dict[str, Any]:
        """Get metadata for all available collector types."""
        # Implementation
        pass
    
    def search_assets(
        self, 
        asset_type: str, 
        query: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for assets/symbols."""
        # Use AssetRegistry instead of hard-coded lists
        return self._asset_registry.search_assets(asset_type, query, limit)
    
    def validate_collection_params(
        self,
        asset_type: str,
        symbol: str,
        collector_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Validate collection parameters."""
        # Implementation
        pass
```

**File:** `src/investment_platform/ingestion/error_classifier.py`

**Changes:**
- Create `ErrorClassifier` class
- Move function to class method
- Make error indicators configurable

**Implementation:**
```python
class ErrorClassifier:
    """Classifies errors into categories for retry logic."""
    
    def __init__(self, config: Optional[Dict[str, List[str]]] = None):
        """Initialize error classifier."""
        self._transient_indicators = config.get("transient", [
            'rate limit', '429', 'timeout', ...
        ]) if config else DEFAULT_TRANSIENT_INDICATORS
        # ... other indicators
    
    def classify(
        self, 
        error: Exception, 
        error_message: Optional[str] = None
    ) -> Tuple[str, str]:
        """Classify error into category."""
        # Implementation
        pass
```

#### 11.4 Apply SOLID Principles

**Single Responsibility Principle:**

**File:** `src/investment_platform/ingestion/ingestion_engine.py`

**Changes:**
- Split `IngestionEngine` into smaller classes:
  - `IngestionOrchestrator` - coordinates the process
  - `DataCollectionService` - handles data collection
  - `DataLoadingService` - handles data loading
  - `IngestionResultBuilder` - builds result dictionaries

**Open/Closed Principle:**

**New File:** `src/investment_platform/collectors/factory.py`

```python
class CollectorFactory:
    """Factory for creating collector instances."""
    
    _registry: Dict[str, Type[BaseDataCollector]] = {}
    
    @classmethod
    def register(
        cls, 
        asset_type: str, 
        collector_class: Type[BaseDataCollector]
    ) -> None:
        """Register a collector class for an asset type."""
        cls._registry[asset_type] = collector_class
    
    @classmethod
    def create(
        cls, 
        asset_type: str, 
        **kwargs: Any
    ) -> BaseDataCollector:
        """Create a collector instance for an asset type."""
        collector_class = cls._registry.get(asset_type)
        if not collector_class:
            raise ValueError(f"Unknown asset type: {asset_type}")
        return collector_class(**kwargs)
    
    @classmethod
    def get_registered_types(cls) -> List[str]:
        """Get list of registered asset types."""
        return list(cls._registry.keys())
```

**Dependency Inversion Principle:**

**New File:** `src/investment_platform/collectors/interfaces.py`

```python
from typing import Protocol
from datetime import datetime
from typing import Any, Dict, List, Union
import pandas as pd

class IDataCollector(Protocol):
    """Interface for data collectors."""
    
    def collect_historical_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        **kwargs: Any,
    ) -> Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
        """Collect historical data."""
        ...
    
    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """Get asset information."""
        ...
```

**Update IngestionEngine:**
```python
class IngestionEngine:
    def __init__(
        self,
        collector_factory: CollectorFactory,
        asset_manager: AssetManager,
        schema_mapper: SchemaMapper,
        # ... other dependencies
    ):
        """Initialize with injected dependencies."""
        self._collector_factory = collector_factory
        self._asset_manager = asset_manager
        # ... etc
```

#### 11.5 Implement Design Patterns

**Factory Pattern:**

**File:** `src/investment_platform/collectors/factory.py` (see above)

**Singleton Pattern:**

**File:** `src/investment_platform/config/__init__.py`

**Changes:**
- Convert Config to proper singleton
- Or use dependency injection instead

**Repository Pattern:**

**New File:** `src/investment_platform/ingestion/repositories/asset_repository.py`

```python
class AssetRepository:
    """Repository for asset data access."""
    
    def __init__(self, db_connection_factory: Callable):
        """Initialize repository."""
        self._get_connection = db_connection_factory
    
    def find_by_symbol(self, symbol: str) -> Optional[Asset]:
        """Find asset by symbol."""
        # Implementation
        pass
    
    def create(self, asset: Asset) -> Asset:
        """Create new asset."""
        # Implementation
        pass
    
    def update(self, asset: Asset) -> Asset:
        """Update existing asset."""
        # Implementation
        pass
```

**Strategy Pattern:**

**New File:** `src/investment_platform/ingestion/strategies/data_loading_strategy.py`

```python
class DataLoadingStrategy(ABC):
    """Abstract strategy for loading data."""
    
    @abstractmethod
    def load(
        self, 
        data: pd.DataFrame, 
        table: str, 
        on_conflict: str
    ) -> int:
        """Load data into table."""
        pass

class CopyDataLoadingStrategy(DataLoadingStrategy):
    """Strategy using PostgreSQL COPY."""
    # Implementation

class InsertDataLoadingStrategy(DataLoadingStrategy):
    """Strategy using INSERT statements."""
    # Implementation
```

#### 11.6 Eliminate Global State

**File:** `src/investment_platform/ingestion/request_coordinator.py`

**Changes:**
- Remove global `_coordinator` variable
- Use dependency injection
- Create coordinator in application startup

**File:** `src/investment_platform/ingestion/db_connection.py`

**Changes:**
- Encapsulate connection pool in a class
- Use dependency injection
- Remove global state

**Implementation:**
```python
class DatabaseConnectionManager:
    """Manages database connection pool."""
    
    def __init__(
        self,
        min_conn: int = 1,
        max_conn: int = 10,
        **db_config: Any
    ):
        """Initialize connection manager."""
        self._pool = None
        self._min_conn = min_conn
        self._max_conn = max_conn
        self._db_config = db_config
    
    def initialize(self) -> None:
        """Initialize connection pool."""
        # Implementation
    
    @contextmanager
    def get_connection(self, autocommit: bool = False):
        """Get connection from pool."""
        # Implementation
    
    def close(self) -> None:
        """Close connection pool."""
        # Implementation
```

---

### 12. Test Fixtures

#### 5.1 Centralize Test Data

**New File:** `tests/fixtures/asset_symbols.py`

```python
"""
Centralized test asset symbols.

This module provides test asset symbols that can be used across all tests.
"""

# Test Stock Symbols
TEST_STOCK_SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA"]

# Test Crypto Symbols
TEST_CRYPTO_SYMBOLS = ["BTC-USD", "ETH-USD"]

# Test Forex Symbols
TEST_FOREX_SYMBOLS = ["USD_EUR", "USD_GBP"]

# Test Bond Symbols
TEST_BOND_SYMBOLS = ["TB3MS", "DGS10"]

# Test Commodity Symbols
TEST_COMMODITY_SYMBOLS = ["GC=F", "CL=F"]

# Test Economic Indicator Symbols
TEST_ECONOMIC_SYMBOLS = ["GDP", "UNRATE"]
```

#### 5.2 Update Test Files

Update all test files to import from `tests/fixtures/asset_symbols.py` instead of hard-coding symbols.

---

## Implementation Phases

### Phase 1: Foundation (Week 1)

**Goal:** Create infrastructure for configuration and asset management.

**Tasks:**
1. ✅ Create enhanced `Config` class with all constants
2. ✅ Create `constants.py` module
3. ✅ Create `AssetRegistry` service (basic implementation)
4. ✅ Create configuration YAML files
5. ✅ Create database migration for asset seeding
6. ✅ Update `db_connection.py` to use Config
7. ✅ Create `table_mapping.py` to centralize asset type mappings
8. ✅ Create `date_utils.py` for centralized date handling
9. ✅ Fix CORS configuration
10. ✅ Add SQL injection prevention utilities

**Deliverables:**
- Enhanced Config class
- Constants module
- AssetRegistry service (skeleton)
- Configuration files
- Database migration script
- Security improvements (CORS, SQL injection prevention)
- Code deduplication utilities

**Testing:**
- Unit tests for Config class
- Unit tests for constants
- Integration test for AssetRegistry (basic)
- Security tests for SQL injection prevention

---

### Phase 2: Asset Management (Week 2)

**Goal:** Migrate asset symbols to database-driven system.

**Tasks:**
1. ✅ Complete AssetRegistry implementation
2. ✅ Create asset configuration YAML
3. ✅ Create database seeding script
4. ✅ Update `collector_service.py` to use AssetRegistry
5. ✅ Update collectors to use AssetRegistry (with fallbacks)
6. ✅ Update test fixtures to use centralized symbols

**Deliverables:**
- Complete AssetRegistry service
- Asset configuration file
- Database seeding script
- Updated collector service
- Updated collectors
- Updated test fixtures

**Testing:**
- Integration tests for AssetRegistry
- Tests for asset search functionality
- Tests for collector service with AssetRegistry
- Regression tests for existing functionality

---

### Phase 3: Configuration Migration (Week 3)

**Goal:** Replace hard-coded configuration values throughout codebase.

**Tasks:**
1. ✅ Update all collectors to use Config constants
2. ✅ Update ingestion engine to use Config
3. ✅ Update test files to use Config constants
4. ✅ Update database connection to use Config
5. ✅ Update docker-compose to use environment variables
6. ✅ Create `.env.example` file

**Deliverables:**
- Updated collectors
- Updated ingestion engine
- Updated test files
- Updated database configuration
- Environment variable documentation

**Testing:**
- Unit tests with different configurations
- Integration tests
- Regression tests

---

### Phase 4: OOP Improvements (Week 4)

**Goal:** Implement object-oriented programming standards and design patterns.

**Tasks:**
1. ✅ Add encapsulation (private attributes, properties)
2. ✅ Add dunder methods (__str__, __repr__, __eq__)
3. ✅ Refactor functions to classes (CollectorService, ErrorClassifier)
4. ✅ Apply SOLID principles (split IngestionEngine, add interfaces)
5. ✅ Implement design patterns (Factory, Repository, Strategy)
6. ✅ Eliminate global state (dependency injection)
7. ✅ Add type hints and protocols
8. ✅ Update tests for new class structure

**Deliverables:**
- Encapsulated classes with proper access control
- Classes with dunder methods for better debugging
- SOLID-compliant code structure
- Design patterns implemented
- Dependency injection in place
- No global state

**Testing:**
- Unit tests for new class structure
- Integration tests with dependency injection
- Mock tests for interfaces/protocols
- Regression tests

---

### Phase 5: Cleanup and Documentation (Week 5)

**Goal:** Remove old hard-coded values and document changes.

**Tasks:**
1. ✅ Remove all hard-coded asset symbols
2. ✅ Remove all hard-coded configuration values
3. ✅ Remove magic numbers (replace with constants)
4. ✅ Remove code duplication (use centralized utilities)
5. ✅ Fix security issues (CORS, SQL injection, credentials)
6. ✅ Enhance input validation
7. ✅ Update documentation
8. ✅ Create migration guide
9. ✅ Code review and refactoring
10. ✅ Security audit
11. ✅ OOP standards documentation

**Deliverables:**
- Clean codebase (no hard-coded values)
- Security improvements implemented
- Code duplication eliminated
- OOP standards implemented
- Updated documentation
- Migration guide
- Configuration guide
- Security guide
- OOP design guide

**Testing:**
- Full regression test suite
- Performance testing
- Configuration validation testing
- Security testing (SQL injection, input validation)
- OOP design validation

---

## Testing Strategy

### Unit Tests

1. **Config Class Tests**
   - Test environment variable loading
   - Test default values
   - Test configuration validation

2. **AssetRegistry Tests**
   - Test asset lookup
   - Test asset search
   - Test caching behavior
   - Test database fallback

3. **Constants Tests**
   - Verify constant values
   - Test constant usage

### Integration Tests

1. **Asset Management Integration**
   - Test asset seeding from YAML
   - Test asset search across asset types
   - Test asset metadata retrieval

2. **Configuration Integration**
   - Test configuration loading from YAML
   - Test environment variable overrides
   - Test configuration validation

3. **Collector Integration**
   - Test collectors with AssetRegistry
   - Test fallback behavior
   - Test with different configurations

### Regression Tests

1. **API Compatibility**
   - Ensure API endpoints still work
   - Ensure response formats unchanged
   - Test backward compatibility

2. **Data Collection**
   - Test data collection with new system
   - Verify data quality unchanged
   - Test error handling

### Performance Tests

1. **AssetRegistry Performance**
   - Test caching effectiveness
   - Test database query performance
   - Test search performance

2. **Configuration Loading**
   - Test configuration file loading time
   - Test environment variable parsing

---

## Migration Plan

### Pre-Migration

1. **Backup**
   - Backup database
   - Tag current code version
   - Document current behavior

2. **Preparation**
   - Review all hard-coded values
   - Identify all affected components
   - Create test plan

### Migration Steps

1. **Deploy Foundation (Phase 1)**
   - Deploy Config and constants
   - Deploy AssetRegistry (disabled)
   - Monitor for issues

2. **Enable Asset Management (Phase 2)**
   - Seed database with common assets
   - Enable AssetRegistry (with fallbacks)
   - Monitor asset lookups
   - Gradually migrate consumers

3. **Migrate Configuration (Phase 3)**
   - Update collectors one by one
   - Test each update
   - Monitor for issues

4. **Cleanup (Phase 4)**
   - Remove old hard-coded values
   - Remove fallback code (after verification)
   - Final testing

### Rollback Plan

1. **Immediate Rollback**
   - Revert to previous code version
   - Restore database backup if needed

2. **Partial Rollback**
   - Disable AssetRegistry (use fallbacks)
   - Revert specific components
   - Keep Config changes (backward compatible)

---

## Success Criteria

### Functional Requirements

- ✅ All asset symbols come from database or configuration (not hard-coded)
- ✅ All configuration values come from Config class or environment variables
- ✅ All magic numbers replaced with named constants
- ✅ Asset search works from database
- ✅ All existing functionality still works
- ✅ API compatibility maintained
- ✅ Security vulnerabilities addressed (CORS, SQL injection, credentials)
- ✅ Code duplication eliminated
- ✅ Input validation enhanced
- ✅ OOP standards implemented (encapsulation, SOLID principles, design patterns)
- ✅ Proper class design with dunder methods
- ✅ Dependency injection implemented
- ✅ Global state eliminated

### Non-Functional Requirements

- ✅ No performance degradation
- ✅ Configuration changes don't require code changes
- ✅ Easy to add new assets
- ✅ Easy to adjust configuration
- ✅ Code is more maintainable
- ✅ Tests pass
- ✅ Documentation updated

### Metrics

- **Code Quality:**
  - Reduced hard-coded values: Target 95% reduction
  - Increased configuration coverage: Target 90% of configurable values
  - Reduced code duplication: Target 30% reduction

- **Maintainability:**
  - Time to add new asset: < 5 minutes (vs. code change before)
  - Time to change configuration: < 1 minute (vs. code change before)

---

## Risk Assessment

### High Risk

1. **Database Migration**
   - Risk: Data loss or corruption
   - Mitigation: Comprehensive backups, staged rollout, rollback plan

2. **Asset Lookup Changes**
   - Risk: Breaking existing functionality
   - Mitigation: Fallback mechanisms, comprehensive testing, gradual rollout

3. **Security Changes**
   - Risk: Breaking API access or introducing new vulnerabilities
   - Mitigation: Careful testing, gradual rollout, security review

### Medium Risk

1. **Configuration Changes**
   - Risk: Unexpected behavior with new configurations
   - Mitigation: Default values match current behavior, extensive testing

2. **Performance Impact**
   - Risk: Database queries slower than hard-coded lists
   - Mitigation: Caching, performance testing, optimization

### Low Risk

1. **Code Refactoring**
   - Risk: Introduction of bugs
   - Mitigation: Comprehensive testing, code review

---

## Dependencies

### External Dependencies

- Database must be available for AssetRegistry
- YAML parsing library (PyYAML - already in requirements)
- Environment variable support (standard library)

### Internal Dependencies

- Database schema must support assets table (already exists)
- Config class must be enhanced
- AssetRegistry service must be created

---

## Timeline

| Phase | Duration | Start Date | End Date |
|-------|----------|------------|----------|
| Phase 1: Foundation | 1 week | TBD | TBD |
| Phase 2: Asset Management | 1 week | TBD | TBD |
| Phase 3: Configuration Migration | 1 week | TBD | TBD |
| Phase 4: OOP Improvements | 1 week | TBD | TBD |
| Phase 5: Cleanup | 1 week | TBD | TBD |
| **Total** | **5 weeks** | | |

---

## Next Steps

1. **Review and Approval**
   - Review this proposal with team
   - Get approval for approach
   - Adjust timeline if needed

2. **Setup**
   - Create feature branch
   - Set up development environment
   - Prepare test data

3. **Execution**
   - Begin Phase 1 implementation
   - Follow phased approach
   - Regular progress reviews

---

## Appendix

### A. Files to be Modified

**New Files:**
- `src/investment_platform/services/asset_registry.py`
- `src/investment_platform/constants.py`
- `src/investment_platform/ingestion/table_mapping.py`
- `src/investment_platform/utils/date_utils.py`
- `src/investment_platform/utils/security.py` (error sanitization, input validation)
- `src/investment_platform/collectors/factory.py` (factory pattern)
- `src/investment_platform/collectors/interfaces.py` (protocols/interfaces)
- `src/investment_platform/ingestion/repositories/asset_repository.py` (repository pattern)
- `src/investment_platform/ingestion/strategies/data_loading_strategy.py` (strategy pattern)
- `config/assets.yaml`
- `config/platform_config.yaml`
- `init-db/08-seed-common-assets.sql`
- `tests/fixtures/asset_symbols.py`
- `.env.example`

**Modified Files:**
- `src/investment_platform/config/__init__.py`
- `src/investment_platform/api/services/collector_service.py`
- `src/investment_platform/api/main.py` (CORS, connection pool)
- `src/investment_platform/collectors/commodity_collector.py`
- `src/investment_platform/collectors/bond_collector.py`
- `src/investment_platform/collectors/stock_collector.py`
- `src/investment_platform/collectors/forex_collector.py`
- `src/investment_platform/collectors/base.py` (retry configuration, encapsulation, dunder methods)
- `src/investment_platform/ingestion/ingestion_engine.py` (SOLID refactoring, dependency injection)
- `src/investment_platform/ingestion/db_connection.py` (SQL injection prevention, eliminate global state)
- `src/investment_platform/ingestion/data_loader.py` (SQL injection prevention, strategy pattern)
- `src/investment_platform/ingestion/schema_mapper.py` (use table_mapping)
- `src/investment_platform/api/services/collector_service.py` (refactor to class, OOP)
- `src/investment_platform/ingestion/error_classifier.py` (refactor to class)
- `src/investment_platform/ingestion/request_coordinator.py` (eliminate global state)
- `src/investment_platform/config/__init__.py` (singleton pattern or DI)
- `scripts/execute_functions.py` (remove hard-coded credentials)
- `scripts/execute_schema.py` (remove hard-coded credentials)
- `docker-compose.yml`
- All test files (multiple)
- All API routers (input validation, error sanitization)
- All collector classes (encapsulation, dunder methods)

### B. Configuration Reference

See `config/platform_config.yaml` and `.env.example` for complete configuration reference.

### C. Asset Registry API

See `src/investment_platform/services/asset_registry.py` for AssetRegistry API documentation.

---

**Document Status:** Ready for Review and Approval  
**Next Review Date:** TBD  
**Owner:** Full Stack Engineering Team

