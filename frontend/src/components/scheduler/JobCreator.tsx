import { useState, useEffect } from 'react';
import { Card } from '@/components/common/Card';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { AssetTypeSelector } from '@/components/scheduler/AssetTypeSelector';
import { AssetSelector } from '@/components/scheduler/AssetSelector';
import { CollectionParamsForm } from '@/components/scheduler/CollectionParamsForm';
import { ScheduleConfigForm } from '@/components/scheduler/ScheduleConfigForm';
import { JobReviewCard } from '@/components/scheduler/JobReviewCard';
import { JobTemplateSelector } from '@/components/scheduler/JobTemplateSelector';
import { useSchedulerStore } from '@/store/slices/schedulerSlice';
import { useCollectorMetadata } from '@/hooks/useCollectorMetadata';
import type { AssetType, TriggerConfig, JobTemplate, JobDependency } from '@/types/scheduler';

type Step = 0 | 1 | 2 | 3 | 4 | 5;

interface JobCreatorProps {
  onSuccess?: () => void;
}

export function JobCreator({ onSuccess }: JobCreatorProps) {
  const [step, setStep] = useState<Step>(0);
  const [assetType, setAssetType] = useState<AssetType | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<JobTemplate | null>(null);
  const [symbol, setSymbol] = useState<string | string[]>('');
  const [collectorKwargs, setCollectorKwargs] = useState<Record<string, unknown>>({});
  const [triggerConfig, setTriggerConfig] = useState<TriggerConfig | null>(null);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [incremental, setIncremental] = useState(true);
  const [maxRetries, setMaxRetries] = useState(3);
  const [retryDelaySeconds, setRetryDelaySeconds] = useState(60);
  const [retryBackoffMultiplier, setRetryBackoffMultiplier] = useState(2.0);
  const [dependencies, setDependencies] = useState<JobDependency[]>([]);

  const { metadata, loading: metadataLoading } = useCollectorMetadata();
  const { createJob, triggerJob, isLoading, error } = useSchedulerStore();
  const [isTriggering, setIsTriggering] = useState(false);
  const [bulkCreating, setBulkCreating] = useState(false);

  // Apply template when selected
  useEffect(() => {
    if (selectedTemplate && assetType) {
      // Pre-fill form with template values
      if (selectedTemplate.symbol) {
        setSymbol(selectedTemplate.symbol);
      }
      if (selectedTemplate.trigger_config) {
        setTriggerConfig(selectedTemplate.trigger_config);
      }
      if (selectedTemplate.start_date) {
        setStartDate(selectedTemplate.start_date);
      }
      if (selectedTemplate.end_date) {
        setEndDate(selectedTemplate.end_date);
      }
      if (selectedTemplate.collector_kwargs) {
        setCollectorKwargs(selectedTemplate.collector_kwargs);
      }
      if (selectedTemplate.max_retries !== undefined) {
        setMaxRetries(selectedTemplate.max_retries);
      }
      if (selectedTemplate.retry_delay_seconds !== undefined) {
        setRetryDelaySeconds(selectedTemplate.retry_delay_seconds);
      }
      if (selectedTemplate.retry_backoff_multiplier !== undefined) {
        setRetryBackoffMultiplier(selectedTemplate.retry_backoff_multiplier);
      }
    }
  }, [selectedTemplate, assetType]);

  const handleCreate = async () => {
    if (!assetType || !symbol || !triggerConfig) {
      return;
    }

    const symbols = Array.isArray(symbol) ? symbol : [symbol];
    if (symbols.length === 0) {
      return;
    }

    // Check if this is immediate execution only
    const shouldExecuteNow = triggerConfig.execute_now === true;

    // For immediate execution, keep execute_now in trigger_config so backend knows not to schedule it
    // For scheduled jobs, strip execute_now flag
    const triggerConfigForBackend = shouldExecuteNow 
      ? triggerConfig  // Keep execute_now flag for backend
      : (() => {
          const { execute_now, ...config } = triggerConfig;
          return config;
        })();

    // Bulk create jobs
    if (symbols.length > 1) {
      setBulkCreating(true);
      try {
        const jobPromises = symbols.map(sym => 
          createJob({
            symbol: sym,
            asset_type: assetType,
            trigger_type: triggerConfig.type,
            trigger_config: triggerConfigForBackend,
            start_date: startDate || undefined,
            end_date: endDate || undefined,
            collector_kwargs: Object.keys(collectorKwargs).length > 0 ? collectorKwargs : undefined,
            incremental,
            max_retries: maxRetries,
            retry_delay_seconds: retryDelaySeconds,
            retry_backoff_multiplier: retryBackoffMultiplier,
            dependencies: dependencies.length > 0 ? dependencies : undefined,
          } as any)
        );

        const jobs = await Promise.all(jobPromises);
        const successfulJobs = jobs.filter(job => job !== null);

        // Trigger jobs if needed
        if (shouldExecuteNow && successfulJobs.length > 0) {
          setIsTriggering(true);
          try {
            await Promise.all(successfulJobs.map(job => triggerJob(job!.job_id)));
            console.log(`Successfully triggered ${successfulJobs.length} jobs`);
          } catch (err) {
            console.error('Failed to trigger some jobs:', err);
          } finally {
            setIsTriggering(false);
          }
        }

        if (onSuccess) {
          onSuccess();
        }
      } catch (err) {
        console.error('Failed to create some jobs:', err);
      } finally {
        setBulkCreating(false);
      }
    } else {
      // Single job creation
      const job = await createJob({
        symbol: symbols[0],
        asset_type: assetType,
        trigger_type: triggerConfig.type,
        trigger_config: triggerConfigForBackend,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        collector_kwargs: Object.keys(collectorKwargs).length > 0 ? collectorKwargs : undefined,
        incremental,
        max_retries: maxRetries,
        retry_delay_seconds: retryDelaySeconds,
        retry_backoff_multiplier: retryBackoffMultiplier,
        dependencies: dependencies.length > 0 ? dependencies : undefined,
      } as any);

      if (job) {
        // Check if job should be executed immediately
        if (shouldExecuteNow) {
          setIsTriggering(true);
          try {
            await triggerJob(job.job_id);
            console.log('Job triggered successfully');
          } catch (err) {
            console.error('Failed to trigger job:', err);
          } finally {
            setIsTriggering(false);
          }
        }

        if (onSuccess) {
          onSuccess();
        }
      }
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
        {[0, 1, 2, 3, 4, 5].map((s) => (
          <div key={s} className="flex items-center flex-1">
            <div className="flex flex-col items-center">
              <div
                className={`
                  w-10 h-10 rounded-full flex items-center justify-center font-medium
                  ${step >= s ? 'bg-primary-600 text-white' : 'bg-gray-200 text-gray-600'}
                `}
              >
                {s === 0 ? 'T' : s}
              </div>
              <span className="mt-2 text-xs text-gray-600">
                {s === 0 && 'Template'}
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
        {step === 0 && !assetType && (
          <AssetTypeSelector
            metadata={metadata}
            selected={assetType}
            onSelect={(type) => {
              setAssetType(type);
              setSelectedTemplate(null); // Clear template when changing asset type
            }}
            onNext={() => {
              if (assetType) {
                // If template was selected, skip to asset selection, otherwise show template selector
                if (selectedTemplate) {
                  setStep(2);
                } else {
                  setStep(0); // Show template selector (will now render since assetType is set)
                }
              }
            }}
          />
        )}
        {step === 0 && assetType && (
          <JobTemplateSelector
            assetType={assetType}
            selectedTemplateId={selectedTemplate?.template_id || null}
            onSelect={(template) => {
              setSelectedTemplate(template);
              if (template) {
                setStep(2); // Skip to asset selection if template selected
              }
            }}
            onNext={() => setStep(2)}
            onSkip={() => setStep(2)}
          />
        )}
        {step === 1 && (
          <AssetTypeSelector
            metadata={metadata}
            selected={assetType}
            onSelect={(type) => {
              setAssetType(type);
              setSelectedTemplate(null); // Clear template when changing asset type
            }}
            onNext={() => {
              if (assetType) {
                // If template was selected, skip to asset selection, otherwise show template selector
                if (selectedTemplate) {
                  setStep(2);
                } else {
                  setStep(0); // Show template selector
                }
              }
            }}
          />
        )}
        {step === 2 && (
          <AssetSelector
            assetType={assetType!}
            selected={symbol}
            onSelect={setSymbol}
            onBack={() => {
              if (selectedTemplate) {
                setStep(0); // Go back to template selector
              } else {
                setStep(1); // Go back to asset type
              }
            }}
            onNext={() => {
              const symbols = Array.isArray(symbol) ? symbol : (symbol ? [symbol] : []);
              if (symbols.length > 0) {
                setStep(3);
              }
            }}
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
            incremental={incremental}
            startDate={startDate}
            endDate={endDate}
            maxRetries={maxRetries}
            retryDelaySeconds={retryDelaySeconds}
            retryBackoffMultiplier={retryBackoffMultiplier}
            onRetryConfigUpdate={(max, delay, backoff) => {
              setMaxRetries(max);
              setRetryDelaySeconds(delay);
              setRetryBackoffMultiplier(backoff);
            }}
            dependencies={dependencies}
            onDependenciesUpdate={setDependencies}
          />
        )}
        {step === 5 && (
          <JobReviewCard
            assetType={assetType!}
            symbol={Array.isArray(symbol) ? symbol.join(', ') : symbol}
            collectorKwargs={collectorKwargs}
            triggerConfig={triggerConfig!}
            startDate={startDate}
            endDate={endDate}
            incremental={incremental}
            onBack={() => setStep(4)}
            onCreate={handleCreate}
            isLoading={isLoading || isTriggering || bulkCreating}
          />
        )}
      </Card>
    </div>
  );
}

