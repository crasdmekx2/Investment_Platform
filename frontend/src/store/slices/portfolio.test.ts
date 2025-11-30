import { describe, it, expect, beforeEach } from 'vitest';
import { usePortfolioStore } from './portfolio';
import { mockPortfolio, mockPortfolios, mockTransaction } from '@/test/fixtures/portfolio';
import type { Portfolio, Holding, Transaction } from '@/types/portfolio';

describe('PortfolioStore', () => {
  beforeEach(() => {
    // Reset store state
    usePortfolioStore.setState({
      portfolios: [],
      selectedPortfolio: null,
      isLoading: false,
      error: null,
    });
  });

  it('initializes with empty state', () => {
    const state = usePortfolioStore.getState();
    expect(state.portfolios).toEqual([]);
    expect(state.selectedPortfolio).toBeNull();
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('sets portfolios', () => {
    usePortfolioStore.getState().setPortfolios(mockPortfolios);

    const state = usePortfolioStore.getState();
    expect(state.portfolios).toEqual(mockPortfolios);
    expect(state.portfolios).toHaveLength(2);
  });

  it('adds portfolio', () => {
    usePortfolioStore.getState().addPortfolio(mockPortfolio);

    const state = usePortfolioStore.getState();
    expect(state.portfolios).toHaveLength(1);
    expect(state.portfolios[0]).toEqual(mockPortfolio);
  });

  it('updates portfolio', () => {
    usePortfolioStore.getState().addPortfolio(mockPortfolio);
    
    const updates = { name: 'Updated Portfolio' };
    usePortfolioStore.getState().updatePortfolio(mockPortfolio.id, updates);

    const state = usePortfolioStore.getState();
    expect(state.portfolios[0].name).toBe('Updated Portfolio');
  });

  it('updates selected portfolio when it matches', () => {
    usePortfolioStore.getState().addPortfolio(mockPortfolio);
    usePortfolioStore.getState().setSelectedPortfolio(mockPortfolio);

    const updates = { name: 'Updated Name' };
    usePortfolioStore.getState().updatePortfolio(mockPortfolio.id, updates);

    const state = usePortfolioStore.getState();
    expect(state.selectedPortfolio?.name).toBe('Updated Name');
  });

  it('removes portfolio', () => {
    usePortfolioStore.getState().setPortfolios(mockPortfolios);
    usePortfolioStore.getState().removePortfolio(mockPortfolios[0].id);

    const state = usePortfolioStore.getState();
    expect(state.portfolios).toHaveLength(1);
    expect(state.portfolios[0].id).toBe(mockPortfolios[1].id);
  });

  it('clears selected portfolio when it is removed', () => {
    usePortfolioStore.getState().addPortfolio(mockPortfolio);
    usePortfolioStore.getState().setSelectedPortfolio(mockPortfolio);
    usePortfolioStore.getState().removePortfolio(mockPortfolio.id);

    const state = usePortfolioStore.getState();
    expect(state.selectedPortfolio).toBeNull();
  });

  it('sets selected portfolio', () => {
    usePortfolioStore.getState().addPortfolio(mockPortfolio);
    usePortfolioStore.getState().setSelectedPortfolio(mockPortfolio);

    const state = usePortfolioStore.getState();
    expect(state.selectedPortfolio).toEqual(mockPortfolio);
  });

  it('updates holding in portfolio', () => {
    usePortfolioStore.getState().addPortfolio(mockPortfolio);
    
    const updatedHolding: Holding = {
      ...mockPortfolio.holdings[0],
      quantity: 150,
    };

    usePortfolioStore.getState().updateHolding(mockPortfolio.id, updatedHolding);

    const state = usePortfolioStore.getState();
    const portfolio = state.portfolios.find((p) => p.id === mockPortfolio.id);
    expect(portfolio?.holdings[0].quantity).toBe(150);
  });

  it('sets loading state', () => {
    usePortfolioStore.getState().setLoading(true);
    expect(usePortfolioStore.getState().isLoading).toBe(true);

    usePortfolioStore.getState().setLoading(false);
    expect(usePortfolioStore.getState().isLoading).toBe(false);
  });

  it('sets and clears error', () => {
    const errorMessage = 'Failed to load portfolio';
    usePortfolioStore.getState().setError(errorMessage);
    expect(usePortfolioStore.getState().error).toBe(errorMessage);

    usePortfolioStore.getState().clearError();
    expect(usePortfolioStore.getState().error).toBeNull();
  });
});

