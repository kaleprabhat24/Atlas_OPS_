import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts'

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="glass-card p-3 border border-white/10">
      <p className="text-xs font-semibold text-white">{d.name}</p>
      <p className="text-xs text-slate-400">
        SHAP: <span className={`font-mono ${d.raw > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
          {d.raw > 0 ? '+' : ''}{d.raw.toFixed(4)}
        </span>
      </p>
      <p className="text-[10px] text-slate-500 mt-1">
        {d.raw > 0 ? 'Increases failure/fraud risk' : 'Decreases failure/fraud risk'}
      </p>
    </div>
  )
}

export default function ShapChart({ shapValues, title = 'SHAP Feature Contributions' }) {
  if (!shapValues || Object.keys(shapValues).length === 0) return null

  const data = Object.entries(shapValues)
    .map(([name, value]) => ({
      name: name.length > 18 ? name.slice(0, 16) + '…' : name,
      fullName: name,
      value: value,
      raw: value,
      absValue: Math.abs(value),
    }))
    .sort((a, b) => b.absValue - a.absValue)
    .slice(0, 10)

  return (
    <div>
      <p className="text-xs text-slate-500 mb-3 uppercase tracking-wider font-semibold">{title}</p>
      <ResponsiveContainer width="100%" height={Math.max(200, data.length * 28)}>
        <BarChart data={data} layout="vertical" margin={{ left: 100, right: 30, top: 5, bottom: 5 }}>
          <XAxis
            type="number"
            tick={{ fill: '#64748b', fontSize: 10 }}
            axisLine={{ stroke: '#1e2235' }}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            width={100}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine x={0} stroke="#334155" strokeWidth={1} />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={18}>
            {data.map((entry, index) => (
              <Cell
                key={index}
                fill={entry.raw > 0 ? '#ef4444' : '#10b981'}
                fillOpacity={0.75}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
