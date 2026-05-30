import { Badge } from '@/components/ui/badge'
import { statusColor } from '@/lib/utils'
import { cn } from '@/lib/utils'

export function StatusBadge({ status }) {
  return (
    <span
      className={cn(
        'inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium',
        statusColor(status)
      )}
    >
      {status}
    </span>
  )
}

export function AnomalyBadges({ flags = [] }) {
  if (!flags.length) return <span className="text-slate-400 text-xs">—</span>
  return (
    <div className="flex flex-wrap gap-1">
      {flags.map((f) => (
        <Badge
          key={f.id}
          variant={f.severity === 'ERROR' ? 'error' : 'warning'}
          title={f.message}
        >
          {f.flag_type}
        </Badge>
      ))}
    </div>
  )
}
