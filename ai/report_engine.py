import inspect

from sarvamai import SarvamAI
from config import Config
from utils.sanitization import sanitize_model_output


def get_client():
    return SarvamAI(api_subscription_key=Config.SARVAM_API_KEY)


def _chat_completions(client, **kwargs):
    signature = inspect.signature(client.chat.completions)
    if "model" in signature.parameters:
        return client.chat.completions(**kwargs)

    kwargs.pop("model", None)
    return client.chat.completions(**kwargs)


def generate_report(role, qa_history):
    client = get_client()

    formatted = ""
    for i, qa in enumerate(qa_history, 1):
        formatted += f"\nQuestion {i}: {qa.get('question', '')}\nAnswer {i}: {qa.get('answer', '')}\n"

    prompt = f"""You are an expert HR manager and technical interviewer. Evaluate this interview session.

Role: {role}

Interview Transcript:
{formatted}

Provide a detailed evaluation with the following exact format for scores:
- Technical Knowledge Score: [X]/10
- Communication Score: [X]/10
- Problem Solving Score: [X]/10
- Overall Score: [X]/10

For each score, provide a brief justification immediately following the score line.

Also include:
5. Key Strengths (2-3 bullet points)
6. Areas for Improvement (2-3 bullet points)
7. Final Recommendation: [Strong Hire / Hire / Maybe / No Hire]

Be fair, constructive and professional.
Never include hidden reasoning, analysis, or any XML-like tags such as <think> or </think>.
Ensure the scores are clearly labeled exactly as shown above."""

    response = _chat_completions(
        client,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        top_p=1,
        max_tokens=600,
        model=Config.SARVAM_CHAT_MODEL,
    )

    return sanitize_model_output(response.choices[0].message.content)
