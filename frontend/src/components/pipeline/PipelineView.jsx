import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import useStore from '../../store/useStore'
import { connectPipelineSSE } from '../../api/client'
import PipelineStep from './PipelineStep'
import PipelineLogs from './PipelineLogs'
import PipelineMetrics from './PipelineMetrics'
import TransactionForm from './TransactionForm'

export default function PipelineView() {
  const {
    pipelineStages,
    pipelineRunning,
    pipelineLogs,
    pipelineResult,
    pipelineError,
    startPipeline,
    updateStage,
    completePipeline,
    failPipeline,
  } = useStore()

  const [abortFn, setAbortFn] = useState(null)

  const handleSubmit = useCallback(
    (formData) => {
      startPipeline()

      const abort = connectPipelineSSE(
        formData,
        (event) => {
          updateStage(event)
          // Capture final result
          if (event.stage === 16 && event.status === 'completed') {
            completePipeline(event.data)
          }
        },
        (error) => {
          failPipeline(error.message)
        },
        () => {
          // Stream complete
          const state = useStore.getState()
          if (state.pipelineRunning) {
            completePipeline(state.pipelineStages[15]?.data || {})
          }
        }
      )

      setAbortFn(() => abort)
    },
    [startPipeline, updateStage, completePipeline, failPipeline]
  )

  const handleCancel = useCallback(() => {
    abortFn?.()
    failPipeline('Pipeline cancelled by user')
  }, [abortFn, failPipeline])

  // Extract metrics from completed stages
  const metrics = {
    fraudScore: pipelineStages[5]?.data?.fraud_probability,
    fraudFlag: pipelineStages[5]?.data?.fraud_flag,
    selectedGateway: pipelineStages[7]?.data?.selected_gateway,
    gatewayScores: pipelineStages[7]?.data?.gateway_scores,
    routingConfidence: pipelineStages[7]?.data?.confidence,
    circuitState: pipelineStages[8]?.data?.circuit_state,
    gatewayLatency: pipelineStages[9]?.data?.latency_ms || pipelineStages[10]?.data?.latency_ms,
    shapValues: pipelineStages[12]?.data?.fraud_shap || pipelineStages[12]?.data?.shap_values,
    explanation: pipelineStages[13]?.data?.explanation,
    finalStatus: pipelineStages[15]?.data?.status,
    elapsed: pipelineStages[15]?.data?.elapsed_ms,
  }

  return (
    <div className="space-y-6">
      {/* Transaction Form */}
      <TransactionForm
        onSubmit={handleSubmit}
        onCancel={handleCancel}
        isRunning={pipelineRunning}
      />

      {/* Error Banner */}
      {pipelineError && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-card p-4 border border-red-500/30 bg-red-500/5"
        >
          <div className="flex items-center gap-2">
            <span className="text-red-400">❌</span>
            <p className="text-sm text-red-400">{pipelineError}</p>
          </div>
        </motion.div>
      )}

      {/* Main Pipeline Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pipeline Steps — 2 columns */}
        <div className="lg:col-span-2 glass-card p-6">
          <div className="flex items-center gap-3 mb-6">
            <h2 className="text-lg font-bold text-white">Pipeline Stages</h2>
            {pipelineRunning && (
              <span className="flex items-center gap-1.5 text-xs text-atlas-400">
                <span className="w-2 h-2 bg-atlas-400 rounded-full animate-pulse" />
                Processing...
              </span>
            )}
            {pipelineResult && (
              <span className={`text-xs font-semibold ${
                metrics.finalStatus === 'APPROVED' ? 'text-emerald-400' :
                metrics.finalStatus === 'REJECTED' ? 'text-red-400' : 'text-orange-400'
              }`}>
                {metrics.finalStatus} in {metrics.elapsed}ms
              </span>
            )}
          </div>

          <div className="space-y-0">
            {pipelineStages.map((stage, i) => (
              <PipelineStep
                key={stage.id}
                stage={stage}
                isLast={i === pipelineStages.length - 1}
              />
            ))}
          </div>
        </div>

        {/* Right Panel — Metrics + Logs */}
        <div className="space-y-4">
          <PipelineMetrics metrics={metrics} />
          <PipelineLogs logs={pipelineLogs} />
        </div>
      </div>
    </div>
  )
}
