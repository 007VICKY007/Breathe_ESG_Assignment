import { ScrollText } from 'lucide-react'
import { useAuditLog } from '@/api/hooks'
import { Badge } from '@/components/ui/badge'
import { PageHeader, Skeleton, EmptyState } from '@/components/PageElements'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'

const ACTION_VARIANT = {
  APPROVE: 'success',
  REJECT: 'error',
  LOCK: 'default',
  EDIT: 'warning',
}

export default function AuditLog() {
  const { data: actions = [], isLoading } = useAuditLog()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit log"
        description="Append-only record of every analyst decision — complements field-level history on each emission row."
      />

      <Card>
        <CardHeader>
          <CardTitle>Review actions</CardTitle>
          <CardDescription>
            Who approved, rejected, edited, or locked each row and when. Locked rows are immutable.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-6">
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-10" />
              ))}
            </div>
          ) : actions.length === 0 ? (
            <EmptyState
              icon={ScrollText}
              title="No review actions yet"
              description="Actions appear here when analysts approve, reject, edit, or lock emission records."
            />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50/80">
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Analyst</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Record</TableHead>
                    <TableHead>Note</TableHead>
                    <TableHead>Change detail</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {actions.map((a) => (
                    <TableRow key={a.id}>
                      <TableCell className="whitespace-nowrap text-xs text-slate-500">
                        {new Date(a.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell className="text-sm font-medium">
                        {a.performed_by_username || '—'}
                      </TableCell>
                      <TableCell>
                        <Badge variant={ACTION_VARIANT[a.action] || 'default'}>
                          {a.action}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs text-slate-500">
                        {String(a.emission_record_id).slice(0, 8)}…
                      </TableCell>
                      <TableCell className="max-w-[180px] truncate text-sm">
                        {a.note || '—'}
                      </TableCell>
                      <TableCell className="max-w-xs text-xs text-slate-600">
                        {a.action === 'EDIT' && a.previous_values?.raw_value != null ? (
                          <span>
                            <span className="text-red-600 line-through">
                              {a.previous_values.raw_value} {a.previous_values.raw_unit}
                            </span>
                            {' → '}
                            <span className="font-medium text-emerald-700">
                              {a.new_values?.raw_value} {a.new_values?.raw_unit}
                            </span>
                          </span>
                        ) : a.action === 'LOCK' ? (
                          <span className="text-purple-600">Frozen for audit</span>
                        ) : (
                          '—'
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
