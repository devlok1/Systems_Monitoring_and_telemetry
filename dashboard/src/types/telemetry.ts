export interface CpuFrequency {
  current: number | null
  min: number | null
  max: number | null
}

export interface CpuData {
  percent: number
  per_core: number[]
  logical_cores: number | null
  physical_cores: number | null
  frequency: CpuFrequency | null
  temperature: number | null
}

export interface SwapData {
  total: number
  used: number
  free: number
  percent: number
}

export interface MemoryData {
  total: number
  used: number
  available: number
  percent: number
  swap?: SwapData | null
  cached?: number | null
  buffers?: number | null
}

export interface DiskPartition {
  device: string
  mountpoint: string
  fstype: string
  total: number
  used: number
  free: number
  percent: number
}

export interface DiskData {
  percent: number
  total: number
  used: number
  free: number
  partitions: DiskPartition[]
}

export interface NetworkInterface {
  name: string
  is_up: boolean
  mtu: number
  addresses: string[]
  bytes_sent: number
  bytes_received: number
  speed_mbps: number | null
}

export interface NetworkData {
  bytes_sent: number
  bytes_received: number
  packets_sent?: number
  packets_received?: number
  interfaces: NetworkInterface[]
}

export interface ProcessData {
  pid: number
  name: string
  cpu_percent: number
  memory_percent: number
  memory_bytes: number
  username: string | null
  status: string | null
}

export interface ThroughputInfo {
  rx_bytes_sec: number
  tx_bytes_sec: number
  rx_kb_sec: number
  tx_kb_sec: number
  rx_mb_sec: number
  tx_mb_sec: number
}

export interface TelemetryRecord {
  id: number
  host_id?: string
  hostname: string
  os: string
  os_version: string | null
  architecture: string | null
  agent_version: string | null
  timestamp: number
  timestamp_utc: string | null
  uptime: number | null
  cpu_percent: number | null
  memory_percent: number | null
  disk_percent: number | null
  network_bytes_sent: number | null
  network_bytes_recv: number | null
  cpu: CpuData
  memory: MemoryData
  disk: DiskData
  network: NetworkData
  processes: ProcessData[]
  throughput?: ThroughputInfo
}

export interface AggregatedMetric {
  avg: number
  min: number
  max: number
}

export interface StatsResponse {
  hostname: string | null
  sample_count: number
  period_start: number | null
  period_end: number | null
  period_duration_seconds: number
  cpu: AggregatedMetric
  memory: AggregatedMetric
  disk: AggregatedMetric
  network: {
    total_bytes_sent: number
    total_bytes_received: number
    avg_upload_kb_sec?: number
    avg_download_kb_sec?: number
  }
}

export interface HistoryResponse {
  count: number
  limit: number
  offset: number
  start: number | null
  end: number | null
  data: TelemetryRecord[]
}

export interface HealthResponse {
  status: string
  timestamp: string
  database: string
  total_records: number
  version: string
}

export interface LogEntry {
  id: number
  timestamp: number
  timestamp_utc: string | null
  hostname: string | null
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG'
  source: string | null
  message: string
}

export interface AlertEntry {
  id: number
  timestamp: number
  timestamp_utc: string | null
  hostname: string | null
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  source: string | null
  detail: string | null
  dismissed: number
}

export type ConnectionStatus = 'CONNECTED' | 'STALE' | 'DISCONNECTED' | 'INITIALIZING'

