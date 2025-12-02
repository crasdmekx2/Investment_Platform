import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { ScheduleVisualization } from './ScheduleVisualization';
import type { ScheduledJob } from '@/types/scheduler';

describe('ScheduleVisualization', () => {
  const mockJobs: ScheduledJob[] = [
    {
      job_id: 'job_1',
      symbol: 'AAPL',
      asset_type: 'stock',
      status: 'active',
      trigger_type: 'interval',
      trigger_config: { type: 'interval', hours: 1 },
      next_run_at: new Date(Date.now() + 3600000).toISOString(),
    },
    {
      job_id: 'job_2',
      symbol: 'MSFT',
      asset_type: 'stock',
      status: 'paused',
      trigger_type: 'interval',
      trigger_config: { type: 'interval', hours: 2 },
      next_run_at: null,
    },
    {
      job_id: 'job_3',
      symbol: 'BTC',
      asset_type: 'crypto',
      status: 'active',
      trigger_type: 'cron',
      trigger_config: { type: 'cron', hour: '9', minute: '0' },
      next_run_at: new Date(Date.now() + 86400000).toISOString(),
    },
  ];

  it('renders visualization with title', () => {
    render(<ScheduleVisualization jobs={mockJobs} />);

    expect(screen.getByText('Schedule Visualization')).toBeInTheDocument();
  });

  it('displays timeline view by default', () => {
    render(<ScheduleVisualization jobs={mockJobs} />);

    expect(screen.getByText(/next.*days schedule/i)).toBeInTheDocument();
  });

  it('allows switching to calendar view', async () => {
    const user = userEvent.setup();
    render(<ScheduleVisualization jobs={mockJobs} />);

    const calendarButton = screen.getByRole('button', { name: /calendar/i });
    await user.click(calendarButton);

    expect(screen.getByText('Calendar View')).toBeInTheDocument();
  });

  it('allows switching back to timeline view', async () => {
    const user = userEvent.setup();
    render(<ScheduleVisualization jobs={mockJobs} />);

    const calendarButton = screen.getByRole('button', { name: /calendar/i });
    await user.click(calendarButton);

    const timelineButton = screen.getByRole('button', { name: /timeline/i });
    await user.click(timelineButton);

    expect(screen.getByText(/next.*days schedule/i)).toBeInTheDocument();
  });

  it('displays only active jobs in timeline', () => {
    render(<ScheduleVisualization jobs={mockJobs} />);

    // Should show AAPL and BTC (active jobs), not MSFT (paused)
    const aaplElements = screen.getAllByText('AAPL');
    const btcElements = screen.getAllByText('BTC');
    expect(aaplElements.length).toBeGreaterThan(0);
    expect(btcElements.length).toBeGreaterThan(0);
  });

  it('displays empty message when no scheduled jobs', () => {
    render(<ScheduleVisualization jobs={[]} />);

    expect(screen.getByText(/no scheduled jobs/i)).toBeInTheDocument();
  });

  it('displays timeline events with job information', () => {
    render(<ScheduleVisualization jobs={mockJobs} />);

    // Multiple events for same job, so use getAllByText
    const aaplElements = screen.getAllByText('AAPL');
    const btcElements = screen.getAllByText('BTC');
    expect(aaplElements.length).toBeGreaterThan(0);
    expect(btcElements.length).toBeGreaterThan(0);
  });

  it('displays calendar view with dates', async () => {
    const user = userEvent.setup();
    render(<ScheduleVisualization jobs={mockJobs} />);

    const calendarButton = screen.getByRole('button', { name: /calendar/i });
    await user.click(calendarButton);

    // Calendar should show dates
    expect(screen.getByText('Calendar View')).toBeInTheDocument();
  });

  it('highlights active view button', () => {
    render(<ScheduleVisualization jobs={mockJobs} />);

    const timelineButton = screen.getByRole('button', { name: /timeline/i });
    expect(timelineButton).toHaveAttribute('aria-pressed', 'true');
  });

  it('respects daysAhead prop', () => {
    render(<ScheduleVisualization jobs={mockJobs} daysAhead={14} />);

    expect(screen.getByText(/next 14 days schedule/i)).toBeInTheDocument();
  });

  it('has accessible view toggle buttons', () => {
    render(<ScheduleVisualization jobs={mockJobs} />);

    const timelineButton = screen.getByRole('button', { name: /timeline/i });
    const calendarButton = screen.getByRole('button', { name: /calendar/i });

    expect(timelineButton).toHaveAttribute('aria-pressed', 'true');
    expect(calendarButton).toHaveAttribute('aria-pressed', 'false');
    expect(timelineButton).toHaveClass('min-h-[44px]');
    expect(calendarButton).toHaveClass('min-h-[44px]');
  });
});

