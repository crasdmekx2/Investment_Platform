# Investment Platform Software Architecture

## Executive Summary

The Investment Platform is a comprehensive financial data management system designed to collect, store, process, and analyze market data from multiple sources. The platform follows a modular, microservices-oriented architecture with clear separation of concerns, containerized services, and API-first design principles.

### Architecture Principles

- **Modular Design**: Clear separation of concerns with independent, reusable components
- **Microservices Architecture**: Services are independently deployable and scalable
- **API-First**: All services communicate through well-defined REST APIs and WebSockets
- **Containerization**: All services are containerized using Docker for consistency and portability
- **Data Integrity**: Robust error handling, validation, and data quality measures
- **Scalability**: Designed to scale horizontally to handle increasing data volumes
- **Observability**: Comprehensive logging, metrics, and monitoring capabilities

### Technology Stack Summary

- **Backend**: Python 3.8+, FastAPI, SQLAlchemy, APScheduler
- **Frontend**: React 18+, TypeScript, Tailwind CSS, Vite
- **Database**: PostgreSQL 16 with TimescaleDB extension
- **Infrastructure**: Docker, Docker Compose
- **Data Collection**: yfinance, coinbase-advanced-py, fredapi
- **Data Processing**: Pandas, NumPy

## Current Architecture

### System Overview

The Investment Platform consists of four main services orchestrated via Docker Compose:

1. **Database Service** (`db`): PostgreSQL with TimescaleDB for time-series data storage
2. **API Service** (`api`): FastAPI application providing REST APIs and WebSocket support
3. **Frontend Service** (`frontend`): React application served via Nginx
4. **Scheduler Service** (`scheduler`): Persistent job scheduler for automated data collection

```
┌─────────────┐
│  Frontend   │ (React + TypeScript)
│   (Nginx)   │
└──────┬──────┘
       │ HTTP/WebSocket
       │
┌──────▼──────┐
│  API Service│ (FastAPI)
│             │
│  - REST API │
│  - WebSocket│
└──────┬──────┘
       │
       ├──────────────┐
       │              │
┌──────▼──────┐  ┌────▼──────┐
│  Database   │  │ Scheduler  │
│ (TimescaleDB│  │ (APScheduler)│
└─────────────┘  └───────────┘
```

### Backend Services

#### API Service (`src/investment_platform/api/`)

The API service is the central communication hub for the platform, built with FastAPI.

**Core Components:**

- **Main Application** (`main.py`): FastAPI application with lifespan management, CORS configuration, and router registration
- **Routers** (`routers/`):
  - `scheduler.py`: Job management, templates, and analytics endpoints
  - `collectors.py`: Collector metadata and options endpoints
  - `ingestion.py`: Data collection execution endpoints
  - `assets.py`: Asset metadata management endpoints
- **WebSocket** (`websocket.py`): Real-time updates for job status and collection progress
- **Services** (`services/`):
  - `scheduler_service.py`: Business logic for scheduler operations
  - `collector_service.py`: Collector metadata and validation logic
- **Models** (`models/`): Pydantic models for request/response validation

**API Endpoints:**

- `/api/scheduler/*`: Job management, templates, dependencies, analytics
- `/api/collectors/*`: Collector metadata and options
- `/api/ingestion/*`: Data collection execution
- `/api/assets/*`: Asset CRUD operations
- `/api/health`: Health check endpoint
- `/metrics`: Prometheus metrics endpoint
- `/ws`: WebSocket endpoint for real-time updates

**Key Features:**

- Async/await support for high concurrency
- Automatic OpenAPI documentation at `/docs`
- Connection pooling for database connections
- Embedded scheduler option (can be disabled for separate scheduler service)
- CORS middleware for frontend integration
- Prometheus metrics integration

#### Data Collection Service (`src/investment_platform/collectors/`)

The data collection service provides a unified interface for collecting financial data from multiple sources.

**Core Components:**

- **Base Collector** (`base.py`): Abstract base class with common functionality:
  - Error handling and retry logic (Tenacity)
  - Rate limiting (ratelimit library)
  - Data format conversion (DataFrame/Dict)
  - Logging and observability
