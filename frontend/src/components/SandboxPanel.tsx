import { useState } from 'react'
import { useApi } from '../hooks/useApi'
import Panel from './Panel'

const STATUS_COLORS: Record<string, string> = {
  running: 'var(--hud-success)',
  stopped: 'var(--hud-warning)',
  missing: 'var(--hud-error)',
}

export default function SandboxPanel() {
  const { data, isLoading, mutate } = useApi('/wzrd/sandboxes', 15000)
  const [newName, setNewName] = useState('')
  const [newProfile, setNewProfile] = useState('default')
  const [newProjectDir, setNewProjectDir] = useState('')
  const [execName, setExecName] = useState('')
  const [execCmd, setExecCmd] = useState('')
  const [creating, setCreating] = useState(false)
  const [execResult, setExecResult] = useState<string | null>(null)

  const sandboxes: any[] = data?.sandboxes || []

  async function createSandbox(e: React.FormEvent) {
    e.preventDefault()
    if (!newName.trim()) return
    setCreating(true)
    try {
      const body: any = { name: newName.trim(), profile: newProfile }
      if (newProjectDir.trim()) body.project_dir = newProjectDir.trim()
      await fetch('/api/wzrd/sandboxes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      setNewName('')
      setNewProjectDir('')
      mutate()
    } finally {
      setCreating(false)
    }
  }

  async function deleteSandbox(name: string) {
    await fetch(`/api/wzrd/sandboxes/${encodeURIComponent(name)}`, { method: 'DELETE' })
    mutate()
  }

  async function execCommand(e: React.FormEvent) {
    e.preventDefault()
    if (!execName.trim() || !execCmd.trim()) return
    setExecResult(null)
    try {
      const res = await fetch(`/api/wzrd/sandboxes/${encodeURIComponent(execName)}/exec`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: execCmd }),
      })
      const json = await res.json()
      setExecResult(JSON.stringify(json, null, 2))
    } catch (err: any) {
      setExecResult(`Error: ${err.message}`)
    }
  }

  if (isLoading && !data) {
    return (
      <Panel title="Docker Sandboxes" className="col-span-full">
        <div className="glow text-[13px] animate-pulse">Loading sandboxes...</div>
      </Panel>
    )
  }

  return (
    <>
      {/* Sandbox List */}
      <Panel title="Docker Sandboxes" className="col-span-full">
        <div className="space-y-2 text-[13px]">
          {sandboxes.length === 0 && (
            <div style={{ color: 'var(--hud-text-dim)' }}>No sandboxes configured.</div>
          )}
          {sandboxes.map((sb: any) => {
            const status = sb.status ?? 'unknown'
            const color = STATUS_COLORS[status] || 'var(--hud-text-dim)'
            return (
              <div key={sb.name} className="p-2" style={{ border: '1px solid var(--hud-border)' }}>
                <div className="flex justify-between items-start mb-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold" style={{ color: 'var(--hud-primary)' }}>{sb.name}</span>
                    <span
                      className="px-1.5 py-0.5 rounded text-[11px] uppercase"
                      style={{ background: color, color: 'var(--hud-bg-deep)' }}
                    >
                      {status}
                    </span>
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => { setExecName(sb.name); setExecCmd(''); setExecResult(null) }}
                      className="px-2 py-0.5 text-[11px] cursor-pointer"
                      style={{ border: '1px solid var(--hud-primary)', color: 'var(--hud-primary)', background: 'transparent' }}
                    >
                      Exec
                    </button>
                    <button
                      onClick={() => deleteSandbox(sb.name)}
                      className="px-2 py-0.5 text-[11px] cursor-pointer"
                      style={{ border: '1px solid var(--hud-error)', color: 'var(--hud-error)', background: 'transparent' }}
                    >
                      Delete
                    </button>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-0.5" style={{ color: 'var(--hud-text-dim)' }}>
                  <div>Profile: <span style={{ color: 'var(--hud-text)' }}>{sb.profile ?? '-'}</span></div>
                  <div>Container: <span style={{ color: 'var(--hud-text)' }}>{sb.container_id ? sb.container_id.substring(0, 12) : '-'}</span></div>
                  <div>Created: <span style={{ color: 'var(--hud-text)' }}>{sb.created ?? '-'}</span></div>
                </div>
              </div>
            )
          })}
        </div>
      </Panel>

      {/* Create Sandbox */}
      <Panel title="Create Sandbox" className="col-span-1">
        <form onSubmit={createSandbox} className="space-y-2 text-[13px]">
          <div>
            <label className="block mb-1" style={{ color: 'var(--hud-text-dim)' }}>Name</label>
            <input
              value={newName}
              onChange={e => setNewName(e.target.value)}
              placeholder="my-sandbox"
              className="w-full px-2 py-1 text-[13px]"
              style={{ background: 'var(--hud-bg-deep)', border: '1px solid var(--hud-border)', color: 'var(--hud-text)' }}
            />
          </div>
          <div>
            <label className="block mb-1" style={{ color: 'var(--hud-text-dim)' }}>Profile</label>
            <select
              value={newProfile}
              onChange={e => setNewProfile(e.target.value)}
              className="w-full px-2 py-1 text-[13px]"
              style={{ background: 'var(--hud-bg-deep)', border: '1px solid var(--hud-border)', color: 'var(--hud-text)' }}
            >
              <option value="default">default</option>
              <option value="python">python</option>
              <option value="node">node</option>
              <option value="fullstack">fullstack</option>
            </select>
          </div>
          <div>
            <label className="block mb-1" style={{ color: 'var(--hud-text-dim)' }}>Project Dir (optional)</label>
            <input
              value={newProjectDir}
              onChange={e => setNewProjectDir(e.target.value)}
              placeholder="/path/to/project"
              className="w-full px-2 py-1 text-[13px]"
              style={{ background: 'var(--hud-bg-deep)', border: '1px solid var(--hud-border)', color: 'var(--hud-text)' }}
            />
          </div>
          <button
            type="submit"
            disabled={creating}
            className="px-3 py-1 text-[13px] cursor-pointer"
            style={{ border: '1px solid var(--hud-primary)', color: 'var(--hud-primary)', background: 'transparent', opacity: creating ? 0.5 : 1 }}
          >
            {creating ? 'Creating...' : 'Create'}
          </button>
        </form>
      </Panel>

      {/* Exec Command */}
      <Panel title="Exec Command" className="col-span-1">
        <form onSubmit={execCommand} className="space-y-2 text-[13px]">
          <div>
            <label className="block mb-1" style={{ color: 'var(--hud-text-dim)' }}>Sandbox Name</label>
            <input
              value={execName}
              onChange={e => setExecName(e.target.value)}
              placeholder="sandbox-name"
              className="w-full px-2 py-1 text-[13px]"
              style={{ background: 'var(--hud-bg-deep)', border: '1px solid var(--hud-border)', color: 'var(--hud-text)' }}
            />
          </div>
          <div>
            <label className="block mb-1" style={{ color: 'var(--hud-text-dim)' }}>Command</label>
            <input
              value={execCmd}
              onChange={e => setExecCmd(e.target.value)}
              placeholder="ls -la"
              className="w-full px-2 py-1 text-[13px]"
              style={{ background: 'var(--hud-bg-deep)', border: '1px solid var(--hud-border)', color: 'var(--hud-text)' }}
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1 text-[13px] cursor-pointer"
            style={{ border: '1px solid var(--hud-primary)', color: 'var(--hud-primary)', background: 'transparent' }}
          >
            Execute
          </button>
        </form>
        {execResult && (
          <pre
            className="mt-2 p-2 text-[12px] overflow-auto max-h-48"
            style={{ background: 'var(--hud-bg-deep)', border: '1px solid var(--hud-border)', color: 'var(--hud-text)' }}
          >
            {execResult}
          </pre>
        )}
      </Panel>
    </>
  )
}
