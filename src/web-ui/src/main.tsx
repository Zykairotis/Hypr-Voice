import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

// Mock WebSocket polyfill for demo
if (typeof window !== 'undefined' && !window.WebSocket) {
  // This would normally be handled by the browser
  console.warn('WebSocket not supported in this environment');
}

// Mock WebSocket event handling for demo
React.useEffect(() => {
  // Override WebSocket for demo purposes
  const originalWebSocket = window.WebSocket;

  if (process.env.NODE_ENV === 'development') {
    // Only override in development for demo
    window.WebSocket = class MockWebSocket extends EventTarget {
      url: string;
      readyState: number = WebSocket.CONNECTING;
      protocol: string = '';
      extensions: string = '';
      bufferedAmount: number = 0;
      binaryType: BinaryType = 'blob';

      constructor(url: string) {
        super();
        this.url = url;

        // Simulate connection
        setTimeout(() => {
          this.readyState = WebSocket.OPEN;
          this.dispatchEvent(new Event('open'));

          // Listen for mock logs from the app
          window.addEventListener('mock-log', this.handleMockLog);
        }, 100);
      }

      private handleMockLog = (event: CustomEvent) => {
        if (this.readyState === WebSocket.OPEN) {
          const messageEvent = new MessageEvent('message', {
            data: JSON.stringify(event.detail)
          });
          this.dispatchEvent(messageEvent);
        }
      }

      send(data: string) {
        // Mock send - just log to console
        console.log('Mock WebSocket send:', data);
      }

      close(code?: number, reason?: string) {
        this.readyState = WebSocket.CLOSING;
        window.removeEventListener('mock-log', this.handleMockLog);

        setTimeout(() => {
          this.readyState = WebSocket.CLOSED;
          this.dispatchEvent(new CloseEvent('close', { code: code || 1000, reason: reason || '' }));
        }, 10);
      }

      addEventListener(type: string, listener: EventListenerOrEventListenerObject, options?: boolean | AddEventListenerOptions) {
        super.addEventListener(type, listener, options);
      }

      removeEventListener(type: string, listener: EventListenerOrEventListenerObject, options?: boolean | EventListenerOptions) {
        super.removeEventListener(type, listener, options);
      }

      // Static properties
      static CONNECTING = 0;
      static OPEN = 1;
      static CLOSING = 2;
      static CLOSED = 3;
    } as any;
  }

  return () => {
    // Restore original WebSocket on cleanup
    window.WebSocket = originalWebSocket;
  };
}, []);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);