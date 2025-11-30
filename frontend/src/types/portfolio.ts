export interface Portfolio {
  id: string;
  name: string;
  totalValue: number;
  totalCost: number;
  totalGain: number;
  totalGainPercent: number;
  holdings: Holding[];
  createdAt: string;
  updatedAt: string;
}

export interface Holding {
  id: string;
  symbol: string;
  assetType: string;
  quantity: number;
  averageCost: number;
  currentPrice: number;
  totalCost: number;
  currentValue: number;
  gain: number;
  gainPercent: number;
}

export interface Transaction {
  id: string;
  portfolioId: string;
  symbol: string;
  assetType: string;
  type: 'buy' | 'sell';
  quantity: number;
  price: number;
  total: number;
  timestamp: string;
}

