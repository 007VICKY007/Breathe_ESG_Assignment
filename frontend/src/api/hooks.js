import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, getPaginatedResults } from './client'

export function useMe(enabled = true) {
  return useQuery({
    queryKey: ['me'],
    queryFn: async () => (await api.get('/auth/me/')).data,
    enabled,
  })
}

export function useJobs() {
  return useQuery({
    queryKey: ['jobs'],
    queryFn: async () => getPaginatedResults((await api.get('/jobs/')).data),
    refetchInterval: (query) => {
      const jobs = query.state.data || []
      const pending = jobs.some((j) => ['PENDING', 'PROCESSING'].includes(j.status))
      return pending ? 3000 : false
    },
  })
}

export function useJob(jobId) {
  return useQuery({
    queryKey: ['jobs', jobId],
    queryFn: async () => (await api.get(`/jobs/${jobId}/`)).data,
    enabled: !!jobId,
    refetchInterval: (query) => {
      const job = query.state.data
      if (job && ['PENDING', 'PROCESSING'].includes(job.status)) return 2000
      return false
    },
  })
}

export function useJobRecords(jobId) {
  return useQuery({
    queryKey: ['jobs', jobId, 'records'],
    queryFn: async () =>
      getPaginatedResults((await api.get(`/jobs/${jobId}/records/`)).data),
    enabled: !!jobId,
  })
}

export function useRecords(filters = {}) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => {
    if (v) params.set(k, v)
  })
  return useQuery({
    queryKey: ['records', filters],
    queryFn: async () =>
      getPaginatedResults((await api.get(`/records/?${params}`)).data),
  })
}

export function useAnomalies(filters = {}) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => {
    if (v) params.set(k, v)
  })
  return useQuery({
    queryKey: ['anomalies', filters],
    queryFn: async () => (await api.get(`/anomalies/?${params}`)).data,
  })
}

export function useDashboard() {
  return useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => (await api.get('/dashboard/summary/')).data,
  })
}

export function useAuditLog() {
  return useQuery({
    queryKey: ['audit-log'],
    queryFn: async () => getPaginatedResults((await api.get('/audit-log/')).data),
  })
}

export function useIngest(sourceType) {
  const qc = useQueryClient()
  const paths = { sap: '/ingest/sap/', utility: '/ingest/utility/', travel: '/ingest/travel/' }
  return useMutation({
    mutationFn: async (file) => {
      const form = new FormData()
      form.append('file', file)
      return (await api.post(paths[sourceType], form)).data
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['jobs'] }),
  })
}

export function useBulkApprove(jobId) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () =>
      (await api.post(`/jobs/${jobId}/bulk-approve/`)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['jobs', jobId] })
      qc.invalidateQueries({ queryKey: ['jobs', jobId, 'records'] })
    },
  })
}

export function useRecordAction() {
  const qc = useQueryClient()
  const invalidate = (jobId) => {
    qc.invalidateQueries({ queryKey: ['records'] })
    qc.invalidateQueries({ queryKey: ['jobs'] })
    if (jobId) {
      qc.invalidateQueries({ queryKey: ['jobs', jobId] })
      qc.invalidateQueries({ queryKey: ['jobs', jobId, 'records'] })
    }
  }
  return {
    approve: useMutation({
      mutationFn: ({ id, note }) =>
        api.post(`/records/${id}/approve/`, { note }),
      onSuccess: (_, { jobId }) => invalidate(jobId),
    }),
    reject: useMutation({
      mutationFn: ({ id, note }) =>
        api.post(`/records/${id}/reject/`, { note }),
      onSuccess: (_, { jobId }) => invalidate(jobId),
    }),
    lock: useMutation({
      mutationFn: ({ id, note }) =>
        api.post(`/records/${id}/lock/`, { note }),
      onSuccess: (_, { jobId }) => invalidate(jobId),
    }),
    edit: useMutation({
      mutationFn: ({ id, ...body }) =>
        api.patch(`/records/${id}/`, body),
      onSuccess: (_, { jobId }) => invalidate(jobId),
    }),
  }
}
