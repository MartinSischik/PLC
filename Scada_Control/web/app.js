const $ = (id) => document.getElementById(id)

const els = {
  plcStatus: $("plcStatus"),
  wsStatus: $("wsStatus"),
  summarySilos: $("summarySilos"),
  summarySensors: $("summarySensors"),
  summaryAlerts: $("summaryAlerts"),
  summaryTime: $("summaryTime"),
  alertCount: $("alertCount"),
  alertsList: $("alertsList"),
  silosGrid: $("silosGrid"),
}

let ws = null
let pingTimer = null
let reconnectTimer = null

let config = { silos: [] }

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;")
}

function formatNum(value, suffix = "") {
  if (value === null || value === undefined || Number.isNaN(value)) return "---"
  return `${Number(value).toFixed(1)}${suffix}`
}

function setPill(el, text, connected) {
  el.textContent = text
  el.classList.remove("connected", "disconnected")
  el.classList.add(connected ? "connected" : "disconnected")
}

async function loadConfig() {
  const response = await fetch("/api/config")
  config = await response.json()
}

function getWsUrl() {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws"
  return `${protocol}://${window.location.host}/ws/monitor`
}

function connectWs() {
  ws = new WebSocket(getWsUrl())

  ws.onopen = () => {
    setPill(els.wsStatus, "WS ONLINE", true)
    if (pingTimer) clearInterval(pingTimer)
    pingTimer = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) ws.send("ping")
    }, 15000)
  }

  ws.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data)
      renderSnapshot(payload)
    } catch (error) {
      console.error("Error parsing ws payload", error)
    }
  }

  ws.onclose = () => {
    setPill(els.wsStatus, "WS OFFLINE", false)
    if (pingTimer) {
      clearInterval(pingTimer)
      pingTimer = null
    }
    if (!reconnectTimer) {
      reconnectTimer = setTimeout(() => {
        reconnectTimer = null
        connectWs()
      }, 2000)
    }
  }

  ws.onerror = () => ws.close()
}

function renderAlerts(alerts) {
  els.alertCount.textContent = String(alerts.length)
  if (!alerts.length) {
    els.alertsList.innerHTML = '<li class="muted">Sin alertas por ahora.</li>'
    return
  }
  els.alertsList.innerHTML = alerts
    .slice(0, 40)
    .map((alert) => `<li>${escapeHtml(alert)}</li>`)
    .join("")
}

function classifySensor(reading, thresholds) {
  if (!reading.active || !thresholds) return ""

  const hasTemp = typeof reading.temperature === "number" && reading.temperature > 0
  const hasHum = typeof reading.humidity === "number" && reading.humidity > 0

  if (
    (hasTemp && (reading.temperature >= thresholds.temp_max || reading.temperature <= thresholds.temp_min)) ||
    (hasHum && reading.humidity >= thresholds.humid_max)
  ) {
    return "danger"
  }

  if (
    (hasTemp &&
      (reading.temperature >= thresholds.temp_max - 5 ||
        reading.temperature <= thresholds.temp_min + 5)) ||
    (hasHum && reading.humidity >= thresholds.humid_max - 10)
  ) {
    return "warn"
  }

  return ""
}

