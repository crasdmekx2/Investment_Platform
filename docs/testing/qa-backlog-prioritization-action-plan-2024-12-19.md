# QA Backlog Prioritization & Action Plan - December 19, 2024

## Overview

This document provides a prioritized action plan based on the backlog items review, following the QA testing workflow priorities:
1. ✅ Fix Failing Tests (Critical)
2. ✅ Address Coverage Gaps (High Priority)
3. 📋 Review and Prioritize Backlog Items

## Current Status

### ✅ Completed

1. **Fix Failing Tests (Critical)** ✅
   - ✅ Backend service tests: All 31 tests passing
   - ✅ Frontend tests: All 332+ tests passing
   - ✅ Test failures fixed and documented

2. **E2E Test Creation** ✅
   - ✅ Playwright framework set up
   - ✅ 9 E2E tests created
   - ⏳ E2E tests ready for execution

### ⏳ In Progress

3. **Address Coverage Gaps (High Priority)** ⏳
   - ⏳ Backend coverage: 30% (target: >80%)
   - ✅ Frontend coverage: ~80-85% (target achieved)
   - ⏳ API router tests needed
   - ⏳ Service layer coverage improvement needed

## Prioritized Action Plan

### 🔴 CRITICAL Priority Actions

**Status:** ✅ **COMPLETE**

All critical test failures have been addressed:
- Backend service tests: All passing
- Frontend tests: All passing
- No critical blockers

---

### 🟠 HIGH Priority Actions

#### Action 1: Increase Backend Test Coverage to >80%

**Current Status:**
- Overall coverage: 30%
- Target: >80%
- Gap: 50%

**Priority Modules:**
1. **API Routers** (20-29% → >80%)
   - `scheduler.py`: 23% → >80%
   - `assets.py`: 20% → >80%
   - `collectors.py`: 29% → >80%
   - `ingestion.py`: 29% → >80%

2. **API Services** (11-16% → >80%)
   - `scheduler_service.py`: 11% → >80% (Note: Tests passing but coverage low)
   - `collector_service.py`: 16% → >80% (Note: Tests passing but coverage low)

3. **WebSocket** (29% → >80%)
   - `websocket.py`: 29% → >80%

4. **Persistent Scheduler** (8% → >80%)
   - `persistent_scheduler.py`: 8% → >80%

**Tasks:**
1. Create API router integration tests for scheduler router
2. Create integration tests for remaining routers
3. Add error handling and edge case tests
4. Add WebSocket endpoint tests
5. Add persistent scheduler tests

**Assigned To:** Backend Developer  
**Target Completion:** Next Sprint  
**Estimated Effort:** 2-3 days

---

#### Action 2: Fix Infrastructure-Dependent Test Failures

**Current Status:**
- Database connection tests: 4 failing
- Docker container tests: 3 failing
- Collector test: 1 error

**Tasks:**
1. Add proper skip conditions for database-dependent tests
2. Add proper skip conditions for Docker-dependent tests
3. Investigate and fix collector test error
4. Improve test isolation

**Assigned To:** DevOps/Backend Developer  
**Target Completion:** Next Sprint  
**Estimated Effort:** 1-2 days

---

### 🟡 MEDIUM Priority Actions

#### Action 3: Fix Test Quality Issues

**Current Status:**
- Tests returning boolean values instead of assertions
- Pytest warnings: `PytestReturnNotNoneWarning`
- 7 affected tests

**Tasks:**
1. Refactor `test_ingestion_db_connection.py::test_connection`
2. Refactor `test_scheduler_improvements.py` (6 tests)
3. Verify warnings resolved
4. Review all tests for similar patterns

**Assigned To:** Backend Developer  
**Target Completion:** Next Sprint  
**Estimated Effort:** 0.5 days

---

## Implementation Roadmap

### Week 1 (Current Week)

**Day 1-2:**
- ✅ Complete: Fix backend service test failures
- ✅ Complete: Create E2E tests
- ⏳ In Progress: Review and prioritize backlog items

**Day 3-4:**
- ⏳ Start: Create API router integration tests (scheduler router)
- ⏳ Start: Fix infrastructure-dependent test failures

**Day 5:**
- ⏳ Continue: API router integration tests
- ⏳ Review: Test quality issues

### Week 2 (Next Sprint)

**Day 1-3:**
- Complete API router integration tests
- Increase service layer coverage
- Add WebSocket endpoint tests

**Day 4-5:**
- Add persistent scheduler tests
- Fix test quality issues
- Generate updated coverage report

### Week 3 (Follow-up)

**Day 1-2:**
- Review coverage improvements
- Verify all tests passing
- Update documentation

**Day 3-5:**
- Set up coverage gates in CI/CD
- Configure test infrastructure
- Final validation

## Success Criteria

### High Priority Actions

✅ **Coverage Improvement:**
- Backend coverage: 30% → >80%
- API routers: >80% coverage
- API services: >80% coverage
- WebSocket: >80% coverage
- Persistent scheduler: >80% coverage

✅ **Infrastructure Tests:**
- All database-dependent tests skip gracefully
- All Docker-dependent tests skip gracefully
- Collector test error resolved
- Test suite runs successfully in all environments

### Medium Priority Actions

✅ **Test Quality:**
- All tests use proper assertions
- No pytest warnings
- Test reliability improved

## Risk Assessment

### High Risk
- **Coverage gaps:** May miss bugs and security vulnerabilities
- **Mitigation:** Prioritize critical paths first, set coverage gates

### Medium Risk
- **Infrastructure tests:** May block CI/CD if not handled properly
- **Mitigation:** Add proper skip conditions, set up test infrastructure

### Low Risk
- **Test quality issues:** May cause false positives
- **Mitigation:** Refactor tests, add test reviews

## Tracking & Reporting

### Progress Tracking
- Update backlog items with progress
- Document test creation and fixes
- Generate weekly progress reports

### Reporting
- Weekly status updates
- Coverage improvement metrics
- Test execution results

## Related Documents

- `backlog/2024-12-19-backlog-prioritization-review.md` - Detailed backlog review
- `backlog/2024-12-19-backend-coverage-gaps.md` - Coverage gaps details
- `backlog/2024-12-19-backend-test-failures.md` - Infrastructure failures
- `backlog/2024-12-19-backend-test-quality-issues.md` - Test quality issues
- `docs/testing/qa-test-coverage-analysis.md` - Coverage analysis

