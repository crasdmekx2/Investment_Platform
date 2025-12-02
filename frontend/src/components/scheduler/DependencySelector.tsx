import { useState, useEffect } from 'react';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { schedulerApi } from '@/lib/api/scheduler';
import type { JobDependency, ScheduledJob } from '@/types/scheduler';

interface DependencySelectorProps {
  currentJobId?: string;
  selectedDependencies: JobDependency[];
  onUpdate: (dependencies: JobDependency[]) => void;
}

export function DependencySelector({
  currentJobId,
  selectedDependencies,
  onUpdate,
}: DependencySelectorProps) {
  const [jobs, setJobs] = useState<ScheduledJob[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const response = await schedulerApi.listJobs({ status: 'active' });
      // Filter out current job to prevent self-dependencies
      const filteredJobs = currentJobId
        ? response.data.filter(job => job.job_id !== currentJobId)
        : response.data;
      setJobs(filteredJobs);
    } catch (error) {
      console.error('Failed to load jobs:', error);
      setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredJobs = jobs.filter(job =>
    job.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
    job.job_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleToggleDependency = (jobId: string) => {
    const existing = selectedDependencies.find(dep => dep.depends_on_job_id === jobId);
    if (existing) {
      onUpdate(selectedDependencies.filter(dep => dep.depends_on_job_id !== jobId));
    } else {
      onUpdate([
        ...selectedDependencies,
        { depends_on_job_id: jobId, condition: 'success' },
      ]);
    }
  };

  const handleConditionChange = (jobId: string, condition: 'success' | 'complete' | 'any') => {
    onUpdate(
      selectedDependencies.map(dep =>
        dep.depends_on_job_id === jobId
          ? { ...dep, condition }
          : dep
      )
    );
  };

  const getDependencyCondition = (jobId: string): 'success' | 'complete' | 'any' => {
    const dep = selectedDependencies.find(d => d.depends_on_job_id === jobId);
    return dep?.condition || 'success';
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Job Dependencies</h3>
        <p className="text-sm text-gray-600 mb-4">
          Select jobs that must complete before this job can run
        </p>
      </div>

      <div>
        <label htmlFor="dependency-search" className="block text-sm font-medium text-gray-700 mb-2">
          Search Jobs
        </label>
        <input
          id="dependency-search"
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search by symbol or job ID..."
          className="block w-full rounded-md border-gray-300 shadow-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px]"
          aria-label="Search for jobs"
          aria-describedby="dependency-search-help"
        />
        <p id="dependency-search-help" className="sr-only">
          Search for jobs to add as dependencies
        </p>
      </div>

      {loading && <LoadingSpinner />}

      {filteredJobs.length > 0 && (
        <div className="space-y-2 max-h-64 overflow-y-auto border border-gray-200 rounded-md p-2">
          {filteredJobs.map((job) => {
            const isSelected = selectedDependencies.some(
              dep => dep.depends_on_job_id === job.job_id
            );
            return (
              <div
                key={job.job_id}
                className={`p-3 rounded-md border-2 ${
                  isSelected
                    ? 'bg-primary-50 border-primary-500'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => handleToggleDependency(job.job_id)}
                    className="mt-1 w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                    aria-label={`Select ${job.symbol} as dependency`}
                  />
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{job.symbol}</div>
                    <div className="text-sm text-gray-600">
                      {job.asset_type} • {job.job_id}
                    </div>
                    {isSelected && (
                      <div className="mt-2">
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Condition:
                        </label>
                        <select
                          value={getDependencyCondition(job.job_id)}
                          onChange={(e) =>
                            handleConditionChange(
                              job.job_id,
                              e.target.value as 'success' | 'complete' | 'any'
                            )
                          }
                          className="block w-full text-sm rounded-md border-gray-300 shadow-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px]"
                          aria-label={`Condition for ${job.symbol} dependency`}
                        >
                          <option value="success">Must succeed</option>
                          <option value="complete">Must complete</option>
                          <option value="any">Just run</option>
                        </select>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selectedDependencies.length > 0 && (
        <div className="p-4 bg-primary-50 rounded-md">
          <p className="text-sm font-medium text-gray-700 mb-2">
            Selected Dependencies ({selectedDependencies.length}):
          </p>
          <div className="flex flex-wrap gap-2">
            {selectedDependencies.map((dep) => {
              const job = jobs.find(j => j.job_id === dep.depends_on_job_id);
              return (
                <span
                  key={dep.depends_on_job_id}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary-600 text-white"
                >
                  {job?.symbol || dep.depends_on_job_id} ({dep.condition})
                  <button
                    onClick={() => handleToggleDependency(dep.depends_on_job_id)}
                    className="ml-2 text-primary-200 hover:text-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-primary-600 rounded min-h-[44px] min-w-[44px] flex items-center justify-center"
                    aria-label={`Remove ${job?.symbol || dep.depends_on_job_id} dependency`}
                  >
                    <span aria-hidden="true">×</span>
                  </button>
                </span>
              );
            })}
          </div>
        </div>
      )}

      {filteredJobs.length === 0 && !loading && (
        <p className="text-sm text-gray-500">No jobs found. Create some jobs first to set up dependencies.</p>
      )}
    </div>
  );
}

