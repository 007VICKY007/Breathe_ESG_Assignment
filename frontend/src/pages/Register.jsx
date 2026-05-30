import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useAuth } from '@/context/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function Register() {
  const { register: registerUser } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const { register, handleSubmit, formState: { isSubmitting } } = useForm()

  const onSubmit = async (data) => {
    setError('')
    try {
      await registerUser(data)
      navigate('/')
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Create organization</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="grid gap-3 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <Label>Organization name</Label>
              <Input {...register('organization_name', { required: true })} />
            </div>
            <div className="sm:col-span-2">
              <Label>Slug</Label>
              <Input {...register('organization_slug', { required: true })} placeholder="acme-corp" />
            </div>
            <div>
              <Label>Username</Label>
              <Input {...register('username', { required: true })} />
            </div>
            <div>
              <Label>Email</Label>
              <Input type="email" {...register('email', { required: true })} />
            </div>
            <div className="sm:col-span-2">
              <Label>Password</Label>
              <Input type="password" {...register('password', { required: true, minLength: 8 })} />
            </div>
            {error && <p className="sm:col-span-2 text-sm text-red-600">{error}</p>}
            <Button type="submit" className="sm:col-span-2" disabled={isSubmitting}>
              Create & sign in
            </Button>
          </form>
          <p className="mt-4 text-center text-sm">
            <Link to="/login" className="text-teal-700 hover:underline">
              Back to login
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
