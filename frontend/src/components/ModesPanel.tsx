import { useApi } from '../hooks/useApi'
import Panel from './Panel'

const MODE_COLORS: Record<string, string> = {
  explore: '#60a5fa',
  build: '#34d399',
  refactor: '#a78bfa',
  debug: '#f87171',
  plan: '#fbbf24',
  review: '#2dd4bf',
  learn: '#c084fc',
  chat: '#94a3b8',
}

const MODE_DESCRIPTIONS: Record<string, string> = {
  explore: 'Investigate and discover codebases, APIs, and data',
  build: 'Create new features, files, and implementations',
  refactor: 'Restructure and improve existing code',
  debug: 'Diagnose and fix bugs and issues',
  plan: 'Strategic thinking and architecture design',
  review: 'Analyze code quality and suggest improvements',
  learn: 'Study patterns, documentation, and best practices',
  chat: 'General conversation and Q&A',
}

export default function ModesPanel() {
  const { data, isLoading, mutate } = useApi('/wzrd/modes', 15000)

  if (isLoading && !data) {
    return (
      <Panel title="Mode Switcher" className="col-span-full">
        <div className="glow text-[13px] animate-pulse">Loading modes...</div>
      </Panel>
    )
  }

  const currentMode: string = data?.current_mode ?? data?.mode ?? ''
  const modes: string[] = data?.modes ?? Object.keys(MODE_DESCRIPTIONS)

  async function switchMode(mode: string) {
    await fetch('/api/wzrd/modes', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode }),
    })
    mutate()
  }

  return (
    <>
      {/* Current Mode */}
      <Panel title="Current Mode" className="col-span-full">
        <div className="flex items-center gap-3 text-[13px]">
          <span
            className="px-3 py-1.5 rounded text-[15px] font-bold uppercase tracking-wider"
            style={{
              background: MODE_COLORS[currentMode] || 'var(--hud-primary)',
              color: 'var(--hud-bg-deep)',
            }}
          >
            {currentMode || 'Unknown'}
          </span>
          {MODE_DESCRIPTIONS[currentMode] && (
            <span style={{ color: 'var(--hud-text-dim)' }}>
              {MODE_DESCRIPTIONS[currentMode]}
            </span>
          )}
        </div>
      </Panel>

      {/* Mode Grid */}
      <Panel title="Available Modes" className="col-span-full">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {modes.map((mode: string) => {
            const isActive = mode === currentMode
            const color = MODE_COLORS[mode] || 'var(--hud-primary)'
            return (
              <button
                key={mode}
                onClick={() => switchMode(mode)}
                className="p-3 text-left transition-all duration-150 cursor-pointer"
                style={{
                  background: isActive ? 'var(--hud-bg-hover)' : 'var(--hud-bg-deep)',
                  border: isActive ? `2px solid ${color}` : '1px solid var(--hud-border)',
                  boxShadow: isActive ? `0 0 12px ${color}40` : 'none',
                }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ background: color }}
                  />
                  <span
                    className="font-bold uppercase tracking-wider text-[13px]"
                    style={{ color: isActive ? color : 'var(--hud-text)' }}
                  >
                    {mode}
                  </span>
                  {isActive && (
                    <span className="ml-auto text-[11px]" style={{ color: 'var(--hud-success)' }}>● ACTIVE</span>
                  )}
                </div>
                <div className="text-[12px]" style={{ color: 'var(--hud-text-dim)' }}>
                  {MODE_DESCRIPTIONS[mode] || 'No description'}
                </div>
              </button>
            )
          })}
        </div>
      </Panel>
    </>
  )
}
