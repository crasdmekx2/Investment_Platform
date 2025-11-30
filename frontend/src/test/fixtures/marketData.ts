import type { MarketData, PriceData, AssetInfo } from '@/types/market';

// Sample market data matching database schema
export const mockMarketData: MarketData = {
  symbol: 'AAPL',
  price: 175.43,
  change: 2.15,
  changePercent: 1.24,
  volume: 45000000,
  timestamp: '2024-01-15T16:00:00Z',
};

// Sample price history (OHLCV format from database)
export const mockPriceHistory: PriceData[] = [
  {
    timestamp: '2024-01-15T00:00:00Z',
    open: 173.20,
    high: 175.50,
    low: 172.80,
    close: 175.43,
    volume: 45000000,
  },
  {
    timestamp: '2024-01-14T00:00:00Z',
    open: 172.10,
    high: 173.50,
    low: 171.90,
    close: 173.28,
    volume: 42000000,
  },
  {
    timestamp: '2024-01-13T00:00:00Z',
    open: 171.50,
    high: 172.80,
    low: 171.20,
    close: 172.15,
    volume: 38000000,
  },
];

// Sample asset info matching database schema
export const mockAssetInfo: AssetInfo = {
  symbol: 'AAPL',
  name: 'Apple Inc.',
  type: 'stock',
  exchange: 'NASDAQ',
  currency: 'USD',
};

// Multiple assets for testing
export const mockAssets: AssetInfo[] = [
  {
    symbol: 'AAPL',
    name: 'Apple Inc.',
    type: 'stock',
    exchange: 'NASDAQ',
    currency: 'USD',
  },
  {
    symbol: 'MSFT',
    name: 'Microsoft Corporation',
    type: 'stock',
    exchange: 'NASDAQ',
    currency: 'USD',
  },
  {
    symbol: 'BTC-USD',
    name: 'Bitcoin',
    type: 'crypto',
    currency: 'USD',
  },
  {
    symbol: 'USD_EUR',
    name: 'USD/EUR',
    type: 'forex',
    currency: 'EUR',
  },
];

// Market data for multiple symbols
export const mockMarketDataMap: Record<string, MarketData> = {
  AAPL: {
    symbol: 'AAPL',
    price: 175.43,
    change: 2.15,
    changePercent: 1.24,
    volume: 45000000,
    timestamp: '2024-01-15T16:00:00Z',
  },
  MSFT: {
    symbol: 'MSFT',
    price: 378.85,
    change: -1.25,
    changePercent: -0.33,
    volume: 25000000,
    timestamp: '2024-01-15T16:00:00Z',
  },
  'BTC-USD': {
    symbol: 'BTC-USD',
    price: 42500.00,
    change: 1250.00,
    changePercent: 3.03,
    volume: 15000000000,
    timestamp: '2024-01-15T16:00:00Z',
  },
};

