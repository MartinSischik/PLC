import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
from datetime import datetime

# ──────────────────────────────────────────────
#  CONFIGURACIÓN  ← Edita aquí tus datos
# ──────────────────────────────────────────────
API_KEY = ""

LOCATIONS = [
    {"name": "San José",         "lat":  9.9281,  "lon": -84.0907},
    {"name": "Liberia",          "lat":  10.6333, "lon": -85.4333},
    {"name": "Limón",            "lat":  9.9900,  "lon": -83.0360},
    {"name": "Puntarenas",       "lat":  9.9763,  "lon": -84.8327},
    {"name": "Alajuela",         "lat":  10.0162, "lon": -84.2144},
    # Agrega o quita ubicaciones aquí (máx. recomendado: 5)
]

FORECAST_DAYS = 5          # días de pronóstico (máx. 15 con plan estándar)

# ──────────────────────────────────────────────
#  PALETA DE COLORES
# ──────────────────────────────────────────────
C = {
    "bg":         "#F0F4F8",
    "sidebar":    "#FFFFFF",
    "card":       "#FFFFFF",
    "accent":     "#2563EB",
    "accent2":    "#3B82F6",
    "text":       "#1E293B",
    "subtext":    "#64748B",
    "border":     "#E2E8F0",
    "hot":        "#EF4444",
    "cold":       "#3B82F6",
    "mild":       "#10B981",
    "header":     "#1E3A5F",
    "shadow":     "#CBD5E1",
}

WEATHER_ICONS = {
    # Mapeo de iconCode TWC → emoji representativo
    range(1, 3):   "☀️",   # despejado
    range(3, 7):   "⛅",   # parcialmente nublado
    range(7, 12):  "☁️",   # nublado
    range(11, 13): "🌧️",  # lluvia
    range(13, 19): "🌨️",  # nieve
    range(19, 22): "🌪️",  # tormenta
    range(37, 40): "⛈️",   # tormenta eléctrica
    range(40, 48): "🌧️",  # lluvia moderada
}

def get_weather_icon(code):
    if code is None:
        return "🌡️"
    for r, icon in WEATHER_ICONS.items():
        if code in r:
            return icon
    return "🌤️"

def temp_color(temp_c):
    if temp_c is None:
        return C["subtext"]
    if temp_c >= 35:
        return C["hot"]
    if temp_c <= 10:
        return C["cold"]
    return C["mild"]

# ──────────────────────────────────────────────
#  LLAMADAS A LA API
# ──────────────────────────────────────────────
BASE = "https://api.weather.com/v3"

HEADERS = {"Accept-Encoding": "gzip"}

def _raise_with_detail(r):
    """Lanza excepción con el cuerpo de la respuesta para facilitar diagnóstico."""
    try:
        detail = r.json()
    except Exception:
        detail = r.text[:500]
    raise requests.HTTPError(
        f"HTTP {r.status_code} — {detail}", response=r
    )

def fetch_forecast(lat, lon):
    url = f"{BASE}/wx/forecast/daily/{FORECAST_DAYS}day"
    params = {
        "geocode":  f"{lat},{lon}",
        "format":   "json",
        "units":    "m",
        "language": "es-ES",
        "apiKey":   API_KEY.strip(),
    }
    r = requests.get(url, params=params, headers=HEADERS, timeout=10)
    if not r.ok:
        _raise_with_detail(r)
    return r.json()

