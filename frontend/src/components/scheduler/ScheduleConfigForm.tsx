import { useState } from 'react';
import { Button } from '@/components/common/Button';
import type { TriggerConfig, CronTriggerConfig, IntervalTriggerConfig } from '@/types/scheduler';

interface ScheduleConfigFormProps {
  triggerConfig: TriggerConfig | null;
  onUpdate: (config: TriggerConfig) => void;
  onBack: () => void;
  onNext: () => void;
}

export function ScheduleConfigForm({ triggerConfig, onUpdate, onBack, onNext }: ScheduleConfigFormProps) {
  const [triggerType, setTriggerType] = useState<'cron' | 'interval'>(
    triggerConfig?.type || 'interval'
  );
  const [cronConfig, setCronConfig] = useState<CronTriggerConfig>(
    (triggerConfig as CronTriggerConfig) || {
      type: 'cron',
      minute: '0',
      hour: '9',
      second: '0',
    }
  );
  const [intervalConfig, setIntervalConfig] = useState<IntervalTriggerConfig>(
    (triggerConfig as IntervalTriggerConfig) || {
      type: 'interval',
      hours: 1,
    }
  );

  const handleUpdate = () => {
    if (triggerType === 'cron') {
      onUpdate(cronConfig);
    } else {
      onUpdate(intervalConfig);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Schedule Configuration</h2>
        <p className="text-gray-600">Configure when the job should run</p>
      </div>

      {/* Trigger Type Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Trigger Type</label>
        <div className="flex gap-4">
          <label className="flex items-center space-x-2 cursor-pointer min-h-[44px]">
            <input
              type="radio"
              name="trigger-type"
              value="interval"
              checked={triggerType === 'interval'}
              onChange={() => setTriggerType('interval')}
              className="w-5 h-5 text-primary-600 border-gray-300 focus:ring-primary-500"
            />
            <span className="text-sm font-medium text-gray-700">Interval</span>
          </label>
          <label className="flex items-center space-x-2 cursor-pointer min-h-[44px]">
            <input
              type="radio"
              name="trigger-type"
              value="cron"
              checked={triggerType === 'cron'}
              onChange={() => setTriggerType('cron')}
              className="w-5 h-5 text-primary-600 border-gray-300 focus:ring-primary-500"
            />
            <span className="text-sm font-medium text-gray-700">Cron Schedule</span>
          </label>
        </div>
      </div>

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
              onChange={(e) =>
                setIntervalConfig({ ...intervalConfig, hours: parseInt(e.target.value) || 0 })
              }
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 min-h-[44px]"
            />
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
              onChange={(e) =>
                setIntervalConfig({ ...intervalConfig, minutes: parseInt(e.target.value) || 0 })
              }
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 min-h-[44px]"
            />
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
              onChange={(e) => setCronConfig({ ...cronConfig, hour: e.target.value })}
              placeholder="9"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 min-h-[44px]"
            />
          </div>
          <div>
            <label htmlFor="cron-minute" className="block text-sm font-medium text-gray-700 mb-2">
              Minute (0-59)
            </label>
            <input
              id="cron-minute"
              type="text"
              value={cronConfig.minute || ''}
              onChange={(e) => setCronConfig({ ...cronConfig, minute: e.target.value })}
              placeholder="0"
              className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 min-h-[44px]"
            />
          </div>
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

