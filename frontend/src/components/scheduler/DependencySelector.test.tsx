import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { DependencySelector } from './DependencySelector';
import { schedulerApi } from '@/lib/api/scheduler';

// Mock the API
vi.mock('@/lib/api/scheduler', () => ({
  schedulerApi: {
    listJobs: vi.fn(),
  },
}));

describe('DependencySelector', () => {
  const mockOnUpdate = vi.fn();

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
      status: 'active',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(schedulerApi.listJobs).mockResolvedValue({
      data: mockJobs,
    } as any);
  });

  it('renders dependency selector with title', async () => {
    render(
      <DependencySelector
        selectedDependencies={[]}
        onUpdate={mockOnUpdate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Job Dependencies')).toBeInTheDocument();
    });
  });

  it('loads and displays available jobs', async () => {
    render(
      <DependencySelector
        selectedDependencies={[]}
        onUpdate={mockOnUpdate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('MSFT')).toBeInTheDocument();
    });
  });

  it('filters out current job from dependencies', async () => {
    render(
      <DependencySelector
        currentJobId="job_1"
        selectedDependencies={[]}
        onUpdate={mockOnUpdate}
      />
    );

    await waitFor(() => {
      expect(screen.queryByText('AAPL')).not.toBeInTheDocument();
      expect(screen.getByText('MSFT')).toBeInTheDocument();
    });
  });

  it('allows selecting a job as dependency', async () => {
    const user = userEvent.setup();
    render(
      <DependencySelector
        selectedDependencies={[]}
        onUpdate={mockOnUpdate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    const checkbox = screen.getByLabelText(/select aapl as dependency/i);
    await user.click(checkbox);

    expect(mockOnUpdate).toHaveBeenCalledWith([
      { depends_on_job_id: 'job_1', condition: 'success' },
    ]);
  });

  it('allows removing a dependency', async () => {
    const user = userEvent.setup();
    render(
      <DependencySelector
        selectedDependencies={[{ depends_on_job_id: 'job_1', condition: 'success' }]}
        onUpdate={mockOnUpdate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    const checkbox = screen.getByLabelText(/select aapl as dependency/i);
    await user.click(checkbox);

    expect(mockOnUpdate).toHaveBeenCalledWith([]);
  });

  it('allows changing dependency condition', async () => {
    const user = userEvent.setup();
    render(
      <DependencySelector
        selectedDependencies={[{ depends_on_job_id: 'job_1', condition: 'success' }]}
        onUpdate={mockOnUpdate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    const conditionSelect = screen.getByLabelText(/condition for aapl dependency/i);
    await user.selectOptions(conditionSelect, 'complete');

    expect(mockOnUpdate).toHaveBeenCalledWith([
      { depends_on_job_id: 'job_1', condition: 'complete' },
    ]);
  });

  it('displays selected dependencies', async () => {
    render(
      <DependencySelector
        selectedDependencies={[
          { depends_on_job_id: 'job_1', condition: 'success' },
          { depends_on_job_id: 'job_2', condition: 'complete' },
        ]}
        onUpdate={mockOnUpdate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/selected dependencies \(2\)/i)).toBeInTheDocument();
      expect(screen.getByText(/AAPL.*success/i)).toBeInTheDocument();
      expect(screen.getByText(/MSFT.*complete/i)).toBeInTheDocument();
    });
  });

  it('filters jobs by search query', async () => {
    const user = userEvent.setup();
    render(
      <DependencySelector
        selectedDependencies={[]}
        onUpdate={mockOnUpdate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    const searchInput = screen.getByLabelText(/search for jobs/i);
    await user.type(searchInput, 'AAPL');

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.queryByText('MSFT')).not.toBeInTheDocument();
    });
  });

  it('displays empty message when no jobs found', async () => {
    vi.mocked(schedulerApi.listJobs).mockResolvedValue({
      data: [],
    } as any);

    render(
      <DependencySelector
        selectedDependencies={[]}
        onUpdate={mockOnUpdate}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/no jobs found/i)).toBeInTheDocument();
    });
  });

  it('has accessible search input', async () => {
    render(
      <DependencySelector
        selectedDependencies={[]}
        onUpdate={mockOnUpdate}
      />
    );

    await waitFor(() => {
      const searchInput = screen.getByLabelText(/search for jobs/i);
      expect(searchInput).toHaveAttribute('aria-label', 'Search for jobs');
      expect(searchInput).toHaveAttribute('aria-describedby', 'dependency-search-help');
    });
  });
});