function renderSiloCard(silo, thresholds) {
  const sensorsHtml = silo.sensors
    .map((sensor) => {
      const css = classifySensor(sensor, thresholds)
      const mainValue = sensor.label.startsWith("T-")
        ? formatNum(sensor.temperature, " C")
        : formatNum(sensor.humidity, " %")
      return `
        <div class="sensor-tile">
          <div class="sensor-name">${escapeHtml(sensor.label)}</div>
          <div class="sensor-value ${css}">${mainValue}</div>
        </div>
      `
    })
    .join("")

  const levelHighClass = silo.levels.high ? "state-pill high" : "state-pill"
  const levelLowClass = silo.levels.low ? "state-pill high" : "state-pill"

  const gasesHtml = silo.gases
    .map((gas) => {
      const gasClass = gas.alarm_trip ? "state-pill gas-trip" : gas.alarm_warn ? "state-pill gas-warn" : "state-pill good"
      return `<span class="${gasClass}">${escapeHtml(gas.label)} ${formatNum(gas.ppm, " ppm")}</span>`
    })
    .join("")

  const motorsHtml = silo.motors
    .map((motor) => {
      let cls = "state-pill"
      if (motor.fault) cls = "state-pill fault"
      else if (motor.is_running) cls = "state-pill running"
      else if (motor.enabled) cls = "state-pill enabled"
      return `<span class="${cls}">${escapeHtml(motor.label)}${motor.is_running ? " ON" : " OFF"}</span>`
    })
    .join("")

  const gatesHtml = silo.gates
    .map((gate) => {
      let cls = "state-pill"
      if (gate.fault) cls = "state-pill fault"
      else if (gate.is_open) cls = "state-pill open"
      else if (gate.is_closed) cls = "state-pill closed"
      return `<span class="${cls}">${escapeHtml(gate.label)}</span>`
    })
    .join("")

  return `
    <article class="silo-card">
      <div class="silo-head">
        <h3>${escapeHtml(silo.silo_name)}</h3>
        <span class="state-pill">Indice ${silo.silo_index + 1}</span>
      </div>
      <div class="silo-body">
        <section>
          <p class="section-title">Sensores Analogicos</p>
          <div class="sensor-grid">${sensorsHtml}</div>
        </section>

        <section>
          <p class="section-title">Nivel y Gas</p>
          <div class="level-gas-row">
            <div class="pill-row">
              <span class="${levelHighClass}">HL ${silo.levels.high === null ? "---" : silo.levels.high ? "ACTIVO" : "INACTIVO"}</span>
              <span class="${levelLowClass}">LL ${silo.levels.low === null ? "---" : silo.levels.low ? "ACTIVO" : "INACTIVO"}</span>
            </div>
            <div class="pill-row">${gasesHtml || '<span class="state-pill">Sin sensor gas</span>'}</div>
          </div>
        </section>

        <section>
          <p class="section-title">Motores (solo estado)</p>
          <div class="pill-row">${motorsHtml || '<span class="state-pill">Sin motores</span>'}</div>
        </section>

        <section>
          <p class="section-title">Compuertas (solo estado)</p>
          <div class="pill-row">${gatesHtml || '<span class="state-pill">Sin compuertas</span>'}</div>
        </section>
      </div>
    </article>
  `
}

function renderSnapshot(snapshot) {
  setPill(els.plcStatus, snapshot.connected ? "PLC ONLINE" : "PLC OFFLINE", snapshot.connected)

  const summary = snapshot.summary || { silo_count: 0, sensor_count: 0, active_sensor_count: 0, alarm_count: 0 }
  els.summarySilos.textContent = String(summary.silo_count)
  els.summarySensors.textContent = `${summary.active_sensor_count} / ${summary.sensor_count}`
  els.summaryAlerts.textContent = String(summary.alarm_count)
  els.summaryTime.textContent = new Date(snapshot.timestamp).toLocaleString("es-CR")

  renderAlerts(snapshot.alerts || [])

  const silos = Array.isArray(snapshot.silos) ? snapshot.silos : []
  els.silosGrid.innerHTML = silos.map((silo) => renderSiloCard(silo, snapshot.thresholds)).join("")
}

async function preloadSnapshot() {
  try {
    const response = await fetch("/api/snapshot")
    const snapshot = await response.json()
    renderSnapshot(snapshot)
  } catch (error) {
    console.error("Could not preload snapshot", error)
  }
}

async function boot() {
  try {
    await loadConfig()
  } catch (error) {
    console.error("Could not load config", error)
  }
  await preloadSnapshot()
  connectWs()
}

boot()
