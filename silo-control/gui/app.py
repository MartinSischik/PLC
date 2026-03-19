# gui/app.py
# Interfaz grafica principal del sistema SCADA — soporte multi-silo modular.
#
# Layout:
#   - Header: titulo, IP del PLC, estado de conexion, reloj.
#   - Barra de estado: indicador de alarma global + botones "Habilitar/Deshabilitar Todo".
#   - Area de silos (scrollable): una tarjeta por silo definido en config.SILOS.
#
# Cada tarjeta SiloPanel contiene:
#   1. Tiles de sensores (temperatura/humedad) — con color segun alarma.
#   2. Por cada motor: tipo (SS/VFD), boton AUTO/MANUAL, ON/OFF, HAB/DESH.
#
# Para agregar silos/motores/sensores: editar config.py (sin tocar este archivo).

import tkinter as tk
from tkinter import messagebox
import time
from typing import Optional

from core.plc_interface import SiloPLC, SensorReading, MotorStatus
from config import PLC_IP, SILOS, SiloDefinition, SensorConfig, MotorConfig


# ══════════════════════════════════════════════════════════════════════════════
# Paleta de colores
# ══════════════════════════════════════════════════════════════════════════════

C_BG        = "#f0f4f8"
C_FRAME     = "#ffffff"
C_FRAME2    = "#f1f5f9"
C_TEXT      = "#1e293b"
C_TEXT_DIM  = "#64748b"
C_GREEN     = "#166534"
C_RED       = "#991b1b"
C_YELLOW    = "#92400e"
C_BLUE      = "#1d4ed8"
C_BTN       = "#e2e8f0"
C_BTN_ACT   = "#cbd5e1"
C_BORDER    = "#cbd5e1"

C_TILE_OK    = "#dcfce7"
C_TILE_WARN  = "#fef9c3"
C_TILE_ALARM = "#fee2e2"
C_TILE_OFF   = "#f1f5f9"

C_ALARM_GRN = "#22c55e"
C_ALARM_YEL = "#f59e0b"
C_ALARM_RED = "#ef4444"

C_BTN_AUTO_ON   = "#bfdbfe"
C_BTN_MANUAL_ON = "#fef08a"

# Color badge tipo motor
C_BADGE_SS  = "#dbeafe"   # azul claro — soft starter
C_BADGE_VFD = "#fce7f3"   # rosa claro — VFD

REFRESH_MS       = 2000
WARN_TEMP_MARGIN = 5.0
WARN_HUM_MARGIN  = 5.0

FONT_TITLE      = ("Consolas", 13, "bold")
FONT_LABEL      = ("Consolas", 10)
FONT_VALUE      = ("Consolas", 11, "bold")
FONT_BTN        = ("Consolas", 9)
FONT_HEADER     = ("Consolas", 16, "bold")
FONT_ALARM      = ("Consolas", 12, "bold")
FONT_SENSOR_VAL = ("Consolas", 22, "bold")
FONT_SENSOR_LBL = ("Consolas", 9)
FONT_SENSOR_SUB = ("Consolas", 8)
FONT_BADGE      = ("Consolas", 7, "bold")


# ══════════════════════════════════════════════════════════════════════════════
# SensorTile — tile visual grande para un sensor
# ══════════════════════════════════════════════════════════════════════════════

