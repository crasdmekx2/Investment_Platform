import { useState, useCallback } from 'react';
import apiClient from '@/lib/api/client';
import type { ApiError, ApiResponse } from '@/types/api';

interface UseApiOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: ApiError) => void;
}

export function useApi<T>() {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const execute = useCallback(
    async (
      apiCall: () => Promise<ApiResponse<T>>,
      options?: UseApiOptions<T>
    ): Promise<T | null> => {
      setLoading(true);
      setError(null);

      try {
        const response = await apiCall();
        setData(response.data);
        options?.onSuccess?.(response.data);
        return response.data;
      } catch (err) {
        const apiError = err as ApiError;
        setError(apiError);
        options?.onError?.(apiError);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    reset,
  };
}

