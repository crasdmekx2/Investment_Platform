# Test Failure Workflow

## Overview

This document outlines the complete process for handling test failures in CI/CD, from identification to resolution. This workflow ensures that all test failures are properly addressed, documented, and tracked.

## Table of Contents

1. [Identifying Test Failures](#1-identifying-test-failures)
2. [Reproducing Failures Locally](#2-reproducing-failures-locally)
3. [Debugging and Investigation](#3-debugging-and-investigation)
4. [Fixing the Code](#4-fixing-the-code)
5. [Verifying Fixes](#5-verifying-fixes)
6. [Creating Backlog Items](#6-creating-backlog-items)
7. [Re-running Tests](#7-re-running-tests)
8. [Best Practices](#8-best-practices)

---

## 1. Identifying Test Failures

### In GitHub Actions

When tests fail in CI/CD, you'll see:

1. **Red X icon** on your commit or pull request
2. **Failed workflow** in the Actions tab
3. **Detailed logs** showing which tests failed

### Accessing Test Results

1. Go to your repository on GitHub
2. Click on the **Actions** tab
3. Find the failed workflow run
4. Click on the failed job (e.g., "Backend Tests" or "Frontend Tests")
5. Expand the "Run backend tests with coverage" step to see detailed output

### Understanding Test Failure Output

The CI/CD output will show:
- **Test name** that failed
- **Error message** and stack trace
- **File and line number** where the failure occurred
- **Coverage information** (if applicable)

Example failure output:
```
FAILED tests/test_api_routers_scheduler.py::TestSchedulerRouter::test_create_job_success
AssertionError: assert response.status_code == 201
  assert 500 == 201
```

---

## 2. Reproducing Failures Locally

**CRITICAL:** Always reproduce test failures locally before fixing them.

### Step 1: Pull Latest Code

```bash
git pull origin main  # or your branch name
```

### Step 2: Set Up Test Environment

**Backend Tests:**
```bash
# Ensure you have the test database running
docker-compose up -d

# Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=investment_platform_test
export DB_USER=postgres
export DB_PASSWORD=postgres

# Install dependencies (if needed)
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

**Frontend Tests:**
```bash
cd frontend
npm install
```

### Step 3: Run the Failing Test

**Backend:**
```bash
# Run the specific failing test
pytest tests/test_api_routers_scheduler.py::TestSchedulerRouter::test_create_job_success -v

# Or run with more verbose output
pytest tests/test_api_routers_scheduler.py::TestSchedulerRouter::test_create_job_success -vv -s
```

**Frontend:**
```bash
cd frontend
npm test -- TestComponent.test.tsx -t "test name"
```

### Step 4: Verify You Can Reproduce

- ✅ If you can reproduce locally: Proceed to [Debugging](#3-debugging-and-investigation)
- ❌ If you cannot reproduce: Check for environment differences (see [Troubleshooting](#troubleshooting))

---

## 3. Debugging and Investigation

### Understanding the Failure

1. **Read the error message carefully**
   - What assertion failed?
   - What was the expected value?
   - What was the actual value?

2. **Check the stack trace**
   - Which file and line number?
   - What function was being called?
   - What was the call chain?

3. **Review the test code**
   - What is the test trying to verify?
   - What are the test setup steps?
   - What are the test assumptions?

### Debugging Techniques

**Backend (Python/pytest):**

```bash
# Run with pdb debugger
pytest tests/test_file.py::test_name --pdb

# Run with print statements (add to test)
pytest tests/test_file.py::test_name -s

# Run with verbose output
pytest tests/test_file.py::test_name -vv

# Run with coverage to see what code executed
pytest tests/test_file.py::test_name --cov=src/investment_platform --cov-report=term-missing
```

**Frontend (TypeScript/Vitest):**

```bash
cd frontend

# Run with UI for debugging
npm run test:ui

# Run with verbose output
npm test -- --reporter=verbose

# Run with debugger (add debugger; statement in test)
npm test -- --inspect-brk
```

### Common Failure Types

1. **Assertion Errors**
   - Expected value doesn't match actual value
   - Check data transformations, calculations, or API responses

2. **Import Errors**
   - Module not found
   - Check imports and dependencies

3. **Type Errors**
   - Type mismatch
   - Check type definitions and conversions

4. **Database Errors**
   - Connection issues
   - Check database setup and migrations

5. **Timing Issues**
   - Race conditions
   - Add appropriate waits or mocks

---

## 4. Fixing the Code

### Fix Strategy

1. **Identify the root cause**
   - Is it a bug in the code?
   - Is it a bug in the test?
   - Is it an environment issue?

2. **Make the minimal fix**
   - Fix only what's necessary
   - Don't refactor unrelated code
   - Keep changes focused

3. **Follow coding standards**
   - Use Black formatter (backend)
   - Use Prettier formatter (frontend)
   - Follow type hints (backend)
   - Follow TypeScript types (frontend)

### Example Fix Process

**Before:**
```python
def create_job(job_data: JobCreate) -> JobResponse:
    # Missing error handling
    job = scheduler_svc.create_job(job_data)
    return job
```

**After:**
```python
def create_job(job_data: JobCreate) -> JobResponse:
    try:
        job = scheduler_svc.create_job(job_data)
        return job
    except ValidationError as e:
        logger.warning(f"Validation error creating job: {e}")
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
```

### Code Review Checklist

Before committing your fix:
- [ ] Code follows project style guidelines
- [ ] Type hints/types are correct
- [ ] Error handling is appropriate
- [ ] Logging is added (if needed)
- [ ] Comments explain complex logic
- [ ] No hardcoded values or secrets

---

## 5. Verifying Fixes

### Step 1: Run the Specific Test

```bash
# Backend
pytest tests/test_api_routers_scheduler.py::TestSchedulerRouter::test_create_job_success -v

# Frontend
cd frontend
npm test -- TestComponent.test.tsx -t "test name"
```

### Step 2: Run Related Tests

```bash
# Run all tests in the same file
pytest tests/test_api_routers_scheduler.py -v

# Run all tests in the same module
pytest tests/test_api_routers/ -v
```

### Step 3: Run Full Test Suite

```bash
# Backend - all tests
pytest

# Backend - with coverage
pytest --cov=src/investment_platform --cov-report=html

# Frontend - all tests
cd frontend
npm test

# Frontend - with coverage
cd frontend
npm run test:coverage
```

### Step 4: Check for Regressions

- Run tests that might be affected by your change
- Check if any other tests now fail
- Verify coverage hasn't decreased

---

## 6. Creating Backlog Items

**MANDATORY:** All test failures must generate backlog items per [Testing Standards](./testing-standards.md#5-backlog-item-generation).

### When to Create Backlog Items

- ✅ Test failure indicates a real bug
- ✅ Test failure requires investigation
- ✅ Test failure is non-trivial to fix
- ❌ Test failure is a simple typo (fix immediately)
- ❌ Test failure is a test bug (fix test, no backlog needed)

### Backlog Item Format

Create a file in `backlog/` directory:

**Filename:** `backlog/YYYY-MM-DD-test-failure-description.md`

**Template:**
```markdown
# [SEVERITY] Title of the Issue

## Description
Brief description of the test failure and issue.

## Test File Reference
- File: `tests/test_api_routers_scheduler.py`
- Test: `TestSchedulerRouter::test_create_job_success`
- Line: 45

## Steps to Reproduce
1. Run the test: `pytest tests/test_api_routers_scheduler.py::TestSchedulerRouter::test_create_job_success`
2. Observe the failure

## Expected Behavior
The test should pass, creating a job successfully.

## Actual Behavior
The test fails with HTTP 500 error.

## Error Message
```
AssertionError: assert response.status_code == 201
  assert 500 == 201
```

## Severity
- **Critical**: Blocks critical functionality
- **High**: Blocks important functionality
- **Medium**: Affects non-critical functionality
- **Low**: Minor issue

## Additional Context
- CI/CD run: [link to GitHub Actions run]
- Related PR: [link to PR if applicable]

## Recommended Fix
1. Add proper error handling in `create_job` function
2. Handle ValidationError exceptions
3. Return appropriate HTTP status codes

## Related Issues
- Related backlog items or issues
```

### Severity Classification

- **Critical**: Financial transactions, data integrity, security issues
- **High**: Core functionality, API endpoints, critical user flows
- **Medium**: Non-critical features, edge cases
- **Low**: Minor issues, enhancements, cosmetic problems

---

## 7. Re-running Tests

### Local Verification

After fixing the code:

```bash
# Run the specific test
pytest tests/test_file.py::test_name -v

# Run all tests
pytest

# Run with coverage
pytest --cov=src/investment_platform --cov-report=html
```

### Triggering CI/CD Re-run

**Option 1: Push a new commit**
```bash
git add .
git commit -m "Fix: Resolve test failure in test_create_job_success"
git push
```

**Option 2: Re-run failed workflow (GitHub)**
1. Go to Actions tab
2. Click on the failed workflow
3. Click "Re-run jobs" button

**Option 3: Create an empty commit**
```bash
git commit --allow-empty -m "Trigger CI/CD re-run"
git push
```

### Verifying CI/CD Success

1. Wait for workflow to complete (usually 5-10 minutes)
2. Check for green checkmark ✅ on commit/PR
3. Review test results in Actions tab
4. Check coverage reports (if uploaded)

---

## 8. Best Practices

### Do's ✅

- **Always reproduce locally first** - Don't fix blindly
- **Run related tests** - Ensure no regressions
- **Check coverage** - Ensure coverage maintained
- **Create backlog items** - For non-trivial failures
- **Write clear commit messages** - Explain what was fixed
- **Test your fix** - Verify it works before pushing
- **Review CI/CD logs** - Understand the full context

### Don'ts ❌

- **Don't skip tests** - Unless absolutely necessary
- **Don't ignore failures** - Address them promptly
- **Don't fix without understanding** - Investigate first
- **Don't break other tests** - Run full suite
- **Don't decrease coverage** - Maintain or improve
- **Don't commit broken code** - Fix before pushing
- **Don't ignore CI/CD** - Check results regularly

### Commit Message Format

```
Fix: Resolve test failure in test_create_job_success

- Added error handling for ValidationError in create_job
- Return appropriate HTTP 400 status for validation errors
- Updated test to verify error handling

Fixes: backlog/2024-12-19-scheduler-create-job-validation-error.md
```

### Pull Request Checklist

When creating a PR to fix test failures:

- [ ] Test failure reproduced locally
- [ ] Root cause identified
- [ ] Fix implemented and tested
- [ ] All related tests pass
- [ ] Full test suite passes
- [ ] Coverage maintained or improved
- [ ] Backlog item created (if needed)
- [ ] Commit message is clear
- [ ] Code follows style guidelines
- [ ] PR description explains the fix

---

## Troubleshooting

### Can't Reproduce Locally

**Possible causes:**
1. Environment differences (database, dependencies)
2. Timing issues (race conditions)
3. Missing test data
4. Different Python/Node versions

**Solutions:**
1. Check CI/CD environment setup
2. Use Docker to match CI/CD environment
3. Add appropriate waits/mocks
4. Verify dependency versions

### Tests Pass Locally but Fail in CI/CD

**Possible causes:**
1. Environment variables missing
2. Database not set up correctly
3. Dependencies not installed
4. File permissions issues

**Solutions:**
1. Check `.github/workflows/test.yml` for environment setup
2. Verify database service configuration
3. Check dependency installation steps
4. Review file paths and permissions

### Intermittent Failures

**Possible causes:**
1. Race conditions
2. Timing issues
3. Resource contention
4. Network issues

**Solutions:**
1. Add appropriate waits/timeouts
2. Use mocks for external services
3. Increase test isolation
4. Add retry logic (if appropriate)

---

## Quick Reference

### Common Commands

```bash
# Reproduce failure
pytest tests/test_file.py::test_name -vv -s

# Run with debugger
pytest tests/test_file.py::test_name --pdb

# Run all tests
pytest

# Run with coverage
pytest --cov=src/investment_platform --cov-report=html

# Frontend tests
cd frontend && npm test

# Frontend with coverage
cd frontend && npm run test:coverage
```

### Workflow Summary

1. **Identify** → Check GitHub Actions for failures
2. **Reproduce** → Run failing test locally
3. **Debug** → Understand root cause
4. **Fix** → Implement minimal fix
5. **Verify** → Run tests locally
6. **Document** → Create backlog item (if needed)
7. **Commit** → Push fix with clear message
8. **Verify CI/CD** → Check workflow passes

---

## Related Documents

- [Testing Standards](./testing-standards.md) - Testing requirements and standards
- [Development Standards](./development-standards.md) - Code quality standards
- [QA Tester Role](../roles/qa-tester.md) - QA testing responsibilities
- [Python Developer Role](../roles/python-developer.md) - Backend development guidelines
- [Front End Engineer Role](../roles/front-end-engineer.md) - Frontend development guidelines

---

**Last Updated:** 2024-12-19  
**Maintained By:** Development Team

