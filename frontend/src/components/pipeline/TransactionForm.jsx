import { useState } from 'react'
import { motion } from 'framer-motion'

const PRESETS = {
  normal: {
    label: '✅ Normal Transaction',
    data: {
      amount: 49.99,
      card1: 12345,
      card2: 111,
      email_domain: 'gmail.com',
      addr1: 300,
      addr2: 87,
      device_type: 'desktop',
      device_info: 'Chrome 120 / Windows 11',
      dist1: 5.0,
      dist2: 2.0,
    },
  },
  suspicious: {
    label: '⚠️ High-Risk Transaction',
    data: {
      amount: 9999.99,
      card1: 99999,
      card2: 999,
      email_domain: 'tempmail.xyz',
      addr1: 1,
      addr2: 1,
      device_type: 'mobile',
      device_info: 'Unknown Browser / Linux',
      dist1: 500.0,
      dist2: 300.0,
    },
  },
  medium: {
    label: '🔶 Medium Risk',
    data: {
      amount: 299.50,
      card1: 55555,
      card2: 444,
      email_domain: 'yahoo.com',
      addr1: 150,
      addr2: 40,
      device_type: 'tablet',
      device_info: 'Safari / iPadOS 17',
      dist1: 50.0,
      dist2: 25.0,
    },
  },
}

export default function TransactionForm({ onSubmit, onCancel, isRunning }) {
  const [formData, setFormData] = useState(PRESETS.normal.data)

  const applyPreset = (key) => {
    setFormData(PRESETS[key].data)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <span>💳</span> Submit Transaction
        </h2>
        <div className="flex gap-2">
          {Object.entries(PRESETS).map(([key, preset]) => (
            <button
              key={key}
              onClick={() => applyPreset(key)}
              disabled={isRunning}
              className="text-[11px] px-3 py-1.5 rounded-md bg-surface-900 border border-white/5
                         hover:border-atlas-500/30 text-slate-400 hover:text-white transition-all
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-4">
          {Object.entries(formData).map(([key, value]) => (
            <div key={key}>
              <label className="text-[10px] text-slate-500 uppercase tracking-wider block mb-1">
                {key.replace(/_/g, ' ')}
              </label>
              <input
                type={typeof value === 'number' ? 'number' : 'text'}
                step={typeof value === 'number' ? 'any' : undefined}
                value={value}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    [key]: typeof value === 'number' ? parseFloat(e.target.value) || 0 : e.target.value,
                  }))
                }
                disabled={isRunning}
                className="input-field w-full text-xs"
              />
            </div>
          ))}
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={isRunning}
            className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRunning ? (
              <>
                <motion.span
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                />
                Processing...
              </>
            ) : (
              <>⚡ Process Transaction</>
            )}
          </button>
          {isRunning && (
            <button type="button" onClick={onCancel} className="btn-secondary">
              Cancel
            </button>
          )}
        </div>
      </form>
    </motion.div>
  )
}