- **Asset-Specific Collectors**:
  - `stock_collector.py`: Yahoo Finance integration for stocks
  - `forex_collector.py`: Yahoo Finance integration for forex pairs
  - `crypto_collector.py`: Coinbase Advanced API integration
  - `bond_collector.py`: FRED API integration for bond rates
  - `commodity_collector.py`: Yahoo Finance integration for commodities
  - `economic_collector.py`: FRED API integration for economic indicators
- **Rate Limiter** (`rate_limiter.py`): Shared rate limiting across collectors

**Key Features:**

- Unified interface for all asset types
- Automatic retry with exponential backoff
- Rate limiting to respect API constraints
- Data validation and error classification
- Support for multiple output formats

#### Ingestion Service (`src/investment_platform/ingestion/`)

The ingestion service orchestrates data collection and loading into the database.

**Core Components:**

- **IngestionEngine** (`ingestion_engine.py`): Main orchestrator that coordinates:
  - Collector initialization
  - Asset registration
  - Incremental data tracking
  - Data collection
  - Data transformation
  - Database loading
- **AssetManager** (`asset_manager.py`): Handles asset registration and metadata management
- **SchemaMapper** (`schema_mapper.py`): Maps collector output to database schema format
- **IncrementalTracker** (`incremental_tracker.py`): Determines existing data ranges for incremental updates
- **DataLoader** (`data_loader.py`): Handles bulk data insertion using PostgreSQL COPY
- **PersistentScheduler** (`persistent_scheduler.py`): APScheduler-based persistent job scheduler
- **RequestCoordinator** (`request_coordinator.py`): Coordinates concurrent data collection requests
- **ErrorClassifier** (`error_classifier.py`): Classifies and handles different error types

**Key Features:**

- Batch and incremental ingestion modes
- Automatic gap detection for missing data
- Bulk insert optimization using PostgreSQL COPY
- Comprehensive error handling and logging
- Job scheduling with cron and interval patterns
- Job dependencies and templates

#### Scheduler Service

The scheduler service runs as a separate container or can be embedded in the API service.

**Features:**

- Persistent job storage in database
- Job templates for reusable configurations
- Job dependencies (jobs can depend on other jobs)
- Flexible scheduling (cron expressions, intervals)
- Collection logging and analytics
- Job status tracking and monitoring

### Frontend Application (`frontend/`)

The frontend is a modern React application built with TypeScript and Tailwind CSS.

**Architecture:**

- **Pages** (`src/pages/`):
  - `Dashboard.tsx`: Main dashboard view
  - `Portfolio.tsx`: Portfolio management
  - `Scheduler.tsx`: Job scheduler interface
  - `NotFound.tsx`: 404 page
- **Components** (`src/components/`):
  - `scheduler/`: Scheduler-specific components (JobCreator, JobsList, JobAnalytics, etc.)
  - `common/`: Reusable UI components (Button, Card, LoadingSpinner, etc.)
  - `layout/`: Layout components (Header, Sidebar, Layout)
  - `charts/`: Chart components for data visualization
- **State Management** (`src/store/`):
  - Redux store with slices:
    - `schedulerSlice.ts`: Scheduler state
    - `marketData.ts`: Market data state
    - `portfolio.ts`: Portfolio state
    - `collectionSlice.ts`: Collection state
- **API Client** (`src/lib/api/`):
  - `client.ts`: Axios-based API client
  - `endpoints.ts`: API endpoint definitions
  - `scheduler.ts`: Scheduler API functions
  - `types.ts`: TypeScript type definitions
- **WebSocket Client** (`src/lib/websocket/`):
  - `websocketClient.ts`: WebSocket connection management
- **Hooks** (`src/hooks/`):
  - Custom React hooks for API calls, WebSocket, debouncing, etc.

**Key Features:**

- TypeScript for type safety
- Responsive design with Tailwind CSS
- Real-time updates via WebSocket
- Redux for state management
- Comprehensive error handling
- Loading states and user feedback
- Accessibility compliance (WCAG 2.2 AA)

### Database Layer

#### Schema Structure

