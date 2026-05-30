import { Link } from 'react-router-dom'
import {
  Database, CloudUpload, AlertCircle, Clock, Download, FileSpreadsheet,
} from 'lucide-react'
import { useJobs, useDashboard } from '@/api/hooks'
import { UploadForm } from '@/components/UploadForm'
import { StatusBadge } from '@/components/StatusBadge'
import { ScopePieChart, ReviewStatusBar } from '@/components/DashboardCharts'
import { StatCard, PageHeader, Skeleton, EmptyState } from '@/components/PageElements'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import { formatDate, formatNumber } from '@/lib/utils'

const SAMPLE_FILES = [
  { name: 'sap_me2m_export.csv', label: 'SAP ME2M export', desc: '50 rows · fuel + procurement' },
  { name: 'utility_meter_export.csv', label: 'Utility portal CSV', desc: '36 rows · 3 meters × 12 months' },
  { name: 'travel_concur_export.csv', label: 'Concur TRX extract', desc: '31 rows · flights, hotels, ground' },
]

export default function IngestionHistory() {
  const { data: jobs = [], isLoading } = useJobs()
  const { data: dashboard, isLoading: dashLoading } = useDashboard()

  return (
    <div className="space-y-8">
      <PageHeader
        title="Ingestion & review"
        description="Upload client source files, monitor jobs, and approve normalized emission rows before audit lock."
      />

      {/* KPI row */}
      {dashLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : dashboard ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            icon={Database}
            label="Total records"
            value={dashboard.total_records.toLocaleString()}
            sub="Across all sources"
            accent="teal"
          />
          <StatCard
            icon={CloudUpload}
            label="Total kgCO₂e"
            value={formatNumber(dashboard.total_kgco2e, 0)}
            sub="Normalized at ingestion"
            accent="blue"
          />
          <StatCard
            icon={Clock}
            label="Pending review"
            value={dashboard.pending_review}
            sub="Awaiting analyst sign-off"
            accent="amber"
          />
          <StatCard
            icon={AlertCircle}
            label="Open anomalies"
            value={dashboard.open_anomalies}
            sub="System-flagged issues"
            accent="red"
          />
        </div>
      ) : null}

      {/* Charts row */}
      {dashboard && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Emissions by scope</CardTitle>
              <CardDescription>kgCO₂e distribution across Scope 1/2/3</CardDescription>
            </CardHeader>
            <CardContent>
              <ScopePieChart data={dashboard.by_scope} />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Review pipeline</CardTitle>
              <CardDescription>Records by review status</CardDescription>
            </CardHeader>
            <CardContent>
              <ReviewStatusBar data={dashboard.by_review_status} />
            </CardContent>
          </Card>
        </div>
      )}

      {/* Sample files */}
      <Card className="border-dashed border-teal-200 bg-teal-50/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <FileSpreadsheet className="h-4 w-4 text-teal-700" />
            Sample data files
          </CardTitle>
          <CardDescription>
            Realistic exports matching SAP ME2M, utility portal, and Concur TRX formats — download and upload to test.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-3">
            {SAMPLE_FILES.map((f) => (
              <a
                key={f.name}
                href={`/sample_data/${f.name}`}
                download
                className="flex items-start gap-3 rounded-lg border border-teal-100 bg-white p-4 transition-shadow hover:shadow-md"
              >
                <Download className="mt-0.5 h-4 w-4 shrink-0 text-teal-600" />
                <div>
                  <p className="text-sm font-medium text-slate-800">{f.label}</p>
                  <p className="text-xs text-slate-500">{f.desc}</p>
                </div>
              </a>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Upload cards */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-slate-800">Upload new data</h2>
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="border-l-4 border-l-amber-500">
            <CardHeader className="pb-2">
              <CardTitle className="text-base">SAP · ME2M flat file</CardTitle>
              <CardDescription>Scope 1 fuel + Scope 3 procurement</CardDescription>
            </CardHeader>
            <CardContent>
              <UploadForm sourceType="sap" label="Select .csv or .txt export" />
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-blue-500">
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Utility · Portal CSV</CardTitle>
              <CardDescription>Scope 2 electricity · multi-meter</CardDescription>
            </CardHeader>
            <CardContent>
              <UploadForm sourceType="utility" label="Select meter billing export" />
            </CardContent>
          </Card>
          <Card className="border-l-4 border-l-violet-500">
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Travel · Concur TRX</CardTitle>
              <CardDescription>Scope 3 Category 6 business travel</CardDescription>
            </CardHeader>
            <CardContent>
              <UploadForm sourceType="travel" label="Select expense extract" />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Jobs table */}
      <Card>
        <CardHeader>
          <CardTitle>Ingestion history</CardTitle>
          <CardDescription>All upload jobs for your organization</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-10" />
              ))}
            </div>
          ) : jobs.length === 0 ? (
            <EmptyState
              icon={CloudUpload}
              title="No ingestion jobs yet"
              description="Download a sample file above or upload your own export to start the pipeline."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Source</TableHead>
                  <TableHead>Filename</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Rows</TableHead>
                  <TableHead className="text-right">Errors</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.map((job) => (
                  <TableRow key={job.id}>
                    <TableCell>
                      <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-medium">
                        {job.source_category}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Link
                        to={`/jobs/${job.id}`}
                        className="font-medium text-teal-700 hover:underline"
                      >
                        {job.original_filename}
                      </Link>
                    </TableCell>
                    <TableCell className="text-slate-500">{formatDate(job.created_at)}</TableCell>
                    <TableCell className="text-right tabular-nums">{job.rows_created}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {job.error_count > 0 ? (
                        <span className="text-red-600">{job.error_count}</span>
                      ) : (
                        '0'
                      )}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={job.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
