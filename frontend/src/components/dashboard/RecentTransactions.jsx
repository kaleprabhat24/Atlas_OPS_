import { motion } from 'framer-motion'
import StatusBadge from '../ui/StatusBadge'

// Mock recent transactions for dashboard display when backend has no history endpoint
const mockTransactions = [
  { id: 'demo-001', amount: 49.99, status: 'APPROVED', gateway: 'stripe', fraud_score: 0.12, time: '2 min ago' },
  { id: 'demo-002', amount: 1299.00, status: 'REJECTED', gateway: '—', fraud_score: 0.87, time: '5 min ago' },
  { id: 'demo-003', amount: 89.50, status: 'APPROVED', gateway: 'razorpay', fraud_score: 0.08, time: '8 min ago' },
  { id: 'demo-004', amount: 450.00, status: 'FAILED', gateway: 'paypal', fraud_score: 0.31, time: '12 min ago' },
  { id: 'demo-005', amount: 24.99, status: 'APPROVED', gateway: 'square', fraud_score: 0.05, time: '15 min ago' },
]

export default function RecentTransactions({ transactions }) {
  const data = transactions && transactions.length > 0 ? transactions : mockTransactions

  return (
    <div className="glass-card p-6">
      <h3 className="text-sm font-semibold text-slate-300 mb-4">Recent Transactions</h3>
      <div className="space-y-2">
        {data.map((txn, i) => (
          <motion.div
            key={txn.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-white/[0.02] transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-surface-900 flex items-center justify-center text-xs font-mono text-slate-500">
                {txn.id.slice(-3)}
              </div>
              <div>
                <p className="text-sm font-medium text-white">
                  ${typeof txn.amount === 'number' ? txn.amount.toFixed(2) : txn.amount}
                </p>
                <p className="text-[10px] text-slate-500">
                  {txn.gateway ? txn.gateway.toUpperCase() : '—'} · {txn.time || 'just now'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-[10px] font-mono text-slate-500">
                fraud: {typeof txn.fraud_score === 'number' ? txn.fraud_score.toFixed(2) : txn.fraud_score}
              </span>
              <StatusBadge status={txn.status}>{txn.status}</StatusBadge>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
