import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export function formatNumber(value, decimals = 2) {
  const n = Number(value)
  if (Number.isNaN(n)) return '—'
  return n.toLocaleString(undefined, { maximumFractionDigits: decimals })
}

export function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString()
}

export function statusColor(status) {
  const map = {
    PENDING: 'bg-slate-100 text-slate-700',
    PROCESSING: 'bg-blue-100 text-blue-800',
    DONE: 'bg-emerald-100 text-emerald-800',
    FAILED: 'bg-red-100 text-red-800',
    APPROVED: 'bg-emerald-100 text-emerald-800',
    REJECTED: 'bg-red-100 text-red-800',
    LOCKED: 'bg-purple-100 text-purple-800',
  }
  return map[status] || 'bg-slate-100 text-slate-700'
}
