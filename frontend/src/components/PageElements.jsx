import { cn } from '@/lib/utils'

export function StatCard({ icon: Icon, label, value, sub, accent = 'teal' }) {
  const accents = {
    teal: 'bg-teal-50 text-teal-700 border-teal-100',
    blue: 'bg-blue-50 text-blue-700 border-blue-100',
    amber: 'bg-amber-50 text-amber-700 border-amber-100',
    red: 'bg-red-50 text-red-700 border-red-100',
    slate: 'bg-slate-50 text-slate-700 border-slate-100',
  }
  return (
    <div className="rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className="mt-1 text-2xl font-bold tracking-tight text-slate-900">{value}</p>
          {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
        </div>
        {Icon && (
          <div className={cn('rounded-lg border p-2.5', accents[accent])}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
    </div>
  )
}

export function Skeleton({ className }) {
  return <div className={cn('skeleton', className)} />
}

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {Icon && (
        <div className="mb-4 rounded-full bg-slate-100 p-4">
          <Icon className="h-8 w-8 text-slate-400" />
        </div>
      )}
      <h3 className="text-lg font-semibold text-slate-700">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function PageHeader({ title, description, action }) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
        {description && (
          <div className="mt-1 text-slate-500">{description}</div>
        )}
      </div>
      {action}
    </div>
  )
}
