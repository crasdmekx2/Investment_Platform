import { useEffect, useState } from 'react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { StatusBadge } from '@/components/common/StatusBadge';
import { JobAnalytics } from '@/components/scheduler/JobAnalytics';
import { useSchedulerStore } from '@/store/slices/schedulerSlice';
import { useCollectionStore } from '@/store/slices/collectionSlice';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';

export function JobsDashboard() {
  const { jobs, isLoading, fetchJobs } = useSchedulerStore();
  const { activeJobs, logs, fetchCollectionLogs } = useCollectionStore();
  const [showAnalytics, setShowAnalytics] = useState(false);

  useEffect(() => {
    fetchJobs();
    fetchCollectionLogs({ limit: 100 });
  }, [fetchJobs, fetchCollectionLogs]);

  const activeJobsCount = jobs.filter((j) => j.status === 'active').length;
  const pausedJobsCount = jobs.filter((j) => j.status === 'paused').length;
  const runningJobsCount = Object.keys(activeJobs).length;
  
  const recentLogs = logs.slice(0, 10);
  const successCount = recentLogs.filter((l) => l.status === 'success').length;
  const successRate = recentLogs.length > 0 ? (successCount / recentLogs.length) * 100 : 0;

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-6">
      {/* Analytics Toggle */}
      <div className="flex justify-end">
        <Button
          variant="secondary"
          onClick={() => setShowAnalytics(!showAnalytics)}
          className="min-h-[44px]"
        >
          {showAnalytics ? 'Hide' : 'Show'} Analytics
        </Button>
      </div>

      {showAnalytics && <JobAnalytics />}

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <div className="space-y-2">
            <p className="text-sm text-gray-600">Active Jobs</p>
            <p className="text-3xl font-bold text-gray-900">{activeJobsCount}</p>
          </div>
        </Card>
        <Card>
          <div className="space-y-2">
            <p className="text-sm text-gray-600">Running Now</p>
            <p className="text-3xl font-bold text-gray-900">{runningJobsCount}</p>
          </div>
        </Card>
        <Card>
          <div className="space-y-2">
            <p className="text-sm text-gray-600">Paused Jobs</p>
            <p className="text-3xl font-bold text-gray-900">{pausedJobsCount}</p>
          </div>
        </Card>
        <Card>
          <div className="space-y-2">
            <p className="text-sm text-gray-600">Success Rate</p>
            <p className="text-3xl font-bold text-gray-900">{successRate.toFixed(1)}%</p>
          </div>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card title="Recent Activity">
        <div className="space-y-4">
          {recentLogs.length === 0 ? (
            <p className="text-gray-500">No recent activity</p>
          ) : (
            <div className="space-y-2">
              {recentLogs.map((log) => (
                <div
                  key={log.log_id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Asset ID: {log.asset_id} - {log.collector_type}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(log.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <StatusBadge
                      status={
                        log.status === 'success'
                          ? 'success'
                          : log.status === 'failed'
                          ? 'failed'
                          : 'warning'
                      }
                    >
                      {log.status}
                    </StatusBadge>
                    <span className="text-sm text-gray-600">
                      {log.records_collected} records
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

