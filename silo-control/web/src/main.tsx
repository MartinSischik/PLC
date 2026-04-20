import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { App } from './App'
import { ScadaPage } from './pages/ScadaPage'
import { WeatherPage } from './pages/WeatherPage'
import { WorkOrdersPage } from './pages/WorkOrdersPage'
import { SchedulerPage } from './pages/SchedulerPage'
import './styles/globals.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<App />}>
          <Route path="/scada" element={<ScadaPage />} />
          <Route path="/ordenes" element={<WorkOrdersPage />} />
          <Route path="/scheduler" element={<SchedulerPage />} />
          <Route path="/weather" element={<WeatherPage />} />
          <Route path="*" element={<Navigate to="/scada" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