class SensorTile(tk.Frame):
    """Tile cuadrado que muestra el valor principal de un sensor."""

    def __init__(self, parent: tk.Widget, sensor_cfg: SensorConfig, **kwargs) -> None:
        kwargs.setdefault("bg", C_TILE_OFF)
        super().__init__(parent, relief=tk.FLAT, bd=0, **kwargs)
        self._cfg = sensor_cfg
        self._bg_widgets: list = []
        self._build()

    def _build(self) -> None:
        bg = self["bg"]

        hdr = tk.Frame(self, bg=bg)
        hdr.pack(fill=tk.X, padx=8, pady=(8, 0))
        self._bg_widgets.append(hdr)

        self._canvas = tk.Canvas(hdr, width=12, height=12,
                                 bg=bg, highlightthickness=0)
        self._canvas.pack(side=tk.LEFT, padx=(0, 4))
        self._dot = self._canvas.create_oval(1, 1, 11, 11,
                                             fill=C_TEXT_DIM, outline="")

        lbl_name = tk.Label(hdr, text=self._cfg.label,
                            font=FONT_SENSOR_LBL, bg=bg, fg=C_TEXT_DIM)
        lbl_name.pack(side=tk.LEFT)
        self._bg_widgets.append(lbl_name)

        self._lbl_main = tk.Label(self, text="---",
                                   font=FONT_SENSOR_VAL, bg=bg, fg=C_TEXT_DIM)
        self._lbl_main.pack(pady=(4, 0))
        self._bg_widgets.append(self._lbl_main)

        self._lbl_sub = tk.Label(self, text="",
                                  font=FONT_SENSOR_SUB, bg=bg, fg=C_TEXT_DIM)
        self._lbl_sub.pack(pady=(0, 8))
        self._bg_widgets.append(self._lbl_sub)

    def _set_bg(self, color: str) -> None:
        self.config(bg=color)
        self._canvas.config(bg=color)
        for w in self._bg_widgets:
            try:
                w.config(bg=color)
            except tk.TclError:
                pass

    def refresh_data(self, s: SensorReading, cfg: Optional[dict]) -> None:
        if not s.active:
            self._set_bg(C_TILE_OFF)
            self._canvas.itemconfig(self._dot, fill=C_TEXT_DIM)
            self._lbl_main.config(text="---", fg=C_TEXT_DIM)
            self._lbl_sub.config(text="INACTIVO", fg=C_TEXT_DIM)
            return

        temp_max  = float(cfg["temp_max"])  if cfg else 35.0
        temp_min  = float(cfg["temp_min"])  if cfg else 10.0
        humid_max = float(cfg["humid_max"]) if cfg else 70.0

        if self._cfg.show_humidity:
            val   = s.humidity
            alarm = val >= humid_max
            warn  = val >= humid_max - WARN_HUM_MARGIN
            bg    = C_TILE_ALARM if alarm else (C_TILE_WARN if warn else C_TILE_OK)
            self._set_bg(bg)
            self._canvas.itemconfig(self._dot, fill=C_GREEN)
            self._lbl_main.config(text=f"{val:.1f}%", fg=C_TEXT)
            self._lbl_sub.config(text="humedad", fg=C_TEXT_DIM)
        else:
            val   = s.temperature
            alarm = val >= temp_max or val <= temp_min
            warn  = (val >= temp_max - WARN_TEMP_MARGIN
                     or val <= temp_min + WARN_TEMP_MARGIN)
            bg    = C_TILE_ALARM if alarm else (C_TILE_WARN if warn else C_TILE_OK)
            self._set_bg(bg)
            self._canvas.itemconfig(self._dot, fill=C_GREEN)
            self._lbl_main.config(text=f"{val:.1f}\u00b0C", fg=C_TEXT)
            self._lbl_sub.config(text="temperatura", fg=C_TEXT_DIM)


# ══════════════════════════════════════════════════════════════════════════════
# MotorControl — panel de control para un motor individual
# ══════════════════════════════════════════════════════════════════════════════

