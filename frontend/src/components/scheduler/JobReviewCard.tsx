import { Button } from '@/components/common/Button';
import { formatTrigger } from '@/lib/utils/scheduler';
import { getAssetTypeDisplayName } from '@/lib/utils/collectors';
import type { AssetType, TriggerConfig } from '@/types/scheduler';

interface JobReviewCardProps {
  assetType: AssetType;
  symbol: string;
  collectorKwargs: Record<string, unknown>;
  triggerConfig: TriggerConfig;
  startDate: string;
  endDate: string;
  incremental: boolean;
  onBack: () => void;
  onCreate: () => void;
  isLoading: boolean;
}

export function JobReviewCard({
  assetType,
  symbol,
  collectorKwargs,
  triggerConfig,
  startDate,
  endDate,
  incremental,
  onBack,
  onCreate,
  isLoading,
}: JobReviewCardProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Review Job Configuration</h2>
        <p className="text-gray-600">Review your job configuration before creating</p>
      </div>

      <div className="bg-gray-50 rounded-lg p-6 space-y-4">
        <div>
          <h3 className="text-sm font-medium text-gray-500">Asset Type</h3>
          <p className="text-lg font-semibold text-gray-900">{getAssetTypeDisplayName(assetType)}</p>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-500">Symbol</h3>
          <p className="text-lg font-semibold text-gray-900">{symbol}</p>
        </div>

        {Object.keys(collectorKwargs).length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-500">Collection Parameters</h3>
            <div className="mt-1 space-y-1">
              {Object.entries(collectorKwargs).map(([key, value]) => (
                <p key={key} className="text-sm text-gray-900">
                  {key}: {String(value)}
                </p>
              ))}
            </div>
          </div>
        )}

        <div>
          <h3 className="text-sm font-medium text-gray-500">Schedule</h3>
          <p className="text-lg font-semibold text-gray-900">{formatTrigger(triggerConfig)}</p>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-500">Collection Mode</h3>
          <p className="text-lg font-semibold text-gray-900">
            {incremental ? 'Incremental (missing data only)' : 'Full History'}
          </p>
        </div>

        {!incremental && (startDate || endDate) && (
          <div>
            <h3 className="text-sm font-medium text-gray-500">Date Range</h3>
            <p className="text-lg font-semibold text-gray-900">
              {startDate && new Date(startDate).toLocaleDateString()}
              {startDate && endDate && ' - '}
              {endDate && new Date(endDate).toLocaleDateString()}
            </p>
          </div>
        )}
      </div>

      <div className="flex justify-between">
        <Button variant="secondary" onClick={onBack} disabled={isLoading} className="min-h-[44px] min-w-[120px]">
          Back
        </Button>
        <Button onClick={onCreate} isLoading={isLoading} className="min-h-[44px] min-w-[120px]">
          Create Job
        </Button>
      </div>
    </div>
  );
}

