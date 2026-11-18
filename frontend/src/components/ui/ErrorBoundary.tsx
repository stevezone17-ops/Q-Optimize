import { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from './Button'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    if (this.props.onError) {
      this.props.onError(error, errorInfo)
    }
  }

  public handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="p-8 my-6 bg-red-950/20 border border-red-500/30 rounded-xl text-scientific-text max-w-3xl mx-auto space-y-4 shadow-lg backdrop-blur-sm" role="alert">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">Component Render Failure</h3>
              <p className="text-xs text-scientific-muted">
                An isolated exception occurred while rendering this workspace view.
              </p>
            </div>
          </div>

          {this.state.error && (
            <div className="p-3 bg-midnight-950/80 rounded border border-scientific-border font-mono text-xs text-red-300 break-all overflow-x-auto max-h-40">
              {this.state.error.message || String(this.state.error)}
            </div>
          )}

          <div className="flex items-center gap-3 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={this.handleReset}
              leftIcon={<RefreshCw className="h-4 w-4" />}
            >
              Reset Component
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => window.location.reload()}
            >
              Reload Page
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
