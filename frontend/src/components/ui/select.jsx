import { cn } from '@/lib/utils'

export function Select({ className, children, ...props }) {
  return (
    <select
      className={cn(
        'flex h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500',
        className
      )}
      {...props}
    >
      {children}
    </select>
  )
}
