import { motion } from 'framer-motion'
import OutageSimulator from '../components/admin/OutageSimulator'
import MLStatus from '../components/admin/MLStatus'

export default function AdminPage() {
  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <span>⚙️</span> Admin Panel
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Manage ML models, simulate gateway outages, and monitor system health
        </p>
      </motion.div>

      <MLStatus />
      <OutageSimulator />
    </div>
  )
}
