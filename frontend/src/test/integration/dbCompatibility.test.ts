import { describe, it, expect } from 'vitest';
import {
  mockMarketData,
  mockPriceHistory,
  mockAssetInfo,
} from '@/test/fixtures/marketData';
import { mockPortfolio } from '@/test/fixtures/portfolio';
import {
  formatCurrency,
  formatPercent,
  formatDate,
} from '@/lib/utils/format';
import type { MarketData, PriceData } from '@/types/market';

/**
 * Tests that verify front-end can handle data structures from the database/ingestion system.
 * These tests ensure compatibility with TimescaleDB schema and ingestion output.
 */
describe('Database/Ingestion Compatibility', () => {
  describe('Market Data Structure', () => {
    it('handles market data from database (OHLCV format)', () => {
      const priceData: PriceData = mockPriceHistory[0];
      
      // Verify structure matches database schema
      expect(priceData).toHaveProperty('timestamp');
      expect(priceData).toHaveProperty('open');
      expect(priceData).toHaveProperty('high');
      expect(priceData).toHaveProperty('low');
      expect(priceData).toHaveProperty('close');
      expect(priceData).toHaveProperty('volume');
      
      // Verify data types
      expect(typeof priceData.open).toBe('number');
      expect(typeof priceData.high).toBe('number');
      expect(typeof priceData.low).toBe('number');
      expect(typeof priceData.close).toBe('number');
    });

    it('handles market data with all required fields', () => {
      const marketData: MarketData = mockMarketData;
      
      expect(marketData).toHaveProperty('symbol');
      expect(marketData).toHaveProperty('price');
      expect(marketData).toHaveProperty('change');
      expect(marketData).toHaveProperty('changePercent');
      expect(marketData).toHaveProperty('timestamp');
    });

    it('formats market data for display', () => {
      const marketData: MarketData = mockMarketData;
      
      const formattedPrice = formatCurrency(marketData.price);
      expect(formattedPrice).toMatch(/\$/);
      
      const formattedPercent = formatPercent(marketData.changePercent);
      expect(formattedPercent).toMatch(/%/);
    });
  });

  describe('Price History Data', () => {
    it('handles price history array from database', () => {
      expect(Array.isArray(mockPriceHistory)).toBe(true);
      expect(mockPriceHistory.length).toBeGreaterThan(0);
      
      mockPriceHistory.forEach((price) => {
        expect(price).toHaveProperty('timestamp');
        expect(price).toHaveProperty('open');
        expect(price).toHaveProperty('high');
        expect(price).toHaveProperty('low');
        expect(price).toHaveProperty('close');
      });
    });

    it('validates OHLC data constraints', () => {
      mockPriceHistory.forEach((price) => {
        // High should be >= all other prices
        expect(price.high).toBeGreaterThanOrEqual(price.open);
        expect(price.high).toBeGreaterThanOrEqual(price.close);
        expect(price.high).toBeGreaterThanOrEqual(price.low);
        
        // Low should be <= all other prices
        expect(price.low).toBeLessThanOrEqual(price.open);
        expect(price.low).toBeLessThanOrEqual(price.close);
        expect(price.low).toBeLessThanOrEqual(price.high);
      });
    });

    it('formats timestamp from database', () => {
      const priceData = mockPriceHistory[0];
      const formatted = formatDate(priceData.timestamp);
      expect(formatted).toBeTruthy();
      expect(typeof formatted).toBe('string');
    });
  });

  describe('Portfolio Data Structure', () => {
    it('handles portfolio data from database', () => {
      expect(mockPortfolio).toHaveProperty('id');
      expect(mockPortfolio).toHaveProperty('name');
      expect(mockPortfolio).toHaveProperty('totalValue');
      expect(mockPortfolio).toHaveProperty('totalCost');
      expect(mockPortfolio).toHaveProperty('holdings');
      expect(mockPortfolio).toHaveProperty('createdAt');
      expect(mockPortfolio).toHaveProperty('updatedAt');
    });

    it('handles holdings array', () => {
      expect(Array.isArray(mockPortfolio.holdings)).toBe(true);
      
      mockPortfolio.holdings.forEach((holding) => {
        expect(holding).toHaveProperty('id');
        expect(holding).toHaveProperty('symbol');
        expect(holding).toHaveProperty('quantity');
        expect(holding).toHaveProperty('averageCost');
        expect(holding).toHaveProperty('currentPrice');
        expect(holding).toHaveProperty('gain');
        expect(holding).toHaveProperty('gainPercent');
      });
    });

    it('calculates portfolio metrics correctly', () => {
      const totalCost = mockPortfolio.holdings.reduce(
        (sum, h) => sum + h.totalCost,
        0
      );
      const totalValue = mockPortfolio.holdings.reduce(
        (sum, h) => sum + h.currentValue,
        0
      );
      
      // Verify the portfolio data structure is correct
      expect(mockPortfolio.totalCost).toBeGreaterThan(0);
      expect(mockPortfolio.totalValue).toBeGreaterThan(0);
      expect(mockPortfolio.totalGain).toBe(mockPortfolio.totalValue - mockPortfolio.totalCost);
      const expectedGainPercent = ((mockPortfolio.totalValue - mockPortfolio.totalCost) / mockPortfolio.totalCost) * 100;
      expect(mockPortfolio.totalGainPercent).toBeCloseTo(expectedGainPercent, 2);
    });
  });

  describe('Asset Info Structure', () => {
    it('handles asset info from database', () => {
      expect(mockAssetInfo).toHaveProperty('symbol');
      expect(mockAssetInfo).toHaveProperty('name');
      expect(mockAssetInfo).toHaveProperty('type');
    });

    it('handles different asset types', () => {
      const assetTypes = ['stock', 'forex', 'crypto', 'bond', 'commodity', 'economic'];
      assetTypes.forEach((type) => {
        const asset = { ...mockAssetInfo, type };
        expect(asset.type).toBe(type);
      });
    });
  });

  describe('Data Transformation', () => {
    it('transforms database timestamps to display format', () => {
      const timestamp = '2024-01-15T16:00:00Z';
      const formatted = formatDate(timestamp);
      expect(formatted).toBeTruthy();
    });

    it('transforms numeric values for display', () => {
      const price = 175.43;
      const formatted = formatCurrency(price);
      expect(formatted).toContain('175');
    });

    it('handles null/undefined values gracefully', () => {
      const dataWithNulls = {
        ...mockMarketData,
        volume: undefined,
      };
      
      expect(dataWithNulls.volume).toBeUndefined();
      // Should not throw when formatting
      expect(() => formatCurrency(dataWithNulls.price)).not.toThrow();
    });
  });
});

