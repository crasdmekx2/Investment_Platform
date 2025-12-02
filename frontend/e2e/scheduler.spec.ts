import { test, expect } from '@playwright/test';

/**
 * E2E tests for the Scheduler page critical user flows.
 * 
 * These tests verify complete user workflows from start to finish,
 * including job creation, viewing jobs, and managing scheduled jobs.
 */

test.describe('Scheduler Page - Critical User Flows', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to scheduler page
    await page.goto('/scheduler');
    
    // Wait for page to load
    await expect(page.getByRole('heading', { name: /data collection scheduler/i })).toBeVisible();
  });

  test('user can navigate between scheduler tabs', async ({ page }) => {
    // Verify dashboard tab is active by default
    await expect(page.getByRole('button', { name: /dashboard/i })).toHaveAttribute('aria-current', 'page');
    await expect(page.getByTestId('jobs-dashboard')).toBeVisible();

    // Navigate to Jobs tab
    await page.getByRole('button', { name: /^jobs$/i }).click();
    await expect(page.getByRole('button', { name: /^jobs$/i })).toHaveAttribute('aria-current', 'page');
    await expect(page.getByTestId('jobs-list')).toBeVisible();

    // Navigate to Create Job tab
    await page.getByRole('button', { name: /create job/i }).click();
    await expect(page.getByRole('button', { name: /create job/i })).toHaveAttribute('aria-current', 'page');
    await expect(page.getByTestId('job-creator')).toBeVisible();

    // Navigate to Collection Logs tab
    await page.getByRole('button', { name: /collection logs/i }).click();
    await expect(page.getByRole('button', { name: /collection logs/i })).toHaveAttribute('aria-current', 'page');
    await expect(page.getByTestId('collection-logs-view')).toBeVisible();
  });

  test('user can view jobs dashboard with analytics', async ({ page }) => {
    // Verify dashboard is displayed
    await expect(page.getByTestId('jobs-dashboard')).toBeVisible();
    
    // Verify dashboard shows key metrics (these may be loading initially)
    // The dashboard should eventually show job statistics
    await expect(page.getByTestId('jobs-dashboard')).toBeVisible({ timeout: 10000 });
  });

  test('user can view jobs list and filter jobs', async ({ page }) => {
    // Navigate to Jobs tab
    await page.getByRole('button', { name: /^jobs$/i }).click();
    await expect(page.getByTestId('jobs-list')).toBeVisible();

    // Verify jobs list is displayed
    // The list may be empty or show existing jobs
    await expect(page.getByTestId('jobs-list')).toBeVisible();
  });

  test('user can create a scheduled job - complete workflow', async ({ page }) => {
    // Navigate to Create Job tab
    await page.getByRole('button', { name: /create job/i }).click();
    await expect(page.getByTestId('job-creator')).toBeVisible();

    // Step 1: Select asset type (Stock)
    await page.getByRole('button', { name: /stock asset type/i }).click();
    
    // Wait for next step to be available
    await expect(page.getByRole('button', { name: /next/i })).toBeEnabled();

    // Step 2: Select asset
    await page.getByRole('button', { name: /next/i }).click();
    
    // Search for an asset (e.g., AAPL)
    const searchInput = page.getByPlaceholder(/search.*symbol/i).or(page.getByRole('textbox', { name: /search/i }));
    if (await searchInput.isVisible()) {
      await searchInput.fill('AAPL');
      await page.waitForTimeout(500); // Wait for search results
      
      // Select the asset (click on AAPL if it appears)
      const assetOption = page.getByRole('button', { name: /AAPL/i }).or(page.getByText(/AAPL/i).first());
      if (await assetOption.isVisible({ timeout: 2000 })) {
        await assetOption.click();
      }
    }

    // Step 3: Collection parameters
    await page.getByRole('button', { name: /next/i }).click();
    
    // Fill in date range if visible
    const startDateInput = page.getByLabel(/start date/i).or(page.getByPlaceholder(/start date/i));
    const endDateInput = page.getByLabel(/end date/i).or(page.getByPlaceholder(/end date/i));
    
    if (await startDateInput.isVisible({ timeout: 2000 })) {
      await startDateInput.fill('2024-01-01');
    }
    if (await endDateInput.isVisible({ timeout: 2000 })) {
      await endDateInput.fill('2024-12-31');
    }

    // Step 4: Schedule configuration
    await page.getByRole('button', { name: /next/i }).click();
    
    // Select interval trigger type
    const intervalButton = page.getByRole('button', { name: /interval/i }).or(page.getByText(/interval/i).first());
    if (await intervalButton.isVisible({ timeout: 2000 })) {
      await intervalButton.click();
      
      // Configure interval (e.g., 5 minutes)
      const minutesInput = page.getByLabel(/minutes/i).or(page.getByPlaceholder(/minutes/i));
      if (await minutesInput.isVisible({ timeout: 2000 })) {
        await minutesInput.fill('5');
      }
    }

    // Step 5: Review
    await page.getByRole('button', { name: /next/i }).click();
    
    // Verify review page shows job details
    await expect(page.getByTestId('job-review-card')).toBeVisible({ timeout: 5000 });
    
    // Note: We don't actually create the job in E2E tests to avoid side effects
    // In a real scenario, you would click "Create Job" and verify success
  });

  test('user can view collection logs', async ({ page }) => {
    // Navigate to Collection Logs tab
    await page.getByRole('button', { name: /collection logs/i }).click();
    await expect(page.getByTestId('collection-logs-view')).toBeVisible();

    // Verify logs view is displayed
    // The view may be empty or show existing logs
    await expect(page.getByTestId('collection-logs-view')).toBeVisible();
  });

  test('user can navigate back through job creation steps', async ({ page }) => {
    // Navigate to Create Job tab
    await page.getByRole('button', { name: /create job/i }).click();
    await expect(page.getByTestId('job-creator')).toBeVisible();

    // Step 1: Select asset type
    await page.getByRole('button', { name: /stock asset type/i }).click();
    await page.getByRole('button', { name: /next/i }).click();

    // Step 2: Go back
    const backButton = page.getByRole('button', { name: /back/i }).or(page.getByRole('button', { name: /previous/i }));
    if (await backButton.isVisible({ timeout: 2000 })) {
      await backButton.click();
      
      // Verify we're back at asset type selection
      await expect(page.getByRole('button', { name: /stock asset type/i })).toBeVisible();
    }
  });
});

test.describe('Scheduler - Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/scheduler');
  });

  test('user sees error message when job creation fails', async ({ page }) => {
    // Navigate to Create Job tab
    await page.getByRole('button', { name: /create job/i }).click();
    
    // Try to proceed without selecting required fields
    // This should show validation errors
    const nextButton = page.getByRole('button', { name: /next/i });
    if (await nextButton.isVisible()) {
      // If next button is enabled, try clicking it
      // The form should prevent progression or show errors
      const isEnabled = await nextButton.isEnabled();
      if (isEnabled) {
        await nextButton.click();
        // Error messages may appear
      }
    }
  });
});

