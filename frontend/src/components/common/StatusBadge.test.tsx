import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { StatusBadge } from './StatusBadge';

describe('StatusBadge', () => {
  it('renders with default label for success status', () => {
    render(<StatusBadge status="success" />);
    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('Success')).toBeInTheDocument();
    expect(screen.getByLabelText(/status: success/i)).toBeInTheDocument();
  });

  it('renders with custom children', () => {
    render(<StatusBadge status="success">Custom Text</StatusBadge>);
    expect(screen.getByText('Custom Text')).toBeInTheDocument();
    expect(screen.queryByText('Success')).not.toBeInTheDocument();
  });

  it('renders all status types correctly', () => {
    const statuses = ['success', 'failed', 'active', 'paused', 'completed', 'pending', 'warning'] as const;
    
    statuses.forEach((status) => {
      const { unmount } = render(<StatusBadge status={status} />);
      expect(screen.getByRole('status')).toBeInTheDocument();
      expect(screen.getByLabelText(new RegExp(`status: ${status}`, 'i'))).toBeInTheDocument();
      unmount();
    });
  });

  it('applies correct classes for success status', () => {
    render(<StatusBadge status="success" />);
    const badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-success-100');
    expect(badge).toHaveClass('text-success-800');
  });

  it('applies correct classes for failed status', () => {
    render(<StatusBadge status="failed" />);
    const badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-danger-100');
    expect(badge).toHaveClass('text-danger-800');
  });

  it('applies correct classes for warning status', () => {
    render(<StatusBadge status="warning" />);
    const badge = screen.getByRole('status');
    expect(badge).toHaveClass('bg-warning-100');
    expect(badge).toHaveClass('text-warning-800');
  });

  it('applies custom className', () => {
    render(<StatusBadge status="success" className="custom-class" />);
    const badge = screen.getByRole('status');
    expect(badge).toHaveClass('custom-class');
  });

  it('renders icon for each status', () => {
    render(<StatusBadge status="success" />);
    const icon = screen.getByRole('status').querySelector('svg');
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveAttribute('aria-hidden', 'true');
  });

  it('has proper accessibility attributes', () => {
    render(<StatusBadge status="active" />);
    const badge = screen.getByRole('status');
    expect(badge).toHaveAttribute('role', 'status');
    expect(badge).toHaveAttribute('aria-label', 'Status: Active');
  });
});

