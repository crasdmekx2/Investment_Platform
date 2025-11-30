import { create } from 'zustand';
import type { JobExecution, CollectionLog, CollectRequest, CollectResponse } from '@/types/scheduler';
import { ingestionApi, schedulerApi } from '@/lib/api/scheduler';
import type { ApiError } from '@/types/api';

interface CollectionState {
  activeJobs: Record<string, CollectResponse & { started_at: string }>;
  executions: Record<string, JobExecution[]>;
  logs: CollectionLog[];
  isLoading: boolean;
  error: string | null;
  
  // Actions
  collectData: (request: CollectRequest) => Promise<CollectResponse | null>;
  getCollectionStatus: (jobId: string) => Promise<void>;
  fetchJobExecutions: (jobId: string) => Promise<void>;
  fetchCollectionLogs: (filters?: {
    asset_id?: number;
    status?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }) => Promise<void>;
  updateActiveJob: (jobId: string, updates: Partial<CollectResponse>) => void;
  removeActiveJob: (jobId: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useCollectionStore = create<CollectionState>((set) => ({
  activeJobs: {},
  executions: {},
  logs: [],
  isLoading: false,
  error: null,

  collectData: async (request) => {
    set({ isLoading: true, error: null });
    try {
      const response = await ingestionApi.collect(request);
      const collectResponse = response.data;
      set((state) => ({
        activeJobs: {
          ...state.activeJobs,
          [collectResponse.job_id]: {
            ...collectResponse,
            started_at: new Date().toISOString(),
          },
        },
        isLoading: false,
      }));
      return collectResponse;
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || 'Failed to start collection', isLoading: false });
      return null;
    }
  },

  getCollectionStatus: async (jobId: string) => {
    try {
      const response = await ingestionApi.getStatus(jobId);
      const status = response.data;
      
      set((state) => {
        const activeJob = state.activeJobs[jobId];
        if (activeJob) {
          return {
            activeJobs: {
              ...state.activeJobs,
              [jobId]: {
                ...activeJob,
                status: status.status as string,
                records_loaded: status.records_loaded as number | undefined,
              },
            },
          };
        }
        return state;
      });
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || 'Failed to get collection status' });
    }
  },

  fetchJobExecutions: async (jobId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await schedulerApi.getJobExecutions(jobId);
      set((state) => ({
        executions: {
          ...state.executions,
          [jobId]: response.data,
        },
        isLoading: false,
      }));
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || 'Failed to fetch executions', isLoading: false });
    }
  },

  fetchCollectionLogs: async (filters) => {
    set({ isLoading: true, error: null });
    try {
      const response = await ingestionApi.getLogs(filters);
      set({ logs: response.data, isLoading: false });
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || 'Failed to fetch collection logs', isLoading: false });
    }
  },

  updateActiveJob: (jobId, updates) => {
    set((state) => {
      const activeJob = state.activeJobs[jobId];
      if (activeJob) {
        return {
          activeJobs: {
            ...state.activeJobs,
            [jobId]: {
              ...activeJob,
              ...updates,
            },
          },
        };
      }
      return state;
    });
  },

  removeActiveJob: (jobId) => {
    set((state) => {
      const { [jobId]: removed, ...rest } = state.activeJobs;
      return { activeJobs: rest };
    });
  },

  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));

