import { useState, useEffect, useCallback } from 'react'
import type { LogEntry } from '../types/telemetry'
import { fetchLogs } from '../services/api'

type Level = 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'

const LEVEL_COLOR: Record<Level, string> = {
  INFO: '#4ade80',
  WARN: '#facc15',
  ERROR: '#f87171',
  DEBUG: '#94a3b8',
}

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [filter, setFilter] = useState<Level | 'ALL'>('ALL')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)

  const loadLogs = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchLogs({
        level: filter,
        search: search || undefined,
        limit: 100,
      })
      setLogs(data)
    } catch {
      // Fallback empty list on error
      setLogs([])
    } finally {
      setLoading(false)
    }
  }, [filter, search])

  useEffect(() => {
    loadLogs()
  }, [loadLogs])

  return (
    <div className="flex flex-col gap-4 font-mono">
      {/* Controls */}
      <div
        className="flex flex-wrap gap-3 items-center"
        style={{ background: '#3e3e3e', border: '1px solid #555', padding: '10px 12px' }}
      >
        <span className="text-xs tracking-widest" style={{ color: '#888' }}>
          LEVEL:
        </span>
        {(['ALL', 'INFO', 'WARN', 'ERROR', 'DEBUG'] as const).map(lv => (
          <button
            key={lv}
            onClick={() => setFilter(lv)}
            className="px-3 py-1 text-xs tracking-widest transition-colors cursor-pointer"
            style={{
              background: filter === lv ? (lv === 'ALL' ? '#555' : LEVEL_COLOR[lv as Level] + '33') : 'transparent',
              color: lv === 'ALL' ? '#ccc' : LEVEL_COLOR[lv as Level],
              border: `1px solid ${lv === 'ALL' ? '#666' : LEVEL_COLOR[lv as Level]}`,
            }}
          >
            {lv}
          </button>
        ))}

        <input
          type="text"
          placeholder="search logs..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="ml-auto px-3 py-1 text-xs outline-none"
          style={{ background: '#2a2a2a', border: '1px solid #555', color: '#ccc', minWidth: 200 }}
        />

        <button
          onClick={loadLogs}
          className="px-3 py-1 text-xs tracking-widest cursor-pointer"
          style={{ background: '#444', border: '1px solid #666', color: '#ccc' }}
        >
          {loading ? 'REFRESHING...' : 'REFRESH'}
        </button>
      </div>

      {/* Log table */}
      <div style={{ background: '#2e2e2e', border: '1px solid #555' }}>
        <div
          className="flex text-xs px-3 py-2 font-bold"
          style={{ background: '#3a3a3a', borderBottom: '1px solid #555', color: '#888' }}
        >
          <span className="w-36">TIME</span>
          <span className="w-16">LEVEL</span>
          <span className="w-24">SOURCE</span>
          <span className="flex-1">MESSAGE</span>
        </div>
        <div style={{ maxHeight: 460, overflowY: 'auto' }}>
          {logs.length > 0 ? (
            logs.map((log, i) => {
              const timeStr = log.timestamp_utc
                ? new Date(log.timestamp_utc).toLocaleTimeString()
                : new Date(log.timestamp * 1000).toLocaleTimeString()
              return (
                <div
                  key={log.id || i}
                  className="flex items-start text-xs px-3 py-1.5"
                  style={{
                    borderBottom: '1px solid #333',
                    background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
                  }}
                >
                  <span className="w-36 shrink-0" style={{ color: '#666', fontVariantNumeric: 'tabular-nums' }}>
                    {timeStr}
                  </span>
                  <span className="w-16 shrink-0 font-bold" style={{ color: LEVEL_COLOR[log.level] || '#aaa' }}>
                    {log.level}
                  </span>
                  <span className="w-24 shrink-0 truncate" style={{ color: '#a78bfa' }}>
                    {log.source || 'syswatch'}
                  </span>
                  <span className="flex-1" style={{ color: log.level === 'ERROR' ? '#fca5a5' : '#ccc' }}>
                    {log.message}
                  </span>
                </div>
              )
            })
          ) : (
            <div className="py-12 text-center text-xs" style={{ color: '#777' }}>
              {loading ? 'Loading logs...' : 'No system logs recorded matching filter.'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

