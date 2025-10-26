'use client';

import React from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error?: Error; errorInfo?: React.ErrorInfo; onReset?: () => void }>;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ error, errorInfo });
    this.props.onError?.(error, errorInfo);

    // Log error to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('ErrorBoundary caught an error:', error, errorInfo);
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      const { fallback: Fallback } = this.props;

      if (Fallback) {
        return (
          <Fallback
            error={this.state.error}
            errorInfo={this.state.errorInfo}
            onReset={this.handleReset}
          />
        );
      }

      return <DefaultErrorFallback error={this.state.error} onReset={this.handleReset} />;
    }

    return this.props.children;
  }
}

interface DefaultErrorFallbackProps {
  error?: Error;
  onReset?: () => void;
}

function DefaultErrorFallback({ error, onReset }: DefaultErrorFallbackProps) {
  return (
    <div className="min-h-[400px] flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 bg-red-100 dark:bg-red-900 rounded-full flex items-center justify-center mb-4">
            <AlertTriangle className="h-6 w-6 text-red-600" />
          </div>
          <CardTitle className="text-red-800 dark:text-red-200">
            Something went wrong
          </CardTitle>
          <CardDescription>
            An unexpected error occurred while rendering this component.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {process.env.NODE_ENV === 'development' && error && (
            <Alert className="border-red-200 bg-red-50 dark:bg-red-950/20">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <div className="font-medium mb-1">Error Details:</div>
                <div className="text-xs font-mono bg-background p-2 rounded border">
                  {error.message}
                </div>
                {error.stack && (
                  <details className="mt-2">
                    <summary className="text-xs cursor-pointer">Stack trace</summary>
                    <pre className="text-xs mt-1 whitespace-pre-wrap font-mono bg-background p-2 rounded border">
                      {error.stack}
                    </pre>
                  </details>
                )}
              </AlertDescription>
            </Alert>
          )}

          <div className="flex gap-2">
            <Button onClick={onReset} className="flex-1">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
            <Button
              variant="outline"
              onClick={() => window.location.reload()}
            >
              Reload Page
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Hook for handling async errors in function components
export function useErrorHandler() {
  return React.useCallback((error: Error, errorInfo?: React.ErrorInfo) => {
    console.error('Async error caught:', error, errorInfo);
    // You can also send this to an error reporting service
  }, []);
}

// Component for handling loading and error states
interface AsyncStateProps {
  loading?: boolean;
  error?: Error | null;
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error?: Error; onRetry?: () => void }>;
  loadingComponent?: React.ComponentType;
  onRetry?: () => void;
}

export function AsyncState({
  loading = false,
  error = null,
  children,
  fallback: Fallback,
  loadingComponent: LoadingComponent,
  onRetry,
}: AsyncStateProps) {
  if (loading) {
    return LoadingComponent ? <LoadingComponent /> : <LoadingSpinner />;
  }

  if (error) {
    if (Fallback) {
      return <Fallback error={error} onRetry={onRetry} />;
    }
    return <ErrorFallback error={error} onRetry={onRetry} />;
  }

  return <>{children}</>;
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
    </div>
  );
}

interface ErrorFallbackProps {
  error?: Error;
  onRetry?: () => void;
}

function ErrorFallback({ error, onRetry }: ErrorFallbackProps) {
  return (
    <Alert className="border-red-200 bg-red-50 dark:bg-red-950/20">
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription>
        <div className="font-medium mb-1">Something went wrong</div>
        <div className="text-sm mb-2">{error?.message || 'An unexpected error occurred'}</div>
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry} className="mt-2">
            <RefreshCw className="h-4 w-4 mr-1" />
            Try Again
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}