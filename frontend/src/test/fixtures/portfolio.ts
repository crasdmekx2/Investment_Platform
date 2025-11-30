import type { Portfolio, Holding, Transaction } from '@/types/portfolio';

// Sample portfolio data matching database structure
export const mockPortfolio: Portfolio = {
  id: '1',
  name: 'Main Portfolio',
  totalValue: 125000.50,
  totalCost: 100000.00,
  totalGain: 25000.50,
  totalGainPercent: 25.0,
  holdings: [
    {
      id: '1',
      symbol: 'AAPL',
      assetType: 'stock',
      quantity: 100,
      averageCost: 150.00,
      currentPrice: 175.43,
      totalCost: 15000.00,
      currentValue: 17543.00,
      gain: 2543.00,
      gainPercent: 16.95,
    },
    {
      id: '2',
      symbol: 'MSFT',
      assetType: 'stock',
      quantity: 50,
      averageCost: 300.00,
      currentPrice: 378.85,
      totalCost: 15000.00,
      currentValue: 18942.50,
      gain: 3942.50,
      gainPercent: 26.28,
    },
    {
      id: '3',
      symbol: 'BTC-USD',
      assetType: 'crypto',
      quantity: 2,
      averageCost: 40000.00,
      currentPrice: 42500.00,
      totalCost: 80000.00,
      currentValue: 85000.00,
      gain: 5000.00,
      gainPercent: 6.25,
    },
  ],
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-15T16:00:00Z',
};

// Sample transaction
export const mockTransaction: Transaction = {
  id: '1',
  portfolioId: '1',
  symbol: 'AAPL',
  assetType: 'stock',
  type: 'buy',
  quantity: 100,
  price: 150.00,
  total: 15000.00,
  timestamp: '2024-01-01T10:00:00Z',
};

// Multiple portfolios
export const mockPortfolios: Portfolio[] = [
  mockPortfolio,
  {
    id: '2',
    name: 'Retirement Portfolio',
    totalValue: 500000.00,
    totalCost: 450000.00,
    totalGain: 50000.00,
    totalGainPercent: 11.11,
    holdings: [],
    createdAt: '2023-06-01T00:00:00Z',
    updatedAt: '2024-01-15T16:00:00Z',
  },
];

