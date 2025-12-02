# Testing Standards

## Introduction & Purpose

This document establishes the testing standards for the Investment Platform, covering both backend (Python/pytest) and frontend (TypeScript/Jest/React Testing Library) development. All code implementations must adhere to these standards to ensure consistent, maintainable, and high-quality test coverage. These standards are based on industry best practices, modern testing methodologies, and the specific requirements of financial data processing and trading applications.

**Purpose:**
- Ensure consistent test quality across all backend and frontend features
- Maintain comprehensive test coverage (>80% minimum, 100% for critical paths)
- Guide developers in implementing robust, reliable test suites
- Establish clear patterns for unit, integration, and end-to-end testing
- Enable automated test execution and backlog item generation
- Provide actionable checklists and implementation guidelines

**Who Should Use This Document:**
- Backend engineers writing Python tests with pytest
- Frontend engineers writing TypeScript/React tests with Jest and React Testing Library
- QA engineers creating and maintaining test suites
- Code reviewers ensuring testing standards compliance
- DevOps engineers integrating tests into CI/CD pipelines

**Reference Documents:**
- [QA Tester Role](../roles/qa-tester.md)
- [Python Developer Role](../roles/python-developer.md)
- [Front End Engineer Role](../roles/front-end-engineer.md)
- [Development Standards](./development-standards.md)
- [UX Standards](./ux-standards.md)

---

## 1. Test Types & Requirements

### 1.1 Unit Tests

**MANDATORY:** All public functions, methods, and components MUST have unit tests.

**Requirements:**
- Test individual functions/methods in isolation
- Mock external dependencies (APIs, databases, file systems)
- Test both happy paths and error cases
- Test edge cases and boundary conditions
- Aim for >80% code coverage (100% for critical paths)

**Backend Unit Tests:**
- Test all public methods of classes
- Test utility functions and helpers
- Test data transformation and validation logic
- Test error handling and exception paths

**Frontend Unit Tests:**
- Test React components in isolation
- Test custom hooks independently
- Test utility functions and helpers
- Test state management logic (Redux slices, Zustand stores)

**Checklist:**
- [ ] All public functions/methods have unit tests
- [ ] Error cases are tested
- [ ] Edge cases and boundary conditions are tested
- [ ] External dependencies are mocked appropriately
- [ ] Tests are fast and can run independently
- [ ] Test coverage >80% for unit tests

### 1.2 Integration Tests

**MANDATORY:** Component interactions, API endpoints, and database operations MUST have integration tests.

**Requirements:**
- Test interactions between components/modules
- Test API endpoints with real request/response cycles
- Test database operations with test databases
- Test external service integrations (with mocks or test environments)
- Verify data flow between components

**Backend Integration Tests:**
- Test API endpoint handlers with request/response
- Test database operations (CRUD operations, transactions)
- Test data pipeline components working together
- Test service layer interactions

**Frontend Integration Tests:**
- Test component interactions and data flow
- Test API integration with MSW (Mock Service Worker)
- Test state management with multiple components
- Test form submissions and user interactions

**Checklist:**
- [ ] Component interactions are tested
- [ ] API endpoints have integration tests
- [ ] Database operations are tested
- [ ] External service integrations are tested
- [ ] Data flow between components is verified
- [ ] Integration tests use test databases/environments

### 1.3 End-to-End (E2E) Tests

**MANDATORY:** Critical user flows and financial transactions MUST have E2E tests.

**Requirements:**
- Test complete user workflows from start to finish
- Test critical financial operations (trades, transfers, portfolio updates)
- Test real-time data updates and WebSocket connections
- Test error scenarios and recovery flows
- Use E2E testing frameworks (Playwright, Cypress)

**Critical E2E Test Scenarios:**
- User authentication and authorization flows
- Financial transaction flows (buy/sell orders, transfers)
- Portfolio management workflows
- Real-time market data updates
- Data visualization and chart interactions
- Error handling and recovery flows

