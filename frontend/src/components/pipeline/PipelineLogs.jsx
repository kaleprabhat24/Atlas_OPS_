import { useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function PipelineLogs({ logs }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs.length])

  const statusColors = {
    completed: 'text-emerald-400',
    active: 'text-atlas-400',
    failed: 'text-red-400',
    skipped: 'text-amber-400',
    pending: 'text-slate-500',
  }

  return (
    <div className="glass-card p-4">
      <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
        <span>📋</span> Live Logs
        <span className="text-[10px] text-slate-600 font-mono">({logs.length})</span>
      </h3>
      <div className="h-64 overflow-y-auto space-y-1 font-mono text-[11px]">
        {logs.length === 0 && (
          <p className="text-slate-600 text-center py-8">Waiting for pipeline execution...</p>
        )}
        <AnimatePresence>
          {logs.map((log, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex gap-2 py-1 border-b border-white/[0.03]"
            >
              <span className="text-slate-600 shrink-0">
                {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '--:--:--'}
              </span>
              <span className={`shrink-0 w-16 text-right ${statusColors[log.status] || 'text-slate-500'}`}>
                [{log.status}]
              </span>
              <span className="text-slate-400">
                Stage {log.stage}: {log.name}
                {log.message && <span className="text-slate-600"> — {log.message}</span>}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
