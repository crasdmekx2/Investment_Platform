import { create } from 'zustand';
import type { Portfolio, Holding, Transaction } from '@/types/portfolio';

interface PortfolioState {
  portfolios: Portfolio[];
  selectedPortfolio: Portfolio | null;
  isLoading: boolean;
  error: string | null;
  setPortfolios: (portfolios: Portfolio[]) => void;
  addPortfolio: (portfolio: Portfolio) => void;
  updatePortfolio: (id: string, portfolio: Partial<Portfolio>) => void;
  removePortfolio: (id: string) => void;
  setSelectedPortfolio: (portfolio: Portfolio | null) => void;
  updateHolding: (portfolioId: string, holding: Holding) => void;
  addTransaction: (portfolioId: string, transaction: Transaction) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const usePortfolioStore = create<PortfolioState>((set) => ({
  portfolios: [],
  selectedPortfolio: null,
  isLoading: false,
  error: null,
  setPortfolios: (portfolios) => set({ portfolios }),
  addPortfolio: (portfolio) =>
    set((state) => ({
      portfolios: [...state.portfolios, portfolio],
    })),
  updatePortfolio: (id, updates) =>
    set((state) => ({
      portfolios: state.portfolios.map((p) =>
        p.id === id ? { ...p, ...updates } : p
      ),
      selectedPortfolio:
        state.selectedPortfolio?.id === id
          ? { ...state.selectedPortfolio, ...updates }
          : state.selectedPortfolio,
    })),
  removePortfolio: (id) =>
    set((state) => ({
      portfolios: state.portfolios.filter((p) => p.id !== id),
      selectedPortfolio:
        state.selectedPortfolio?.id === id ? null : state.selectedPortfolio,
    })),
  setSelectedPortfolio: (portfolio) => set({ selectedPortfolio: portfolio }),
  updateHolding: (portfolioId, holding) =>
    set((state) => ({
      portfolios: state.portfolios.map((p) =>
        p.id === portfolioId
          ? {
              ...p,
              holdings: p.holdings.map((h) =>
                h.id === holding.id ? holding : h
              ),
            }
          : p
      ),
    })),
  addTransaction: (portfolioId, transaction) =>
    set((state) => ({
      portfolios: state.portfolios.map((p) =>
        p.id === portfolioId
          ? { ...p, transactions: [...(p as any).transactions, transaction] }
          : p
      ),
    })),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));

