import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import { Sidebar } from './Sidebar';
import * as reactRouterDom from 'react-router-dom';

// Mock useLocation
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useLocation: vi.fn(),
  };
});

describe('Sidebar', () => {
  beforeEach(() => {
    vi.mocked(reactRouterDom.useLocation).mockReturnValue({
      pathname: '/',
      search: '',
      hash: '',
      state: null,
      key: 'default',
    });
  });

  it('renders sidebar with navigation title', () => {
    render(<Sidebar />);

    expect(screen.getByText('Navigation')).toBeInTheDocument();
  });

  it('displays all navigation items', () => {
    render(<Sidebar />);

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Portfolio')).toBeInTheDocument();
    expect(screen.getByText('Scheduler')).toBeInTheDocument();
  });

  it('highlights active route', () => {
    vi.mocked(reactRouterDom.useLocation).mockReturnValue({
      pathname: '/scheduler',
      search: '',
      hash: '',
      state: null,
      key: 'default',
    });

    render(<Sidebar />);

    const schedulerLink = screen.getByText('Scheduler').closest('a');
    expect(schedulerLink).toHaveClass('bg-primary-100', 'text-primary-700');
  });

  it('renders links with correct paths', () => {
    render(<Sidebar />);

    const dashboardLink = screen.getByText('Dashboard').closest('a');
    const portfolioLink = screen.getByText('Portfolio').closest('a');
    const schedulerLink = screen.getByText('Scheduler').closest('a');

    expect(dashboardLink).toHaveAttribute('href', '/');
    expect(portfolioLink).toHaveAttribute('href', '/portfolio');
    expect(schedulerLink).toHaveAttribute('href', '/scheduler');
  });

  it('has accessible navigation structure', () => {
    render(<Sidebar />);

    const nav = screen.getByRole('navigation', { hidden: true });
    expect(nav).toBeInTheDocument();
  });
});

