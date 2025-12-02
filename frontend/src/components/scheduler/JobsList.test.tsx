import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { JobsList } from './JobsList';
import { useSchedulerStore } from '@/store/slices/schedulerSlice';

// Mock the store
vi.mock('@/store/slices/schedulerSlice', () => ({
  useSchedulerStore: vi.fn(),
}));

// Mock ScheduleVisualization component
vi.mock('@/components/scheduler/ScheduleVisualization', () => ({
  ScheduleVisualization: ({ jobs }: { jobs: any[] }) => (
    <div data-testid="schedule-visualization">Visualization for {jobs.length} jobs</div>
  ),
}));

// Mock window.confirm
const mockConfirm = vi.fn();
window.confirm = mockConfirm;

describe('JobsList', () => {
  const mockFetchJobs = vi.fn();
  const mockSetFilters = vi.fn();
  const mockPauseJob = vi.fn();
  const mockResumeJob = vi.fn();
  const mockDeleteJob = vi.fn();
  
  const mockJobs = [
    {
      job_id: 'job_1',
      symbol: 'AAPL',
      asset_type: 'stock',
      status: 'active',
      trigger_type: 'interval',
      trigger_config: { minutes: 5 },
    },
    {
      job_id: 'job_2',
      symbol: 'MSFT',
      asset_type: 'stock',
      status: 'paused',
      trigger_type: 'cron',
      trigger_config: { hour: 9, minute: 0 },
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    mockConfirm.mockReturnValue(true);
    vi.mocked(useSchedulerStore).mockReturnValue({
      jobs: mockJobs,
      isLoading: false,
      error: null,
      setFilters: mockSetFilters,
      fetchJobs: mockFetchJobs,
      pauseJob: mockPauseJob,
      resumeJob: mockResumeJob,
      deleteJob: mockDeleteJob,
    } as any);
  });

  it('renders jobs list with title', () => {
    render(<JobsList />);
    
    // Use getAllByText since there are multiple "Scheduled Jobs" headings
    const titles = screen.getAllByText('Scheduled Jobs');
    expect(titles.length).toBeGreaterThan(0);
    expect(titles[0]).toBeInTheDocument();
  });

  it('displays loading spinner when loading', () => {
    vi.mocked(useSchedulerStore).mockReturnValue({
      jobs: [],
      isLoading: true,
      error: null,
      setFilters: mockSetFilters,
      fetchJobs: mockFetchJobs,
      pauseJob: mockPauseJob,
      resumeJob: mockResumeJob,
      deleteJob: mockDeleteJob,
    } as any);

    render(<JobsList />);
    
    expect(screen.queryByText('Scheduled Jobs')).not.toBeInTheDocument();
  });

  it('displays error message when error occurs', () => {
    vi.mocked(useSchedulerStore).mockReturnValue({
      jobs: [],
      isLoading: false,
      error: 'Failed to load jobs',
      setFilters: mockSetFilters,
      fetchJobs: mockFetchJobs,
      pauseJob: mockPauseJob,
      resumeJob: mockResumeJob,
      deleteJob: mockDeleteJob,
    } as any);

    render(<JobsList />);
    
    expect(screen.getByText('Failed to load jobs')).toBeInTheDocument();
  });

  it('displays jobs in table', () => {
    render(<JobsList />);
    
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('MSFT')).toBeInTheDocument();
  });

  it('filters jobs by status', async () => {
    const user = userEvent.setup();
    render(<JobsList />);
    
    const statusFilter = screen.getByLabelText(/filter jobs by status/i);
    await user.selectOptions(statusFilter, 'active');
    
    // Click apply filters button (if exists) or wait for filter to apply
    const applyButton = screen.queryByRole('button', { name: /apply/i });
    if (applyButton) {
      await user.click(applyButton);
    }
    
    // Verify filter was set
    expect(mockSetFilters).toHaveBeenCalled();
  });

  it('filters jobs by asset type', async () => {
    const user = userEvent.setup();
    render(<JobsList />);
    
    const assetTypeFilter = screen.getByLabelText(/filter jobs by asset type/i);
    await user.selectOptions(assetTypeFilter, 'stock');
    
    // Click apply filters button to trigger filter
    const applyButton = screen.getByRole('button', { name: /apply filters/i });
    await user.click(applyButton);
    
    // Verify filter was set
    expect(mockSetFilters).toHaveBeenCalled();
  });

  it('toggles schedule visualization', async () => {
    const user = userEvent.setup();
    render(<JobsList />);
    
    const toggleButton = screen.getByRole('button', { name: /show schedule visualization/i });
    expect(screen.queryByTestId('schedule-visualization')).not.toBeInTheDocument();
    
    await user.click(toggleButton);
    
    await waitFor(() => {
      expect(screen.getByTestId('schedule-visualization')).toBeInTheDocument();
    });
  });

  it('pauses job with confirmation', async () => {
    const user = userEvent.setup();
    mockConfirm.mockReturnValue(true);
    render(<JobsList />);
    
    const pauseButtons = screen.getAllByRole('button', { name: /pause/i });
    if (pauseButtons.length > 0) {
      await user.click(pauseButtons[0]);
      
      expect(mockConfirm).toHaveBeenCalled();
      expect(mockPauseJob).toHaveBeenCalled();
      expect(mockFetchJobs).toHaveBeenCalled();
    }
  });

  it('does not pause job if confirmation cancelled', async () => {
    const user = userEvent.setup();
    mockConfirm.mockReturnValue(false);
    render(<JobsList />);
    
    const pauseButtons = screen.getAllByRole('button', { name: /pause/i });
    if (pauseButtons.length > 0) {
      await user.click(pauseButtons[0]);
      
      expect(mockConfirm).toHaveBeenCalled();
      expect(mockPauseJob).not.toHaveBeenCalled();
    }
  });

  it('resumes job', async () => {
    const user = userEvent.setup();
    render(<JobsList />);
    
    const resumeButtons = screen.getAllByRole('button', { name: /resume/i });
    if (resumeButtons.length > 0) {
      await user.click(resumeButtons[0]);
      
      expect(mockResumeJob).toHaveBeenCalled();
      expect(mockFetchJobs).toHaveBeenCalled();
    }
  });

  it('deletes job with confirmation', async () => {
    const user = userEvent.setup();
    mockConfirm.mockReturnValue(true);
    render(<JobsList />);
    
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    if (deleteButtons.length > 0) {
      await user.click(deleteButtons[0]);
      
      expect(mockConfirm).toHaveBeenCalled();
      expect(mockDeleteJob).toHaveBeenCalled();
      expect(mockFetchJobs).toHaveBeenCalled();
    }
  });

  it('does not delete job if confirmation cancelled', async () => {
    const user = userEvent.setup();
    mockConfirm.mockReturnValue(false);
    render(<JobsList />);
    
    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    if (deleteButtons.length > 0) {
      await user.click(deleteButtons[0]);
      
      expect(mockConfirm).toHaveBeenCalled();
      expect(mockDeleteJob).not.toHaveBeenCalled();
    }
  });

  it('displays empty message when no jobs', () => {
    vi.mocked(useSchedulerStore).mockReturnValue({
      jobs: [],
      isLoading: false,
      error: null,
      setFilters: mockSetFilters,
      fetchJobs: mockFetchJobs,
      pauseJob: mockPauseJob,
      resumeJob: mockResumeJob,
      deleteJob: mockDeleteJob,
    } as any);

    render(<JobsList />);
    
    expect(screen.getByText(/no jobs found/i)).toBeInTheDocument();
  });

  it('has accessible filter selects', () => {
    render(<JobsList />);
    
    const statusFilter = screen.getByLabelText(/filter jobs by status/i);
    expect(statusFilter).toBeInTheDocument();
    expect(statusFilter).toHaveAttribute('aria-label', 'Filter jobs by status');
    
    const assetTypeFilter = screen.getByLabelText(/filter jobs by asset type/i);
    expect(assetTypeFilter).toBeInTheDocument();
  });
});