class MotorControl(tk.Frame):
    """Panel de control compacto para un motor.

    Muestra el tipo (SS/VFD), estado en la cabecera y tres botones toggle:
      [AUTO/MANUAL]  [ON/OFF]  [HAB/DESH]
    """

    def __init__(self, parent: tk.Widget, motor_cfg: MotorConfig,
                 plc: SiloPLC, **kwargs) -> None:
        kwargs.setdefault("bg", C_FRAME2)
        super().__init__(parent, **kwargs)
        self._plc      = plc
        self._cfg      = motor_cfg
        self._idx      = motor_cfg.index
        self._auto_mode = False
        self._running   = False
        self._enabled   = True
        self._build()

    def _build(self) -> None:
        bg = self["bg"]

        # ── Cabecera: tipo + nombre + indicadores ──────────────────────
        hdr = tk.Frame(self, bg=bg)
        hdr.pack(fill=tk.X, padx=8, pady=(6, 3))

        # Badge tipo motor
        type_text = "VFD" if self._cfg.motor_type == "vfd" else "SS"
        type_bg   = C_BADGE_VFD if self._cfg.motor_type == "vfd" else C_BADGE_SS
        type_fg   = "#9d174d" if self._cfg.motor_type == "vfd" else "#1e40af"
        tk.Label(hdr, text=f" {type_text} ", font=FONT_BADGE,
                 bg=type_bg, fg=type_fg).pack(side=tk.LEFT, padx=(0, 4))

        # Nombre del motor
        label = self._cfg.label or f"Motor {self._idx}"
        tk.Label(hdr, text=label,
                 font=FONT_LABEL, bg=bg, fg=C_TEXT).pack(side=tk.LEFT)

        self._lbl_fault = tk.Label(hdr, text="  OK ",
                                    font=FONT_LABEL, bg=bg, fg=C_GREEN, width=6)
        self._lbl_fault.pack(side=tk.RIGHT, padx=2)

        self._lbl_enabled_ind = tk.Label(hdr, text=" HAB ",
                                          font=FONT_LABEL, bg=bg, fg=C_GREEN, width=5)
        self._lbl_enabled_ind.pack(side=tk.RIGHT, padx=2)

        self._lbl_running = tk.Label(hdr, text="OFF",
                                      font=FONT_VALUE, bg=bg, fg=C_RED, width=4)
        self._lbl_running.pack(side=tk.RIGHT, padx=4)

        tk.Frame(self, bg=C_BORDER, height=1).pack(fill=tk.X, padx=8)

        # ── Fila de botones toggle ──────────────────────────────────────
        btn_row = tk.Frame(self, bg=bg)
        btn_row.pack(fill=tk.X, padx=8, pady=(4, 6))

        self._btn_mode = tk.Button(
            btn_row, text="MANUAL", font=FONT_BTN,
            bg=C_BTN_MANUAL_ON, fg=C_YELLOW,
            activebackground=C_BTN_ACT, relief=tk.FLAT,
            padx=8, pady=4, cursor="hand2",
            command=self._toggle_mode,
        )
        self._btn_mode.pack(side=tk.LEFT, padx=2)

        self._btn_onoff = tk.Button(
            btn_row, text="\u25b6 ON", font=FONT_BTN,
            bg=C_BTN, fg=C_GREEN,
            activebackground=C_BTN_ACT, relief=tk.FLAT,
            padx=8, pady=4, cursor="hand2",
            command=self._toggle_onoff,
        )
        self._btn_onoff.pack(side=tk.LEFT, padx=2)

        self._btn_enabled = tk.Button(
            btn_row, text=" HAB ", font=FONT_BTN,
            bg=C_BTN, fg=C_GREEN,
            activebackground=C_BTN_ACT, relief=tk.FLAT,
            padx=8, pady=4, cursor="hand2",
            command=self._toggle_enabled,
        )
        self._btn_enabled.pack(side=tk.LEFT, padx=2)

    def _toggle_mode(self) -> None:
        self._cmd("manual" if self._auto_mode else "auto")

    def _toggle_onoff(self) -> None:
        self._cmd("stop" if self._running else "start")

    def _toggle_enabled(self) -> None:
        self._cmd("disable" if self._enabled else "enable")

    def _cmd(self, action: str) -> None:
        dispatch = {
            "start":   lambda: self._plc.set_motor_command(self._idx, True),
            "stop":    lambda: self._plc.set_motor_command(self._idx, False),
            "auto":    lambda: self._plc.set_motor_auto_mode(self._idx, True),
            "manual":  lambda: self._plc.set_motor_auto_mode(self._idx, False),
            "enable":  lambda: self._plc.set_motor_enabled(self._idx, True),
            "disable": lambda: self._plc.set_motor_enabled(self._idx, False),
        }
        if not dispatch[action]():
            label = self._cfg.label or f"Motor {self._idx}"
            messagebox.showerror(
                "Error PLC",
                f"No se pudo ejecutar '{action}' en {label}.\n"
                "Verifica la conexion con el S7/PLCSIM.",
            )

    def update_status(self, m: MotorStatus) -> None:
        self._auto_mode = m.auto_mode
        self._running   = m.is_running
        self._enabled   = m.enabled

        if m.is_running:
            self._lbl_running.config(text=" ON ", fg=C_GREEN)
            self._btn_onoff.config(text="\u25a0 OFF", fg=C_RED, bg="#fecaca")
        else:
            self._lbl_running.config(text="OFF ", fg=C_RED)
            self._btn_onoff.config(text="\u25b6 ON ", fg=C_GREEN, bg=C_BTN)

        if m.auto_mode:
            self._btn_mode.config(text=" AUTO ", fg=C_BLUE, bg=C_BTN_AUTO_ON)
        else:
            self._btn_mode.config(text="MANUAL", fg=C_YELLOW, bg=C_BTN_MANUAL_ON)

        if m.enabled:
            self._btn_enabled.config(text=" HAB ", fg=C_GREEN, bg=C_BTN)
        else:
            self._btn_enabled.config(text=" DESH", fg=C_RED, bg="#fecaca")

        if m.enabled:
            self._lbl_enabled_ind.config(text=" HAB ", fg=C_GREEN)
        else:
            self._lbl_enabled_ind.config(text=" DESH", fg=C_RED)

        if m.fault:
            self._lbl_fault.config(text="FALLA", fg=C_RED)
        else:
            self._lbl_fault.config(text="  OK ", fg=C_GREEN)


