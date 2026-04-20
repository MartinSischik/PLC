# core/database.py
# SQLite persistence for work orders, quality status, scheduler, motor runtime.

import sqlite3
import threading
import time
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "scada.db"

_local = threading.local()


def _get_conn() -> sqlite3.Connection:
    """One connection per thread (sqlite3 is not thread-safe by default)."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(str(DB_PATH))
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def init_db() -> None:
    """Create tables if they don't exist."""
    conn = _get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS silo_quality (
        silo_index   INTEGER PRIMARY KEY,
        status       TEXT NOT NULL DEFAULT 'libre'
                     CHECK (status IN ('libre', 'ok', 'cuarentena')),
        updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS work_orders (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        silo_index   INTEGER NOT NULL,
        order_type   TEXT NOT NULL
                     CHECK (order_type IN ('aireacion', 'enfriamiento', 'fumigacion', 'otro')),
        description  TEXT NOT NULL DEFAULT '',
        status       TEXT NOT NULL DEFAULT 'pendiente'
                     CHECK (status IN ('pendiente', 'en_progreso', 'completada', 'cancelada')),
        created_at   TEXT NOT NULL DEFAULT (datetime('now')),
        started_at   TEXT,
        completed_at TEXT
    );

    CREATE TABLE IF NOT EXISTS scheduled_actions (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        silo_index   INTEGER NOT NULL,
        action_type  TEXT NOT NULL
                     CHECK (action_type IN ('motor', 'ventilador', 'compuerta')),
        target_index INTEGER NOT NULL,
        start_time   TEXT NOT NULL,
        duration_min INTEGER NOT NULL,
        enabled      INTEGER NOT NULL DEFAULT 1,
        executed     INTEGER NOT NULL DEFAULT 0,
        created_at   TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS motor_runtime (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        motor_index  INTEGER NOT NULL,
        started_at   TEXT NOT NULL,
        stopped_at   TEXT,
        duration_sec REAL NOT NULL DEFAULT 0,
        work_order_id INTEGER,
        FOREIGN KEY (work_order_id) REFERENCES work_orders(id)
    );

    CREATE TABLE IF NOT EXISTS motor_runtime_totals (
        motor_index  INTEGER PRIMARY KEY,
        total_hours  REAL NOT NULL DEFAULT 0,
        updated_at   TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS weather_thresholds (
        id                   INTEGER PRIMARY KEY CHECK (id = 1),
        ambient_temp_max     REAL NOT NULL DEFAULT 30.0,
        ambient_humid_max    REAL NOT NULL DEFAULT 75.0,
        weather_auto_enabled INTEGER NOT NULL DEFAULT 0
    );

    INSERT OR IGNORE INTO weather_thresholds (id) VALUES (1);
    """)
    conn.commit()


# ── Quality Status ────────────────────────────────────────────────────────

def get_silo_quality(silo_index: int) -> str:
    conn = _get_conn()
    row = conn.execute(
        "SELECT status FROM silo_quality WHERE silo_index = ?", (silo_index,)
    ).fetchone()
    return row["status"] if row else "libre"


def get_all_silo_quality() -> dict[int, str]:
    conn = _get_conn()
    rows = conn.execute("SELECT silo_index, status FROM silo_quality").fetchall()
    return {r["silo_index"]: r["status"] for r in rows}


def set_silo_quality(silo_index: int, status: str) -> bool:
    if status not in ("libre", "ok", "cuarentena"):
        return False
    conn = _get_conn()
    conn.execute(
        """INSERT INTO silo_quality (silo_index, status, updated_at)
           VALUES (?, ?, datetime('now'))
           ON CONFLICT(silo_index)
           DO UPDATE SET status = excluded.status, updated_at = excluded.updated_at""",
        (silo_index, status),
    )
    conn.commit()
    return True


# ── Work Orders ───────────────────────────────────────────────────────────

def create_work_order(silo_index: int, order_type: str, description: str = "") -> int:
    conn = _get_conn()
    cur = conn.execute(
        "INSERT INTO work_orders (silo_index, order_type, description) VALUES (?, ?, ?)",
        (silo_index, order_type, description),
    )
    conn.commit()
    return cur.lastrowid


def get_work_orders(silo_index: Optional[int] = None, status: Optional[str] = None) -> list[dict]:
    conn = _get_conn()
    q = "SELECT * FROM work_orders WHERE 1=1"
    params: list = []
    if silo_index is not None:
        q += " AND silo_index = ?"
        params.append(silo_index)
    if status is not None:
        q += " AND status = ?"
        params.append(status)
    q += " ORDER BY created_at DESC"
    rows = conn.execute(q, params).fetchall()
    return [dict(r) for r in rows]


def update_work_order_status(order_id: int, status: str) -> bool:
    if status not in ("pendiente", "en_progreso", "completada", "cancelada"):
        return False
    conn = _get_conn()
    extra = ""
    if status == "en_progreso":
        extra = ", started_at = datetime('now')"
    elif status in ("completada", "cancelada"):
        extra = ", completed_at = datetime('now')"
    conn.execute(
        f"UPDATE work_orders SET status = ?{extra} WHERE id = ?",
        (status, order_id),
    )
    conn.commit()
    return True


# ── Scheduled Actions ─────────────────────────────────────────────────────

def create_scheduled_action(
    silo_index: int,
    action_type: str,
    target_index: int,
    start_time: str,
    duration_min: int,
) -> int:
    conn = _get_conn()
    cur = conn.execute(
        """INSERT INTO scheduled_actions
           (silo_index, action_type, target_index, start_time, duration_min)
           VALUES (?, ?, ?, ?, ?)""",
        (silo_index, action_type, target_index, start_time, duration_min),
    )
    conn.commit()
    return cur.lastrowid


def get_scheduled_actions(silo_index: Optional[int] = None, pending_only: bool = False) -> list[dict]:
    conn = _get_conn()
    q = "SELECT * FROM scheduled_actions WHERE 1=1"
    params: list = []
    if silo_index is not None:
        q += " AND silo_index = ?"
        params.append(silo_index)
    if pending_only:
        q += " AND executed = 0 AND enabled = 1"
    q += " ORDER BY start_time ASC"
    rows = conn.execute(q, params).fetchall()
    return [dict(r) for r in rows]


def mark_action_executed(action_id: int) -> None:
    conn = _get_conn()
    conn.execute("UPDATE scheduled_actions SET executed = 1 WHERE id = ?", (action_id,))
    conn.commit()


def delete_scheduled_action(action_id: int) -> None:
    conn = _get_conn()
    conn.execute("DELETE FROM scheduled_actions WHERE id = ?", (action_id,))
    conn.commit()


# ── Motor Runtime ─────────────────────────────────────────────────────────

def record_motor_start(motor_index: int, work_order_id: Optional[int] = None) -> int:
    conn = _get_conn()
    cur = conn.execute(
        "INSERT INTO motor_runtime (motor_index, started_at, work_order_id) VALUES (?, datetime('now'), ?)",
        (motor_index, work_order_id),
    )
    conn.commit()
    return cur.lastrowid


def record_motor_stop(motor_index: int) -> None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT id, started_at FROM motor_runtime WHERE motor_index = ? AND stopped_at IS NULL ORDER BY id DESC LIMIT 1",
        (motor_index,),
    ).fetchone()
    if row is None:
        return
    conn.execute(
        """UPDATE motor_runtime
           SET stopped_at = datetime('now'),
               duration_sec = (julianday(datetime('now')) - julianday(started_at)) * 86400
           WHERE id = ?""",
        (row["id"],),
    )
    # Update totals
    conn.execute(
        """INSERT INTO motor_runtime_totals (motor_index, total_hours, updated_at)
           VALUES (?, 0, datetime('now'))
           ON CONFLICT(motor_index) DO NOTHING""",
        (motor_index,),
    )
    conn.execute(
        """UPDATE motor_runtime_totals
           SET total_hours = (
               SELECT COALESCE(SUM(duration_sec), 0) / 3600.0
               FROM motor_runtime WHERE motor_index = ? AND stopped_at IS NOT NULL
           ), updated_at = datetime('now')
           WHERE motor_index = ?""",
        (motor_index, motor_index),
    )
    conn.commit()


def get_motor_runtime_totals() -> dict[int, float]:
    conn = _get_conn()
    rows = conn.execute("SELECT motor_index, total_hours FROM motor_runtime_totals").fetchall()
    return {r["motor_index"]: r["total_hours"] for r in rows}


def get_motor_runtime_history(motor_index: int, limit: int = 50) -> list[dict]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM motor_runtime WHERE motor_index = ? ORDER BY id DESC LIMIT ?",
        (motor_index, limit),
    ).fetchall()
    return [dict(r) for r in rows]


# ── Weather Thresholds ─────────────────────────────────────────────────────

def get_weather_thresholds() -> dict:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM weather_thresholds WHERE id = 1").fetchone()
    if row:
        return {
            "ambient_temp_max": row["ambient_temp_max"],
            "ambient_humid_max": row["ambient_humid_max"],
            "weather_auto_enabled": bool(row["weather_auto_enabled"]),
        }
    return {"ambient_temp_max": 30.0, "ambient_humid_max": 75.0, "weather_auto_enabled": False}


def set_weather_thresholds(
    ambient_temp_max: float,
    ambient_humid_max: float,
    weather_auto_enabled: bool,
) -> None:
    conn = _get_conn()
    conn.execute(
        """UPDATE weather_thresholds
           SET ambient_temp_max = ?, ambient_humid_max = ?, weather_auto_enabled = ?
           WHERE id = 1""",
        (ambient_temp_max, ambient_humid_max, int(weather_auto_enabled)),
    )
    conn.commit()
