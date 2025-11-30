import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { ErrorMessage } from './ErrorMessage';

describe('ErrorMessage', () => {
  it('renders error message', () => {
    render(<ErrorMessage message="Something went wrong" />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('renders custom title', () => {
    render(<ErrorMessage title="Custom Error" message="Error details" />);
    expect(screen.getByText('Custom Error')).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', async () => {
    const handleRetry = vi.fn();
    const user = userEvent.setup();
    render(<ErrorMessage message="Error" onRetry={handleRetry} />);

    await user.click(screen.getByText(/retry/i));
    expect(handleRetry).toHaveBeenCalledTimes(1);
  });

  it('renders custom actions', () => {
    render(
      <ErrorMessage
        message="Error"
        actions={<button>Custom Action</button>}
      />
    );
    expect(screen.getByRole('button', { name: /custom action/i })).toBeInTheDocument();
  });

  it('does not show retry button when onRetry is not provided', () => {
    render(<ErrorMessage message="Error" />);
    expect(screen.queryByText(/retry/i)).not.toBeInTheDocument();
  });
});

