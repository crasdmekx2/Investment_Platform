# Fix All Test Failures - Batch Helper

## Purpose

This prompt helps you systematically identify, prioritize, and fix all test failures from GitHub issues. It provides a structured approach to handle multiple test failures efficiently, starting with the highest severity issues.

## When to Use This Prompt

- ✅ Multiple test failures exist in GitHub Issues
- ✅ You want to systematically fix all test failures
- ✅ You need to prioritize which failures to fix first
- ✅ You want to track progress on fixing test failures
- ✅ After a CI/CD run that created multiple issues

## Usage

Act as a QA Tester and help me fix all test failures from GitHub Issues. Follow the workflow below:

---

## Step 1: Identify All Test Failure Issues

**Get all open test failure issues from GitHub:**

1. List all open issues with the `test-failure` label
2. Filter to show only test failure issues
3. Group by severity (Critical → High → Medium → Low)
4. Show summary statistics

**Help me:**
1. Query GitHub API for open issues with `test-failure` label
2. Parse issue titles and bodies to extract test information
3. Classify severity from issue labels or content
4. Create a prioritized list
5. Display summary: Total issues, by severity, by test type (backend/frontend)

**Expected Output:**
```
## Test Failure Issues Summary

**Total Open Issues:** 5
- Critical: 1
- High: 2
- Medium: 2
- Low: 0

**By Type:**
- Backend: 3
- Frontend: 2

**Prioritized List:**
1. [Critical] Test Failure: test_security_validation::test_sql_injection_prevention (#123)
2. [High] Test Failure: test_api_routers_scheduler::test_create_job_success (#124)
3. [High] Test Failure: test_api_services_collector::test_search_assets (#125)
...
```

---

## Step 2: Prioritize Issues

**Create a prioritized fixing order:**

1. **Critical issues first** - Security, financial transactions, data integrity
2. **High issues second** - Core functionality, API endpoints
3. **Medium issues third** - Non-critical features
4. **Low issues last** - Minor issues, enhancements

**Within each severity level:**
- Backend issues before frontend (if backend blocks frontend)
- Integration tests before unit tests (if integration tests are blocking)
- Most recent failures first (to catch regressions early)

**Help me:**
1. Sort issues by priority
2. Create a numbered list
3. Explain the prioritization logic
4. Show estimated effort for each (if possible)

---

## Step 3: Fix Issues One by One

**For each issue in priority order:**

### 3.1 Select Next Issue

**Help me:**
1. Show the next issue in the priority list
2. Display issue details (title, number, severity, test info)
3. Show related information (CI/CD run, commit, etc.)

### 3.2 Analyze the Issue

**Extract information from the GitHub issue:**
- Test file and test name
- Error message and stack trace
- Expected vs actual behavior
- Steps to reproduce
- Related context

**Help me:**
1. Parse the GitHub issue body
2. Extract test details (file, class, test name)
3. Extract error information
4. Identify what needs to be fixed
5. Determine if it's a code bug, test bug, or environment issue

### 3.3 Fix the Issue

**Follow the workflow from `handle-test-failure.md`:**

1. **Reproduce locally**
   ```bash
   # Get the test command from the issue
   pytest tests/test_file.py::TestClass::test_name -vv -s
   ```

2. **Debug and investigate**
   - Understand the root cause
   - Review test code and implementation
   - Identify the fix needed

3. **Implement the fix**
   - Make minimal, focused changes
   - Follow coding standards
   - Add error handling if needed

4. **Verify the fix**
   ```bash
   # Run the specific test
   pytest tests/test_file.py::TestClass::test_name -v
   
   # Run related tests
   pytest tests/test_file.py -v
   
   # Run full suite (optional, can do at end)
   pytest
   ```

**Help me:**
1. Guide through reproducing the failure
2. Help debug and identify root cause
3. Implement the fix
4. Verify the fix works
5. Check for regressions

### 3.4 Commit and Push

**Create a focused commit for this fix:**

```bash
git add .
git commit -m "Fix: Resolve test failure in test_name

- Brief description of fix
- Issue: #123

Fixes: #123"
git push
```

**Help me:**
1. Create appropriate commit message
2. Reference the GitHub issue number
3. Verify all checks pass locally
4. Prepare for push

### 3.5 Verify CI/CD and Close Issue

**After pushing:**
1. Wait for CI/CD to complete
2. Verify tests pass
3. Close the GitHub issue (or add comment)

**Help me:**
1. Monitor CI/CD results
2. Verify the fix worked
3. Update the GitHub issue with results
4. Close the issue if tests pass

---

## Step 4: Track Progress

**Maintain a progress tracker:**

**Help me:**
1. Update the list of remaining issues
2. Mark completed issues
3. Show progress percentage
4. Display summary after each fix

**Progress Format:**
```
## Progress Update

✅ Fixed: [Critical] test_security_validation::test_sql_injection_prevention (#123)
⏳ In Progress: [High] test_api_routers_scheduler::test_create_job_success (#124)
📋 Pending: [High] test_api_services_collector::test_search_assets (#125)
📋 Pending: [Medium] test_component_rendering::test_button_click (#126)
📋 Pending: [Medium] test_hook_behavior::test_use_api (#127)

Progress: 1/5 (20%) complete
```

