import { useState, useEffect } from 'react';
import { Button } from '@/components/common/Button';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { collectorsApi } from '@/lib/api/scheduler';
import { useDebounce } from '@/hooks/useDebounce';
import type { AssetType, AssetOption } from '@/types/scheduler';

interface AssetSelectorProps {
  assetType: AssetType;
  selected: string;
  onSelect: (symbol: string) => void;
  onBack: () => void;
  onNext: () => void;
}

export function AssetSelector({ assetType, selected, onSelect, onBack, onNext }: AssetSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [options, setOptions] = useState<AssetOption[]>([]);
  const [loading, setLoading] = useState(false);
  const debouncedQuery = useDebounce(searchQuery, 300);

  useEffect(() => {
    if (debouncedQuery.length >= 1) {
      setLoading(true);
      collectorsApi
        .search(assetType, debouncedQuery)
        .then((response) => {
          setOptions(response.data);
          setLoading(false);
        })
        .catch(() => {
          setOptions([]);
          setLoading(false);
        });
    } else {
      setOptions([]);
    }
  }, [debouncedQuery, assetType]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Select Asset</h2>
        <p className="text-gray-600">Search and select the asset to collect data for</p>
      </div>

      <div>
        <label htmlFor="asset-search" className="block text-sm font-medium text-gray-700 mb-2">
          Search {assetType}
        </label>
        <input
          id="asset-search"
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Enter symbol or name..."
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 min-h-[44px]"
          aria-label="Search for asset"
        />
      </div>

      {loading && <LoadingSpinner />}

      {options.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700">Search Results</p>
          <div className="space-y-1">
            {options.map((option) => (
              <button
                key={option.symbol}
                onClick={() => onSelect(option.symbol)}
                className={`
                  w-full p-3 rounded-md text-left transition-colors min-h-[44px]
                  ${selected === option.symbol
                    ? 'bg-primary-50 border-2 border-primary-500'
                    : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
                  }
                `}
                aria-pressed={selected === option.symbol}
              >
                <div className="font-medium text-gray-900">{option.symbol}</div>
                <div className="text-sm text-gray-600">{option.name}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {selected && (
        <div className="p-4 bg-primary-50 rounded-md">
          <p className="text-sm font-medium text-gray-700">Selected:</p>
          <p className="text-lg font-semibold text-gray-900">{selected}</p>
        </div>
      )}

      <div className="flex justify-between">
        <Button variant="secondary" onClick={onBack} className="min-h-[44px] min-w-[120px]">
          Back
        </Button>
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

