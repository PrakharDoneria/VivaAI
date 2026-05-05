import sqlite3
import re
import json
from config import Config


def get_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _extract_score(text, pattern):
    """Extract a numeric score from report text using a regex pattern."""
    if not text:
        return None
    # Use DOTALL to allow .* to match across newlines if needed
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, IndexError):
            return None
    return None


def _parse_report_scores(report_text):
    """Parse structured scores from an AI-generated interview report."""
    if not report_text:
        return {}

    scores = {}

    # Technical Knowledge Score
    patterns = [
        r'Technical[\s-]*Knowledge(?:[\s-]*Score)?[:\s]*(\d+(?:\.\d+)?)\s*/\s*10',
        r'technical[\s-]*knowledge.*?\s+(\d+(?:\.\d+)?)\s*/\s*10',
        r'1\.\s+.*?(\d+(?:\.\d+)?)\s*/\s*10'
    ]
    for p in patterns:
        val = _extract_score(report_text, p)
        if val is not None:
            scores['technical'] = min(val, 10)
            break

    # Communication Score
    patterns = [
        r'Communication(?:[\s-]*Score)?[:\s]*(\d+(?:\.\d+)?)\s*/\s*10',
        r'communication.*?\s+(\d+(?:\.\d+)?)\s*/\s*10',
        r'2\.\s+.*?(\d+(?:\.\d+)?)\s*/\s*10'
    ]
    for p in patterns:
        val = _extract_score(report_text, p)
        if val is not None:
            scores['communication'] = min(val, 10)
            break

    # Problem Solving Score
    patterns = [
        r'Problem[\s-]*Solving(?:[\s-]*Score)?[:\s]*(\d+(?:\.\d+)?)\s*/\s*10',
        r'problem[\s-]*solving.*?\s+(\d+(?:\.\d+)?)\s*/\s*10',
        r'3\.\s+.*?(\d+(?:\.\d+)?)\s*/\s*10'
    ]
    for p in patterns:
        val = _extract_score(report_text, p)
        if val is not None:
            scores['problem_solving'] = min(val, 10)
            break

    # Overall Score
    patterns = [
        r'Overall(?:[\s-]*Score)?[:\s]*(\d+(?:\.\d+)?)\s*/\s*10',
        r'overall.*?\s+(\d+(?:\.\d+)?)\s*/\s*10',
        r'4\.\s+.*?(\d+(?:\.\d+)?)\s*/\s*10'
    ]
    for p in patterns:
        val = _extract_score(report_text, p)
        if val is not None:
            scores['overall'] = min(val, 10)
            break

    if 'overall' not in scores:
        # Final fallback: average of available scores
        available = [v for k, v in scores.items() if k in ['technical', 'communication', 'problem_solving']]
        if available:
            scores['overall'] = round(sum(available) / len(available), 1)

    # Confidence — derive from communication and problem solving if available
    if 'communication' in scores and 'problem_solving' in scores:
        scores['confidence'] = round((scores['communication'] + scores['problem_solving']) / 2, 1)

    # Recommendation
    rec_match = re.search(
        r'(?:final\s+)?recommendation[:\s]*\[?(strong\s+hire|hire|maybe|no\s+hire)\]?',
        report_text, re.IGNORECASE
    )
    if rec_match:
        scores['recommendation'] = rec_match.group(1).strip().title()

    return scores


def _extract_improvements(report_text):
    """Extract improvement suggestions from the report text."""
    if not report_text:
        return []

    improvements = []
    # 1. Look for "Areas for Improvement" section
    section_match = re.search(
        r'areas?\s+for\s+improvement[:\s]*\n?((?:[-•*]\s*.+\n?)+)',
        report_text, re.IGNORECASE
    )
    if section_match:
        lines = section_match.group(1).strip().split('\n')
        for line in lines:
            clean = re.sub(r'^[-•*\d.)\s]+', '', line).strip()
            if clean and len(clean) > 5:
                improvements.append(clean)

    # 2. If no bullet points found, extract feedback from Justification sections
    if not improvements:
        # Look for "Justification" blocks and find critical feedback sentences
        justifications = re.findall(r'justification[:\s]*(.*?)(?=\n\d\.|\n\*\*|\Z)', report_text, re.IGNORECASE | re.DOTALL)
        for just in justifications:
            # Split into sentences
            sentences = re.split(r'(?<=[.!?])\s+', just.strip())
            for sent in sentences:
                sent = sent.strip().strip('*')
                # Look for feedback-like keywords
                if any(kw in sent.lower() for kw in ['lacks', 'fail', 'struggle', 'should', 'need', 'improve', 'missing', 'without', 'vague', 'disorganized']):
                    if len(sent) > 15 and len(sent) < 150:
                        improvements.append(sent)
    
    # 3. Fallback: catch any lines starting with bullet points
    if not improvements:
        for line in report_text.split('\n'):
            if re.match(r'^\s*[-•*]\s*', line):
                clean = re.sub(r'^[-•*\d.)\s]+', '', line).strip()
                if clean and len(clean) > 5:
                    improvements.append(clean)

    return improvements[:6]

    return improvements


