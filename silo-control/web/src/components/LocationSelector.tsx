import type { WeatherLocation } from '../types'
import { MapPin } from 'lucide-react'

interface Props {
  locations: WeatherLocation[]
  selected: number
  onSelect: (index: number) => void
}

export function LocationSelector({ locations, selected, onSelect }: Props) {
  return (
    <div className="flex gap-2 overflow-x-auto px-4 pb-2 -mx-4 scrollbar-hide">
      {locations.map((loc, i) => (
        <button
          key={i}
          onClick={() => onSelect(i)}
          className={`flex items-center gap-1 px-3 py-2 rounded-full text-xs font-medium whitespace-nowrap transition-colors shrink-0 ${
            i === selected
              ? 'bg-accent text-white'
              : 'bg-white text-slate-600 border border-slate-200'
          }`}
        >
          <MapPin size={12} />
          {loc.name}
        </button>
      ))}
    </div>
  )
}
