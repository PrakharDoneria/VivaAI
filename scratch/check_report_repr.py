import sqlite3
import os

db_path = r'c:\Users\Aiswarya\Downloads\VivaAI\database\vivaai.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT report FROM interviews WHERE id=1")
report = cur.fetchone()[0]
print("FULL REPORT CONTENT:")
print(repr(report[:2000]))
conn.close()
