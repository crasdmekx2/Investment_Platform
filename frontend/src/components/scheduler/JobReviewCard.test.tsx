import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { JobReviewCard } from './JobReviewCard';

describe('JobReviewCard', () => {
  const mockOnBack = vi.fn();
  const mockOnCreate = vi.fn();

  const defaultProps = {
    assetType: 'stock' as const,
    symbol: 'AAPL',
    collectorKwargs: { interval: '1d' },
    triggerConfig: { trigger_type: 'interval', minutes: 5 },
    startDate: '2024-01-01',
    endDate: '2024-01-31',
    incremental: true,
    onBack: mockOnBack,
    onCreate: mockOnCreate,
    isLoading: false,
  };

  it('renders review card with title', () => {
    render(<JobReviewCard {...defaultProps} />);

    expect(screen.getByText('Review Job Configuration')).toBeInTheDocument();
  });

  it('displays asset type', () => {
    render(<JobReviewCard {...defaultProps} />);

    expect(screen.getByText('Stock')).toBeInTheDocument();
  });

  it('displays symbol', () => {
    render(<JobReviewCard {...defaultProps} />);

    expect(screen.getByText('AAPL')).toBeInTheDocument();
  });

  it('displays collection parameters', () => {
    render(<JobReviewCard {...defaultProps} />);

    expect(screen.getByText('interval: 1d')).toBeInTheDocument();
  });

  it('displays schedule information', () => {
    render(<JobReviewCard {...defaultProps} />);

    expect(screen.getByText(/every 5 minutes/i)).toBeInTheDocument();
  });

  it('displays execute now when trigger config has execute_now', () => {
    render(
      <JobReviewCard
        {...defaultProps}
        triggerConfig={{ trigger_type: 'interval', minutes: 5, execute_now: true }}
      />
    );

    expect(screen.getByText(/execute now.*one-time/i)).toBeInTheDocument();
    expect(screen.getByText(/will execute immediately/i)).toBeInTheDocument();
  });

  it('displays incremental mode', () => {
    render(<JobReviewCard {...defaultProps} incremental={true} />);

    expect(screen.getByText(/incremental.*missing data only/i)).toBeInTheDocument();
  });

  it('displays full history mode', () => {
    render(<JobReviewCard {...defaultProps} incremental={false} />);

    expect(screen.getByText('Full History')).toBeInTheDocument();
  });

  it('displays date range when not incremental', () => {
    render(
      <JobReviewCard
        {...defaultProps}
        incremental={false}
        startDate="2024-01-01"
        endDate="2024-01-31"
      />
    );

    // Date format may vary by locale, so check for date parts
    expect(screen.getByText(/2024/i)).toBeInTheDocument();
  });

  it('calls onBack when back button is clicked', async () => {
    const user = userEvent.setup();
    render(<JobReviewCard {...defaultProps} />);

    const backButton = screen.getByRole('button', { name: /back/i });
    await user.click(backButton);

    expect(mockOnBack).toHaveBeenCalledTimes(1);
  });

  it('calls onCreate when create button is clicked', async () => {
    const user = userEvent.setup();
    render(<JobReviewCard {...defaultProps} />);

    const createButton = screen.getByRole('button', { name: /create job/i });
    await user.click(createButton);

    expect(mockOnCreate).toHaveBeenCalledTimes(1);
  });

  it('disables buttons when loading', () => {
    render(<JobReviewCard {...defaultProps} isLoading={true} />);

    const backButton = screen.getByRole('button', { name: /back/i });
    // When loading, button text changes to "Loading..."
    const createButton = screen.getByRole('button', { name: /loading/i });

    expect(backButton).toBeDisabled();
    expect(createButton).toBeDisabled();
  });

  it('has accessible buttons', () => {
    render(<JobReviewCard {...defaultProps} />);

    const backButton = screen.getByRole('button', { name: /back/i });
    const createButton = screen.getByRole('button', { name: /create job/i });

    expect(backButton).toHaveClass('min-h-[44px]');
    expect(createButton).toHaveClass('min-h-[44px]');
  });
});

