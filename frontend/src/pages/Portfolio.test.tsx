import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Portfolio } from './Portfolio';

describe('Portfolio', () => {
  it('renders portfolio title', () => {
    render(<Portfolio />);
    expect(screen.getByRole('heading', { name: /portfolio/i, level: 1 })).toBeInTheDocument();
  });

  it('renders add holding button', () => {
    render(<Portfolio />);
    expect(screen.getByRole('button', { name: /add holding/i })).toBeInTheDocument();
  });

  it('renders portfolio holdings section', () => {
    render(<Portfolio />);
    expect(screen.getByText('Portfolio Holdings')).toBeInTheDocument();
  });

  it('renders transactions section', () => {
    render(<Portfolio />);
    expect(screen.getByText('Recent Transactions')).toBeInTheDocument();
  });
});

