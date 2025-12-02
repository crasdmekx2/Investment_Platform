import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { JobsDashboard } from './JobsDashboard';
import { useSchedulerStore } from '@/store/slices/schedulerSlice';
import { useCollectionStore } from '@/store/slices/collectionSlice';

// Mock the stores
vi.mock('@/store/slices/schedulerSlice', () => ({
  useSchedulerStore: vi.fn(),
}));

vi.mock('@/store/slices/collectionSlice', () => ({
  useCollectionStore: vi.fn(),
}));

// Mock JobAnalytics component
vi.mock('@/components/scheduler/JobAnalytics', () => ({
  JobAnalytics: () => <div data-testid="job-analytics">Job Analytics</div>,
}));

describe('JobsDashboard', () => {
  const mockFetchJobs = vi.fn();
  const mockFetchCollectionLogs = vi.fn();
  const mockJobs = [
    {
      job_id: 'job_1',
      symbol: 'AAPL',
      asset_type: 'stock',
      status: 'active',
    },
    {
      job_id: 'job_2',
      symbol: 'MSFT',
      asset_type: 'stock',
      status: 'paused',
    },
    {
      job_id: 'job_3',
      symbol: 'GOOGL',
      asset_type: 'stock',
      status: 'active',
    },
  ];

  const mockLogs = [
    {
      log_id: 1,
      asset_id: 1,
      collector_type: 'stock',
      status: 'success',
      records_collected: 100,
      created_at: '2024-12-19T10:00:00Z',
    },
    {
      log_id: 2,
      asset_id: 2,
      collector_type: 'crypto',
      status: 'success',
      records_collected: 50,
      created_at: '2024-12-19T11:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useSchedulerStore).mockReturnValue({
      jobs: mockJobs,
      isLoading: false,
      fetchJobs: mockFetchJobs,
    } as any);
    vi.mocked(useCollectionStore).mockReturnValue({
      activeJobs: { job_1: {} },
      logs: mockLogs,
      fetchCollectionLogs: mockFetchCollectionLogs,
    } as any);
  });

  it('renders dashboard with metrics', () => {
    render(<JobsDashboard />);
    
    expect(screen.getByText('Active Jobs')).toBeInTheDocument();
    expect(screen.getByText('Running Now')).toBeInTheDocument();
    expect(screen.getByText('Paused Jobs')).toBeInTheDocument();
    expect(screen.getByText('Success Rate')).toBeInTheDocument();
  });

  it('fetches jobs and logs on mount', () => {
    render(<JobsDashboard />);
    
    expect(mockFetchJobs).toHaveBeenCalledTimes(1);
    expect(mockFetchCollectionLogs).toHaveBeenCalledWith({ limit: 100 });
  });

  it('displays correct active jobs count', () => {
    render(<JobsDashboard />);
    
    // Should show 2 active jobs (job_1 and job_3)
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('displays correct paused jobs count', () => {
    render(<JobsDashboard />);
    
    // Should show 1 paused job (job_2)
    const pausedCard = screen.getByText('Paused Jobs').closest('.space-y-2');
    expect(pausedCard).toHaveTextContent('1');
  });

  it('displays correct running jobs count', () => {
    render(<JobsDashboard />);
    
    // Should show 1 running job (from activeJobs)
    const runningCard = screen.getByText('Running Now').closest('.space-y-2');
    expect(runningCard).toHaveTextContent('1');
  });

  it('calculates and displays success rate', () => {
    render(<JobsDashboard />);
    
    // Both logs are success, so 100%
    const successCard = screen.getByText('Success Rate').closest('.space-y-2');
    expect(successCard).toHaveTextContent('100.0%');
  });

  it('shows loading spinner when loading', () => {
    vi.mocked(useSchedulerStore).mockReturnValue({
      jobs: [],
      isLoading: true,
      fetchJobs: mockFetchJobs,
    } as any);

    render(<JobsDashboard />);
    
    // LoadingSpinner should be rendered
    expect(screen.queryByText('Active Jobs')).not.toBeInTheDocument();
  });

  it('toggles analytics visibility', async () => {
    const user = userEvent.setup();
    render(<JobsDashboard />);
    
    const toggleButton = screen.getByRole('button', { name: /show analytics/i });
    expect(screen.queryByTestId('job-analytics')).not.toBeInTheDocument();
    
    await user.click(toggleButton);
    
    await waitFor(() => {
      expect(screen.getByTestId('job-analytics')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /hide analytics/i })).toBeInTheDocument();
    });
  });

  it('displays recent activity logs', () => {
    render(<JobsDashboard />);
    
    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
    expect(screen.getByText(/Asset ID: 1 - stock/i)).toBeInTheDocument();
    expect(screen.getByText(/Asset ID: 2 - crypto/i)).toBeInTheDocument();
  });

  it('displays empty message when no recent activity', () => {
    vi.mocked(useCollectionStore).mockReturnValue({
      activeJobs: {},
      logs: [],
      fetchCollectionLogs: mockFetchCollectionLogs,
    } as any);

    render(<JobsDashboard />);
    
    expect(screen.getByText('No recent activity')).toBeInTheDocument();
  });

  it('displays log status badges', () => {
    render(<JobsDashboard />);
    
    // Use getAllByText since there are multiple "success" status badges
    const successBadges = screen.getAllByText('success');
    expect(successBadges.length).toBeGreaterThan(0);
    expect(successBadges[0]).toBeInTheDocument();
  });

  it('displays log record counts', () => {
    render(<JobsDashboard />);
    
    expect(screen.getByText('100 records')).toBeInTheDocument();
    expect(screen.getByText('50 records')).toBeInTheDocument();
  });

  it('has accessible analytics toggle button', () => {
    render(<JobsDashboard />);
    
    const toggleButton = screen.getByRole('button', { name: /show analytics/i });
    expect(toggleButton).toBeInTheDocument();
    expect(toggleButton).toHaveClass('min-h-[44px]'); // Accessibility: minimum touch target
  });
});

