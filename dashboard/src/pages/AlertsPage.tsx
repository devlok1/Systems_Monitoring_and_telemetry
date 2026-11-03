import { useState, useEffect, useCallback } from 'react'
import type { AlertEntry } from '../types/telemetry'
import { fetchAlerts, dismissAlert } from '../services/api'

type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

const SEV_COLOR: Record<Severity, string> = {
  CRITICAL: '#f87171',
  HIGH: '#fb923c',
  MEDIUM: '#facc15',
  LOW: '#60a5fa',
}

const SEV_BG: Record<Severity, string> = {
  CRITICAL: 'rgba(248,113,113,0.08)',
  HIGH: 'rgba(251,146,60,0.08)',
  MEDIUM: 'rgba(250,204,21,0.06)',
  LOW: 'rgba(96,165,250,0.06)',
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertEntry[]>([])
  const [loading, setLoading] = useState(false)

  const loadAlerts = useCallback(async () => {
    setLoading(true)
    try {
      const data = await fetchAlerts(true)
      setAlerts(data)
    } catch {
      setAlerts([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAlerts()
  }, [loadAlerts])

  const handleDismiss = async (id: number) => {
    try {
      await dismissAlert(id)
      setAlerts(prev => prev.filter(a => a.id !== id))
    } catch {
      // Refresh on error
      loadAlerts()
    }
  }

  const counts: Record<Severity, number> = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 }
  alerts.forEach(a => {
    if (a.severity in counts) {
      counts[a.severity as Severity]++
    }
  })

  return (
    <div className="flex flex-col gap-4 font-mono">
      {/* Summary bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as Severity[]).map(s => (
          <div
            key={s}
            className="flex flex-col items-center py-3"
            style={{
              background: '#3e3e3e',
              border: `1px solid ${SEV_COLOR[s]}44`,
              borderTop: `3px solid ${SEV_COLOR[s]}`,
            }}
          >
            <span className="text-2xl font-bold" style={{ color: counts[s] > 0 ? SEV_COLOR[s] : '#555' }}>
              {counts[s]}
            </span>
            <span className="text-xs tracking-widest mt-1" style={{ color: '#888' }}>
              {s}
            </span>
          </div>
        ))}
      </div>

      {/* Header & Controls */}
      <div className="flex items-center justify-between px-2">
        <span className="text-xs tracking-widest" style={{ color: '#888' }}>
          {alerts.length} ACTIVE SYSTEM NOTIFICATIONS / ALERTS
        </span>
        <button
          onClick={loadAlerts}
          className="px-3 py-1 text-xs tracking-widest cursor-pointer"
          style={{ background: '#383838', border: '1px solid #555', color: '#ccc' }}
        >
          {loading ? 'CHECKING...' : 'REFRESH'}
        </button>
      </div>

      {/* Alert cards */}
      <div className="flex flex-col gap-3">
        {alerts.length > 0 ? (
          alerts.map(alert => {
            const sev = (alert.severity as Severity) || 'LOW'
            const timeStr = alert.timestamp_utc
              ? new Date(alert.timestamp_utc).toLocaleTimeString()
              : new Date(alert.timestamp * 1000).toLocaleTimeString()

            return (
              <div
                key={alert.id}
                className="flex gap-4 p-4 items-start"
                style={{
                  background: SEV_BG[sev] || '#333',
                  border: `1px solid ${SEV_COLOR[sev] || '#666'}44`,
                  borderLeft: `4px solid ${SEV_COLOR[sev] || '#666'}`,
                }}
              >
                <div className="flex flex-col items-center gap-1 shrink-0" style={{ minWidth: 72 }}>
                  <span
                    className="text-xs font-bold px-2 py-0.5"
                    style={{
                      background: (SEV_COLOR[sev] || '#888') + '22',
                      color: SEV_COLOR[sev] || '#888',
                      border: `1px solid ${SEV_COLOR[sev] || '#888'}`,
                    }}
                  >
                    {sev}
                  </span>
                  <span className="text-xs" style={{ color: '#666' }}>
                    {timeStr}
                  </span>
                </div>
                <div className="flex-1">
                  <div className="text-sm font-bold mb-1 text-white">
                    {alert.source ? `Notice from ${alert.source}` : 'System Alert'}
                  </div>
                  <div className="text-xs mb-1" style={{ color: '#888' }}>
                    source: <span style={{ color: '#a78bfa' }}>{alert.source || 'monitor'}</span>
                    {alert.hostname && <span style={{ color: '#666' }}> &nbsp;|&nbsp; host: {alert.hostname}</span>}
                  </div>
                  <div className="text-xs text-gray-300">
                    {alert.detail || 'Condition detected by monitoring telemetry.'}
                  </div>
                </div>
                <button
                  onClick={() => handleDismiss(alert.id)}
                  className="self-start text-xs px-2 py-1 shrink-0 cursor-pointer transition-colors"
                  style={{ color: '#aaa', border: '1px solid #555', background: '#2a2a2a' }}
                >
                  DISMISS
                </button>
              </div>
            )
          })
        ) : (
          <div
            className="p-8 text-center text-xs rounded"
            style={{ background: '#2a2a2a', border: '1px solid #444', color: '#4ade80' }}
          >
            ✓ All systems operating nominally. No active threshold alerts or errors.
          </div>
        )}
      </div>
    </div>
  )
}
