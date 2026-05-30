import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, CheckCheck, Loader2, AlertTriangle } from 'lucide-react'
import { useJob, useJobRecords, useBulkApprove } from '@/api/hooks'
import { RecordRow } from '@/components/RecordRow'
import { StatusBadge } from '@/components/StatusBadge'
import { StatCard, PageHeader, Skeleton } from '@/components/PageElements'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import {
  Table, TableBody, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import { useToast } from '@/context/ToastContext'

export default function JobDetail() {
  const { jobId } = useParams()
  const { toast } = useToast()
  const { data: job, isLoading: jobLoading } = useJob(jobId)
  const { data: records = [], isLoading: recordsLoading } = useJobRecords(jobId)
  const bulkApprove = useBulkApprove(jobId)

  const handleBulkApprove = async () => {
    try {
      const result = await bulkApprove.mutateAsync()
      toast(`Approved ${result.approved_count} rows`, 'success')
    } catch (e) {
      toast(e.message, 'error')
    }
  }

  if (jobLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-4 sm:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      </div>
    )
  }

  if (!job) return <p className="text-red-600">Job not found</p>

  const isProcessing = job.status === 'PENDING' || job.status === 'PROCESSING'
  const errorFlags = records.filter((r) => r.has_error_flags).length

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-4">
        <Link
          to="/"
          className="mt-1 rounded-lg border border-slate-200 bg-white p-2 text-slate-500 hover:text-teal-700"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <PageHeader
          title={job.original_filename}
          description={
            <span className="flex items-center gap-2">
              {job.source_category} · <StatusBadge status={job.status} />
            </span>
          }
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Rows created" value={job.rows_created} accent="teal" />
        <StatCard label="Anomalies" value={job.anomaly_count ?? '—'} accent="amber" />
        <StatCard label="Pending review" value={job.pending_review_count ?? '—'} accent="blue" />
        <StatCard
          label="Parse errors"
          value={job.error_count}
          accent={job.error_count > 0 ? 'red' : 'slate'}
        />
      </div>

      {isProcessing && (
        <div className="flex items-center gap-3 rounded-xl border border-blue-200 bg-blue-50 px-5 py-4 text-sm text-blue-800">
          <Loader2 className="h-4 w-4 animate-spin" />
          Processing ingestion pipeline — this page refreshes automatically…
        </div>
      )}

      {job.status === 'DONE' && (
        <div className="flex flex-wrap items-center gap-3">
          <Button onClick={handleBulkApprove} disabled={bulkApprove.isPending}>
            <CheckCheck className="mr-2 h-4 w-4" />
            Bulk approve non-flagged rows
          </Button>
          {errorFlags > 0 && (
            <span className="flex items-center gap-1 text-sm text-amber-700">
              <AlertTriangle className="h-4 w-4" />
              {errorFlags} rows have ERROR flags and cannot be bulk-approved
            </span>
          )}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Emission records</CardTitle>
          <CardDescription>
            Review each row — approve clean data, edit corrections, lock approved rows for audit
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {recordsLoading ? (
            <div className="space-y-2 p-6">
              {[...Array(8)].map((_, i) => (
                <Skeleton key={i} className="h-10" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50/80">
                    <TableHead>Date</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Scope</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Raw value</TableHead>
                    <TableHead>kgCO₂e</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Flags</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {records.map((r) => (
                    <RecordRow key={r.id} record={r} jobId={jobId} />
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {job.error_log?.length > 0 && (
        <Card className="border-red-200">
          <CardHeader>
            <CardTitle className="text-base text-red-700">Parse error log</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="max-h-48 space-y-1 overflow-auto font-mono text-xs text-slate-600">
              {job.error_log.map((e, i) => (
                <li key={i} className="rounded bg-red-50 px-2 py-1">
                  Row {e.row}: {e.message}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
