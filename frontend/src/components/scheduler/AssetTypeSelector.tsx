import { Button } from '@/components/common/Button';
import type { AssetType, CollectorMetadata } from '@/types/scheduler';
import { getAssetTypeDisplayName, getAssetTypeDescription } from '@/lib/utils/collectors';

interface AssetTypeSelectorProps {
  metadata: CollectorMetadata | null;
  selected: AssetType | null;
  onSelect: (type: AssetType) => void;
  onNext: () => void;
}

const ASSET_TYPES: AssetType[] = [
  'stock',
  'crypto',
  'forex',
  'bond',
  'commodity',
  'economic_indicator',
];

export function AssetTypeSelector({ metadata, selected, onSelect, onNext }: AssetTypeSelectorProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Select Asset Type</h2>
        <p className="text-gray-600">Choose the type of data you want to collect</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {ASSET_TYPES.map((type) => {
          const typeMetadata = metadata?.[type];
          const isSelected = selected === type;

          return (
            <button
              key={type}
              onClick={() => onSelect(type)}
              className={`
                p-4 rounded-lg border-2 text-left transition-colors min-h-[120px]
                focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                ${isSelected
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
                }
              `}
              aria-pressed={isSelected}
              aria-label={`Select ${getAssetTypeDisplayName(type)} asset type`}
            >
              <h3 className="font-semibold text-gray-900 mb-1">
                {getAssetTypeDisplayName(type)}
              </h3>
              <p className="text-sm text-gray-600">
                {typeMetadata?.description || getAssetTypeDescription(type)}
              </p>
            </button>
          );
        })}
      </div>

      <div className="flex justify-end">
        <Button
          onClick={onNext}
          disabled={!selected}
          className="min-h-[44px] min-w-[120px]"
        >
          Next
        </Button>
      </div>
    </div>
  );
}

