import re

def test_patterns(text):
    patterns = [
        r'technical[\s-]*knowledge(?:[\s-]*score)?.*?\s+(\d+(?:\.\d+)?)\s*/\s*10',
        r'technical[\s-]*knowledge[:\s]*(\d+(?:\.\d+)?)\s*/\s*10',
        r'technical[\s-]*knowledge.*?(\d+(?:\.\d+)?)\s*/\s*10',
        r'\d\.\s*\*\*Technical Knowledge Score.*?\*\*[:\s]*(\d+(?:\.\d+)?)\s*/\s*10'
    ]
    
    print(f"Testing text: {repr(text[:50])}...")
    for i, p in enumerate(patterns):
        match = re.search(p, text, re.IGNORECASE | re.DOTALL)
        if match:
            print(f"Pattern {i} matched: {match.group(1)}")
        else:
            print(f"Pattern {i} failed")

text = """
**Evaluation of Interview Session**

1. **Technical Knowledge Score (out of 10):** 5/10  
   *Justification:* The candidate demonstrates basic familiarity with cloud APIs (Gemini/Vertex) and quota/billing concepts but lacks specificity. They mention troubleshooting steps like enabling APIs and adjusting billing but fail to name specific APIs, quota types, or tools (e.g., Google Cloud’s IAM, monitoring dashboards). The explanation of quota limits and billing misalignment is vague and lacks technical depth.
"""

test_patterns(text)
