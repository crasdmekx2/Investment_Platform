import { Button } from '@/components/common/Button';
import type { AssetType } from '@/types/scheduler';

interface CollectionParamsFormProps {
  assetType: AssetType;
  collectorKwargs: Record<string, unknown>;
  onUpdate: (kwargs: Record<string, unknown>) => void;
  startDate: string;
  endDate: string;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
  incremental: boolean;
  onIncrementalChange: (incremental: boolean) => void;
  onBack: () => void;
  onNext: () => void;
}

export function CollectionParamsForm({
  assetType,
  collectorKwargs,
  onUpdate,
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  incremental,
  onIncrementalChange,
  onBack,
  onNext,
}: CollectionParamsFormProps) {
  const handleParamChange = (key: string, value: unknown) => {
    onUpdate({ ...collectorKwargs, [key]: value });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Collection Parameters</h2>
        <p className="text-gray-600">Configure data collection parameters</p>
      </div>

      {/* Asset-specific parameters */}
      {assetType === 'crypto' && (
        <div>
          <label htmlFor="granularity" className="block text-sm font-medium text-gray-700 mb-2">
            Granularity
          </label>
          <select
            id="granularity"
            value={(collectorKwargs.granularity as string) || 'ONE_DAY'}
            onChange={(e) => handleParamChange('granularity', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px]"
            aria-describedby="granularity-help"
          >
            <option value="ONE_MINUTE">1 Minute</option>
            <option value="FIVE_MINUTE">5 Minutes</option>
            <option value="FIFTEEN_MINUTE">15 Minutes</option>
            <option value="ONE_HOUR">1 Hour</option>
            <option value="SIX_HOUR">6 Hours</option>
            <option value="ONE_DAY">1 Day</option>
          </select>
        </div>
      )}

      {assetType === 'stock' && (
        <div>
          <label htmlFor="interval" className="block text-sm font-medium text-gray-700 mb-2">
            Interval
          </label>
          <select
            id="interval"
            value={(collectorKwargs.interval as string) || '1d'}
            onChange={(e) => handleParamChange('interval', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px]"
            aria-describedby="interval-help"
          >
            <option value="1m">1 Minute</option>
            <option value="5m">5 Minutes</option>
            <option value="15m">15 Minutes</option>
            <option value="1h">1 Hour</option>
            <option value="1d">1 Day</option>
            <option value="1wk">1 Week</option>
            <option value="1mo">1 Month</option>
          </select>
        </div>
      )}

      {/* Incremental vs Full History */}
      <div>
        <label className="flex items-center space-x-3 cursor-pointer min-h-[44px]">
          <input
            type="checkbox"
            checked={incremental}
            onChange={(e) => onIncrementalChange(e.target.checked)}
            className="w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            aria-describedby="incremental-help"
          />
          <span className="text-sm font-medium text-gray-700">
            Incremental mode (only fetch missing data)
          </span>
        </label>
        <p id="incremental-help" className="mt-1 text-sm text-gray-500">
          When enabled, only missing data will be collected. When disabled, full history will be downloaded.
        </p>
      </div>

      {/* Date Range (for full history) */}
      {!incremental && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="start-date" className="block text-sm font-medium text-gray-700 mb-2">
              Start Date
            </label>
            <input
              id="start-date"
              type="date"
              value={startDate}
              onChange={(e) => onStartDateChange(e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px]"
              aria-describedby="start-date-help"
            />
            <p id="start-date-help" className="sr-only">
              Start date for data collection
            </p>
          </div>
          <div>
            <label htmlFor="end-date" className="block text-sm font-medium text-gray-700 mb-2">
              End Date
            </label>
            <input
              id="end-date"
              type="date"
              value={endDate}
              onChange={(e) => onEndDateChange(e.target.value)}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px]"
              aria-describedby="end-date-help"
            />
            <p id="end-date-help" className="sr-only">
              End date for data collection
            </p>
          </div>
        </div>
      )}

      <div className="flex justify-between">
        <Button variant="secondary" onClick={onBack} className="min-h-[44px] min-w-[120px]">
          Back
        </Button>
        <Button onClick={onNext} className="min-h-[44px] min-w-[120px]">
          Next
        </Button>
      </div>
    </div>
  );
}

