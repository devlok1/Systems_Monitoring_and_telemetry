interface LineChartProps {
  data: number[]
  color?: string
  label?: string
  unit?: string
  height?: number
  fillColor?: string
  maxVal?: number
}

export default function LineChart({
  data,
  color = '#4ade80',
  label,
  unit = '%',
  height = 160,
  fillColor,
  maxVal,
}: LineChartProps) {
  const w = 600
  const h = height
  const pad = { top: 12, right: 12, bottom: 24, left: 45 }
  const innerW = w - pad.left - pad.right
  const innerH = h - pad.top - pad.bottom

  // If data is empty, supply a baseline 0
  const chartData = data.length === 0 ? [0] : data
  const calculatedMax = Math.max(...chartData, maxVal ?? 100)
  const max = calculatedMax <= 0 ? 100 : calculatedMax
  const min = 0

  const count = chartData.length
  const pts = chartData.map((v, i) => {
    const x = count <= 1 ? pad.left + innerW / 2 : pad.left + (i / (count - 1)) * innerW
    const clampedV = Math.max(min, Math.min(max, v))
    const y = pad.top + (1 - (clampedV - min) / (max - min)) * innerH
    return { x, y, v }
  })

  const polyline = pts.map(p => `${p.x},${p.y}`).join(' ')
  const fill = count > 1 ? [
    `M${pts[0].x},${pad.top + innerH}`,
    ...pts.map(p => `L${p.x},${p.y}`),
    `L${pts[pts.length - 1].x},${pad.top + innerH}`,
    'Z',
  ].join(' ') : ''

  const gridLines = [0, 25, 50, 75, 100]
  const lastVal = chartData[chartData.length - 1]

  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: '100%', height }} preserveAspectRatio="none">
      {/* Grid */}
      {gridLines.map(g => {
        const y = pad.top + (1 - g / 100) * innerH
        const labelVal = Math.round((g / 100) * max)
        return (
          <g key={g}>
            <line x1={pad.left} y1={y} x2={w - pad.right} y2={y} stroke="#444" strokeWidth="1" strokeDasharray="3 3" />
            <text x={pad.left - 6} y={y + 3} textAnchor="end" fontSize="9" fill="#777" fontFamily="monospace">
              {labelVal}
            </text>
          </g>
        )
      })}

      {/* Fill area */}
      {fill && <path d={fill} fill={fillColor ?? color} fillOpacity="0.15" />}

      {/* Line */}
      {count > 1 ? (
        <polyline points={polyline} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" />
      ) : (
        <line x1={pad.left} y1={pts[0].y} x2={w - pad.right} y2={pts[0].y} stroke={color} strokeWidth="2" strokeDasharray="4 4" />
      )}

      {/* Last value dot */}
      {pts.length > 0 && (
        <circle cx={pts[pts.length - 1].x} cy={pts[pts.length - 1].y} r="4" fill={color} />
      )}

      {/* Label */}
      {label && (
        <text x={pad.left} y={h - 6} fontSize="10" fill="#888" fontFamily="monospace">
          {label}
        </text>
      )}

      {/* Current value */}
      <text x={w - pad.right} y={pad.top + 10} textAnchor="end" fontSize="11" fill={color} fontWeight="bold" fontFamily="monospace">
        {data.length === 0 ? 'NO DATA' : `${lastVal}${unit}`}
      </text>
    </svg>
  )
}
