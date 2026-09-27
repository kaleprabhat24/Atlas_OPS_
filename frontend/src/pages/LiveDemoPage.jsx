import { motion } from 'framer-motion'
import PipelineView from '../components/pipeline/PipelineView'

export default function LiveDemoPage() {
  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <span>⚡</span> Live Pipeline Demo
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Submit a transaction and watch all 16 AI pipeline stages execute in real time
        </p>
      </motion.div>

      <PipelineView />
    </div>
  )
}
