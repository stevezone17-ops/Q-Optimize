import React from 'react'
import { cn } from '../../utils/cn'

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = 'text', label, error, helperText, ...props }, ref) => {
    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label className="block text-xs font-medium text-slate-300 font-mono">
            {label}
          </label>
        )}
        <input
          type={type}
          ref={ref}
          className={cn(
            'flex h-9 w-full rounded-lg border border-scientific-border bg-midnight-900/80 px-3 py-1.5 text-sm text-scientific-text placeholder:text-slate-500 shadow-inner focus:outline-none focus:ring-1 focus:ring-scientific-accent focus:border-scientific-accent transition-colors disabled:opacity-50',
            error && 'border-scientific-rose focus:ring-scientific-rose focus:border-scientific-rose',
            className
          )}
          {...props}
        />
        {error && <p className="text-[11px] text-scientific-rose">{error}</p>}
        {!error && helperText && (
          <p className="text-[11px] text-scientific-muted">{helperText}</p>
        )}
      </div>
    )
  }
)
Input.displayName = 'Input'