**Checklist:**
- [ ] Critical user flows have E2E tests
- [ ] Financial transactions are tested end-to-end
- [ ] Real-time data updates are tested
- [ ] Error scenarios and recovery are tested
- [ ] E2E tests are stable and reliable
- [ ] E2E tests run in CI/CD pipeline

### 1.4 Performance Tests

**Requirements:**
- Test API response times
- Test database query performance
- Test frontend rendering performance
- Test load handling for high-frequency data updates
- Identify performance bottlenecks

**Checklist:**
- [ ] API endpoints have performance benchmarks
- [ ] Database queries are optimized and tested
- [ ] Frontend rendering performance is tested
- [ ] Load testing for high-frequency scenarios
- [ ] Performance regressions are caught early

### 1.5 Security Tests

**MANDATORY:** Input validation, authentication, and authorization MUST be tested.

**Requirements:**
- Test input validation and sanitization
- Test authentication flows
- Test authorization and access control
- Test SQL injection prevention
- Test XSS (Cross-Site Scripting) prevention
- Test CSRF (Cross-Site Request Forgery) protection

**Checklist:**
- [ ] Input validation is tested
- [ ] Authentication flows are tested
- [ ] Authorization and access control are tested
- [ ] Security vulnerabilities are prevented
- [ ] OWASP Top 10 vulnerabilities are addressed

### 1.6 Accessibility Tests

**MANDATORY:** All frontend components MUST meet WCAG 2.2 AA standards and be tested for accessibility.

**Requirements:**
- Test keyboard navigation
- Test screen reader compatibility
- Test color contrast ratios
- Test ARIA attributes
- Test focus management
- Use accessibility testing tools (axe-core, jest-axe)

**Checklist:**
- [ ] Keyboard navigation is tested
- [ ] Screen reader compatibility is tested
- [ ] Color contrast meets WCAG 2.2 AA standards
- [ ] ARIA attributes are correct and tested
- [ ] Focus management is tested
- [ ] Accessibility violations are caught in tests

---

## 2. Backend Testing Standards (Python/pytest)

### 2.1 Test File Naming

**MANDATORY:** All test files MUST follow the naming convention `test_*.py`.

**Naming Convention:**
- Test files: `test_*.py` (e.g., `test_ingestion_engine.py`)
- Test classes: `Test*` (e.g., `TestIngestionEngine`)
- Test functions: `test_*` (e.g., `test_ingest_success`)

**File Organization:**
```
tests/
├── test_ingestion_engine.py
├── test_schema_mapper.py
├── test_data_loader.py
├── integration/
│   ├── test_api_endpoints.py
│   └── test_database_operations.py
└── e2e/
    └── test_complete_workflows.py
```

**Checklist:**
- [ ] All test files follow `test_*.py` naming convention
- [ ] Test files are organized logically
- [ ] Integration and E2E tests are in separate directories

### 2.2 Test Structure

**MANDATORY:** Tests MUST be well-structured using pytest classes and fixtures.

**Test Structure:**
```python
# ✅ Good: Well-structured test
import pytest
from investment_platform.ingestion.ingestion_engine import IngestionEngine
from investment_platform.ingestion.exceptions import ValidationError

class TestIngestionEngine:
    """Test suite for IngestionEngine."""
    
    @pytest.fixture
    def engine(self):
        """Create IngestionEngine instance for testing."""
        return IngestionEngine(incremental=False)
    
    def test_ingest_success(self, engine):
        """Test successful data ingestion."""
        result = engine.ingest(
            symbol="AAPL",
            asset_type="stock",
            start_date="2024-01-01",
            end_date="2024-01-31",
        )
        
        assert result["status"] == "success"
        assert result["records_loaded"] > 0
        assert result["asset_id"] is not None
    
    def test_ingest_invalid_symbol(self, engine):
        """Test ingestion with invalid symbol."""
        with pytest.raises(ValidationError):
            engine.ingest(
                symbol="INVALID",
                asset_type="stock",
                start_date="2024-01-01",
                end_date="2024-01-31",
            )
```

