# gui/app.py
# Interfaz gráfica principal del sistema SCADA para control de silos.
#
# Construida con tkinter (incluido en Python, sin dependencias extra).
# Muestra en tiempo real: sensores, motores, umbrales y estado de alarma.
# Se actualiza automáticamente cada 2 segundos usando root.after().

import tkinter as tk
from tkinter import messagebox
import time
from typing import Optional

from core.plc_interface import SiloPLC, SensorReading, MotorStatus
from config import PLC_IP


# ══════════════════════════════════════════════════════════════════════════════
# Paleta de colores (tema oscuro tipo SCADA industrial)
# ══════════════════════════════════════════════════════════════════════════════
C_BG        = "#f0f4f8"   # Fondo principal de la ventana
C_FRAME     = "#ffffff"   # Fondo de cada panel
C_FRAME2    = "#f1f5f9"   # Fondo de filas alternadas / sub-frames
C_TEXT      = "#1e293b"   # Texto general
C_TEXT_DIM  = "#64748b"   # Texto secundario / etiquetas
C_GREEN     = "#166534"   # Estado OK, motor ON, sensor activo
C_RED       = "#991b1b"   # Alarma, motor con falla, error
C_YELLOW    = "#92400e"   # Advertencia, modo manual
C_BLUE      = "#1d4ed8"   # Valores de sensor, títulos
C_BTN       = "#e2e8f0"   # Fondo de botones
C_BTN_ACT   = "#cbd5e1"   # Botón hover / activo
C_BORDER    = "#cbd5e1"   # Borde de frames

# Fondos para el bloque indicador de alarma (3 niveles)
C_ALARM_GRN = "#22c55e"   # Verde  — sin alarma
C_ALARM_YEL = "#f59e0b"   # Ámbar  — advertencia
C_ALARM_RED = "#ef4444"   # Rojo   — alarma activa

REFRESH_MS       = 2000   # milisegundos entre cada refresco automático
WARN_TEMP_MARGIN = 5.0    # °C antes del umbral máx/mín → nivel ADVERTENCIA
WARN_HUM_MARGIN  = 5.0    # %RH antes del umbral máx   → nivel ADVERTENCIA

FONT_TITLE  = ("Consolas", 13, "bold")
FONT_LABEL  = ("Consolas", 10)
FONT_VALUE  = ("Consolas", 11, "bold")
FONT_BTN    = ("Consolas", 9)
FONT_HEADER = ("Consolas", 16, "bold")
FONT_ALARM  = ("Consolas", 12, "bold")


