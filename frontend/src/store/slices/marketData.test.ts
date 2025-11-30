import { describe, it, expect, beforeEach } from 'vitest';
import { useMarketDataStore } from './marketData';
import { mockMarketData, mockPriceHistory, mockAssetInfo } from '@/test/fixtures/marketData';
import type { MarketData, PriceData, AssetInfo } from '@/types/market';

describe('MarketDataStore', () => {
  beforeEach(() => {
    // Reset store state
    useMarketDataStore.setState({
      marketData: {},
      priceHistory: {},
      assetInfo: {},
      isLoading: false,
      error: null,
    });
  });

  it('initializes with empty state', () => {
    const state = useMarketDataStore.getState();
    expect(state.marketData).toEqual({});
    expect(state.priceHistory).toEqual({});
    expect(state.assetInfo).toEqual({});
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('sets market data', () => {
    useMarketDataStore.getState().setMarketData('AAPL', mockMarketData);

    const state = useMarketDataStore.getState();
    expect(state.marketData['AAPL']).toEqual(mockMarketData);
  });

  it('updates existing market data', () => {
    useMarketDataStore.getState().setMarketData('AAPL', mockMarketData);
    
    const updatedData: MarketData = { ...mockMarketData, price: 200.00 };
    useMarketDataStore.getState().setMarketData('AAPL', updatedData);

    const state = useMarketDataStore.getState();
    expect(state.marketData['AAPL'].price).toBe(200.00);
  });

  it('sets price history', () => {
    useMarketDataStore.getState().setPriceHistory('AAPL', mockPriceHistory);

    const state = useMarketDataStore.getState();
    expect(state.priceHistory['AAPL']).toEqual(mockPriceHistory);
  });

  it('sets asset info', () => {
    useMarketDataStore.getState().setAssetInfo('AAPL', mockAssetInfo);

    const state = useMarketDataStore.getState();
    expect(state.assetInfo['AAPL']).toEqual(mockAssetInfo);
  });

  it('sets loading state', () => {
    useMarketDataStore.getState().setLoading(true);
    expect(useMarketDataStore.getState().isLoading).toBe(true);

    useMarketDataStore.getState().setLoading(false);
    expect(useMarketDataStore.getState().isLoading).toBe(false);
  });

  it('sets error state', () => {
    const errorMessage = 'Failed to fetch data';
    useMarketDataStore.getState().setError(errorMessage);
    expect(useMarketDataStore.getState().error).toBe(errorMessage);
  });

  it('clears error', () => {
    useMarketDataStore.getState().setError('Error message');
    useMarketDataStore.getState().clearError();
    expect(useMarketDataStore.getState().error).toBeNull();
  });

  it('handles multiple symbols', () => {
    const aaplData: MarketData = { ...mockMarketData, symbol: 'AAPL' };
    const msftData: MarketData = { ...mockMarketData, symbol: 'MSFT', price: 300.00 };

    useMarketDataStore.getState().setMarketData('AAPL', aaplData);
    useMarketDataStore.getState().setMarketData('MSFT', msftData);

    const state = useMarketDataStore.getState();
    expect(state.marketData['AAPL']).toEqual(aaplData);
    expect(state.marketData['MSFT']).toEqual(msftData);
  });
});

