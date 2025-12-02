import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { Scheduler } from './Scheduler';

// Mock child components
vi.mock('@/components/scheduler/JobsDashboard', () => ({
  JobsDashboard: () => <div data-testid="jobs-dashboard">Jobs Dashboard</div>,
}));

vi.mock('@/components/scheduler/JobsList', () => ({
  JobsList: () => <div data-testid="jobs-list">Jobs List</div>,
}));

vi.mock('@/components/scheduler/JobCreator', () => ({
  JobCreator: ({ onSuccess }: { onSuccess?: () => void }) => (
    <div data-testid="job-creator">
      Job Creator
      <button onClick={onSuccess}>Success</button>
    </div>
  ),
}));

vi.mock('@/components/scheduler/CollectionLogsView', () => ({
  CollectionLogsView: () => <div data-testid="collection-logs">Collection Logs</div>,
}));

describe('Scheduler', () => {
  it('renders scheduler page with title', () => {
    render(<Scheduler />);

    expect(screen.getByText('Data Collection Scheduler')).toBeInTheDocument();
  });

  it('displays all tabs', () => {
    render(<Scheduler />);

    expect(screen.getByRole('button', { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /jobs/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create job/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /collection logs/i })).toBeInTheDocument();
  });

  it('displays dashboard tab by default', () => {
    render(<Scheduler />);

    expect(screen.getByTestId('jobs-dashboard')).toBeInTheDocument();
    expect(screen.queryByTestId('jobs-list')).not.toBeInTheDocument();
  });

  it('switches to jobs tab when clicked', async () => {
    const user = userEvent.setup();
    render(<Scheduler />);

    const jobsTab = screen.getByRole('button', { name: /jobs/i });
    await user.click(jobsTab);

    expect(screen.getByTestId('jobs-list')).toBeInTheDocument();
    expect(screen.queryByTestId('jobs-dashboard')).not.toBeInTheDocument();
  });

  it('switches to create job tab when clicked', async () => {
    const user = userEvent.setup();
    render(<Scheduler />);

    const createTab = screen.getByRole('button', { name: /create job/i });
    await user.click(createTab);

    expect(screen.getByTestId('job-creator')).toBeInTheDocument();
    expect(screen.queryByTestId('jobs-dashboard')).not.toBeInTheDocument();
  });

  it('switches to collection logs tab when clicked', async () => {
    const user = userEvent.setup();
    render(<Scheduler />);

    const logsTab = screen.getByRole('button', { name: /collection logs/i });
    await user.click(logsTab);

    expect(screen.getByTestId('collection-logs')).toBeInTheDocument();
    expect(screen.queryByTestId('jobs-dashboard')).not.toBeInTheDocument();
  });

  it('highlights active tab', async () => {
    const user = userEvent.setup();
    render(<Scheduler />);

    const jobsTab = screen.getByRole('button', { name: /jobs/i });
    await user.click(jobsTab);

    expect(jobsTab).toHaveAttribute('aria-current', 'page');
    expect(jobsTab).toHaveClass('border-primary-500', 'text-primary-600');
  });

  it('switches to jobs tab after successful job creation', async () => {
    const user = userEvent.setup();
    render(<Scheduler />);

    // Navigate to create tab
    const createTab = screen.getByRole('button', { name: /create job/i });
    await user.click(createTab);

    // Simulate successful job creation
    const successButton = screen.getByRole('button', { name: /success/i });
    await user.click(successButton);

    // Should switch to jobs tab
    expect(screen.getByTestId('jobs-list')).toBeInTheDocument();
    expect(screen.queryByTestId('job-creator')).not.toBeInTheDocument();
  });

  it('has accessible tabs', () => {
    render(<Scheduler />);

    const dashboardTab = screen.getByRole('button', { name: /dashboard/i });
    expect(dashboardTab).toHaveAttribute('aria-current', 'page');
    expect(dashboardTab).toHaveClass('min-h-[44px]', 'min-w-[44px]');
  });
});