The database uses PostgreSQL 16 with TimescaleDB extension for time-series data optimization.

**Core Tables:**

1. **assets**: Central metadata table for all asset types
   - Primary key: `asset_id`
   - Unique constraint on `symbol`
   - Asset types: stock, forex, crypto, bond, commodity, economic_indicator
   - JSONB field for flexible metadata storage

2. **market_data**: OHLCV data for stocks, crypto, commodities
   - Composite primary key: `(asset_id, time)`
   - TimescaleDB hypertable
   - Columns: time, asset_id, open, high, low, close, volume, dividends, stock_splits

3. **forex_rates**: Exchange rates for forex pairs
   - Composite primary key: `(asset_id, time)`
   - TimescaleDB hypertable
   - Columns: time, asset_id, rate

4. **bond_rates**: Interest rates for bonds
   - Composite primary key: `(asset_id, time)`
   - TimescaleDB hypertable
   - Columns: time, asset_id, rate

5. **economic_data**: Economic indicator values
   - Composite primary key: `(asset_id, time)`
   - TimescaleDB hypertable
   - Columns: time, asset_id, value

6. **data_collection_log**: Logging table for collection runs
   - Tracks: job_id, asset_id, status, records_collected, execution_time, errors

7. **scheduler_jobs**: Persistent job storage
   - Job configuration, schedule, dependencies, status

8. **scheduler_job_templates**: Reusable job templates

**Indexing Strategy:**

- Primary indexes on composite keys for time-series tables
- Indexes on `asset_id` for foreign key lookups
- Indexes on `asset_type` and `symbol` for asset queries
- TimescaleDB automatic indexing on time dimension

**TimescaleDB Features:**

- Hypertables for automatic partitioning by time
- Continuous aggregates for pre-computed metrics (future)
- Data retention policies (future)
- Compression policies (future)

### Infrastructure

#### Docker Containerization

All services are containerized using Docker:

**Services:**

1. **db** (`timescale/timescaledb:latest-pg16`):
   - PostgreSQL 16 with TimescaleDB
   - Persistent volume for data
   - Health checks via `pg_isready`
   - Port: 5432

2. **api** (`Dockerfile.api`):
   - FastAPI application
   - Python 3.8+ base image
   - Environment-based configuration
   - Health check endpoint
   - Port: 8000
   - Depends on: db

3. **frontend** (`frontend/Dockerfile`):
   - React application built with Vite
   - Nginx for serving static files
   - Environment variables for API URLs
   - Port: 3000 (mapped to 80 in container)
   - Depends on: api

4. **scheduler** (`Dockerfile.scheduler`):
   - Persistent scheduler service
   - Can run independently or embedded in API
   - Health checks
   - Depends on: db, api

**Docker Compose Configuration:**

- Network: `investment-platform-network` (bridge driver)
- Volumes: `postgres_data` for database persistence
- Health checks for all services
- Dependency management for startup order
- Environment variable configuration

**Network Architecture:**

- All services communicate via Docker network
- Frontend → API: HTTP/WebSocket
- API → Database: PostgreSQL protocol
- Scheduler → Database: PostgreSQL protocol
- Scheduler → API: HTTP (for job execution)

## Microservices Architecture

### Service Boundaries

The platform follows a microservices architecture with clear service boundaries:

1. **API Service**: Handles all HTTP/WebSocket requests, business logic, and coordination
2. **Scheduler Service**: Manages job scheduling and execution (can be embedded or separate)
3. **Database Service**: Data persistence layer
4. **Frontend Service**: User interface layer

### Inter-Service Communication

- **Synchronous**: REST API calls between frontend and API service
- **Asynchronous**: WebSocket for real-time updates
- **Database**: Shared database for data persistence and job storage
- **Future**: Message queue (RabbitMQ/Kafka) for event-driven communication

### API Contracts

All services communicate through well-defined API contracts:

- **REST APIs**: OpenAPI/Swagger documentation at `/docs`
- **WebSocket**: JSON message protocol for real-time updates
- **Database**: SQL schema with foreign key constraints

### Data Consistency Patterns

