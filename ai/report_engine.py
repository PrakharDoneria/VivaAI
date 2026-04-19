import re
from urllib import response
from sarvamai import SarvamAI
from config import Config


def get_client():
    return SarvamAI(api_subscription_key=Config.SARVAM_API_KEY)


def generate_report(role, qa_history):
    client = get_client()

    formatted = ""
    for i, qa in enumerate(qa_history, 1):
        formatted += f"\nQuestion {i}: {qa.get('question', '')}\nAnswer {i}: {qa.get('answer', '')}\n"

    prompt = f"""You are an expert HR manager and technical interviewer. Evaluate this interview session.

Role: {role}

Interview Transcript:
{formatted}

Provide a detailed evaluation with:
1. Technical Knowledge Score (out of 10) - with brief justification
2. Communication Score (out of 10) - with brief justification  
3. Problem Solving Score (out of 10) - with brief justification
4. Overall Score (out of 10)
5. Key Strengths (2-3 bullet points)
6. Areas for Improvement (2-3 bullet points)
7. Final Recommendation: Strong Hire / Hire / Maybe / No Hire

Be fair, constructive and professional."""

    # response = client.chat.completions(
    #     messages=[{"role": "user", "content": prompt}],
    #     temperature=0.3,
    #     top_p=1,
    #     max_tokens=600
    # )

    # return response.choices[0].message.content
    
    response = client.chat.completions(
        model="sarvam-m",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        top_p=1,
        max_tokens=600
    )
    import re

    clean_response = re.sub(
        r"<think>.*?</think>",
        "",
        response.choices[0].message.content,
        flags=re.DOTALL
    )

    return clean_response.strip()

    return response.choices[0].message.content
    