import { useEffect, useRef, useCallback } from 'react';
import { WebSocketClient } from '@/lib/websocket/websocketClient';

interface UseWebSocketOptions {
  url: string;
  onMessage?: (data: unknown) => void;
  onError?: (error: Event) => void;
  onClose?: () => void;
  autoConnect?: boolean;
}

export function useWebSocket(options: UseWebSocketOptions) {
  const { url, onMessage, onError, onClose, autoConnect = true } = options;
  const wsClientRef = useRef<WebSocketClient | null>(null);
  const handlersRef = useRef<{
    message?: (data: unknown) => void;
    error?: (error: Event) => void;
    close?: () => void;
  }>({});

  // Update handlers ref when callbacks change
  handlersRef.current = { message: onMessage, error: onError, close: onClose };

  useEffect(() => {
    if (!autoConnect) return;

    const wsUrl = import.meta.env.VITE_WS_URL || url;
    const client = new WebSocketClient(wsUrl);

    // Set up handlers
    if (handlersRef.current.message) {
      client.onMessage(handlersRef.current.message);
    }
    if (handlersRef.current.error) {
      client.onError(handlersRef.current.error);
    }
    if (handlersRef.current.close) {
      client.onClose(handlersRef.current.close);
    }

    wsClientRef.current = client;
    client.connect();

    return () => {
      client.disconnect();
    };
  }, [url, autoConnect]);

  const send = useCallback((data: unknown) => {
    wsClientRef.current?.send(data);
  }, []);

  const connect = useCallback(() => {
    wsClientRef.current?.connect();
  }, []);

  const disconnect = useCallback(() => {
    wsClientRef.current?.disconnect();
  }, []);

  return {
    send,
    connect,
    disconnect,
    isConnected: wsClientRef.current?.isConnected ?? false,
    readyState: wsClientRef.current?.readyState ?? WebSocket.CLOSED,
  };
}

