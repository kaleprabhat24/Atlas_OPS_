export default function StatusBadge({ status, children }) {
  const styles = {
    completed: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20',
    active: 'bg-atlas-500/15 text-atlas-400 border border-atlas-500/20',
    failed: 'bg-red-500/15 text-red-400 border border-red-500/20',
    pending: 'bg-slate-500/10 text-slate-500 border border-slate-500/10',
    skipped: 'bg-amber-500/10 text-amber-400 border border-amber-500/20',
    APPROVED: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20',
    REJECTED: 'bg-red-500/15 text-red-400 border border-red-500/20',
    FAILED: 'bg-orange-500/15 text-orange-400 border border-orange-500/20',
    PENDING: 'bg-slate-500/10 text-slate-500 border border-slate-500/10',
    healthy: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20',
    degraded: 'bg-amber-500/15 text-amber-400 border border-amber-500/20',
    closed: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20',
    open: 'bg-red-500/15 text-red-400 border border-red-500/20',
    'half-open': 'bg-amber-500/15 text-amber-400 border border-amber-500/20',
    loaded: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20',
    fallback: 'bg-amber-500/15 text-amber-400 border border-amber-500/20',
  }

  return (
    <span className={`status-badge ${styles[status] || styles.pending}`}>
      {children || status}
    </span>
  )
}
