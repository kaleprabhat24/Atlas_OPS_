import { motion } from 'framer-motion'

const cards = [
  {
    label: 'Total Transactions',
    key: 'totalTransactions',
    icon: '💳',
    color: 'from-atlas-500/20 to-atlas-600/10',
    border: 'border-atlas-500/20',
  },
  {
    label: 'Approval Rate',
    key: 'approvedRate',
    icon: '✅',
    color: 'from-emerald-500/20 to-emerald-600/10',
    border: 'border-emerald-500/20',
    suffix: '%',
  },
  {
    label: 'Avg Fraud Score',
    key: 'avgFraudScore',
    icon: '🛡️',
    color: 'from-amber-500/20 to-amber-600/10',
    border: 'border-amber-500/20',
  },
  {
    label: 'Avg Latency',
    key: 'avgLatency',
    icon: '⚡',
    color: 'from-cyan-500/20 to-cyan-600/10',
    border: 'border-cyan-500/20',
    suffix: 'ms',
  },
]

export default function StatsCards({ stats }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, i) => (
        <motion.div
          key={card.key}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1 }}
          className={`glass-card-hover p-5 bg-gradient-to-br ${card.color} ${card.border}`}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-2xl">{card.icon}</span>
          </div>
          <p className="text-2xl font-bold text-white">
            {stats[card.key] ?? '—'}
            {card.suffix && (
              <span className="text-sm text-slate-400 ml-1">{card.suffix}</span>
            )}
          </p>
          <p className="text-xs text-slate-400 mt-1">{card.label}</p>
        </motion.div>
      ))}
    </div>
  )
}