- **Transactional**: Database transactions for critical operations
- **Eventual Consistency**: For non-critical updates (future)
- **Idempotency**: API endpoints designed to be idempotent where possible

## API Architecture

### REST API Design

**Design Principles:**

- RESTful resource-based URLs
- HTTP methods: GET (read), POST (create), PUT (update), DELETE (delete)
- JSON request/response format
- Status codes: 200 (success), 201 (created), 400 (bad request), 404 (not found), 500 (server error)
- Pagination for list endpoints
- Filtering and sorting via query parameters

**API Versioning:**

- Current version: v1 (implicit)
- Future: `/api/v1/`, `/api/v2/` for versioning

**Authentication/Authorization:**

- Currently: None (development)
- Future: JWT tokens, OAuth 2.0, role-based access control

### WebSocket Real-Time Updates

**WebSocket Endpoint:** `/ws`

**Message Protocol:**

- JSON format
- Message types: `job_status`, `collection_progress`, `error`
- Client can subscribe to specific job IDs or asset types

**Use Cases:**

- Real-time job status updates
- Collection progress notifications
- Error notifications

### API Documentation

- Automatic OpenAPI documentation at `/docs`
- Interactive Swagger UI
- Request/response examples
- Schema definitions

## Data Architecture

### Data Collection Flow

```
External API → Collector → IngestionEngine → SchemaMapper → Database
     ↓              ↓            ↓              ↓
  Rate Limit    Retry Logic   Validation   Transformation
```

1. **Collection**: Collector fetches data from external APIs (Yahoo Finance, Coinbase, FRED)
2. **Validation**: Data validated against schema and business rules
3. **Transformation**: SchemaMapper converts collector output to database format
4. **Loading**: DataLoader performs bulk insert using PostgreSQL COPY
5. **Logging**: Collection run logged to `data_collection_log` table

### Data Ingestion Pipeline

**Modes:**

- **Batch Mode**: Collect all data in date range, ignoring existing data
- **Incremental Mode**: Only collect missing data by detecting gaps

**Process:**

1. Check asset registration (create if missing)
2. If incremental: Query existing data ranges, calculate gaps
3. Collect data for missing ranges
4. Transform and validate data
5. Bulk insert into appropriate table
6. Log collection run

### Storage Strategy

**Time-Series Data:**

- Stored in TimescaleDB hypertables
- Automatic partitioning by time
- Composite primary keys: `(asset_id, time)`
- Efficient queries for time ranges

**Metadata:**

- Stored in regular PostgreSQL tables
- JSONB fields for flexible schema
- Indexed for fast lookups

### Data Retention Policies

- **Current**: No automatic retention (manual cleanup)
- **Future**: TimescaleDB retention policies for automatic data archival/deletion

## Future Architecture Placeholders

### Analytics Service (PLANNED)

**Purpose:** Advanced analytics, reporting, and insights generation

**Architecture:**

- **Separate Microservice**: `analytics-api` service
- **Analytics Engine**: Python-based computation engine using Pandas, NumPy, SciPy
- **Caching Layer**: Redis for computed metrics and aggregations
- **Data Warehouse Integration**: Read from TimescaleDB, write aggregated results
- **API Gateway**: RESTful API for analytics endpoints

**Technology Considerations:**

- **Python Analytics Libraries**: Pandas, NumPy, SciPy for data analysis
- **ML Libraries** (future): scikit-learn, TensorFlow for predictive analytics
- **Visualization Libraries**: Matplotlib, Plotly for chart generation
- **Caching**: Redis for performance optimization
- **Computation**: Async processing for long-running analytics jobs

**API Endpoints (Planned):**

- `GET /api/analytics/portfolio`: Portfolio performance analytics
- `GET /api/analytics/performance`: Asset performance metrics
- `GET /api/analytics/risk`: Risk analysis and metrics
- `GET /api/analytics/reports`: Report generation endpoints
- `POST /api/analytics/compute`: Trigger custom analytics computations

**Data Requirements:**

- Read access to `market_data`, `forex_rates`, `bond_rates`, `economic_data` tables
- Read access to portfolio data (future)
- Write access to aggregated metrics storage (new table: `analytics_results`)
- Historical analysis capabilities with time-series queries

