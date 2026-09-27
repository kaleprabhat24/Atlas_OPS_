import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="glass-card p-3 border border-white/10">
      <p className="text-xs font-semibold text-white">{d.name}</p>
      <p className="text-xs text-slate-400">
        Value: <span className="text-atlas-400 font-mono">{d.value.toFixed(4)}</span>
      </p>
    </div>
  )
}

export default function FraudChart({ shapValues }) {
  if (!shapValues || Object.keys(shapValues).length === 0) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-4">SHAP Feature Impact</h3>
        <div className="h-48 flex items-center justify-center text-slate-500 text-sm">
          Run a transaction to see SHAP values
        </div>
      </div>
    )
  }

  const data = Object.entries(shapValues)
    .map(([name, value]) => ({ name, value: Math.abs(value), raw: value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8)

  return (
    <div className="glass-card p-6">
      <h3 className="text-sm font-semibold text-slate-300 mb-4">SHAP Feature Impact</h3>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} layout="vertical" margin={{ left: 80, right: 20 }}>
          <XAxis type="number" tick={{ fill: '#64748b', fontSize: 10 }} />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            width={80}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={20}>
            {data.map((entry, index) => (
              <Cell
                key={index}
                fill={entry.raw > 0 ? '#ef4444' : '#10b981'}
                fillOpacity={0.8}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
