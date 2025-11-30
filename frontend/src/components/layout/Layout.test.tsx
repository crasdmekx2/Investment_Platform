import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Layout } from './Layout';

describe('Layout', () => {
  it('renders children', () => {
    render(
      <Layout>
        <div>Test Content</div>
      </Layout>
    );
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('renders Header', () => {
    render(<Layout>Content</Layout>);
    expect(screen.getByText('Investment Platform')).toBeInTheDocument();
  });

  it('shows sidebar when showSidebar is true', () => {
    render(
      <Layout showSidebar>
        <div>Content</div>
      </Layout>
    );
    expect(screen.getByText('Navigation')).toBeInTheDocument();
  });

  it('does not show sidebar when showSidebar is false', () => {
    render(
      <Layout showSidebar={false}>
        <div>Content</div>
      </Layout>
    );
    expect(screen.queryByText('Navigation')).not.toBeInTheDocument();
  });
});

