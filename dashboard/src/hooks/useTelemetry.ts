import { useState, useEffect, useRef, useCallback } from 'react'
import type { TelemetryRecord, ConnectionStatus } from '../types/telemetry'
import { fetchLatestTelemetry, fetchTelemetryHistory } from '../services/api'

export function useTelemetry(pollIntervalMs = 3000) {
  const [latest, setLatest] = useState<TelemetryRecord | null>(null)
  const [history, setHistory] = useState<TelemetryRecord[]>([])
  const [status, setStatus] = useState<ConnectionStatus>('INITIALIZING')
  const [error, setError] = useState<string | null>(null)
  const [timeRangeMinutes, setTimeRangeMinutes] = useState<number>(15)

  const isFetchingRef = useRef<boolean>(false)
  const lastSuccessRef = useRef<number>(0)

  const loadData = useCallback(async () => {
    if (isFetchingRef.current) return
    isFetchingRef.current = true

    try {
      // 1. Fetch latest telemetry snapshot
      const current = await fetchLatestTelemetry()
      setLatest(current)
      lastSuccessRef.current = Date.now()
      setError(null)

      // Check if data is stale (record timestamp is older than 20 seconds from wall clock)
      const nowEpoch = Date.now() / 1000
      const ageSeconds = nowEpoch - current.timestamp
      if (ageSeconds > 25) {
        setStatus('STALE')
      } else {
        setStatus('CONNECTED')
      }

      // 2. Fetch history for the active time range
      const windowSeconds = timeRangeMinutes * 60
      const startTs = nowEpoch - windowSeconds
      const historyRes = await fetchTelemetryHistory({
        start: startTs,
        limit: 100,
      })
      setHistory(historyRes.data)
    } catch (err: any) {
      const msg = err.message || 'Failed to connect to SYSWATCH backend'
      setError(msg)
      // If we haven't succeeded recently, mark disconnected
      if (Date.now() - lastSuccessRef.current > 6000) {
        setStatus('DISCONNECTED')
      }
    } finally {
      isFetchingRef.current = false
    }
  }, [timeRangeMinutes])

  useEffect(() => {
    // Initial fetch
    loadData()

    // Configurable polling interval
    const interval = setInterval(() => {
      loadData()
    }, pollIntervalMs)

    return () => clearInterval(interval)
  }, [loadData, pollIntervalMs])

  return {
    latest,
    history,
    status,
    error,
    timeRangeMinutes,
    setTimeRangeMinutes,
    refresh: loadData,
  }
}

