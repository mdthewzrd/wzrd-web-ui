import { useApi } from '../hooks/useApi'
import Panel from './Panel'

export default function FleetPanel() {
  const { data, isLoading } = useApi('/wzrd/fleet', 15000)

  if (isLoading && !data) {
    return (
      <Panel title="Fleet Coordination" className="col-span-full">
        <div className="glow text-[13px] animate-pulse">Loading fleet data...</div>
      </Panel>
    )
  }

  const agents: any[] = data?.agents ?? []
  const activeCount: number = data?.active_count ?? agents.filter((a: any) => a.status === 'active').length
  const coordinationStatus: string = data?.coordination_status ?? data?.status ?? 'unknown'

  const statusColors: Record<string, string> = {
    active: 'var(--hud-success)',
    idle: 'var(--hud-warning)',
    offline: 'var(--hud-error)',
    unknown: 'var(--hud-text-dim)',
  }

  const coordColors: Record<string, string> = {
    synchronized: 'var(--hud-success)',
    coordinating: 'var(--hud-warning)',
    degraded: 'var(--hud-error)',
    unknown: 'var(--hud-text-dim)',
  }

  return (
    <>
      {/* Fleet Overview */}
      <Panel title="Fleet Coordination" className="col-span-full">
        <div className="flex items-center gap-6 text-[13px]">
          <div className="flex items-center gap-2">
            <span style={{ color: 'var(--hud-text-dim)' }}>Active Agents:</span>
            <span className="text-[18px] font-bold" style={{ color: 'var(--hud-primary)' }}>{activeCount}</span>
          </div>
          <div className="flex items-center gap-2">
            <span style={{ color: 'var(--hud-text-dim)' }}>Coordination:</span>
            <span
              className="px-2 py-0.5 rounded text-[12px] uppercase font-bold tracking-wider"
              style={{ background: coordColors[coordinationStatus] || 'var(--hud-text-dim)', color: 'var(--hud-bg-deep)' }}
            >
              {coordinationStatus}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span style={{ color: 'var(--hud-text-dim)' }}>Total:</span>
            <span style={{ color: 'var(--hud-text)' }}>{agents.length}</span>
          </div>
        </div>
      </Panel>

      {/* Agent List */}
      <Panel title="Fleet Agents" className="col-span-full">
        <div className="space-y-1 text-[13px]">
          {agents.length === 0 && (
            <div style={{ color: 'var(--hud-text-dim)' }}>No fleet agents registered.</div>
          )}
          {agents.map((agent: any) => {
            const status = agent.status ?? 'unknown'
            const color = statusColors[status] || 'var(--hud-text-dim)'
            const roles: string[] = agent.roles ?? (agent.role ? [agent.role] : [])

            return (
              <div
                key={agent.name}
                className="flex items-center justify-between p-2"
                style={{ borderBottom: '1px solid var(--hud-border)' }}
              >
                <div className="flex items-center gap-3">
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ background: color }}
                    title={status}
                  />
                  <div>
                    <span className="font-bold" style={{ color: 'var(--hud-primary)' }}>{agent.name}</span>
                    {roles.length > 0 && (
                      <span className="ml-2" style={{ color: 'var(--hud-text-dim)' }}>
                        [{roles.join(', ')}]
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className="px-1.5 py-0.5 rounded text-[11px] uppercase"
                    style={{ color }}
                  >
                    {status}
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </Panel>
    </>
  )
}
