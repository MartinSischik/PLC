import time
import tkinter as tk


class SiloApp(tk.Tk):
    """Minimal GUI used by solo_simulacion/main_gui.py."""

    def __init__(self, plc) -> None:
        super().__init__()
        self._plc = plc
        self._job = None

        self.title("SCADA Demo Local")
        self.geometry("760x460")
        self.configure(bg="#f4f6f8")

        self._build_ui()
        self._refresh()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        root = tk.Frame(self, bg="#f4f6f8")
        root.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        title = tk.Label(
            root,
            text="SCADA Demo (sin Docker)",
            bg="#f4f6f8",
            fg="#1f2937",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(anchor="w")

        self._lbl_time = tk.Label(root, bg="#f4f6f8", fg="#4b5563", font=("Segoe UI", 10))
        self._lbl_time.pack(anchor="w", pady=(4, 12))

        card = tk.Frame(root, bg="#ffffff", bd=1, relief=tk.SOLID)
        card.pack(fill=tk.X, pady=(0, 12))

        self._lbl_conn = tk.Label(card, bg="#ffffff", fg="#111827", font=("Segoe UI", 12, "bold"))
        self._lbl_conn.pack(anchor="w", padx=12, pady=(10, 2))

        self._lbl_sensors = tk.Label(card, bg="#ffffff", fg="#111827", font=("Segoe UI", 11))
        self._lbl_sensors.pack(anchor="w", padx=12, pady=2)

        self._lbl_motors = tk.Label(card, bg="#ffffff", fg="#111827", font=("Segoe UI", 11))
        self._lbl_motors.pack(anchor="w", padx=12, pady=2)

        self._lbl_thresholds = tk.Label(card, bg="#ffffff", fg="#111827", font=("Segoe UI", 11))
        self._lbl_thresholds.pack(anchor="w", padx=12, pady=(2, 10))

        help_text = (
            "Tip: esta GUI es de compatibilidad para demo local.\n"
            "Para la version web, usa uvicorn + npm run dev."
        )
        tk.Label(root, text=help_text, bg="#f4f6f8", fg="#6b7280", justify="left").pack(anchor="w")

    def _refresh(self) -> None:
        self._lbl_time.config(text=f"Hora: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        connected = self._plc.is_connected()
        if not connected:
            self._lbl_conn.config(text="PLC: DESCONECTADO", fg="#dc2626")
            self._lbl_sensors.config(text="Sensores activos: 0")
            self._lbl_motors.config(text="Motores corriendo: 0")
            self._lbl_thresholds.config(text="Umbrales: no disponibles")
        else:
            sensors = self._plc.read_all_sensors()
            motors = self._plc.read_all_motors()
            thresholds = self._plc.read_thresholds()

            active_sensors = [s for s in sensors if s.active]
            running_motors = [m for m in motors if m.is_running]

            self._lbl_conn.config(text="PLC: CONECTADO", fg="#059669")
            self._lbl_sensors.config(
                text=f"Sensores activos: {len(active_sensors)}/{len(sensors)}"
            )
            self._lbl_motors.config(
                text=f"Motores corriendo: {len(running_motors)}/{len(motors)}"
            )

            if thresholds:
                self._lbl_thresholds.config(
                    text=(
                        f"Umbrales -> Temp max: {thresholds['temp_max']:.1f} C, "
                        f"Temp min: {thresholds['temp_min']:.1f} C"
                    )
                )
            else:
                self._lbl_thresholds.config(text="Umbrales: no disponibles")

        self._job = self.after(2000, self._refresh)

    def _on_close(self) -> None:
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None
        self.destroy()
