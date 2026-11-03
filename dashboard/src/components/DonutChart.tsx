interface DonutChartProps {
  value: number
  max?: number
  color?: string
  label?: string
  size?: number
  unit?: string
}

export default function DonutChart({
  value,
  max = 100,
  color = '#4ade80',
  label,
  size = 120,
  unit = '%',
}: DonutChartProps) {
  const r = 42
  const cx = 60
  const cy = 60
  const circumference = 2 * Math.PI * r
  const safeMax = max > 0 ? max : 100
  const pct = Math.min(Math.max(value / safeMax, 0), 1)
  const dash = pct * circumference

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} viewBox="0 0 120 120">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#444" strokeWidth="12" />
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeDasharray={`${dash} ${circumference}`}
          strokeLinecap="round"
          transform="rotate(-90 60 60)"
        />
        <text x={cx} y={cy - 4} textAnchor="middle" fontSize="16" fill="#fff" fontWeight="bold" fontFamily="monospace">
          {Math.round(value)}{unit}
        </text>
        <text x={cx} y={cy + 12} textAnchor="middle" fontSize="9" fill="#888" fontFamily="monospace">
          / {max}{unit}
        </text>
      </svg>
      {label && (
        <span style={{ fontSize: 10, color: '#aaa', textTransform: 'uppercase', letterSpacing: 1.5, fontFamily: 'monospace' }}>
          {label}
        </span>
      )}
    </div>
  )
}
