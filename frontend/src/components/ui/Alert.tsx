import React from 'react'
import { cn } from '../../utils/cn'
import { AlertCircle, AlertTriangle, CheckCircle2, Info } from 'lucide-react'

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'warning' | 'error' | 'success'
  title?: string
}

export const Alert: React.FC<AlertProps> = ({
  className,
  variant = 'info',
  title,
  children,
  ...props
}) => {
  const styles = {
    info: {
      container: 'border-sky-500/30 bg-sky-950/20 text-sky-200',
      icon: <Info className="h-4 w-4 text-sky-400 shrink-0 mt-0.5" />,
      titleColor: 'text-sky-300',
    },
    warning: {
      container: 'border-amber-500/30 bg-amber-950/20 text-amber-200',
      icon: <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />,
      titleColor: 'text-amber-300',
    },
    error: {
      container: 'border-rose-500/30 bg-rose-950/20 text-rose-200',
      icon: <AlertCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />,
      titleColor: 'text-rose-300',
    },
    success: {
      container: 'border-emerald-500/30 bg-emerald-950/20 text-emerald-200',
      icon: <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />,
      titleColor: 'text-emerald-300',
    },
  }

  const current = styles[variant]

  return (
    <div
      role="alert"
      className={cn(
        'flex gap-3 p-3.5 rounded-lg border text-xs leading-relaxed',
        current.container,
        className
      )}
      {...props}
    >
      {current.icon}
      <div className="flex-1 space-y-1">
        {title && <h5 className={cn('font-semibold', current.titleColor)}>{title}</h5>}
        <div className="opacity-90">{children}</div>
      </div>
    </div>
  )
}
