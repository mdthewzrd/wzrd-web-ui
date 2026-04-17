import { useState, useEffect, useCallback } from 'react'

interface TreeNode {
  name: string
  path: string
  icon: string
  is_dir: boolean
  children?: TreeNode[] | null
  size?: number
}

interface FileContent {
  path: string
  content: string
  size: number
  name: string
}

const API_BASE = '/api/files'

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function TreeItem({
  node,
  depth,
  selectedPath,
  onSelect,
  onExpand,
  expandedPaths,
}: {
  node: TreeNode
  depth: number
  selectedPath: string
  onSelect: (node: TreeNode) => void
  onExpand: (node: TreeNode) => void
  expandedPaths: Set<string>
}) {
  const isExpanded = expandedPaths.has(node.path)
  const isSelected = selectedPath === node.path
  const hasChildren = node.is_dir && node.children && node.children.length > 0

  return (
    <div>
      <div
        onClick={() => {
          onSelect(node)
          if (node.is_dir) onExpand(node)
        }}
        style={{
          paddingLeft: `${depth * 16 + 8}px`,
          paddingRight: '8px',
          paddingTop: '3px',
          paddingBottom: '3px',
          cursor: 'pointer',
          background: isSelected ? 'var(--hud-bg-hover)' : 'transparent',
          borderLeft: isSelected ? '2px solid var(--hud-primary)' : '2px solid transparent',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          fontSize: '13px',
          color: isSelected ? 'var(--hud-primary)' : 'var(--hud-text)',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}
        title={node.path}
      >
        {node.is_dir && (
          <span style={{ fontSize: '10px', opacity: 0.6, width: '12px', textAlign: 'center' }}>
            {hasChildren ? (isExpanded ? '▼' : '▶') : '·'}
          </span>
        )}
        <span>{node.icon}</span>
        <span>{node.name}</span>
        {!node.is_dir && node.size !== undefined && (
          <span style={{ marginLeft: 'auto', opacity: 0.4, fontSize: '11px' }}>
            {formatSize(node.size)}
          </span>
        )}
      </div>
      {isExpanded && node.children && (
        <div>
          {node.children.map(child => (
            <TreeItem
              key={child.path}
              node={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              onSelect={onSelect}
              onExpand={onExpand}
              expandedPaths={expandedPaths}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function FilesPanel() {
  const [tree, setTree] = useState<TreeNode | null>(null)
  const [selectedPath, setSelectedPath] = useState('')
  const [fileContent, setFileContent] = useState<FileContent | null>(null)
  const [editContent, setEditContent] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set(['.']))
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [saveStatus, setSaveStatus] = useState('')

  const loadTree = useCallback(async (path = '.') => {
    try {
      const res = await fetch(`${API_BASE}/tree?path=${encodeURIComponent(path)}`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setTree(data)
    } catch (e: any) {
      setError(e.message)
    }
  }, [])

  useEffect(() => { loadTree() }, [loadTree])

  const handleSelect = useCallback(async (node: TreeNode) => {
    setSelectedPath(node.path)
    if (!node.is_dir) {
      setLoading(true)
      setError('')
      try {
        const res = await fetch(`${API_BASE}/read?path=${encodeURIComponent(node.path)}`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setFileContent(data)
        setEditContent(data.content)
        setIsEditing(false)
      } catch (e: any) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    } else {
      setFileContent(null)
      setIsEditing(false)
    }
  }, [])

  const handleExpand = useCallback((node: TreeNode) => {
    setExpandedPaths(prev => {
      const next = new Set(prev)
      if (next.has(node.path)) next.delete(node.path)
      else next.add(node.path)
      return next
    })
  }, [])

  const handleSave = useCallback(async () => {
    if (!fileContent) return
    setSaveStatus('Saving...')
    try {
      const res = await fetch(`${API_BASE}/write`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: fileContent.path, content: editContent }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setSaveStatus('Saved!')
      setFileContent(prev => prev ? { ...prev, content: editContent } : null)
      setTimeout(() => setSaveStatus(''), 2000)
    } catch (e: any) {
      setSaveStatus(`Error: ${e.message}`)
    }
  }, [fileContent, editContent])

  // Breadcrumb
  const breadcrumbs = selectedPath
    ? selectedPath.split('/').filter(Boolean)
    : []

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '260px 1fr',
      gap: '0',
      height: '100%',
      background: 'var(--hud-bg-deep)',
      border: '1px solid var(--hud-border)',
      borderRadius: '6px',
      overflow: 'hidden',
    }}>
      {/* Sidebar: File tree */}
      <div style={{
        borderRight: '1px solid var(--hud-border)',
        overflowY: 'auto',
        background: 'var(--hud-bg-surface)',
      }}>
        <div style={{
          padding: '8px 12px',
          borderBottom: '1px solid var(--hud-border)',
          fontSize: '12px',
          textTransform: 'uppercase',
          letterSpacing: '0.1em',
          color: 'var(--hud-text-dim)',
          fontWeight: 600,
        }}>
          📁 File Explorer
        </div>
        <div style={{ padding: '4px 0' }}>
          <button
            onClick={() => loadTree()}
            style={{
              width: '100%',
              padding: '4px 12px',
              textAlign: 'left',
              fontSize: '12px',
              cursor: 'pointer',
              background: 'transparent',
              border: 'none',
              color: 'var(--hud-text-dim)',
            }}
          >
            ↻ Refresh
          </button>
          {tree && (
            <TreeItem
              node={tree}
              depth={0}
              selectedPath={selectedPath}
              onSelect={handleSelect}
              onExpand={handleExpand}
              expandedPaths={expandedPaths}
            />
          )}
        </div>
      </div>

      {/* Main: File viewer/editor */}
      <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Breadcrumb bar */}
        <div style={{
          padding: '6px 12px',
          borderBottom: '1px solid var(--hud-border)',
          background: 'var(--hud-bg-surface)',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          fontSize: '12px',
          color: 'var(--hud-text-dim)',
          flexShrink: 0,
          overflow: 'hidden',
        }}>
          <span
            style={{ cursor: 'pointer', color: 'var(--hud-primary)' }}
            onClick={() => { setSelectedPath(''); setFileContent(null); setIsEditing(false); }}
          >
            root
          </span>
          {breadcrumbs.map((part, i) => (
            <span key={i} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ opacity: 0.4 }}>/</span>
              <span>{part}</span>
            </span>
          ))}
          {fileContent && (
            <span style={{ marginLeft: 'auto', fontSize: '11px', opacity: 0.5 }}>
              {formatSize(fileContent.size)}
            </span>
          )}
        </div>

        {/* Content area */}
        <div style={{ flex: '1 1 0', overflow: 'auto', padding: '0' }}>
          {error && (
            <div style={{ padding: '16px', color: '#e74c3c', fontSize: '13px' }}>
              Error: {error}
            </div>
          )}
          {loading && (
            <div style={{ padding: '16px', color: 'var(--hud-text-dim)', fontSize: '13px' }}>
              Loading...
            </div>
          )}
          {!fileContent && !loading && !error && (
            <div style={{
              padding: '40px',
              textAlign: 'center',
              color: 'var(--hud-text-dim)',
              fontSize: '13px',
              opacity: 0.6,
            }}>
              Select a file to view its contents
            </div>
          )}
          {fileContent && !isEditing && (
            <pre style={{
              padding: '12px',
              fontSize: '13px',
              lineHeight: '1.5',
              fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
              color: 'var(--hud-text)',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              margin: 0,
              minHeight: '100%',
            }}>
              {fileContent.content}
            </pre>
          )}
          {fileContent && isEditing && (
            <textarea
              value={editContent}
              onChange={e => setEditContent(e.target.value)}
              style={{
                width: '100%',
                height: '100%',
                padding: '12px',
                fontSize: '13px',
                lineHeight: '1.5',
                fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                color: 'var(--hud-text)',
                background: 'var(--hud-bg-deep)',
                border: 'none',
                outline: 'none',
                resize: 'none',
                boxSizing: 'border-box',
              }}
              spellCheck={false}
            />
          )}
        </div>

        {/* Action bar */}
        {fileContent && (
          <div style={{
            padding: '6px 12px',
            borderTop: '1px solid var(--hud-border)',
            background: 'var(--hud-bg-surface)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            flexShrink: 0,
          }}>
            {!isEditing ? (
              <button
                onClick={() => setIsEditing(true)}
                style={{
                  padding: '3px 12px',
                  fontSize: '12px',
                  cursor: 'pointer',
                  background: 'var(--hud-primary)',
                  color: '#000',
                  border: 'none',
                  borderRadius: '3px',
                  fontWeight: 600,
                }}
              >
                ✏️ Edit
              </button>
            ) : (
              <>
                <button
                  onClick={handleSave}
                  style={{
                    padding: '3px 12px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    background: '#00ff88',
                    color: '#000',
                    border: 'none',
                    borderRadius: '3px',
                    fontWeight: 600,
                  }}
                >
                  💾 Save
                </button>
                <button
                  onClick={() => {
                    setIsEditing(false)
                    setEditContent(fileContent.content)
                  }}
                  style={{
                    padding: '3px 12px',
                    fontSize: '12px',
                    cursor: 'pointer',
                    background: 'transparent',
                    color: 'var(--hud-text-dim)',
                    border: '1px solid var(--hud-border)',
                    borderRadius: '3px',
                  }}
                >
                  Cancel
                </button>
              </>
            )}
            {saveStatus && (
              <span style={{ fontSize: '12px', color: 'var(--hud-primary)' }}>{saveStatus}</span>
            )}
            <span style={{ marginLeft: 'auto', fontSize: '11px', color: 'var(--hud-text-dim)', opacity: 0.5 }}>
              {fileContent.name}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
