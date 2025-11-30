import { useState, useEffect } from 'react';
import { collectorsApi } from '@/lib/api/scheduler';
import type { CollectorMetadata } from '@/types/scheduler';
import type { ApiError } from '@/types/api';

/**
 * Hook for fetching and caching collector metadata
 */
export function useCollectorMetadata() {
  const [metadata, setMetadata] = useState<CollectorMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    let cancelled = false;
    
    async function fetchMetadata() {
      try {
        const response = await collectorsApi.getMetadata();
        if (!cancelled) {
          setMetadata(response.data);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          const apiError = err as ApiError;
          setError(apiError.message || 'Failed to fetch collector metadata');
          setLoading(false);
        }
      }
    }
    
    fetchMetadata();
    
    return () => {
      cancelled = true;
    };
  }, []);
  
  return { metadata, loading, error };
}

