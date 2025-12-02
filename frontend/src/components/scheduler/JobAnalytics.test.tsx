import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { JobAnalytics } from './JobAnalytics';
import { schedulerApi } from '@/lib/api/scheduler';

// Mock the API
vi.mock('@/lib/api/scheduler', () => ({
  schedulerApi: {
    getAnalytics: vi.fn(),
  },
}));

describe('JobAnalytics', () => {
  const mockAnalyticsData = {
    total_executions: 100,
    success_rate: 95.5,
    success_count: 95,
    failure_count: 5,
    avg_execution_time_ms: 1500,
    failures_by_category: [
      { error_category: 'Network Error', failure_count: 3 },
      { error_category: 'Validation Error', failure_count: 2 },
    ],
    jobs_by_asset_type: [
      { asset_type: 'stock', job_count: 50 },
      { asset_type: 'crypto', job_count: 30 },
    ],
    execution_trends: [
      {
        date: '2024-12-19',
        execution_count: 10,
        success_count: 9,
        avg_execution_time_ms: 1400,
      },
    ],
    top_failing_jobs: [
      {
        job_id: 'job_1',
        symbol: 'AAPL',
        asset_type: 'stock',
        failure_count: 2,
        total_executions: 10,
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(schedulerApi.getAnalytics).mockResolvedValue({
      data: mockAnalyticsData,
    } as any);
  });

  it('renders analytics with loading state', () => {
    render(<JobAnalytics />);

    // Should show loading spinner initially
    expect(screen.queryByText('Collection Parameters')).not.toBeInTheDocument();
  });

  it('loads and displays analytics data', async () => {
    render(<JobAnalytics />);

    await waitFor(() => {
      expect(screen.getByText('Analytics Filters')).toBeInTheDocument();
    });

    expect(screen.getByText(/100/i)).toBeInTheDocument(); // Total executions
    expect(screen.getByText(/95.5/i)).toBeInTheDocument(); // Success rate
  });

  it('displays success rate', async () => {
    render(<JobAnalytics />);

    await waitFor(() => {
      expect(screen.getByText(/95.5/i)).toBeInTheDocument();
    });
  });

  it('displays execution statistics', async () => {
    render(<JobAnalytics />);

    await waitFor(() => {
      expect(screen.getByText(/100/i)).toBeInTheDocument(); // Total executions
      expect(screen.getByText(/95/i)).toBeInTheDocument(); // Success count
      expect(screen.getByText(/5/i)).toBeInTheDocument(); // Failure count
    });
  });

  it('allows filtering by date range', async () => {
    const user = userEvent.setup();
    render(<JobAnalytics />);

    await waitFor(() => {
      expect(screen.getByLabelText(/start date/i)).toBeInTheDocument();
    });

    const startDateInput = screen.getByLabelText(/start date/i);
    await user.clear(startDateInput);
    await user.type(startDateInput, '2024-12-01');

    await waitFor(() => {
      expect(schedulerApi.getAnalytics).toHaveBeenCalledWith(
        expect.objectContaining({
          start_date: '2024-12-01',
        })
      );
    });
  });

  it('allows filtering by asset type', async () => {
    const user = userEvent.setup();
    render(<JobAnalytics />);

    await waitFor(() => {
      expect(screen.getByLabelText(/asset type/i)).toBeInTheDocument();
    });

    const assetTypeSelect = screen.getByLabelText(/asset type/i);
    await user.selectOptions(assetTypeSelect, 'stock');

    await waitFor(() => {
      expect(schedulerApi.getAnalytics).toHaveBeenCalledWith(
        expect.objectContaining({
          asset_type: 'stock',
        })
      );
    });
  });

  it('displays error message when API fails', async () => {
    vi.mocked(schedulerApi.getAnalytics).mockRejectedValue(new Error('API Error'));

    render(<JobAnalytics />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load analytics/i)).toBeInTheDocument();
    });
  });

  it('displays failures by category', async () => {
    render(<JobAnalytics />);

    await waitFor(() => {
      expect(screen.getByText('Network Error')).toBeInTheDocument();
      expect(screen.getByText('Validation Error')).toBeInTheDocument();
    });
  });

  it('displays jobs by asset type', async () => {
    render(<JobAnalytics />);

    await waitFor(() => {
      expect(screen.getByText(/stock/i)).toBeInTheDocument();
      expect(screen.getByText(/crypto/i)).toBeInTheDocument();
    });
  });

  it('displays top failing jobs', async () => {
    render(<JobAnalytics />);

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });
  });

  it('has accessible filter inputs', async () => {
    render(<JobAnalytics />);

    await waitFor(() => {
      const startDateInput = screen.getByLabelText(/start date/i);
      expect(startDateInput).toHaveClass('min-h-[44px]');
    });
  });
});

