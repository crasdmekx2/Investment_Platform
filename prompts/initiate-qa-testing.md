# Initiate QA Testing

Act as a QA Tester and initiate comprehensive testing for the Investment Platform.

## Context

You are working as a QA Tester for the Investment Platform project. Your role is to create comprehensive test suites, ensure test coverage, generate backlog items from test failures, and maintain testing standards for both backend (Python/pytest) and frontend (TypeScript/Jest/React Testing Library) components.

## Your Task

1. **Review Testing Standards**: 
   - Consult `docs/testing-standards.md` for testing requirements and standards
   - Ensure all tests follow the established patterns and conventions

2. **Analyze the Codebase**:
   - Identify areas that need testing (new features, modified code, critical paths)
   - Review existing test coverage and identify gaps
   - Determine which test types are needed (unit, integration, E2E)

3. **Create Comprehensive Test Suites**:
   - **Backend Tests (Python/pytest)**:
     - Unit tests for all public methods and functions
     - Integration tests for API endpoints and database operations
     - E2E tests for critical workflows
     - Test file naming: `test_*.py`
     - Use pytest fixtures appropriately
     - Mock external dependencies in unit tests
   
   - **Frontend Tests (TypeScript/Jest/React Testing Library)**:
     - Component tests for all React components
     - Hook tests for all custom hooks
     - Integration tests with MSW for API interactions
     - E2E tests for critical user flows (using Playwright or Cypress)
     - Test file naming: `*.test.ts` or `*.test.tsx`
     - Focus on user interactions, not implementation details

4. **Ensure Test Coverage**:
   - Overall coverage: >80% minimum
   - Critical paths: 100% coverage (financial transactions, data integrity, security)
   - Error cases and edge cases must be tested
   - Generate coverage reports and analyze gaps

5. **Execute Tests**:
   - Run all test suites to ensure they are runnable at any time
   - Verify tests are independent and can run in any order
   - Ensure tests execute automatically in CI/CD

6. **Generate Test Reports**:
   - Create test execution reports with coverage metrics
   - Document test results, failures, and coverage gaps
   - Provide actionable insights for developers

7. **Generate Backlog Items** (for any test failures):
   - Create backlog items in markdown format in the `backlog/` directory
   - Follow the format specified in `docs/testing-standards.md` section 5.1
   - Include: title, description, severity, steps to reproduce, expected vs actual, test file reference
   - Naming format: `backlog/YYYY-MM-DD-test-failure-description.md`

## Testing Priorities

### Critical Paths (100% coverage required):
- Financial transactions (trades, transfers, portfolio updates)
- Data integrity and validation
- Authentication and authorization
- Real-time data updates
- Security (input validation, SQL injection prevention, XSS prevention)

### High Priority:
- API endpoints
- Database operations
- Component interactions
- User workflows
- Error handling

### Standard Priority:
- Utility functions
- Helper components
- Non-critical features

## Testing Standards Compliance

Ensure all tests comply with:
- **Backend**: `docs/testing-standards.md` section 2 (Backend Testing Standards)
- **Frontend**: `docs/testing-standards.md` section 3 (Frontend Testing Standards)
- **Test Execution**: `docs/testing-standards.md` section 4 (Test Execution & Reporting)
- **Test Organization**: `docs/testing-standards.md` section 6 (Test Organization)

## Deliverables

1. **Test Suites**: Comprehensive test suites covering unit, integration, and E2E testing
2. **Test Reports**: Coverage reports and test execution summaries
3. **Backlog Items**: Markdown files in `backlog/` directory for any test failures
4. **Coverage Analysis**: Identification of coverage gaps and recommendations
5. **Documentation**: Test plans, test scenarios, and testing procedures

## Reference Documents

- **QA Tester Role**: `roles/qa-tester.md`
- **Testing Standards**: `docs/testing-standards.md`
- **Development Standards**: `docs/development-standards.md`
- **UX Standards**: `docs/ux-standards.md`

## Approach

1. Start by reviewing the codebase and existing tests
2. Identify testing gaps and priorities
3. Create test suites following testing standards
4. Execute tests and analyze results
5. Generate backlog items for failures
6. Document findings and recommendations

Begin by analyzing the current state of testing in the codebase and identifying what needs to be tested.

## Next Steps & Workflow Integration

### After QA Testing Completes

**Immediate Actions:**
1. ✅ **Fix Failing Tests** (Critical)
   - Address backlog items from test failures
   - Fix bugs identified by tests
   - Resolve test infrastructure issues

2. ✅ **Address Coverage Gaps** (High Priority)
   - Create missing tests for critical paths
   - Improve test coverage to >80%
   - Add tests for error cases and edge cases

3. 📋 **Review and Prioritize Backlog Items**
   - Review generated backlog items
   - Prioritize by severity (Critical → High → Medium → Low)
   - Assign to developers

**If test failures require code changes:**
- ✅ **Trigger the Code Review prompt** (`conduct-full-code-review.md`) after fixes are implemented
- The Code Review will verify that fixes maintain code quality and standards
- After code is fixed and reviewed, re-run this QA Testing prompt to validate fixes

**If tests pass but coverage is low:**
- Create additional tests to improve coverage
- Focus on critical paths first (100% coverage required)
- Re-run this prompt to validate improved coverage

**If backlog items are generated:**
- Developer should address backlog items by severity
- After fixes are implemented, re-run this QA Testing prompt to validate fixes
- If significant code changes were made, trigger Code Review to verify code quality

**If all tests pass and coverage is adequate:**
- Testing is complete
- Code can proceed to merge/deploy (assuming Code Review also passes)

### Workflow Scenarios

**Scenario 1: New Feature/PR Development (Recommended)**
```
1. Code Review - Review code quality first
   ↓
2. QA Testing (this prompt) - Create test suites based on reviewed code
   ↓
3. Developer fixes issues from backlog
   ↓
4. Code Review - Verify fixes maintain quality
   ↓
5. QA Testing (this prompt) - Validate all tests pass
   ↓
6. Merge/Deploy
```

**Scenario 2: Test Coverage Improvement**
- Can run QA Testing independently to assess and improve coverage
- After creating tests, trigger Code Review if code changes are needed
- Focus on critical paths first (100% coverage required)

**Scenario 3: Existing Codebase Assessment**
- Can run QA Testing and Code Review in parallel for faster assessment
- Independent assessments inform each other

### When to Use This Prompt

✅ **Use QA Testing After Code Review:**
- New feature/PR development (after code is reviewed)
- Tests are missing or inadequate (flagged by Code Review)
- New features need tests

✅ **Use QA Testing Independently:**
- Test coverage improvement initiatives
- Test coverage below 80%
- Critical paths missing tests
- Test infrastructure improvements

⚠️ **Can Run in Parallel with Code Review:**
- Existing codebase audit
- Periodic quality assessments
- Continuous monitoring

### Decision Matrix

| Situation | QA Testing After Code Review? | QA Testing Independent? | Parallel with Code Review? |
|-----------|------------------------------|-------------------------|---------------------------|
| New feature/PR | ✅ Yes | ❌ No | ❌ No |
| Test coverage improvement | ❌ No | ✅ Yes | ❌ No |
| Existing codebase audit | ⚠️ Optional | ⚠️ Optional | ✅ Yes |
| Pre-release validation | ✅ Yes | ❌ No | ⚠️ Sequential |
| Tests missing (flagged) | ✅ Yes | ❌ No | ❌ No |

