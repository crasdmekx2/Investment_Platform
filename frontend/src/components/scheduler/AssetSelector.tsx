import { useState, useEffect } from 'react';
import { Button } from '@/components/common/Button';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { collectorsApi } from '@/lib/api/scheduler';
import { useDebounce } from '@/hooks/useDebounce';
import type { AssetType, AssetOption } from '@/types/scheduler';

interface AssetSelectorProps {
  assetType: AssetType;
  selected: string | string[];
  onSelect: (symbol: string | string[]) => void;
  onBack: () => void;
  onNext: () => void;
  bulkMode?: boolean;
}

export function AssetSelector({ assetType, selected, onSelect, onBack, onNext, bulkMode = false }: AssetSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [options, setOptions] = useState<AssetOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [isBulkMode, setIsBulkMode] = useState(bulkMode);
  const debouncedQuery = useDebounce(searchQuery, 300);
  
  const selectedArray = Array.isArray(selected) ? selected : (selected ? [selected] : []);

  useEffect(() => {
    // Only search if we have a query and assetType is set
    if (!assetType) {
      setOptions([]);
      setLoading(false);
      return;
    }

    const trimmedQuery = debouncedQuery.trim();
    if (trimmedQuery.length >= 1) {
      setLoading(true);
      let cancelled = false;
      
      // Debug log to verify API call is being made
      console.log(`Searching for ${assetType} with query: "${trimmedQuery}"`);
      
      collectorsApi
        .search(assetType, trimmedQuery)
        .then((response) => {
          if (!cancelled) {
            console.log(`Search results for "${trimmedQuery}":`, response.data);
            setOptions(response.data || []);
            setLoading(false);
          }
        })
        .catch((error) => {
          if (!cancelled) {
            console.error('Asset search failed:', error);
            setOptions([]);
            setLoading(false);
          }
        });
      
      // Cleanup function to cancel request if component unmounts or dependencies change
      return () => {
        cancelled = true;
      };
    } else {
      setOptions([]);
      setLoading(false);
    }
  }, [debouncedQuery, assetType]);

  const handleSelect = (symbol: string) => {
    if (isBulkMode) {
      const currentSelected = selectedArray;
      const newSelected = currentSelected.includes(symbol)
        ? currentSelected.filter(s => s !== symbol)
        : [...currentSelected, symbol];
      onSelect(newSelected);
    } else {
      onSelect(symbol);
    }
  };

  const isSelected = (symbol: string) => {
    return selectedArray.includes(symbol);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Select Asset{isBulkMode ? 's' : ''}</h2>
        <p className="text-gray-600">
          {isBulkMode 
            ? 'Search and select multiple assets to create jobs for'
            : 'Search and select the asset to collect data for'}
        </p>
      </div>

      {/* Bulk mode toggle */}
      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id="bulk-mode"
          checked={isBulkMode}
          onChange={(e) => {
            setIsBulkMode(e.target.checked);
            if (!e.target.checked) {
              // Switch to single mode - keep first selected or clear
              onSelect(selectedArray[0] || '');
            }
          }}
          className="w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          aria-describedby="bulk-mode-help"
        />
        <label htmlFor="bulk-mode" className="text-sm font-medium text-gray-700 cursor-pointer min-h-[44px] flex items-center">
          Enable bulk selection (select multiple assets)
        </label>
      </div>
      <p id="bulk-mode-help" className="sr-only">
        When enabled, you can select multiple assets to create jobs for all of them at once
      </p>

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
                onClick={() => handleSelect(option.symbol)}
                className={`
                  w-full p-3 rounded-md text-left transition-colors min-h-[44px]
                  flex items-center space-x-3
                  focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                  ${isSelected(option.symbol)
                    ? 'bg-primary-50 border-2 border-primary-500'
                    : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
                  }
                `}
                aria-pressed={isSelected(option.symbol)}
                aria-label={`${isSelected(option.symbol) ? 'Deselect' : 'Select'} ${option.symbol} - ${option.name}`}
              >
                {isBulkMode && (
                  <input
                    type="checkbox"
                    checked={isSelected(option.symbol)}
                    onChange={() => handleSelect(option.symbol)}
                    className="w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                    onClick={(e) => e.stopPropagation()}
                    aria-label={`Select ${option.symbol}`}
                  />
                )}
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{option.symbol}</div>
                  <div className="text-sm text-gray-600">{option.name}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {selectedArray.length > 0 && (
        <div className="p-4 bg-primary-50 rounded-md">
          <p className="text-sm font-medium text-gray-700 mb-2">
            Selected {isBulkMode ? `(${selectedArray.length})` : ''}:
          </p>
          {isBulkMode ? (
            <div className="flex flex-wrap gap-2">
              {selectedArray.map((symbol) => (
                <span
                  key={symbol}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-primary-600 text-white"
                >
                  {symbol}
                  <button
                    onClick={() => handleSelect(symbol)}
                    className="ml-2 text-primary-200 hover:text-white focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-primary-600 rounded min-h-[44px] min-w-[44px] flex items-center justify-center"
                    aria-label={`Remove ${symbol}`}
                  >
                    <span aria-hidden="true">×</span>
                  </button>
                </span>
              ))}
            </div>
          ) : (
            <p className="text-lg font-semibold text-gray-900">{selectedArray[0]}</p>
          )}
        </div>
      )}

      <div className="flex justify-between">
        <Button variant="secondary" onClick={onBack} className="min-h-[44px] min-w-[120px]">
          Back
        </Button>
        <Button
          onClick={onNext}
          disabled={selectedArray.length === 0}
          className="min-h-[44px] min-w-[120px]"
        >
          Next
        </Button>
      </div>
    </div>
  );
}

