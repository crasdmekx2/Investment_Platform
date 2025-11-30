import { useEffect } from 'react';
import { useSchedulerStore } from '@/store/slices/schedulerSlice';

/**
 * Hook for scheduler operations
 */
export function useScheduler() {
  const store = useSchedulerStore();
  
  useEffect(() => {
    // Fetch jobs on mount
    store.fetchJobs();
  }, [store.filters.status, store.filters.asset_type]);
  
  return store;
}

