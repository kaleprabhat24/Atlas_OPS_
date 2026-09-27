import { useEffect } from 'react'
import { motion } from 'framer-motion'
import useStore from '../../store/useStore'
import { api } from '../../api/client'
import StatusBadge from '../ui/StatusBadge'

export default function MLStatus() {
  const mlStatus = useStore((s) => s.mlStatus)
  const setMLStatus = useStore((s) => s.setMLStatus)

  useEffect(() => {
    api.getMLStatus().then(setMLStatus).catch(() => {})
  }, [setMLStatus])

  const models = [
    { key: 'fraud_model', label: 'Fraud Detection', icon: '🛡️', desc: 'XGBoost binary classifier for transaction fraud probability' },
    { key: 'routing_model', label: 'Intelligent Routing', icon: '🎯', desc: 'ML model for optimal gateway selection' },
    { key: 'failure_model', label: 'Failure Analysis', icon: '🔍', desc: 'Diagnoses payment failures via gateway telemetry' },
  ]

  return (
    <div className="glass-card p-6">
      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
        <span>🤖</span> ML Model Status
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {models.map((model, i) => {
          const status = mlStatus?.[model.key] || 'unknown'
          return (
            <motion.div
              key={model.key}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="glass-card-hover p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-2xl">{model.icon}</span>
                <StatusBadge status={status}>{status}</StatusBadge>
              </div>
              <h4 className="text-sm font-semibold text-white">{model.label}</h4>
              <p className="text-[11px] text-slate-500 mt-1">{model.desc}</p>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
