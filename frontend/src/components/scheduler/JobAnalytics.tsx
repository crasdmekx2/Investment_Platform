import { useState, useEffect } from 'react';
import { Card } from '@/components/common/Card';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { schedulerApi } from '@/lib/api/scheduler';

interface AnalyticsData {
  total_executions: number;
  success_rate: number;
  success_count: number;
  failure_count: number;
  avg_execution_time_ms: number;
  failures_by_category: Array<{ error_category: string; failure_count: number }>;
  jobs_by_asset_type: Array<{ asset_type: string; job_count: number }>;
  execution_trends: Array<{
    date: string;
    execution_count: number;
    success_count: number;
    avg_execution_time_ms: number;
  }>;
  top_failing_jobs: Array<{
    job_id: string;
    symbol: string;
    asset_type: string;
    failure_count: number;
    total_executions: number;
  }>;
}

export function JobAnalytics() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<{ start: string; end: string }>({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    end: new Date().toISOString().split('T')[0],
  });
  const [assetTypeFilter, setAssetTypeFilter] = useState<string>('');

  useEffect(() => {
    loadAnalytics();
  }, [dateRange, assetTypeFilter]);

  const loadAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await schedulerApi.getAnalytics({
        start_date: dateRange.start,
        end_date: dateRange.end,
        asset_type: assetTypeFilter || undefined,
      });
      setAnalytics(response.data);
    } catch (err) {
      setError('Failed to load analytics. Please try again.');
      console.error('Failed to load analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  if (!analytics) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <Card title="Analytics Filters">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="start-date" className="block text-sm font-medium text-gray-700 mb-2">
              Start Date
            </label>
            <input
              id="start-date"
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 min-h-[44px]"
            />
          </div>
          <div>
            <label htmlFor="end-date" className="block text-sm font-medium text-gray-700 mb-2">
              End Date
            </label>
            <input
              id="end-date"
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 min-h-[44px]"
            />
          </div>
          <div>
            <label htmlFor="asset-type-filter" className="block text-sm font-medium text-gray-700 mb-2">
              Asset Type
            </label>
            <select
              id="asset-type-filter"
              value={assetTypeFilter}
              onChange={(e) => setAssetTypeFilter(e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 min-h-[44px]"
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
      </Card>

      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <div className="space-y-2">
            <p className="text-sm text-gray-600">Total Executions</p>
            <p className="text-3xl font-bold text-gray-900">{analytics.total_executions}</p>
          </div>
        </Card>
        <Card>
          <div className="space-y-2">
            <p className="text-sm text-gray-600">Success Rate</p>
            <p className="text-3xl font-bold text-gray-900">{analytics.success_rate.toFixed(1)}%</p>
          </div>
        </Card>
        <Card>
          <div className="space-y-2">
            <p className="text-sm text-gray-600">Avg Execution Time</p>
            <p className="text-3xl font-bold text-gray-900">
              {(analytics.avg_execution_time_ms / 1000).toFixed(2)}s
            </p>
          </div>
        </Card>
        <Card>
          <div className="space-y-2">
            <p className="text-sm text-gray-600">Failure Count</p>
            <p className="text-3xl font-bold text-gray-900">{analytics.failure_count}</p>
          </div>
        </Card>
      </div>

      {/* Execution Trends */}
      <Card title="Execution Trends">
        <div className="space-y-2">
          {analytics.execution_trends.length === 0 ? (
            <p className="text-gray-500">No execution data for the selected period</p>
          ) : (
            <div className="space-y-1">
              {analytics.execution_trends.map((trend) => {
                const successRate = trend.execution_count > 0
                  ? (trend.success_count / trend.execution_count) * 100
                  : 0;
                return (
                  <div
                    key={trend.date}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                  >
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">
                        {new Date(trend.date).toLocaleDateString()}
                      </p>
                      <p className="text-sm text-gray-600">
                        {trend.execution_count} executions • {successRate.toFixed(1)}% success
                      </p>
                    </div>
                    <div className="text-sm text-gray-600">
                      Avg: {(trend.avg_execution_time_ms / 1000).toFixed(2)}s
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </Card>

      {/* Jobs by Asset Type */}
      <Card title="Jobs by Asset Type">
        <div className="space-y-2">
          {analytics.jobs_by_asset_type.length === 0 ? (
            <p className="text-gray-500">No job data available</p>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {analytics.jobs_by_asset_type.map((item) => (
                <div key={item.asset_type} className="p-4 bg-gray-50 rounded-md">
                  <p className="text-sm font-medium text-gray-700">{item.asset_type}</p>
                  <p className="text-2xl font-bold text-gray-900">{item.job_count}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>

      {/* Failures by Category */}
      {analytics.failures_by_category.length > 0 && (
        <Card title="Failures by Error Category">
          <div className="space-y-2">
            {analytics.failures_by_category.map((item) => (
              <div
                key={item.error_category}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
              >
                <span className="font-medium text-gray-900 capitalize">{item.error_category}</span>
                <span className="text-lg font-semibold text-gray-900">
                  {item.failure_count}
                </span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Top Failing Jobs */}
      {analytics.top_failing_jobs.length > 0 && (
        <Card title="Top Failing Jobs">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Asset Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Failures
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Total Executions
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Failure Rate
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {analytics.top_failing_jobs.map((job) => {
                  const failureRate = job.total_executions > 0
                    ? (job.failure_count / job.total_executions) * 100
                    : 0;
                  return (
                    <tr key={job.job_id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {job.symbol}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {job.asset_type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {job.failure_count}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {job.total_executions}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-red-600">
                        {failureRate.toFixed(1)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

