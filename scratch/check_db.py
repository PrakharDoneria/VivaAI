import sqlite3
import os

db_path = r'c:\Users\Aiswarya\Downloads\VivaAI\database\vivaai.db'
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print("Tables:", cur.fetchall())
    
    cur.execute("SELECT COUNT(*) FROM interviews")
    print("Interview count:", cur.fetchone()[0])
    
    cur.execute("SELECT id, room_id, status, report IS NOT NULL FROM interviews")
    rows = cur.fetchall()
    print("Rows:", rows)
    conn.close()
