import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Header } from './Header';

describe('Header', () => {
  it('renders platform title', () => {
    render(<Header />);
    expect(screen.getByText('Investment Platform')).toBeInTheDocument();
  });

  it('renders navigation links', () => {
    render(<Header />);
    expect(screen.getByRole('link', { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /portfolio/i })).toBeInTheDocument();
  });

  it('renders with correct link attributes', () => {
    render(<Header />);
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i });
    expect(dashboardLink).toHaveAttribute('href', '/');
    
    const portfolioLink = screen.getByRole('link', { name: /portfolio/i });
    expect(portfolioLink).toHaveAttribute('href', '/portfolio');
  });
});

