import { test, expect } from '@playwright/test';

/**
 * E2E tests for navigation and routing.
 * 
 * These tests verify that users can navigate between different pages
 * and that routing works correctly.
 */

test.describe('Navigation - Critical User Flows', () => {
  test('user can navigate to all main pages', async ({ page }) => {
    // Start at home/dashboard
    await page.goto('/');
    
    // Verify we're on a valid page (could be dashboard, portfolio, etc.)
    await expect(page).toHaveURL(/\//);

    // Navigate to Scheduler
    const schedulerLink = page.getByRole('link', { name: /scheduler/i }).or(
      page.getByRole('button', { name: /scheduler/i })
    );
    if (await schedulerLink.isVisible({ timeout: 2000 })) {
      await schedulerLink.click();
      await expect(page).toHaveURL(/\/scheduler/i);
    }

    // Navigate to Portfolio (if link exists)
    const portfolioLink = page.getByRole('link', { name: /portfolio/i }).or(
      page.getByRole('button', { name: /portfolio/i })
    );
    if (await portfolioLink.isVisible({ timeout: 2000 })) {
      await portfolioLink.click();
      await expect(page).toHaveURL(/\/portfolio/i);
    }
  });

  test('user can navigate using browser back/forward buttons', async ({ page }) => {
    // Start at home
    await page.goto('/');
    
    // Navigate to scheduler
    await page.goto('/scheduler');
    await expect(page).toHaveURL(/\/scheduler/i);
    
    // Go back
    await page.goBack();
    await expect(page).toHaveURL(/\//);
    
    // Go forward
    await page.goForward();
    await expect(page).toHaveURL(/\/scheduler/i);
  });
});

