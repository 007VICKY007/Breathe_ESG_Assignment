import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { Upload, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { useIngest } from '@/api/hooks'
import { useToast } from '@/context/ToastContext'

export function UploadForm({ sourceType, label }) {
  const navigate = useNavigate()
  const ingest = useIngest(sourceType)
  const { toast } = useToast()
  const { register, handleSubmit, reset, formState: { errors } } = useForm()

  const onSubmit = async ({ file }) => {
    if (!file?.[0]) return
    try {
      const job = await ingest.mutateAsync(file[0])
      reset()
      toast(`Ingestion started — ${file[0].name}`, 'success')
      if (job?.id) navigate(`/jobs/${job.id}`)
    } catch (e) {
      toast(e.message, 'error')
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <Label className="text-xs text-slate-500">{label}</Label>
      <input
        type="file"
        accept=".csv,.txt"
        className="w-full text-xs file:mr-2 file:rounded-md file:border-0 file:bg-teal-50 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-teal-700 hover:file:bg-teal-100"
        {...register('file', { required: true })}
      />
      <Button type="submit" size="sm" className="w-full" disabled={ingest.isPending}>
        {ingest.isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Processing…
          </>
        ) : (
          <>
            <Upload className="mr-2 h-4 w-4" />
            Upload & ingest
          </>
        )}
      </Button>
      {errors.file && <p className="text-xs text-red-600">Please select a file</p>}
    </form>
  )
}