# ──────────────────────────────────────────────
#  APLICACIÓN TKINTER
# ──────────────────────────────────────────────
class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Weather Monitor · The Weather Company")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(bg=C["bg"])
        self.resizable(True, True)

        self.current_location = tk.IntVar(value=0)
        self.data_cache = {}   # {index: {"forecast": ...}}

        self._build_ui()
        self._select_location(0)

    # ── UI PRINCIPAL ──────────────────────────
    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=C["header"], height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="🌤  Weather Monitor",
                 font=("Segoe UI", 18, "bold"),
                 bg=C["header"], fg="white").pack(side="left", padx=20, pady=12)

        self.lbl_updated = tk.Label(header, text="",
                                     font=("Segoe UI", 9),
                                     bg=C["header"], fg="#93C5FD")
        self.lbl_updated.pack(side="right", padx=20)

        # Contenedor principal
        main = tk.Frame(self, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=16, pady=16)

        # Sidebar de ubicaciones
        sidebar = tk.Frame(main, bg=C["sidebar"], width=200,
                           relief="flat", bd=0,
                           highlightbackground=C["border"],
                           highlightthickness=1)
        sidebar.pack(side="left", fill="y", padx=(0, 14))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="UBICACIONES",
                 font=("Segoe UI", 9, "bold"),
                 bg=C["sidebar"], fg=C["subtext"]).pack(pady=(16, 8), padx=12, anchor="w")

        self.loc_buttons = []
        for i, loc in enumerate(LOCATIONS):
            btn = tk.Button(sidebar,
                            text=f"📍  {loc['name']}",
                            font=("Segoe UI", 10),
                            anchor="w", padx=12,
                            relief="flat", bd=0, cursor="hand2",
                            command=lambda idx=i: self._select_location(idx))
            btn.pack(fill="x", pady=2, padx=8)
            self.loc_buttons.append(btn)

        tk.Frame(sidebar, bg=C["border"], height=1).pack(fill="x", pady=12, padx=8)

        self.btn_refresh = tk.Button(sidebar, text="🔄  Actualizar",
                                      font=("Segoe UI", 10, "bold"),
                                      bg=C["accent"], fg="white",
                                      activebackground=C["accent2"],
                                      activeforeground="white",
                                      relief="flat", bd=0, cursor="hand2",
                                      pady=8,
                                      command=self._refresh)
        self.btn_refresh.pack(fill="x", padx=8, pady=4)

        # Panel derecho
        right = tk.Frame(main, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True)

        # Nombre de la ciudad
        self.lbl_city = tk.Label(right, text="",
                                  font=("Segoe UI", 22, "bold"),
                                  bg=C["bg"], fg=C["text"])
        self.lbl_city.pack(anchor="w", pady=(0, 4))

        self.lbl_coords = tk.Label(right, text="",
                                    font=("Segoe UI", 9),
                                    bg=C["bg"], fg=C["subtext"])
        self.lbl_coords.pack(anchor="w", pady=(0, 12))

        # Scrollable forecast cards
        canvas_frame = tk.Frame(right, bg=C["bg"])
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=C["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical",
                                   command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.cards_frame = tk.Frame(self.canvas, bg=C["bg"])
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.cards_frame, anchor="nw")

        self.cards_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Spinner / estado
        self.lbl_status = tk.Label(right, text="",
                                    font=("Segoe UI", 11),
                                    bg=C["bg"], fg=C["subtext"])
        self.lbl_status.pack(pady=8)

    def _on_frame_configure(self, _):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── LÓGICA DE SELECCIÓN / CARGA ───────────
    def _select_location(self, idx):
        self.current_location.set(idx)
        loc = LOCATIONS[idx]

        # Resaltar botón activo
        for i, btn in enumerate(self.loc_buttons):
            if i == idx:
                btn.configure(bg=C["accent"], fg="white",
                               font=("Segoe UI", 10, "bold"))
            else:
                btn.configure(bg=C["sidebar"], fg=C["text"],
                               font=("Segoe UI", 10))

        self.lbl_city.configure(text=loc["name"])
        self.lbl_coords.configure(text=f"Lat {loc['lat']}  ·  Lon {loc['lon']}")

        if idx in self.data_cache:
            self._render(idx, self.data_cache[idx])
        else:
            self._load_data(idx)

    def _refresh(self):
        idx = self.current_location.get()
        if idx in self.data_cache:
            del self.data_cache[idx]
        self._load_data(idx)

    def _load_data(self, idx):
        self._clear_cards()
        self.lbl_status.configure(text="⏳  Cargando datos...")
        self.btn_refresh.configure(state="disabled")

        def worker():
            loc = LOCATIONS[idx]
            try:
                forecast = fetch_forecast(loc["lat"], loc["lon"])
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda m=err_msg: self._show_error(m))
                return
            data = {"forecast": forecast}
            self.data_cache[idx] = data
            self.after(0, lambda: self._render(idx, data))

        threading.Thread(target=worker, daemon=True).start()

    # ── RENDERIZADO ───────────────────────────
    def _render(self, idx, data):
        self.lbl_status.configure(text="")
        self.btn_refresh.configure(state="normal")
        now = datetime.now().strftime("%d/%m/%Y  %H:%M")
        self.lbl_updated.configure(text=f"Actualizado: {now}")

        self._render_forecast(data.get("forecast", {}))

    def _render_forecast(self, fc):
        self._clear_cards()
        days        = fc.get("dayOfWeek", [])
        dates       = fc.get("validTimeLocal", [])
        max_temps   = fc.get("temperatureMax", [])
        min_temps   = fc.get("temperatureMin", [])
        narratives  = fc.get("narrative", [])
        icon_codes  = fc.get("daypart", [{}])[0].get("iconCode", []) if fc.get("daypart") else []
        precip      = fc.get("qpf", [])

        if not days:
            self.lbl_status.configure(text="⚠️  No se recibieron datos de pronóstico.")
            return

        for i, day in enumerate(days):
            date_str = ""
            if i < len(dates) and dates[i]:
                try:
                    dt = datetime.fromisoformat(dates[i][:10])
                    date_str = dt.strftime("%d %b %Y")
                except:
                    date_str = dates[i][:10]

            t_max  = max_temps[i] if i < len(max_temps) else None
            t_min  = min_temps[i] if i < len(min_temps) else None
            narr   = narratives[i] if i < len(narratives) else ""
            code   = icon_codes[i*2] if icon_codes and i*2 < len(icon_codes) else None
            rain   = precip[i] if i < len(precip) else None

            self._make_day_card(i, day, date_str, t_max, t_min, narr, code, rain)

    def _make_day_card(self, idx, day, date_str, t_max, t_min, narrative, icon_code, rain):
        card = tk.Frame(self.cards_frame,
                        bg=C["card"],
                        highlightbackground=C["border"],
                        highlightthickness=1)
        card.pack(fill="x", pady=5, padx=2)

        # Franja izquierda de color
        accent_bar = tk.Frame(card, bg=C["accent"], width=5)
        accent_bar.pack(side="left", fill="y")

        inner = tk.Frame(card, bg=C["card"], padx=16, pady=12)
        inner.pack(side="left", fill="both", expand=True)

        # Fila superior
        top = tk.Frame(inner, bg=C["card"])
        top.pack(fill="x")

        # Icono + día
        icon = get_weather_icon(icon_code)
        tk.Label(top, text=icon,
                 font=("Segoe UI Emoji", 24),
                 bg=C["card"]).pack(side="left")

        day_frame = tk.Frame(top, bg=C["card"])
        day_frame.pack(side="left", padx=12)

        tk.Label(day_frame, text=day or f"Día {idx+1}",
                 font=("Segoe UI", 13, "bold"),
                 bg=C["card"], fg=C["text"]).pack(anchor="w")
        tk.Label(day_frame, text=date_str,
                 font=("Segoe UI", 9),
                 bg=C["card"], fg=C["subtext"]).pack(anchor="w")

        # Temperaturas
        temp_frame = tk.Frame(top, bg=C["card"])
        temp_frame.pack(side="right", padx=8)

        if t_max is not None:
            tk.Label(temp_frame,
                     text=f"↑ {t_max}°C",
                     font=("Segoe UI", 14, "bold"),
                     bg=C["card"],
                     fg=temp_color(t_max)).pack(anchor="e")
        if t_min is not None:
            tk.Label(temp_frame,
                     text=f"↓ {t_min}°C",
                     font=("Segoe UI", 11),
                     bg=C["card"],
                     fg=temp_color(t_min)).pack(anchor="e")

        # Lluvia
        if rain is not None:
            tk.Label(temp_frame,
                     text=f"💧 {rain} mm",
                     font=("Segoe UI", 9),
                     bg=C["card"], fg=C["subtext"]).pack(anchor="e")

        # Narrativa
        if narrative:
            tk.Frame(inner, bg=C["border"], height=1).pack(fill="x", pady=(8, 6))
            tk.Label(inner, text=narrative,
                     font=("Segoe UI", 9),
                     bg=C["card"], fg=C["subtext"],
                     wraplength=750, justify="left").pack(anchor="w")

    def _clear_cards(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()

    def _show_error(self, msg):
        self.lbl_status.configure(text="")
        self.btn_refresh.configure(state="normal")
        messagebox.showerror("Error al conectar con la API",
                             f"No se pudo obtener datos:\n\n{msg}\n\n"
                             "Verifica tu API key y conexión a internet.")


if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()
