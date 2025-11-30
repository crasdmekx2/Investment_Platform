import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Card } from './Card';

describe('Card', () => {
  it('renders children', () => {
    render(
      <Card>
        <p>Card content</p>
      </Card>
    );
    expect(screen.getByText('Card content')).toBeInTheDocument();
  });

  it('renders with title', () => {
    render(<Card title="Card Title">Content</Card>);
    expect(screen.getByText('Card Title')).toBeInTheDocument();
  });

  it('renders header actions', () => {
    render(
      <Card title="Card Title" headerActions={<button>Action</button>}>
        Content
      </Card>
    );
    expect(screen.getByText('Card Title')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /action/i })).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<Card className="custom-class">Content</Card>);
    expect(container.firstChild).toHaveClass('custom-class');
  });
});

