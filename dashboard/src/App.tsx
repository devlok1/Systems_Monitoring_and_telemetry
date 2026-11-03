import { useState, type ReactNode } from 'react'
import HomePage from './pages/HomePage'
import CpuPage from './pages/CpuPage'
import MemoryPage from './pages/MemoryPage'
import NetworkPage from './pages/NetworkPage'
import LogsPage from './pages/LogsPage'
import AlertsPage from './pages/AlertsPage'
import { useTelemetry } from './hooks/useTelemetry'

type Page = 'HOME' | 'CPU' | 'MEMORY' | 'NETWORK' | 'LOGS' | 'ALERTS'

const NAV_ITEMS: Page[] = ['HOME', 'CPU', 'MEMORY', 'NETWORK', 'LOGS', 'ALERTS']

const PAGE_LABEL: Record<Page, string> = {
  HOME: 'OVERVIEW',
  CPU: 'MY_CPU',
  MEMORY: 'MEMORY',
  NETWORK: 'NETWORK',
  LOGS: 'LOGS',
  ALERTS: 'ALERTS',
}

const PAGE_THEME_COLOR: Record<Page, string> = {
  HOME: '#4ade80',
  CPU: '#facc15',
  MEMORY: '#60a5fa',
  NETWORK: '#a78bfa',
  LOGS: '#94a3b8',
  ALERTS: '#f87171',
}

