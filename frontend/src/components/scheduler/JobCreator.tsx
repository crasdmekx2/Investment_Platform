import { useState } from 'react';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { AssetTypeSelector } from '@/components/scheduler/AssetTypeSelector';
import { AssetSelector } from '@/components/scheduler/AssetSelector';
import { CollectionParamsForm } from '@/components/scheduler/CollectionParamsForm';
import { ScheduleConfigForm } from '@/components/scheduler/ScheduleConfigForm';
import { JobReviewCard } from '@/components/scheduler/JobReviewCard';
import { useSchedulerStore } from '@/store/slices/schedulerSlice';
import { useCollectorMetadata } from '@/hooks/useCollectorMetadata';
import type { AssetType, TriggerConfig } from '@/types/scheduler';

type Step = 1 | 2 | 3 | 4 | 5;

interface JobCreatorProps {
  onSuccess?: () => void;
}

export function JobCreator({ onSuccess }: JobCreatorProps) {
  const [step, setStep] = useState<Step>(1);
  const [assetType, setAssetType] = useState<AssetType | null>(null);
  const [symbol, setSymbol] = useState('');
  const [collectorKwargs, setCollectorKwargs] = useState<Record<string, unknown>>({});
  const [triggerConfig, setTriggerConfig] = useState<TriggerConfig | null>(null);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [incremental, setIncremental] = useState(true);

  const { metadata, loading: metadataLoading } = useCollectorMetadata();
  const { createJob, isLoading, error } = useSchedulerStore();

  const handleCreate = async () => {
    if (!assetType || !symbol || !triggerConfig) {
      return;
    }

    const job = await createJob({
      symbol,
      asset_type: assetType,
      trigger_type: triggerConfig.type,
      trigger_config: triggerConfig,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
      collector_kwargs: Object.keys(collectorKwargs).length > 0 ? collectorKwargs : undefined,
      incremental,
    } as any);

    if (job && onSuccess) {
      onSuccess();
    }
  };

  if (metadataLoading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="space-y-6">
      {error && <ErrorMessage message={error} />}

      {/* Progress Steps */}
      <div className="flex items-center justify-between">
        {[1, 2, 3, 4, 5].map((s) => (
          <div key={s} className="flex items-center flex-1">
            <div className="flex flex-col items-center">
              <div
                className={`
                  w-10 h-10 rounded-full flex items-center justify-center font-medium
                  ${step >= s ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-600'}
                `}
              >
                {s}
              </div>
              <span className="mt-2 text-xs text-gray-600">
                {s === 1 && 'Asset Type'}
                {s === 2 && 'Asset'}
                {s === 3 && 'Parameters'}
                {s === 4 && 'Schedule'}
                {s === 5 && 'Review'}
              </span>
            </div>
            {s < 5 && (
              <div
                className={`flex-1 h-1 mx-2 ${step > s ? 'bg-primary-600' : 'bg-gray-200'}`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Step Content */}
      <Card>
        {step === 1 && (
          <AssetTypeSelector
            metadata={metadata}
            selected={assetType}
            onSelect={setAssetType}
            onNext={() => assetType && setStep(2)}
          />
        )}
        {step === 2 && (
          <AssetSelector
            assetType={assetType!}
            selected={symbol}
            onSelect={setSymbol}
            onBack={() => setStep(1)}
            onNext={() => symbol && setStep(3)}
          />
        )}
        {step === 3 && (
          <CollectionParamsForm
            assetType={assetType!}
            collectorKwargs={collectorKwargs}
            onUpdate={setCollectorKwargs}
            startDate={startDate}
            endDate={endDate}
            onStartDateChange={setStartDate}
            onEndDateChange={setEndDate}
            incremental={incremental}
            onIncrementalChange={setIncremental}
            onBack={() => setStep(2)}
            onNext={() => setStep(4)}
          />
        )}
        {step === 4 && (
          <ScheduleConfigForm
            triggerConfig={triggerConfig}
            onUpdate={setTriggerConfig}
            onBack={() => setStep(3)}
            onNext={() => triggerConfig && setStep(5)}
          />
        )}
        {step === 5 && (
          <JobReviewCard
            assetType={assetType!}
            symbol={symbol}
            collectorKwargs={collectorKwargs}
            triggerConfig={triggerConfig!}
            startDate={startDate}
            endDate={endDate}
            incremental={incremental}
            onBack={() => setStep(4)}
            onCreate={handleCreate}
            isLoading={isLoading}
          />
        )}
      </Card>
    </div>
  );
}

