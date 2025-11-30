import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { NotFound } from './NotFound';

describe('NotFound', () => {
  it('renders 404 message', () => {
    render(<NotFound />);
    expect(screen.getByText('404')).toBeInTheDocument();
    expect(screen.getByText('Page Not Found')).toBeInTheDocument();
  });

  it('renders link to dashboard', () => {
    render(<NotFound />);
    const link = screen.getByRole('link', { name: /go to dashboard/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/');
  });
});