export default function App() {
  const [page, setPage] = useState<Page>('HOME')
  const [showHelp, setShowHelp] = useState(false)

  const {
    latest,
    history,
    status,
    timeRangeMinutes,
    setTimeRangeMinutes,
    refresh,
  } = useTelemetry(3000)

  const statusColor =
    status === 'CONNECTED'
      ? '#4ade80'
      : status === 'STALE'
      ? '#facc15'
      : status === 'DISCONNECTED'
      ? '#f87171'
      : '#94a3b8'

  const pages: Record<Page, ReactNode> = {
    HOME: (
      <HomePage
        latest={latest}
        history={history}
        timeRangeMinutes={timeRangeMinutes}
        onTimeRangeChange={setTimeRangeMinutes}
      />
    ),
    CPU: (
      <CpuPage
        latest={latest}
        history={history}
        timeRangeMinutes={timeRangeMinutes}
        onTimeRangeChange={setTimeRangeMinutes}
      />
    ),
    MEMORY: (
      <MemoryPage
        latest={latest}
        history={history}
        timeRangeMinutes={timeRangeMinutes}
        onTimeRangeChange={setTimeRangeMinutes}
      />
    ),
    NETWORK: (
      <NetworkPage
        latest={latest}
        history={history}
        timeRangeMinutes={timeRangeMinutes}
        onTimeRangeChange={setTimeRangeMinutes}
      />
    ),
    LOGS: <LogsPage />,
    ALERTS: <AlertsPage />,
  }

  return (
    <div className="min-h-screen flex flex-col font-mono" style={{ background: '#2a2a2a' }}>
      {/* Outer shell */}
      <div
        className="flex-1 flex flex-col m-2 md:m-3"
        style={{ background: '#383838', border: '1px solid #555', borderRadius: 4 }}
      >
        {/* Header bar */}
        <div
          className="flex items-center px-4 py-3"
          style={{ background: '#404040', borderBottom: '1px solid #555' }}
        >
          <div
            className="flex-1 text-center py-2 px-4 text-xs md:text-sm tracking-widest font-bold truncate"
            style={{
              border: `2px solid ${statusColor}`,
              color: '#fff',
              background: '#2a2a2a',
              letterSpacing: '0.15em',
            }}
          >
            SYSWATCH&nbsp;&nbsp;|&nbsp;&nbsp;{PAGE_LABEL[page]}&nbsp;&nbsp;|&nbsp;&nbsp;
            <span style={{ color: statusColor }}>STATUS: {status}</span>
            {latest?.hostname && (
              <span className="hidden md:inline" style={{ color: '#aaa' }}>
                &nbsp;&nbsp;[{latest.hostname} / {latest.os}]
              </span>
            )}
          </div>
          <button
            onClick={() => setShowHelp(prev => !prev)}
            className="ml-3 w-8 h-8 flex items-center justify-center text-sm font-bold rounded cursor-pointer"
            style={{ background: '#facc15', color: '#1a1a1a' }}
            title="Help / System Info"
          >
            ?
          </button>
        </div>

        {/* Stale / Disconnection notification banner */}
        {status === 'DISCONNECTED' && (
          <div
            className="px-4 py-2 text-xs text-center font-bold flex items-center justify-center gap-2"
            style={{ background: '#7f1d1d', color: '#fca5a5', borderBottom: '1px solid #b91c1c' }}
          >
            <span>⚠ BACKEND UNREACHABLE — Please verify FastAPI server is running on http://127.0.0.1:8000</span>
            <button
              onClick={refresh}
              className="px-2 py-0.5 rounded text-xs bg-red-950 border border-red-700 cursor-pointer"
            >
              RETRY NOW
            </button>
          </div>
        )}
        {status === 'STALE' && (
          <div
            className="px-4 py-1.5 text-xs text-center font-bold"
            style={{ background: '#713f12', color: '#fef08a', borderBottom: '1px solid #a16207' }}
          >
            ⚠ TELEMETRY STALE — The agent has not sent a telemetry pulse within the last 20 seconds.
          </div>
        )}

        {/* Main Body Layout */}
        <div className="flex flex-1 overflow-hidden flex-col md:flex-row">
          {/* Sidebar */}
          <div
            className="flex md:flex-col py-3 md:py-4 px-2 md:px-0 overflow-x-auto md:overflow-x-visible shrink-0"
            style={{ width: 'auto', minWidth: 170, background: '#3a3a3a', borderRight: '1px solid #555' }}
          >
            <div className="hidden md:flex justify-center mb-4">
              <span style={{ fontSize: 36 }}>🎃</span>
            </div>
            <nav className="flex md:flex-col gap-1 w-full">
              {NAV_ITEMS.map(item => (
                <button
                  key={item}
                  onClick={() => setPage(item)}
                  className="text-left px-3 py-2 text-xs md:text-sm tracking-widest transition-colors cursor-pointer whitespace-nowrap"
                  style={{
                    color: page === item ? PAGE_THEME_COLOR[item] : '#ccc',
                    background: page === item ? 'rgba(255,255,255,0.07)' : 'transparent',
                    borderLeft: page === item ? `3px solid ${PAGE_THEME_COLOR[item]}` : '3px solid transparent',
                    fontWeight: page === item ? 700 : 400,
                  }}
                >
                  {item}
                </button>
              ))}
            </nav>
          </div>

          {/* Main content viewport */}
          <div className="flex-1 p-3 md:p-4 overflow-auto" style={{ background: '#383838' }}>
            {pages[page]}
          </div>
        </div>
      </div>

      {/* Help Modal */}
      {showHelp && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,0.75)' }}
          onClick={() => setShowHelp(false)}
        >
          <div
            className="p-6 max-w-lg w-full font-mono text-xs rounded"
            style={{ background: '#333', border: '1px solid #666', color: '#ccc' }}
            onClick={e => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4 pb-2 border-b border-gray-600">
              <span className="font-bold text-sm text-yellow-400">SYSWATCH TELEMETRY SYSTEM v1.0</span>
              <button
                onClick={() => setShowHelp(false)}
                className="text-gray-400 hover:text-white cursor-pointer text-base font-bold"
              >
                ✕
              </button>
            </div>
            <p className="mb-3">
              SYSWATCH is an industrial cross-platform system monitoring suite supporting Windows 10/11, Windows Server,
              and Linux distributions (Debian, Ubuntu, Kali).
            </p>
            <div className="mb-3">
              <span className="font-bold text-white block mb-1">Architecture:</span>
              <ul className="list-disc list-inside space-y-1 text-gray-400">
                <li>Shared Python Telemetry Agent (psutil + platform engine)</li>
                <li>FastAPI High-Throughput Ingestion Backend</li>
                <li>SQLite Persistent Telemetry Store (WAL Mode)</li>
                <li>React + TypeScript Dark Industrial Dashboard</li>
              </ul>
            </div>
            <div className="mb-4">
              <span className="font-bold text-white block mb-1">Status Badges:</span>
              <ul className="list-disc list-inside space-y-1 text-gray-400">
                <li><span className="text-green-400 font-bold">CONNECTED:</span> Receiving live telemetry (every 3s).</li>
                <li><span className="text-yellow-400 font-bold">STALE:</span> Server connected, but agent pulse is idle.</li>
                <li><span className="text-red-400 font-bold">DISCONNECTED:</span> Backend server unreachable.</li>
              </ul>
            </div>
            <button
              onClick={() => setShowHelp(false)}
              className="w-full py-2 bg-neutral-700 hover:bg-neutral-600 text-white font-bold cursor-pointer rounded"
            >
              CLOSE
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