**Integration Points:**

- Consumes data from TimescaleDB
- Provides analytics via REST API
- Can trigger computations via API or scheduled jobs
- WebSocket support for real-time analytics updates (future)

**Containerization:**

- Separate Docker container: `analytics-api`
- Docker Compose service with dependencies on `db` and `api`
- Health checks and monitoring

### Additional Future Services (PLACEHOLDERS)

#### Trading Service (PLANNED)

**Purpose:** Order execution, portfolio management, trade processing

**Architecture:**

- Separate microservice for trading operations
- Integration with trading APIs (brokerage, exchanges)
- Order management system
- Portfolio tracking and rebalancing
- Trade execution engine

**Key Features:**

- Order placement and management
- Portfolio holdings tracking
- Trade history and audit trail
- Risk management and compliance checks

#### Notification Service (PLANNED)

**Purpose:** Alerts, notifications, and user communications

**Architecture:**

- Event-driven notification service
- Multiple notification channels (email, SMS, push, in-app)
- Notification templates and preferences
- Delivery tracking and retry logic

**Integration:**

- Consumes events from other services
- Integrates with email/SMS providers
- WebSocket for real-time in-app notifications

#### Authentication Service (PLANNED)

**Purpose:** User management, authentication, and authorization

**Architecture:**

- Separate authentication microservice
- OAuth 2.0 / OpenID Connect support
- JWT token management
- User profile and preferences
- Role-based access control (RBAC)

**Integration:**

- All services authenticate via this service
- Token validation middleware
- User session management

#### Reporting Service (PLANNED)

**Purpose:** Report generation, export, and distribution

**Architecture:**

- Report generation engine
- Multiple export formats (PDF, Excel, CSV)
- Scheduled report generation
- Report templates and customization
- Distribution via email or download

**Integration:**

- Consumes data from analytics and database
- Integrates with notification service for distribution

## Technology Stack Details

### Backend Technologies

**Core Framework:**
- **Python**: 3.8+ with type hints
- **FastAPI**: Modern, fast web framework for APIs
- **SQLAlchemy**: ORM for database operations
- **APScheduler**: Advanced Python Scheduler for job management

**Data Collection:**
- **yfinance**: Yahoo Finance data collection
- **coinbase-advanced-py**: Coinbase Advanced API client
- **fredapi**: FRED (Federal Reserve Economic Data) API client

**Data Processing:**
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing

**Error Handling & Resilience:**
- **Tenacity**: Retry library with exponential backoff
- **ratelimit**: Rate limiting for API calls

**Database:**
- **PostgreSQL**: 16 with TimescaleDB extension
- **psycopg2**: PostgreSQL adapter
- **asyncpg**: Async PostgreSQL driver (future)

**Testing:**
- **pytest**: Testing framework
- **pytest-asyncio**: Async testing support

**Code Quality:**
- **Black**: Code formatter (line length: 100)
- **Flake8**: Linter
- **mypy**: Type checker

### Frontend Technologies

**Core Framework:**
- **React**: 18+ for UI components
- **TypeScript**: Type safety
- **Vite**: Build tool and dev server

**State Management:**
- **Redux Toolkit**: State management
- **React Router**: Client-side routing

**Styling:**
- **Tailwind CSS**: Utility-first CSS framework
- **PostCSS**: CSS processing

**API Communication:**
- **Axios**: HTTP client
- **WebSocket API**: Native WebSocket support

**Testing:**
- **Jest**: Testing framework
- **React Testing Library**: Component testing
- **Vitest**: Fast unit test runner

**Build & Deployment:**
- **Vite**: Production build
- **Nginx**: Web server for production

### Database Technologies

**Database Engine:**
- **PostgreSQL**: 16 relational database
- **TimescaleDB**: Time-series extension

**Features:**
- Hypertables for automatic partitioning
- Continuous aggregates (future)
- Data retention policies (future)
- Compression (future)

### Infrastructure Technologies

**Containerization:**
- **Docker**: Container runtime
- **Docker Compose**: Multi-container orchestration

