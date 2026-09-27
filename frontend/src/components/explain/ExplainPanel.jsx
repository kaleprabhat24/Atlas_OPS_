import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '../../api/client'
import ShapChart from './ShapChart'

export default function ExplainPanel({ transactionId, shapValues, explanation }) {
  const [fetchedExplanation, setFetchedExplanation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [txnIdInput, setTxnIdInput] = useState(transactionId || '')

  const handleFetch = async () => {
    if (!txnIdInput.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.explainTransaction(txnIdInput.trim())
      setFetchedExplanation(res)
    } catch (err) {
      setError(err.message)
    }
    setLoading(false)
  }

  const displayExplanation = explanation || fetchedExplanation?.llm_explanation
  const displayShap = shapValues || fetchedExplanation?.shap_values

  return (
    <div className="glass-card p-6 space-y-4">
      <h3 className="text-lg font-bold text-white flex items-center gap-2">
        <span>🧠</span> AI Explanation
      </h3>

      {/* Lookup by ID */}
      {!explanation && (
        <div className="flex gap-2">
          <input
            type="text"
            value={txnIdInput}
            onChange={(e) => setTxnIdInput(e.target.value)}
            placeholder="Transaction ID (UUID)"
            className="input-field flex-1 text-sm"
          />
          <button
            onClick={handleFetch}
            disabled={loading}
            className="btn-primary text-sm"
          >
            {loading ? 'Loading...' : 'Explain'}
          </button>
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-red-400">
          {error}
        </div>
      )}

      <AnimatePresence>
        {displayExplanation && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="bg-surface-900/50 rounded-lg p-4 border border-white/5"
          >
            <p className="text-xs text-slate-500 mb-2 uppercase tracking-wider font-semibold">
              AI-Generated Explanation
            </p>
            <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
              {displayExplanation}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {displayShap && Object.keys(displayShap).length > 0 && (
        <ShapChart shapValues={displayShap} />
      )}
    </div>
  )
}
