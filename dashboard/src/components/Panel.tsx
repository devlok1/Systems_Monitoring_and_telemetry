import type { ReactNode } from 'react'

interface PanelProps {
  title: string
  accent?: string
  children: ReactNode
  className?: string
  action?: ReactNode
}

export default function Panel({
  title,
  accent = '#888',
  children,
  className = '',
  action,
}: PanelProps) {
  return (
    <div className={`flex flex-col ${className}`} style={{ background: '#383838', border: '1px solid #555', borderRadius: 3 }}>
      <div
        className="flex items-center justify-between px-3 py-2 text-xs tracking-widest font-bold"
        style={{ color: '#ccc', borderBottom: '1px solid #555', background: '#323232' }}
      >
        <div className="flex items-center gap-2">
          <span style={{ fontSize: 16 }}>🎃</span>
          <span style={{ color: accent }}>{title}</span>
        </div>
        {action && <div>{action}</div>}
      </div>
      <div className="flex-1 p-3">{children}</div>
    </div>
  )
}
