import sqlite3
import os
from config import Config


def get_connection():
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
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

    conn.commit()
    conn.close()


def create_interview(room_id, role, candidate_name, duration=10):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT OR REPLACE INTO interviews (room_id, role, candidate_name, duration, status) VALUES (?, ?, ?, ?, 'active')",
        (room_id, role, candidate_name, duration)
    )

    conn.commit()
    conn.close()


def save_answers(room_id, answers):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE interviews SET answers=? WHERE room_id=?",
        (answers, room_id)
    )

    conn.commit()
    conn.close()


def save_report(room_id, report, qa_history=None):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE interviews SET report=?, qa_history=?, status='completed', ended_at=CURRENT_TIMESTAMP WHERE room_id=?",
        (report, qa_history, room_id)
    )

    conn.commit()
    conn.close()


def end_interview(room_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "UPDATE interviews SET status='ended', ended_at=CURRENT_TIMESTAMP WHERE room_id=?",
        (room_id,)
    )

    conn.commit()
    conn.close()


def get_interview(room_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM interviews WHERE room_id=?",
        (room_id,)
    )

    interview = cur.fetchone()
    conn.close()

    return interview


def get_all_interviews():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, room_id, candidate_name, role, duration, status, created_at, ended_at FROM interviews ORDER BY created_at DESC"
    )

    interviews = [dict(row) for row in cur.fetchall()]
    conn.close()

    return interviews


def get_interviews_by_ids(room_ids):
    if not room_ids:
        return []

    conn = get_connection()
    cur = conn.cursor()

    placeholders = ",".join("?" for _ in room_ids)
    cur.execute(
        f"SELECT * FROM interviews WHERE room_id IN ({placeholders})",
        room_ids
    )

    interviews = [dict(row) for row in cur.fetchall()]
    conn.close()

    return interviews