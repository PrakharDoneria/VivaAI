import sqlite3
import threading
import os
from contextlib import contextmanager
from config import Config

# Thread-safe database connection management
_db_lock = threading.RLock()
_thread_local = threading.local()


def get_connection():
    """Get thread-local database connection"""
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    
    if not hasattr(_thread_local, 'connection'):
        _thread_local.connection = sqlite3.connect(
            Config.DATABASE_PATH,
            check_same_thread=False,
            timeout=30.0
        )
        _thread_local.connection.row_factory = sqlite3.Row
    return _thread_local.connection


@contextmanager
def db_transaction():
    """Context manager for database transactions with automatic commit/rollback"""
    with _db_lock:
        conn = get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def init_db():
    """Initialize database tables"""
    with db_transaction() as conn:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT UNIQUE,
            role TEXT,
            candidate_name TEXT,
            duration INTEGER DEFAULT 10,
            answers TEXT,
            qa_history TEXT,
            report TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP
        )
        """)


def create_interview(room_id, role, candidate_name, duration=10):
    """Create a new interview"""
    with db_transaction() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO interviews (room_id, role, candidate_name, duration, status) VALUES (?, ?, ?, ?, 'active')",
            (room_id, role, candidate_name, duration)
        )


def save_answers(room_id, answers):
    """Save answers for an interview"""
    with db_transaction() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE interviews SET answers=? WHERE room_id=?",
            (answers, room_id)
        )


def save_report(room_id, report, qa_history=None):
    """Save report for an interview"""
    with db_transaction() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE interviews SET report=?, qa_history=?, status='completed', ended_at=CURRENT_TIMESTAMP WHERE room_id=?",
            (report, qa_history, room_id)
        )


def end_interview(room_id):
    """Mark interview as ended"""
    with db_transaction() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE interviews SET status='ended', ended_at=CURRENT_TIMESTAMP WHERE room_id=?",
            (room_id,)
        )


def get_interview(room_id):
    """Get interview by room ID"""
    with db_transaction() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM interviews WHERE room_id=?",
            (room_id,)
        )
        return cur.fetchone()


def get_all_interviews():
    """Get all interviews"""
    with db_transaction() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, room_id, candidate_name, role, duration, status, created_at, ended_at FROM interviews ORDER BY created_at DESC"
        )
        return [dict(row) for row in cur.fetchall()]


def get_interviews_by_ids(room_ids):
    """Get interviews by list of room IDs"""
    if not room_ids:
        return []
    
    with db_transaction() as conn:
        cur = conn.cursor()
        placeholders = ",".join("?" for _ in room_ids)
        cur.execute(
            f"SELECT * FROM interviews WHERE room_id IN ({placeholders})",
            room_ids
        )
        return [dict(row) for row in cur.fetchall()]