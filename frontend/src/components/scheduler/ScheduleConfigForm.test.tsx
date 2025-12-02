import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { ScheduleConfigForm } from './ScheduleConfigForm';

// Mock DependencySelector
vi.mock('@/components/scheduler/DependencySelector', () => ({
  DependencySelector: ({ selectedDependencies, onUpdate }: any) => (
    <div data-testid="dependency-selector">
      Dependencies: {selectedDependencies.length}
      <button onClick={() => onUpdate([])}>Clear</button>
    </div>
  ),
}));

describe('ScheduleConfigForm', () => {
  const mockOnUpdate = vi.fn();
  const mockOnBack = vi.fn();
  const mockOnNext = vi.fn();
  const mockOnRetryConfigUpdate = vi.fn();
  const mockOnDependenciesUpdate = vi.fn();

  const defaultProps = {
    triggerConfig: null,
    onUpdate: mockOnUpdate,
    onBack: mockOnBack,
    onNext: mockOnNext,
    incremental: false,
    startDate: '2024-01-01',
    endDate: '2024-01-31',
    maxRetries: 3,
    retryDelaySeconds: 60,
    retryBackoffMultiplier: 2.0,
    onRetryConfigUpdate: mockOnRetryConfigUpdate,
    dependencies: [],
    onDependenciesUpdate: mockOnDependenciesUpdate,
  };

  it('renders form with title', () => {
    render(<ScheduleConfigForm {...defaultProps} />);

    expect(screen.getByText('Schedule Configuration')).toBeInTheDocument();
  });

  it('displays interval trigger option', () => {
    render(<ScheduleConfigForm {...defaultProps} />);

    expect(screen.getByLabelText(/interval trigger/i)).toBeInTheDocument();
  });

  it('displays cron trigger option', () => {
    render(<ScheduleConfigForm {...defaultProps} />);

    expect(screen.getByLabelText(/cron schedule trigger/i)).toBeInTheDocument();
  });

  it('displays schedule now option when date range is provided', () => {
    render(<ScheduleConfigForm {...defaultProps} />);

    expect(screen.getByLabelText(/schedule now trigger/i)).toBeInTheDocument();
  });

  it('hides schedule now option when incremental', () => {
    render(<ScheduleConfigForm {...defaultProps} incremental={true} />);

    expect(screen.queryByLabelText(/schedule now trigger/i)).not.toBeInTheDocument();
  });

  it('displays interval configuration when interval is selected', async () => {
    const user = userEvent.setup();
    render(<ScheduleConfigForm {...defaultProps} />);

    const intervalRadio = screen.getByLabelText(/interval trigger/i);
    await user.click(intervalRadio);

    expect(screen.getByLabelText(/hours/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/minutes/i)).toBeInTheDocument();
  });

  it('displays cron configuration when cron is selected', async () => {
    const user = userEvent.setup();
    render(<ScheduleConfigForm {...defaultProps} />);

    const cronRadio = screen.getByLabelText(/cron schedule trigger/i);
    await user.click(cronRadio);

    expect(screen.getByLabelText(/hour.*0-23/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/minute.*0-59/i)).toBeInTheDocument();
  });

  it('updates interval configuration', async () => {
    const user = userEvent.setup();
    render(<ScheduleConfigForm {...defaultProps} />);

    const intervalRadio = screen.getByLabelText(/interval trigger/i);
    await user.click(intervalRadio);

    const hoursInput = screen.getByLabelText(/hours/i);
    await user.clear(hoursInput);
    await user.type(hoursInput, '2');

    expect(hoursInput).toHaveValue(2);
  });

  it('updates cron configuration', async () => {
    const user = userEvent.setup();
    render(<ScheduleConfigForm {...defaultProps} />);

    const cronRadio = screen.getByLabelText(/cron schedule trigger/i);
    await user.click(cronRadio);

    const hourInput = screen.getByLabelText(/hour.*0-23/i);
    await user.clear(hourInput);
    await user.type(hourInput, '9');

    expect(hourInput).toHaveValue('9');
  });

  it('calls onUpdate with execute_now when schedule now is selected', async () => {
    const user = userEvent.setup();
    render(<ScheduleConfigForm {...defaultProps} />);

    const scheduleNowRadio = screen.getByLabelText(/schedule now trigger/i);
    await user.click(scheduleNowRadio);

    expect(mockOnUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        execute_now: true,
      })
    );
  });

  it('displays retry configuration for interval and cron', () => {
    render(<ScheduleConfigForm {...defaultProps} />);

    expect(screen.getByLabelText(/maximum retries/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/initial retry delay/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/backoff multiplier/i)).toBeInTheDocument();
  });

  it('hides retry configuration for schedule now', async () => {
    const user = userEvent.setup();
    render(<ScheduleConfigForm {...defaultProps} />);

    const scheduleNowRadio = screen.getByLabelText(/schedule now trigger/i);
    await user.click(scheduleNowRadio);

    expect(screen.queryByLabelText(/maximum retries/i)).not.toBeInTheDocument();
  });

  it('calls onRetryConfigUpdate when retry settings change', async () => {
    const user = userEvent.setup();
    render(<ScheduleConfigForm {...defaultProps} />);

    const maxRetriesInput = screen.getByLabelText(/maximum retries/i);
    await user.clear(maxRetriesInput);
    await user.type(maxRetriesInput, '5');

    expect(mockOnRetryConfigUpdate).toHaveBeenCalledWith(5, 60, 2.0);
  });

  it('displays dependency selector when dependencies are enabled', () => {
    render(<ScheduleConfigForm {...defaultProps} />);

    expect(screen.getByTestId('dependency-selector')).toBeInTheDocument();
  });

  it('hides dependency selector for schedule now', async () => {
    const user = userEvent.setup();
    render(<ScheduleConfigForm {...defaultProps} />);

    const scheduleNowRadio = screen.getByLabelText(/schedule now trigger/i);
    await user.click(scheduleNowRadio);

    expect(screen.queryByTestId('dependency-selector')).not.toBeInTheDocument();
  });

  it('calls onBack when back button is clicked', async () => {
    const user = userEvent.setup();
    render(<ScheduleConfigForm {...defaultProps} />);

    const backButton = screen.getByRole('button', { name: /back/i });
    await user.click(backButton);

    expect(mockOnBack).toHaveBeenCalledTimes(1);
  });

  it('calls onNext and onUpdate when next button is clicked', async () => {
    const user = userEvent.setup();
    render(<ScheduleConfigForm {...defaultProps} />);

    const nextButton = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton);

    expect(mockOnUpdate).toHaveBeenCalled();
    expect(mockOnNext).toHaveBeenCalledTimes(1);
  });

  it('has accessible form inputs', () => {
    render(<ScheduleConfigForm {...defaultProps} />);

    const intervalRadio = screen.getByLabelText(/interval trigger/i);
    expect(intervalRadio).toHaveAttribute('aria-label', 'Interval trigger');
    expect(intervalRadio).toHaveClass('min-h-[44px]');
  });
});

