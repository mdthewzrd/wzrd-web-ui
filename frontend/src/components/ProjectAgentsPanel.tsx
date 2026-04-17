import { useApi } from '../hooks/useApi'
import Panel from './Panel'

export default function ProjectAgentsPanel() {
  const { data, isLoading } = useApi('/wzrd/agents', 30000)

  if (isLoading && !data) {
    return (
      <Panel title="Project Agents" className="col-span-full">
        <div className="glow text-[13px] animate-pulse">Loading agents...</div>
      </Panel>
    )
  }

  const agents: any[] = data?.agents || []

  if (agents.length === 0) {
    return (
      <Panel title="Project Agents" className="col-span-full">
        <div className="text-[13px]" style={{ color: 'var(--hud-text-dim)' }}>
          No project agents found. Configure agents in your project settings.
        </div>
      </Panel>
    )
  }

  return (
    <>
      {agents.map((agent: any) => {
        const modes: string[] = agent.modes || []
        const sandboxStatus = agent.sandbox_status ?? 'unknown'
        const statusColors: Record<string, string> = {
          running: 'var(--hud-success)',
          stopped: 'var(--hud-warning)',
          missing: 'var(--hud-error)',
          unknown: 'var(--hud-text-dim)',
        }

        return (
          <Panel
            key={agent.name}
            title={agent.name}
            className="col-span-1"
          >
            <div className="space-y-2 text-[13px]">
              {/* Description */}
              {agent.description && (
                <div style={{ color: 'var(--hud-text-dim)' }}>{agent.description}</div>
              )}

              {/* Sandbox Status */}
              <div className="flex items-center gap-2">
                <span style={{ color: 'var(--hud-text-dim)' }}>Sandbox:</span>
                <span
                  className="px-1.5 py-0.5 rounded text-[11px] uppercase"
                  style={{ background: statusColors[sandboxStatus] || 'var(--hud-text-dim)', color: 'var(--hud-bg-deep)' }}
                >
                  {sandboxStatus}
                </span>
              </div>

              {/* Counts */}
              <div className="flex gap-4">
                <div>
                  <span style={{ color: 'var(--hud-text-dim)' }}>Blueprints: </span>
                  <span style={{ color: 'var(--hud-primary)' }}>{agent.blueprint_count ?? agent.blueprints ?? 0}</span>
                </div>
                <div>
                  <span style={{ color: 'var(--hud-text-dim)' }}>Skills: </span>
                  <span style={{ color: 'var(--hud-primary)' }}>{agent.skill_count ?? agent.skills ?? 0}</span>
                </div>
              </div>

              {/* Modes */}
              {modes.length > 0 && (
                <div className="pt-2 mt-2" style={{ borderTop: '1px solid var(--hud-border)' }}>
                  <div className="mb-1" style={{ color: 'var(--hud-text-dim)' }}>Modes:</div>
                  <div className="flex flex-wrap gap-1">
                    {modes.map((m: string) => (
                      <span
                        key={m}
                        className="px-1.5 py-0.5 text-[11px] rounded"
                        style={{ background: 'var(--hud-bg-deep)', border: '1px solid var(--hud-border)', color: 'var(--hud-text)' }}
                      >
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Panel>
        )
      })}
    </>
  )
}
