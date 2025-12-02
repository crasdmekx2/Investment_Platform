# Handle Test Failure Workflow

## Purpose

This prompt guides you through the complete process of handling test failures in CI/CD, from identification to resolution. Use this prompt when tests fail in GitHub Actions or when you need to debug and fix failing tests.

## When to Use This Prompt

- ✅ Tests are failing in CI/CD (GitHub Actions)
- ✅ A specific test is failing locally
- ✅ You need to debug a test failure
- ✅ You need to create a backlog item for a test failure
- ✅ You want to verify a test fix before pushing

## Usage

Act as a QA Tester and help me handle a test failure. Follow the workflow below:

---

## Step 1: Identify the Test Failure

**If the failure is in CI/CD:**
1. Check the GitHub Actions workflow run
2. Identify which job failed (Backend Tests, Frontend Tests, etc.)
3. Find the specific test that failed
4. Note the error message and stack trace

**If the failure is local:**
1. Run the test and capture the output
2. Note the error message and stack trace

**Provide me with:**
- The test file and test name
- The error message
- The stack trace (if available)
- Any relevant context from CI/CD logs

---

## Step 2: Reproduce the Failure Locally

**For Backend Tests:**
```bash
# Pull latest code
git pull origin main

# Set up test environment
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=investment_platform_test
export DB_USER=postgres
export DB_PASSWORD=postgres

# Run the specific failing test
pytest tests/test_file.py::TestClass::test_name -vv -s
```

**For Frontend Tests:**
```bash
cd frontend
npm install
npm test -- TestComponent.test.tsx -t "test name"
```

**Help me:**
1. Set up the correct test environment
2. Run the failing test locally
3. Verify we can reproduce the failure
4. If we can't reproduce, identify environment differences

---

## Step 3: Debug and Investigate

**Analyze the failure:**
1. Read and understand the error message
2. Review the test code to understand what it's testing
3. Check the stack trace to identify where the failure occurred
4. Review the code being tested
5. Identify the root cause

**Use debugging tools:**
- Backend: `pytest --pdb` for interactive debugging
- Frontend: `npm run test:ui` for visual debugging
- Add print statements or logging
- Check coverage to see what code executed

**Help me:**
1. Understand what the test is trying to verify
2. Identify the root cause of the failure
3. Determine if it's a bug in code, test, or environment
4. Suggest debugging approaches

---

## Step 4: Fix the Code

**Before fixing:**
1. Understand the root cause
2. Plan the minimal fix needed
3. Consider edge cases and error handling

**While fixing:**
1. Make focused, minimal changes
2. Follow coding standards:
   - Backend: Black formatter, type hints, Flake8
   - Frontend: Prettier, TypeScript types, ESLint
3. Add appropriate error handling
4. Add logging if needed
5. Write clear comments for complex logic

**Help me:**
1. Implement the fix
2. Ensure code follows project standards
3. Add appropriate error handling
4. Verify the fix addresses the root cause

---

## Step 5: Verify the Fix

**Run tests in this order:**
1. Run the specific failing test
2. Run all tests in the same file
3. Run all tests in the same module
4. Run the full test suite
5. Check coverage hasn't decreased

**Commands:**
```bash
# Specific test
pytest tests/test_file.py::TestClass::test_name -v

# All tests in file
pytest tests/test_file.py -v

# All tests with coverage
pytest --cov=src/investment_platform --cov-report=html

# Frontend
cd frontend && npm test
cd frontend && npm run test:coverage
```

**Help me:**
1. Run the appropriate tests
2. Verify the fix works
3. Check for regressions
4. Ensure coverage is maintained

---

## Step 6: Create Backlog Item (If Needed)

**Create a backlog item if:**
- ✅ The failure indicates a real bug
- ✅ The failure requires investigation
- ✅ The failure is non-trivial to fix
- ❌ Skip if it's a simple typo (fix immediately)
- ❌ Skip if it's a test bug (fix test, no backlog)

**Backlog item format:**
- Location: `backlog/YYYY-MM-DD-test-failure-description.md`
- Include: Description, test reference, steps to reproduce, expected/actual behavior, error message, severity, recommended fix

**Help me:**
1. Determine if a backlog item is needed
2. Create the backlog item with proper format
3. Classify severity (Critical/High/Medium/Low)
4. Document the issue clearly