**Checklist:**
- [ ] Tests are organized into test classes
- [ ] Test functions have descriptive names
- [ ] Tests use fixtures for setup/teardown
- [ ] Tests are independent and can run in any order
- [ ] Test docstrings describe what is being tested

### 2.3 Test Coverage Requirements

**MANDATORY:** Code coverage MUST be >80% overall, and 100% for critical paths.

**Coverage Requirements:**
- Overall code coverage: >80%
- Critical paths: 100% (financial transactions, data integrity, security)
- Error handling paths: Must be tested
- Edge cases: Must be tested

**Running Coverage:**
```bash
# Run tests with coverage
pytest --cov=src/investment_platform --cov-report=html --cov-report=term

# Generate HTML coverage report
pytest --cov=src/investment_platform --cov-report=html
# Open htmlcov/index.html in browser

# Check coverage threshold
pytest --cov=src/investment_platform --cov-report=term --cov-fail-under=80
```

**Checklist:**
- [ ] Overall coverage >80%
- [ ] Critical paths have 100% coverage
- [ ] Error handling paths are tested
- [ ] Edge cases are tested
- [ ] Coverage reports are generated and reviewed

### 2.4 Test Fixtures

**MANDATORY:** Common setup/teardown MUST use pytest fixtures.

**Fixture Patterns:**
```python
# ✅ Good: Reusable fixtures
import pytest
from investment_platform.ingestion.db_connection import get_db_connection

@pytest.fixture
def db_connection():
    """Provide database connection for testing."""
    conn = get_db_connection()
    yield conn
    conn.close()

@pytest.fixture
def sample_market_data():
    """Provide sample market data DataFrame."""
    return pd.DataFrame({
        'open': [100.0, 101.0],
        'high': [105.0, 106.0],
        'low': [99.0, 100.0],
        'close': [103.0, 104.0],
        'volume': [1000000, 1100000],
    }, index=[
        pd.Timestamp('2024-01-01'),
        pd.Timestamp('2024-01-02'),
    ])

@pytest.fixture
def mock_collector(monkeypatch):
    """Mock data collector for testing."""
    def mock_collect(symbol, start_date, end_date):
        return pd.DataFrame({
            'open': [100.0],
            'high': [105.0],
            'low': [99.0],
            'close': [103.0],
        }, index=[pd.Timestamp('2024-01-01')])
    
    monkeypatch.setattr(
        'investment_platform.collectors.StockCollector.collect_historical_data',
        mock_collect
    )
```

**Fixture Scopes:**
- `function`: Default scope, fixture runs for each test function
- `class`: Fixture runs once per test class
- `module`: Fixture runs once per test module
- `session`: Fixture runs once per test session

**Checklist:**
- [ ] Fixtures used for common setup/teardown
- [ ] Database fixtures properly clean up after tests
- [ ] Mock fixtures used for external dependencies
- [ ] Fixtures are reusable across test files
- [ ] Fixture scopes are appropriate (function, class, module, session)

### 2.5 Mocking and Test Doubles

**MANDATORY:** External dependencies MUST be mocked in unit tests.

**Mocking Patterns:**
```python
# ✅ Good: Mocking external dependencies
import pytest
from unittest.mock import Mock, patch, MagicMock

def test_collect_data_with_mock_api(monkeypatch):
    """Test data collection with mocked API."""
    mock_response = {
        'data': [{'price': 100.0, 'volume': 1000000}]
    }
    
    def mock_api_call(*args, **kwargs):
        return mock_response
    
    monkeypatch.setattr(
        'investment_platform.collectors.StockCollector._fetch_data',
        mock_api_call
    )
    
    collector = StockCollector()
    result = collector.collect_historical_data('AAPL', '2024-01-01', '2024-01-31')
    
    assert len(result) > 0
    assert result['price'].iloc[0] == 100.0

# Using pytest-mock
def test_with_pytest_mock(mocker):
    """Test using pytest-mock."""
    mock_api = mocker.patch('investment_platform.collectors.StockCollector._fetch_data')
    mock_api.return_value = {'data': [{'price': 100.0}]}
    
    collector = StockCollector()
    result = collector.collect_historical_data('AAPL', '2024-01-01', '2024-01-31')
    
    mock_api.assert_called_once()
    assert len(result) > 0
```

