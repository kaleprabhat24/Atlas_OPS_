import { useState } from 'react'
import { motion } from 'framer-motion'
import { api } from '../../api/client'

const GATEWAYS = ['stripe', 'razorpay', 'paypal', 'square']

export default function OutageSimulator() {
  const [gateway, setGateway] = useState('stripe')
  const [failureRate, setFailureRate] = useState(0.8)
  const [duration, setDuration] = useState(120)
  const [adminKey, setAdminKey] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSimulate = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await api.simulateOutage(
        { gateway, failure_rate: failureRate, duration_seconds: duration },
        adminKey
      )
      setResult(res)
    } catch (err) {
      setError(err.message)
    }
    setLoading(false)
  }

  const handleClear = async (gw) => {
    try {
      await api.clearOutage(gw, adminKey)
      setResult({ message: `Simulation cleared for ${gw}` })
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="glass-card p-6">
      <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
        <span>🔥</span> Gateway Outage Simulator
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <div>
          <label className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">Gateway</label>
          <select
            value={gateway}
            onChange={(e) => setGateway(e.target.value)}
            className="input-field w-full text-sm"
          >
            {GATEWAYS.map((gw) => (
              <option key={gw} value={gw}>{gw.charAt(0).toUpperCase() + gw.slice(1)}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">
            Failure Rate ({(failureRate * 100).toFixed(0)}%)
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={failureRate}
            onChange={(e) => setFailureRate(parseFloat(e.target.value))}
            className="w-full accent-red-500"
          />
        </div>
        <div>
          <label className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">Duration (sec)</label>
          <input
            type="number"
            value={duration}
            onChange={(e) => setDuration(parseInt(e.target.value) || 60)}
            className="input-field w-full text-sm"
          />
        </div>
        <div>
          <label className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">Admin Key</label>
          <input
            type="password"
            value={adminKey}
            onChange={(e) => setAdminKey(e.target.value)}
            placeholder="X-Admin-Key"
            className="input-field w-full text-sm"
          />
        </div>
      </div>

      <div className="flex gap-3 mb-4">
        <button onClick={handleSimulate} disabled={loading} className="btn-primary text-sm">
          {loading ? 'Simulating...' : '🔥 Start Outage'}
        </button>
        {GATEWAYS.map((gw) => (
          <button
            key={gw}
            onClick={() => handleClear(gw)}
            className="btn-secondary text-xs capitalize"
          >
            Clear {gw}
          </button>
        ))}
      </div>

      {error && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-red-400">
          {error}
        </motion.div>
      )}
      {result && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-sm text-emerald-400">
          {result.message}
        </motion.div>
      )}
    </div>
  )
}
