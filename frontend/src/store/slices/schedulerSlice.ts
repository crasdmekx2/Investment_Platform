import { create } from 'zustand';
import type { ScheduledJob, JobStatus, AssetType } from '@/types/scheduler';
import { schedulerApi } from '@/lib/api/scheduler';
import type { ApiError } from '@/types/api';

interface SchedulerState {
  jobs: ScheduledJob[];
  selectedJob: ScheduledJob | null;
  isLoading: boolean;
  error: string | null;
  filters: {
    status?: JobStatus;
    asset_type?: AssetType;
  };
  
  // Actions
  fetchJobs: () => Promise<void>;
  fetchJob: (jobId: string) => Promise<void>;
  createJob: (job: Omit<ScheduledJob, 'job_id' | 'created_at' | 'updated_at' | 'status'>) => Promise<ScheduledJob | null>;
  updateJob: (jobId: string, updates: Partial<ScheduledJob>) => Promise<void>;
  deleteJob: (jobId: string) => Promise<void>;
  pauseJob: (jobId: string) => Promise<void>;
  resumeJob: (jobId: string) => Promise<void>;
  triggerJob: (jobId: string) => Promise<void>;
  setSelectedJob: (job: ScheduledJob | null) => void;
  setFilters: (filters: { status?: JobStatus; asset_type?: AssetType }) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useSchedulerStore = create<SchedulerState>((set, get) => ({
  jobs: [],
  selectedJob: null,
  isLoading: false,
  error: null,
  filters: {},

  fetchJobs: async () => {
    set({ isLoading: true, error: null });
    try {
      const { filters } = get();
      const response = await schedulerApi.listJobs({
        status: filters.status,
        asset_type: filters.asset_type,
      });
      set({ jobs: response.data, isLoading: false });
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || 'Failed to fetch jobs', isLoading: false });
    }
  },

  fetchJob: async (jobId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await schedulerApi.getJob(jobId);
      set({ selectedJob: response.data, isLoading: false });
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || 'Failed to fetch job', isLoading: false });
    }
  },

  createJob: async (job) => {
    set({ isLoading: true, error: null });
    try {
      const response = await schedulerApi.createJob(job as any);
      const newJob = response.data;
      set((state) => ({
        jobs: [newJob, ...state.jobs],
        isLoading: false,
      }));
      return newJob;
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || 'Failed to create job', isLoading: false });
      return null;
    }
  },

  updateJob: async (jobId: string, updates) => {
    set({ isLoading: true, error: null });
    try {
      const response = await schedulerApi.updateJob(jobId, updates as any);
      const updatedJob = response.data;
      set((state) => ({
        jobs: state.jobs.map((j) => (j.job_id === jobId ? updatedJob : j)),
        selectedJob: state.selectedJob?.job_id === jobId ? updatedJob : state.selectedJob,
        isLoading: false,
      }));
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || 'Failed to update job', isLoading: false });
    }
  },

  deleteJob: async (jobId: string) => {
    set({ isLoading: true, error: null });
    try {
      await schedulerApi.deleteJob(jobId);
      set((state) => ({
        jobs: state.jobs.filter((j) => j.job_id !== jobId),
        selectedJob: state.selectedJob?.job_id === jobId ? null : state.selectedJob,
        isLoading: false,
      }));
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || 'Failed to delete job', isLoading: false });
    }
  },

  pauseJob: async (jobId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await schedulerApi.pauseJob(jobId);
      const updatedJob = response.data;
      set((state) => ({
        jobs: state.jobs.map((j) => (j.job_id === jobId ? updatedJob : j)),
        selectedJob: state.selectedJob?.job_id === jobId ? updatedJob : state.selectedJob,
        isLoading: false,
      }));
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || 'Failed to pause job', isLoading: false });
    }
  },

  resumeJob: async (jobId: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await schedulerApi.resumeJob(jobId);
      const updatedJob = response.data;
      set((state) => ({
        jobs: state.jobs.map((j) => (j.job_id === jobId ? updatedJob : j)),
        selectedJob: state.selectedJob?.job_id === jobId ? updatedJob : state.selectedJob,
        isLoading: false,
      }));
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || 'Failed to resume job', isLoading: false });
    }
  },

  triggerJob: async (jobId: string) => {
    set({ isLoading: true, error: null });
    try {
      await schedulerApi.triggerJob(jobId);
      set({ isLoading: false });
    } catch (err) {
      const error = err as ApiError;
      set({ error: error.message || 'Failed to trigger job', isLoading: false });
    }
  },

  setSelectedJob: (job) => set({ selectedJob: job }),
  setFilters: (filters) => set({ filters }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));

