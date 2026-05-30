import { Trash2, RotateCcw } from 'lucide-react'
import { isJobStale, useDeleteJob, useRetryJob } from '@/api/hooks'
import { Button } from '@/components/ui/button'
import { useToast } from '@/context/ToastContext'

export function JobActions({ job, onDeleted }) {
  const deleteJob = useDeleteJob()
  const retryJob = useRetryJob()
  const { toast } = useToast()
  const stale = isJobStale(job)

  const handleDelete = async () => {
    if (!window.confirm(`Delete "${job.original_filename}" and all its emission rows?`)) return
    try {
      await deleteJob.mutateAsync(job.id)
      toast('Job deleted', 'success')
      onDeleted?.()
    } catch (e) {
      toast(e.message, 'error')
    }
  }

  const handleRetry = async () => {
    try {
      await retryJob.mutateAsync(job.id)
      toast('Job reprocessed', 'success')
    } catch (e) {
      toast(e.message, 'error')
    }
  }

  return (
    <div className="flex items-center gap-1">
      {(stale || job.status === 'FAILED') && (
        <Button
          size="sm"
          variant="outline"
          title="Reprocess this file"
          disabled={retryJob.isPending}
          onClick={handleRetry}
        >
          <RotateCcw className="h-3.5 w-3.5" />
        </Button>
      )}
      <Button
        size="sm"
        variant="outline"
        title="Delete job"
        disabled={deleteJob.isPending}
        onClick={handleDelete}
        className="text-red-600 hover:bg-red-50 hover:text-red-700"
      >
        <Trash2 className="h-3.5 w-3.5" />
      </Button>
    </div>
  )
}