def get_analytics_data():
    """Fetch all analytics data for the dashboard."""
    conn = get_connection()
    cur = conn.cursor()

    # --- Summary stats ---
    cur.execute("SELECT COUNT(*) as total FROM interviews WHERE status = 'completed'")
    total_completed = cur.fetchone()['total']

    cur.execute("SELECT COUNT(*) as total FROM interviews")
    total_all = cur.fetchone()['total']

    # --- Fetch all completed interviews ---
    cur.execute("""
        SELECT id, room_id, role, candidate_name, duration, report, qa_history, 
               technical_score, communication_score, problem_solving_score, 
               overall_score, recommendation, created_at, ended_at, status
        FROM interviews
        WHERE status = 'completed'
        ORDER BY created_at DESC
    """)
    completed_interviews = [dict(row) for row in cur.fetchall()]

    conn.close()

    # --- Parse scores from each report ---
    all_scores = []
    skill_totals = {'technical': [], 'communication': [], 'problem_solving': [], 'confidence': []}
    all_improvements = []
    interview_history = []
    recommendations = {'Strong Hire': 0, 'Hire': 0, 'Maybe': 0, 'No Hire': 0}

    for interview in completed_interviews:
        # Use existing scores if available, otherwise parse from report
        if interview.get('overall_score') is not None:
            scores = {
                'technical': interview.get('technical_score'),
                'communication': interview.get('communication_score'),
                'problem_solving': interview.get('problem_solving_score'),
                'overall': interview.get('overall_score'),
                'recommendation': interview.get('recommendation'),
            }
            # Calculate confidence on the fly for consistency
            if scores['communication'] and scores['problem_solving']:
                scores['confidence'] = round((scores['communication'] + scores['problem_solving']) / 2, 1)
        else:
            # Legacy or failed initial parse: parse from report
            scores = _parse_report_scores(interview.get('report', ''))
            
        improvements = _extract_improvements(interview.get('report', ''))
        all_improvements.extend(improvements)

        overall = scores.get('overall')
        if overall is not None:
            all_scores.append(overall)

        for skill in ['technical', 'communication', 'problem_solving', 'confidence']:
            if scores.get(skill) is not None:
                skill_totals[skill].append(scores[skill])

        rec = scores.get('recommendation', '')
        if rec in recommendations:
            recommendations[rec] += 1

        # Build history entry
        qa_count = 0
        if interview.get('qa_history'):
            try:
                qa_list = json.loads(interview['qa_history'])
                qa_count = len(qa_list) if isinstance(qa_list, list) else 0
            except (json.JSONDecodeError, TypeError):
                pass

        interview_history.append({
            'id': interview['id'],
            'room_id': interview['room_id'],
            'role': interview['role'],
            'candidate_name': interview['candidate_name'],
            'duration': interview['duration'],
            'date': interview['created_at'],
            'ended_at': interview['ended_at'],
            'overall_score': overall,
            'technical': scores.get('technical'),
            'communication': scores.get('communication'),
            'problem_solving': scores.get('problem_solving'),
            'confidence': scores.get('confidence'),
            'recommendation': scores.get('recommendation', 'N/A'),
            'questions_count': qa_count,
        })

    # --- Compute aggregate metrics ---
    avg_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else None
    highest_score = max(all_scores) if all_scores else None
    lowest_score = min(all_scores) if all_scores else None

    skill_averages = {}
    for skill, values in skill_totals.items():
        skill_averages[skill] = round(sum(values) / len(values), 1) if values else None

    # Progress data (chronological for chart)
    progress_data = []
    for entry in reversed(interview_history):
        if entry['overall_score'] is not None:
            progress_data.append({
                'date': entry['date'],
                'score': entry['overall_score'],
                'role': entry['role'],
            })

    # Deduplicate and rank improvement suggestions
    improvement_counts = {}
    for imp in all_improvements:
        key = imp.lower().strip()
        if key not in improvement_counts:
            improvement_counts[key] = {'text': imp, 'count': 0}
        improvement_counts[key]['count'] += 1
    top_improvements = sorted(improvement_counts.values(), key=lambda x: x['count'], reverse=True)[:6]

    return {
        'summary': {
            'total_completed': total_completed,
            'total_all': total_all,
            'average_score': avg_score,
            'highest_score': highest_score,
            'lowest_score': lowest_score,
        },
        'skill_averages': skill_averages,
        'recommendations': recommendations,
        'progress': progress_data,
        'history': interview_history[:20],  # Last 20 interviews
        'improvements': [item['text'] for item in top_improvements],
    }
