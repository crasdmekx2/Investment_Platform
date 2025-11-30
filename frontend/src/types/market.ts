export type AssetType = 'stock' | 'forex' | 'crypto' | 'bond' | 'commodity' | 'economic';

export interface MarketData {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume?: number;
  timestamp: string;
}

export interface PriceData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface AssetInfo {
  symbol: string;
  name: string;
  type: AssetType;
  exchange?: string;
  currency?: string;
}