# ══════════════════════════════════════════════════════════════════════════════
# SiloPanel — tarjeta completa de un silo
# ══════════════════════════════════════════════════════════════════════════════

class SiloPanel(tk.Frame):
    """Tarjeta vertical con sensores y motores de un silo."""

    def __init__(self, parent: tk.Widget, silo_def: SiloDefinition,
                 plc: SiloPLC, **kwargs) -> None:
        super().__init__(parent, bg=C_FRAME, relief=tk.FLAT, **kwargs)
        self._silo = silo_def
        self._plc  = plc
        self._sensor_tiles:    dict[int, SensorTile]    = {}
        self._motor_controls:  dict[int, MotorControl]  = {}
        self._build()

    def _build(self) -> None:
        # ── Cabecera ─────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=C_BLUE)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=self._silo.name,
                 font=FONT_TITLE, bg=C_BLUE, fg="#ffffff").pack(pady=10, padx=12)

        # ── Seccion sensores ─────────────────────────────────────────────
        if self._silo.sensors:
            sens_outer = tk.Frame(self, bg=C_BORDER, bd=1)
            sens_outer.pack(fill=tk.X, padx=10, pady=(10, 5))

            sens_inner = tk.Frame(sens_outer, bg=C_FRAME2)
            sens_inner.pack(fill=tk.BOTH, padx=1, pady=1)

            tk.Label(sens_inner, text="SENSORES",
                     font=FONT_LABEL, bg=C_FRAME2, fg=C_TEXT_DIM
                     ).pack(anchor="w", padx=10, pady=(6, 2))

            tiles_row = tk.Frame(sens_inner, bg=C_FRAME2)
            tiles_row.pack(fill=tk.X, padx=8, pady=(0, 8))

            for s_cfg in self._silo.sensors:
                tile = SensorTile(tiles_row, s_cfg, bg=C_TILE_OFF)
                tile.pack(side=tk.LEFT, padx=4, pady=2, expand=True, fill=tk.BOTH)
                self._sensor_tiles[s_cfg.index] = tile

        # ── Seccion motores ──────────────────────────────────────────────
        if self._silo.motors:
            mot_outer = tk.Frame(self, bg=C_BORDER, bd=1)
            mot_outer.pack(fill=tk.X, padx=10, pady=(5, 10))

            mot_inner = tk.Frame(mot_outer, bg=C_FRAME)
            mot_inner.pack(fill=tk.BOTH, padx=1, pady=1)

            tk.Label(mot_inner, text="MOTORES",
                     font=FONT_LABEL, bg=C_FRAME, fg=C_TEXT_DIM
                     ).pack(anchor="w", padx=10, pady=(6, 2))

            for i, motor_cfg in enumerate(self._silo.motors):
                if i > 0:
                    tk.Frame(mot_inner, bg=C_BORDER, height=1).pack(
                        fill=tk.X, padx=8)
                ctrl = MotorControl(mot_inner, motor_cfg, self._plc, bg=C_FRAME2)
                ctrl.pack(fill=tk.X, padx=6, pady=3)
                self._motor_controls[motor_cfg.index] = ctrl

    def refresh_data(self, sensors: list[SensorReading],
                     motors: list[MotorStatus],
                     cfg: Optional[dict]) -> None:
        sensor_map = {s.index: s for s in sensors}
        for s_idx, tile in self._sensor_tiles.items():
            s = sensor_map.get(s_idx)
            if s is not None:
                tile.refresh_data(s, cfg)

        motor_map = {m.index: m for m in motors}
        for m_idx, ctrl in self._motor_controls.items():
            m = motor_map.get(m_idx)
            if m is not None:
                ctrl.update_status(m)

    def motor_indices(self) -> list[int]:
        return list(self._motor_controls.keys())


