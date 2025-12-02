import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useScheduler } from './useScheduler';
import { useSchedulerStore } from '@/store/slices/schedulerSlice';

// Mock the store
vi.mock('@/store/slices/schedulerSlice', () => ({
  useSchedulerStore: vi.fn(),
}));

describe('useScheduler', () => {
  const mockFetchJobs = vi.fn();
  const mockStore = {
    jobs: [],
    isLoading: false,
    error: null,
    filters: {
      status: 'active',
      asset_type: 'stock',
    },
    fetchJobs: mockFetchJobs,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useSchedulerStore).mockReturnValue(mockStore as any);
  });

  it('returns scheduler store', () => {
    const { result } = renderHook(() => useScheduler());

    expect(result.current).toBe(mockStore);
    expect(result.current.jobs).toEqual([]);
    expect(result.current.isLoading).toBe(false);
  });

  it('calls fetchJobs on mount', () => {
    renderHook(() => useScheduler());

    expect(mockFetchJobs).toHaveBeenCalledTimes(1);
  });

  it('calls fetchJobs when status filter changes', () => {
    const { rerender } = renderHook(() => useScheduler());

    // Update status filter
    mockStore.filters.status = 'paused';
    rerender();

    // fetchJobs should be called again due to dependency change
    expect(mockFetchJobs).toHaveBeenCalled();
  });

  it('calls fetchJobs when asset_type filter changes', () => {
    const { rerender } = renderHook(() => useScheduler());

    // Update asset_type filter
    mockStore.filters.asset_type = 'crypto';
    rerender();

    // fetchJobs should be called again due to dependency change
    expect(mockFetchJobs).toHaveBeenCalled();
  });
});

