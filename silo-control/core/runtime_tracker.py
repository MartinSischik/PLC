# core/runtime_tracker.py
# Tracks motor runtime: detects start/stop transitions, records to SQLite.

import threading
from config import MOTOR_COUNT
from core.database import record_motor_start, record_motor_stop


class RuntimeTracker:
    """Polls motor states and records runtime transitions to the database."""

    def __init__(self, plc, interval: float = 2.0):
        self._plc = plc
        self._interval = interval
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        # Previous running state per motor (None = unknown)
        self._prev_running: list[bool | None] = [None] * MOTOR_COUNT

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[RUNTIME] Tracker iniciado.")

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        # Record stop for any still-running motors
        for i in range(MOTOR_COUNT):
            if self._prev_running[i]:
                record_motor_stop(i)
        print("[RUNTIME] Tracker detenido.")

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception as e:
                print(f"[RUNTIME] Error: {e}")
            self._stop.wait(self._interval)

    def _tick(self) -> None:
        if not self._plc.is_connected():
            return

        motors = self._plc.read_all_motors()
        if not motors:
            return

        for m in motors:
            idx = m.index
            if idx >= MOTOR_COUNT:
                continue
            running = m.is_running
            prev = self._prev_running[idx]

            if prev is not None:
                if not prev and running:
                    # Motor just started
                    record_motor_start(idx)
                elif prev and not running:
                    # Motor just stopped
                    record_motor_stop(idx)

            self._prev_running[idx] = running
