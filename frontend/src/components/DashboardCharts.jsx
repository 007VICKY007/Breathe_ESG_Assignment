import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts'

const SCOPE_COLORS = ['#0d9488', '#3b82f6', '#8b5cf6']
const SOURCE_COLORS = ['#14b8a6', '#6366f1', '#f59e0b', '#ef4444', '#ec4899', '#64748b']

export function ScopePieChart({ data = [] }) {
  const chartData = data.map((d) => ({
    name: `Scope ${d.scope}`,
    value: Number(d.kg) || 0,
    count: d.count,
  }))

  if (!chartData.length) {
    return <p className="py-8 text-center text-sm text-slate-400">No emission data yet</p>
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={55}
          outerRadius={85}
          paddingAngle={3}
          dataKey="value"
        >
          {chartData.map((_, i) => (
            <Cell key={i} fill={SCOPE_COLORS[i % SCOPE_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(v) => [`${Number(v).toLocaleString()} kgCO₂e`, 'Emissions']} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}

export function ReviewStatusBar({ data = [] }) {
  const chartData = data.map((d) => ({
    name: d.review_status,
    count: d.count,
  }))

  if (!chartData.length) return null

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
        <XAxis dataKey="name" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="count" fill="#0d9488" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export { SOURCE_COLORS }
