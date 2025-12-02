import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { AssetSelector } from './AssetSelector';
import { collectorsApi } from '@/lib/api/scheduler';

// Mock the API
vi.mock('@/lib/api/scheduler', () => ({
  collectorsApi: {
    search: vi.fn(),
  },
}));

describe('AssetSelector', () => {
  const mockOnSelect = vi.fn();
  const mockOnBack = vi.fn();
  const mockOnNext = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders asset selector with title', () => {
    render(
      <AssetSelector
        assetType="stock"
        selected=""
        onSelect={mockOnSelect}
        onBack={mockOnBack}
        onNext={mockOnNext}
      />
    );

    expect(screen.getByText('Select Asset')).toBeInTheDocument();
  });

  it('displays search input', () => {
    render(
      <AssetSelector
        assetType="stock"
        selected=""
        onSelect={mockOnSelect}
        onBack={mockOnBack}
        onNext={mockOnNext}
      />
    );

    const searchInput = screen.getByLabelText(/search for asset/i);
    expect(searchInput).toBeInTheDocument();
  });

  it('searches for assets when query is entered', async () => {
    const user = userEvent.setup();
    const mockResults = [
      { symbol: 'AAPL', name: 'Apple Inc.' },
      { symbol: 'MSFT', name: 'Microsoft Corporation' },
    ];

    vi.mocked(collectorsApi.search).mockResolvedValue({
      data: mockResults,
    } as any);

    render(
      <AssetSelector
        assetType="stock"
        selected=""
        onSelect={mockOnSelect}
        onBack={mockOnBack}
        onNext={mockOnNext}
      />
    );

    const searchInput = screen.getByLabelText(/search for asset/i);
    await user.type(searchInput, 'AAPL');

    await waitFor(() => {
      expect(collectorsApi.search).toHaveBeenCalledWith('stock', 'AAPL');
    }, { timeout: 1000 });
  });

  it('displays search results', async () => {
    const user = userEvent.setup();
    const mockResults = [
      { symbol: 'AAPL', name: 'Apple Inc.' },
      { symbol: 'MSFT', name: 'Microsoft Corporation' },
    ];

    vi.mocked(collectorsApi.search).mockResolvedValue({
      data: mockResults,
    } as any);

    render(
      <AssetSelector
        assetType="stock"
        selected=""
        onSelect={mockOnSelect}
        onBack={mockOnBack}
        onNext={mockOnNext}
      />
    );

    const searchInput = screen.getByLabelText(/search for asset/i);
    await user.type(searchInput, 'AAPL');

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
    });
  });

  it('calls onSelect when asset is selected', async () => {
    const user = userEvent.setup();
    const mockResults = [
      { symbol: 'AAPL', name: 'Apple Inc.' },
    ];

    vi.mocked(collectorsApi.search).mockResolvedValue({
      data: mockResults,
    } as any);

    render(
      <AssetSelector
        assetType="stock"
        selected=""
        onSelect={mockOnSelect}
        onBack={mockOnBack}
        onNext={mockOnNext}
      />
    );

    const searchInput = screen.getByLabelText(/search for asset/i);
    await user.type(searchInput, 'AAPL');

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    const assetButton = screen.getByRole('button', { name: /select aapl/i });
    await user.click(assetButton);

    expect(mockOnSelect).toHaveBeenCalledWith('AAPL');
  });

  it('displays selected asset', () => {
    render(
      <AssetSelector
        assetType="stock"
        selected="AAPL"
        onSelect={mockOnSelect}
        onBack={mockOnBack}
        onNext={mockOnNext}
      />
    );

    expect(screen.getByText('AAPL')).toBeInTheDocument();
  });

  it('supports bulk mode selection', async () => {
    const user = userEvent.setup();
    const mockResults = [
      { symbol: 'AAPL', name: 'Apple Inc.' },
      { symbol: 'MSFT', name: 'Microsoft Corporation' },
    ];

    vi.mocked(collectorsApi.search).mockResolvedValue({
      data: mockResults,
    } as any);

    render(
      <AssetSelector
        assetType="stock"
        selected={[]}
        onSelect={mockOnSelect}
        onBack={mockOnBack}
        onNext={mockOnNext}
        bulkMode={true}
      />
    );

    // Enable bulk mode
    const bulkModeCheckbox = screen.getByLabelText(/enable bulk selection/i);
    expect(bulkModeCheckbox).toBeChecked();

    const searchInput = screen.getByLabelText(/search for asset/i);
    await user.type(searchInput, 'AAPL');

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    const assetButton = screen.getByRole('button', { name: /select aapl/i });
    await user.click(assetButton);

    expect(mockOnSelect).toHaveBeenCalledWith(['AAPL']);
  });

  it('calls onBack when back button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <AssetSelector
        assetType="stock"
        selected=""
        onSelect={mockOnSelect}
        onBack={mockOnBack}
        onNext={mockOnNext}
      />
    );

    const backButton = screen.getByRole('button', { name: /back/i });
    await user.click(backButton);

    expect(mockOnBack).toHaveBeenCalledTimes(1);
  });

  it('calls onNext when next button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <AssetSelector
        assetType="stock"
        selected="AAPL"
        onSelect={mockOnSelect}
        onBack={mockOnBack}
        onNext={mockOnNext}
      />
    );

    const nextButton = screen.getByRole('button', { name: /next/i });
    await user.click(nextButton);

    expect(mockOnNext).toHaveBeenCalledTimes(1);
  });

  it('disables next button when no asset is selected', () => {
    render(
      <AssetSelector
        assetType="stock"
        selected=""
        onSelect={mockOnSelect}
        onBack={mockOnBack}
        onNext={mockOnNext}
      />
    );

    const nextButton = screen.getByRole('button', { name: /next/i });
    expect(nextButton).toBeDisabled();
  });

  it('has accessible search input', () => {
    render(
      <AssetSelector
        assetType="stock"
        selected=""
        onSelect={mockOnSelect}
        onBack={mockOnBack}
        onNext={mockOnNext}
      />
    );

    const searchInput = screen.getByLabelText(/search for asset/i);
    expect(searchInput).toHaveAttribute('aria-label', 'Search for asset');
  });
});

