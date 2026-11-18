import React from 'react'
import { Loader2 } from 'lucide-react'

interface LoadingStateProps {
  message?: string
  subtext?: string
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading workspace module...',
  subtext = 'Preparing quantum-classical environment and analytics',
}) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[360px] p-8 text-center" role="status" aria-live="polite">
      <div className="relative flex items-center justify-center mb-4">
        <div className="w-12 h-12 rounded-full border-2 border-scientific-border border-t-scientific-accent animate-spin" />
        <Loader2 className="w-5 h-5 text-scientific-accent absolute animate-pulse" />
      </div>
      <h4 className="text-sm font-medium text-white tracking-tight">{message}</h4>
      <p className="text-xs text-scientific-muted mt-1 max-w-sm">{subtext}</p>
    </div>
  )
}
