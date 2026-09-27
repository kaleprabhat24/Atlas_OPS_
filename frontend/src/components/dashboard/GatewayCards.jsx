import { motion } from 'framer-motion'
import StatusBadge from '../ui/StatusBadge'

export default function GatewayCards({ gateways }) {
  if (!gateways || gateways.length === 0) {
    return (
      <div className="glass-card p-6 text-center text-slate-500">
        <p>No gateway data available. Start the backend to see live metrics.</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {gateways.map((gw, i) => (
        <motion.div
          key={gw.gateway_name}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: i * 0.08 }}
          className="glass-card-hover p-5"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-atlas-500/20 to-atlas-600/10 border border-atlas-500/20 flex items-center justify-center">
                <span className="text-sm font-bold text-atlas-400 uppercase">
                  {gw.gateway_name.slice(0, 2)}
                </span>
              </div>
              <div>
                <h3 className="font-semibold text-white capitalize">{gw.gateway_name}</h3>
                <p className="text-xs text-slate-500">{gw.total_requests} requests</p>
              </div>
            </div>
            <StatusBadge status={gw.circuit_state}>{gw.circuit_state}</StatusBadge>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs text-slate-500 mb-1">Success Rate</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 h-1.5 bg-surface-900 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-emerald-400"
                    initial={{ width: 0 }}
                    animate={{ width: `${(gw.success_rate * 100)}%` }}
                    transition={{ duration: 0.8, delay: i * 0.1 }}
                  />
                </div>
                <span className="text-xs font-mono text-emerald-400">
                  {(gw.success_rate * 100).toFixed(1)}%
                </span>
              </div>
            </div>
            <div>
              <p className="text-xs text-slate-500 mb-1">Avg Latency</p>
              <p className="text-sm font-mono text-white">
                {gw.avg_latency_ms.toFixed(0)}<span className="text-slate-500">ms</span>
              </p>
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  )
}
