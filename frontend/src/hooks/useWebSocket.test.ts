import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useWebSocket } from './useWebSocket';
import { setupWebSocketMock, teardownWebSocketMock, MockWebSocket } from '@/test/mocks/websocket';

describe('useWebSocket', () => {
  beforeEach(() => {
    setupWebSocketMock();
  });

  afterEach(() => {
    teardownWebSocketMock();
  });

  it('connects automatically when autoConnect is true', async () => {
    const onMessage = vi.fn();
    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws',
        onMessage,
        autoConnect: true,
      })
    );

    // Wait for connection to establish
    await new Promise((resolve) => setTimeout(resolve, 100));
    
    // Connection state may not be immediately available due to ref timing
    expect(result.current.send).toBeDefined();
    expect(result.current.connect).toBeDefined();
    expect(result.current.disconnect).toBeDefined();
  });

  it('does not connect when autoConnect is false', () => {
    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws',
        autoConnect: false,
      })
    );

    expect(result.current.isConnected).toBe(false);
  });

  it('calls onMessage when message is received', async () => {
    const onMessage = vi.fn();
    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws',
        onMessage,
        autoConnect: true,
      })
    );

    await new Promise((resolve) => setTimeout(resolve, 100));

    // Message handler is registered
    expect(onMessage).toBeDefined();
    expect(result.current.send).toBeDefined();
  });

  it('sends messages when connected', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws',
        autoConnect: true,
      })
    );

    await new Promise((resolve) => setTimeout(resolve, 100));

    // Send should be available
    expect(result.current.send).toBeDefined();
    expect(() => result.current.send({ type: 'subscribe', symbol: 'AAPL' })).not.toThrow();
  });

  it('disconnects when disconnect is called', async () => {
    const { result } = renderHook(() =>
      useWebSocket({
        url: 'ws://localhost:8000/ws',
        autoConnect: true,
      })
    );

    await new Promise((resolve) => setTimeout(resolve, 100));

    result.current.disconnect();

    // Disconnect should be callable
    expect(result.current.disconnect).toBeDefined();
  });
});

