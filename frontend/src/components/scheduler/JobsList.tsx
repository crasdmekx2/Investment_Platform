import { useState } from 'react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { StatusBadge } from '@/components/common/StatusBadge';
import { ScheduleVisualization } from '@/components/scheduler/ScheduleVisualization';
import { useSchedulerStore } from '@/store/slices/schedulerSlice';
import { formatTrigger } from '@/lib/utils/scheduler';
import type { JobStatus, AssetType } from '@/types/scheduler';

export function JobsList() {
  const { jobs, isLoading, error, setFilters, fetchJobs, pauseJob, resumeJob, deleteJob } = useSchedulerStore();
  const [selectedStatus, setSelectedStatus] = useState<JobStatus | ''>('');
  const [selectedAssetType, setSelectedAssetType] = useState<AssetType | ''>('');
  const [showVisualization, setShowVisualization] = useState(false);

  const handleFilterChange = () => {
    setFilters({
      status: selectedStatus || undefined,
      asset_type: selectedAssetType || undefined,
    });
    fetchJobs();
  };

  const handlePause = async (jobId: string) => {
    if (window.confirm('Are you sure you want to pause this job?')) {
      await pauseJob(jobId);
      fetchJobs();
    }
  };

  const handleResume = async (jobId: string) => {
    await resumeJob(jobId);
    fetchJobs();
  };

  const handleDelete = async (jobId: string) => {
    if (window.confirm('Are you sure you want to delete this job? This action cannot be undone.')) {
      await deleteJob(jobId);
      fetchJobs();
    }
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  return (
    <div className="space-y-6">
      {/* Visualization Toggle */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Scheduled Jobs</h2>
        <Button
          variant="secondary"
          onClick={() => setShowVisualization(!showVisualization)}
          className="min-h-[44px]"
        >
          {showVisualization ? 'Hide' : 'Show'} Schedule Visualization
        </Button>
      </div>

      {showVisualization && (
        <ScheduleVisualization jobs={jobs} viewMode="timeline" daysAhead={7} />
      )}

      {/* Filters */}
      <Card title="Filters">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              id="status-filter"
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value as JobStatus | '')}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px]"
              aria-label="Filter jobs by status"
            >
              <option value="">All</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="failed">Failed</option>
              <option value="completed">Completed</option>
              <option value="pending">Pending</option>
            </select>
          </div>
          <div>
            <label htmlFor="asset-type-filter" className="block text-sm font-medium text-gray-700 mb-2">
              Asset Type
            </label>
            <select
              id="asset-type-filter"
              value={selectedAssetType}
              onChange={(e) => setSelectedAssetType(e.target.value as AssetType | '')}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px]"
              aria-label="Filter jobs by asset type"
            >
              <option value="">All</option>
              <option value="stock">Stock</option>
              <option value="crypto">Crypto</option>
              <option value="forex">Forex</option>
              <option value="bond">Bond</option>
              <option value="commodity">Commodity</option>
              <option value="economic_indicator">Economic Indicator</option>
            </select>
          </div>
        </div>
        <div className="mt-4">
          <Button onClick={handleFilterChange}>Apply Filters</Button>
        </div>
      </Card>

      {/* Jobs Table */}
      <Card title="Scheduled Jobs">
        {jobs.length === 0 ? (
          <p className="text-gray-500">No jobs found</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200" aria-label="Scheduled jobs table">
              <thead>
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Symbol
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Asset Type
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Schedule
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Next Run
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {jobs.map((job) => (
                  <tr key={job.job_id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {job.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {job.asset_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatTrigger(job.trigger_config)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge
                        status={
                          job.status === 'active'
                            ? 'active'
                            : job.status === 'paused'
                            ? 'paused'
                            : job.status === 'failed'
                            ? 'failed'
                            : job.status === 'completed'
                            ? 'completed'
                            : 'pending'
                        }
                      >
                        {job.status}
                      </StatusBadge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {job.next_run_at ? new Date(job.next_run_at).toLocaleString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                      {job.status === 'active' ? (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handlePause(job.job_id)}
                          className="min-h-[44px] min-w-[44px]"
                        >
                          Pause
                        </Button>
                      ) : job.status === 'paused' ? (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => handleResume(job.job_id)}
                          className="min-h-[44px] min-w-[44px]"
                        >
                          Resume
                        </Button>
                      ) : null}
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleDelete(job.job_id)}
                        className="min-h-[44px] min-w-[44px]"
                      >
                        Delete
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

