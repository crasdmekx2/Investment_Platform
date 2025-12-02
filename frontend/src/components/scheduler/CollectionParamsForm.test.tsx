import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { CollectionParamsForm } from './CollectionParamsForm';

describe('CollectionParamsForm', () => {
  const mockOnUpdate = vi.fn();
  const mockOnBack = vi.fn();
  const mockOnNext = vi.fn();
  const mockOnStartDateChange = vi.fn();
  const mockOnEndDateChange = vi.fn();
  const mockOnIncrementalChange = vi.fn();

  const defaultProps = {
    assetType: 'stock' as const,
    collectorKwargs: {},
    onUpdate: mockOnUpdate,
    startDate: '',
    endDate: '',
    onStartDateChange: mockOnStartDateChange,
    onEndDateChange: mockOnEndDateChange,
    incremental: true,
    onIncrementalChange: mockOnIncrementalChange,
    onBack: mockOnBack,
    onNext: mockOnNext,
  };

  it('renders form with title', () => {
    render(<CollectionParamsForm {...defaultProps} />);

    expect(screen.getByText('Collection Parameters')).toBeInTheDocument();
  });

  it('displays stock interval selector for stock asset type', () => {
    render(<CollectionParamsForm {...defaultProps} assetType="stock" />);

    expect(screen.getByLabelText(/interval/i)).toBeInTheDocument();
  });

  it('displays crypto granularity selector for crypto asset type', () => {
    render(<CollectionParamsForm {...defaultProps} assetType="crypto" />);

    expect(screen.getByLabelText(/granularity/i)).toBeInTheDocument();
  });

  it('updates collector kwargs when stock interval changes', async () => {
    const user = userEvent.setup();
    render(<CollectionParamsForm {...defaultProps} assetType="stock" />);

    const intervalSelect = screen.getByLabelText(/interval/i);
    await user.selectOptions(intervalSelect, '1h');

    expect(mockOnUpdate).toHaveBeenCalledWith({ interval: '1h' });
  });

  it('updates collector kwargs when crypto granularity changes', async () => {
    const user = userEvent.setup();
    render(<CollectionParamsForm {...defaultProps} assetType="crypto" />);

    const granularitySelect = screen.getByLabelText(/granularity/i);
    await user.selectOptions(granularitySelect, 'ONE_HOUR');

    expect(mockOnUpdate).toHaveBeenCalledWith({ granularity: 'ONE_HOUR' });
  });

  it('displays incremental mode checkbox', () => {
    render(<CollectionParamsForm {...defaultProps} />);

    const checkbox = screen.getByLabelText(/incremental mode/i);
    expect(checkbox).toBeInTheDocument();
    expect(checkbox).toBeChecked();
  });

  it('calls onIncrementalChange when checkbox is toggled', async () => {
    const user = userEvent.setup();
    render(<CollectionParamsForm {...defaultProps} />);

    const checkbox = screen.getByLabelText(/incremental mode/i);
    await user.click(checkbox);

    expect(mockOnIncrementalChange).toHaveBeenCalledWith(false);
  });

  it('displays date range inputs when not incremental', () => {
    render(<CollectionParamsForm {...defaultProps} incremental={false} />);

    expect(screen.getByLabelText(/start date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/end date/i)).toBeInTheDocument();
  });

  it('hides date range inputs when incremental', () => {
    render(<CollectionParamsForm {...defaultProps} incremental={true} />);

    expect(screen.queryByLabelText(/start date/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/end date/i)).not.toBeInTheDocument();
  });

  it('calls onStartDateChange when start date changes', async () => {
    const user = userEvent.setup();
    render(<CollectionParamsForm {...defaultProps} incremental={false} />);

    const startDateInput = screen.getByLabelText(/start date/i);
    await user.type(startDateInput, '2024-01-01');

    expect(mockOnStartDateChange).toHaveBeenCalled();
  });

  it('calls onEndDateChange when end date changes', async () => {
    const user = userEvent.setup();
    render(<CollectionParamsForm {...defaultProps} incremental={false} />);

    const endDateInput = screen.getByLabelText(/end date/i);
    await user.type(endDateInput, '2024-01-31');

    expect(mockOnEndDateChange).toHaveBeenCalled();
  });

  it('calls onBack when back button is clicked', async () => {
    const user = userEvent.setup();
    render(<CollectionParamsForm {...defaultProps} />);

    const backButton = screen.getByRole('button', { name: /back/i });
    await user.click(backButton);

    expect(mockOnBack).toHaveBeenCalledTimes(1);
  });

  it('calls onNext when next button is clicked', async () => {
    const user = userEvent.setup();
    render(<CollectionParamsForm {...defaultProps} />);

    const nextButton = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton);

    expect(mockOnNext).toHaveBeenCalledTimes(1);
  });

  it('has accessible form inputs', () => {
    render(<CollectionParamsForm {...defaultProps} assetType="stock" />);

    const intervalSelect = screen.getByLabelText(/interval/i);
    expect(intervalSelect).toHaveAttribute('aria-describedby', 'interval-help');
    expect(intervalSelect).toHaveClass('min-h-[44px]');
  });

  it('preserves existing collector kwargs when updating', async () => {
    const user = userEvent.setup();
    render(
      <CollectionParamsForm
        {...defaultProps}
        assetType="stock"
        collectorKwargs={{ interval: '1d', otherParam: 'value' }}
      />
    );

    const intervalSelect = screen.getByLabelText(/interval/i);
    await user.selectOptions(intervalSelect, '1h');

    expect(mockOnUpdate).toHaveBeenCalledWith({
      interval: '1h',
      otherParam: 'value',
    });
  });
});

