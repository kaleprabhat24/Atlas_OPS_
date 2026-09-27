import { motion, AnimatePresence } from 'framer-motion'

const statusConfig = {
  completed: {
    icon: '✓',
    color: 'bg-emerald-500',
    ring: 'ring-emerald-500/30',
    text: 'text-emerald-400',
    line: 'bg-emerald-500/40',
    glow: '',
  },
  active: {
    icon: '●',
    color: 'bg-atlas-500',
    ring: 'ring-atlas-500/30',
    text: 'text-atlas-400',
    line: 'bg-atlas-500/20',
    glow: 'pipeline-active',
  },
  failed: {
    icon: '✗',
    color: 'bg-red-500',
    ring: 'ring-red-500/30',
    text: 'text-red-400',
    line: 'bg-red-500/30',
    glow: '',
  },
  skipped: {
    icon: '−',
    color: 'bg-amber-500/50',
    ring: 'ring-amber-500/20',
    text: 'text-amber-400/60',
    line: 'bg-amber-500/10',
    glow: '',
  },
  pending: {
    icon: '',
    color: 'bg-slate-700',
    ring: 'ring-slate-700/30',
    text: 'text-slate-500',
    line: 'bg-slate-700/30',
    glow: '',
  },
}

export default function PipelineStep({ stage, isLast }) {
  const config = statusConfig[stage.status] || statusConfig.pending
  const hasData = stage.data && Object.keys(stage.data).length > 0

  return (
    <div className="flex gap-4">
      {/* Timeline */}
      <div className="flex flex-col items-center">
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className={`w-8 h-8 rounded-full ${config.color} ring-4 ${config.ring} ${config.glow}
                      flex items-center justify-center text-white text-xs font-bold z-10 shrink-0`}
        >
          {config.icon || stage.id}
        </motion.div>
        {!isLast && (
          <div className={`w-0.5 flex-1 min-h-[24px] ${config.line} transition-colors duration-300`} />
        )}
      </div>

      {/* Content */}
      <motion.div
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.05 }}
        className={`pb-4 flex-1 ${isLast ? '' : ''}`}
      >
        <div className="flex items-center justify-between">
          <h3 className={`text-sm font-semibold ${config.text}`}>
            {stage.name}
          </h3>
          {stage.timestamp && (
            <span className="text-[10px] font-mono text-slate-600">
              {new Date(stage.timestamp).toLocaleTimeString()}
            </span>
          )}
        </div>

        {/* Expandable data */}
        <AnimatePresence>
          {hasData && stage.status !== 'pending' && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="mt-2 overflow-hidden"
            >
              <div className="bg-surface-900/50 rounded-lg p-3 border border-white/5">
                {renderStageData(stage)}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}

function renderStageData(stage) {
  const d = stage.data
  if (!d || Object.keys(d).length === 0) return null

  // Special rendering for certain stages
  if (stage.id === 6 && d.fraud_probability !== undefined) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-400">Fraud Probability</span>
          <span className={`text-sm font-mono font-bold ${d.fraud_flag ? 'text-red-400' : 'text-emerald-400'}`}>
            {(d.fraud_probability * 100).toFixed(2)}%
          </span>
        </div>
        <div className="w-full h-2 bg-surface-900 rounded-full overflow-hidden">
          <motion.div
            className={`h-full rounded-full ${d.fraud_flag ? 'bg-red-500' : 'bg-emerald-500'}`}
            initial={{ width: 0 }}
            animate={{ width: `${d.fraud_probability * 100}%` }}
            transition={{ duration: 0.6 }}
          />
        </div>
        {d.top_features && (
          <div className="text-[10px] text-slate-500">
            Top: {Object.entries(d.top_features).map(([k, v]) => `${k}: ${v > 0 ? '+' : ''}${v.toFixed(3)}`).join(', ')}
          </div>
        )}
      </div>
    )
  }

  if (stage.id === 8 && d.selected_gateway) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-400">Selected Gateway</span>
          <span className="text-sm font-semibold text-atlas-400 uppercase">{d.selected_gateway}</span>
        </div>
        {d.gateway_scores && (
          <div className="grid grid-cols-2 gap-1">
            {Object.entries(d.gateway_scores).map(([gw, score]) => (
              <div key={gw} className="flex items-center justify-between text-[10px]">
                <span className={`capitalize ${gw === d.selected_gateway ? 'text-atlas-300 font-semibold' : 'text-slate-500'}`}>
                  {gw}
                </span>
                <span className="font-mono text-slate-400">{(score * 100).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        )}
      </div>
    )
  }

  if (stage.id === 14 && d.explanation) {
    return (
      <div className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap max-h-40 overflow-y-auto">
        {d.explanation}
      </div>
    )
  }

  if (stage.id === 16) {
    return (
      <div className="flex items-center gap-4">
        <span className={`text-lg font-bold ${
          d.status === 'APPROVED' ? 'text-emerald-400' :
          d.status === 'REJECTED' ? 'text-red-400' : 'text-orange-400'
        }`}>
          {d.status}
        </span>
        {d.elapsed_ms && (
          <span className="text-xs text-slate-500 font-mono">{d.elapsed_ms}ms total</span>
        )}
      </div>
    )
  }

  // Generic key-value display
  const displayKeys = Object.entries(d).filter(
    ([k]) => k !== 'message' && typeof d[k] !== 'object'
  ).slice(0, 4)

  if (displayKeys.length === 0 && d.message) {
    return <p className="text-xs text-slate-400">{d.message}</p>
  }

  return (
    <div className="space-y-1">
      {d.message && <p className="text-xs text-slate-400 mb-1">{d.message}</p>}
      {displayKeys.map(([k, v]) => (
        <div key={k} className="flex justify-between text-[11px]">
          <span className="text-slate-500">{k.replace(/_/g, ' ')}</span>
          <span className="font-mono text-slate-300">{String(v)}</span>
        </div>
      ))}
    </div>
  )
}
