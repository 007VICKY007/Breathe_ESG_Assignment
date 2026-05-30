import { cn } from '@/lib/utils'

export function Card({ className, ...props }) {
  return (
    <div
      className={cn('rounded-lg border border-slate-200 bg-white shadow-sm', className)}
      {...props}
    />
  )
}

export function CardHeader({ className, ...props }) {
  return <div className={cn('flex flex-col gap-1 p-6 pb-2', className)} {...props} />
}

export function CardTitle({ className, ...props }) {
  return <h3 className={cn('text-lg font-semibold', className)} {...props} />
}

export function CardDescription({ className, ...props }) {
  return <p className={cn('text-sm text-slate-500', className)} {...props} />
}

export function CardContent({ className, ...props }) {
  return <div className={cn('p-6 pt-2', className)} {...props} />
}
