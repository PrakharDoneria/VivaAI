import sqlite3
import os
import json
from datetime import datetime

db_path = r'c:\Users\Aiswarya\Downloads\VivaAI\database\vivaai.db'
report_text = """
**Evaluation of Interview Session**

1. **Technical Knowledge Score (out of 10):** 5/10  
   *Justification:* The candidate demonstrates basic familiarity with cloud APIs (Gemini/Vertex) and quota/billing concepts but lacks specificity. They mention troubleshooting steps like enabling APIs and adjusting billing but fail to name specific APIs, quota types, or tools (e.g., Google Cloud’s IAM, monitoring dashboards). The explanation of quota limits and billing misalignment is vague and lacks technical depth.

2. **Communication Score (out of 10):** 4/10  
   *Justification:* Responses are disorganized, filled with filler words (“like,” “uh”), and lack clarity. For example, Answer 1 is incoherent, and Answer 4 conflates billing and API enablement without logical flow. The candidate struggles to articulate a structured narrative, making it difficult to follow their reasoning.

3. **Problem-Solving Score (out of 10):** 6/10  
   *Justification:* The candidate shows persistence (4–5 hours of research) and resourcefulness (leveraging documentation/YouTube), but their troubleshooting process lacks methodical rigor. They do not explain how they isolated the root cause (e.g., checking quota metrics, reviewing API-specific logs) or validated the effectiveness of each step. The focus on “enabling APIs” is overly broad and uncritical.
"""

qa_history = [
    {"question": "Tell me about a technical challenge you faced.", "answer": "Uh, like, I was trying to enable some APIs and it wasn't working, so I spent 5 hours on YouTube."},
    {"question": "How did you resolve the billing issue?", "answer": "I just went to the dashboard and clicked some things until it worked."}
]

def insert_interview():
    if not os.path.exists(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Ensure table exists (though it should)
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
    
    room_id = "manual_" + datetime.now().strftime("%Y%m%d%H%M%S")
    cur.execute(
        "INSERT INTO interviews (room_id, role, candidate_name, duration, report, qa_history, status, ended_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (room_id, "Cloud Engineer", "Aiswarya", 15, report_text, json.dumps(qa_history), "completed", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    
    conn.commit()
    print(f"Inserted manual interview record with room_id: {room_id}")
    conn.close()

if __name__ == "__main__":
    insert_interview()
