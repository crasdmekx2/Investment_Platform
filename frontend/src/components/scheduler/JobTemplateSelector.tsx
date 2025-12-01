import { useState, useEffect } from 'react';
import { Button } from '@/components/common/Button';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { ErrorMessage } from '@/components/common/ErrorMessage';
import { schedulerApi } from '@/lib/api/scheduler';
import type { JobTemplate, AssetType } from '@/types/scheduler';

interface JobTemplateSelectorProps {
  assetType: AssetType;
  selectedTemplateId: number | null;
  onSelect: (template: JobTemplate | null) => void;
  onNext: () => void;
  onSkip: () => void;
}

export function JobTemplateSelector({
  assetType,
  selectedTemplateId,
  onSelect,
  onNext,
  onSkip,
}: JobTemplateSelectorProps) {
  const [templates, setTemplates] = useState<JobTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTemplates();
  }, [assetType]);

  const loadTemplates = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await schedulerApi.listTemplates({
        asset_type: assetType,
        is_public: true,
      });
      setTemplates(response.data);
    } catch (err) {
      setError('Failed to load templates. Please try again.');
      console.error('Failed to load templates:', err);
    } finally {
      setLoading(false);
    }
  };

  const selectedTemplate = templates.find(t => t.template_id === selectedTemplateId);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Select Template (Optional)</h2>
        <p className="text-gray-600">
          Choose a template to pre-fill job configuration, or skip to create from scratch
        </p>
      </div>

      {error && <ErrorMessage message={error} />}

      {loading && <LoadingSpinner />}

      {!loading && templates.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700">Available Templates</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templates.map((template) => {
              const isSelected = selectedTemplateId === template.template_id;
              return (
                <button
                  key={template.template_id}
                  onClick={() => onSelect(isSelected ? null : template)}
                  className={`
                    p-4 rounded-lg border-2 text-left transition-colors min-h-[120px]
                    ${isSelected
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                    }
                  `}
                  aria-pressed={isSelected}
                >
                  <h3 className="font-semibold text-gray-900 mb-1">{template.name}</h3>
                  {template.description && (
                    <p className="text-sm text-gray-600 mb-2">{template.description}</p>
                  )}
                  <div className="text-xs text-gray-500">
                    {template.trigger_type === 'cron' ? 'Cron' : 'Interval'} schedule
                    {template.symbol && ` • ${template.symbol}`}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {!loading && templates.length === 0 && (
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-md">
          <p className="text-sm text-gray-600">
            No templates available for {assetType}. You can create a job from scratch.
          </p>
        </div>
      )}

      {selectedTemplate && (
        <div className="p-4 bg-primary-50 rounded-md">
          <p className="text-sm font-medium text-gray-700 mb-1">Selected Template:</p>
          <p className="text-lg font-semibold text-gray-900">{selectedTemplate.name}</p>
          {selectedTemplate.description && (
            <p className="text-sm text-gray-600 mt-1">{selectedTemplate.description}</p>
          )}
        </div>
      )}

      <div className="flex justify-between">
        <Button variant="secondary" onClick={onSkip} className="min-h-[44px] min-w-[120px]">
          Skip
        </Button>
        <Button
          onClick={onNext}
          className="min-h-[44px] min-w-[120px]"
        >
          {selectedTemplate ? 'Use Template' : 'Continue'}
        </Button>
      </div>
    </div>
  );
}

