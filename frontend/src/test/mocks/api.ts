import type { ApiResponse, PaginatedResponse } from '@/types/api';
import type { MarketData, AssetInfo, PriceData } from '@/types/market';
import type { Portfolio, Holding, Transaction } from '@/types/portfolio';
import { mockMarketData, mockPriceHistory, mockAssetInfo, mockAssets, mockMarketDataMap } from '../fixtures/marketData';
import { mockPortfolio, mockPortfolios, mockTransaction } from '../fixtures/portfolio';

// Mock API responses
export const mockApiResponses = {
  // Market data endpoints
  getMarketData: (symbol: string): ApiResponse<MarketData> => ({
    data: mockMarketDataMap[symbol] || mockMarketData,
    status: 200,
  }),

  getPriceHistory: (symbol: string): ApiResponse<PriceData[]> => ({
    data: mockPriceHistory,
    status: 200,
  }),

  getAssetInfo: (symbol: string): ApiResponse<AssetInfo> => ({
    data: mockAssetInfo,
    status: 200,
  }),

  listAssets: (): ApiResponse<AssetInfo[]> => ({
    data: mockAssets,
    status: 200,
  }),

  // Portfolio endpoints
  listPortfolios: (): ApiResponse<Portfolio[]> => ({
    data: mockPortfolios,
    status: 200,
  }),

  getPortfolio: (id: string): ApiResponse<Portfolio> => ({
    data: mockPortfolio,
    status: 200,
  }),

  createPortfolio: (portfolio: Partial<Portfolio>): ApiResponse<Portfolio> => ({
    data: { ...mockPortfolio, ...portfolio, id: '3' },
    status: 201,
  }),

  updatePortfolio: (id: string, updates: Partial<Portfolio>): ApiResponse<Portfolio> => ({
    data: { ...mockPortfolio, ...updates },
    status: 200,
  }),

  deletePortfolio: (): ApiResponse<void> => ({
    data: undefined as unknown as void,
    status: 204,
  }),

  // Transaction endpoints
  listTransactions: (portfolioId: string): ApiResponse<Transaction[]> => ({
    data: [mockTransaction],
    status: 200,
  }),

  createTransaction: (portfolioId: string, transaction: Partial<Transaction>): ApiResponse<Transaction> => ({
    data: { ...mockTransaction, ...transaction, id: '2' },
    status: 201,
  }),
};

// Mock API errors
export const mockApiErrors = {
  notFound: {
    message: 'Resource not found',
    code: 'NOT_FOUND',
    status: 404,
  },
  serverError: {
    message: 'Internal server error',
    code: 'SERVER_ERROR',
    status: 500,
  },
  badRequest: {
    message: 'Invalid request',
    code: 'BAD_REQUEST',
    status: 400,
  },
  unauthorized: {
    message: 'Unauthorized',
    code: 'UNAUTHORIZED',
    status: 401,
  },
};