**Checklist:**
- [ ] External dependencies are mocked in unit tests
- [ ] API calls are mocked appropriately
- [ ] Database operations use test databases or mocks
- [ ] File system operations are mocked when needed
- [ ] Mocks are reset between tests

### 2.6 Database Testing

**MANDATORY:** Database tests MUST use test databases and clean up after tests.

**Database Testing Patterns:**
```python
# ✅ Good: Database testing with fixtures
import pytest
from investment_platform.ingestion.db_connection import get_db_connection

@pytest.fixture
def db_connection():
    """Provide test database connection."""
    conn = get_db_connection(test=True)  # Use test database
    yield conn
    # Cleanup
    with conn.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE market_data CASCADE")
    conn.commit()
    conn.close()

def test_load_data(db_connection):
    """Test loading data into database."""
    loader = DataLoader()
    data = pd.DataFrame({
        'time': [pd.Timestamp('2024-01-01')],
        'asset_id': [1],
        'open': [100.0],
        'high': [105.0],
        'low': [99.0],
        'close': [103.0],
        'volume': [1000000],
    })
    
    records_loaded = loader.load_data(data, db_connection)
    
    assert records_loaded == 1
    
    # Verify data in database
    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM market_data WHERE asset_id = %s",
            (1,)
        )
        count = cursor.fetchone()[0]
        assert count == 1
```

**Checklist:**
- [ ] Database tests use test databases
- [ ] Test data is cleaned up after tests
- [ ] Transactions are properly managed
- [ ] Database fixtures use appropriate scopes
- [ ] Database tests are isolated from each other

---

## 3. Frontend Testing Standards (TypeScript/Jest/React Testing Library)

### 3.1 Test File Naming

**MANDATORY:** All test files MUST follow the naming convention `*.test.ts` or `*.test.tsx`.

**Naming Convention:**
- Test files: `*.test.ts` or `*.test.tsx` (e.g., `Button.test.tsx`, `useApi.test.ts`)
- Test files should be co-located with source files or in `__tests__` directories

**File Organization:**
```
src/
├── components/
│   ├── Button/
│   │   ├── Button.tsx
│   │   └── Button.test.tsx
│   └── Card/
│       ├── Card.tsx
│       └── Card.test.tsx
├── hooks/
│   ├── useApi.ts
│   └── useApi.test.ts
└── __tests__/
    └── integration/
        └── api.test.ts
```

**Checklist:**
- [ ] All test files follow `*.test.ts` or `*.test.tsx` naming convention
- [ ] Test files are co-located with source files or in `__tests__` directories
- [ ] Integration and E2E tests are in separate directories

### 3.2 Component Testing

**MANDATORY:** All React components MUST have component tests using React Testing Library.

**Component Testing Patterns:**
```typescript
// ✅ Good: Component test with React Testing Library
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button', () => {
  it('renders button with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByRole('button', { name: /click me/i }));
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('disables button when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

**Testing Principles:**
- Test user interactions, not implementation details
- Use semantic queries (getByRole, getByLabelText, getByText)
- Test accessibility (keyboard navigation, ARIA attributes)
- Test error states and loading states

**Checklist:**
- [ ] All components have component tests
- [ ] Tests use React Testing Library
- [ ] Tests focus on user interactions, not implementation
- [ ] Accessibility is tested (keyboard navigation, ARIA)
- [ ] Error and loading states are tested

### 3.3 Hook Testing

**MANDATORY:** All custom hooks MUST have hook tests.

**Hook Testing Patterns:**
```typescript
// ✅ Good: Custom hook test
import { renderHook, act } from '@testing-library/react';
import { useApi } from './useApi';

