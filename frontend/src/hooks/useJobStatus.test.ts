import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useJobStatus } from './useJobStatus';
import { useWebSocket } from './useWebSocket';
import { useCollectionStore } from '@/store/slices/collectionSlice';

// Mock dependencies
vi.mock('./useWebSocket');
vi.mock('@/store/slices/collectionSlice');

describe('useJobStatus', () => {
  const mockUpdateActiveJob = vi.fn();
  const mockOnMessage = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useCollectionStore).mockReturnValue({
      updateActiveJob: mockUpdateActiveJob,
    } as any);
    vi.mocked(useWebSocket).mockReturnValue({
      isConnected: true,
      connect: vi.fn(),
      disconnect: vi.fn(),
      send: vi.fn(),
    } as any);
  });

  it('connects to WebSocket with scheduler endpoint', () => {
    renderHook(() => useJobStatus());

    expect(useWebSocket).toHaveBeenCalledWith(
      expect.objectContaining({
        url: expect.stringContaining('/scheduler'),
        autoConnect: true,
      })
    );
  });

  it('updates job status when job_update message is received', () => {
    let messageHandler: ((data: unknown) => void) | undefined;

    vi.mocked(useWebSocket).mockImplementation((config) => {
      messageHandler = config.onMessage;
      return {
        isConnected: true,
        connect: vi.fn(),
        disconnect: vi.fn(),
        send: vi.fn(),
      } as any;
    });

    renderHook(() => useJobStatus('job_123'));

    // Simulate job update message
    if (messageHandler) {
      messageHandler({
        type: 'job_update',
        job_id: 'job_123',
        status: 'running',
        records_loaded: 100,
      });
    }

    expect(mockUpdateActiveJob).toHaveBeenCalledWith('job_123', {
      status: 'running',
      records_loaded: 100,
    });
  });

  it('filters job updates by jobId when provided', () => {
    let messageHandler: ((data: unknown) => void) | undefined;

    vi.mocked(useWebSocket).mockImplementation((config) => {
      messageHandler = config.onMessage;
      return {
        isConnected: true,
        connect: vi.fn(),
        disconnect: vi.fn(),
        send: vi.fn(),
      } as any;
    });

    renderHook(() => useJobStatus('job_123'));

    // Simulate job update for different job
    if (messageHandler) {
      messageHandler({
        type: 'job_update',
        job_id: 'job_456',
        status: 'running',
        records_loaded: 50,
      });
    }

    // Should not update since jobId doesn't match
    expect(mockUpdateActiveJob).not.toHaveBeenCalled();
  });

  it('processes all job updates when jobId is not provided', () => {
    let messageHandler: ((data: unknown) => void) | undefined;

    vi.mocked(useWebSocket).mockImplementation((config) => {
      messageHandler = config.onMessage;
      return {
        isConnected: true,
        connect: vi.fn(),
        disconnect: vi.fn(),
        send: vi.fn(),
      } as any;
    });

    renderHook(() => useJobStatus());

    // Simulate job update
    if (messageHandler) {
      messageHandler({
        type: 'job_update',
        job_id: 'job_123',
        status: 'running',
        records_loaded: 100,
      });
    }

    expect(mockUpdateActiveJob).toHaveBeenCalledWith('job_123', {
      status: 'running',
      records_loaded: 100,
    });
  });

  it('handles string message format', () => {
    let messageHandler: ((data: unknown) => void) | undefined;

    vi.mocked(useWebSocket).mockImplementation((config) => {
      messageHandler = config.onMessage;
      return {
        isConnected: true,
        connect: vi.fn(),
        disconnect: vi.fn(),
        send: vi.fn(),
      } as any;
    });

    renderHook(() => useJobStatus());

    // Simulate string message
    if (messageHandler) {
      messageHandler(JSON.stringify({
        type: 'job_update',
        job_id: 'job_123',
        status: 'completed',
        records_loaded: 200,
      }));
    }

    expect(mockUpdateActiveJob).toHaveBeenCalledWith('job_123', {
      status: 'completed',
      records_loaded: 200,
    });
  });

  it('handles invalid message gracefully', () => {
    let messageHandler: ((data: unknown) => void) | undefined;
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    vi.mocked(useWebSocket).mockImplementation((config) => {
      messageHandler = config.onMessage;
      return {
        isConnected: true,
        connect: vi.fn(),
        disconnect: vi.fn(),
        send: vi.fn(),
      } as any;
    });

    renderHook(() => useJobStatus());

    // Simulate invalid message
    if (messageHandler) {
      messageHandler('invalid json');
    }

    expect(consoleErrorSpy).toHaveBeenCalled();
    expect(mockUpdateActiveJob).not.toHaveBeenCalled();

    consoleErrorSpy.mockRestore();
  });

  it('returns connection status', () => {
    vi.mocked(useWebSocket).mockReturnValue({
      isConnected: true,
      connect: vi.fn(),
      disconnect: vi.fn(),
      send: vi.fn(),
    } as any);

    const { result } = renderHook(() => useJobStatus());

    expect(result.current.connected).toBe(true);
  });

  it('ignores non-job_update messages', () => {
    let messageHandler: ((data: unknown) => void) | undefined;

    vi.mocked(useWebSocket).mockImplementation((config) => {
      messageHandler = config.onMessage;
      return {
        isConnected: true,
        connect: vi.fn(),
        disconnect: vi.fn(),
        send: vi.fn(),
      } as any;
    });

    renderHook(() => useJobStatus());

    // Simulate non-job_update message
    if (messageHandler) {
      messageHandler({
        type: 'other_message',
        data: 'some data',
      });
    }

    expect(mockUpdateActiveJob).not.toHaveBeenCalled();
  });
});

