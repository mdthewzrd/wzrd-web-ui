import { useApi } from '../hooks/useApi'
import Panel from './Panel'

const PHASES = ['plan', 'implement', 'validate', 'learn'] as const

const PHASE_COLORS: Record<string, string> = {
  plan: '#60a5fa',
  implement: '#34d399',
  validate: '#fbbf24',
  learn: '#c084fc',
}

const PHASE_LABELS: Record<string, string> = {
  plan: 'Plan',
  implement: 'Implement',
  validate: 'Validate',
  learn: 'Learn',
}

export default function PIVPanel() {
  const { data, isLoading } = useApi('/wzrd/piv', 15000)

  if (isLoading && !data) {
    return (
      <Panel title="PIV Workflow" className="col-span-full">
        <div className="glow text-[13px] animate-pulse">Loading PIV data...</div>
      </Panel>
    )
  }

  const currentPhase: string = data?.current_phase ?? data?.phase ?? ''
  const task: string = data?.task ?? data?.task_description ?? ''
  const history: any[] = data?.history ?? data?.phases ?? []

  const phaseIndex = PHASES.indexOf(currentPhase as any)
  const progressPct = phaseIndex >= 0 ? ((phaseIndex + 1) / PHASES.length) * 100 : 0

  return (
    <>
      {/* Current Phase + Progress */}
      <Panel title="PIV Workflow Tracker" className="col-span-full">
        <div className="space-y-3 text-[13px]">
          {/* Progress bar */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span style={{ color: 'var(--hud-text-dim)' }}>Cycle Progress</span>
              <span style={{ color: 'var(--hud-primary)' }}>{progressPct.toFixed(0)}%</span>
            </div>
            <div className="flex gap-0.5 h-6">
              {PHASES.map((phase, i) => {
                const isActive = phase === currentPhase
                const isPast = i < phaseIndex
                const color = PHASE_COLORS[phase] || 'var(--hud-primary)'
                return (
                  <div
                    key={phase}
                    className="flex-1 flex items-center justify-center text-[11px] uppercase tracking-wider font-bold rounded-sm"
                    style={{
                      background: isActive ? color : isPast ? `${color}30` : 'var(--hud-bg-deep)',
                      color: isActive ? 'var(--hud-bg-deep)' : isPast ? color : 'var(--hud-text-dim)',
                      border: isActive ? 'none' : '1px solid var(--hud-border)',
                    }}
                  >
                    {PHASE_LABELS[phase]}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Current task */}
          {task && (
            <div className="p-2" style={{ background: 'var(--hud-bg-deep)', border: '1px solid var(--hud-border)' }}>
              <div className="mb-1 text-[11px] uppercase tracking-wider" style={{ color: 'var(--hud-text-dim)' }}>Current Task</div>
              <div style={{ color: 'var(--hud-text)' }}>{task}</div>
            </div>
          )}

          {/* Current phase detail */}
          {currentPhase && (
            <div className="flex items-center gap-2">
              <span style={{ color: 'var(--hud-text-dim)' }}>Current Phase:</span>
              <span
                className="px-2 py-0.5 rounded text-[12px] font-bold uppercase tracking-wider"
                style={{ background: PHASE_COLORS[currentPhase] || 'var(--hud-primary)', color: 'var(--hud-bg-deep)' }}
              >
                {PHASE_LABELS[currentPhase] || currentPhase}
              </span>
            </div>
          )}
        </div>
      </Panel>

      {/* Phase History */}
      <Panel title="Phase History" className="col-span-full">
        <div className="space-y-1 text-[13px]">
          {history.length === 0 && (
            <div style={{ color: 'var(--hud-text-dim)' }}>No phase history yet.</div>
          )}
          {history.map((entry: any, i: number) => {
            const phase = entry.phase ?? entry.name ?? ''
            const color = PHASE_COLORS[phase] || 'var(--hud-text-dim)'
            return (
              <div key={i} className="flex items-center gap-2 py-1">
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ background: color }}
                />
                <span className="font-bold uppercase tracking-wider text-[12px]" style={{ color }}>
                  {PHASE_LABELS[phase] || phase}
                </span>
                {entry.timestamp && (
                  <span style={{ color: 'var(--hud-text-dim)' }}>{entry.timestamp}</span>
                )}
                {entry.description && (
                  <span className="truncate" style={{ color: 'var(--hud-text-dim)' }}>
                    — {entry.description}
                  </span>
                )}
              </div>
            )
          })}
        </div>
      </Panel>
    </>
  )
}
