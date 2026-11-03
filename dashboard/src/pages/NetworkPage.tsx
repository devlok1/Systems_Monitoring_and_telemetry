import Panel from '../components/Panel'
import LineChart from '../components/LineChart'
import TimeRangeSelector from '../components/TimeRangeSelector'
import type { TelemetryRecord } from '../types/telemetry'

interface NetworkPageProps {
  latest: TelemetryRecord | null
  history: TelemetryRecord[]
  timeRangeMinutes: number
  onTimeRangeChange: (mins: number) => void
}

function formatBytes(bytes: number | null | undefined): string {
  if (bytes == null || isNaN(bytes)) return '0 B'
  if (bytes >= 1024 ** 3) return `${(bytes / 1024 ** 3).toFixed(2)} GB`
  if (bytes >= 1024 ** 2) return `${(bytes / 1024 ** 2).toFixed(2)} MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${bytes} B`
}

export default function NetworkPage({
  latest,
  history,
  timeRangeMinutes,
  onTimeRangeChange,
}: NetworkPageProps) {
  const rxSeries = history.map(h => h.throughput?.rx_mb_sec ?? 0)
  const txSeries = history.map(h => h.throughput?.tx_mb_sec ?? 0)

  const currentThroughput = latest?.throughput
  const rxSpeedStr = currentThroughput ? `${currentThroughput.rx_kb_sec.toFixed(1)} KB/s` : '0.0 KB/s'
  const txSpeedStr = currentThroughput ? `${currentThroughput.tx_kb_sec.toFixed(1)} KB/s` : '0.0 KB/s'

  const interfaces = latest?.network?.interfaces ?? []

  const totalBytesSent = latest?.network_bytes_sent ?? latest?.network?.bytes_sent ?? 0
  const totalBytesRecv = latest?.network_bytes_recv ?? latest?.network?.bytes_received ?? 0

  return (
    <div className="flex flex-col gap-4 font-mono">
      {/* Real-time Throughput Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="flex flex-col items-center py-3" style={{ background: '#3e3e3e', border: '1px solid #555', borderTop: '3px solid #a78bfa' }}>
          <span className="text-xs text-gray-400 mb-1">DOWNLOAD (RX)</span>
          <span className="text-lg font-bold" style={{ color: '#a78bfa' }}>{rxSpeedStr}</span>
        </div>
        <div className="flex flex-col items-center py-3" style={{ background: '#3e3e3e', border: '1px solid #555', borderTop: '3px solid #f97316' }}>
          <span className="text-xs text-gray-400 mb-1">UPLOAD (TX)</span>
          <span className="text-lg font-bold" style={{ color: '#f97316' }}>{txSpeedStr}</span>
        </div>
        <div className="flex flex-col items-center py-3" style={{ background: '#3e3e3e', border: '1px solid #555', borderTop: '3px solid #4ade80' }}>
          <span className="text-xs text-gray-400 mb-1">TOTAL RECEIVED</span>
          <span className="text-lg font-bold text-white">{formatBytes(totalBytesRecv)}</span>
        </div>
        <div className="flex flex-col items-center py-3" style={{ background: '#3e3e3e', border: '1px solid #555', borderTop: '3px solid #38bdf8' }}>
          <span className="text-xs text-gray-400 mb-1">TOTAL TRANSMITTED</span>
          <span className="text-lg font-bold text-white">{formatBytes(totalBytesSent)}</span>
        </div>
      </div>

      {/* Historical Throughput Chart */}
      <Panel
        title={`NETWORK THROUGHPUT — LAST ${timeRangeMinutes} MINUTES`}
        accent="#a78bfa"
        action={
          <TimeRangeSelector
            value={timeRangeMinutes}
            onChange={onTimeRangeChange}
          />
        }
      >
        <div style={{ background: '#2e2e2e', borderRadius: 2, padding: 8 }}>
          <div style={{ background: '#3a3a3a', padding: 6 }}>
            <div className="flex gap-4 text-xs mb-2 px-1 font-bold">
              <span style={{ color: '#a78bfa' }}>▲ RX (Download Rate MB/s)</span>
              <span style={{ color: '#f97316' }}>▼ TX (Upload Rate MB/s)</span>
            </div>
            <LineChart
              data={rxSeries}
              color="#a78bfa"
              label="RX (MB/s)"
              unit=" MB/s"
              height={140}
              fillColor="#a78bfa"
            />
            <div className="mt-2">
              <LineChart
                data={txSeries}
                color="#f97316"
                label="TX (MB/s)"
                unit=" MB/s"
                height={120}
                fillColor="#f97316"
              />
            </div>
          </div>
        </div>
      </Panel>

      {/* Network Interfaces */}
      <Panel title={`NETWORK INTERFACES (${interfaces.length})`} accent="#a78bfa">
        <div style={{ background: '#2e2e2e', borderRadius: 2, padding: 8 }}>
          <div style={{ background: '#3a3a3a', padding: 12 }}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {interfaces.length > 0 ? (
                interfaces.map(iface => (
                  <div
                    key={iface.name}
                    className="p-3 rounded"
                    style={{ background: '#2a2a2a', border: '1px solid #444' }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-bold truncate" style={{ color: '#a78bfa' }} title={iface.name}>
                        {iface.name}
                      </span>
                      <span
                        className="text-xs px-2 py-0.5 rounded font-bold"
                        style={{
                          background: iface.is_up ? 'rgba(74,222,128,0.2)' : 'rgba(248,113,113,0.2)',
                          color: iface.is_up ? '#4ade80' : '#f87171',
                          border: `1px solid ${iface.is_up ? '#4ade80' : '#f87171'}`,
                        }}
                      >
                        {iface.is_up ? 'UP' : 'DOWN'}
                      </span>
                    </div>

                    <div className="text-xs mb-2" style={{ color: '#aaa' }}>
                      IP: {iface.addresses.length > 0 ? iface.addresses.join(', ') : 'None assigned'}
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs" style={{ color: '#888' }}>
                      <div>MTU: <span className="text-gray-300">{iface.mtu}</span></div>
                      <div>SPEED: <span className="text-gray-300">{iface.speed_mbps ? `${iface.speed_mbps} Mbps` : 'N/A'}</span></div>
                      <div>SENT: <span style={{ color: '#f97316' }}>{formatBytes(iface.bytes_sent)}</span></div>
                      <div>RECV: <span style={{ color: '#4ade80' }}>{formatBytes(iface.bytes_received)}</span></div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-xs text-center py-6 text-gray-400">
                  No network interfaces detected.
                </div>
              )}
            </div>
          </div>
        </div>
      </Panel>
    </div>
  )
}
