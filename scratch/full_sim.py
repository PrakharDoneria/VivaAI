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

    # Confidence — derive from communication and problem solving if available
    if 'communication' in scores and 'problem_solving' in scores:
        scores['confidence'] = round((scores['communication'] + scores['problem_solving']) / 2, 1)

    return scores

def get_analytics_data_sim():
    db_path = r'c:\Users\Aiswarya\Downloads\VivaAI\database\vivaai.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as total FROM interviews WHERE status = 'completed'")
    total_completed = cur.fetchone()['total']

    cur.execute("""
        SELECT id, room_id, role, candidate_name, duration, report, qa_history, 
               created_at, ended_at, status
        FROM interviews
        WHERE status = 'completed' AND report IS NOT NULL
        ORDER BY created_at DESC
    """)
    completed_interviews = [dict(row) for row in cur.fetchall()]
    conn.close()

    all_scores = []
    skill_totals = {'technical': [], 'communication': [], 'problem_solving': [], 'confidence': []}
    
    for interview in completed_interviews:
        scores = _parse_report_scores(interview.get('report', ''))
        overall = scores.get('overall')
        if overall is not None:
            all_scores.append(overall)

        for skill in skill_totals:
            if skill in scores:
                skill_totals[skill].append(scores[skill])

    avg_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0
    
    skill_averages = {}
    for skill, values in skill_totals.items():
        skill_averages[skill] = round(sum(values) / len(values), 1) if values else 0

    return {
        'total_completed': total_completed,
        'avg_score': avg_score,
        'skill_averages': skill_averages,
        'all_scores': all_scores
    }

print(json.dumps(get_analytics_data_sim(), indent=2))
