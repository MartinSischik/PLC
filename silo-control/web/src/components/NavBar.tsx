import { NavLink } from 'react-router-dom'
import { Activity, CloudSun } from 'lucide-react'

const tabs = [
  { to: '/scada', label: 'SCADA', icon: Activity },
  { to: '/weather', label: 'Clima', icon: CloudSun },
]

export function NavBar() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 flex z-50 pb-safe">
      {tabs.map(({ to, label, icon: Icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            `flex-1 flex flex-col items-center py-2 gap-0.5 text-xs font-medium transition-colors ${
              isActive ? 'text-accent' : 'text-slate-400'
            }`
          }
        >
          <Icon size={22} />
          {label}
        </NavLink>
      ))}
    </nav>
  )
}