class SiloApp(tk.Tk):
    """Ventana principal del monitor S7-1515-2 PN.

    Muestra en tres paneles:
      - Cables SL: temperatura máxima (hotspot) y promedio de cada cable SL3000/SL5000.
      - Ventilación: estado de cada ventilador de aireación con botones de control.
      - Umbrales: temp_max, temp_min editables y semáforo de alarma.

    Se actualiza cada REFRESH_MS ms usando tkinter.after() para no bloquear la GUI.

    Args:
        plc: Instancia de SiloPLC ya conectada.
    """

    def __init__(self, plc: SiloPLC) -> None:
        super().__init__()
        self._plc = plc

        # ── Configuración de la ventana ────────────────────────────────────
        self.title("S7-1515-2 PN / PLCSIM - Monitor de Silo")
        self.configure(bg=C_BG)
        self.resizable(True, True)
        self.minsize(960, 640)

        # Centrar en pantalla
        self.update_idletasks()
        w, h = 1050, 680
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Interceptar el cierre de ventana para limpiar recursos
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Variables de estado compartidas ───────────────────────────────
        # Widgets dinámicos que se actualizan en _refresh()
        self._sensor_widgets: list[dict] = []   # una entrada por sensor
        self._motor_widgets:  list[dict] = []   # una entrada por motor
        self._lbl_conn:     Optional[tk.Label] = None
        self._lbl_time:     Optional[tk.Label] = None
        self._lbl_alarm:    Optional[tk.Label] = None
        self._entry_tmax:   Optional[tk.Entry] = None
        self._entry_hmax:   Optional[tk.Entry] = None
        self._lbl_tmin:       Optional[tk.Label] = None
        self._lbl_avg_temp:   Optional[tk.Label] = None
        self._lbl_avg_hum:    Optional[tk.Label] = None
        self._btn_mode_all: Optional[tk.Button] = None
        # ID del callback after() activo — necesario para cancelarlo en _on_close
        self._refresh_job:    Optional[str] = None

        # Construir la UI
        self._build_ui()

        # Lanzar el primer ciclo de refresco
        self._refresh_job = self.after(100, self._refresh)

    # ══════════════════════════════════════════════════════════════════════
    # Construcción de la UI
    # ══════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        """Construye todos los widgets de la ventana."""
        self._build_header()

        # Contenedor principal con 3 columnas
        body = tk.Frame(self, bg=C_BG)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.columnconfigure(2, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_sensors_frame(body)
        self._build_motors_frame(body)
        self._build_thresholds_frame(body)

    # ── Header ─────────────────────────────────────────────────────────────

    def _build_header(self) -> None:
        """Barra superior con título, IP, estado de conexión y reloj."""
        hdr = tk.Frame(self, bg=C_FRAME, height=60)
        hdr.pack(fill=tk.X, padx=10, pady=10)
        hdr.pack_propagate(False)

        # Título
        tk.Label(
            hdr, text="S7-1515-2 PN / PLCSIM",
            font=FONT_HEADER, bg=C_FRAME, fg=C_BLUE,
        ).pack(side=tk.LEFT, padx=16)

        # IP del PLC
        tk.Label(
            hdr, text=f"PLC: {PLC_IP}",
            font=FONT_LABEL, bg=C_FRAME, fg=C_TEXT_DIM,
        ).pack(side=tk.LEFT, padx=10)

        # Estado de conexión (se actualiza en _refresh)
        self._lbl_conn = tk.Label(
            hdr, text="● CONECTANDO...",
            font=FONT_LABEL, bg=C_FRAME, fg=C_YELLOW,
        )
        self._lbl_conn.pack(side=tk.LEFT, padx=10)

        # Reloj (se actualiza en _refresh)
        self._lbl_time = tk.Label(
            hdr, text="",
            font=FONT_LABEL, bg=C_FRAME, fg=C_TEXT_DIM,
        )
        self._lbl_time.pack(side=tk.RIGHT, padx=16)

    # ── Panel Sensores ──────────────────────────────────────────────────────

    def _build_sensors_frame(self, parent: tk.Frame) -> None:
        """Panel izquierdo con lecturas de los cables sensor SL3000/SL5000."""
        outer = tk.Frame(parent, bg=C_BORDER, bd=1)
        outer.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        frame = tk.Frame(outer, bg=C_FRAME)
        frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # Título del panel
        tk.Label(
            frame, text="CABLES SL",
            font=FONT_TITLE, bg=C_FRAME, fg=C_BLUE,
        ).pack(pady=(12, 6))

        # ── Tabla centrada con grid ────────────────────────────────────────
        table = tk.Frame(frame, bg=C_FRAME)
        table.pack(anchor="center", pady=(0, 4))

        # Anchos fijos de columna (en caracteres)
        COL_WIDTHS = [4, 10, 10, 3]   # Sensor | Temp | Humedad | Est

        # Cabecera
        hdr_bg = C_FRAME2
        for col, (txt, w) in enumerate(zip(["#", "Temp", "Humedad", "Est"], COL_WIDTHS)):
            tk.Label(
                table, text=txt, font=FONT_LABEL,
                bg=hdr_bg, fg=C_TEXT_DIM, width=w, anchor="center",
                padx=6, pady=4,
            ).grid(row=0, column=col, padx=2, pady=(0, 2), sticky="nsew")

        # Una fila por sensor
        self._sensor_widgets = []
        sensor_names = ["T0", "T1", "H2"]
        for i in range(3):
            row_bg = C_FRAME if i % 2 == 0 else C_FRAME2
            r = i + 1   # fila 0 es la cabecera

            # Columna 0 — índice del cable
            tk.Label(
                table, text=sensor_names[i], font=FONT_LABEL,
                bg=row_bg, fg=C_TEXT_DIM, width=COL_WIDTHS[0], anchor="center",
                padx=6, pady=6,
            ).grid(row=r, column=0, padx=2, pady=1, sticky="nsew")

            # Columna 1 — temperatura
            lbl_temp = tk.Label(
                table, text="---", font=FONT_VALUE,
                bg=row_bg, fg=C_BLUE, width=COL_WIDTHS[1], anchor="center",
            )
            lbl_temp.grid(row=r, column=1, padx=2, pady=1, sticky="nsew")

            # Columna 2 — humedad
            lbl_hum = tk.Label(
                table, text="---", font=FONT_VALUE,
                bg=row_bg, fg=C_BLUE, width=COL_WIDTHS[2], anchor="center",
            )
            lbl_hum.grid(row=r, column=2, padx=2, pady=1, sticky="nsew")

            # Columna 3 — indicador circular
            cell = tk.Frame(table, bg=row_bg, width=COL_WIDTHS[3] * 8, height=30)
            cell.grid(row=r, column=3, padx=2, pady=1, sticky="nsew")
            cell.pack_propagate(False)
            canvas = tk.Canvas(cell, width=18, height=18,
                               bg=row_bg, highlightthickness=0)
            canvas.place(relx=0.5, rely=0.5, anchor="center")
            dot = canvas.create_oval(2, 2, 16, 16, fill=C_TEXT_DIM, outline="")

            self._sensor_widgets.append({
                "lbl_temp": lbl_temp,
                "lbl_hum":  lbl_hum,
                "canvas":   canvas,
                "dot":      dot,
                "row_bg":   row_bg,
            })

        # Separador y promedio
        tk.Frame(frame, bg=C_BORDER, height=1).pack(fill=tk.X, padx=8, pady=8)
        avg_row = tk.Frame(frame, bg=C_FRAME)
        avg_row.pack(anchor="center")
        tk.Label(avg_row, text="Prom Temp / Humedad:",
                 font=FONT_LABEL, bg=C_FRAME, fg=C_TEXT_DIM).pack(side=tk.LEFT)
        self._lbl_avg_temp = tk.Label(avg_row, text="--.- °C",
                                      font=FONT_VALUE, bg=C_FRAME, fg=C_YELLOW)
        self._lbl_avg_temp.pack(side=tk.LEFT, padx=8)
        self._lbl_avg_hum = tk.Label(avg_row, text="--.- %",
                                     font=FONT_VALUE, bg=C_FRAME, fg=C_YELLOW)
        self._lbl_avg_hum.pack(side=tk.LEFT)

    # ── Panel Motores ───────────────────────────────────────────────────────

    def _build_motors_frame(self, parent: tk.Frame) -> None:
        """Panel central con estado y controles de los ventiladores de aireación."""
        outer = tk.Frame(parent, bg=C_BORDER, bd=1)
        outer.grid(row=0, column=1, sticky="nsew", padx=5)

        frame = tk.Frame(outer, bg=C_FRAME)
        frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        tk.Label(frame, text="VENTILACIÓN", font=FONT_TITLE,
                 bg=C_FRAME, fg=C_BLUE).pack(pady=(12, 6))

        self._motor_widgets = []
        for i in range(4):
            mf = tk.LabelFrame(
                frame,
                text=f" Ventilador {i} ",
                font=FONT_LABEL,
                bg=C_FRAME2,
                fg=C_TEXT_DIM,
                bd=1,
                relief=tk.GROOVE,
            )
            mf.pack(fill=tk.X, padx=10, pady=5)

            # ── Fila de estado ──────────────────────────────────────────
            status_row = tk.Frame(mf, bg=C_FRAME2)
            status_row.pack(fill=tk.X, padx=6, pady=(6, 2))

            lbl_running = tk.Label(status_row, text="OFF",
                                   font=FONT_VALUE, bg=C_FRAME2, fg=C_RED, width=4)
            lbl_running.pack(side=tk.LEFT, padx=(0, 6))

            lbl_mode = tk.Label(status_row, text="MANUAL",
                                font=FONT_LABEL, bg=C_FRAME2, fg=C_YELLOW, width=7)
            lbl_mode.pack(side=tk.LEFT, padx=4)

            lbl_enabled = tk.Label(status_row, text="HAB",
                                   font=FONT_LABEL, bg=C_FRAME2, fg=C_GREEN, width=5)
            lbl_enabled.pack(side=tk.LEFT, padx=4)

            lbl_fault = tk.Label(status_row, text="OK",
                                 font=FONT_LABEL, bg=C_FRAME2, fg=C_GREEN, width=6)
            lbl_fault.pack(side=tk.LEFT, padx=4)

            # ── Fila de botones ─────────────────────────────────────────
            btn_row = tk.Frame(mf, bg=C_FRAME2)
            btn_row.pack(fill=tk.X, padx=6, pady=(2, 6))

            idx = i  # captura para el lambda

            def _make_btn(parent, text, color, cmd):
                b = tk.Button(
                    parent, text=text, font=FONT_BTN,
                    bg=C_BTN, fg=color, activebackground=C_BTN_ACT,
                    activeforeground=color, relief=tk.FLAT,
                    padx=4, pady=2, cursor="hand2",
                    command=cmd,
                )
                b.pack(side=tk.LEFT, padx=2)
                return b

            _make_btn(btn_row, "▶ Start", C_GREEN,
                      lambda i=idx: self._cmd_motor(i, "start"))
            _make_btn(btn_row, "■ Stop",  C_RED,
                      lambda i=idx: self._cmd_motor(i, "stop"))
            _make_btn(btn_row, "A Auto",  C_BLUE,
                      lambda i=idx: self._cmd_motor(i, "auto"))
            _make_btn(btn_row, "M Man",   C_YELLOW,
                      lambda i=idx: self._cmd_motor(i, "manual"))
            _make_btn(btn_row, "✓ Hab",   C_GREEN,
                      lambda i=idx: self._cmd_motor(i, "enable"))
            _make_btn(btn_row, "✗ Desh",  C_RED,
                      lambda i=idx: self._cmd_motor(i, "disable"))

            self._motor_widgets.append({
                "lbl_running": lbl_running,
                "lbl_mode":    lbl_mode,
                "lbl_enabled": lbl_enabled,
                "lbl_fault":   lbl_fault,
                "frame":       mf,
            })

    # ── Panel Umbrales ──────────────────────────────────────────────────────

    def _build_thresholds_frame(self, parent: tk.Frame) -> None:
        """Panel derecho con umbrales editables y semáforo de alarma."""
        outer = tk.Frame(parent, bg=C_BORDER, bd=1)
        outer.grid(row=0, column=2, sticky="nsew", padx=(5, 0))

        frame = tk.Frame(outer, bg=C_FRAME)
        frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        tk.Label(frame, text="UMBRALES", font=FONT_TITLE,
                 bg=C_FRAME, fg=C_BLUE).pack(pady=(12, 10))

        # ── Campos editables ────────────────────────────────────────────
        def _labeled_entry(label_text: str) -> tk.Entry:
            row = tk.Frame(frame, bg=C_FRAME)
            row.pack(fill=tk.X, padx=14, pady=5)
            tk.Label(row, text=label_text, font=FONT_LABEL,
                     bg=C_FRAME, fg=C_TEXT_DIM, width=12, anchor="w").pack(side=tk.LEFT)
            entry = tk.Entry(
                row, font=FONT_VALUE, bg=C_FRAME2, fg=C_TEXT,
                insertbackground=C_TEXT, relief=tk.FLAT,
                width=8,
            )
            entry.pack(side=tk.LEFT, padx=4)
            return entry

        self._entry_tmax = _labeled_entry("Temp máx °C:")
        self._entry_tmax.insert(0, "35.0")

        self._entry_hmax = _labeled_entry("Humedad máx %:")
        self._entry_hmax.insert(0, "70.0")

        # Temp min activa (solo lectura)
        row = tk.Frame(frame, bg=C_FRAME)
        row.pack(fill=tk.X, padx=14, pady=5)
        tk.Label(row, text="T.mín activa:", font=FONT_LABEL,
                 bg=C_FRAME, fg=C_TEXT_DIM, width=12, anchor="w").pack(side=tk.LEFT)
        self._lbl_tmin = tk.Label(row, text="--.-", font=FONT_VALUE,
                                  bg=C_FRAME, fg=C_TEXT_DIM)
        self._lbl_tmin.pack(side=tk.LEFT, padx=4)

        # Botón Aplicar
        tk.Frame(frame, bg=C_BORDER, height=1).pack(fill=tk.X, padx=14, pady=8)
        tk.Button(
            frame, text="  Aplicar  ",
            font=FONT_BTN, bg=C_BLUE, fg=C_BG,
            activebackground=C_BTN_ACT, activeforeground=C_TEXT,
            relief=tk.FLAT, padx=6, pady=4, cursor="hand2",
            command=self._apply_thresholds,
        ).pack(pady=4)

        # ── Semáforo de alarma ──────────────────────────────────────────
        tk.Frame(frame, bg=C_BORDER, height=1).pack(fill=tk.X, padx=14, pady=12)

        tk.Label(frame, text="ALARMA", font=FONT_LABEL,
                 bg=C_FRAME, fg=C_TEXT_DIM).pack()

        self._lbl_alarm = tk.Label(
            frame, text="   SIN ALARMA    ",
            font=FONT_ALARM, bg=C_ALARM_GRN, fg="#ffffff",
            padx=10, pady=8,
        )
        self._lbl_alarm.pack(pady=6, padx=14, fill=tk.X)

        # Modo de todos los motores (accion global)
        self._btn_mode_all = tk.Button(
            frame,
            text="Todo a AUTOMATICO",
            font=FONT_BTN,
            bg=C_BTN,
            fg=C_BLUE,
            activebackground=C_BTN_ACT,
            activeforeground=C_BLUE,
            relief=tk.FLAT,
            padx=6,
            pady=4,
            cursor="hand2",
            command=self._toggle_all_modes,
        )
        self._btn_mode_all.pack(pady=(2, 8))

    # ══════════════════════════════════════════════════════════════════════
    # Bucle de refresco
    # ══════════════════════════════════════════════════════════════════════

    def _refresh(self) -> None:
        """Lee el PLC y actualiza todos los widgets.  Se reprograma sola."""
        if self._lbl_time is None or self._lbl_conn is None:
            return

        # Reloj
        self._lbl_time.config(text=time.strftime("%Y-%m-%d  %H:%M:%S"))

        # Estado de conexión
        if self._plc.is_connected():
            self._lbl_conn.config(text="● CONECTADO", fg=C_GREEN)
        else:
            self._lbl_conn.config(text="● DESCONECTADO", fg=C_RED)

        # Umbrales (se leen primero para usarlos al colorear sensores)
        cfg = self._plc.read_thresholds()

        # Sensores
        sensors = self._plc.read_all_sensors()
        if sensors:
            visible_sensors = [s for s in sensors if s.index in (0, 1, 2)]
            temp_sensors = [s for s in visible_sensors if s.active and s.index in (0, 1)]
            hum_sensor = next((s for s in visible_sensors if s.index == 2 and s.active), None)
            self._update_sensors(visible_sensors, cfg)   # cfg puede ser None
            if self._lbl_avg_temp is not None and self._lbl_avg_hum is not None:
                avg_t = (sum(s.temperature for s in temp_sensors) / len(temp_sensors)) if temp_sensors else None
                avg_h = hum_sensor.humidity if hum_sensor else None
                self._lbl_avg_temp.config(text=f"{avg_t:.1f} °C" if avg_t is not None else "--.- °C")
                self._lbl_avg_hum.config(text=f"{avg_h:.1f} %" if avg_h is not None else "--.- %")

        # Motores
        motors = self._plc.read_all_motors()
        if motors:
            self._update_motors(motors)
            self._update_mode_all_button(motors)

        # Entries y etiquetas de umbrales
        if cfg:
            self._update_thresholds(cfg)

        # Indicador de alarma con 3 niveles
        self._update_alarm(self._compute_alarm_level(sensors, cfg))

        # Programar el próximo refresco y guardar el ID para poder cancelarlo
        self._refresh_job = self.after(REFRESH_MS, self._refresh)

    # ── Actualizadores de widgets ─────────────────────────────────────────

    def _update_sensors(
        self,
        sensors: list[SensorReading],
        cfg: dict | None = None,
    ) -> None:
        """Actualiza las filas del panel de sensores.

        Si se pasa cfg, colorea los valores en función de la proximidad al umbral:
          azul   — valor normal
          ámbar  — dentro del margen de advertencia
        """
        temp_max  = float(cfg["temp_max"])  if cfg else 35.0
        temp_min  = float(cfg["temp_min"])  if cfg else 10.0
        humid_max = float(cfg["humid_max"]) if cfg else 70.0

        for s in sensors:
            w = self._sensor_widgets[s.index]
            if s.active:
                if s.index == 2:
                    # H2: solo humedad
                    h_color = C_YELLOW if s.humidity >= humid_max - WARN_HUM_MARGIN else C_BLUE
                    w["lbl_temp"].config(text="    ---", fg=C_TEXT_DIM)
                    w["lbl_hum"].config(text=f"{s.humidity:>7.2f}", fg=h_color)
                else:
                    # T0-T1: solo temperatura
                    t_color = (
                        C_YELLOW
                        if (s.temperature >= temp_max - WARN_TEMP_MARGIN
                            or s.temperature <= temp_min + WARN_TEMP_MARGIN)
                        else C_BLUE
                    )
                    w["lbl_temp"].config(text=f"{s.temperature:>7.2f}", fg=t_color)
                    w["lbl_hum"].config(text="    ---", fg=C_TEXT_DIM)
                w["canvas"].itemconfig(w["dot"], fill=C_GREEN)
            else:
                w["lbl_temp"].config(text="    ---", fg=C_TEXT_DIM)
                w["lbl_hum"].config(text="    ---", fg=C_TEXT_DIM)
                w["canvas"].itemconfig(w["dot"], fill=C_TEXT_DIM)

    def _update_motors(self, motors: list[MotorStatus]) -> None:
        """Actualiza las filas del panel de motores."""
        for m in motors:
            w = self._motor_widgets[m.index]

            # Estado corriendo
            if m.is_running:
                w["lbl_running"].config(text=" ON ", fg=C_GREEN)
            else:
                w["lbl_running"].config(text="OFF ", fg=C_RED)

            # Modo
            if m.auto_mode:
                w["lbl_mode"].config(text="AUTO   ", fg=C_BLUE)
            else:
                w["lbl_mode"].config(text="MANUAL ", fg=C_YELLOW)

            # Habilitado
            if m.enabled:
                w["lbl_enabled"].config(text=" HAB", fg=C_GREEN)
            else:
                w["lbl_enabled"].config(text="DESH", fg=C_RED)

            # Falla
            if m.fault:
                w["lbl_fault"].config(text="FALLA", fg=C_RED)
            else:
                w["lbl_fault"].config(text="  OK ", fg=C_GREEN)

            # Resaltar frame si hay falla
            w["frame"].config(fg=C_RED if m.fault else C_TEXT_DIM)

    @staticmethod
    def _compute_alarm_level(
        sensors: list[SensorReading] | None,
        cfg: dict | None,
    ) -> str:
        """Retorna el nivel de alarma: 'red', 'yellow' o 'green'.

        red    — alarm_active en DB3 está activo (disparado por el PLC).
        yellow — algún sensor activo supera el margen de advertencia.
        green  — todo dentro de los límites normales.
        """
        if cfg is None:
            return "green"
        if cfg.get("alarm_active", False):
            return "red"
        if sensors:
            temp_max  = float(cfg.get("temp_max",  35.0))
            temp_min  = float(cfg.get("temp_min",  10.0))
            humid_max = float(cfg.get("humid_max", 70.0))
            for s in sensors:
                if not s.active:
                    continue
                is_temp_sensor = s.index in (0, 1)
                is_hum_sensor = s.index == 2
                if is_temp_sensor and (
                    s.temperature >= temp_max - WARN_TEMP_MARGIN
                    or s.temperature <= temp_min + WARN_TEMP_MARGIN
                ):
                    return "yellow"
                if is_hum_sensor and s.humidity >= humid_max - WARN_HUM_MARGIN:
                    return "yellow"
        return "green"

    def _update_alarm(self, level: str) -> None:
        """Actualiza el indicador de alarma con color y texto del nivel dado."""
        if self._lbl_alarm is None:
            return
        if level == "red":
            self._lbl_alarm.config(
                text="  *** ALARMA ***  ", bg=C_ALARM_RED, fg="#ffffff")
        elif level == "yellow":
            self._lbl_alarm.config(
                text="   ADVERTENCIA   ", bg=C_ALARM_YEL, fg="#ffffff")
        else:
            self._lbl_alarm.config(
                text="   SIN ALARMA    ", bg=C_ALARM_GRN, fg="#ffffff")

    def _update_thresholds(self, cfg: dict) -> None:
        """Actualiza entries y etiquetas de solo lectura del panel de umbrales."""
        if (self._entry_tmax is None or self._entry_hmax is None
                or self._lbl_tmin is None):
            return

        # Actualizar entries SOLO si el usuario no está escribiendo
        if not self._entry_tmax.focus_get() == self._entry_tmax:
            self._entry_tmax.delete(0, tk.END)
            self._entry_tmax.insert(0, f"{cfg['temp_max']:.1f}")

        if not self._entry_hmax.focus_get() == self._entry_hmax:
            self._entry_hmax.delete(0, tk.END)
            self._entry_hmax.insert(0, f"{cfg['humid_max']:.1f}")

        self._lbl_tmin.config(text=f"{cfg['temp_min']:.1f}")

    def _update_mode_all_button(self, motors: list[MotorStatus]) -> None:
        """Ajusta el texto del boton global segun el estado actual."""
        if self._btn_mode_all is None or not motors:
            return
        all_auto = all(m.auto_mode for m in motors)
        if all_auto:
            self._btn_mode_all.config(text="Todo a MANUAL", fg=C_YELLOW)
        else:
            self._btn_mode_all.config(text="Todo a AUTOMATICO", fg=C_BLUE)

    # ══════════════════════════════════════════════════════════════════════
    # Manejadores de comandos
    # ══════════════════════════════════════════════════════════════════════

    def _cmd_motor(self, index: int, action: str) -> None:
        """Ejecuta un comando de motor y fuerza un refresco inmediato.

        Args:
            index:  Índice del motor (0-3).
            action: Uno de: start, stop, auto, manual, enable, disable.
        """
        dispatch = {
            "start":   lambda: self._plc.set_motor_command(index, True),
            "stop":    lambda: self._plc.set_motor_command(index, False),
            "auto":    lambda: self._plc.set_motor_auto_mode(index, True),
            "manual":  lambda: self._plc.set_motor_auto_mode(index, False),
            "enable":  lambda: self._plc.set_motor_enabled(index, True),
            "disable": lambda: self._plc.set_motor_enabled(index, False),
        }
        ok = dispatch[action]()
        if not ok:
            messagebox.showerror(
                "Error PLC",
                f"No se pudo ejecutar '{action}' en ventilador {index}.\n"
                "Verifica la conexion con el S7/PLCSIM.",
            )

    def _apply_thresholds(self) -> None:
        """Lee los Entry de umbrales y los envia al PLC."""
        if self._entry_tmax is None or self._entry_hmax is None:
            return

        try:
            temp_max = float(self._entry_tmax.get())
            humid_max = float(self._entry_hmax.get())
        except ValueError:
            messagebox.showerror(
                "Valor inválido",
                "Los umbrales deben ser números decimales (ej: 35.0).",
            )
            return

        ok = self._plc.set_thresholds(temp_max=temp_max, humid_max=humid_max)
        if ok:
            messagebox.showinfo(
                "Umbrales actualizados",
                f"Temperatura máx: {temp_max:.1f} °C\n"
                f"Humedad máx: {humid_max:.1f} %",
            )
        else:
            messagebox.showerror(
                "Error PLC",
                "No se pudieron escribir los umbrales en el S7/PLCSIM.",
            )

    def _toggle_all_modes(self) -> None:
        """Alterna todos los motores entre modo manual y automatico."""
        motors = self._plc.read_all_motors()
        if not motors:
            messagebox.showerror(
                "Error PLC",
                "No se pudo leer el estado de motores para cambio global.",
            )
            return

        target_auto = not all(m.auto_mode for m in motors)
        failed: list[int] = []
        for m in motors:
            if not self._plc.set_motor_auto_mode(m.index, target_auto):
                failed.append(m.index)

        if failed:
            messagebox.showerror(
                "Error PLC",
                "No se pudo cambiar el modo en: " + ", ".join(str(i) for i in failed),
            )
            return

        # Actualizacion inmediata del panel de motores, sin crear un nuevo ciclo after().
        updated = self._plc.read_all_motors()
        if updated:
            self._update_motors(updated)
            self._update_mode_all_button(updated)

    # ══════════════════════════════════════════════════════════════════════
    # Cierre limpio
    # ══════════════════════════════════════════════════════════════════════

    def _on_close(self) -> None:
        """Desconecta el PLC antes de cerrar la ventana."""
        if self._refresh_job is not None:
            self.after_cancel(self._refresh_job)
            self._refresh_job = None
        try:
            self._plc.disconnect()
        except Exception:
            pass
        self.destroy()
