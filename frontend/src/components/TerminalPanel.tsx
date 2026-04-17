import { useEffect, useRef, useState, useCallback } from 'react'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'
import '@xterm/xterm/css/xterm.css'

function getWsUrl(): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.hostname}:3001/ws/terminal`
}

export default function TerminalPanel() {
  const termRef = useRef<HTMLDivElement>(null)
  const xtermRef = useRef<Terminal | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const fitAddonRef = useRef<FitAddon | null>(null)
  const [status, setStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected')

  const connect = useCallback(() => {
    if (wsRef.current) {
      try { wsRef.current.close() } catch (_) {}
    }

    setStatus('connecting')
    const ws = new WebSocket(getWsUrl())
    wsRef.current = ws

    ws.onopen = () => {
      setStatus('connected')
      // Send initial resize
      if (xtermRef.current && fitAddonRef.current) {
        const dims = fitAddonRef.current.proposeDimensions()
        if (dims) {
          ws.send(JSON.stringify({ type: 'resize', cols: dims.cols, rows: dims.rows }))
        }
      }
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'output' && xtermRef.current) {
          xtermRef.current.write(msg.data)
        }
      } catch (_) {
        // fallback: write raw text
        if (xtermRef.current) {
          xtermRef.current.write(event.data)
        }
      }
    }

    ws.onclose = () => {
      setStatus('disconnected')
    }

    ws.onerror = () => {
      setStatus('disconnected')
    }
  }, [])

  useEffect(() => {
    if (!termRef.current) return

    const xterm = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
      theme: {
        background: '#0a0a0f',
        foreground: '#c8d6e5',
        cursor: '#00ff88',
        cursorAccent: '#0a0a0f',
        selectionBackground: '#264f78',
        black: '#0a0a0f',
        red: '#e74c3c',
        green: '#00ff88',
        yellow: '#f1c40f',
        blue: '#3498db',
        magenta: '#9b59b6',
        cyan: '#1abc9c',
        white: '#ecf0f1',
        brightBlack: '#636e72',
        brightRed: '#ff6b6b',
        brightGreen: '#00ff88',
        brightYellow: '#ffeaa7',
        brightBlue: '#74b9ff',
        brightMagenta: '#a29bfe',
        brightCyan: '#55efc4',
        brightWhite: '#ffffff',
      },
      allowProposedApi: true,
    })

    const fitAddon = new FitAddon()
    xterm.loadAddon(fitAddon)
    xterm.loadAddon(new WebLinksAddon())

    xterm.open(termRef.current)
    fitAddon.fit()

    xtermRef.current = xterm
    fitAddonRef.current = fitAddon

    // Input handler
    xterm.onData((data) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'input', data }))
      }
    })

    // Connect WebSocket
    connect()

    // Resize observer
    const resizeObserver = new ResizeObserver(() => {
      try {
        fitAddon.fit()
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          const dims = fitAddon.proposeDimensions()
          if (dims) {
            wsRef.current.send(JSON.stringify({ type: 'resize', cols: dims.cols, rows: dims.rows }))
          }
        }
      } catch (_) {}
    })

    resizeObserver.observe(termRef.current)

    return () => {
      resizeObserver.disconnect()
      xterm.dispose()
      if (wsRef.current) {
        try { wsRef.current.close() } catch (_) {}
        wsRef.current = null
      }
      xtermRef.current = null
      fitAddonRef.current = null
    }
  }, [connect])

  const handleReconnect = () => {
    if (xtermRef.current) {
      xtermRef.current.clear()
    }
    connect()
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', background: '#0a0a0f' }}>
      {/* Status bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '4px 12px',
        background: 'var(--hud-bg-surface)',
        borderBottom: '1px solid var(--hud-border)',
        fontSize: '12px',
        color: 'var(--hud-text-dim)',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%',
            background: status === 'connected' ? '#00ff88' : status === 'connecting' ? '#f1c40f' : '#e74c3c',
            display: 'inline-block',
            boxShadow: status === 'connected' ? '0 0 6px #00ff88' : 'none',
          }} />
          <span style={{ textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            {status === 'connected' ? 'Connected' : status === 'connecting' ? 'Connecting...' : 'Disconnected'}
          </span>
        </div>
        {status === 'disconnected' && (
          <button
            onClick={handleReconnect}
            style={{
              background: 'var(--hud-primary)',
              color: '#000',
              border: 'none',
              padding: '2px 10px',
              fontSize: '11px',
              cursor: 'pointer',
              borderRadius: '3px',
              fontWeight: 600,
            }}
          >
            Reconnect
          </button>
        )}
        <span style={{ opacity: 0.5 }}>bash — PTY</span>
      </div>
      {/* Terminal container */}
      <div ref={termRef} style={{ flex: '1 1 0', padding: '4px', overflow: 'hidden' }} />
    </div>
  )
}