describe('useApi', () => {
  it('fetches data successfully', async () => {
    const mockData = { id: 1, name: 'Test' };
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: async () => mockData,
    });

    const { result, waitForNextUpdate } = renderHook(() => useApi('/api/data'));

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();

    await waitForNextUpdate();

    expect(result.current.loading).toBe(false);
    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBeNull();
  });

  it('handles errors', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

    const { result, waitForNextUpdate } = renderHook(() => useApi('/api/data'));

    await waitForNextUpdate();

    expect(result.current.loading).toBe(false);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeTruthy();
  });
});
```

**Checklist:**
- [ ] All custom hooks have hook tests
- [ ] Tests use renderHook from React Testing Library
- [ ] Async operations are properly tested
- [ ] Error cases are tested

### 3.4 Integration Testing with MSW

**MANDATORY:** API integration MUST be tested using MSW (Mock Service Worker).

**MSW Integration Testing:**
```typescript
// ✅ Good: Integration test with MSW
import { render, screen, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import { Portfolio } from './Portfolio';

const server = setupServer(
  rest.get('/api/portfolio', (req, res, ctx) => {
    return res(ctx.json({
      holdings: [
        { symbol: 'AAPL', shares: 100, price: 150.0 },
      ],
    }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Portfolio Integration', () => {
  it('loads and displays portfolio data', async () => {
    render(<Portfolio />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
    });
  });
});
```

**Checklist:**
- [ ] API integration is tested with MSW
- [ ] MSW server is set up and torn down properly
- [ ] API error cases are tested
- [ ] Loading and error states are tested

### 3.5 End-to-End Testing

**MANDATORY:** Critical user flows MUST have E2E tests using Playwright or Cypress.

**Playwright E2E Testing:**
```typescript
// ✅ Good: E2E test with Playwright
import { test, expect } from '@playwright/test';

test('user can place a trade order', async ({ page }) => {
  // Navigate to trading page
  await page.goto('/trading');
  
  // Login (if needed)
  await page.fill('[data-testid="username"]', 'testuser');
  await page.fill('[data-testid="password"]', 'password');
  await page.click('[data-testid="login-button"]');
  
  // Place order
  await page.fill('[data-testid="symbol-input"]', 'AAPL');
  await page.fill('[data-testid="quantity-input"]', '10');
  await page.selectOption('[data-testid="order-type"]', 'market');
  await page.click('[data-testid="submit-order"]');
  
  // Verify order confirmation
  await expect(page.locator('[data-testid="order-confirmation"]')).toBeVisible();
  await expect(page.locator('[data-testid="order-confirmation"]')).toContainText('Order placed successfully');
});
```

**Checklist:**
- [ ] Critical user flows have E2E tests
- [ ] E2E tests use Playwright or Cypress
- [ ] Tests are stable and reliable
- [ ] Tests run in CI/CD pipeline
- [ ] E2E tests cover financial transactions

---

## 4. Test Execution & Reporting

### 4.1 Test Execution

**MANDATORY:** Tests MUST be runnable at any time and execute automatically in CI/CD.

**Running Tests:**
```bash
# Backend: Run all tests
pytest

# Backend: Run with coverage
pytest --cov=src/investment_platform --cov-report=html

# Frontend: Run all tests
npm test

# Frontend: Run with coverage
npm test -- --coverage

# Run specific test file
pytest tests/test_ingestion_engine.py
npm test Button.test.tsx

# Run specific test
pytest tests/test_ingestion_engine.py::TestIngestionEngine::test_ingest_success
npm test -- Button.test.tsx -t "renders button"
```

**CI/CD Integration:**
- Tests must run automatically on every commit
- Tests must run on pull requests
- Test failures must block merges
- Coverage reports must be generated

**Checklist:**
- [ ] Tests are runnable at any time
- [ ] Tests execute automatically in CI/CD
- [ ] Test failures block merges
- [ ] Coverage reports are generated
- [ ] Test execution is fast and efficient

### 4.2 Test Reporting

**MANDATORY:** Test reports MUST be generated with coverage metrics and failure details.

**Test Report Requirements:**
- Coverage metrics (overall, by file, by function)
- Test execution summary (passed, failed, skipped)
- Failure details with stack traces
- Test execution time
- HTML reports for easy viewing

**Backend Test Reports:**
```bash
# Generate HTML report
pytest --cov=src/investment_platform --cov-report=html --html=report.html

# Generate Allure report
pytest --alluredir=allure-results
allure serve allure-results
```

**Frontend Test Reports:**
```bash
# Generate coverage report
npm test -- --coverage --coverageReporters=html

# Generate Jest HTML report
npm test -- --reporters=default --reporters=jest-html-reporter
```

**Checklist:**
- [ ] Test reports include coverage metrics
- [ ] Test reports include failure details
- [ ] HTML reports are generated for easy viewing
- [ ] Reports are accessible to all team members
- [ ] Reports are archived for historical tracking

---

## 5. Backlog Item Generation

### 5.1 Backlog Item Format

**MANDATORY:** Test failures MUST generate backlog items in markdown format in the `backlog/` directory.

**Backlog Item Structure:**
```markdown
# [SEVERITY] Title of the Issue

## Description
Brief description of the test failure and issue.

## Test File Reference
- File: `tests/test_ingestion_engine.py`
- Test: `TestIngestionEngine::test_ingest_invalid_symbol`
- Line: 45

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen when the test passes.

## Actual Behavior
What actually happens when the test fails.

## Error Message
```
Full error message and stack trace
```

## Severity
- **Critical**: Blocks critical functionality (financial transactions, data integrity)
- **High**: Blocks important functionality
- **Medium**: Affects non-critical functionality
- **Low**: Minor issue or enhancement

## Additional Context
Any additional information, screenshots, or context that helps understand the issue.

## Related Issues
- Related backlog items or issues
```

**Backlog Item Naming:**
- Format: `backlog/YYYY-MM-DD-test-failure-description.md`
- Example: `backlog/2024-01-15-ingestion-engine-validation-error.md`

**Checklist:**
- [ ] Backlog items are generated from test failures
- [ ] Backlog items follow the markdown format
- [ ] Backlog items include all required sections
- [ ] Backlog items are stored in `backlog/` directory
- [ ] Backlog items have clear severity classification

### 5.2 Automated Backlog Generation

**Implementation:**
- Test failures should automatically generate backlog items
- Backlog items should be created with consistent format
- Severity should be automatically classified based on test type and failure
- Test file references should be automatically included

**Checklist:**
- [ ] Backlog generation is automated
- [ ] Backlog items have consistent format
- [ ] Severity is automatically classified
- [ ] Test references are automatically included

---

## 6. Test Organization

### 6.1 Test Directory Structure

**Backend Test Structure:**
```
tests/
├── unit/
│   ├── test_ingestion_engine.py
│   ├── test_schema_mapper.py
│   └── test_data_loader.py
├── integration/
│   ├── test_api_endpoints.py
│   └── test_database_operations.py
├── e2e/
│   └── test_complete_workflows.py
└── fixtures/
    ├── conftest.py
    └── test_data.py
```

**Frontend Test Structure:**
```
src/
├── components/
│   └── Button/
│       ├── Button.tsx
│       └── Button.test.tsx
├── hooks/
│   ├── useApi.ts
│   └── useApi.test.ts
├── __tests__/
│   ├── integration/
│   │   └── api.test.ts
│   └── e2e/
│       └── trading-flow.test.ts
└── test-utils/
    ├── test-utils.tsx
    └── mocks.ts
```

**Checklist:**
- [ ] Tests are organized by type (unit, integration, E2E)
- [ ] Test fixtures are in dedicated directories
- [ ] Test utilities are reusable
- [ ] Test structure is consistent across the project

### 6.2 Test Data Management

**MANDATORY:** Test data MUST be managed through fixtures and factories.

**Test Data Patterns:**
```python
# ✅ Good: Test data factory
from factory import Factory, Faker
import pandas as pd
from datetime import datetime

class MarketDataFactory:
    """Factory for creating test market data."""
    
    @staticmethod
    def create_market_data(
        symbol: str = "AAPL",
        date: datetime = None,
        price: float = 100.0,
    ) -> pd.DataFrame:
        """Create test market data DataFrame."""
        if date is None:
            date = datetime(2024, 1, 1)
        
        return pd.DataFrame({
            'time': [date],
            'asset_id': [1],
            'open': [price],
            'high': [price * 1.05],
            'low': [price * 0.99],
            'close': [price * 1.03],
            'volume': [1000000],
        })
```

**Checklist:**
- [ ] Test data is created through factories
- [ ] Test data is isolated and doesn't affect other tests
- [ ] Test data is realistic and representative
- [ ] Test data is easy to customize for different scenarios

---

## 7. Code Review Checklist

### Backend Testing Checklist

When reviewing backend code, verify:

- [ ] All public functions/methods have unit tests
- [ ] Integration tests for component interactions
- [ ] Error cases and edge cases are tested
- [ ] Test coverage >80% (100% for critical paths)
- [ ] Tests use pytest fixtures appropriately
- [ ] External dependencies are mocked in unit tests
- [ ] Database tests use test databases and clean up
- [ ] Tests are independent and can run in any order
- [ ] Test names are descriptive and clear
- [ ] Test docstrings describe what is being tested

### Frontend Testing Checklist

When reviewing frontend code, verify:

- [ ] All components have component tests
- [ ] All custom hooks have hook tests
- [ ] API integration is tested with MSW
- [ ] Critical user flows have E2E tests
- [ ] Accessibility is tested (keyboard navigation, ARIA)
- [ ] Error and loading states are tested
- [ ] Tests use React Testing Library (not Enzyme)
- [ ] Tests focus on user interactions, not implementation
- [ ] Test coverage >80% (100% for critical paths)
- [ ] Tests are independent and can run in any order

---

## 8. Quick Reference

### Common Commands

**Backend Testing:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/investment_platform --cov-report=html

# Run specific test file
pytest tests/test_ingestion_engine.py

# Run specific test
pytest tests/test_ingestion_engine.py::TestIngestionEngine::test_ingest_success

# Run with verbose output
pytest -v

# Run and stop on first failure
pytest -x
```

**Frontend Testing:**
```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test Button.test.tsx

# Run in watch mode
npm test -- --watch

# Run with verbose output
npm test -- --verbose
```

### Test Templates

**Backend Test Template:**
```python
import pytest
from investment_platform.module import MyClass

class TestMyClass:
    """Test suite for MyClass."""
    
    @pytest.fixture
    def instance(self):
        """Create MyClass instance for testing."""
        return MyClass()
    
    def test_method_success(self, instance):
        """Test successful method execution."""
        result = instance.method(param="value")
        assert result == expected_value
    
    def test_method_error(self, instance):
        """Test method error handling."""
        with pytest.raises(ExpectedError):
            instance.method(param="invalid")
```

**Frontend Component Test Template:**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { Component } from './Component';

describe('Component', () => {
  it('renders correctly', () => {
    render(<Component />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('handles user interaction', () => {
    const handleClick = jest.fn();
    render(<Component onClick={handleClick} />);
    
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

---

## Resources

### External Resources
- [pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [React Testing Library Documentation](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)
- [MSW Documentation](https://mswjs.io/)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)

### Internal Resources
- [QA Tester Role](../roles/qa-tester.md)
- [Python Developer Role](../roles/python-developer.md)
- [Front End Engineer Role](../roles/front-end-engineer.md)
- [Development Standards](./development-standards.md)
- [UX Standards](./ux-standards.md)

---

**Last Updated:** 2024
**Version:** 1.0
**Maintained By:** QA Team