---

## Step 5: Batch Verification

**After fixing all issues (or a batch):**

1. Run full test suite locally
2. Verify all fixes work together
3. Check coverage hasn't decreased
4. Ensure no new failures introduced

**Help me:**
1. Run complete test suite
2. Generate coverage report
3. Verify all tests pass
4. Check for any regressions
5. Create summary of all fixes

---

## Workflow Summary

1. **Identify** → List all test failure issues from GitHub
2. **Prioritize** → Sort by severity and importance
3. **Fix** → Work through issues one by one using handle-test-failure workflow
4. **Track** → Maintain progress and update status
5. **Verify** → Run full test suite to ensure all fixes work

---

## Example Usage

### Initial Request

**User:** "I have multiple test failures from the last CI/CD run. Help me fix them all."

**AI Response:**
1. Queries GitHub for all open test-failure issues
2. Lists them prioritized by severity
3. Starts with the first Critical issue
4. Guides through fixing it
5. Moves to next issue

### During Fixing

**User:** "Let's move to the next issue."

**AI Response:**
1. Shows next issue in priority list
2. Extracts test details from issue
3. Helps reproduce and fix
4. Updates progress tracker

### After All Fixes

**User:** "Verify all fixes work together."

**AI Response:**
1. Runs full test suite
2. Checks coverage
3. Verifies no regressions
4. Creates summary report

---

## Integration with handle-test-failure.md

This prompt uses the detailed workflow from `handle-test-failure.md` for each individual fix. The difference is:

- **handle-test-failure.md**: Fixes ONE specific test failure
- **fix-all-test-failures.md**: Manages MULTIPLE test failures systematically

When fixing each issue, follow the 8-step process from `handle-test-failure.md`:
1. Identify the test failure
2. Reproduce locally
3. Debug and investigate
4. Fix the code
5. Verify the fix
6. Create backlog item (if needed)
7. Commit and push
8. Verify CI/CD

---

## Advanced Features

### Skip Non-Critical Issues

**Option:** "Only fix Critical and High severity issues for now."

**Help me:**
1. Filter to only Critical/High issues
2. Create separate list for Medium/Low
3. Focus on high-priority fixes first

### Fix by Type

**Option:** "Fix all backend issues first, then frontend."

**Help me:**
1. Group issues by type (backend/frontend)
2. Fix all of one type before moving to next
3. Useful if one type blocks the other

### Batch Commits

**Option:** "Fix multiple related issues in one commit."

**Help me:**
1. Identify related issues (same file, same root cause)
2. Fix them together
3. Create one commit for related fixes
4. Reference all issue numbers

---

## Progress Tracking Template

```markdown
# Test Failure Fix Progress

**Date:** YYYY-MM-DD
**Total Issues:** X
**Fixed:** Y
**Remaining:** Z

## Issues Fixed

1. ✅ [Critical] Issue #123 - test_security_validation::test_sql_injection_prevention
   - Fixed: Added input validation
   - Commit: abc123
   - CI/CD: ✅ Passed

2. ✅ [High] Issue #124 - test_api_routers_scheduler::test_create_job_success
   - Fixed: Added error handling
   - Commit: def456
   - CI/CD: ✅ Passed

## Issues Remaining

3. ⏳ [High] Issue #125 - test_api_services_collector::test_search_assets
   - Status: In progress
   - Next: Reproduce locally

4. 📋 [Medium] Issue #126 - test_component_rendering::test_button_click
   - Status: Pending
```

---

## Troubleshooting

### Issue Already Fixed

**If an issue is already fixed but still open:**
1. Verify the fix in CI/CD
2. Add a comment to the issue
3. Close the issue
4. Move to next issue

### Issue is a Test Bug

**If the issue is actually a test bug (not code bug):**
1. Fix the test instead
2. Update issue with explanation
3. Close issue
4. Move to next issue

### Can't Reproduce Issue

**If you can't reproduce the failure:**
1. Check if it's environment-specific
2. Check if it's already fixed
3. Add comment to issue asking for more info
4. Move to next issue (can revisit later)

### Related Issues

**If multiple issues have the same root cause:**
1. Fix the root cause
2. Verify all related issues are resolved
3. Close all related issues
4. Reference all issue numbers in commit

---

## Related Documents

- [Handle Test Failure](../prompts/handle-test-failure.md) - Detailed workflow for fixing one issue
- [Test Failure Workflow](../docs/TEST_FAILURE_WORKFLOW.md) - Complete workflow documentation
- [Testing Standards](../docs/testing-standards.md) - Testing requirements
- [QA Tester Role](../roles/qa-tester.md) - QA responsibilities

---

## Notes

- Fix issues one at a time for clarity and safety
- Verify each fix before moving to the next
- Update progress tracker regularly
- Run full test suite periodically to catch regressions
- Don't skip verification steps
- Close GitHub issues when fixes are verified
- Create focused commits for each fix (or related fixes)

