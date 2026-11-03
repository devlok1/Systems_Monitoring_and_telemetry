interface BarMeterProps {
  label: string
  value: number
  max?: number
  color?: string
  unit?: string
  displayValue?: string
}

export default function BarMeter({
  label,
  value,
  max = 100,
  color = '#4ade80',
  unit = '%',
  displayValue,
}: BarMeterProps) {
  const safeMax = max > 0 ? max : 100
  const pct = Math.min(Math.max((value / safeMax) * 100, 0), 100)

  return (
    <div className="flex flex-col gap-1 mb-2 font-mono">
      <div className="flex justify-between text-xs" style={{ color: '#aaa' }}>
        <span className="truncate pr-2">{label}</span>
        <span style={{ color }}>
          {displayValue ?? (max === 100 ? `${Math.round(value)}${unit}` : `${value}/${max}`)}
        </span>
      </div>
      <div style={{ height: 6, background: '#444', borderRadius: 3 }}>
        <div
          style={{
            height: '100%',
            width: `${pct}%`,
            background: color,
            borderRadius: 3,
            transition: 'width 0.3s ease-out',
          }}
        />
      </div>
    </div>
  )
}
