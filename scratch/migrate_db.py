import sqlite3
import os
from config import Config

def migrate():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cur = conn.cursor()
    
    # Check if columns already exist
    cur.execute("PRAGMA table_info(interviews)")
    columns = [row[1] for row in cur.fetchall()]
    
    new_cols = [
        ("technical_score", "REAL"),
        ("communication_score", "REAL"),
        ("problem_solving_score", "REAL"),
        ("overall_score", "REAL"),
        ("recommendation", "TEXT")
    ]
    
    for col_name, col_type in new_cols:
        if col_name not in columns:
            print(f"Adding column {col_name}...")
            cur.execute(f"ALTER TABLE interviews ADD COLUMN {col_name} {col_type}")
    
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
