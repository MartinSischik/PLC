# core/scheduler_service.py
# Executes scheduled actions at their start_time and stops them after duration.

import threading
import time
from datetime import datetime, timedelta

from core.database import get_scheduled_actions, mark_action_executed


class SchedulerService:
    """Checks pending scheduled actions every 10s, executes them via PLC."""

    def __init__(self, plc, interval: float = 10.0):
        self._plc = plc
        self._interval = interval
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        # Track active actions: action_id -> stop_datetime
        self._active: dict[int, tuple[datetime, int]] = {}

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[SCHEDULER] Iniciado.")

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        print("[SCHEDULER] Detenido.")

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception as e:
                print(f"[SCHEDULER] Error: {e}")
            self._stop.wait(self._interval)

    def _tick(self) -> None:
        now = datetime.now()

        # Check for new actions that should start
        pending = get_scheduled_actions(pending_only=True)
        for action in pending:
            try:
                start_dt = datetime.fromisoformat(action["start_time"])
            except (ValueError, TypeError):
                continue

            if now >= start_dt and action["id"] not in self._active:
                # Start the action
                target = action["target_index"]
                print(f"[SCHEDULER] Ejecutando accion {action['id']}: "
                      f"silo={action['silo_index']} tipo={action['action_type']} target={target}")
                self._plc.set_motor_command(target, True)
                stop_dt = start_dt + timedelta(minutes=action["duration_min"])
                self._active[action["id"]] = (stop_dt, target)
                mark_action_executed(action["id"])

        # Check active actions that should stop
        finished = []
        for action_id, (stop_dt, target) in self._active.items():
            if now >= stop_dt:
                print(f"[SCHEDULER] Finalizando accion {action_id}: target={target}")
                self._plc.set_motor_command(target, False)
                finished.append(action_id)

        for aid in finished:
            del self._active[aid]
