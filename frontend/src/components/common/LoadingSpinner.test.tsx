import { describe, it, expect } from 'vitest';
import { render } from '@/test/utils';
import { LoadingSpinner } from './LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders spinner', () => {
    const { container } = render(<LoadingSpinner />);
    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
    expect(svg).toHaveClass('animate-spin');
  });

  it('applies size classes', () => {
    const { rerender, container } = render(<LoadingSpinner size="sm" />);
    let svg = container.querySelector('svg');
    expect(svg).toHaveClass('h-4', 'w-4');

    rerender(<LoadingSpinner size="md" />);
    svg = container.querySelector('svg');
    expect(svg).toHaveClass('h-8', 'w-8');

    rerender(<LoadingSpinner size="lg" />);
    svg = container.querySelector('svg');
    expect(svg).toHaveClass('h-12', 'w-12');
  });

  it('applies custom className', () => {
    const { container } = render(<LoadingSpinner className="custom-class" />);
    expect(container.firstChild).toHaveClass('custom-class');
  });
});

