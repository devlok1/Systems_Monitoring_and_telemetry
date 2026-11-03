import type {
  TelemetryRecord,
  HistoryResponse,
  StatsResponse,
  HealthResponse,
  LogEntry,
  AlertEntry,
} from '../types/telemetry'

const API_BASE_URL = (
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
).replace(/\/$/, '')

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const errorText = await res.text().catch(() => 'Network request failed')
    throw new Error(`API Error ${res.status}: ${errorText}`)
  }
  return res.json() as Promise<T>
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`)
  return handleResponse<HealthResponse>(res)
}

export async function fetchLatestTelemetry(hostname?: string): Promise<TelemetryRecord> {
  const url = new URL(`${API_BASE_URL}/telemetry/latest`)
  if (hostname) {
    url.searchParams.set('hostname', hostname)
  }
  const res = await fetch(url.toString())
  return handleResponse<TelemetryRecord>(res)
}

export async function fetchTelemetryHistory(options: {
  start?: number
  end?: number
  limit?: number
  offset?: number
  hostname?: string
} = {}): Promise<HistoryResponse> {
  const url = new URL(`${API_BASE_URL}/telemetry/history`)
  if (options.start !== undefined) url.searchParams.set('start', options.start.toString())
  if (options.end !== undefined) url.searchParams.set('end', options.end.toString())
  if (options.limit !== undefined) url.searchParams.set('limit', options.limit.toString())
  if (options.offset !== undefined) url.searchParams.set('offset', options.offset.toString())
  if (options.hostname) url.searchParams.set('hostname', options.hostname)

  const res = await fetch(url.toString())
  return handleResponse<HistoryResponse>(res)
}

export async function fetchStats(options: {
  start?: number
  end?: number
  hostname?: string
} = {}): Promise<StatsResponse> {
  const url = new URL(`${API_BASE_URL}/telemetry/stats`)
  if (options.start !== undefined) url.searchParams.set('start', options.start.toString())
  if (options.end !== undefined) url.searchParams.set('end', options.end.toString())
  if (options.hostname) url.searchParams.set('hostname', options.hostname)

  const res = await fetch(url.toString())
  return handleResponse<StatsResponse>(res)
}

export async function fetchLogs(options: {
  level?: string
  search?: string
  limit?: number
} = {}): Promise<LogEntry[]> {
  const url = new URL(`${API_BASE_URL}/logs`)
  if (options.level && options.level !== 'ALL') url.searchParams.set('level', options.level)
  if (options.search) url.searchParams.set('search', options.search)
  if (options.limit) url.searchParams.set('limit', options.limit.toString())

  const res = await fetch(url.toString())
  return handleResponse<LogEntry[]>(res)
}

export async function fetchAlerts(activeOnly = true): Promise<AlertEntry[]> {
  const url = new URL(`${API_BASE_URL}/alerts`)
  url.searchParams.set('active_only', activeOnly ? 'true' : 'false')
  const res = await fetch(url.toString())
  return handleResponse<AlertEntry[]>(res)
}

export async function dismissAlert(alertId: number): Promise<{ status: string; id: number }> {
  const res = await fetch(`${API_BASE_URL}/alerts/${alertId}/dismiss`, {
    method: 'POST',
  })
  return handleResponse<{ status: string; id: number }>(res)
}
