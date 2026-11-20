import type {
  TelemetryRecord,
  HistoryResponse,
  StatsResponse,
  HealthResponse,
  LogEntry,
  AlertEntry,
} from '../types/telemetry'

// In development mode (Vite dev server), default to http://127.0.0.1:8000.
// In production builds (Nginx reverse proxy), default to empty string so requests are relative to origin.
const DEFAULT_URL = import.meta.env.DEV ? 'http://127.0.0.1:8000' : ''
const API_BASE_URL = (
  import.meta.env.VITE_API_URL !== undefined ? import.meta.env.VITE_API_URL : DEFAULT_URL
).replace(/\/$/, '')

function resolveUrl(path: string, params?: Record<string, string | number | undefined>): string {
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  let fullUrl: URL

  if (API_BASE_URL.startsWith('http://') || API_BASE_URL.startsWith('https://')) {
    fullUrl = new URL(`${API_BASE_URL}${cleanPath}`)
  } else {
    const base = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000'
    const prefix = API_BASE_URL ? (API_BASE_URL.startsWith('/') ? API_BASE_URL : `/${API_BASE_URL}`) : ''
    fullUrl = new URL(`${prefix}${cleanPath}`, base)
  }

  if (params) {
    for (const [key, val] of Object.entries(params)) {
      if (val !== undefined && val !== null && val !== '') {
        fullUrl.searchParams.set(key, String(val))
      }
    }
  }

  // If base is relative, return pathname + search for clean relative requests
  if (!API_BASE_URL.startsWith('http://') && !API_BASE_URL.startsWith('https://')) {
    return `${fullUrl.pathname}${fullUrl.search}`
  }
  return fullUrl.toString()
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const errorText = await res.text().catch(() => 'Network request failed')
    throw new Error(`API Error ${res.status}: ${errorText}`)
  }
  return res.json() as Promise<T>
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(resolveUrl('/health'))
  return handleResponse<HealthResponse>(res)
}

export async function fetchLatestTelemetry(hostname?: string): Promise<TelemetryRecord> {
  const url = resolveUrl('/telemetry/latest', { hostname })
  const res = await fetch(url)
  return handleResponse<TelemetryRecord>(res)
}

export async function fetchTelemetryHistory(options: {
  start?: number
  end?: number
  limit?: number
  offset?: number
  hostname?: string
} = {}): Promise<HistoryResponse> {
  const url = resolveUrl('/telemetry/history', {
    start: options.start,
    end: options.end,
    limit: options.limit,
    offset: options.offset,
    hostname: options.hostname,
  })
  const res = await fetch(url)
  return handleResponse<HistoryResponse>(res)
}

export async function fetchStats(options: {
  start?: number
  end?: number
  hostname?: string
} = {}): Promise<StatsResponse> {
  const url = resolveUrl('/telemetry/stats', {
    start: options.start,
    end: options.end,
    hostname: options.hostname,
  })
  const res = await fetch(url)
  return handleResponse<StatsResponse>(res)
}

export async function fetchLogs(options: {
  level?: string
  search?: string
  limit?: number
} = {}): Promise<LogEntry[]> {
  const url = resolveUrl('/logs', {
    level: options.level && options.level !== 'ALL' ? options.level : undefined,
    search: options.search,
    limit: options.limit,
  })
  const res = await fetch(url)
  return handleResponse<LogEntry[]>(res)
}

export async function fetchAlerts(activeOnly = true): Promise<AlertEntry[]> {
  const url = resolveUrl('/alerts', {
    active_only: activeOnly ? 'true' : 'false',
  })
  const res = await fetch(url)
  return handleResponse<AlertEntry[]>(res)
}

export async function dismissAlert(alertId: number): Promise<{ status: string; id: number }> {
  const url = resolveUrl(`/alerts/${alertId}/dismiss`)
  const res = await fetch(url, {
    method: 'POST',
  })
  return handleResponse<{ status: string; id: number }>(res)
}