**Future Considerations:**
- **Kubernetes**: Container orchestration for production
- **Terraform**: Infrastructure as code
- **CI/CD**: GitHub Actions, GitLab CI

## Deployment Architecture

### Development Environment

**Docker Compose Setup:**

- All services run locally via Docker Compose
- Hot reload for development (API and frontend)
- Local database with persistent volumes
- Environment variables via `.env` file

**Development Workflow:**

1. Start services: `docker-compose up`
2. API available at `http://localhost:8000`
3. Frontend available at `http://localhost:3000`
4. Database accessible at `localhost:5432`

### Production Considerations

**Scaling Strategies:**

- **Horizontal Scaling**: Multiple API service instances behind load balancer
- **Database Scaling**: Read replicas for read-heavy workloads
- **Caching**: Redis for frequently accessed data
- **CDN**: For frontend static assets

**High Availability:**

- Multiple service instances
- Database replication
- Health checks and auto-restart
- Monitoring and alerting

**Security:**

- HTTPS/TLS for all communications
- API authentication and authorization
- Database connection encryption
- Secrets management (AWS Secrets Manager, HashiCorp Vault)

### Monitoring and Observability

**Current:**

- Health check endpoints
- Prometheus metrics endpoint
- Application logging

**Future:**

- **Metrics**: Prometheus + Grafana dashboards
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: OpenTelemetry for distributed tracing
- **APM**: Application Performance Monitoring tools

## Security Architecture

### Current Security Measures

- **Input Validation**: Pydantic models for request validation
- **SQL Injection Prevention**: Parameterized queries via SQLAlchemy
- **CORS Configuration**: Configurable CORS middleware
- **Error Handling**: Secure error messages (no sensitive data exposure)
- **Logging**: Comprehensive logging without sensitive data

### Future Security Enhancements

**Authentication & Authorization:**

- JWT token-based authentication
- OAuth 2.0 / OpenID Connect
- Role-based access control (RBAC)
- API key management for external integrations

**Data Security:**

- Encryption at rest (database)
- Encryption in transit (TLS/SSL)
- Secrets management (environment variables, secret stores)
- Data masking for sensitive information

**API Security:**

- Rate limiting per user/API key
- Request signing for external APIs
- API versioning for backward compatibility
- Input sanitization and validation

**Compliance:**

- Financial regulations (SEC, FINRA) compliance
- Data privacy (GDPR, CCPA) compliance
- Audit trails for all financial operations
- Data retention policies

## Performance Considerations

### Database Optimization

**Current:**

- Composite primary keys for efficient lookups
- Indexes on foreign keys and frequently queried columns
- TimescaleDB hypertables for time-series optimization
- Connection pooling (min: 2, max: 20)

**Future:**

- Query optimization and EXPLAIN analysis
- Materialized views for complex queries
- Continuous aggregates for pre-computed metrics
- Partition pruning for time-range queries

### API Performance

**Current:**

- Async/await for non-blocking I/O
- Connection pooling for database
- Background tasks for long-running operations

**Future:**

- Response caching (Redis)
- API response compression
- Pagination optimization
- GraphQL for flexible queries (if needed)

### Frontend Optimization

**Current:**

- Code splitting with Vite
- Lazy loading for routes
- Optimized bundle size

**Future:**

- Image optimization
- CDN for static assets
- Service workers for offline support
- Virtual scrolling for large lists

### Caching Strategies

**Future:**

- **Application-Level**: In-memory caching for frequently accessed data
- **Database-Level**: Query result caching
- **API-Level**: Response caching with Redis
- **CDN**: Static asset caching

## Conclusion

The Investment Platform follows a modern, modular architecture designed for scalability, maintainability, and extensibility. The current implementation provides a solid foundation with clear service boundaries, comprehensive APIs, and robust data handling. Future enhancements, particularly the Analytics Service, will extend the platform's capabilities while maintaining architectural integrity and separation of concerns.

All services are containerized and can be deployed independently, enabling flexible scaling and deployment strategies. The API-first design ensures that new services can be integrated seamlessly, and the microservices architecture allows for independent development and deployment of new capabilities.

