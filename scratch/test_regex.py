import re

def _extract_score(text, pattern):
    """Extract a numeric score from report text using a regex pattern."""
    if not text:
        return None
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        print(f"Matched pattern: {pattern}")
        print(f"Groups: {match.groups()}")
        try:
            return float(match.group(1))
        except (ValueError, IndexError):
            return None
    return None

report_text = """
**Evaluation of Interview Session**

1. **Technical Knowledge Score (out of 10):** 5/10  
   *Justification:* The candidate demonstrates basic familiarity with cloud APIs (Gemini/Vertex) and quota/billing concepts but lacks specificity. They mention troubleshooting steps like enabling APIs and adjusting billing but fail to name specific APIs, quota types, or tools (e.g., Google Cloud’s IAM, monitoring dashboards). The explanation of quota limits and billing misalignment is vague and lacks technical depth.

2. **Communication Score (out of 10):** 4/10  
   *Justification:* Responses are disorganized, filled with filler words (“like,” “uh”), and lack clarity. For example, Answer 1 is incoherent, and Answer 4 conflates billing and API enablement without logical flow. The candidate struggles to articulate a structured narrative, making it difficult to follow their reasoning.

3. **Problem-Solving Score (out of 10):** 6/10  
   *Justification:* The candidate shows persistence (4–5 hours of research) and resourcefulness (leveraging documentation/YouTube), but their troubleshooting process lacks methodical rigor. They do not explain how they isolated the root cause (e.g., checking quota metrics, reviewing API-specific logs) or validated the effectiveness of each step. The focus on “enabling APIs” is overly broad and uncritical.
"""

patterns = {
    'technical': [
        r'technical[\s-]*knowledge(?:[\s-]*score)?.*?\s+(\d+(?:\.\d+)?)\s*/\s*10',
        r'technical[\s-]*knowledge[:\s]*(\d+(?:\.\d+)?)\s*/\s*10'
    ],
    'communication': [
        r'communication(?:[\s-]*score)?.*?\s+(\d+(?:\.\d+)?)\s*/\s*10',
        r'communication[:\s]*(\d+(?:\.\d+)?)\s*/\s*10'
    ],
    'problem_solving': [
        r'problem[\s-]*solving(?:[\s-]*score)?.*?\s+(\d+(?:\.\d+)?)\s*/\s*10',
        r'problem[\s-]*solving[:\s]*(\d+(?:\.\d+)?)\s*/\s*10'
    ]
}

for key, pats in patterns.items():
    print(f"Testing {key}:")
    found = False
    for p in pats:
        val = _extract_score(report_text, p)
        if val is not None:
            print(f"  Result: {val}")
            found = True
            break
    if not found:
        print(f"  FAILED to extract {key}")
