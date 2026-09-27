import { motion } from 'framer-motion'

export default function PipelineMetrics({ metrics }) {
  const {
    fraudScore,
    fraudFlag,
    selectedGateway,
    routingConfidence,
    circuitState,
    gatewayLatency,
    finalStatus,
    elapsed,
  } = metrics

  const items = [
    {
      label: 'Fraud Score',
      value: fraudScore !== undefined ? `${(fraudScore * 100).toFixed(1)}%` : '—',
      color: fraudFlag ? 'text-red-400' : fraudScore !== undefined ? 'text-emerald-400' : 'text-slate-500',
      icon: '🛡️',
    },
    {
      label: 'Gateway',
      value: selectedGateway ? selectedGateway.toUpperCase() : '—',
      color: selectedGateway ? 'text-atlas-400' : 'text-slate-500',
      icon: '🏦',
    },
    {
      label: 'Routing Confidence',
      value: routingConfidence !== undefined ? `${(routingConfidence * 100).toFixed(1)}%` : '—',
      color: routingConfidence ? 'text-cyan-400' : 'text-slate-500',
      icon: '🎯',
    },
    {
      label: 'Circuit State',
      value: circuitState || '—',
      color: circuitState === 'closed' ? 'text-emerald-400' : circuitState === 'open' ? 'text-red-400' : 'text-slate-500',
      icon: '🔌',
    },
    {
      label: 'Gateway Latency',
      value: gatewayLatency ? `${Math.round(gatewayLatency)}ms` : '—',
      color: gatewayLatency > 1000 ? 'text-amber-400' : gatewayLatency ? 'text-slate-300' : 'text-slate-500',
      icon: '⚡',
    },
    {
      label: 'Total Time',
      value: elapsed ? `${elapsed}ms` : '—',
      color: elapsed ? 'text-slate-300' : 'text-slate-500',
      icon: '⏱️',
    },
  ]

  return (
    <div className="glass-card p-4">
      <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
        <span>📊</span> Live Metrics
      </h3>
      <div className="space-y-3">
        {items.map((item, i) => (
          <motion.div
            key={item.label}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.05 }}
            className="flex items-center justify-between py-1"
          >
            <div className="flex items-center gap-2">
              <span className="text-sm">{item.icon}</span>
              <span className="text-xs text-slate-400">{item.label}</span>
            </div>
            <span className={`text-sm font-mono font-semibold ${item.color}`}>
              {item.value}
            </span>
          </motion.div>
        ))}
      </div>

      {/* Final Result Banner */}
      {finalStatus && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`mt-4 p-3 rounded-lg text-center font-bold text-sm ${
            finalStatus === 'APPROVED'
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
              : finalStatus === 'REJECTED'
              ? 'bg-red-500/10 text-red-400 border border-red-500/20'
              : 'bg-orange-500/10 text-orange-400 border border-orange-500/20'
          }`}
        >
          {finalStatus === 'APPROVED' ? '✅' : finalStatus === 'REJECTED' ? '🚫' : '⚠️'}{' '}
          {finalStatus}
        </motion.div>
      )}
    </div>
  )
}
