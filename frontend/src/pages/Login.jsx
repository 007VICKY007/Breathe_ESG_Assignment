import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Leaf, Loader2 } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const { register, handleSubmit, formState: { isSubmitting } } = useForm()

  const onSubmit = async (data) => {
    setError('')
    try {
      await login(data.username, data.password)
      navigate('/')
    } catch (e) {
      setError(e.message)
    }
  }

  const fillDemo = () => {
    document.getElementById('username').value = 'demo'
    document.getElementById('password').value = 'demo12345'
  }

  return (
    <div className="flex min-h-screen">
      {/* Brand panel */}
      <div className="hidden w-1/2 flex-col justify-between bg-slate-900 p-12 text-white lg:flex">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-600">
            <Leaf className="h-6 w-6" />
          </div>
          <span className="text-xl font-bold">Breathe ESG</span>
        </div>
        <div>
          <h2 className="text-3xl font-bold leading-tight">
            Ingest. Normalize.<br />Review. Lock.
          </h2>
          <p className="mt-4 max-w-md text-slate-400">
            Enterprise emissions data from SAP, utility portals, and travel platforms —
            normalized to a canonical kgCO₂e model with full audit trail.
          </p>
          <ul className="mt-8 space-y-2 text-sm text-slate-400">
            <li>✓ Multi-tenant row isolation</li>
            <li>✓ Scope 1/2/3 categorization</li>
            <li>✓ Anomaly flagging before approval</li>
            <li>✓ Immutable audit lock for auditors</li>
          </ul>
        </div>
        <p className="text-xs text-slate-600">Breathe ESG · Tech Intern Prototype 2024</p>
      </div>

      {/* Form panel */}
      <div className="flex flex-1 items-center justify-center p-6">
        <Card className="w-full max-w-md border-0 shadow-xl">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Analyst sign in</CardTitle>
            <CardDescription>Access your organization&apos;s ingestion dashboard</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div>
                <Label htmlFor="username">Username</Label>
                <Input id="username" autoComplete="username" {...register('username', { required: true })} />
              </div>
              <div>
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" autoComplete="current-password" {...register('password', { required: true })} />
              </div>
              {error && (
                <div className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
              )}
              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Sign in'}
              </Button>
            </form>

            <div className="mt-6 rounded-lg border border-dashed border-slate-200 bg-slate-50 p-4 text-center">
              <p className="text-xs font-medium text-slate-600">Demo credentials</p>
              <p className="mt-1 font-mono text-sm text-slate-800">demo / demo12345</p>
              <button
                type="button"
                onClick={fillDemo}
                className="mt-2 text-xs text-teal-700 hover:underline"
              >
                Fill demo credentials
              </button>
            </div>

            <p className="mt-4 text-center text-sm text-slate-500">
              New organization?{' '}
              <Link to="/register" className="font-medium text-teal-700 hover:underline">
                Register
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
