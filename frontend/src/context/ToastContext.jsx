import { createContext, useCallback, useContext, useState } from 'react'
import { CheckCircle, AlertCircle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const toast = useCallback((message, type = 'info') => {
    const id = Date.now()
    setToasts((t) => [...t, { id, message, type }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000)
  }, [])

  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    info: Info,
  }

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map(({ id, message, type }) => {
          const Icon = icons[type] || Info
          return (
            <div
              key={id}
              className={cn(
                'flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-medium shadow-lg animate-fade-in',
                type === 'success' && 'bg-emerald-600 text-white',
                type === 'error' && 'bg-red-600 text-white',
                type === 'info' && 'bg-slate-800 text-white'
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {message}
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast requires ToastProvider')
  return ctx
}