# ══════════════════════════════════════════════════════════════════════════════
# SiloApp — ventana principal
# ══════════════════════════════════════════════════════════════════════════════

class SiloApp(tk.Tk):
    """Ventana SCADA multi-silo modular.

    Genera un SiloPanel por cada SiloDefinition en config.SILOS.
    """

    def __init__(self, plc: SiloPLC) -> None:
        super().__init__()
        self._plc          = plc
        self._silo_panels: list[SiloPanel]    = []
        self._lbl_conn:    Optional[tk.Label] = None
        self._lbl_time:    Optional[tk.Label] = None
        self._lbl_alarm:   Optional[tk.Label] = None
        self._refresh_job: Optional[str]      = None

        self.title("SCADA \u2014 Control de Silos")
        self.configure(bg=C_BG)
        self.resizable(True, True)
        self.minsize(760, 580)

        w = max(320 * max(len(SILOS), 1) + 80, 900)
        h = 720
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._build_ui()
        self._refresh_job = self.after(100, self._refresh)

    # ── Construccion de la UI ─────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._build_header()
        self._build_status_bar()
        self._build_silos_area()

    def _build_header(self) -> None:
        hdr = tk.Frame(self, bg=C_FRAME, height=58)
        hdr.pack(fill=tk.X, padx=10, pady=(10, 0))
        hdr.pack_propagate(False)

        tk.Label(hdr, text="SCADA \u2014 Control de Silos",
                 font=FONT_HEADER, bg=C_FRAME, fg=C_BLUE,
                 ).pack(side=tk.LEFT, padx=16)

        tk.Label(hdr, text=f"PLC: {PLC_IP}",
                 font=FONT_LABEL, bg=C_FRAME, fg=C_TEXT_DIM,
                 ).pack(side=tk.LEFT, padx=10)

        self._lbl_conn = tk.Label(hdr, text="\u25cf CONECTANDO...",
                                   font=FONT_LABEL, bg=C_FRAME, fg=C_YELLOW)
        self._lbl_conn.pack(side=tk.LEFT, padx=10)

        self._lbl_time = tk.Label(hdr, text="",
                                   font=FONT_LABEL, bg=C_FRAME, fg=C_TEXT_DIM)
        self._lbl_time.pack(side=tk.RIGHT, padx=16)

    def _build_status_bar(self) -> None:
        bar = tk.Frame(self, bg=C_FRAME2, height=50)
        bar.pack(fill=tk.X, padx=10, pady=(4, 0))
        bar.pack_propagate(False)

        self._lbl_alarm = tk.Label(
            bar, text="   SIN ALARMA   ",
            font=FONT_ALARM, bg=C_ALARM_GRN, fg="#ffffff",
            padx=12, pady=6,
        )
        self._lbl_alarm.pack(side=tk.LEFT, padx=12, pady=7)

        btn_frame = tk.Frame(bar, bg=C_FRAME2)
        btn_frame.pack(side=tk.RIGHT, padx=12, pady=7)

        tk.Button(
            btn_frame, text="\u2717 DESHABILITAR TODO",
            font=FONT_BTN, bg=C_BTN, fg=C_RED,
            activebackground=C_BTN_ACT, relief=tk.FLAT,
            padx=10, pady=4, cursor="hand2",
            command=lambda: self._global_enable_disable(False),
        ).pack(side=tk.RIGHT, padx=4)

        tk.Button(
            btn_frame, text="\u2713 HABILITAR TODO",
            font=FONT_BTN, bg=C_BTN, fg=C_GREEN,
            activebackground=C_BTN_ACT, relief=tk.FLAT,
            padx=10, pady=4, cursor="hand2",
            command=lambda: self._global_enable_disable(True),
        ).pack(side=tk.RIGHT, padx=4)

    def _build_silos_area(self) -> None:
        wrapper = tk.Frame(self, bg=C_BG)
        wrapper.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        hscroll = tk.Scrollbar(wrapper, orient=tk.HORIZONTAL)
        hscroll.pack(side=tk.BOTTOM, fill=tk.X)

        vscroll = tk.Scrollbar(wrapper, orient=tk.VERTICAL)
        vscroll.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(
            wrapper, bg=C_BG, highlightthickness=0,
            xscrollcommand=hscroll.set,
            yscrollcommand=vscroll.set,
        )
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hscroll.config(command=canvas.xview)
        vscroll.config(command=canvas.yview)

        inner = tk.Frame(canvas, bg=C_BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_resize(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_resize(event):
            if inner.winfo_reqwidth() < event.width:
                canvas.itemconfig(win_id, width=event.width)

        inner.bind("<Configure>", _on_inner_resize)
        canvas.bind("<Configure>", _on_canvas_resize)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        for silo_def in SILOS:
            border = tk.Frame(inner, bg=C_BORDER, bd=1)
            border.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)

            panel = SiloPanel(border, silo_def, self._plc)
            panel.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
            self._silo_panels.append(panel)

    # ── Bucle de refresco ─────────────────────────────────────────────────

    def _refresh(self) -> None:
        if self._lbl_conn is None or self._lbl_time is None:
            return

        self._lbl_time.config(text=time.strftime("%Y-%m-%d  %H:%M:%S"))

        if self._plc.is_connected():
            self._lbl_conn.config(text="\u25cf CONECTADO", fg=C_GREEN)
        else:
            self._lbl_conn.config(text="\u25cf DESCONECTADO", fg=C_RED)

        sensors = self._plc.read_all_sensors()
        motors  = self._plc.read_all_motors()
        cfg     = self._plc.read_thresholds()

        for panel in self._silo_panels:
            panel.refresh_data(sensors, motors, cfg)

        self._update_alarm(self._compute_alarm_level(sensors, cfg))

        self._refresh_job = self.after(REFRESH_MS, self._refresh)

    # ── Alarma ───────────────────────────────────────────────────────────

    @staticmethod
    def _compute_alarm_level(
        sensors: list[SensorReading],
        cfg: Optional[dict],
    ) -> str:
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
                if (s.temperature >= temp_max - WARN_TEMP_MARGIN
                        or s.temperature <= temp_min + WARN_TEMP_MARGIN):
                    return "yellow"
                if s.humidity >= humid_max - WARN_HUM_MARGIN:
                    return "yellow"
        return "green"

    def _update_alarm(self, level: str) -> None:
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

    # ── Habilitar / Deshabilitar todo ─────────────────────────────────────

    def _global_enable_disable(self, enable: bool) -> None:
        all_indices = [idx
                       for panel in self._silo_panels
                       for idx in panel.motor_indices()]
        total      = len(all_indices)
        action_str = "HABILITAR" if enable else "DESHABILITAR"

        if total == 0:
            messagebox.showinfo("Sin motores",
                                "No hay motores configurados en ningun silo.")
            return

        confirmed = messagebox.askyesno(
            f"Confirmar: {action_str} TODO",
            f"Esta accion afecta TODOS los motores de la instalacion.\n\n"
            f"Se van a {action_str.lower()} {total} motor"
            f"{'es' if total != 1 else ''} en "
            f"{len(self._silo_panels)} silo"
            f"{'s' if len(self._silo_panels) != 1 else ''}.\n\n"
            f"\u00bfConfirmas?",
            icon="warning",
        )
        if not confirmed:
            return

        failed: list[int] = []
        for idx in all_indices:
            if not self._plc.set_motor_enabled(idx, enable):
                failed.append(idx)

        if failed:
            messagebox.showerror(
                "Error PLC",
                f"No se pudo {'habilitar' if enable else 'deshabilitar'} "
                f"los motores: {', '.join(str(i) for i in failed)}.",
            )
        else:
            messagebox.showinfo(
                "Operacion exitosa",
                f"{total} motor{'es' if total != 1 else ''} "
                f"{'habilitados' if enable else 'deshabilitados'} correctamente.",
            )

    # ── Cierre limpio ─────────────────────────────────────────────────────

    def _on_close(self) -> None:
        if self._refresh_job is not None:
            self.after_cancel(self._refresh_job)
            self._refresh_job = None
        try:
            self._plc.disconnect()
        except Exception:
            pass
        self.destroy()
