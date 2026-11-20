interface TimeRangeSelectorProps {
  value: number
  onChange: (minutes: number) => void
}

const RANGES = [
  { label: '5M', minutes: 5 },
  { label: '15M', minutes: 15 },
  { label: '1H', minutes: 60 },
  { label: '6H', minutes: 360 },
  { label: '24H', minutes: 1440 },
]

export default function TimeRangeSelector({ value, onChange }: TimeRangeSelectorProps) {
  return (
    <div className="flex items-center gap-1">
      {RANGES.map(r => (
        <button
          key={r.label}
          onClick={() => onChange(r.minutes)}
          className="px-2 py-0.5 text-xs font-mono tracking-wider transition-colors"
          style={{
            background: value === r.minutes ? '#555' : 'transparent',
            color: value === r.minutes ? '#4ade80' : '#888',
            border: `1px solid ${value === r.minutes ? '#4ade80' : '#444'}`,
            borderRadius: 2,
            cursor: 'pointer',
          }}
        >
          {r.label}
        </button>
      ))}
    </div>
  )
}