---

## Step 7: Commit and Push

**Commit message format:**
```
Fix: Resolve test failure in test_name

- Brief description of what was fixed
- Key changes made
- Any related issues

Fixes: backlog/YYYY-MM-DD-issue-description.md (if applicable)
```

**Before pushing:**
- [ ] All tests pass locally
- [ ] Code follows style guidelines
- [ ] Coverage maintained or improved
- [ ] Backlog item created (if needed)
- [ ] Commit message is clear

**Help me:**
1. Create an appropriate commit message
2. Verify all checks pass
3. Prepare for push

---

## Step 8: Verify CI/CD

**After pushing:**
1. Wait for GitHub Actions workflow to complete
2. Check for green checkmark ✅ on commit/PR
3. Review test results in Actions tab
4. Check coverage reports

**If CI/CD still fails:**
1. Check if the failure is the same or different
2. Compare local vs CI/CD environment
3. Check for environment-specific issues
4. Repeat the workflow if needed

**Help me:**
1. Monitor CI/CD results
2. Interpret test results
3. Troubleshoot if CI/CD still fails
4. Verify the fix is complete

---

## Troubleshooting

### Can't Reproduce Locally

**Possible causes:**
- Environment differences (database, dependencies)
- Timing issues (race conditions)
- Missing test data
- Different Python/Node versions

**Help me:**
1. Identify environment differences
2. Set up matching environment (Docker)
3. Add appropriate waits/mocks
4. Verify dependency versions

### Tests Pass Locally but Fail in CI/CD

**Possible causes:**
- Missing environment variables
- Database not set up correctly
- Dependencies not installed
- File permissions issues

**Help me:**
1. Check CI/CD configuration
2. Verify environment setup
3. Check dependency installation
4. Review file paths and permissions

### Intermittent Failures

**Possible causes:**
- Race conditions
- Timing issues
- Resource contention
- Network issues

**Help me:**
1. Add appropriate waits/timeouts
2. Use mocks for external services
3. Increase test isolation
4. Add retry logic (if appropriate)

---

## Quick Reference Commands

**Backend:**
```bash
# Reproduce failure
pytest tests/test_file.py::test_name -vv -s

# Debug with pdb
pytest tests/test_file.py::test_name --pdb

# Run with coverage
pytest --cov=src/investment_platform --cov-report=html

# Run all tests
pytest
```

**Frontend:**
```bash
# Run specific test
cd frontend && npm test -- TestComponent.test.tsx -t "test name"

# Run with UI
cd frontend && npm run test:ui

# Run with coverage
cd frontend && npm run test:coverage
```

---

## Workflow Summary

1. **Identify** → Check GitHub Actions or local test output
2. **Reproduce** → Run failing test locally
3. **Debug** → Understand root cause
4. **Fix** → Implement minimal fix
5. **Verify** → Run tests locally
6. **Document** → Create backlog item (if needed)
7. **Commit** → Push fix with clear message
8. **Verify CI/CD** → Check workflow passes

---

## Example Usage

**User:** "Tests are failing in CI/CD. The backend test `test_api_routers_scheduler.py::TestSchedulerRouter::test_create_job_success` is failing with a 500 error."

**AI Response:** 
1. Identifies the failure from CI/CD logs
2. Helps reproduce locally
3. Debugs the issue (missing error handling)
4. Implements the fix
5. Verifies the fix works
6. Creates backlog item if needed
7. Helps commit and push
8. Monitors CI/CD results

---

## Related Documents

- [Fix All Test Failures](../prompts/fix-all-test-failures.md) - Batch helper for multiple failures
- [Test Failure Workflow](../docs/TEST_FAILURE_WORKFLOW.md) - Complete workflow documentation
- [Testing Standards](../docs/testing-standards.md) - Testing requirements
- [QA Tester Role](../roles/qa-tester.md) - QA responsibilities
- [Development Standards](../docs/development-standards.md) - Code quality standards

---

## Notes

- Always reproduce failures locally before fixing
- Make minimal, focused fixes
- Run full test suite after fixing
- Create backlog items for non-trivial failures
- Follow coding standards and best practices
- Verify CI/CD passes before considering the issue resolved

