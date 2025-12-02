import { useState } from 'react';
import { Button } from '@/components/common/Button';
import { DependencySelector } from '@/components/scheduler/DependencySelector';
import type { TriggerConfig, CronTriggerConfig, IntervalTriggerConfig, JobDependency } from '@/types/scheduler';

interface ScheduleConfigFormProps {
  triggerConfig: TriggerConfig | null;
  onUpdate: (config: TriggerConfig) => void;
  onBack: () => void;
  onNext: () => void;
  incremental: boolean;
  startDate: string;
  endDate: string;
  maxRetries?: number;
  retryDelaySeconds?: number;
  retryBackoffMultiplier?: number;
  onRetryConfigUpdate?: (maxRetries: number, retryDelaySeconds: number, retryBackoffMultiplier: number) => void;
  dependencies?: JobDependency[];
  onDependenciesUpdate?: (dependencies: JobDependency[]) => void;
  currentJobId?: string;
}

export function ScheduleConfigForm({ 
  triggerConfig, 
  onUpdate, 
  onBack, 
  onNext,
  incremental,
  startDate,
  endDate,
  maxRetries = 3,
  retryDelaySeconds = 60,
  retryBackoffMultiplier = 2.0,
  onRetryConfigUpdate,
  dependencies = [],
  onDependenciesUpdate,
  currentJobId,
}: ScheduleConfigFormProps) {
  // Check if "Schedule Now" option should be available
  const showScheduleNow = !incremental && startDate && endDate;
  
  // Determine if "Schedule Now" is selected (check execute_now flag or if no trigger type selected yet)
  const isScheduleNow = triggerConfig?.execute_now === true || 
    (showScheduleNow && !triggerConfig);
  
  const [triggerType, setTriggerType] = useState<'cron' | 'interval' | 'now'>(
    isScheduleNow ? 'now' : (triggerConfig?.type || 'interval')
  );
  const [cronConfig, setCronConfig] = useState<CronTriggerConfig>(
    (triggerConfig as CronTriggerConfig) || {
      type: 'cron',
      minute: '0',
      hour: '9',
      second: '0',
      execute_now: false,
    }
  );
  const [intervalConfig, setIntervalConfig] = useState<IntervalTriggerConfig>(
    (triggerConfig as IntervalTriggerConfig) || {
      type: 'interval',
      hours: 1,
      execute_now: false,
    }
  );
  const [retryMaxRetries, setRetryMaxRetries] = useState(maxRetries);
  const [retryDelay, setRetryDelay] = useState(retryDelaySeconds);
  const [retryBackoff, setRetryBackoff] = useState(retryBackoffMultiplier);

  const handleUpdate = () => {
    if (triggerType === 'now') {
      // For "Schedule Now", use a placeholder trigger config (won't be used for scheduling)
      // The execute_now flag indicates this is immediate execution only
      const nowConfig: IntervalTriggerConfig = {
        type: 'interval',
        hours: 0,
        minutes: 0,
        execute_now: true,
      };
      onUpdate(nowConfig);
    } else if (triggerType === 'cron') {
      onUpdate(cronConfig);
    } else {
      onUpdate(intervalConfig);
    }
  };

  const handleTriggerTypeChange = (type: 'cron' | 'interval' | 'now') => {
    setTriggerType(type);
    if (type === 'now') {
      // When selecting "Schedule Now", set execute_now flag with placeholder config
      const nowConfig: IntervalTriggerConfig = {
        type: 'interval',
        hours: 0,
        minutes: 0,
        execute_now: true,
      };
      onUpdate(nowConfig);
    } else if (type === 'cron') {
      // Clear execute_now when selecting cron
      onUpdate({ ...cronConfig, execute_now: false });
    } else {
      // Clear execute_now when selecting interval
      onUpdate({ ...intervalConfig, execute_now: false });
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Schedule Configuration</h2>
        <p className="text-gray-600">Configure when the job should run</p>
      </div>

      {/* Trigger Type Selection */}
      <fieldset>
        <legend className="block text-sm font-medium text-gray-700 mb-2">Trigger Type</legend>
        <div className="flex gap-4 flex-wrap" role="radiogroup">
          <label className="flex items-center space-x-2 cursor-pointer min-h-[44px]">
            <input
              type="radio"
              name="trigger-type"
              value="interval"
              checked={triggerType === 'interval'}
              onChange={() => handleTriggerTypeChange('interval')}
              className="w-5 h-5 text-primary-600 border-gray-300 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              aria-label="Interval trigger"
            />
            <span className="text-sm font-medium text-gray-700">Interval</span>
          </label>
          <label className="flex items-center space-x-2 cursor-pointer min-h-[44px]">
            <input
              type="radio"
              name="trigger-type"
              value="cron"
              checked={triggerType === 'cron'}
              onChange={() => handleTriggerTypeChange('cron')}
              className="w-5 h-5 text-primary-600 border-gray-300 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              aria-label="Cron schedule trigger"
            />
            <span className="text-sm font-medium text-gray-700">Cron Schedule</span>
          </label>
          {showScheduleNow && (
            <label className="flex items-center space-x-2 cursor-pointer min-h-[44px]">
              <input
                type="radio"
                name="trigger-type"
                value="now"
                checked={triggerType === 'now'}
                onChange={() => handleTriggerTypeChange('now')}
                className="w-5 h-5 text-primary-600 border-gray-300 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                aria-label="Schedule now trigger"
              />
              <span className="text-sm font-medium text-gray-700">Schedule Now</span>
            </label>
          )}
        </div>
        {showScheduleNow && triggerType === 'now' && (
          <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> The job will execute immediately after creation for the specified date range. 
              This is a one-time execution - the job will not be scheduled for future runs.
            </p>
          </div>
        )}
      </div>

      {/* Schedule Now Configuration */}
      {triggerType === 'now' && (
        <div className="space-y-4">
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
            <p className="text-sm text-gray-700">
              The job will execute immediately after creation. No recurring schedule will be configured.
            </p>
          </div>
        </div>
      )}

      {/* Interval Configuration */}
      {triggerType === 'interval' && (
        <div className="space-y-4">
          <div>
            <label htmlFor="interval-hours" className="block text-sm font-medium text-gray-700 mb-2">
              Hours
            </label>
            <input
              id="interval-hours"
              type="number"
              min="0"
              value={intervalConfig.hours || 0}
              onChange={(e) => {
                const updated = { ...intervalConfig, hours: parseInt(e.target.value) || 0, execute_now: false };
                setIntervalConfig(updated);
              }}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px]"
              aria-describedby="interval-hours-help"
            />
            <p id="interval-hours-help" className="sr-only">
              Number of hours between job executions
            </p>
          </div>
          <div>
            <label htmlFor="interval-minutes" className="block text-sm font-medium text-gray-700 mb-2">
              Minutes
            </label>
            <input
              id="interval-minutes"
              type="number"
              min="0"
              value={intervalConfig.minutes || 0}
              onChange={(e) => {
                const updated = { ...intervalConfig, minutes: parseInt(e.target.value) || 0, execute_now: false };
                setIntervalConfig(updated);
              }}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px]"
              aria-describedby="interval-minutes-help"
            />
            <p id="interval-minutes-help" className="sr-only">
              Number of minutes between job executions
            </p>
          </div>
        </div>
      )}

      {/* Cron Configuration */}
      {triggerType === 'cron' && (
        <div className="space-y-4">
          <div>
            <label htmlFor="cron-hour" className="block text-sm font-medium text-gray-700 mb-2">
              Hour (0-23)
            </label>
            <input
              id="cron-hour"
              type="text"
              value={cronConfig.hour || ''}
              onChange={(e) => {
                const updated = { ...cronConfig, hour: e.target.value, execute_now: false };
                setCronConfig(updated);
              }}
              placeholder="9"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px]"
              aria-describedby="cron-hour-help"
            />
            <p id="cron-hour-help" className="mt-1 text-sm text-gray-500">
              Hour of day (0-23) when job should run
            </p>
          </div>
          <div>
            <label htmlFor="cron-minute" className="block text-sm font-medium text-gray-700 mb-2">
              Minute (0-59)
            </label>
            <input
              id="cron-minute"
              type="text"
              value={cronConfig.minute || ''}
              onChange={(e) => {
                const updated = { ...cronConfig, minute: e.target.value, execute_now: false };
                setCronConfig(updated);
              }}
              placeholder="0"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px]"
              aria-describedby="cron-minute-help"
            />
            <p id="cron-minute-help" className="mt-1 text-sm text-gray-500">
              Minute of hour (0-59) when job should run
            </p>
          </div>
        </div>
      )}

      {/* Retry Configuration */}
      {triggerType !== 'now' && (
        <div className="space-y-4 border-t pt-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Retry Configuration</h3>
            <p className="text-sm text-gray-600 mb-4">
              Configure automatic retry behavior for failed jobs
            </p>
          </div>
          
          <div>
            <label htmlFor="max-retries" className="block text-sm font-medium text-gray-700 mb-2">
              Maximum Retries
            </label>
            <input
              id="max-retries"
              type="number"
              min="0"
              max="10"
              value={retryMaxRetries}
              onChange={(e) => {
                const value = parseInt(e.target.value) || 0;
                setRetryMaxRetries(value);
                if (onRetryConfigUpdate) {
                  onRetryConfigUpdate(value, retryDelay, retryBackoff);
                }
              }}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px]"
              aria-describedby="max-retries-help"
            />
            <p id="max-retries-help" className="mt-1 text-sm text-gray-500">
              Number of retry attempts for transient failures (0 = no retries)
            </p>
          </div>
          
          <div>
            <label htmlFor="retry-delay" className="block text-sm font-medium text-gray-700 mb-2">
              Initial Retry Delay (seconds)
            </label>
            <input
              id="retry-delay"
              type="number"
              min="0"
              value={retryDelay}
              onChange={(e) => {
                const value = parseInt(e.target.value) || 0;
                setRetryDelay(value);
                if (onRetryConfigUpdate) {
                  onRetryConfigUpdate(retryMaxRetries, value, retryBackoff);
                }
              }}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px]"
              aria-describedby="retry-delay-help"
            />
            <p id="retry-delay-help" className="mt-1 text-sm text-gray-500">
              Initial delay before first retry attempt
            </p>
          </div>
          
          <div>
            <label htmlFor="retry-backoff" className="block text-sm font-medium text-gray-700 mb-2">
              Backoff Multiplier
            </label>
            <input
              id="retry-backoff"
              type="number"
              min="1"
              step="0.1"
              value={retryBackoff}
              onChange={(e) => {
                const value = parseFloat(e.target.value) || 1.0;
                setRetryBackoff(value);
                if (onRetryConfigUpdate) {
                  onRetryConfigUpdate(retryMaxRetries, retryDelay, value);
                }
              }}
              className="block w-full rounded-md border-gray-300 shadow-sm focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 min-h-[44px]"
              aria-describedby="retry-backoff-help"
            />
            <p id="retry-backoff-help" className="mt-1 text-sm text-gray-500">
              Multiplier for exponential backoff (e.g., 2.0 = double delay each retry)
            </p>
          </div>
        </div>
      )}

      {/* Dependency Configuration */}
      {triggerType !== 'now' && onDependenciesUpdate && (
        <div className="space-y-4 border-t pt-4">
          <DependencySelector
            currentJobId={currentJobId}
            selectedDependencies={dependencies}
            onUpdate={onDependenciesUpdate}
          />
        </div>
      )}

      <div className="flex justify-between">
        <Button variant="secondary" onClick={onBack} className="min-h-[44px] min-w-[120px]">
          Back
        </Button>
        <Button
          onClick={() => {
            handleUpdate();
            onNext();
          }}
          className="min-h-[44px] min-w-[120px]"
        >
          Next
        </Button>
      </div>
    </div>
  );
}

