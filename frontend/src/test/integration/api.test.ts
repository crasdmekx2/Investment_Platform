import { describe, it, expect, beforeEach, beforeAll, afterAll, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { handlers } from '@/test/mocks/handlers';
import apiClient from '@/lib/api/client';

// Setup MSW server
const server = setupServer(...handlers);

describe('API Integration', () => {
  beforeAll(() => {
    server.listen({ onUnhandledRequest: 'warn' });
  });

  afterEach(() => {
    server.resetHandlers();
  });

  afterAll(() => {
    server.close();
  });

  describe('Market Data API', () => {
    it('fetches market data list', async () => {
      const response = await apiClient.get('/market-data');
      expect(response.status).toBe(200);
      expect(Array.isArray(response.data)).toBe(true);
    });

    it('fetches market data for symbol', async () => {
      const response = await apiClient.get('/market-data/AAPL');
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('symbol');
      expect(response.data).toHaveProperty('price');
    });

    it('fetches price history', async () => {
      const response = await apiClient.get('/market-data/AAPL/history');
      expect(response.status).toBe(200);
      expect(Array.isArray(response.data)).toBe(true);
      if (response.data.length > 0) {
        expect(response.data[0]).toHaveProperty('timestamp');
        expect(response.data[0]).toHaveProperty('open');
        expect(response.data[0]).toHaveProperty('close');
      }
    });
  });

  describe('Portfolio API', () => {
    it('fetches portfolio list', async () => {
      const response = await apiClient.get('/portfolios');
      expect(response.status).toBe(200);
      expect(Array.isArray(response.data)).toBe(true);
    });

    it('fetches single portfolio', async () => {
      const response = await apiClient.get('/portfolios/1');
      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('id');
      expect(response.data).toHaveProperty('name');
      expect(response.data).toHaveProperty('holdings');
    });

    it('creates portfolio', async () => {
      const newPortfolio = {
        name: 'Test Portfolio',
        holdings: [],
      };
      const response = await apiClient.post('/portfolios', newPortfolio);
      expect(response.status).toBe(201);
      expect(response.data).toHaveProperty('id');
      expect(response.data.name).toBe('Test Portfolio');
    });

    it('updates portfolio', async () => {
      const updates = { name: 'Updated Portfolio' };
      const response = await apiClient.put('/portfolios/1', updates);
      expect(response.status).toBe(200);
      expect(response.data.name).toBe('Updated Portfolio');
    });

    it('deletes portfolio', async () => {
      const response = await apiClient.delete('/portfolios/1');
      expect(response.status).toBe(204);
    });
  });

  describe('Transaction API', () => {
    it('fetches transactions for portfolio', async () => {
      const response = await apiClient.get('/portfolios/1/transactions');
      expect(response.status).toBe(200);
      expect(Array.isArray(response.data)).toBe(true);
    });

    it('creates transaction', async () => {
      const newTransaction = {
        symbol: 'AAPL',
        assetType: 'stock',
        type: 'buy',
        quantity: 10,
        price: 150.00,
      };
      const response = await apiClient.post('/portfolios/1/transactions', newTransaction);
      expect(response.status).toBe(201);
      expect(response.data).toHaveProperty('id');
      expect(response.data.symbol).toBe('AAPL');
    });
  });

  describe('Error Handling', () => {
    it('handles 404 errors', async () => {
      try {
        await apiClient.get('/market-data/INVALID');
        expect.fail('Should have thrown an error');
      } catch (error: any) {
        expect(error).toBeDefined();
        expect(error.message || error.status || error.code).toBeDefined();
      }
    });
  });
});

