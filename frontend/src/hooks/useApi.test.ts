import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useApi } from './useApi';
import apiClient from '@/lib/api/client';
import type { ApiResponse } from '@/types/api';
import { mockApiResponses } from '@/test/mocks/api';

// Mock the API client
vi.mock('@/lib/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('useApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with null data and no loading/error', () => {
    const { result } = renderHook(() => useApi<string>());
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('sets loading to true during API call', async () => {
    const mockResponse: ApiResponse<string> = {
      data: 'test data',
      status: 200,
    };

    // Create a promise that we can control
    let resolvePromise: (value: ApiResponse<string>) => void;
    const controlledPromise = new Promise<ApiResponse<string>>((resolve) => {
      resolvePromise = resolve;
    });

    vi.mocked(apiClient.get).mockReturnValue(controlledPromise);

    const { result } = renderHook(() => useApi<string>());

    // Start the API call
    const promise = result.current.execute(() => apiClient.get('/test'));

    // Give React a chance to update state
    await new Promise((resolve) => setTimeout(resolve, 0));

    // Verify loading is true
    expect(result.current.loading).toBe(true);

    // Resolve the promise
    resolvePromise!(mockResponse);

    // Wait for API call to complete
    await promise;

    // Verify loading becomes false
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it('handles successful API call', async () => {
    const mockResponse: ApiResponse<string> = {
      data: 'success',
      status: 200,
    };

    vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useApi<string>());

    await result.current.execute(() => apiClient.get('/test'));

    await waitFor(() => {
      expect(result.current.data).toBe('success');
      expect(result.current.error).toBeNull();
      expect(result.current.loading).toBe(false);
    });
  });

  it('handles API error', async () => {
    const mockError = {
      message: 'API Error',
      code: 'ERROR',
      status: 500,
    };

    vi.mocked(apiClient.get).mockRejectedValue(mockError);

    const { result } = renderHook(() => useApi<string>());

    await result.current.execute(() => apiClient.get('/test'));

    await waitFor(() => {
      expect(result.current.error).toEqual(mockError);
      expect(result.current.data).toBeNull();
      expect(result.current.loading).toBe(false);
    });
  });

  it('calls onSuccess callback on success', async () => {
    const mockResponse: ApiResponse<string> = {
      data: 'success',
      status: 200,
    };
    const onSuccess = vi.fn();

    vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useApi<string>());

    await result.current.execute(() => apiClient.get('/test'), { onSuccess });

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith('success');
    });
  });

  it('calls onError callback on error', async () => {
    const mockError = {
      message: 'API Error',
      code: 'ERROR',
      status: 500,
    };
    const onError = vi.fn();

    vi.mocked(apiClient.get).mockRejectedValue(mockError);

    const { result } = renderHook(() => useApi<string>());

    await result.current.execute(() => apiClient.get('/test'), { onError });

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(mockError);
    });
  });

  it('resets state when reset is called', async () => {
    const mockResponse: ApiResponse<string> = {
      data: 'test',
      status: 200,
    };

    vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useApi<string>());

    await result.current.execute(() => apiClient.get('/test'));
    await waitFor(() => {
      expect(result.current.data).toBe('test');
    });

    result.current.reset();

    await waitFor(() => {
      expect(result.current.data).toBeNull();
      expect(result.current.error).toBeNull();
      expect(result.current.loading).toBe(false);
    });
  });
});

