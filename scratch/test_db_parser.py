import sqlite3
import re
import json

def _extract_score(text, pattern):
    if not text:
        return None
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, IndexError):
            return None
    return None

def _parse_report_scores(report_text):
    if not report_text:
        return {}
    scores = {}
    
    # Technical Knowledge Score
    val = _extract_score(report_text, r'technical[\s-]*knowledge(?:[\s-]*score)?.*?\s+(\d+(?:\.\d+)?)\s*/\s*10')
    if val is None:
        val = _extract_score(report_text, r'technical[\s-]*knowledge[:\s]*(\d+(?:\.\d+)?)\s*/\s*10')
    if val is not None:
        scores['technical'] = min(val, 10)

    # Communication Score
    val = _extract_score(report_text, r'communication(?:[\s-]*score)?.*?\s+(\d+(?:\.\d+)?)\s*/\s*10')
    if val is None:
        val = _extract_score(report_text, r'communication[:\s]*(\d+(?:\.\d+)?)\s*/\s*10')
    if val is not None:
        scores['communication'] = min(val, 10)

    # Problem Solving Score
    val = _extract_score(report_text, r'problem[\s-]*solving(?:[\s-]*score)?.*?\s+(\d+(?:\.\d+)?)\s*/\s*10')
    if val is None:
        val = _extract_score(report_text, r'problem[\s-]*solving[:\s]*(\d+(?:\.\d+)?)\s*/\s*10')
    if val is not None:
        scores['problem_solving'] = min(val, 10)

    # Overall Score
    val = _extract_score(report_text, r'overall(?:[\s-]*score)?.*?\s+(\d+(?:\.\d+)?)\s*/\s*10')
    if val is None:
        val = _extract_score(report_text, r'overall[:\s]*(\d+(?:\.\d+)?)\s*/\s*10')
    
    if val is not None:
        scores['overall'] = min(val, 10)
    else:
        # Fallback: average of available scores
        available = [v for k, v in scores.items() if k in ['technical', 'communication', 'problem_solving']]
        if available:
            scores['overall'] = round(sum(available) / len(available), 1)

    return scores

db_path = r'c:\Users\Aiswarya\Downloads\VivaAI\database\vivaai.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("SELECT report FROM interviews WHERE id=1")
report = cur.fetchone()[0]
conn.close()

print(f"Report length: {len(report)}")
scores = _parse_report_scores(report)
print(f"Parsed scores: {scores}")
