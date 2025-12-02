import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { AssetTypeSelector } from './AssetTypeSelector';
import type { CollectorMetadata } from '@/types/scheduler';

describe('AssetTypeSelector', () => {
  const mockOnSelect = vi.fn();
  const mockOnNext = vi.fn();

  const mockMetadata: CollectorMetadata = {
    stock: {
      description: 'Stock market data',
      parameters: [],
    },
    crypto: {
      description: 'Cryptocurrency data',
      parameters: [],
    },
  };

  it('renders asset type selector with title', () => {
    render(
      <AssetTypeSelector
        metadata={mockMetadata}
        selected={null}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
      />
    );

    expect(screen.getByText('Select Asset Type')).toBeInTheDocument();
  });

  it('displays all asset types', () => {
    render(
      <AssetTypeSelector
        metadata={mockMetadata}
        selected={null}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
      />
    );

    expect(screen.getByText('Stock')).toBeInTheDocument();
    expect(screen.getByText('Cryptocurrency')).toBeInTheDocument();
    expect(screen.getByText('Forex')).toBeInTheDocument();
    expect(screen.getByText('Bond')).toBeInTheDocument();
    expect(screen.getByText('Commodity')).toBeInTheDocument();
    expect(screen.getByText('Economic Indicator')).toBeInTheDocument();
  });

  it('calls onSelect when asset type is clicked', async () => {
    const user = userEvent.setup();
    render(
      <AssetTypeSelector
        metadata={mockMetadata}
        selected={null}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
      />
    );

    const stockButton = screen.getByRole('button', { name: /select stock asset type/i });
    await user.click(stockButton);

    expect(mockOnSelect).toHaveBeenCalledWith('stock');
  });

  it('highlights selected asset type', () => {
    render(
      <AssetTypeSelector
        metadata={mockMetadata}
        selected="stock"
        onSelect={mockOnSelect}
        onNext={mockOnNext}
      />
    );

    const stockButton = screen.getByRole('button', { name: /select stock asset type/i });
    expect(stockButton).toHaveAttribute('aria-pressed', 'true');
  });

  it('disables next button when no asset type is selected', () => {
    render(
      <AssetTypeSelector
        metadata={mockMetadata}
        selected={null}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
      />
    );

    const nextButton = screen.getByRole('button', { name: /next/i });
    expect(nextButton).toBeDisabled();
  });

  it('enables next button when asset type is selected', () => {
    render(
      <AssetTypeSelector
        metadata={mockMetadata}
        selected="stock"
        onSelect={mockOnSelect}
        onNext={mockOnNext}
      />
    );

    const nextButton = screen.getByRole('button', { name: /next/i });
    expect(nextButton).not.toBeDisabled();
  });

  it('calls onNext when next button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <AssetTypeSelector
        metadata={mockMetadata}
        selected="stock"
        onSelect={mockOnSelect}
        onNext={mockOnNext}
      />
    );

    const nextButton = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton);

    expect(mockOnNext).toHaveBeenCalledTimes(1);
  });

  it('displays metadata description when available', () => {
    render(
      <AssetTypeSelector
        metadata={mockMetadata}
        selected={null}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
      />
    );

    expect(screen.getByText('Stock market data')).toBeInTheDocument();
    expect(screen.getByText('Cryptocurrency data')).toBeInTheDocument();
  });

  it('has accessible asset type buttons', () => {
    render(
      <AssetTypeSelector
        metadata={mockMetadata}
        selected={null}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
      />
    );

    const stockButton = screen.getByRole('button', { name: /select stock asset type/i });
    expect(stockButton).toHaveAttribute('aria-pressed', 'false');
    expect(stockButton).toHaveClass('min-h-[120px]'); // Accessibility: minimum touch target
  });
});

