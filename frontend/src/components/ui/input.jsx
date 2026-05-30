import { cn } from '@/lib/utils'

export function Input({ className, ...props }) {
  return (
    <input
      className={cn(
        'flex h-9 w-full rounded-md border border-slate-200 bg-white px-3 py-1 text-sm shadow-sm placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500',
        className
      )}
      {...props}
    />
  )
}
