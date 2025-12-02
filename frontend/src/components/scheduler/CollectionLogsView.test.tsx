import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { CollectionLogsView } from './CollectionLogsView';
import { useCollectionStore } from '@/store/slices/collectionSlice';

// Mock the store
vi.mock('@/store/slices/collectionSlice', () => ({
  useCollectionStore: vi.fn(),
}));

describe('CollectionLogsView', () => {
  const mockFetchCollectionLogs = vi.fn();
  const mockLogs = [
    {
      log_id: 1,
      asset_id: 1,
      collector_type: 'stock',
      start_date: '2024-01-01T00:00:00Z',
      end_date: '2024-12-31T23:59:59Z',
      records_collected: 100,
      status: 'success',
      error_message: null,
      execution_time_ms: 1000,
      created_at: '2024-12-19T10:00:00Z',
    },
    {
      log_id: 2,
      asset_id: 2,
      collector_type: 'crypto',
      start_date: '2024-01-01T00:00:00Z',
      end_date: '2024-12-31T23:59:59Z',
      records_collected: 50,
      status: 'failed',
      error_message: 'API error',
      execution_time_ms: 500,
      created_at: '2024-12-19T11:00:00Z',
    },
    {
      log_id: 3,
      asset_id: 3,
      collector_type: 'forex',
      start_date: '2024-01-01T00:00:00Z',
      end_date: '2024-12-31T23:59:59Z',
      records_collected: 75,
      status: 'partial',
      error_message: null,
      execution_time_ms: 750,
      created_at: '2024-12-19T12:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useCollectionStore).mockReturnValue({
      logs: mockLogs,
      isLoading: false,
      error: null,
      fetchCollectionLogs: mockFetchCollectionLogs,
      activeJobs: {},
    } as any);
  });

  it('renders collection logs table', () => {
    render(<CollectionLogsView />);
    
    expect(screen.getByText('Collection Logs')).toBeInTheDocument();
    expect(screen.getByRole('table', { name: /collection logs table/i })).toBeInTheDocument();
  });

  it('fetches collection logs on mount', () => {
    render(<CollectionLogsView />);
    
    expect(mockFetchCollectionLogs).toHaveBeenCalledWith({ limit: 100 });
  });

  it('displays loading spinner when loading', () => {
    vi.mocked(useCollectionStore).mockReturnValue({
      logs: [],
      isLoading: true,
      error: null,
      fetchCollectionLogs: mockFetchCollectionLogs,
      activeJobs: {},
    } as any);

    render(<CollectionLogsView />);
    
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('displays error message when error occurs', () => {
    vi.mocked(useCollectionStore).mockReturnValue({
      logs: [],
      isLoading: false,
      error: 'Failed to fetch logs',
      fetchCollectionLogs: mockFetchCollectionLogs,
      activeJobs: {},
    } as any);

    render(<CollectionLogsView />);
    
    expect(screen.getByText('Failed to fetch logs')).toBeInTheDocument();
  });

  it('displays all logs when no filter is applied', () => {
    render(<CollectionLogsView />);
    
    expect(screen.getByText('1')).toBeInTheDocument(); // Asset ID
    expect(screen.getByText('stock')).toBeInTheDocument();
    expect(screen.getByText('crypto')).toBeInTheDocument();
    expect(screen.getByText('forex')).toBeInTheDocument();
  });

  it('filters logs by status', async () => {
    const user = userEvent.setup();
    render(<CollectionLogsView />);
    
    const filterSelect = screen.getByLabelText(/filter collection logs by status/i);
    await user.selectOptions(filterSelect, 'success');
    
    await waitFor(() => {
      expect(screen.getByText('stock')).toBeInTheDocument();
      expect(screen.queryByText('crypto')).not.toBeInTheDocument();
      expect(screen.queryByText('forex')).not.toBeInTheDocument();
    });
  });

  it('displays empty message when no logs', () => {
    vi.mocked(useCollectionStore).mockReturnValue({
      logs: [],
      isLoading: false,
      error: null,
      fetchCollectionLogs: mockFetchCollectionLogs,
      activeJobs: {},
    } as any);

    render(<CollectionLogsView />);
    
    expect(screen.getByText('No collection logs found')).toBeInTheDocument();
  });

  it('displays log details correctly', () => {
    render(<CollectionLogsView />);
    
    // Check first log details
    expect(screen.getByText('1')).toBeInTheDocument(); // Asset ID
    expect(screen.getByText('stock')).toBeInTheDocument(); // Collector type
    expect(screen.getByText('100')).toBeInTheDocument(); // Records collected
    expect(screen.getByText('1000ms')).toBeInTheDocument(); // Execution time
  });

  it('displays N/A for missing execution time', () => {
    const logsWithoutTime = [
      {
        ...mockLogs[0],
        execution_time_ms: null,
      },
    ];

    vi.mocked(useCollectionStore).mockReturnValue({
      logs: logsWithoutTime,
      isLoading: false,
      error: null,
      fetchCollectionLogs: mockFetchCollectionLogs,
      activeJobs: {},
    } as any);

    render(<CollectionLogsView />);
    
    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  it('displays status badges correctly', () => {
    render(<CollectionLogsView />);
    
    // Check status badges are rendered
    expect(screen.getByText('success')).toBeInTheDocument();
    expect(screen.getByText('failed')).toBeInTheDocument();
    expect(screen.getByText('partial')).toBeInTheDocument();
  });

  it('has accessible filter select', () => {
    render(<CollectionLogsView />);
    
    const filterSelect = screen.getByLabelText(/filter collection logs by status/i);
    expect(filterSelect).toBeInTheDocument();
    expect(filterSelect).toHaveAttribute('aria-label', 'Filter collection logs by status');
  });

  it('has accessible table', () => {
    render(<CollectionLogsView />);
    
    const table = screen.getByRole('table', { name: /collection logs table/i });
    expect(table).toBeInTheDocument();
    expect(table).toHaveAttribute('aria-label', 'Collection logs table');
  });
});

