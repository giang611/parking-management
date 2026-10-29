"""SQLite queries only. Each operation owns and closes its connection."""
import sqlite3
from contextlib import closing

DB_NAME = "vehicle.db"


def configure(db_name):
    global DB_NAME
    DB_NAME = db_name


def _connect():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init():
    with closing(_connect()) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS vehicles_in (
                ticket_id INTEGER PRIMARY KEY,
                plate TEXT,
                type TEXT NOT NULL
                    CHECK (type IN ('CAR', 'MOTORCYCLE', 'BICYCLE')),
                in_time INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                paid_at INTEGER NOT NULL
            );
        """)
        conn.commit()


def get(ticket):
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT ticket_id, plate, type, in_time FROM vehicles_in WHERE ticket_id = ?",
            (ticket,)
        ).fetchone()
        return dict(row) if row else None


def post(ticket, plate, vehicle_type, time_in):
    try:
        with closing(_connect()) as conn:
            conn.execute(
                "INSERT INTO vehicles_in (ticket_id, plate, type, in_time) VALUES (?, ?, ?, ?)",
                (ticket, plate, vehicle_type, time_in)
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def delete(ticket):
    with closing(_connect()) as conn:
        cur = conn.execute("DELETE FROM vehicles_in WHERE ticket_id = ?", (ticket,))
        conn.commit()
        return cur.rowcount > 0


def settle(ticket, vehicle_type, amount, paid_at):
    """Record revenue and remove the active ticket in one transaction."""
    with closing(_connect()) as conn:
        try:
            conn.execute("BEGIN")
            cur = conn.execute("DELETE FROM vehicles_in WHERE ticket_id = ?", (ticket,))
            if cur.rowcount == 0:
                conn.rollback()
                return False
            conn.execute(
                "INSERT INTO payments (ticket_id, type, amount, paid_at) VALUES (?, ?, ?, ?)",
                (ticket, vehicle_type, amount, paid_at)
            )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise


def revenue(start_time, end_time):
    with closing(_connect()) as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM payments WHERE paid_at >= ? AND paid_at < ?",
            (start_time, end_time)
        ).fetchone()
        return int(row["total"])
