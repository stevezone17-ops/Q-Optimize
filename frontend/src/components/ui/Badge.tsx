import React from 'react'
import { cn } from '../../utils/cn'

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'accent' | 'violet' | 'gold' | 'outline' | 'success' | 'warning' | 'danger'
  size?: 'sm' | 'md'
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'default',
  size = 'md',
  children,
  ...props
}) => {
  const variants = {
    default: 'bg-midnight-800 text-slate-300 border border-scientific-border',
    accent: 'bg-sky-500/10 text-sky-400 border border-sky-500/30',
    violet: 'bg-purple-500/10 text-purple-400 border border-purple-500/30',
    gold: 'bg-amber-500/10 text-amber-400 border border-amber-500/30',
    success: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30',
    warning: 'bg-amber-500/10 text-amber-300 border border-amber-500/30',
    danger: 'bg-rose-500/10 text-rose-400 border border-rose-500/30',
    outline: 'text-scientific-muted border border-scientific-border bg-transparent',
  }

  const sizes = {
    sm: 'text-[10px] font-medium px-2 py-0.5 rounded',
    md: 'text-xs font-medium px-2.5 py-1 rounded-md',
  }

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 transition-colors font-mono',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}
