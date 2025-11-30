import { useEffect } from 'react';
import { useWebSocket } from './useWebSocket';
import { useCollectionStore } from '@/store/slices/collectionSlice';

/**
 * Hook for real-time job status updates via WebSocket
 */
export function useJobStatus(jobId?: string) {
  const { updateActiveJob } = useCollectionStore();
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
  
  const { isConnected } = useWebSocket({
    url: `${wsUrl}/scheduler`,
    autoConnect: true,
    onMessage: (data) => {
      try {
        const message = typeof data === 'string' ? JSON.parse(data) : data;
        
        if (message.type === 'job_update' && (!jobId || message.job_id === jobId)) {
          // Update job status
          if (message.job_id) {
            updateActiveJob(message.job_id, {
              status: message.status,
              records_loaded: message.records_loaded,
            });
          }
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    },
  });
  
  return { connected: isConnected };
}

