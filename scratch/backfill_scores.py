import sqlite3
import json
from config import Config
from models.analytics import _parse_report_scores

def backfill():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Fetch all completed interviews that don't have scores yet
    cur.execute("SELECT id, report, qa_history FROM interviews WHERE status = 'completed' AND overall_score IS NULL")
    interviews = cur.fetchall()
    
    print(f"Found {len(interviews)} interviews to backfill.")
    
    for row in interviews:
        report_text = row['report']
        if not report_text:
            continue
            
        scores = _parse_report_scores(report_text)
        if scores:
            print(f"Updating interview {row['id']} with scores: {scores}")
            cur.execute(
                """UPDATE interviews 
                   SET technical_score=?, communication_score=?, problem_solving_score=?, 
                       overall_score=?, recommendation=?
                   WHERE id=?""",
                (
                    scores.get('technical'), 
                    scores.get('communication'), 
                    scores.get('problem_solving'), 
                    scores.get('overall'), 
                    scores.get('recommendation'),
                    row['id']
                )
            )
    
    conn.commit()
    conn.close()
    print("Backfill complete.")

if __name__ == "__main__":
    backfill()
