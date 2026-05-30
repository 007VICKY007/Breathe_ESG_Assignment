import { useState } from 'react'
import {
  Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, Cell,
} from 'recharts'
import { AlertTriangle } from 'lucide-react'
import { useAnomalies } from '@/api/hooks'
import { Badge } from '@/components/ui/badge'
import { PageHeader, Skeleton, EmptyState } from '@/components/PageElements'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'

export default function AnomalyDashboard() {
  const [scope, setScope] = useState('')
  const [sourceType, setSourceType] = useState('')
  const filters = {
    ...(scope && { scope }),
    ...(sourceType && { source_type: sourceType }),
  }
  const { data: groups = [], isLoading } = useAnomalies(filters)

  const chartData = groups.map((g) => ({
    name: g.flag_type.replace(/_/g, ' '),
    count: g.count,
    severity: g.severity,
    fill: g.severity === 'ERROR' ? '#dc2626' : '#d97706',
  }))

  const totalFlags = groups.reduce((s, g) => s + g.count, 0)
  const errorCount = groups.filter((g) => g.severity === 'ERROR').reduce((s, g) => s + g.count, 0)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Anomaly summary"
        description="System-detected data quality issues grouped by type — ERROR flags block approval."
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-1">
            <CardDescription>Total flags</CardDescription>
            <CardTitle>{totalFlags}</CardTitle>
          </CardHeader>
        </Card>
        <Card className="border-red-100">
          <CardHeader className="pb-1">
            <CardDescription className="text-red-600">Blocking errors</CardDescription>
            <CardTitle className="text-red-700">{errorCount}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-1">
            <CardDescription>Distinct types</CardDescription>
            <CardTitle>{groups.length}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      <div className="flex flex-wrap gap-4 rounded-xl border border-slate-200 bg-white p-4">
        <div>
          <Label className="text-xs">Scope</Label>
          <Select value={scope} onChange={(e) => setScope(e.target.value)} className="mt-1 w-36">
            <option value="">All scopes</option>
            <option value="1">Scope 1</option>
            <option value="2">Scope 2</option>
            <option value="3">Scope 3</option>
          </Select>
        </div>
        <div>
          <Label className="text-xs">Source type</Label>
          <Select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
            className="mt-1 w-52"
          >
            <option value="">All sources</option>
            <option value="SAP_FUEL">SAP fuel</option>
            <option value="SAP_PROCUREMENT">SAP procurement</option>
            <option value="UTILITY_ELECTRICITY">Utility electricity</option>
            <option value="TRAVEL_FLIGHT">Travel flight</option>
            <option value="TRAVEL_HOTEL">Travel hotel</option>
            <option value="TRAVEL_GROUND">Travel ground</option>
          </Select>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="text-base">Flags by type</CardTitle>
            <CardDescription>Red = ERROR (blocks approval) · Amber = WARNING</CardDescription>
          </CardHeader>
          <CardContent className="h-80">
            {isLoading ? (
              <Skeleton className="h-full" />
            ) : chartData.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
                  <XAxis type="number" allowDecimals={false} />
                  <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" radius={4}>
                    {chartData.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState
                icon={AlertTriangle}
                title="No anomalies"
                description="No flags match your filters — either clean data or try broadening filters."
              />
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Breakdown</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Sev.</TableHead>
                  <TableHead className="text-right">#</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {groups.map((g) => (
                  <TableRow key={`${g.flag_type}-${g.severity}`}>
                    <TableCell className="font-mono text-[11px]">{g.flag_type}</TableCell>
                    <TableCell>
                      <Badge variant={g.severity === 'ERROR' ? 'error' : 'warning'}>
                        {g.severity}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right font-semibold">{g.count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
