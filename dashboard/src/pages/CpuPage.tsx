import Panel from '../components/Panel'
import LineChart from '../components/LineChart'
import DonutChart from '../components/DonutChart'
import TimeRangeSelector from '../components/TimeRangeSelector'
import type { TelemetryRecord } from '../types/telemetry'

interface CpuPageProps {
  latest: TelemetryRecord | null
  history: TelemetryRecord[]
  timeRangeMinutes: number
  onTimeRangeChange: (mins: number) => void
}

export default function CpuPage({
  latest,
  history,
  timeRangeMinutes,
  onTimeRangeChange,
}: CpuPageProps) {
  const cpuPct = latest?.cpu_percent ?? (latest?.cpu?.percent ?? 0)
  const cpuSeries = history.map(h => h.cpu_percent ?? h.cpu?.percent ?? 0)
  const perCore = latest?.cpu?.per_core ?? []
  const freq = latest?.cpu?.frequency
  const temp = latest?.cpu?.temperature

  return (
    <div className="flex flex-col gap-4 font-mono">
      {/* Historical CPU Utilization */}
      <Panel
        title={`CPU USAGE OVER TIME — LAST ${timeRangeMinutes} MINUTES`}
        accent="#facc15"
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
              label={`CPU % (${cpuSeries.length} recorded points)`}
              fillColor="#facc15"
              height={180}
            />
          </div>
        </div>
      </Panel>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Core Breakdown */}
        <Panel title="PER-CORE BREAKDOWN" accent="#facc15">
          <div style={{ background: '#2e2e2e', borderRadius: 2, padding: 8 }}>
            <div style={{ background: '#3a3a3a', padding: 12 }}>
              <div className="flex items-start gap-4">
                <DonutChart value={cpuPct} color="#facc15" label="Overall" />
                <div className="flex-1 max-h-64 overflow-y-auto pr-1">
                  {perCore.length > 0 ? (
                    perCore.map((val, i) => (
                      <div key={i} className="mb-2">
                        <div className="flex justify-between text-xs mb-1" style={{ color: '#aaa' }}>
                          <span>Core {i}</span>
                          {freq?.current && (
                            <span style={{ color: '#888' }}>{Math.round(freq.current)} MHz</span>
                          )}
                          <span style={{ color: '#facc15' }}>{Math.round(val)}%</span>
                        </div>
                        <div style={{ height: 4, background: '#555', borderRadius: 2 }}>
                          <div
                            style={{
                              height: '100%',
                              width: `${Math.min(val, 100)}%`,
                              background: '#facc15',
                              borderRadius: 2,
                            }}
                          />
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs py-4 text-center" style={{ color: '#888' }}>
                      Per-core telemetry not available on this platform.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </Panel>

        {/* CPU Hardware & Frequency Details */}
        <Panel title="HARDWARE & THERMAL METRICS" accent="#f87171">
          <div style={{ background: '#2e2e2e', borderRadius: 2, padding: 8 }}>
            <div style={{ background: '#3a3a3a', padding: 12 }}>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="flex flex-col items-center py-2 px-1" style={{ background: '#2a2a2a', border: '1px solid #444' }}>
                  <span className="text-xs" style={{ color: '#888' }}>LOGICAL CORES</span>
                  <span className="text-lg font-bold text-white mt-1">{latest?.cpu?.logical_cores ?? 'N/A'}</span>
                </div>
                <div className="flex flex-col items-center py-2 px-1" style={{ background: '#2a2a2a', border: '1px solid #444' }}>
                  <span className="text-xs" style={{ color: '#888' }}>PHYSICAL CORES</span>
                  <span className="text-lg font-bold text-white mt-1">{latest?.cpu?.physical_cores ?? 'N/A'}</span>
                </div>
                <div className="flex flex-col items-center py-2 px-1" style={{ background: '#2a2a2a', border: '1px solid #444' }}>
                  <span className="text-xs" style={{ color: '#888' }}>CURRENT FREQ</span>
                  <span className="text-lg font-bold text-yellow-400 mt-1">
                    {freq?.current ? `${Math.round(freq.current)} MHz` : 'N/A'}
                  </span>
                </div>
                <div className="flex flex-col items-center py-2 px-1" style={{ background: '#2a2a2a', border: '1px solid #444' }}>
                  <span className="text-xs" style={{ color: '#888' }}>TEMPERATURE</span>
                  <span className="text-lg font-bold mt-1" style={{ color: temp != null ? '#f87171' : '#777' }}>
                    {temp != null ? `${temp.toFixed(1)}°C` : 'UNSUPPORTED'}
                  </span>
                </div>
              </div>

              <div className="text-xs p-2 rounded" style={{ background: '#262626', color: '#888', border: '1px solid #333' }}>
                <span className="font-bold text-gray-300">NOTE:</span> Hardware sensors like CPU temperature
                depend on kernel thermal drivers on Linux and WMI/ACPI providers on Windows. When unsupported
                by the platform, values are marked explicitly rather than fabricated.
              </div>
            </div>
          </div>
        </Panel>
      </div>
    </div>
  )
}

