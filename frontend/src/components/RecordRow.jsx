import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Check, Lock, Pencil, X } from 'lucide-react'
import { useRecordAction } from '@/api/hooks'
import { AnomalyBadges, StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { TableCell, TableRow } from '@/components/ui/table'
import { useToast } from '@/context/ToastContext'
import { formatDate, formatNumber } from '@/lib/utils'

export function RecordRow({ record, jobId }) {
  const [editing, setEditing] = useState(false)
  const actions = useRecordAction()
  const { toast } = useToast()
  const { register, handleSubmit, reset } = useForm({
    defaultValues: {
      raw_value: record.raw_value,
      raw_unit: record.raw_unit,
      note: '',
    },
  })

  const busy =
    actions.approve.isPending ||
    actions.reject.isPending ||
    actions.lock.isPending ||
    actions.edit.isPending

  const canApprove = record.review_status === 'PENDING' && !record.has_error_flags
  const canLock = record.review_status === 'APPROVED'
  const isLocked = record.review_status === 'LOCKED'

  const runAction = async (fn, successMsg) => {
    try {
      await fn()
      toast(successMsg, 'success')
    } catch (e) {
      toast(e.message, 'error')
    }
  }

  const onEdit = async (data) => {
    await runAction(
      () =>
        actions.edit.mutateAsync({
          id: record.id,
          jobId,
          raw_value: data.raw_value,
          raw_unit: data.raw_unit,
          note: data.note,
        }),
      'Record updated — pending re-review'
    )
    setEditing(false)
  }

  if (editing) {
    return (
      <TableRow className="bg-teal-50/40">
        <TableCell colSpan={9}>
          <form onSubmit={handleSubmit(onEdit)} className="flex flex-wrap items-end gap-3 py-3 px-1">
            <div>
              <label className="text-[10px] font-medium uppercase tracking-wide text-slate-400">
                Raw value
              </label>
              <Input className="mt-1 w-32" {...register('raw_value')} />
            </div>
            <div>
              <label className="text-[10px] font-medium uppercase tracking-wide text-slate-400">
                Unit
              </label>
              <Input className="mt-1 w-24" {...register('raw_unit')} />
            </div>
            <div className="min-w-[200px] flex-1">
              <label className="text-[10px] font-medium uppercase tracking-wide text-slate-400">
                Correction note
              </label>
              <Input className="mt-1" placeholder="Why is this being corrected?" {...register('note')} />
            </div>
            <Button type="submit" size="sm" disabled={busy}>
              Save correction
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                reset()
                setEditing(false)
              }}
            >
              Cancel
            </Button>
          </form>
        </TableCell>
      </TableRow>
    )
  }

  return (
    <TableRow className={record.has_error_flags ? 'bg-red-50/30' : undefined}>
      <TableCell className="whitespace-nowrap text-sm">{formatDate(record.activity_date)}</TableCell>
      <TableCell className="text-xs font-medium text-slate-600">
        {record.source_type.replace(/_/g, ' ')}
      </TableCell>
      <TableCell>
        <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs font-medium">
          S{record.scope}
        </span>
      </TableCell>
      <TableCell className="max-w-[140px] truncate text-xs" title={record.location}>
        {record.location || '—'}
      </TableCell>
      <TableCell className="tabular-nums text-sm">
        {formatNumber(record.raw_value)} <span className="text-slate-400">{record.raw_unit}</span>
      </TableCell>
      <TableCell className="font-semibold tabular-nums text-teal-800">
        {formatNumber(record.normalized_value_kg)}
      </TableCell>
      <TableCell>
        <StatusBadge status={record.review_status} />
        {record.is_edited && (
          <span className="ml-1 text-[10px] font-medium text-amber-600">EDITED</span>
        )}
      </TableCell>
      <TableCell>
        <AnomalyBadges flags={record.anomaly_flags} />
      </TableCell>
      <TableCell>
        <div className="flex gap-1">
          {canApprove && (
            <Button
              size="sm"
              variant="outline"
              title="Approve"
              disabled={busy}
              onClick={() =>
                runAction(
                  () => actions.approve.mutateAsync({ id: record.id, jobId, note: '' }),
                  'Record approved'
                )
              }
            >
              <Check className="h-3.5 w-3.5 text-emerald-600" />
            </Button>
          )}
          {record.review_status === 'PENDING' && (
            <Button
              size="sm"
              variant="outline"
              title="Reject"
              disabled={busy}
              onClick={() =>
                runAction(
                  () => actions.reject.mutateAsync({ id: record.id, jobId, note: '' }),
                  'Record rejected'
                )
              }
            >
              <X className="h-3.5 w-3.5 text-red-600" />
            </Button>
          )}
          {!isLocked && (
            <Button
              size="sm"
              variant="outline"
              title="Edit values"
              disabled={busy}
              onClick={() => setEditing(true)}
            >
              <Pencil className="h-3.5 w-3.5" />
            </Button>
          )}
          {canLock && (
            <Button
              size="sm"
              variant="outline"
              title="Lock for audit (irreversible)"
              disabled={busy}
              onClick={() =>
                runAction(
                  () =>
                    actions.lock.mutateAsync({ id: record.id, jobId, note: 'Audit lock' }),
                  'Record locked for audit'
                )
              }
            >
              <Lock className="h-3.5 w-3.5 text-purple-600" />
            </Button>
          )}
        </div>
      </TableCell>
    </TableRow>
  )
}
