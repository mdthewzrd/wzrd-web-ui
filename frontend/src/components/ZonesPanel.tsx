import { useApi } from '../hooks/useApi'
import Panel, { CapacityBar } from './Panel'

export default function ZonesPanel() {
  const { data, isLoading } = useApi('/wzrd/zones', 30000)

  if (isLoading && !data) {
    return (
      <Panel title="Memory Zones" className="col-span-full">
        <div className="glow text-[13px] animate-pulse">Loading zones...</div>
      </Panel>
    )
  }

  const zones: any[] = data?.zones || []

  if (zones.length === 0) {
    return (
      <Panel title="Memory Zones" className="col-span-full">
        <div className="text-[13px]" style={{ color: 'var(--hud-text-dim)' }}>
          No memory zones found. Start the WZRD agent to initialize zones.
        </div>
      </Panel>
    )
  }

  return (
    <>
      {zones.map((zone: any) => {
        const fileCount = zone.file_count ?? zone.files?.length ?? 0
        const totalSize = zone.total_size ?? 0
        const files: string[] = zone.files || []

        return (
          <Panel
            key={zone.id ?? zone.number ?? zone.name}
            title={`Zone ${zone.number ?? '?'}: ${zone.name ?? 'Unknown'}`}
            className="col-span-1"
          >
            <div className="space-y-2 text-[13px]">
              {/* Stats row */}
              <div className="flex justify-between">
                <span style={{ color: 'var(--hud-text-dim)' }}>Files</span>
                <span style={{ color: 'var(--hud-primary)' }}>{fileCount}</span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: 'var(--hud-text-dim)' }}>Total Size</span>
                <span style={{ color: 'var(--hud-primary)' }}>{formatSize(totalSize)}</span>
              </div>

              {/* Capacity bar if max capacity defined */}
              {zone.capacity != null && zone.capacity > 0 && (
                <CapacityBar
                  value={totalSize}
                  max={zone.capacity}
                  label="Capacity"
                />
              )}

              {/* File list */}
              {files.length > 0 && (
                <div className="mt-2 pt-2 space-y-0.5" style={{ borderTop: '1px solid var(--hud-border)' }}>
                  <div className="mb-1" style={{ color: 'var(--hud-text-dim)' }}>Files:</div>
                  {files.map((f: string, i: number) => (
                    <div key={i} className="truncate py-0.5" style={{ color: 'var(--hud-text)' }}>
                      📄 {f}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Panel>
        )
      })}
    </>
  )
}

function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`
}
