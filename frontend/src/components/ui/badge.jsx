import { cn } from '@/lib/utils'

export function Badge({ className, variant = 'default', ...props }) {
  const variants = {
    default: 'bg-slate-100 text-slate-700',
    error: 'bg-red-100 text-red-800',
    warning: 'bg-amber-100 text-amber-800',
    success: 'bg-emerald-100 text-emerald-800',
  }
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        variants[variant] || variants.default,
        className
      )}
      {...props}
    />
  )
}
