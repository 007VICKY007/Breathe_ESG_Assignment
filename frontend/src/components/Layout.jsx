import { NavLink, Outlet } from 'react-router-dom'
import {
  Leaf, LogOut, History, AlertTriangle, ScrollText, ChevronRight,
} from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { cn } from '@/lib/utils'

const nav = [
  { to: '/', label: 'Ingestion', icon: History, end: true },
  { to: '/anomalies', label: 'Anomalies', icon: AlertTriangle },
  { to: '/audit', label: 'Audit log', icon: ScrollText },
]

export function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-30 flex w-60 flex-col bg-slate-900 text-white">
        <div className="flex h-16 items-center gap-2.5 border-b border-slate-700/50 px-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-600">
            <Leaf className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-bold leading-tight">Breathe ESG</p>
            <p className="text-[10px] text-slate-400">Analyst Console</p>
          </div>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {nav.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-teal-600/90 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                )
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
              <ChevronRight className="ml-auto h-3.5 w-3.5 opacity-40" />
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-slate-700/50 p-4">
          <p className="truncate text-xs font-medium text-slate-300">{user?.username}</p>
          <p className="truncate text-[10px] text-slate-500">{user?.organization?.name}</p>
          <button
            type="button"
            onClick={logout}
            className="mt-3 flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-xs text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            <LogOut className="h-3.5 w-3.5" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="ml-60 flex flex-1 flex-col">
        <main className="page-bg flex-1 p-6 lg:p-8">
          <div className="animate-fade-in mx-auto max-w-6xl">
            <Outlet />
          </div>
        </main>
        <footer className="ml-0 border-t border-slate-200 bg-white/80 px-8 py-3 text-center text-xs text-slate-400">
          Breathe ESG · Prototype ingestion pipeline · Data frozen at ingestion for audit
        </footer>
      </div>
    </div>
  )
}
