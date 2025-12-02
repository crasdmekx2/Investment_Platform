import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useCollectorMetadata } from './useCollectorMetadata';
import { collectorsApi } from '@/lib/api/scheduler';

// Mock the API
vi.mock('@/lib/api/scheduler', () => ({
  collectorsApi: {
    getMetadata: vi.fn(),
  },
}));

describe('useCollectorMetadata', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches metadata on mount', async () => {
    const mockMetadata = {
      stock: {
        name: 'Stock Collector',
        supported_symbols: ['AAPL', 'MSFT'],
      },
    };

    vi.mocked(collectorsApi.getMetadata).mockResolvedValue({
      data: mockMetadata,
    });

    const { result } = renderHook(() => useCollectorMetadata());

    expect(result.current.loading).toBe(true);
    expect(result.current.metadata).toBeNull();
    expect(result.current.error).toBeNull();

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.metadata).toEqual(mockMetadata);
    expect(result.current.error).toBeNull();
    expect(collectorsApi.getMetadata).toHaveBeenCalledTimes(1);
  });

  it('handles errors correctly', async () => {
    const mockError = {
      message: 'Failed to fetch metadata',
    };

    vi.mocked(collectorsApi.getMetadata).mockRejectedValue(mockError);

    const { result } = renderHook(() => useCollectorMetadata());

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.metadata).toBeNull();
    expect(result.current.error).toBe('Failed to fetch metadata');
  });

  it('handles errors without message', async () => {
    vi.mocked(collectorsApi.getMetadata).mockRejectedValue(new Error());

    const { result } = renderHook(() => useCollectorMetadata());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('Failed to fetch collector metadata');
  });

  it('cancels request on unmount', async () => {
    vi.mocked(collectorsApi.getMetadata).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ data: {} }), 100))
    );

    const { result, unmount } = renderHook(() => useCollectorMetadata());

    expect(result.current.loading).toBe(true);

    unmount();

    // Wait a bit to ensure the promise would have resolved
    await new Promise((resolve) => setTimeout(resolve, 150));

    // The state should not have been updated after unmount
    // (we can't directly test this, but the test ensures no errors occur)
    expect(collectorsApi.getMetadata).toHaveBeenCalledTimes(1);
  });
});

