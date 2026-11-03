import Panel from '../components/Panel'
import LineChart from '../components/LineChart'
import DonutChart from '../components/DonutChart'
import BarMeter from '../components/BarMeter'
import TimeRangeSelector from '../components/TimeRangeSelector'
import type { TelemetryRecord } from '../types/telemetry'

interface MemoryPageProps {
  latest: TelemetryRecord | null
  history: TelemetryRecord[]
  timeRangeMinutes: number
  onTimeRangeChange: (mins: number) => void
}

function formatBytes(bytes: number | null | undefined): string {
  if (bytes == null || isNaN(bytes)) return '0 B'
  if (bytes >= 1024 ** 3) return `${(bytes / 1024 ** 3).toFixed(1)} GB`
  if (bytes >= 1024 ** 2) return `${(bytes / 1024 ** 2).toFixed(1)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${bytes} B`
}

export default function MemoryPage({
  latest,
  history,
  timeRangeMinutes,
  onTimeRangeChange,
}: MemoryPageProps) {
  const memPct = latest?.memory_percent ?? (latest?.memory?.percent ?? 0)
  const memSeries = history.map(h => h.memory_percent ?? h.memory?.percent ?? 0)
  const swapPct = latest?.memory?.swap?.percent ?? 0
  const processes = latest?.processes ?? []

  return (
    <div className="flex flex-col gap-4 font-mono">
      {/* Memory Historical Chart */}
      <Panel
        title={`MEMORY USAGE OVER TIME — LAST ${timeRangeMinutes} MINUTES`}
        accent="#60a5fa"
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
              data={memSeries}
              color="#60a5fa"
              label={`RAM % (${memSeries.length} samples)`}
              fillColor="#60a5fa"
              height={170}
            />
          </div>
        </div>
      </Panel>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Memory Breakdown */}
        <Panel title="RAM & SWAP ALLOCATION" accent="#60a5fa">
          <div style={{ background: '#2e2e2e', borderRadius: 2, padding: 8 }}>
            <div style={{ background: '#3a3a3a', padding: 12 }}>
              <div className="flex items-center gap-6 mb-4 justify-around">
                <DonutChart value={memPct} color="#60a5fa" label="RAM" />
                <DonutChart value={swapPct} color="#a78bfa" label="Swap" />
              </div>

              <BarMeter
                label={`RAM (${formatBytes(latest?.memory?.used)} / ${formatBytes(latest?.memory?.total)})`}
                value={memPct}
                color="#60a5fa"
              />
              <BarMeter
                label={`Swap (${formatBytes(latest?.memory?.swap?.used)} / ${formatBytes(latest?.memory?.swap?.total)})`}
                value={swapPct}
                color="#a78bfa"
              />
              {latest?.memory?.cached != null && latest.memory.cached > 0 && (
                <BarMeter
                  label={`Cache (${formatBytes(latest.memory.cached)})`}
                  value={Math.round((latest.memory.cached / (latest.memory.total || 1)) * 100)}
                  color="#38bdf8"
                />
              )}
              {latest?.memory?.buffers != null && latest.memory.buffers > 0 && (
                <BarMeter
                  label={`Buffers (${formatBytes(latest.memory.buffers)})`}
                  value={Math.round((latest.memory.buffers / (latest.memory.total || 1)) * 100)}
                  color="#818cf8"
                />
              )}

              <div className="mt-3 text-xs text-center" style={{ color: '#888' }}>
                TOTAL: {formatBytes(latest?.memory?.total)} &nbsp;|&nbsp;
                AVAILABLE: {formatBytes(latest?.memory?.available)} &nbsp;|&nbsp;
                USED: {formatBytes(latest?.memory?.used)}
              </div>
            </div>
          </div>
        </Panel>

        {/* Top Active Processes */}
        <Panel title={`TOP ACTIVE PROCESSES (${processes.length})`} accent="#a78bfa">
          <div style={{ background: '#2e2e2e', borderRadius: 2, padding: 8 }}>
            <div style={{ background: '#3a3a3a', padding: 10 }}>
              <div className="flex text-xs mb-2 px-1 pb-1 font-bold" style={{ color: '#888', borderBottom: '1px solid #444' }}>
                <span className="flex-1">PROCESS</span>
                <span className="w-16 text-right">PID</span>
                <span className="w-20 text-right">MEM</span>
                <span className="w-14 text-right">CPU</span>
              </div>
              <div className="max-h-56 overflow-y-auto">
                {processes.length > 0 ? (
                  processes.map(p => (
                    <div
                      key={p.pid}
                      className="flex items-center text-xs py-1.5 px-1 hover:bg-neutral-800 transition-colors"
                      style={{ borderBottom: '1px solid #383838' }}
                    >
                      <span className="flex-1 truncate" style={{ color: '#a78bfa' }} title={p.name}>
                        {p.name}
                      </span>
                      <span className="w-16 text-right" style={{ color: '#666' }}>
                        {p.pid}
                      </span>
                      <span className="w-20 text-right" style={{ color: '#60a5fa' }}>
                        {formatBytes(p.memory_bytes)}
                      </span>
                      <span
                        className="w-14 text-right font-bold"
                        style={{ color: p.cpu_percent > 10 ? '#f87171' : '#4ade80' }}
                      >
                        {p.cpu_percent.toFixed(1)}%
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-center py-6" style={{ color: '#777' }}>
                    No process telemetry available.
                  </div>
                )}
              </div>
            </div>
          </div>
        </Panel>
      </div>
    </div>
  )
}
