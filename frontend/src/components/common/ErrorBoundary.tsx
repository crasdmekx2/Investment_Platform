import { Component, ReactNode, ErrorInfo } from 'react';
import { ErrorMessage } from './ErrorMessage';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary component to catch and handle React component errors.
 * 
 * This component catches errors in the component tree and displays
 * a user-friendly error message instead of crashing the entire app.
 * 
 * Features:
 * - Catches errors in child components
 * - Logs errors for debugging
 * - Displays user-friendly error UI
 * - Provides error recovery options
 * 
 * Usage:
 * ```tsx
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Call optional error handler (e.g., for error reporting service)
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // TODO: In production, send error to error reporting service
    // Example: Sentry.captureException(error, { contexts: { react: errorInfo } });
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Use custom fallback if provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center p-4">
          <div className="max-w-md w-full">
            <ErrorMessage
              title="Something went wrong"
              message={
                this.state.error?.message ||
                'An unexpected error occurred. Please try refreshing the page.'
              }
              onRetry={this.handleReset}
              actions={
                <button
                  onClick={() => window.location.reload()}
                  className="text-sm font-medium text-danger-800 hover:text-danger-900 underline focus:outline-none focus:ring-2 focus:ring-danger-500 focus:ring-offset-2 rounded min-h-[44px] min-w-[44px] px-2"
                  aria-label="Reload page"
                >
                  Reload Page
                </button>
              }
            />
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

