// Mock WebSocket for testing
export class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState: number = MockWebSocket.CONNECTING;
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;

  private messageQueue: string[] = [];
  private shouldAutoConnect = true;

  constructor(url: string) {
    this.url = url;
    if (this.shouldAutoConnect) {
      setTimeout(() => this.connect(), 0);
    }
  }

  connect(): void {
    this.readyState = MockWebSocket.OPEN;
    if (this.onopen) {
      this.onopen(new Event('open'));
    }
    // Send queued messages
    this.messageQueue.forEach((msg) => {
      if (this.onmessage) {
        this.onmessage(new MessageEvent('message', { data: msg }));
      }
    });
    this.messageQueue = [];
  }

  send(data: string): void {
    if (this.readyState === MockWebSocket.OPEN) {
      // Message sent successfully
    } else if (this.readyState === MockWebSocket.CONNECTING) {
      this.messageQueue.push(data);
    } else {
      throw new Error('WebSocket is not open');
    }
  }

  close(): void {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }

  // Test helpers
  simulateMessage(data: unknown): void {
    const message = typeof data === 'string' ? data : JSON.stringify(data);
    if (this.onmessage) {
      this.onmessage(new MessageEvent('message', { data: message }));
    }
  }

  simulateError(): void {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }

  simulateClose(): void {
    this.close();
  }
}

// Replace global WebSocket with mock during tests
export function setupWebSocketMock(): void {
  global.WebSocket = MockWebSocket as unknown as typeof WebSocket;
}

export function teardownWebSocketMock(): void {
  delete (global as { WebSocket?: unknown }).WebSocket;
}

