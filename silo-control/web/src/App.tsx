import { Outlet } from 'react-router-dom'
import { ScadaContext, useScadaConnection } from './hooks/useScada'
import { Header } from './components/Header'
import { NavBar } from './components/NavBar'

export function App() {
  const scada = useScadaConnection()

  return (
    <ScadaContext.Provider value={scada}>
      <div className="min-h-screen bg-slate-100 flex flex-col">
        <Header connected={scada.connected} wsConnected={scada.wsConnected} />
        <main className="flex-1">
          <Outlet />
        </main>
        <NavBar />
      </div>
    </ScadaContext.Provider>
  )
}
