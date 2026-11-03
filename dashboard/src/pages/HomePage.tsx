import Panel from '../components/Panel'
import LineChart from '../components/LineChart'
import DonutChart from '../components/DonutChart'
import BarMeter from '../components/BarMeter'
import TimeRangeSelector from '../components/TimeRangeSelector'
import type { TelemetryRecord } from '../types/telemetry'

interface HomePageProps {
  latest: TelemetryRecord | null
  history: TelemetryRecord[]
  timeRangeMinutes: number
  onTimeRangeChange: (mins: number) => void
}

function formatUptime(seconds: number | null | undefined): string {
  if (seconds == null || isNaN(seconds)) return 'N/A'
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (d > 0) return `${d}d ${h}h`
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

function formatBytes(bytes: number | null | undefined): string {
  if (bytes == null || isNaN(bytes)) return '0 B'
  if (bytes >= 1024 ** 3) return `${(bytes / 1024 ** 3).toFixed(1)} GB`
  if (bytes >= 1024 ** 2) return `${(bytes / 1024 ** 2).toFixed(1)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${bytes} B`
}

export default function HomePage({
  latest,
  history,
  timeRangeMinutes,
  onTimeRangeChange,
}: HomePageProps) {
  const cpuPct = latest?.cpu_percent ?? (latest?.cpu?.percent ?? 0)
  const memPct = latest?.memory_percent ?? (latest?.memory?.percent ?? 0)
  const diskPct = latest?.disk_percent ?? (latest?.disk?.percent ?? 0)
  const uptimeStr = formatUptime(latest?.uptime)

  const cpuSeries = history.map(h => h.cpu_percent ?? h.cpu?.percent ?? 0)

  const stats = [
    { label: 'CPU USAGE', value: `${Math.round(cpuPct)}%`, color: '#facc15' },
    { label: 'MEMORY', value: `${Math.round(memPct)}%`, color: '#60a5fa' },
    { label: 'DISK', value: `${Math.round(diskPct)}%`, color: '#a78bfa' },
    { label: 'UPTIME', value: uptimeStr, color: '#4ade80' },
  ]

  const partitions = latest?.disk?.partitions ?? []
  const perCore = latest?.cpu?.per_core ?? []

  return (
    <div className="flex flex-col gap-4 font-mono">
      {/* System Host Information Banner */}
      <div
        className="flex flex-wrap items-center justify-between px-3 py-2 text-xs"
        style={{ background: '#323232', border: '1px solid #555', color: '#ccc' }}
      >
        <div className="flex items-center gap-3">
          <span className="font-bold text-white">HOST: {latest?.hostname ?? 'CONNECTING...'}</span>
          <span
            className="px-2 py-0.5 rounded text-xs font-bold"
            style={{
              background: latest?.os === 'Windows' ? 'rgba(96,165,250,0.2)' : 'rgba(74,222,128,0.2)',
              color: latest?.os === 'Windows' ? '#60a5fa' : '#4ade80',
              border: `1px solid ${latest?.os === 'Windows' ? '#60a5fa' : '#4ade80'}`,
            }}
          >
            {latest?.os ?? 'OS DETECTING'}
          </span>
          <span style={{ color: '#888' }}>{latest?.os_version ?? ''}</span>
          {latest?.architecture && <span style={{ color: '#666' }}>({latest.architecture})</span>}
        </div>
        <div style={{ color: '#888' }}>
          LAST UPDATE: {latest?.timestamp_utc ? new Date(latest.timestamp_utc).toLocaleTimeString() : 'N/A'}
        </div>
      </div>

      {/* Top Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {stats.map(s => (
          <div
            key={s.label}
            className="flex flex-col items-center py-3 px-2"
            style={{
              background: '#3e3e3e',
              border: '1px solid #555',
              borderTop: `3px solid ${s.color}`,
            }}
          >
            <span className="text-xs tracking-widest mb-1" style={{ color: '#888' }}>
              {s.label}
            </span>
            <span className="text-xl font-bold" style={{ color: s.color }}>
              {s.value}
            </span>
          </div>
        ))}
      </div>

      {/* Main Historical Chart */}
      <Panel
        title={`SYSTEM OVERVIEW — CPU UTILIZATION (${cpuSeries.length} SAMPLES)`}
        accent="#4ade80"
        action={
          <TimeRangeSelector
            value={timeRangeMinutes}
            onChange={onTimeRangeChange}
          />
        }
      >
        <div style={{ background: '#2e2e2e', borderRadius: 2, padding: 8 }}>
          <div style={{ background: '#3a3a3a', padding: 6 }}>
            <LineChart
              data={cpuSeries}
              color="#facc15"
              label={`CPU % (LAST ${timeRangeMinutes}M)`}
              fillColor="#facc15"
              height={170}
            />
          </div>
        </div>
      </Panel>

      {/* Bottom two panels: CPU Load & Memory Load */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* CPU Breakdown */}
        <Panel title="CPU LOAD & CORES" accent="#facc15">
          <div style={{ background: '#2e2e2e', borderRadius: 2, padding: 8 }}>
            <div style={{ background: '#3a3a3a', padding: 10, display: 'flex', alignItems: 'center', gap: 20 }}>
              <DonutChart value={cpuPct} color="#facc15" label="Usage" />
              <div className="flex-1 max-h-48 overflow-y-auto pr-1">
                {perCore.length > 0 ? (
                  perCore.map((coreVal, i) => (
                    <BarMeter
                      key={i}
                      label={`Core ${i}`}
                      value={coreVal}
                      color="#facc15"
                    />
                  ))
                ) : (
                  <div className="text-xs" style={{ color: '#888' }}>
                    Single core: {Math.round(cpuPct)}%
                  </div>
                )}
              </div>
            </div>
            {latest?.cpu?.frequency?.current && (
              <div className="mt-2 text-xs text-center" style={{ color: '#888' }}>
                FREQ: {latest.cpu.frequency.current} MHz &nbsp;|&nbsp;
                CORES: {latest.cpu.logical_cores ?? 'N/A'} logical / {latest.cpu.physical_cores ?? 'N/A'} physical
              </div>
            )}
          </div>
        </Panel>

        {/* Memory Breakdown */}
        <Panel title="MEMORY & STORAGE" accent="#60a5fa">
          <div style={{ background: '#2e2e2e', borderRadius: 2, padding: 8 }}>
            <div style={{ background: '#3a3a3a', padding: 10, display: 'flex', alignItems: 'center', gap: 20 }}>
              <DonutChart value={memPct} color="#60a5fa" label="Used" />
              <div className="flex-1">
                <BarMeter
                  label="RAM"
                  value={memPct}
                  color="#60a5fa"
                  displayValue={`${formatBytes(latest?.memory?.used)} / ${formatBytes(latest?.memory?.total)}`}
                />
                {latest?.memory?.swap && (
                  <BarMeter
                    label="Swap / Pagefile"
                    value={latest.memory.swap.percent}
                    color="#a78bfa"
                    displayValue={`${formatBytes(latest.memory.swap.used)} / ${formatBytes(latest.memory.swap.total)}`}
                  />
                )}
                {/* Cross-platform disk partitions (Windows drive letter / Linux mount point) */}
                {partitions.map(p => (
                  <BarMeter
                    key={p.mountpoint || p.device}
                    label={`${p.mountpoint} (${p.fstype || 'disk'})`}
                    value={p.percent}
                    color="#38bdf8"
                    displayValue={`${formatBytes(p.used)} / ${formatBytes(p.total)}`}
                  />
                ))}
              </div>
            </div>
            <div className="mt-2 text-xs text-center" style={{ color: '#888' }}>
              AVAILABLE RAM: {formatBytes(latest?.memory?.available)} &nbsp;|&nbsp;
              TOTAL RAM: {formatBytes(latest?.memory?.total)}
            </div>
          </div>
        </Panel>
      </div>
    </div>
  )
}
