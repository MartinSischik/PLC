import { Wifi, WifiOff } from 'lucide-react'

interface Props {
  connected: boolean
  wsConnected: boolean
}

export function Header({ connected, wsConnected }: Props) {
  return (
    <header className="bg-[#1E3A5F] text-white px-4 py-3 flex items-center justify-between sticky top-0 z-40">
      <h1 className="text-lg font-bold tracking-tight">SCADA Silos</h1>
      <div className="flex items-center gap-3 text-sm">
        <span className="hidden sm:inline text-slate-300">
          {new Date().toLocaleTimeString('es-CR')}
        </span>
        <div className="flex items-center gap-1.5">
          {wsConnected ? (
            connected ? (
              <>
                <Wifi size={16} className="text-emerald-400" />
                <span className="text-emerald-400 text-xs">PLC</span>
              </>
            ) : (
              <>
                <WifiOff size={16} className="text-amber-400" />
                <span className="text-amber-400 text-xs">SIN PLC</span>
              </>
            )
          ) : (
            <>
              <WifiOff size={16} className="text-red-400" />
              <span className="text-red-400 text-xs">OFFLINE</span>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
