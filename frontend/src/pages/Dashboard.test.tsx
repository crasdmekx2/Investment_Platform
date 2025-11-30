import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Dashboard } from './Dashboard';

describe('Dashboard', () => {
  it('renders dashboard title', () => {
    render(<Dashboard />);
    expect(screen.getByRole('heading', { name: /dashboard/i, level: 1 })).toBeInTheDocument();
  });

  it('renders portfolio summary cards', () => {
    render(<Dashboard />);
    expect(screen.getByText('Total Portfolio Value')).toBeInTheDocument();
    expect(screen.getByText('Total Gain/Loss')).toBeInTheDocument();
    expect(screen.getByText('Total Gain/Loss %')).toBeInTheDocument();
    expect(screen.getByText('Number of Holdings')).toBeInTheDocument();
  });

  it('renders market overview section', () => {
    render(<Dashboard />);
    expect(screen.getByText('Market Overview')).toBeInTheDocument();
  });
});

