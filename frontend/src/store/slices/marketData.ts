import { create } from 'zustand';
import type { MarketData, PriceData, AssetInfo } from '@/types/market';

interface MarketDataState {
  marketData: Record<string, MarketData>;
  priceHistory: Record<string, PriceData[]>;
  assetInfo: Record<string, AssetInfo>;
  isLoading: boolean;
  error: string | null;
  setMarketData: (symbol: string, data: MarketData) => void;
  setPriceHistory: (symbol: string, history: PriceData[]) => void;
  setAssetInfo: (symbol: string, info: AssetInfo) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useMarketDataStore = create<MarketDataState>((set) => ({
  marketData: {},
  priceHistory: {},
  assetInfo: {},
  isLoading: false,
  error: null,
  setMarketData: (symbol, data) =>
    set((state) => ({
      marketData: { ...state.marketData, [symbol]: data },
    })),
  setPriceHistory: (symbol, history) =>
    set((state) => ({
      priceHistory: { ...state.priceHistory, [symbol]: history },
    })),
  setAssetInfo: (symbol, info) =>
    set((state) => ({
      assetInfo: { ...state.assetInfo, [symbol]: info },
    })),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));

